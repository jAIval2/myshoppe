"""Helpers of the numeric-plan snaps (numeric steps 9-10), kept for tools/snap_edges.py (StepA step 3). Removed in StepA step 7.

The one-off commands that patched the old JSON plate files (shoulders, hem, edge-trim, trim-order) are gone with them (StepA step 1):
their results are in the plates' data (the torso's imported plate.dat; the hem's trims and trim order in tools/annotate_hem.py).
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
