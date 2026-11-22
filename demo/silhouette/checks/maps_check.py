"""StepA step 5: the maps that the page builds (maps.js) against the plate's own numbers. Pillow only.

usage: node silhouette/checks/cdp_shot.mjs <out> <port> --eval 'return window.__studio.readMapsRaw()' "view=<v>"
       python3 silhouette/checks/maps_check.py <plate-dir> <out>/log.json [--debug <png>]

  coverage  id R (zone) of the page, where id A gives a coverage of one half or more, against make_plate.py's in-memory id (the same outlines and under-strips, Pillow's polygon fill):
            the pixels that differ must lie in the 1 px band along an edge (a 3 x 3 window holds two values).        PASS: none outside
  uv        inside each zone, 2 px from every edge: the page's 16-bit (u, v) minus the view's offset against the frame's exact (u, v)
            at the pixel centre (silhouette/pipeline/plateframe.py).                                                                 PASS: max <= 0.01 cm
  fields    (StepA extension) the page's trim fields (uvt with id G: every trim but the slits; uvts: the slits) against the build's
            (make_plate.py rasterise, silhouette/pipeline/trimfield.py): a pixel that only one side has must lie on the field's own border or at the
            garment's edge (the page's soft-edge ribbon); on the common pixels the same trim (or the other side of a boundary between
            two trims: a neighbour has the page's trim; or the garment's edge, where the page's zone runs 3 px further), s within 0.01 cm and t within 0.05 mm
            (99.9 %; one 16-bit step is 0.002 cm of s, 0.02 mm of t).
Exit code 0 = all pass.
"""
import base64, json, math, os, sys
from PIL import Image, ImageChops, ImageFilter
sys.path[:0] = [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), d) for d in ("pipeline", "checks", "views")]
import make_plate, platedat, plateframe

pd, logp = sys.argv[1].rstrip("/"), sys.argv[2]
RANGE = 128.0
log = json.load(open(logp))
res = next(e for e in log if isinstance(e.get("result"), dict))["result"]
P = platedat.read(pd)
plate, Z = platedat.legacy(P)
W, H = P["viewBox"]; MM = P["mmPerPx"]
raw = lambda k: base64.b64decode(res[k])
ok = True


def say(name, passed, text):
    global ok
    ok &= passed
    print(f"{'PASS' if passed else 'FAIL'}  {name:9} {text}")


M = make_plate.maps_of(pd)
ref_r = M["id"].split()[0]
pid = raw("id")
page_r = Image.frombytes("L", (W, H), bytes(pid[0::4]))
page_g = Image.frombytes("L", (W, H), bytes(pid[1::4]))
# soft free edges (step 6): R holds the zone out to 3 px beyond a free edge, A = (d + 3) / 4 the signed distance; the shader's
# coverage is clamp(0.5 + d). A pixel counts as the zone's where its coverage is at least one half (d >= 0, less a quarter of an 8-bit A step)
page_a = Image.frombytes("L", (W, H), bytes(pid[3::4]))
page_r = Image.composite(page_r, Image.new("L", (W, H), 0), page_a.point(lambda a: 255 if a * 4 / 255 - 3 >= -0.01 else 0))
# ---- coverage
diff = ImageChops.difference(page_r, ref_r).point(lambda v: 255 if v else 0)
band = ImageChops.difference(ref_r.filter(ImageFilter.MaxFilter(3)), ref_r.filter(ImageFilter.MinFilter(3))).point(lambda v: 255 if v else 0)
outside = ImageChops.subtract(diff, band)
nd, no = sum(diff.histogram()[1:]), sum(outside.histogram()[1:])
say("coverage", no == 0, f"{nd} px differ, {no} outside the 1 px edge band" + (f" (bbox {outside.getbbox()})" if no else ""))
# ---- uv
puv = raw("uv")
off = Z.get("uvOffsetCm", [0.0, 0.0])
core = ref_r.filter(ImageFilter.MinFilter(5))
eq = ref_r.filter(ImageFilter.MaxFilter(5))
rp, cp, ep = ref_r.load(), core.load(), eq.load()
errs = []
for zn, z in Z["zones"].items():
    F = z.get("frame")
    if not F: continue
    zid = P["zones"][zn]["id"]
    for y in range(0, H, 3):
        for x in range(0, W, 3):
            if rp[x, y] != zid or cp[x, y] != zid or ep[x, y] != zid: continue
            i = (y * W + x) * 4
            u = (puv[i] * 256 + puv[i + 1]) / 65535 * RANGE - off[0]
            v = (puv[i + 2] * 256 + puv[i + 3]) / 65535 * RANGE - off[1]
            eu, ev = plateframe.uv(F, MM, x, y)
            errs.append(max(abs(u - eu), abs(v - ev)))
errs.sort()
if errs:
    say("uv", errs[-1] <= 0.01, f"{len(errs)} px: |du|, |dv| median {errs[len(errs) // 2]:.5f}, 99 % {errs[int(len(errs) * 0.99)]:.5f}, max {errs[-1]:.5f} cm (limit 0.01; a 16-bit step is {RANGE / 65535:.5f})")
# ---- trims (StepA extension, step L2): the page's trim fields (uvt + id G, uvts) against the build's (make_plate.py, trimfield.py)
import trimfield as TF
G = page_g.load()
for key in ("main", "slit"):
    if key == "main" and "uvt" not in res: continue
    if key == "slit" and "uvts" not in res: continue
    buf = raw("uvt" if key == "main" else "uvts")
    ref = M["field"][key]
    page = {}
    for i in range(W * H):
        k = i * 4
        if key == "main":
            g = G[i % W, i // W]
            if not g: continue
        elif not (buf[k] or buf[k + 1] or buf[k + 2] or buf[k + 3]): continue
        u = (buf[k] * 256 + buf[k + 1]) / 65535 * RANGE
        v = (buf[k + 2] * 256 + buf[k + 3]) / 65535 * RANGE
        if key == "main": page[i] = (g, u - TF.S_OFF_CM, v * 10 - TF.T_OFF_MM)
        else:
            sid = 6 if u >= 64 else 5
            page[i] = (sid, u - TF.SLIT_OFF_CM["slit-r" if sid == 6 else "slit-l"], v * 10 - TF.T_OFF_MM)
    only_p = [i for i in page if i not in ref]; only_r = [i for i in ref if i not in page]
    # a pixel that only one side has must lie on the field's own border: a neighbour (8) without a value on that side, or at the
    # garment's edge (the page's soft-edge ribbon gives the zone 3 px beyond a free edge; the build's outline does not)
    def border(i, F):
        x, y = i % W, i // W
        return any((y + dy) * W + (x + dx) not in F for dx in (-1, 0, 1) for dy in (-1, 0, 1) if 0 <= x + dx < W and 0 <= y + dy < H)
    def near_edge(i):
        x, y = i % W, i // W
        return len({R_[x + dx, y + dy] for dx in (-3, 0, 3) for dy in (-3, 0, 3) if 0 <= x + dx < W and 0 <= y + dy < H}) > 1
    R_ = ref_r.load()
    bad_cov = [i for i in only_p if not (border(i, page) or near_edge(i))] + [i for i in only_r if not (border(i, ref) or near_edge(i))]
    say(f"{key} cover", not bad_cov, f"{len(page)} px on the page, {len(ref)} in the build; only one side: {len(only_p)} + {len(only_r)}, "
        f"of them away from the field's border and the garment edge: {len(bad_cov)}" + (f" e.g. {[(i % W, i // W) for i in bad_cov[:5]]}" if bad_cov else ""))
    ds, dt, wrong = [], [], 0
    for i, (tid, s_, t) in ref.items():
        p = page.get(i)
        if not p: continue
        if p[0] != tid:                                       # a tie on a boundary between two trims (float32 / float64): its
            x, y = i % W, i // W                              # neighbour on the build's side has the page's trim
            if not (near_edge(i) or any(ref.get((y + dy) * W + x + dx, (0,))[0] == p[0] for dx in (-1, 0, 1) for dy in (-1, 0, 1))): wrong += 1
            continue
        ds.append(abs(p[1] - s_)); dt.append(abs(p[2] - t * MM))
    ds.sort(); dt.sort()
    if ds:
        q = lambda L, f: L[min(len(L) - 1, int(len(L) * f))]
        say(f"{key} values", wrong == 0 and q(ds, 0.999) <= 0.01 and q(dt, 0.999) <= 0.05,
            f"{len(ds)} px: s 99.9 % {q(ds, 0.999):.4f} max {ds[-1]:.4f} cm (limit 0.01); t 99.9 % {q(dt, 0.999):.4f} max {dt[-1]:.4f} mm (limit 0.05); another trim: {wrong}")
if "--debug" in sys.argv:
    dbg = Image.open(os.path.join(pd, "base.jpg")).convert("RGB")
    dbg.paste((255, 0, 255), mask=outside); dbg.paste((0, 200, 255), mask=ImageChops.subtract(diff, outside))
    dbg.save(sys.argv[sys.argv.index("--debug") + 1])
print("ALL PASS" if ok else "SOME FAIL")
sys.exit(0 if ok else 1)
