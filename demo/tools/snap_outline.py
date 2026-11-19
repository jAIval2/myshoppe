"""Snap plate curves to the photographed garment edge (numeric.md steps 9-10).

usage: python3 tools/snap_outline.py <plate-dir> shoulders [--dry] [--preview out.png]

shoulders (torso plate): the front's shoulder run (sleeve top, over the rounded cap, along the slope, to the neck corner)
  was a straight line inside the real slope, with a gap to the sleeve zone at the tip. For each side:
  1. the run is rebuilt as a polyline from the sleeve's top point through the old tip and the old run to the neck corner,
     densified to 3 px;
  2. every point moves along its outward normal, at most 5 px, to the 50 % crossing of the garment mask
     (garment = low colour saturation, the wall and the mannequin are warm: the same key as plate_invariants.py);
  3. the displacements are smoothed (the ends stay);
  4. the new run replaces the front outline's run AND the front grid's top edge (the grid limits what the outline can show);
     the grid's side corners are the run's ends.
  zones.json "tuck".outlineExemptY keeps the tuck (a 10 px push, made for the side seam) off the run.
Run it once on a zones.json that has not been snapped; it refuses to run twice ("snapped" key).
"""
import json, math, sys
from PIL import Image, ImageFilter


def garment_mask(photo):
    """F image of 0..1: 1 = garment (neutral white linen), 0 = wall / mannequin (warm). 0.5 at saturation 22 of 255."""
    s = photo.convert("HSV").split()[1].filter(ImageFilter.GaussianBlur(0.8)).convert("F")
    from PIL import ImageMath
    return ImageMath.lambda_eval(lambda a: ((28.0 - a["s"]) / 12.0) * (a["s"] > 16.0) * (a["s"] < 28.0) + (a["s"] <= 16.0) * 1.0, s=s)


class Sampler:
    def __init__(self, im):
        self.w, self.h = im.size
        self.d = list(im.getdata())

    def at(self, x, y):
        x = min(max(x, 0.0), self.w - 1.001); y = min(max(y, 0.0), self.h - 1.001)
        x0, y0 = int(x), int(y); fx, fy = x - x0, y - y0; w = self.w; d = self.d
        a = d[y0 * w + x0]; b = d[y0 * w + x0 + 1]; c = d[(y0 + 1) * w + x0]; e = d[(y0 + 1) * w + x0 + 1]
        return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + e * fx) * fy


def densify(pts, step=3.0):
    out = [list(pts[0])]
    for a, b in zip(pts, pts[1:]):
        n = max(1, round(math.dist(a, b) / step))
        for i in range(1, n + 1):
            out.append([a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n])
    return out


def normals(pts):
    out = []
    for i in range(len(pts)):
        a = pts[max(0, i - 1)]; b = pts[min(len(pts) - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]; L = math.hypot(tx, ty) or 1.0
        out.append((ty / L, -tx / L))
    return out


def robust_cubic(pts, d, fixed, degree=3, rounds=3, cut=1.2):
    """Least-squares polynomial of the displacement along the arc length, points more than `cut` px off the fit dropped
    (a soft or shaded edge gives single wild crossings), the `fixed` points (the neck corner) kept at 0 by a heavy weight."""
    s = [0.0]
    for a, b in zip(pts, pts[1:]): s.append(s[-1] + math.dist(a, b))
    L = s[-1] or 1.0; x = [v / L for v in s]
    w = [1.0] * len(d)
    for k in fixed: w[k] = 1e4
    coef = [0.0] * (degree + 1)
    for _ in range(rounds):
        A = [[sum(w[k] * x[k] ** (i + j) for k in range(len(x))) for j in range(degree + 1)] for i in range(degree + 1)]
        b = [sum(w[k] * d[k] * x[k] ** i for k in range(len(x))) for i in range(degree + 1)]
        for i in range(degree + 1):                                       # Gauss elimination
            piv = max(range(i, degree + 1), key=lambda r: abs(A[r][i])); A[i], A[piv] = A[piv], A[i]; b[i], b[piv] = b[piv], b[i]
            for r in range(i + 1, degree + 1):
                f = A[r][i] / A[i][i]
                for c in range(i, degree + 1): A[r][c] -= f * A[i][c]
                b[r] -= f * b[i]
        for i in range(degree, -1, -1):
            coef[i] = (b[i] - sum(A[i][c] * coef[c] for c in range(i + 1, degree + 1))) / A[i][i]
        fit = [sum(coef[i] * xk ** i for i in range(degree + 1)) for xk in x]
        w = [1e4 if k in fixed else (1.0 if abs(d[k] - fit[k]) <= cut else 0.0) for k in range(len(d))]
    return fit


def snap_run(pts, M, reach=5.0, fixed=(0,)):
    """Move each point along its outward normal to the 50 % crossing garment -> wall. Returns the new points and the moves."""
    n = normals(pts)
    # outward = the side where the mask is lower, on average over the run
    side = sum(M.at(p[0] + 8 * q[0], p[1] + 8 * q[1]) - M.at(p[0] - 8 * q[0], p[1] - 8 * q[1]) for p, q in zip(pts, n))
    sgn = -1.0 if side > 0 else 1.0
    n = [(sgn * a, sgn * b) for a, b in n]
    d = []
    for p, q in zip(pts, n):
        best = None; prev = None; t = -reach
        while t <= reach + 1e-9:
            v = M.at(p[0] + t * q[0], p[1] + t * q[1])
            if prev is not None and prev[1] >= 0.5 > v:
                tc = prev[0] + (prev[1] - 0.5) / (prev[1] - v) * (t - prev[0])
                if best is None or abs(tc) < abs(best): best = tc
            prev = (t, v); t += 0.25
        d.append(best)
    # points with no crossing keep the displacement of their neighbours (interpolated), else 0
    known = [i for i, v in enumerate(d) if v is not None]
    for i in range(len(d)):
        if d[i] is None:
            lo = max((k for k in known if k < i), default=None); hi = min((k for k in known if k > i), default=None)
            d[i] = d[lo] if hi is None else d[hi] if lo is None else d[lo] + (d[hi] - d[lo]) * (i - lo) / (hi - lo)
    fixed = [k % len(d) for k in fixed]
    for i in fixed: d[i] = 0.0
    d = robust_cubic(pts, d, fixed)                                              # the shoulder slope is smooth: a cubic of the displacement
    out = [[round(p[0] + k * q[0], 1), round(p[1] + k * q[1], 1)] for p, q, k in zip(pts, n, d)]
    return out, d


def xspan(poly, y):
    """(min x, max x) of a closed polygon on the horizontal line at y, or None."""
    xs = []
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 <= y < y1) or (y1 <= y < y0): xs.append(x0 + (y - y0) / (y1 - y0) * (x1 - x0))
    return (min(xs), max(xs)) if xs else None


def tuck_profile(Z, front_outline, y0, step=6):
    """How far the front's side is pushed outward at each height (zones.json tuck.profile {left, right}, each [[y, push px]]): so
    that the front's edge ends in the MIDDLE of the sleeve there (halfway between the sleeve's inner and outer edge), at most tuck
    'reach'. The front then goes under the sleeve with an overlap on both sides and never shows past the garment's edge (a fixed
    push of 40 px did, where the sleeve is a thin crescent beside the shoulder). Per side: the photo is not symmetric.
    Down to yFull; below it the plate's own taper."""
    t = Z["tuck"]; F = front_outline; ex = y0                                 # the ORIGINAL front outline: its seam, not the new cap
    def push(y, side):
        f = xspan(F, y); sl = xspan(Z["zones"]["sleeve-" + side[0]]["outline"], y)
        if not (f and sl): return None
        d = f[0] - (sl[0] + sl[1]) / 2 if side == "left" else (sl[0] + sl[1]) / 2 - f[1]       # front edge to the middle of the sleeve
        return round(max(0.0, min(t["reach"], d)), 1)
    out = {}
    for side in ("left", "right"):
        prof = []
        for y in [ex] + [float(v) for v in range(int(ex) + step, int(t["yFull"]) + 1, step)]:
            d = push(y + 0.3 if y == ex else y, side)
            if d is not None: prof.append([round(y, 1), d])
        prof.append([float(t["yFull"]), prof[-1][1]])
        out[side] = prof
    return out


def outer_run(sleeve, side, length=10.0):
    """From the sleeve outline's top vertex, the points along its OUTER edge for `length` px (outer = smaller x on the left).
    10 px: far enough to reach the real cap edge on the right; every px more moves the grid corner out and the front grid's side bulge
    (plate_checks.py, limit 5 %) goes up: 22 px gave 5.3 %, 10 px 5.0 %."""
    it = min(range(len(sleeve)), key=lambda i: sleeve[i][1]); n = len(sleeve)
    best = None
    for step in (1, -1):
        nxt = sleeve[(it + step) % n]
        outward = nxt[0] < sleeve[it][0] if side == "left" else nxt[0] > sleeve[it][0]
        if outward: best = step
    if best is None: best = 1
    out = [sleeve[it]]; acc = 0.0; i = it
    while acc < length:
        j = (i + best) % n; acc += math.dist(sleeve[i], sleeve[j]); out.append(sleeve[j]); i = j
        if j == it: break
    return out


def shoulders(plate, dry):
    zj = plate + "/zones.json"
    Z = json.load(open(zj))
    if Z.get("snapped", {}).get("shoulders"): sys.exit("shoulders: already snapped")
    M = Sampler(garment_mask(Image.open(plate + "/base.jpg").convert("RGB")))
    F = Z["zones"]["front"]; o = F["outline"]; top = F["grid"]["top"]
    idx = [i for i, p in enumerate(o) if any(abs(p[0] - q[0]) < 0.06 and abs(p[1] - q[1]) < 0.06 for q in top)]
    left = [i for i in idx if i < 20]; right = [i for i in idx if i > 20]
    assert left == list(range(0, len(left))) and right == list(range(right[0], right[-1] + 1)), "the top run is not contiguous"
    res = {}
    for name, run in (("left", left), ("right", right)):
        sl = Z["zones"]["sleeve-l" if name == "left" else "sleeve-r"]["outline"]
        ext = outer_run(sl, name)                                           # sleeve top vertex, then down its outer edge
        r = [o[i] for i in run]
        # left: far end of the sleeve's outer edge -> top vertex -> old tip -> neck corner; right: the reverse
        poly = list(reversed(ext)) + r if name == "left" else r + ext
        pts = densify(poly)
        fixed = (len(pts) - 1,) if name == "left" else (0,)                 # the neck corner stays
        new, d = snap_run(pts, M, fixed=fixed)
        res[name] = (run, new, d, ext[0][1])
        print(f"{name}: run {len(run)} -> {len(new)} points (sleeve top y {ext[0][1]:.1f}, far end y {ext[-1][1]:.1f}), move mean {sum(abs(v) for v in d) / len(d):.2f} px, max {max(abs(v) for v in d):.2f} px")
    if "--preview" in sys.argv:                                            # old run (red) and new run (green) on the photo, 5x, both shoulders
        from PIL import ImageDraw
        ph = Image.open(plate + "/base.jpg").convert("RGB"); k = 5; tiles = []
        for name, box in (("left", (370, 235, 530, 345)), ("right", (670, 235, 830, 345))):
            c = ph.crop(box).resize(((box[2] - box[0]) * k, (box[3] - box[1]) * k), Image.LANCZOS); dr = ImageDraw.Draw(c)
            run, new, _, _ = res[name]
            for pts, col in (([o[i] for i in run], (255, 0, 0)), (new, (0, 230, 0))):
                dr.line([((x - box[0]) * k, (y - box[1]) * k) for x, y in pts], fill=col, width=1)
            tiles.append(c)
        sh = Image.new("RGB", (tiles[0].width * 2 + 10, tiles[0].height), "white"); sh.paste(tiles[0], (0, 0)); sh.paste(tiles[1], (tiles[0].width + 10, 0))
        sh.save(sys.argv[sys.argv.index("--preview") + 1])
    if dry: return
    (lrun, lnew, _, lps), (rrun, rnew, _, rps) = res["left"], res["right"]
    tail = o[rrun[-1] + 1:]                                                # the old tip's leftovers (above the sleeve's top point) are dropped
    while tail and tail[0][1] < rps - 0.5: tail.pop(0)
    while tail and tail[-1][1] < lps - 0.5: tail.pop()
    mid = o[lrun[-1] + 1:rrun[0]]
    profile = tuck_profile(Z, [list(p) for p in o], min(lps, rps))          # before the outline changes
    F["outline"] = lnew + mid + rnew + tail
    F["grid"]["top"] = lnew + rnew
    # the grid's side edges start at the run's ends; old points above those are dropped
    F["grid"]["left"] = [list(lnew[0])] + [p for p in F["grid"]["left"][1:] if p[1] > lnew[0][1] + 1.0]
    F["grid"]["right"] = [list(rnew[-1])] + [p for p in F["grid"]["right"][1:] if p[1] > rnew[-1][1] + 1.0]
    # the tuck (a push of the front's sides under the sleeves) must leave the run alone: index ranges
    Z["tuck"]["exempt"] = {"outline": [[0, len(lnew) - 1], [len(lnew) + len(mid), len(lnew) + len(mid) + len(rnew) - 1]], "gridLeft": [0, 0], "gridRight": [0, 0]}
    Z["tuck"]["profile"] = profile
    Z["tuck"]["note"] += "; exempt: outline index ranges and grid-edge corners that the tuck does not move (the shoulder run); profile {left, right}: [[y, push px]] measured, the front ends in the middle of the sleeve; replaces tip / reach above yFull"
    Z.setdefault("snapped", {})["shoulders"] = "tools/snap_outline.py shoulders"
    json.dump(Z, open(zj, "w"), separators=(",", ":"))
    print("wrote", zj)


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2 or a[1] != "shoulders": sys.exit(__doc__)
    shoulders(a[0], "--dry" in a)
