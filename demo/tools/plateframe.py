"""The fabric frame of a zone (StepA step 4): fabric coordinates (u, v) in cm for any point of the plate. Pure Python, no Pillow.
plate.js frameUV() is the same arithmetic (tools/frame_check.mjs compares the two).

A frame (stored in plate.dat, zones.<name>.frame):
  axis     the warp line through the zone, a polyline in plate px (the centre front; a sleeve's or a panel's centre line), top -> bottom
  L        the axis length (px);  s0: the anchor's position along the axis (px);  vMm: v at the anchor (mm)
  thetaDeg the half angle of the visible arc of the cylinder the zone is unrolled from
  half     {"left": [c0, c1, c2, c3], "right": [...]}: the half width (px) on each side, a cubic in t = s / L (clamped to 0..1)
  sag      {"c": c, "s1": s1}: the weft lines curve like the hem (or the cuff): s is corrected by c r^2, fully at s1 (the hem's position
           on the axis), not at all at the anchor, linearly between (0 when there is no hem or cuff)
For a point q: s = its position along the axis (the foot of the perpendicular; past the ends, along the end segments' lines), r = its
signed distance (+ to the right of the axis, walking down it). With h = half(side, s):
  u = R asin(r / R'), R = h / sin(theta), r' = r sin(theta) / h ... i.e. u_px = (h / sin th) asin((r / h) sin th) for |r| <= h,
      continued linearly past the silhouette (the slope there: 1 / cos th);  u_cm = u_px * mmPerPx / 10
  v_cm = ((s - c r^2 w(s)) - s0) * mmPerPx / 10 + vMm / 10,   w = clamp((s - s0) / (s1 - s0), 0, 1)
"""
import math


def _normals(axis):
    """Unit normals (to the right walking down) at the vertices: the mean of the two segments' normals (an end: its segment's)."""
    seg = []
    for a, b in zip(axis, axis[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1e-9
        seg.append((dy / L, -dx / L))
    out = []
    for i in range(len(axis)):
        ns = [seg[j] for j in (i - 1, i) if 0 <= j < len(seg)]
        x, y = sum(n[0] for n in ns), sum(n[1] for n in ns); L = math.hypot(x, y) or 1e-9
        out.append((x / L, y / L))
    return out


_NCACHE = {}


def project(axis, q):
    """(s, r): position along the axis (px) and signed distance (+ right of the walking direction). Continuous across the vertices:
    on segment i the normal is interpolated between the vertex normals, and t solves (q - P(t)) x N(t) = 0 (a quadratic), so the
    lines of constant s fan smoothly round a bend (no jump, no wedge). Past the ends the end segments run on straight."""
    key = id(axis)
    if key not in _NCACHE or _NCACHE[key][0] is not axis: _NCACHE[key] = (axis, _normals(axis))
    N = _NCACHE[key][1]
    n = len(axis)
    best = None
    acc = 0.0
    for i in range(n - 1):
        a, b = axis[i], axis[i + 1]
        ex, ey = b[0] - a[0], b[1] - a[1]
        L = math.hypot(ex, ey) or 1e-9
        na, nb = N[i], N[i + 1]
        if i == 0: na = ((ey / L), (-ex / L))           # the end segments: their own normal at the free end (straight run-on)
        if i == n - 2: nb = ((ey / L), (-ex / L))
        wx, wy = q[0] - a[0], q[1] - a[1]
        dnx, dny = nb[0] - na[0], nb[1] - na[1]
        # (w - t e) x (na + t dn) = 0  ->  A t^2 + B t + C = 0
        A = -(ex * dny - ey * dnx)
        B = (wx * dny - wy * dnx) - (ex * na[1] - ey * na[0])
        C = wx * na[1] - wy * na[0]
        ts = []                                             # the stable roots (no cancellation when A is small: a near-straight segment)
        disc = B * B - 4 * A * C
        if disc >= 0:
            qq = -0.5 * (B + math.copysign(math.sqrt(disc), B))
            if abs(qq) > 1e-15: ts.append(C / qq)
            if abs(A) > 1e-12: ts.append(qq / A)
        lo = -math.inf if i == 0 else -1e-9
        hi = math.inf if i == n - 2 else 1 + 1e-9
        for t in ts:
            if not (lo <= t <= hi): continue
            px, py = a[0] + t * ex, a[1] + t * ey
            nx, ny = na[0] + t * dnx, na[1] + t * dny
            nl = math.hypot(nx, ny) or 1e-9
            r = ((q[0] - px) * nx + (q[1] - py) * ny) / nl
            if best is None or abs(r) < abs(best[1]) - 1e-12:
                best = (acc + t * L, r)
        acc += L
    if best is None:                                     # (not reached for a smooth axis) the nearest vertex
        i = min(range(n), key=lambda k: (q[0] - axis[k][0]) ** 2 + (q[1] - axis[k][1]) ** 2)
        s = sum(math.dist(axis[k], axis[k + 1]) for k in range(i))
        best = (s, (q[0] - axis[i][0]) * N[i][0] + (q[1] - axis[i][1]) * N[i][1])
    return best


def cubic(c, t):
    t = min(1.0, max(0.0, t))
    return c[0] + t * (c[1] + t * (c[2] + t * c[3]))


def uv(F, mm, x, y):
    s, r = project(F["axis"], (x, y))
    h = max(4.0, cubic(F["half"]["right" if r >= 0 else "left"], s / F["L"]))
    th = math.radians(F["thetaDeg"])
    st, ct = math.sin(th), math.cos(th)
    a = abs(r)
    if a <= h:
        up = (h / st) * math.asin(a / h * st)
    else:
        up = (h / st) * th + (a - h) / ct
    if r < 0: up = -up
    sg = F.get("sag") or {}
    c, s1 = sg.get("c", 0.0), sg.get("s1", F["s0"])
    w = 0.0 if s1 == F["s0"] else min(1.0, max(0.0, (s - F["s0"]) / (s1 - F["s0"])))
    sc = s - c * r * r * w
    return up * mm / 10.0, ((sc - F["s0"]) * mm + F.get("vMm", 0.0)) / 10.0


# ---- fitting (the build)
def lstsq(xs, ys, deg, ws=None):
    n = deg + 1
    ws = ws or [1.0] * len(xs)
    A = [[sum(w * x ** (i + j) for x, w in zip(xs, ws)) for j in range(n)] for i in range(n)]
    b = [sum(w * y * x ** i for x, y, w in zip(xs, ys, ws)) for i in range(n)]
    for i in range(n):
        piv = max(range(i, n), key=lambda r_: abs(A[r_][i])); A[i], A[piv] = A[piv], A[i]; b[i], b[piv] = b[piv], b[i]
        for r_ in range(i + 1, n):
            f = A[r_][i] / A[i][i]
            for c in range(i, n): A[r_][c] -= f * A[i][c]
            b[r_] -= f * b[i]
    c = [0.0] * n
    for i in range(n - 1, -1, -1): c[i] = (b[i] - sum(A[i][k] * c[k] for k in range(i + 1, n))) / A[i][i]
    return c


def axis_length(axis):
    return sum(math.dist(a, b) for a, b in zip(axis, axis[1:]))


def point_at(axis, s):
    acc = 0.0
    for a, b in zip(axis, axis[1:]):
        L = math.dist(a, b)
        if acc + L >= s or b is axis[-1]:
            f = (s - acc) / (L or 1e-9)
            return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f), ((b[0] - a[0]) / (L or 1e-9), (b[1] - a[1]) / (L or 1e-9))
        acc += L


def ray_hit(o, d, segs, maxd=3000.0):
    """The nearest hit of the ray o + t d (t > 0) on the segments [(a, b, tag)]: (t, tag) or None."""
    best = None
    for a, b, tag in segs:
        ex, ey = b[0] - a[0], b[1] - a[1]
        den = d[0] * ey - d[1] * ex
        if abs(den) < 1e-12: continue
        wx, wy = a[0] - o[0], a[1] - o[1]
        t = (wx * ey - wy * ex) / den
        u = (wx * d[1] - wy * d[0]) / den
        if t > 1e-6 and -1e-9 <= u <= 1 + 1e-9 and t < maxd and (best is None or t < best[0]): best = (t, tag)
    return best


def fit_half(axis, segs, skip_top=0.0, step=8.0):
    """{left, right}: cubic half widths from rays perpendicular to the axis to the zone's outline. A side whose rays mostly end on a
    frame edge (the image border is not a silhouette) takes the other side's profile. skip_top: share of the axis at its top that is
    left out (a sleeve cap: the profile continues the sleeve's own)."""
    L = axis_length(axis)
    out, info = {}, {}
    samples = {"left": [], "right": []}
    n = max(8, int(L / step))
    for i in range(n + 1):
        s = L * i / n
        if s < skip_top * L: continue
        p, (tx, ty) = point_at(axis, s)
        for side, d in (("right", (ty, -tx)), ("left", (-ty, tx))):
            h = ray_hit(p, d, segs)
            if h: samples[side].append((s / L, h[0], h[1]))
    for side in ("left", "right"):
        good = [(t, h) for t, h, tag in samples[side] if tag != "frame"]
        info[side] = (len(good), len(samples[side]))
        if len(good) >= max(6, 0.3 * len(samples[side])):
            out[side] = [round(c, 6) for c in lstsq([t for t, _ in good], [h for _, h in good], 3)]
    for side, other in (("left", "right"), ("right", "left")):
        if side not in out: out[side] = out.get(other) or [100.0, 0.0, 0.0, 0.0]
    return out, info


def fit_sag(axis, pts, s0):
    """{c, s1} from an edge that is one weft line (the hem, a cuff): s = a + b r + c r^2 over its middle 80 %; the slant b is not
    used (a cut across the grain), the curvature c is."""
    sr = [project(axis, p) for p in pts]
    rmax = max(abs(r) for _, r in sr) or 1.0
    mid = [(s, r) for s, r in sr if abs(r) <= 0.8 * rmax]
    if len(mid) < 4: return {"c": 0.0, "s1": s0}
    a, b, c = lstsq([r for _, r in mid], [s for s, _ in mid], 2)
    return {"c": round(c, 9), "s1": round(a, 3)}


if __name__ == "__main__":
    # python3 tools/plateframe.py --samples <plate-dir> <out.json> [n]: n points per zone (default 10,000 in all), in each zone's box
    # + 16 px, deterministic, with the Python (u, v): the input of tools/frame_check.mjs
    import json, os, random, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import platedat
    a = sys.argv[1:]
    if not a or a[0] != "--samples": sys.exit("usage: python3 tools/plateframe.py --samples <plate-dir> <out.json> [n]")
    P = platedat.read(a[1])
    zones = [n for n, z in P["zones"].items() if z.get("frame", {}).get("L")]
    n = int(a[3]) if len(a) > 3 else 10000
    rng = random.Random(1)
    out = {"mmPerPx": P["mmPerPx"], "points": []}
    for zn in zones:
        o = platedat.outline(P, zn)
        x0, x1 = min(p[0] for p in o) - 16, max(p[0] for p in o) + 16
        y0, y1 = min(p[1] for p in o) - 16, max(p[1] for p in o) + 16
        for _ in range(n // len(zones)):
            x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
            out["points"].append([zn, x, y, *uv(P["zones"][zn]["frame"], P["mmPerPx"], x, y)])
    json.dump(out, open(a[2], "w"))
    print(len(out["points"]), "points ->", a[2])
