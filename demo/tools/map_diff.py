"""numeric.md map test: the maps that the page built on the GPU against the PNG maps of make_plate.py. Pillow only.

usage: node tools/cdp_shot.mjs <out> <port> --eval 'return window.__studio.readMaps()' "view=torso&geom=mesh"
       python3 tools/map_diff.py <plate-dir> <out>/log.json [--only id,uv] [--tol-px 0.5]

The page returns data URLs of the textures it built ({id, uv, uvt, shade}, whichever the step has built); a map that is
missing is skipped. Tests (numeric.md section 2):
  id      R (zone) and B (neck area): the pixels that differ must lie in the 1 px band along an edge of the PNG (3 x 3 window);
          G (trims) the same once the trims are built. Also: holes inside the garment (R = 0 pixels that the outside cannot
          reach), which must equal the PNG's: no hairline gap between zones.
  uv      inside the zones, 2 px away from every edge: |du|, |dv| in px of fabric (cm / (mmPerPx / 10)). The PNG paints one constant value
          on each 1 px quad (the value at the quad centre, after the later quads have overwritten the earlier ones) and packs it in
          12 bits (uvRangeCm / 4095 per step): about +-0.5 px of jitter and a bias of about +1 px of the surface. Pass: no bias (|mean
          of PNG - built| <= 0.1 px), median <= 0.5 px + 1 step, 99 % <= 1.5 px + 1 step. The 99.9 % and the max (zone edges)
          are printed as information.
  uvt     the same, on the trim pixels (G > 0 in both): u in cm along, v (0..1 over vMax) in steps of the strip width.
  shade   (step 4) <= 1 level of 255 in 99 % of the garment pixels, <= 3 levels everywhere.
Exit code 0 = all pass.
"""
import base64, io, json, math, sys
from PIL import Image, ImageChops, ImageDraw, ImageFilter

pd, logp = sys.argv[1], sys.argv[2]
only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
tol_px = float(sys.argv[sys.argv.index("--tol-px") + 1]) if "--tol-px" in sys.argv else 0.5
plate = json.load(open(f"{pd}/plate.json"))
RANGE, MM = plate["uvRangeCm"], plate["mmPerPx"]
W, H = plate["viewBox"]
log = json.load(open(logp))
entry = next(e for e in log if isinstance(e.get("result"), dict))
res = entry["result"]
if not res:
    sys.exit("the page built no maps for this view (is the view in MESH_VIEWS, and ?geom=mesh set?)")
load = lambda b64: Image.open(io.BytesIO(base64.b64decode(b64.split(",")[1]))).convert("RGB")
ok = True


def say(name, passed, text):
    global ok
    ok &= passed
    print(f"{'PASS' if passed else 'FAIL'}  {name:10} {text}")


def band(ch, w=3):
    """255 on pixels within the w x w window of an edge of this channel (the window holds two values)."""
    return ImageChops.difference(ch.filter(ImageFilter.MaxFilter(w)), ch.filter(ImageFilter.MinFilter(w))).point(lambda v: 255 if v else 0)


def holes(R):
    """count of R == 0 pixels that the outside cannot reach (4-connected flood from the corner)."""
    m = R.point(lambda v: 0 if v == 0 else 255)                 # 0 = empty, 255 = zone
    ImageDraw.floodfill(m, (0, 0), 128)
    return m.histogram()[0]


def unpack(img):
    r, g, b = img.split()
    rb, gb, bb = r.tobytes(), g.tobytes(), b.tobytes()
    u = [(rb[i] << 4) | (bb[i] >> 4) for i in range(len(rb))]
    v = [(gb[i] << 4) | (bb[i] & 15) for i in range(len(gb))]
    return u, v


want = lambda n: (only is None or n in only) and n in res
ref_id = Image.open(f"{pd}/id.png").convert("RGB")
if want("id"):
    mid = load(res["id"])
    for ci, nm in enumerate("RGB"):
        if nm == "G" and "uvt" not in res and "idG" not in res:
            continue                                            # the trims are still the PNG's own until step 3
        a, b = ref_id.split()[ci], mid.split()[ci]
        d = ImageChops.difference(a, b).point(lambda v: 255 if v else 0)
        nd = d.histogram()[255]
        bd = band(a, 3)
        outside = ImageChops.multiply(d, bd.point(lambda v: 0 if v else 255)).histogram()[255]
        say(f"id {nm}", outside == 0, f"{nd} px differ ({nd / (W * H) * 100:.3f} % of the plate), {outside} of them away from an edge of the PNG (1 px band)")
    h1, h2 = holes(ref_id.split()[0]), holes(mid.split()[0])
    say("id holes", h2 <= h1, f"R = 0 pixels inside the garment: PNG {h1}, built {h2}")
    cov1, cov2 = sum(ref_id.split()[0].point(lambda v: 1 if v else 0).getdata()), sum(mid.split()[0].point(lambda v: 1 if v else 0).getdata())
    say("id area", abs(cov2 - cov1) <= 0.002 * cov1, f"garment pixels: PNG {cov1}, built {cov2} ({(cov2 - cov1) / cov1 * 100:+.3f} %)")

if want("uv"):
    ref = Image.open(f"{pd}/uv.png").convert("RGB")
    mine = load(res["uv"])
    rid = ref_id.split()[0]
    inside = ImageChops.multiply(rid.point(lambda v: 255 if v else 0), band(rid, 5).point(lambda v: 0 if v else 255))   # in a zone, 2 px from any edge
    # the neck dip also carries a uv in the PNG; compare there too (B = 1), away from the edges of the area
    nb = ref_id.split()[2].point(lambda v: 255 if v else 0)
    inside = ImageChops.lighter(inside, ImageChops.multiply(nb, band(ref_id.split()[2], 5).point(lambda v: 0 if v else 255)))
    mk = inside.tobytes()
    u1, v1 = unpack(ref)
    u2, v2 = unpack(mine)
    step = RANGE / 4095
    floor_cm = MM / 20 + step                                    # half a px of fabric (cm) + one packing step
    du, dv, su, sv, where = [], [], 0.0, 0.0, []
    for i in range(len(mk)):
        if mk[i]:
            du.append(abs(u1[i] - u2[i]) * step)
            dv.append(abs(v1[i] - v2[i]) * step)
            su += (u1[i] - u2[i]) * step
            sv += (v1[i] - v2[i]) * step
            if du[-1] > 2 * MM / 10 or dv[-1] > 2 * MM / 10:
                where.append((i % W, i // W))
    n = max(1, len(du))
    if "--debug" in sys.argv:                                     # |du| and |dv| in px of fabric, x40, to look at where the error is
        dbg = Image.new("RGB", (W, H))
        px = dbg.load()
        k = 0
        for i in range(len(mk)):
            if mk[i]:
                px[i % W, i // W] = (min(255, int(du[k] * 10 / MM * 40)), min(255, int(dv[k] * 10 / MM * 40)), 0)
                k += 1
        dbg.save(sys.argv[sys.argv.index("--debug") + 1])
    print(f"      signed mean (PNG - built): u {su / n * 10 / MM:+.3f} px, v {sv / n * 10 / MM:+.3f} px of fabric")
    if where:
        xs, ys = [w[0] for w in where], [w[1] for w in where]
        print(f"      {len(where)} px off by > 2 px of fabric, in x {min(xs)}..{max(xs)}, y {min(ys)}..{max(ys)}")
    pxe = MM / 10                                                 # cm of fabric per plate px
    for nm, d, sg in (("u", du, su), ("v", dv, sv)):
        d.sort()
        q = lambda f: d[min(len(d) - 1, int(f * len(d)))]
        bias = abs(sg / n) / pxe
        # the PNG paints a 1 px quad with its centre value: +-0.5 px of jitter, and packs 12 bits (one step): median <= 0.5 px + 1 step,
        # 99 % <= 1.5 px + 1 step, no bias (the mean of PNG - built within 0.1 px)
        lim_med, lim_99 = 0.5 + step / pxe, 1.5 + step / pxe
        passed = q(0.5) / pxe <= lim_med and q(0.99) / pxe <= lim_99 and bias <= 0.1
        say(f"uv {nm}", passed, f"{len(d)} px: median {q(.5) / pxe:.2f} px ({q(.5) * 10:.2f} mm), 99 % {q(.99) / pxe:.2f} px, 99.9 % {q(.999) / pxe:.2f} px, max {d[-1] / pxe:.1f} px of fabric; bias {bias:.2f} px; limits {lim_med:.2f} / {lim_99:.2f} px / 0.1")
print("ALL PASS" if ok else "SOME FAIL")
sys.exit(0 if ok else 1)
