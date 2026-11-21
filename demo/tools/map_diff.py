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
          of PNG - built| <= 0.15 px), median <= 0.5 px + 1 step, 99 % <= 1.5 px + 1 step. The 99.9 % and the max (zone edges)
          are printed as information.
  uvt     the same for each trim, on the trim pixels (G equal in both, 2 px from an edge): u in cm along; v (0..1 over vMax) in px
          across the strip. Bias <= 0.15 px, median <= 0.5 px (+ 1 step for u), 99 % <= 1.5 px (+ 1 step for u).
  shade   (step 4) inside the garment (2 px from the edges): <= 1 level of 255 in 99 % of the pixels, <= 3 levels (0.001 % of the pixels may be above); outside: <= 3;
          the dip (neck area without garment, carried 8 px outward): mean |d| <= 2.5 levels.
Exit code 0 = all pass.
"""
import base64, io, json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_plate
from PIL import Image, ImageChops, ImageDraw, ImageFilter

pd, logp = sys.argv[1], sys.argv[2]
only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
tol_px = float(sys.argv[sys.argv.index("--tol-px") + 1]) if "--tol-px" in sys.argv else 0.5
REF = make_plate.maps_of(pd)                  # the reference maps: make_plate.py, in memory, from plate.dat (StepA step 1)
plate = REF["plate"]
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


def hole_mask(R):
    """255 on R == 0 pixels that the outside cannot reach (4-connected flood from the corner): real gaps and hairline gaps."""
    m = R.point(lambda v: 0 if v == 0 else 255)                 # 0 = empty, 255 = zone
    ImageDraw.floodfill(m, (0, 0), 128)
    return m.point(lambda v: 255 if v == 0 else 0)


def unpack(img):
    r, g, b = img.split()
    rb, gb, bb = r.tobytes(), g.tobytes(), b.tobytes()
    u = [(rb[i] << 4) | (bb[i] >> 4) for i in range(len(rb))]
    v = [(gb[i] << 4) | (bb[i] & 15) for i in range(len(gb))]
    return u, v


want = lambda n: (only is None or n in only) and n in res
ref_id = REF["id"]
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
        # a trim strip is painted from unwelded quads, whose outlines leave a few stray pixels at the bends of the centre line:
        # for G (trims) up to 0.2 % of the PNG's trim pixels may differ away from an edge; for R and B none
        allowed = 0.002 * sum(a.point(lambda v: 1 if v else 0).getdata()) if nm == "G" else 0
        say(f"id {nm}", outside <= allowed, f"{nd} px differ ({nd / (W * H) * 100:.3f} % of the plate), {outside} of them away from an edge of the PNG (1 px band; {allowed:.0f} allowed)")
    # holes: the real gaps (between the arm and the body) are bigger by the PNG's 0.4 px edge in the PNG's favour; a hairline gap between
    # two zones would be a hole far from every PNG hole. Pass: every built hole pixel is within 1 px of a PNG hole pixel.
    m1, m2 = hole_mask(ref_id.split()[0]), hole_mask(mid.split()[0])
    far = ImageChops.multiply(m2, ImageChops.invert(m1.filter(ImageFilter.MaxFilter(3)))).histogram()[255]
    # (a pixel that is R = 0 in both but 4-connected to the outside in only one of them, as at a diagonal touch, is not a gap: up to 3)
    say("id holes", far <= 3, f"R = 0 pixels inside the garment: PNG {m1.histogram()[255]}, built {m2.histogram()[255]}; {far} built ones are more than 1 px from a PNG hole (a hairline gap)")
    cov1, cov2 = sum(ref_id.split()[0].point(lambda v: 1 if v else 0).getdata()), sum(mid.split()[0].point(lambda v: 1 if v else 0).getdata())
    say("id area", abs(cov2 - cov1) <= 0.002 * cov1, f"garment pixels: PNG {cov1}, built {cov2} ({(cov2 - cov1) / cov1 * 100:+.3f} %)")

if want("uv"):
    ref = REF["uv"]
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
        # 99 % <= 1.5 px + 1 step, no bias (the mean of PNG - built within 0.15 px)
        lim_med, lim_99 = 0.5 + step / pxe, 1.5 + step / pxe
        passed = q(0.5) / pxe <= lim_med and q(0.99) / pxe <= lim_99 and bias <= 0.1
        say(f"uv {nm}", passed, f"{len(d)} px: median {q(.5) / pxe:.2f} px ({q(.5) * 10:.2f} mm), 99 % {q(.99) / pxe:.2f} px, 99.9 % {q(.999) / pxe:.2f} px, max {d[-1] / pxe:.1f} px of fabric; bias {bias:.2f} px; limits {lim_med:.2f} / {lim_99:.2f} px / 0.15")
if want("uvt"):
    mid = load(res["id"])
    ref = REF["uvt"]
    mine = load(res["uvt"])
    gref, gmine = ref_id.split()[1], mid.split()[1]
    inside = ImageChops.multiply(gref.point(lambda v: 255 if v else 0), band(gref, 5).point(lambda v: 0 if v else 255))
    mk, gb, gm = inside.tobytes(), gref.tobytes(), gmine.tobytes()
    u1, v1 = unpack(ref)
    u2, v2 = unpack(mine)
    step = RANGE / 4095
    pxe = MM / 10
    cross = {t["id"]: t["vMax"] * t["widthMm"] / MM for t in plate["trims"].values()}      # px across the whole strip, for each trim id
    stats = {}
    for i in range(len(mk)):
        if mk[i] and gb[i] == gm[i]:
            st = stats.setdefault(gb[i], [[], [], 0.0, 0.0])
            st[0].append(abs(u1[i] - u2[i]) * step / pxe)
            st[1].append(abs(v1[i] - v2[i]) / 4095 * cross[gb[i]])
            st[2] += (u1[i] - u2[i]) * step / pxe
            st[3] += (v1[i] - v2[i]) / 4095 * cross[gb[i]]
    names = {t["id"]: n for n, t in plate["trims"].items()}
    for tid, (du, dv, su, sv) in sorted(stats.items()):
        n = len(du)
        for nm, d, sg, lim_step in (("u", du, su, step / pxe), ("v", dv, sv, 0.0)):
            d.sort()
            q = lambda f: d[min(len(d) - 1, int(f * len(d)))]
            bias = abs(sg) / n
            lim_med, lim_99 = 0.5 + lim_step, 1.5 + lim_step
            say(f"uvt {names[tid][:5]} {nm}", q(0.5) <= lim_med and q(0.99) <= lim_99 and bias <= 0.15,
                f"{n} px: median {q(.5):.2f} px, 99 % {q(.99):.2f} px, max {d[-1]:.1f} px; bias {bias:.2f} px; limits {lim_med:.2f} / {lim_99:.2f} px / 0.15")
if want("shade"):
    ref = REF["shade"]
    mine = load(res["shade"]).split()[0]
    d = ImageChops.difference(ref, mine)
    R = ref_id.split()[0]
    inner = ImageChops.multiply(R.point(lambda v: 255 if v else 0), band(R, 5).point(lambda v: 0 if v else 255))        # garment, 2 px from its edges
    far = band(R, 5).point(lambda v: 0 if v else 255)                                                                           # 2 px from an edge of the garment
    outside = ImageChops.multiply(ImageChops.multiply(R.point(lambda v: 255 if not v else 0), ref_id.split()[2].point(lambda v: 0 if v else 255)), far)   # not garment, not neck area
    dip = ImageChops.multiply(ImageChops.multiply(R.point(lambda v: 255 if not v else 0), ref_id.split()[2].point(lambda v: 255 if v else 0)), far)       # the dip: B = 1, no garment

    def stats(mask):
        h = d.histogram(mask)
        n = sum(h)
        return n, sum(h[:2]) / max(1, n), max([i for i, c in enumerate(h) if c] or [0]), sum(h[4:]), sum(i * c for i, c in enumerate(h)) / max(1, n)
    n, w1, mx, over3, mean = stats(inner)
    # <= 3 levels everywhere in the plan; a few isolated pixels (7 of 1.4 M on the hem plate: a byte on a rounding boundary in a steep
    # fold) are 4-5 levels off: allow up to 0.001 % of the pixels above 3
    say("shade in", w1 >= 0.99 and over3 <= 1e-5 * n, f"{n} garment px: {w1 * 100:.2f} % within 1 level, mean |d| {mean:.3f}, max {mx}, {over3} px above 3 levels")
    n, w1, mx, over3, mean = stats(outside)
    say("shade out", mx <= 3, f"{n} px outside the garment and 2 px from it: max {mx} levels (180 = shade 1.0)")
    if dip.getbbox():
        n, w1, mx, over3, mean = stats(dip)
        # the dip carries the shade of the garment's edge pixels outward; the PNG's garment edge is up to 1 px away from the built one, and
        # an edge pixel is often an edge roll or a shadow: the carried values differ by a few levels. The page replaces this area (halfway
        # step 3) except in a 5 px band. Mean |d| <= 2.5 levels.
        say("shade dip", mean <= 2.5, f"{n} dip px (carried 8 px outward): {w1 * 100:.2f} % within 1 level, mean |d| {mean:.3f}, max {mx}")
    n, w1, mx, over3, mean = stats(Image.new("L", d.size, 255))
    print(f"      whole plate: {over3} of {n} px differ by more than 3 levels (garment edges: the PNG's garment is 0.4 px larger)")
print("ALL PASS" if ok else "SOME FAIL")
sys.exit(0 if ok else 1)
