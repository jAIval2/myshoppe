"""Free edges snapped to the photo (StepA step 3). A module of the build (silhouette/pipeline/make_plate.py); Pillow only. Deterministic.

usage: python3 silhouette/pipeline/snap_edges.py <plate-dir> [--dry] [--preview <png>] [--json]     a report (and a preview); --dry writes nothing
                                                                                    (this tool never writes: make_plate.py does)
As a module: snap(P, base) -> report. P (the plate data of an annotate script) is changed in place: the points of every free and cut
edge, the corners where edges meet, the seams' ends, the grid points and landmarks that sat on a moved corner.

For every FREE or CUT edge (the occluders are chains of these edges, so they follow):
  1. samples every 2 px along the edge, each with the outward normal (out of the zone that uses the edge);
  2. on each normal a local colour model: the mean colour from 3 to 8 px inside and from 3 to 8 px outside (where that finds no
     contrast: from 1.5 to 4 px, for a gap narrower than 8 px), and the sub-pixel 50 %
     crossing of the projection between the two (bilinear colour, 0.25 px steps, within +-8 px; the crossing nearest the edge);
     a WEAK sample (inside and outside closer than 14 levels: a fold against a like background) keeps the measured position (its
     target is 0); so does a sample that a later zone COVERS, or that lies OVER another zone (4 px outward is that zone's fabric: a
     sleeve's edge over the body, white over white): those are counted apart, they are not contour against the background;
  3. a robust smooth fit of the displacement along the edge (Whittaker: data term + lambda x the squared second difference, lambda 4
     at 2 px spacing); samples more than 1.2 px off the fit are dropped and the fit repeated (3 rounds); then the colour model is
     taken again at the fitted edge and steps 2-3 run once more;
  4. points every 2 px, thinned to 0.05 px (Douglas-Peucker).
Corners: the corner of two snapped edges is the mean of their snapped ends; on the image border it stays on the border; a seam that
meets it gets the new end, and its points within 12 px move with it (a linear taper; never its other end: a seam shorter than 12 px
keeps the junction at its far end, 2026-11-23). Seams are not moved otherwise.
Report per edge: samples, weak share and spans, dropped samples, and the accuracy of the fit against the crossings (median, 95 %, max).
"""
import math, os, sys

LAMBDA, CUT, WEAK, STEP = 4.0, 1.2, 14.0, 2.0


class RGB:
    def __init__(self, im):
        self.w, self.h = im.size
        self.d = list(im.convert("RGB").getdata())

    def at(self, x, y):
        x = min(max(x, 0.0), self.w - 1.001); y = min(max(y, 0.0), self.h - 1.001)
        x0, y0 = int(x), int(y); fx, fy = x - x0, y - y0; w = self.w; d = self.d
        a, b, c, e = d[y0 * w + x0], d[y0 * w + x0 + 1], d[(y0 + 1) * w + x0], d[(y0 + 1) * w + x0 + 1]
        return tuple((a[k] * (1 - fx) + b[k] * fx) * (1 - fy) + (c[k] * (1 - fx) + e[k] * fx) * fy for k in range(3))


def resample(pts, step):
    s = [0.0]
    for a, b in zip(pts, pts[1:]): s.append(s[-1] + math.dist(a, b))
    n = max(2, int(round(s[-1] / step)))
    out, j = [], 0
    for i in range(n + 1):
        t = s[-1] * i / n
        while j < len(s) - 2 and s[j + 1] < t: j += 1
        f = (t - s[j]) / ((s[j + 1] - s[j]) or 1.0)
        out.append([pts[j][0] + (pts[j + 1][0] - pts[j][0]) * f, pts[j][1] + (pts[j + 1][1] - pts[j][1]) * f])
    return out


def normals(P, k=2):
    out = []
    for i in range(len(P)):
        a, b = P[max(0, i - k)], P[min(len(P) - 1, i + k)]
        tx, ty = b[0] - a[0], b[1] - a[1]; L = math.hypot(tx, ty) or 1.0
        out.append((-ty / L, tx / L))
    return out


def inside(pt, poly):
    c = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > pt[1]) != (y2 > pt[1]) and pt[0] < (x2 - x1) * (pt[1] - y1) / (y2 - y1) + x1: c = not c
    return c


def whittaker(y, w, lam):
    """argmin sum w (y - z)^2 + lam sum (z[i-1] - 2 z[i] + z[i+1])^2: a banded (pentadiagonal) system, Cholesky."""
    n = len(y)
    if n < 3: return list(y)
    A = [[0.0] * 3 for _ in range(n)]          # A[i][k] = M[i][i + k], k = 0, 1, 2 (symmetric band)
    for i in range(n): A[i][0] = w[i]
    for i in range(1, n - 1):                  # D row i: (i-1, i, i+1) = (1, -2, 1)
        idx, co = (i - 1, i, i + 1), (1.0, -2.0, 1.0)
        for p in range(3):
            for q in range(p, 3):
                A[idx[p]][idx[q] - idx[p]] += lam * co[p] * co[q]
    L = [[0.0] * 3 for _ in range(n)]          # L[i][k] = L[i][i - k]
    for i in range(n):
        for k in (2, 1):
            j = i - k
            if j < 0: continue
            s = A[j][k] - sum(L[i][m] * L[j][m - k] for m in range(k + 1, 3) if j - (m - k) >= 0)
            L[i][k] = s / L[j][0]
        s = A[i][0] - sum(L[i][m] ** 2 for m in (1, 2) if i - m >= 0)
        L[i][0] = math.sqrt(max(s, 1e-12))
    z = [0.0] * n
    b = [w[i] * y[i] for i in range(n)]
    for i in range(n):                         # L z' = b
        z[i] = (b[i] - sum(L[i][k] * z[i - k] for k in (1, 2) if i - k >= 0)) / L[i][0]
    for i in range(n - 1, -1, -1):             # L^T z = z'
        z[i] = (z[i] - sum(L[i + k][k] * z[i + k] for k in (1, 2) if i + k < n)) / L[i][0]
    return z


def dp(pts, tol):
    if len(pts) < 3: return pts
    a, b = pts[0], pts[-1]; dx, dy = b[0] - a[0], b[1] - a[1]; n = math.hypot(dx, dy) or 1.0
    k, dm = 0, 0.0
    for i in range(1, len(pts) - 1):
        d = abs((pts[i][0] - a[0]) * dy - (pts[i][1] - a[1]) * dx) / n
        if d > dm: k, dm = i, d
    return [a, b] if dm <= tol else dp(pts[:k + 1], tol)[:-1] + dp(pts[k:], tol)


def chain_points(P, chain):
    out = []
    for name, d in chain:
        pts = P["edges"][name]["points"]
        pts = pts if d > 0 else pts[::-1]
        out += pts[1:] if out and out[-1] == pts[0] else pts
    return out


def crossings(img, S, N, covered):
    """Per sample: (displacement t of the 50 % crossing or None, weak?)."""
    res = []
    for (x, y), (nx, ny), cov in zip(S, N, covered):
        if cov: res.append((None, True)); continue
        for win in ((3, 4, 5, 6, 7, 8), (1.5, 2, 2.5, 3, 3.5, 4)):     # the narrow window: a gap narrower than 8 px
            cin = [sum(c) / 6 for c in zip(*[img.at(x - t * nx, y - t * ny) for t in win])]
            cout = [sum(c) / 6 for c in zip(*[img.at(x + t * nx, y + t * ny) for t in win])]
            dv = [a - b for a, b in zip(cin, cout)]; dd = sum(v * v for v in dv)
            if math.sqrt(dd) >= WEAK: break
        if math.sqrt(dd) < WEAK: res.append((None, True)); continue
        f = lambda t: sum((c - o) * v for c, o, v in zip(img.at(x + t * nx, y + t * ny), cout, dv)) / dd
        best, prev = None, None
        t = -8.0
        while t <= 8.0 + 1e-9:
            v = f(t)
            if prev is not None and (prev[1] - 0.5) * (v - 0.5) <= 0 and prev[1] != v:
                tc = prev[0] + (prev[1] - 0.5) / (prev[1] - v) * (t - prev[0])
                if best is None or abs(tc) < abs(best): best = tc
            prev = (t, v); t += 0.25
        res.append((best, best is None))
    return res


def fit(d, use):
    """Robust Whittaker fit of the displacements d (None = no crossing) where use: weak samples pull to 0."""
    y = [v if (v is not None and u) else 0.0 for v, u in zip(d, use)]
    w = [1.0] * len(d)
    for _ in range(3):
        z = whittaker(y, w, LAMBDA)
        w = [0.0 if (v is not None and u and abs(v - zz) > CUT) else 1.0 for v, u, zz in zip(d, use, z)]
    return z, w


def snap_edge(img, pts, outward_sign, covered_fn):
    S = resample(pts, STEP)
    N = [(nx * outward_sign, ny * outward_sign) for nx, ny in normals(S)]
    cov = [covered_fn(p, n) for p, n in zip(S, N)]
    total = [0.0] * len(S)
    for rnd in range(2):                                    # the colour model again at the fitted edge
        cur = [[x + t * nx, y + t * ny] for (x, y), (nx, ny), t in zip(S, N, total)]
        cr = crossings(img, cur, N, cov)
        d = [c[0] for c in cr]
        use = [not c[1] for c in cr]
        z, w = fit(d, use)
        total = [t + zz for t, zz in zip(total, z)]
    # accuracy against the crossings of the last round (the samples that were used and kept)
    errs = sorted(abs(v - zz) for v, u, zz, ww in zip(d, use, z, w) if u and ww > 0 and v is not None)
    weak = [(not u) and not c for u, c in zip(use, cov)]
    out = [[x + t * nx, y + t * ny] for (x, y), (nx, ny), t in zip(S, N, total)]
    return out, {"samples": len(S), "weak": sum(weak), "covered": sum(cov), "dropped": sum(1 for u, ww in zip(use, w) if u and ww == 0),
                 "median": errs[len(errs) // 2] if errs else 0.0, "p95": errs[int(len(errs) * 0.95)] if errs else 0.0,
                 "max": errs[-1] if errs else 0.0, "meanMove": sum(abs(t) for t in total) / len(total),
                 "weakSpans": spans(S, weak)}


def spans(S, flags):
    out, i = [], 0
    while i < len(flags):
        if flags[i]:
            j = i
            while j + 1 < len(flags) and flags[j + 1]: j += 1
            if j - i >= 2: out.append([round(S[i][0]), round(S[i][1]), round(S[j][0]), round(S[j][1]), (j - i + 1) * STEP])
            i = j + 1
        else: i += 1
    return out


def snap(P, base):
    import platedat
    img = RGB(base)
    W, H = P["viewBox"]
    E, Z = P["edges"], P["zones"]
    O = {zn: platedat.outline(P, zn) for zn in Z}
    users = {n: [zn for zn, z in Z.items() if any(e == n for e, _ in z["outline"])] for n in E}
    report = {}
    old = {n: [list(p) for p in e["points"]] for n, e in E.items()}
    for n, e in E.items():
        if e["type"] not in ("free", "cut"): continue
        zn = users[n][0]
        poly = O[zn]
        S = resample(e["points"], 6.0)
        Nn = normals(S)
        votes = sum(1 if not inside((x + 2 * nx, y + 2 * ny), poly) else -1 for (x, y), (nx, ny) in zip(S, Nn))
        sign = 1.0 if votes >= 0 else -1.0
        later = [O[u] for u in Z if Z[u]["order"] > Z[zn]["order"]]
        others = [O[u] for u in Z if u != zn]
        covered = lambda p, n_, later=later, others=others: (any(inside(p, q) for q in later)
                                                           or any(inside((p[0] + 4 * n_[0], p[1] + 4 * n_[1]), q) for q in others))
        pts, rep = snap_edge(img, e["points"], sign, covered)
        e["points"] = pts
        report[n] = rep
    # corners: every end point of an edge is a node; group the old ends by position
    nodes = {}
    for n in E:
        for end in (0, -1):
            key = tuple(old[n][end])
            nodes.setdefault(key, []).append((n, end))
    moved = {}
    for key, members in nodes.items():
        snapped = [E[n]["points"][end] for n, end in members if E[n]["type"] in ("free", "cut")]
        if not snapped: continue
        nx_, ny_ = sum(p[0] for p in snapped) / len(snapped), sum(p[1] for p in snapped) / len(snapped)
        if abs(key[0]) < 0.05 or abs(key[0] - W) < 0.05: nx_ = key[0]           # a corner on the border stays on it
        if abs(key[1]) < 0.05 or abs(key[1] - H) < 0.05: ny_ = key[1]
        new = [nx_, ny_]
        moved[key] = new
        for n, end in members:
            pts = E[n]["points"]
            if E[n]["type"] in ("free", "cut"):
                pts[end] = list(new)
            else:                                               # a seam or a frame edge: the end moves, its first 12 px follow (taper)
                dx, dy = new[0] - pts[end][0], new[1] - pts[end][1]
                seq = range(len(pts)) if end == 0 else range(len(pts) - 1, -1, -1)
                far = len(pts) - 1 if end == 0 else 0           # a seam shorter than 12 px keeps its other end (a junction of 3 zones)
                acc, prev = 0.0, None
                for i in seq:
                    if prev is not None: acc += math.dist(pts[i], pts[prev])
                    if acc > 12 or i == far: break
                    f = 1 - acc / 12
                    pts[i] = [pts[i][0] + dx * f, pts[i][1] + dy * f]
                    prev = i
    for n, e in E.items():                                   # 2 px points -> thinned; whole curves in plate units
        if e["type"] in ("free", "cut"): e["points"] = [[round(x, 2), round(y, 2)] for x, y in dp(e["points"], 0.05)]
        else: e["points"] = [[round(x, 2), round(y, 2)] for x, y in e["points"]]
    # grid points and landmarks that sat on a moved corner follow it
    def remap(pts):
        return [list(moved.get(tuple(p), p)) for p in pts]
    for z in Z.values():
        if "grid" in z: z["grid"] = {k: remap(v) for k, v in z["grid"].items()}
    for k, v in list(P.get("landmarks", {}).items()):
        if tuple(v) in moved: P["landmarks"][k] = [round(c, 2) for c in moved[tuple(v)]]
    return report


def summary(report):
    lines = []
    for n, r in report.items():
        ok = r["median"] <= 0.3 and r["p95"] <= 0.75 and r["max"] <= 1.5 and r["weak"] <= 0.05 * (r["samples"] - r["covered"])
        lines.append(f"{'PASS' if ok else 'FAIL'}  {n:22} {r['samples']:4} samples  move {r['meanMove']:.2f} px  fit vs crossing median {r['median']:.2f} "
                     f"95 % {r['p95']:.2f} max {r['max']:.2f} px  weak {100 * r['weak'] / max(1, r['samples'] - r['covered']):.1f} %  covered / over {r['covered']}  dropped {r['dropped']}")
    return lines


if __name__ == "__main__":
    sys.path[:0] = [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), d) for d in ("pipeline", "checks", "views")]
    import json, make_plate
    a = sys.argv[1:]
    pd = a[0].rstrip("/")
    P, base, mod = make_plate.source(pd)
    rep = snap(P, base)
    print("\n".join(summary(rep)))
    if "--json" in a: print(json.dumps(rep))
