"""Closure in the RENDER (StepA step 0): photo garment that the page still shows, and the bright rim along the free edges.

usage: python3 silhouette/checks/fringe.py <canvas.png> <plate-dir> [--photo <off-canvas.png>] [--debug <out.png>] [--json]

  canvas   a render with a dark fabric and no lace: node silhouette/checks/cdp_shot.mjs <out> <port> "view=<v>&fabric=mocha&trims=none&stage=600"
           (stage 600 at DPR 2 = a 1200 x 1600 canvas: one canvas px = one plate px). Another size is resampled to the plate.
  --photo  the same view with fabric=off (the photo as the page draws it). Without it, base.jpg.

Counts (plate px):
  uncovered  pixels where the photo is garment (HSV saturation < 24 of 255, 3 x 3 median: the rule of plate_invariants.py) and the
             render still shows the photo (every channel within 4 levels), within 10 px of rendered fabric; the openings of the
             plate's "invariants" are left out. Reported: the count, the share of the rendered fabric, and the pieces wider than 1 px
             (what survives a 2 x 2 erosion), with their boxes.
  rim        along every FREE edge (silhouette/checks/plate_edges.py), each 1 px: the brightest luminance from 1.5 px inside to 3.5 px outside
             the outline, against the luminance 4 px inside and 6 px outside. A rim sample is brighter than both by more than 8
             levels, and that brightest pixel has the garment's colour (saturation < 24 of 255, as the closure rule): the original
             garment's white or grey, not a light band of the wall or the form. Reported: the share of the free-edge length, and where.
  halo       (StepA step 6) along the same edges, where the photo's own step across the edge (4 px in to 4 px out) is >= 12 levels: the
             render minus the photo, 1.5-3.5 px outside the edge, as a share of that step. Median and 95 % (limit 10 %).
"""
import json, math, sys
import os
sys.path[:0] = [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), d) for d in ("pipeline", "checks", "views")]
from PIL import Image, ImageChops, ImageDraw, ImageFilter
import plate_edges as PE

a = sys.argv[1:]
canvas, pd = a[0], a[1].rstrip("/")
opt = lambda k: a[a.index(k) + 1] if k in a else None
W, H = PE.W, PE.H
R = Image.open(canvas).convert("RGB")
if R.size != (W, H): R = R.resize((W, H), Image.BOX if R.width > W else Image.BILINEAR)
P = Image.open(opt("--photo")).convert("RGB") if opt("--photo") else Image.open(pd + "/base.jpg").convert("RGB")
if P.size != (W, H): P = P.resize((W, H), Image.BOX if P.width > W else Image.BILINEAR)
Z = PE.load(pd)
inv = Z.get("invariants", {})

# ---- uncovered garment
G = P.convert("HSV").split()[1].point(lambda v: 255 if v < 24 else 0).filter(ImageFilter.MedianFilter(3))
d = ImageChops.difference(R, P).split()
D = ImageChops.lighter(ImageChops.lighter(d[0], d[1]), d[2])
same = D.point(lambda v: 255 if v <= 4 else 0)
fabric = D.point(lambda v: 255 if v > 4 else 0)
near = fabric.filter(ImageFilter.MaxFilter(21))
U = ImageChops.multiply(ImageChops.multiply(G, same), near)
dr = ImageDraw.Draw(U)
for box in inv.get("openings", []): dr.rectangle(box, fill=0)
area = sum(fabric.histogram()[1:])
unc = sum(U.histogram()[1:])
# 2 x 2 erosion: a pixel stays when it and its right, lower and lower-right neighbours are all uncovered (offset() wraps at the
# border; a piece there is rare and counted the same)
E = ImageChops.multiply(ImageChops.multiply(U, ImageChops.offset(U, -1, 0)), ImageChops.multiply(ImageChops.offset(U, 0, -1), ImageChops.offset(U, -1, -1)))
wide = sum(E.histogram()[1:])

# pieces wider than 1 px: connected groups of the eroded pixels, with their boxes
ep = E.load()
seen, pieces = set(), []
for y in range(H):
    for x in range(W):
        if ep[x, y] and (x, y) not in seen:
            st, n, bx = [(x, y)], 0, [x, y, x, y]
            seen.add((x, y))
            while st:
                u, v = st.pop(); n += 1
                bx = [min(bx[0], u), min(bx[1], v), max(bx[2], u), max(bx[3], v)]
                for du in (-1, 0, 1):
                    for dv in (-1, 0, 1):
                        q = (u + du, v + dv)
                        if 0 <= q[0] < W and 0 <= q[1] < H and ep[q] and q not in seen: seen.add(q); st.append(q)
            pieces.append((n, bx))
pieces.sort(key=lambda t: -t[0])

# ---- rim along the free edges
L = R.convert("L")
Lp = L.load()
SP = R.convert("HSV").split()[1].load()
LP = P.convert("L").load()


def lum_p(x, y):
    x = min(max(x, 0.0), W - 1.001); y = min(max(y, 0.0), H - 1.001)
    x0, y0 = int(x), int(y); fx, fy = x - x0, y - y0
    return (LP[x0, y0] * (1 - fx) + LP[x0 + 1, y0] * fx) * (1 - fy) + (LP[x0, y0 + 1] * (1 - fx) + LP[x0 + 1, y0 + 1] * fx) * fy


def lum(x, y):
    x = min(max(x, 0.0), W - 1.001); y = min(max(y, 0.0), H - 1.001)
    x0, y0 = int(x), int(y); fx, fy = x - x0, y - y0
    return (Lp[x0, y0] * (1 - fx) + Lp[x0 + 1, y0] * fx) * (1 - fy) + (Lp[x0, y0 + 1] * (1 - fx) + Lp[x0 + 1, y0 + 1] * fx) * fy


C = PE.classify(Z)
free_n = rim_n = 0
rim_pts, by_zone, halos = [], {}, []
for zn, S in C.items():
    zf = zr = 0
    for (x, y, nx, ny, t) in S:
        if t != "free": continue
        zf += 1
        le, sb = max((lum(x + nx * s, y + ny * s), s) for s in [k * 0.5 for k in range(-3, 8)])
        li, lo = lum(x - 4 * nx, y - 4 * ny), lum(x + 6 * nx, y + 6 * ny)
        qx, qy = int(min(max(x + nx * sb, 0), W - 1)), int(min(max(y + ny * sb, 0), H - 1))
        garmentlike = SP[qx, qy] < 24                    # the brightest pixel has the garment's colour (not a light band of the form)
        if le > li + 8 and le > lo + 8 and garmentlike:
            zr += 1; rim_pts.append((x, y))
        step = abs(lum_p(x - 4 * nx, y - 4 * ny) - lum_p(x + 4 * nx, y + 4 * ny))
        if step >= 12:                                  # halo: the render against the photo just outside the edge, per the photo's own step
            d = sum(lum(x + t * nx, y + t * ny) - lum_p(x + t * nx, y + t * ny) for t in (1.5, 2.5, 3.5)) / 3
            halos.append(abs(d) / step)
    free_n += zf; rim_n += zr
    by_zone[zn] = (zf, zr)

res = {"uncovered": unc, "uncoveredPct": round(100 * unc / max(1, area), 4), "fabricPx": area, "wider1px": wide,
       "pieces": [{"px": n, "box": b} for n, b in pieces[:12]], "freeEdgePx": free_n, "rimPx": rim_n,
       "rimPct": round(100 * rim_n / max(1, free_n), 2), "rimByZone": {k: {"free": f, "rim": r} for k, (f, r) in by_zone.items()}}
print(f"uncovered garment {unc} px = {res['uncoveredPct']:.3f} % of the fabric ({area} px); wider than 1 px: {wide} px in {len(pieces)} pieces"
      + (": " + ", ".join(f"{n} px at {b}" for n, b in pieces[:6]) if pieces else ""))
print(f"rim: {rim_n} of {free_n} free-edge px = {res['rimPct']:.2f} %  (" + ", ".join(f"{k} {r}/{f}" for k, (f, r) in by_zone.items()) + ")")
halos.sort()
if halos:
    res["haloMedian"], res["halo95"] = round(halos[len(halos) // 2], 4), round(halos[int(len(halos) * 0.95)], 4)
    print(f"halo: the render minus the photo 1.5-3.5 px outside the free edges, per the photo's own step: median {100 * res['haloMedian']:.1f} %, 95 % {100 * res['halo95']:.1f} % ({len(halos)} samples; limit 10 %)")
if "--json" in a: print(json.dumps(res))
if opt("--debug"):
    ov = P.copy(); ov.paste((255, 0, 255), mask=U)
    dd = ImageDraw.Draw(ov)
    for x, y in rim_pts: dd.point((x, y), fill=(0, 230, 255))
    ov.save(opt("--debug"))
