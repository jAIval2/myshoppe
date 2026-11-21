"""halfway.md step 5.4: does the live neck trim (the 24-point centre line the shader gets) match the baked trim of the plate?
For every baked neck-trim px (id G = 1) the live u (cm along the centre line) and v (0..1 across) are computed as the
shader does, and compared with the plate's uv_trim (in memory). Errors in plate px.

usage: python3 tools/trim_match.py <plate-dir> <sent.json>    sent.json = {"nc": [[x, y] x 24]} (cdp_shot --eval __studio.neckSent())
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_plate

pd, sent = sys.argv[1], json.load(open(sys.argv[2]))
M = make_plate.maps_of(pd)
P = M["plate"]
R, mm, tw = P["uvRangeCm"], P["mmPerPx"], P["trims"]["neck"]["widthMm"] / P["mmPerPx"]
c = sent["nc"]
uvt = M["uvt"].load()
idm = M["id"]
W, H = idm.size
idp = idm.load()
du, dv, miss = [], [], 0
for y in range(H):
    for x in range(W):
        if idp[x, y][1] != 1:
            continue
        p = uvt[x, y]
        u = ((p[0] << 4) | (p[2] >> 4)) / 4095 * R
        v = ((p[1] << 4) | (p[2] & 15)) / 4095
        best, acc = (1e9, 0, 0, 0, 0), 0.0
        for i in range(len(c) - 1):
            a, b = c[i], c[i + 1]
            ab = (b[0] - a[0], b[1] - a[1])
            sl = math.hypot(*ab)
            tr = ((x - a[0]) * ab[0] + (y - a[1]) * ab[1]) / (sl * sl)
            t = max(0.0, min(1.0, tr))
            q = (a[0] + ab[0] * t, a[1] + ab[1] * t)
            d = math.dist((x, y), q)
            if d < best[0]:
                best = (d, acc + sl * t + 0.95, i, tr, q, ab)       # + the page's 0.95 px (plate quad convention)
            acc += sl
        d, arc, i, tr, q, ab = best
        if (i == 0 and tr < 0) or (i == len(c) - 2 and tr > 1):
            miss += 1
            continue
        sl = math.hypot(*ab)
        nx, ny = ab[1] / sl, -ab[0] / sl
        vl = 0.5 + ((x - q[0]) * nx + (y - q[1]) * ny) / tw
        du.append((arc * mm / 10 - u) * 10 / mm)           # px along (signed)
        dv.append((vl - v) * tw)                        # px across (signed)
mean_u, mean_v = sum(du) / len(du), sum(dv) / len(dv)
du = sorted(abs(d) for d in du); dv = sorted(abs(d) for d in dv)
q = lambda l, f: l[min(len(l) - 1, int(f * len(l)))]
print(f"  signed mean: along {mean_u:+.2f} px, across {mean_v:+.2f} px")
print(f"{pd}: {len(du)} trim px compared, {miss} past the strip ends")
print(f"  along (u): median {q(du, .5):.2f} px, 95 % {q(du, .95):.2f} px, max {du[-1]:.2f} px")
print(f"  across (v): median {q(dv, .5):.2f} px, 95 % {q(dv, .95):.2f} px, max {dv[-1]:.2f} px  (v is stored in steps of 1/{max(8, math.ceil(tw))} of the width)")
