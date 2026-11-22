"""Invariants that every plate must hold (numeric.md step 11). Pillow only. PASS / FAIL / info per rule; exit 0 = no FAIL.

usage: python3 silhouette/checks/plate_invariants.py <plate-dir> [--debug <out.png>]

A plate must be right in itself, not only equal to its maps: the maps carry the plate's faults too.

  closure       garment pixels of the PHOTO (low colour saturation: the wall and the mannequin are warm) that no zone covers (a zone's
                outline and its under-strips), within 10 px of a zone: <= 0.02 % of the zone area, and no piece wider than 1 px (what
                survives a 2 x 2 erosion).
                the plate's "invariants": {"openings": [[x0, y0, x1, y1], ...]} leaves out regions where bare garment is right
                (an underskirt seen through a slit).
  no gaps       R = 0 pixels that the outside cannot reach (flood fill from every border pixel): the THIN parts of them (what an erosion and
                a dilation by 3 x 3 removes: a hairline between zones) <= 8 px. Wide ones are real openings (the wall between arm and body).
  trim line     (StepA extension, step L1) each trim's line lies on its own edge (exact, plate.dat): mean <= 0.3 px, std <= 0.5 px (the
                10 % at each end left out). The lace hangs on it at the lace's own width (silhouette/pipeline/trimfield.py).
  trim smooth   residual of local quadratic fits (31 px windows) along the line: <= 0.8 px. A quadratic follows a bend, so
                curvature does not count as wobble; pixel noise does.
  trim ends     information: each end against its anchor landmark.
  trim field    complete: every pixel of the trim's zone that the band reaches (1 px to 30 mm in, along the line's normals) has a value;
                continuous: no seam of s within 30 mm of the edge (a step over 2 px of face-on cloth and over 3 times the steps beside
                it); deeper seams (a bend tighter than the band) are listed.
  landmarks     every landmark of the plate lies on a zone or within 6 px of one.
  frame         (StepA step 4) no fold (Jacobian > 0 in each zone's box + 16 px), constant-u lines within 3 deg of the axis in 95 % of the
                zone, the UV rate at the axis within 2 % of face-on, u = 0 through the centre-front landmarks within 1 px.
"""
import json, math, os, sys
from PIL import Image, ImageChops, ImageDraw, ImageFilter
sys.path[:0] = [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), d) for d in ("pipeline", "checks", "views")]
import make_plate

pd = sys.argv[1].rstrip("/")
MAPS = make_plate.maps_of(pd)                 # the maps of plate.dat, in memory (StepA step 1)
Z, P = MAPS["zones"], MAPS["plate"]
W, H = P["viewBox"]; MM = P["mmPerPx"]
ID = MAPS["id"]; R = ID.split()[0]
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
# StepA limits: 0.02 %, no piece wider than 1 px (2 x 2 erosion)
wide = ImageChops.multiply(ImageChops.multiply(U, ImageChops.offset(U, -1, 0)), ImageChops.multiply(ImageChops.offset(U, 0, -1), ImageChops.offset(U, -1, -1)))
nw = sum(1 for v in wide.getdata() if v)
report("closure", f"uncovered garment {unc} px = {100 * unc / area:.4f} % of the zones (limit 0.02 %); pieces wider than 1 px: {nw} px, bbox {wide.getbbox()}", unc / area <= 0.0002 and nw == 0)

# ---- no gaps
t = zone.copy()
for (x, y) in [(i, 0) for i in range(0, W, 7)] + [(i, H - 1) for i in range(0, W, 7)] + [(0, j) for j in range(0, H, 7)] + [(W - 1, j) for j in range(0, H, 7)]:
    if t.getpixel((x, y)) == 0: ImageDraw.floodfill(t, (x, y), 128)
hole = t.point(lambda v: 255 if v == 0 else 0)
core = hole.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))      # opening: what stays is wider than 2 px (a real opening: the wall between arm and body)
thin = ImageChops.subtract(hole, core)
holes = sum(1 for v in hole.getdata() if v); nthin = sum(1 for v in thin.getdata() if v)
report("no gaps", f"{holes} px enclosed R = 0 ({holes - nthin} px in real openings), thin parts (a hairline between zones): {nthin} px (limit 8)", nthin <= 8)

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


def t_name(t):
    return f"'{t['edge']}'"


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
import trimfield as TF
FIELD = MAPS["field"]
for name, tr in Z["trims"].items():
    PT = MAPS["P"]["trims"][name]
    c = resample(tr["line"], 1.0)
    lo, hi = int(len(c) * 0.1), int(len(c) * 0.9)
    e = MAPS["P"]["edges"][PT["edge"]]["points"]
    def pdist(q):
        best = 1e9
        for u, v in zip(e, e[1:]):
            dx, dy = v[0] - u[0], v[1] - u[1]; L2 = dx * dx + dy * dy or 1.0
            t_ = max(0.0, min(1.0, ((q[0] - u[0]) * dx + (q[1] - u[1]) * dy) / L2))
            best = min(best, math.hypot(q[0] - u[0] - t_ * dx, q[1] - u[1] - t_ * dy))
        return best
    de = [pdist(q) for q in c[lo:hi:2]]
    m = sum(de) / len(de); sd = math.sqrt(sum((v - m) ** 2 for v in de) / len(de))
    report("trim line", f"{name}: on its edge {t_name(PT)}: mean {m:.2f} px, std {sd:.2f} px (limits 0.3 / 0.5)", m <= 0.3 and sd <= 0.5)
    wob = quad_residual(c) if len(c) > 45 else 0.0
    report("trim smooth", f"{name}: residual of local quadratic fits {wob:.2f} px (limit 0.8)", wob <= 0.8)
    for end, q in (("from", tr["line"][0]), ("to", tr["line"][-1])):
        lm = PT.get(end)
        if lm in Z.get("landmarks", {}):
            report("trim ends", f"{name} {end}: {math.dist(q, Z['landmarks'][lm]):.1f} px from {lm} (its nearest point on the edge)", True, info=True)
    # the field: complete (every pixel of the zone that the band reaches, 1 px to 30 mm in, along the line's normals, has a value) and
    # continuous (between 4-neighbours of this trim, s changes by at most 4 px of face-on cloth: the frame crowds it at most 1 / cos 70 deg)
    key = "slit" if name in TF.SLIT_OFF_CM else "main"
    if name == "neck" and P.get("neck"):
        report("trim field", f"{name}: laid by the page from the live neck edge (not in the field)", True, info=True)
        continue
    F_ = FIELD[key]
    zid = make_plate.ZONE_ID[PT["zone"]]
    pts = resample(tr["line"], 2.0)
    miss = tot = 0
    skip = int(TF.NORMAL_MM / MM / 2.0)                  # a cut end is square to its smooth normal: its first 30 mm are left out
    cuts = tr.get("cut", [])
    for i in range(1, len(pts) - 1):
        if ("from" in cuts and i < skip) or ("to" in cuts and i > len(pts) - 1 - skip): continue
        (ax, ay), (bx, by) = pts[i - 1], pts[i + 1]
        L = math.hypot(bx - ax, by - ay) or 1.0
        nx, ny = -(by - ay) / L * PT["side"], (bx - ax) / L * PT["side"]
        for d in range(1, int(30 / MM)):
            x, y = round(pts[i][0] + nx * d), round(pts[i][1] + ny * d)
            if not (0 <= x < W and 0 <= y < H) or rp[x, y] != zid: break
            tot += 1
            if (y * W + x) not in F_: miss += 1
    report("trim field", f"{name}: {miss} of {tot} pixels of the band (1 px to 30 mm in) without a value (limit 0)", miss == 0)
    # a seam in the field: a step of s between two neighbours over 2 px of face-on cloth AND over 3 times the steps on either side of
    # it (a steep but smooth ramp, where the frame crowds the cloth toward a silhouette, is no seam). Within 30 mm of the edge (the
    # default lace): FAIL; deeper (only the widest laces reach there): information.
    lim = 2 * MM / 10
    tid0 = make_plate.TRIM_ID[name]
    def sv(i):
        o = F_.get(i)
        return o[1] if o and o[0] == tid0 else None
    near = far = 0
    for i, (tid, s_, t_) in F_.items():
        if tid != tid0: continue
        for step in (1, W):
            sj = sv(i + step)
            if sj is None: continue
            dlt = abs(sj - s_)
            if dlt <= lim: continue
            sides = [abs(s_ - x) for x in (sv(i - step),) if x is not None] + [abs(x - sj) for x in (sv(i + 2 * step),) if x is not None]
            if sides and dlt <= 3 * max(sides): continue
            if abs(t_) * MM <= 30: near += 1
            else: far += 1
    report("trim field", f"{name}: {near} seams of s within 30 mm of the edge (limit 0)", near == 0)
    if far: report("trim field", f"{name}: {far} seams of s deeper than 30 mm (a bend tighter than the band: only the widest laces reach)", True, info=True)

# ---- landmarks
bad = []
for k, (x, y) in Z.get("landmarks", {}).items():
    if not (0 <= x < W and 0 <= y < H): continue                          # a landmark at the frame edge
    box = (max(0, int(x) - 6), max(0, int(y) - 6), min(W, int(x) + 7), min(H, int(y) + 7))
    if zone.crop(box).getbbox() is None: bad.append(k)
report("landmarks", f"{len(Z.get('landmarks', {}))} landmarks, none away from a zone" if not bad else f"away from every zone: {', '.join(bad)}", not bad)

# ---- the fabric frame of each zone (StepA step 4)
import plateframe
zid = {n: P["zones"][n]["id"] for n in Z["zones"]}
for zn, z in Z["zones"].items():
    F = z.get("frame")
    if not F: continue
    f = lambda x, y, F=F: plateframe.uv(F, MM, x, y)
    o = z["outline"]
    x0, x1 = min(p[0] for p in o) - 16, max(p[0] for p in o) + 16
    y0, y1 = min(p[1] for p in o) - 16, max(p[1] for p in o) + 16
    folds, n, tilts = 0, 0, []
    y = y0
    while y <= y1:
        x = x0
        while x <= x1:
            ux1, vx1 = f(x + 0.5, y); ux0, vx0 = f(x - 0.5, y)
            uy1, vy1 = f(x, y + 0.5); uy0, vy0 = f(x, y - 0.5)
            gu, gv = (ux1 - ux0, uy1 - uy0), (vx1 - vx0, vy1 - vy0)
            J = gu[0] * gv[1] - gu[1] * gv[0]
            n += 1
            if J <= 0: folds += 1
            xi, yi = int(x), int(y)
            if 0 <= xi < W and 0 <= yi < H and rp[xi, yi] == zid[zn] and math.hypot(*gu) > 0:
                s_, _ = plateframe.project(F["axis"], (x, y))
                _, (tx, ty) = plateframe.point_at(F["axis"], min(max(s_, 0.0), F["L"]))
                d = (-gu[1], gu[0])                                # along a constant-u line
                c = abs(d[0] * tx + d[1] * ty) / math.hypot(*d)
                tilts.append(math.degrees(math.acos(min(1.0, c))))
            x += 6
        y += 6
    report("frame fold", f"{zn}: {folds} of {n} points in the box + 16 px with a Jacobian <= 0", folds == 0)
    tilts.sort()
    t95 = tilts[int(0.95 * len(tilts))] if tilts else 0.0
    report("frame grain", f"{zn}: constant-u lines against the axis, 95 % within {t95:.2f} deg (limit 3)", t95 <= 3.0)
    rates = []
    for k in range(1, 20):
        (px, py), _ = plateframe.point_at(F["axis"], F["L"] * k / 20)
        ua, va = f(px + 0.5, py); ub, vb = f(px - 0.5, py); uc, vc = f(px, py + 0.5); ud, vd = f(px, py - 0.5)
        rates += [math.hypot(ua - ub, uc - ud) / (MM / 10), math.hypot(va - vb, vc - vd) / (MM / 10)]
    report("frame rate", f"{zn}: UV rate at the axis {min(rates):.3f} .. {max(rates):.3f} x face-on (limits 0.98 .. 1.02)", all(0.98 <= r_ <= 1.02 for r_ in rates))
    cfs = [k for k in ("cf-neck", "cf-low", "hem-cf") if k in Z.get("landmarks", {})]
    if zn == "front" and cfs and F.get("axisFrom") != "midline":
        off = [abs(plateframe.project(F["axis"], Z["landmarks"][k])[1]) for k in cfs]
        report("frame cf", f"{zn}: u = 0 through {', '.join(cfs)}: {max(off):.2f} px (limit 1)", max(off) <= 1.0)

if "--debug" in sys.argv:
    ov = photo.copy(); ov.paste((255, 0, 255), mask=U); ov.save(sys.argv[sys.argv.index("--debug") + 1])
nf = sum(1 for _, _, ok, info in results if not ok and not info)
print(f"{'ALL PASS' if not nf else f'{nf} FAIL'}  ({pd})")
sys.exit(1 if nf else 0)
