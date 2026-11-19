"""Invariants that every plate must hold (numeric.md step 11). Pillow only. PASS / FAIL / info per rule; exit 0 = no FAIL.

usage: python3 tools/plate_invariants.py <plate-dir> [--debug <out.png>]

A plate must be right in itself, not only equal to its maps: the maps carry the plate's faults too.

  closure       garment pixels of the PHOTO (low colour saturation: the wall and the mannequin are warm) that no zone covers, within
                10 px of a zone: <= 0.05 % of the zone area, and no piece wider than 2 px (it survives a 3 x 3 erosion).
                zones.json "invariants": {"openings": [[x0, y0, x1, y1], ...]} leaves out regions where bare garment is right
                (an underskirt seen through a slit).
  no gaps       R = 0 pixels that the outside cannot reach (flood fill from every border pixel): the THIN parts of them (what an erosion and
                a dilation by 3 x 3 removes: a hairline between zones) <= 8 px. Wide ones are real openings (the wall between arm and body).
  symmetry      (plates with tuck.cx) the front outline mirrored about the centre line, per row: mean <= 2.0 px, max <= 8 px.
                The photo is not symmetric to the pixel: the torso plate as first made (before step 9) measured mean 1.7 / max 5.6 px.
  trim offset   each edging / insertion trim: the distance from its centre line along the garment side to the zone's edge equals half
                the strip: mean within 1.5 px, std <= 1.0 px (the 10 % at each end left out).
  trim smooth   residual of local quadratic fits (31 px windows) along the centre line: <= 0.8 px. A quadratic follows a bend, so
                curvature does not count as wobble; hand-traced noise does (a traced slit trim: about 1 px, a sloppy one: 3-4 px).
                zones.json "invariants": {"skipTrimOffset": [names]} leaves out a trim whose strip is wider than its piece.
  trim joins    information: the distance between the ends of each trim and the nearest other trim's centre line.
  landmarks     every landmark of zones.json lies on a zone or within 6 px of one.
  plate_checks  tools/plate_checks.py (grain, bulge, UV rate, block ratio): no FAIL.
"""
import json, math, os, subprocess, sys
from PIL import Image, ImageChops, ImageDraw, ImageFilter

pd = sys.argv[1].rstrip("/")
Z = json.load(open(pd + "/zones.json")); P = json.load(open(pd + "/plate.json"))
W, H = P["viewBox"]; MM = P["mmPerPx"]
ID = Image.open(pd + "/id.png").convert("RGB"); R = ID.split()[0]
photo = Image.open(pd + "/base.jpg").convert("RGB")
inv = Z.get("invariants", {})
results = []


def report(rule, what, ok, info=False):
    results.append((rule, what, ok, info))
    print(f"{'info' if info else ('PASS' if ok else 'FAIL')}  {rule:<13} {what}")


# ---- closure
zone = R.point(lambda v: 255 if v else 0)
sat = photo.convert("HSV").split()[1]
G = sat.point(lambda v: 255 if v < 24 else 0).filter(ImageFilter.MedianFilter(3))
U = ImageChops.multiply(ImageChops.subtract(G, zone.filter(ImageFilter.MaxFilter(3))), zone.filter(ImageFilter.MaxFilter(21)))
dr = ImageDraw.Draw(U)
for box in inv.get("openings", []): dr.rectangle(box, fill=0)
area = sum(1 for v in zone.getdata() if v)
unc = sum(1 for v in U.getdata() if v)
wide = U.filter(ImageFilter.MinFilter(3))
nw = sum(1 for v in wide.getdata() if v)
report("closure", f"uncovered garment {unc} px = {100 * unc / area:.3f} % of the zones (limit 0.05 %); pieces wider than 2 px: {nw} px, bbox {wide.getbbox()}", unc / area <= 0.0005 and nw == 0)

# ---- no gaps
t = zone.copy()
for (x, y) in [(i, 0) for i in range(0, W, 7)] + [(i, H - 1) for i in range(0, W, 7)] + [(0, j) for j in range(0, H, 7)] + [(W - 1, j) for j in range(0, H, 7)]:
    if t.getpixel((x, y)) == 0: ImageDraw.floodfill(t, (x, y), 128)
hole = t.point(lambda v: 255 if v == 0 else 0)
core = hole.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))      # opening: what stays is wider than 2 px (a real opening: the wall between arm and body)
thin = ImageChops.subtract(hole, core)
holes = sum(1 for v in hole.getdata() if v); nthin = sum(1 for v in thin.getdata() if v)
report("no gaps", f"{holes} px enclosed R = 0 ({holes - nthin} px in real openings), thin parts (a hairline between zones): {nthin} px (limit 8)", nthin <= 8)

# ---- symmetry (torso)
cx = (Z.get("tuck") or {}).get("cx")
if cx:
    o = Z["zones"]["front"]["outline"]
    def span(y):
        xs = []
        for (x0, y0), (x1, y1) in zip(o, o[1:] + o[:1]):
            if (y0 <= y < y1) or (y1 <= y < y0): xs.append(x0 + (y - y0) / (y1 - y0) * (x1 - x0))
        return (min(xs), max(xs)) if xs else None
    ds = []
    for y in range(330, 1400, 4):
        s_ = span(y)
        if s_: ds.append(abs((cx - s_[0]) - (s_[1] - cx)))
    mean = sum(ds) / len(ds)
    report("symmetry", f"front outline left / right about x = {cx}: mean {mean:.1f} px, max {max(ds):.1f} px (limits 2.0 / 8)", mean <= 2.0 and max(ds) <= 8.0)
else:
    report("symmetry", "not applicable (no tuck.cx: a one-sided view)", True, info=True)


# ---- trims
def resample(pts, step=1.0):
    s = [0.0]
    for a, b in zip(pts, pts[1:]): s.append(s[-1] + math.dist(a, b))
    n = max(2, int(s[-1] / step)); out = []; j = 0
    for i in range(n + 1):
        tt = s[-1] * i / n
        while j < len(s) - 2 and s[j + 1] < tt: j += 1
        f = (tt - s[j]) / ((s[j + 1] - s[j]) or 1.0)
        out.append((pts[j][0] + (pts[j + 1][0] - pts[j][0]) * f, pts[j][1] + (pts[j + 1][1] - pts[j][1]) * f))
    return out


def quad_residual(pts, window=31):
    """Largest residual of a local quadratic fit (x(s), y(s), arc length s, `window` samples) at the centre sample."""
    h = window // 2; worst = 0.0
    for i in range(h, len(pts) - h, 3):
        seg = pts[i - h:i + h + 1]; ts = [k - h for k in range(len(seg))]
        for c in (0, 1):
            vs = [p[c] for p in seg]
            S0 = len(ts); S2 = sum(t * t for t in ts); S4 = sum(t ** 4 for t in ts)
            Y0 = sum(vs); Y2 = sum(t * t * v for t, v in zip(ts, vs))
            det = S0 * S4 - S2 * S2
            a0 = (Y0 * S4 - Y2 * S2) / det                                 # value of the fit at t = 0 (the odd terms vanish at the centre)
            worst = max(worst, abs(vs[h] - a0))
    return worst


rp = R.load()
for name, tr in Z["trims"].items():
    info = P["trims"].get(name)
    if not info: continue
    half = tr["widthMm"] / 2 / MM; side = info["side"]
    c = resample(tr["centre"], 1.0)
    # distance along the garment side from the centre line to the first R = 0 pixel
    ds = []
    lo, hi = int(len(c) * 0.1), int(len(c) * 0.9)
    for i in range(lo, hi, 2):
        a, b = c[i - 1], c[i + 1]; tx, ty = b[0] - a[0], b[1] - a[1]; ln = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / ln * side, tx / ln * side
        d = None
        for step in range(0, 200):
            x, y = int(c[i][0] + nx * step), int(c[i][1] + ny * step)
            if not (0 <= x < W and 0 <= y < H) or rp[x, y] == 0: d = step; break
        if d is not None and d < 199: ds.append(d)
    if name in inv.get("skipTrimOffset", []):
        report("trim offset", f"{name}: not tested (zones.json invariants.skipTrimOffset: the strip is wider than its piece)", True, info=True)
    elif len(ds) > 10 and info.get("type") == "edging":
        m = sum(ds) / len(ds); sd = math.sqrt(sum((v - m) ** 2 for v in ds) / len(ds))
        report("trim offset", f"{name}: centre to the edge {m:.1f} px (half strip {half:.1f}), std {sd:.2f} px", abs(m - half) <= 1.5 and sd <= 1.0)
    elif len(ds) > 10:
        report("trim offset", f"{name}: insertion, centre to the nearest edge {sum(ds) / len(ds):.1f} px (half strip {half:.1f}); not tested", True, info=True)
    wob = quad_residual(c) if len(c) > 45 else 0.0
    report("trim smooth", f"{name}: residual of local quadratic fits {wob:.2f} px (limit 0.8)", wob <= 0.8)

names = list(Z["trims"])
for n in names:
    ends = [Z["trims"][n]["centre"][0], Z["trims"][n]["centre"][-1]]
    for m in names:
        if m == n: continue
        cm = resample(Z["trims"][m]["centre"], 2.0)
        for e, tag in zip(ends, ("start", "end")):
            d = min(math.dist(e, p) for p in cm)
            if d < 90: report("trim joins", f"{n} {tag} to the centre line of {m}: {d:.1f} px ({d * MM:.1f} mm)", True, info=True)

# ---- landmarks
bad = []
for k, (x, y) in Z.get("landmarks", {}).items():
    if not (0 <= x < W and 0 <= y < H): continue                          # a landmark at the frame edge
    box = (max(0, int(x) - 6), max(0, int(y) - 6), min(W, int(x) + 7), min(H, int(y) + 7))
    if zone.crop(box).getbbox() is None: bad.append(k)
report("landmarks", f"{len(Z.get('landmarks', {}))} landmarks, none away from a zone" if not bad else f"away from every zone: {', '.join(bad)}", not bad)

# ---- plate_checks
r = subprocess.run([sys.executable, "-W", "ignore", os.path.join(os.path.dirname(__file__), "plate_checks.py"), pd], capture_output=True, text=True)
fails = [l for l in r.stdout.splitlines() if l.startswith("FAIL")]
report("plate_checks", "no FAIL" if not fails else "; ".join(l[5:].strip() for l in fails), not fails)

if "--debug" in sys.argv:
    ov = photo.copy(); ov.paste((255, 0, 255), mask=U); ov.save(sys.argv[sys.argv.index("--debug") + 1])
nf = sum(1 for _, _, ok, info in results if not ok and not info)
print(f"{'ALL PASS' if not nf else f'{nf} FAIL'}  ({pd})")
sys.exit(1 if nf else 0)
