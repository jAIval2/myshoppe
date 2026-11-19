"""Snap plate curves to the photographed garment edge (numeric.md steps 9-10).

usage: python3 tools/snap_outline.py <plate-dir> shoulders [--dry] [--preview out.png]
       python3 tools/snap_outline.py <plate-dir> hem [--dry]
       python3 tools/snap_outline.py <plate-dir> trim-order
       python3 tools/snap_outline.py <plate-dir> edge-trim <zone> <name> <x0> <x1> [--min-y 1250] [--extend-start px] [--extend-end px] [--dry]

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
hem (numeric.md step 10): the hem trim's centre line is derived from the front's hem edge (the grid's bottom edge): the edge
  moved inward by half the trim's width, smoothed, and cut at the inner edges of the two slit trims. The traced list wobbled
  by +-4 px around the hem's real undulation. Prints the wobble and the offset spread before and after.
trim-order (numeric.md step 10): the hem trims are drawn AFTER the slit trims (a later trim wins in id.png G). Before, the slit trim's
  strip (8 mm) overwrote the last 35 px of the hem lace at each corner: with the slits off (the default) that left bare fabric, and
  the lace stopped short of the garment's edge. Now the hem lace runs to the corner and covers the slit trim's lower end.
edge-trim (numeric.md step 10): a new trim along the bottom edge of ANOTHER zone (the side pieces of the hem view, so that the lace
  goes round the whole visible hem): the zone outline's points below --min-y between x0 and x1, ordered by x, moved inward by half the
  strip's width (the widthMm of the hem trim) and smoothed. A strip that ends at the frame ends there (x0 = 0, x1 = 1200).
Run each once on a zones.json that has not been snapped; it refuses to run twice ("snapped" key).
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


# ---- hem (step 10) ----
def resample_arc(pts, step=1.0):
    s = [0.0]
    for a, b in zip(pts, pts[1:]): s.append(s[-1] + math.dist(a, b))
    n = max(2, int(s[-1] / step)); out = []; j = 0
    for i in range(n + 1):
        t = s[-1] * i / n
        while j < len(s) - 2 and s[j + 1] < t: j += 1
        f = (t - s[j]) / ((s[j + 1] - s[j]) or 1.0)
        out.append([pts[j][0] + (pts[j + 1][0] - pts[j][0]) * f, pts[j][1] + (pts[j + 1][1] - pts[j][1]) * f])
    return out


def smooth_arc(pts, window, passes=2, keep_ends=True):
    """Moving average over `window` samples of a 1 px resampled curve; the end points stay."""
    h = max(1, window // 2); P = [list(p) for p in pts]
    for _ in range(passes):
        Q = []
        for i in range(len(P)):
            lo, hi = max(0, i - h), min(len(P), i + h + 1); k = min(i - lo, hi - 1 - i)    # symmetric window near the ends
            lo, hi = i - k, i + k + 1
            Q.append([sum(p[0] for p in P[lo:hi]) / (hi - lo), sum(p[1] for p in P[lo:hi]) / (hi - lo)])
        P = Q
    return P


def point_dist(p, poly):
    best = 1e9
    for a, b in zip(poly, poly[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]; L2 = dx * dx + dy * dy or 1.0
        t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
        best = min(best, math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy))
    return best


def trim_stats(centre, edge, r, skip=60.0):
    """(wobble, offset std, offset mean): wobble = largest distance of a point from the same curve smoothed over 31 px;
    offset = distance centre -> hem edge, the corners (x within `skip` px of an end) left out."""
    c = resample_arc(centre, 1.0); sm = smooth_arc(c, 31)
    wob = max(math.dist(a, b) for a, b in zip(c[20:-20], sm[20:-20]))
    x0, x1 = centre[0][0] + skip, centre[-1][0] - skip
    ds = [point_dist(p, edge) for p in c if x0 <= p[0] <= x1]
    m = sum(ds) / len(ds); sd = math.sqrt(sum((d - m) ** 2 for d in ds) / len(ds))
    return wob, sd, m


def hem(plate, dry):
    zj = plate + "/zones.json"; Z = json.load(open(zj))
    if Z.get("snapped", {}).get("hem"): sys.exit("hem: already derived")
    mm = Z["mmPerPx"]; T = Z["trims"]; H = Z["zones"]["front"]["grid"]["bottom"]
    r = T["hem"]["widthMm"] / mm / 2.0                                      # half the strip: the strip's outer edge is the hem edge
    wob0, sd0, m0 = trim_stats(T["hem"]["centre"], H, r)
    print(f"traced   : {len(T['hem']['centre'])} points, wobble {wob0:.2f} px, offset to the hem edge mean {m0:.1f} px (half strip {r:.1f}), std {sd0:.2f} px")
    E = resample_arc(H, 1.0)
    # normals from the edge smoothed over 24 px; the inward side is up (smaller y)
    Es = smooth_arc(E, 24)
    out = []
    for i, p in enumerate(E):
        a = Es[max(0, i - 3)]; b = Es[min(len(Es) - 1, i + 3)]
        tx, ty = b[0] - a[0], b[1] - a[1]; L = math.hypot(tx, ty) or 1.0
        nx, ny = ty / L, -tx / L
        if ny > 0: nx, ny = -nx, -ny                                        # towards smaller y: into the garment
        out.append([Es[i][0] + nx * r, Es[i][1] + ny * r])
    cen = smooth_arc(out, 24)
    # cut at the inner edges of the slit trims: slit centre x at the hem + half its width
    sl, sr = T["slit-l"]["centre"][-1], T["slit-r"]["centre"][-1]
    xl = sl[0] + T["slit-l"]["widthMm"] / mm / 2.0; xr = sr[0] - T["slit-r"]["widthMm"] / mm / 2.0
    cen = [p for p in cen if xl <= p[0] <= xr]
    # thin to a few points: Douglas-Peucker 0.1 px, then the plate's own 1 px resampling reproduces the curve
    cen = dp(cen, 0.1)
    cen = [[round(x, 1), round(y, 1)] for x, y in cen]
    wob1, sd1, m1 = trim_stats(cen, H, r)
    print(f"derived  : {len(cen)} points, wobble {wob1:.2f} px, offset mean {m1:.1f} px, std {sd1:.2f} px; from x {cen[0][0]} to {cen[-1][0]} (slit inner edges {xl:.1f}, {xr:.1f})")
    if dry: return
    T["hem"]["centre"] = cen
    T["hem"]["derived"] = {"from": "front.grid.bottom", "offsetPx": round(r, 2), "smoothPx": 24, "tool": "tools/snap_outline.py hem"}
    Z.setdefault("snapped", {})["hem"] = "tools/snap_outline.py hem"
    json.dump(Z, open(zj, "w"), separators=(",", ":")); print("wrote", zj)


def dp(pts, tol):
    """Douglas-Peucker."""
    if len(pts) < 3: return pts
    a, b = pts[0], pts[-1]; dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1.0
    k, dmax = 0, 0.0
    for i in range(1, len(pts) - 1):
        d = abs((pts[i][0] - a[0]) * dy - (pts[i][1] - a[1]) * dx) / L
        if d > dmax: k, dmax = i, d
    if dmax <= tol: return [a, b]
    return dp(pts[:k + 1], tol)[:-1] + dp(pts[k:], tol)


def edge_trim(plate, a, dry):
    zone, name, x0, x1 = a[2], a[3], float(a[4]), float(a[5])
    ymin = float(a[a.index("--min-y") + 1]) if "--min-y" in a else 1250.0
    zj = plate + "/zones.json"; Z = json.load(open(zj)); T = Z["trims"]
    if name in T: sys.exit(f"edge-trim: {name} exists")
    mm = Z["mmPerPx"]; w = T["hem"]["widthMm"]; r = w / mm / 2.0
    E = sorted([p for p in Z["zones"][zone]["outline"] if p[1] > ymin and x0 <= p[0] <= x1], key=lambda p: p[0])
    # the corners where the outline turns up (a side edge) are not hem: keep the points in order of x and drop vertical runs
    E = [p for i, p in enumerate(E) if i == 0 or abs(p[0] - E[i - 1][0]) > 0.5]
    def ext(a):                                                            # a strip that runs out of the frame: the edge is extended along its end tangent
        return float(a[a.index(f_)+1]) if f_ in a else 0.0
    f_ = "--extend-start"; e0 = ext(a); f_ = "--extend-end"; e1 = ext(a)
    def along(p, q, d):
        L = math.dist(p, q) or 1.0; return [q[0] + (q[0] - p[0]) / L * d, q[1] + (q[1] - p[1]) / L * d]
    if e0: E = [along(E[1], E[0], e0)] + E
    if e1: E = E + [along(E[-2], E[-1], e1)]
    Er = resample_arc(E, 1.0); Es = smooth_arc(Er, 24)
    out = []
    for i, p in enumerate(Er):
        a_ = Es[max(0, i - 3)]; b_ = Es[min(len(Es) - 1, i + 3)]
        tx, ty = b_[0] - a_[0], b_[1] - a_[1]; L = math.hypot(tx, ty) or 1.0
        nx, ny = ty / L, -tx / L
        if ny > 0: nx, ny = -nx, -ny
        out.append([Es[i][0] + nx * r, Es[i][1] + ny * r])
    cen = [[round(x, 1), round(y, 1)] for x, y in dp(smooth_arc(out, 24), 0.1)]
    print(f"{name}: {len(E)} edge points -> centre {len(cen)} points from {cen[0]} to {cen[-1]} (half strip {r:.1f} px, strip {2 * r:.0f} px)")
    if dry: return
    T[name] = {"order": T["hem"]["order"], "widthMm": w, "type": T["hem"].get("type", "edging"), "centre": cen, "derived": {"from": f"{zone}.outline bottom", "offsetPx": round(r, 2), "tool": "tools/snap_outline.py edge-trim"}}
    json.dump(Z, open(zj, "w"), separators=(",", ":")); print("wrote", zj)


def trim_order(plate, dry):
    zj = plate + "/zones.json"; Z = json.load(open(zj)); T = Z["trims"]
    hems = [k for k in T if k == "hem" or k.startswith("hem-")]
    order = [k for k in T if k not in hems] + hems
    if list(T) == order: print("trim-order: already in order", order); return
    print("trim-order:", list(T), "->", order)
    if dry: return
    Z["trims"] = {k: T[k] for k in order}
    json.dump(Z, open(zj, "w"), separators=(",", ":")); print("wrote", zj)


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2 or a[1] not in ("shoulders", "hem", "edge-trim", "trim-order"): sys.exit(__doc__)
    if a[1] == "edge-trim": edge_trim(a[0], a, "--dry" in a)
    elif a[1] == "trim-order": trim_order(a[0], "--dry" in a)
    else: (shoulders if a[1] == "shoulders" else hem)(a[0], "--dry" in a)
