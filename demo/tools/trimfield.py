"""The trim field (StepA extension, step L1): a lace laid on the garment edge it is sewn to. Pillow-free; plate.js `trimElements`
builds the same elements and maps.js draws them (tools/maps_check.py compares the two).

A trim's `line` is its garment edge between its anchors (make_plate.py derive_trims), with `side` = the sign that turns the line's
left normal onto the trim's zone. The line is resampled every SPACING_PX px. Each point gets a SMOOTH normal: the normal of the chord
over +-NORMAL_MM (30) mm of the line (the lace's across direction follows the edge's run, not every small wave of a drape). For a pixel q:
  t   the distance in px from the edge along the normal (interpolated along each segment): + inward (on the trim's zone), - outward
      (the overhang of an edging lace)
  s   the cloth length in cm along the edge to q's foot point, measured in the zone's fabric frame (the length of the line in (u, v)),
      0 at the anchor: the frame's u = 0 ("cf", the default), or an end ("from", "to")
Each segment is one ELEMENT (inner; outer too for an edging trim): the strip between the normals at its two ends. A pixel's foot point
on the segment solves (q - P(tau)) x N(tau) = 0, N interpolated (the arithmetic of the fabric frame, plateframe.project). Neighbouring
strips share their normal, so s and t are continuous: no wedge on the outer side of a bend, no overlap on its inner side. Where strips
still overlap (two trims of one zone meeting at a corner; a fold beyond the radius of a tight bend) the smallest |t| wins: a mitre.
Ends: an "open" end (the default: the loop goes on out of sight, or a mitre partner meets it) carries the field on along the end's
direction for the whole band, inward only (the garment's outline cuts it); a "cut" end (the slit top) is square, along its normal.
The overhang exists only along the line itself.
"""
import math

import plateframe

LACE_IN_MM = 56.0      # the band inward: the widest lace (53.4 mm, paisley) and a margin
LACE_OUT_MM = 8.0      # the band outward: the deepest overhang (edgeDepth 0.123 x 53.4 mm = 6.6 mm) and a margin
SPACING_PX = 2.0       # the line resampled every 2 px
NORMAL_MM = 30.0       # the normal of a point: the chord over +-30 mm of the line
S_OFF_CM, T_OFF_MM = 64.0, 64.0          # the packing (maps.js): u = s + 64 cm, v = (t mm + 64) / 10 cm
SLIT_OFF_CM = {"slit-l": 32.0, "slit-r": 96.0}   # the slits' field: u = s + 32 (slit-l) or s + 96 (slit-r)


def resample(pts, n):
    """n + 1 points, equal arc length along the polyline (make_plate.resample, Plate.resample)."""
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total = sum(seg) or 1
    out, i, acc = [], 0, 0.0
    for k in range(n + 1):
        target = total * k / n
        while i < len(seg) - 1 and acc + seg[i] < target:
            acc += seg[i]
            i += 1
        f = (target - acc) / seg[i] if seg[i] else 0
        f = max(0.0, min(1.0, f))
        out.append((pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f))
    return out


def py_round(x):
    return math.floor(x + 0.5)


def points(line, F, mm, side, anchor):
    """The resampled line: (points, s cm from the anchor, unit normals onto the zone, length cm)."""
    L = sum(math.dist(a, b) for a, b in zip(line, line[1:]))
    n = max(2, py_round(L / SPACING_PX))
    P = resample(line, n)
    uv = [plateframe.uv(F, mm, x, y) for x, y in P]
    s = [0.0]
    for a, b in zip(uv, uv[1:]):
        s.append(s[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    s0 = anchor_s(s, uv, anchor)
    k = max(1, py_round(NORMAL_MM / mm / (L / n)))
    N = []
    for i in range(n + 1):
        a, b = P[max(0, i - k)], P[min(n, i + k)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        l = math.hypot(tx, ty) or 1.0
        N.append((-ty / l * side, tx / l * side))
    return P, [v - s0 for v in s], N, s[-1]


def anchor_s(s, uv, anchor):
    """s of the anchor (cm, on the scale of s): an end, or where the frame's u crosses 0 (extrapolated from the nearer end)."""
    if anchor == "from": return 0.0
    if anchor == "to": return s[-1]
    for i in range(len(s) - 1):
        u0, u1 = uv[i][0], uv[i + 1][0]
        if u0 == 0.0: return s[i]
        if u0 * u1 < 0: return s[i] + (s[i + 1] - s[i]) * u0 / (u0 - u1)
    if uv[-1][0] == 0.0: return s[-1]
    k, j = (0, min(4, len(s) - 1)) if abs(uv[0][0]) <= abs(uv[-1][0]) else (len(s) - 1, max(0, len(s) - 5))
    du = uv[j][0] - uv[k][0]
    rate = (s[j] - s[k]) / du if abs(du) > 1e-9 else 0.0
    return s[k] - uv[k][0] * rate


def extended(P, S, N, cut, tin):
    """(points, s, normals, outer allowed per segment): open ends carried on by the band + 2 px, square to their normals."""
    P, S, N, ok = list(P), list(S), list(N), [True] * (len(P) - 1)
    E = tin + 2.0
    for end in ("from", "to"):
        if end in cut: continue
        k, j = (0, 1) if end == "from" else (len(P) - 1, len(P) - 2)
        n = N[k]
        tx, ty = (n[1], -n[0])                               # a tangent (either way along the line)
        if (P[k][0] - P[j][0]) * tx + (P[k][1] - P[j][1]) * ty < 0: tx, ty = -tx, -ty   # pointing out of the line at this end
        d = math.dist(P[k], P[j]) or 1.0
        rate = (S[k] - S[j]) / d
        q, sq = (P[k][0] + tx * E, P[k][1] + ty * E), S[k] + rate * E
        if end == "from":
            P.insert(0, q); S.insert(0, sq); N.insert(0, n); ok.insert(0, False)
        else:
            P.append(q); S.append(sq); N.append(n); ok.append(False)
    return P, S, N, ok


def elements(P, S, N, ok, tout):
    """The elements of one trim: (part, a, b, na, nb, sa, sb); part +1 inner, -1 outer."""
    els = []
    for j in range(len(P) - 1):
        if math.dist(P[j], P[j + 1]) < 1e-6: continue
        els.append((1, P[j], P[j + 1], N[j], N[j + 1], S[j], S[j + 1]))
        if ok[j] and tout > 0: els.append((-1, P[j], P[j + 1], N[j], N[j + 1], S[j], S[j + 1]))
    return els


def value(el, qx, qy, tin, tout):
    """(s, t) of the element at pixel (qx, qy), or None where it does not accept the pixel. The roots as maps.js TRIM_FS."""
    part, a, b, na, nb, sa, sb = el
    ex, ey = b[0] - a[0], b[1] - a[1]
    dnx, dny = nb[0] - na[0], nb[1] - na[1]
    wx, wy = qx - a[0], qy - a[1]
    A = -(ex * dny - ey * dnx)
    B = (wx * dny - wy * dnx) - (ex * na[1] - ey * na[0])
    C = wx * na[1] - wy * na[0]
    roots = []
    d = B * B - 4.0 * A * C
    if d >= 0.0:
        qq = -0.5 * (B + (1.0 if B >= 0.0 else -1.0) * math.sqrt(d))
        if abs(qq) > 1e-12: roots.append(C / qq)
        if abs(A) > 1e-9: roots.append(qq / A)
    best = None
    for tau in roots:
        if tau < -1e-6 or tau > 1.0 + 1e-6: continue
        px, py = a[0] + tau * ex, a[1] + tau * ey
        nx, ny = na[0] + tau * dnx, na[1] + tau * dny
        r = ((qx - px) * nx + (qy - py) * ny) / (math.hypot(nx, ny) or 1e-9)
        if part > 0:
            if r < 0.0 or r > tin: continue
        elif r >= 0.0 or r < -tout: continue
        if best is None or abs(r) < abs(best[1]): best = (sa + (sb - sa) * min(1.0, max(0.0, tau)), r)
    return best


def triangles(el, tin, tout):
    """Two triangles that hold every pixel the element accepts (1 px margin along the line and across)."""
    part, a, b, na, nb, _, _ = el
    L = math.dist(a, b)
    tx, ty = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    lo, hi = (-1.0, tin + 1.0) if part > 0 else (1.0, -(tout + 1.0))
    A0 = (a[0] - tx + na[0] * lo, a[1] - ty + na[1] * lo); B0 = (b[0] + tx + nb[0] * lo, b[1] + ty + nb[1] * lo)
    B1 = (b[0] + tx + nb[0] * hi, b[1] + ty + nb[1] * hi); A1 = (a[0] - tx + na[0] * hi, a[1] - ty + na[1] * hi)
    return [(A0, B0, B1), (A0, B1, A1)]


def trim_elements(t, F, mm):
    """Everything the field needs of one trim t (the plate's trim with line, side, type, anchor, cut) on its zone's frame F:
    (elements, tin px, tout px, cloth length cm)."""
    tin, tout = LACE_IN_MM / mm, (LACE_OUT_MM / mm if t.get("type") == "edging" else 0.0)
    P, S, N, length = points([tuple(p) for p in t["line"]], F, mm, t["side"], t.get("anchor", "cf"))
    P, S, N, ok = extended(P, S, N, t.get("cut", []), tin)
    return elements(P, S, N, ok, tout), tin, tout, length


def scan(tri, W, H):
    """The pixels (x, y) whose centres lie in a triangle (inclusive), clipped to the plate."""
    ys = [p[1] for p in tri]
    for y in range(max(0, math.ceil(min(ys))), min(H - 1, math.floor(max(ys))) + 1):
        xs = []
        for (x1, y1), (x2, y2) in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            if (y1 <= y <= y2) or (y2 <= y <= y1):
                if y1 == y2: xs += [x1, x2]
                else: xs.append(x1 + (x2 - x1) * (y - y1) / (y2 - y1))
        if xs:
            for x in range(max(0, math.ceil(min(xs))), min(W - 1, math.floor(max(xs))) + 1):
                yield x, y


def rasterise(groups, W, H, zid, zorder, occl):
    """The field of a list of zone groups (back to front): [(zone id, [(trim id, elements, tin, tout), ...]), ...].
    zid(x, y): the zone of the pixel (0 = none); zorder: {zone id: order}; occl(x, y): an object in front.
    The inner part of a trim only on its own zone; the overhang where there is no zone, its own, or one behind it, and no object in
    front. Within a group the smallest |t| wins; a later group overwrites. -> {pixel index: (trim id, s cm, t px)}."""
    out = {}
    for zone, trims in groups:
        best = {}
        own = zorder.get(zone, 0)
        for tid, els, tin, tout in trims:
            for el in els:
                part = el[0]
                seen = set()
                for tri in triangles(el, tin, tout):
                    for x, y in scan(tri, W, H):
                        i = y * W + x
                        if i in seen: continue
                        seen.add(i)
                        z = zid(x, y)
                        if part > 0:
                            if z != zone: continue
                        elif not (z == 0 or z == zone or zorder.get(z, 99) < own) or occl(x, y):
                            continue
                        r = value(el, x, y, tin, tout)
                        if r is None: continue
                        b = best.get(i)
                        if b is None or abs(r[1]) < abs(b[2]):
                            best[i] = (tid, r[0], r[1])
        out.update(best)
    return out
