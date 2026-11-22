"""The review set of a plate (StepA step 0): fixed crops of the render along its edges, on one sheet.

usage: python3 silhouette/checks/edge_crops.py <canvas.png> <plate-dir> <out.png> [--photo <off-canvas.png>] [--box 40] [--zoom 3] [--every 150]

One crop at each landmark of the plate, and one every 150 px along each FREE edge (silhouette/checks/plate_edges.py), so the set is computed
from the plate and needs no file of its own. Each tile is a pair: the photo (left) and the render (right), the same box of
40 x 40 plate px, magnified 3x with nearest-neighbour pixels (at a 1200 x 1600 canvas that is 3 screen px per plate px: more
than a phone at 2x shows). The tile's label is the landmark, or the zone and the distance along the edge in px.
Make the canvas with silhouette/checks/cdp_shot.mjs at stage=600 (see silhouette/checks/fringe.py); --photo is the same view with fabric=off.
"""
import math, sys
import os
sys.path[:0] = [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), d) for d in ("pipeline", "checks", "views")]
from PIL import Image, ImageDraw
import plate_edges as PE

a = sys.argv[1:]
canvas, pd, out = a[0], a[1].rstrip("/"), a[2]
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
BOX, ZOOM, EVERY = int(opt("--box", 40)), int(opt("--zoom", 3)), float(opt("--every", 150))
W, H = PE.W, PE.H
R = Image.open(canvas).convert("RGB")
if R.size != (W, H): R = R.resize((W, H), Image.BILINEAR)
P = Image.open(opt("--photo")).convert("RGB") if opt("--photo") else Image.open(pd + "/base.jpg").convert("RGB")
if P.size != (W, H): P = P.resize((W, H), Image.BILINEAR)
Z = PE.load(pd)


def points():
    pts = [(k, v[0], v[1]) for k, v in Z.get("landmarks", {}).items()]
    C = PE.classify(Z)
    for zn, S in C.items():
        for ri, run in enumerate(PE.runs(S, "free", min_len=20)):
            n = len(run)
            k = max(1, round(n / EVERY))
            for j in range(k):
                i = int((j + 0.5) * n / k)
                pts.append((f"{zn} {ri}:{i}", run[i][0], run[i][1]))
    return pts


def crop(img, x, y):
    x0, y0 = int(round(x - BOX / 2)), int(round(y - BOX / 2))
    x0, y0 = max(0, min(W - BOX, x0)), max(0, min(H - BOX, y0))
    return img.crop((x0, y0, x0 + BOX, y0 + BOX)).resize((BOX * ZOOM, BOX * ZOOM), Image.NEAREST)


pts = points()
tw, th, lab = 2 * BOX * ZOOM + 4, BOX * ZOOM, 14
cols = max(1, min(4, int(2400 // tw)))
rows = math.ceil(len(pts) / cols)
sheet = Image.new("RGB", (cols * (tw + 8), rows * (th + lab + 8)), (255, 255, 255))
dr = ImageDraw.Draw(sheet)
for i, (name, x, y) in enumerate(pts):
    c, r = i % cols, i // cols
    ox, oy = c * (tw + 8), r * (th + lab + 8)
    dr.text((ox + 2, oy), f"{name}  ({x:.0f}, {y:.0f})", fill=(0, 0, 0))
    sheet.paste(crop(P, x, y), (ox, oy + lab))
    sheet.paste(crop(R, x, y), (ox + BOX * ZOOM + 4, oy + lab))
sheet.save(out, optimize=True)
print(f"{len(pts)} crops -> {out} ({sheet.width} x {sheet.height})")
