"""Flat fabric photo -> de-lit, seamless 1024 px tile for the fabric shader.

usage: python3 tools/prep_fabric.py <in> <out.jpg> [preview_3x3.png] [--no-delight]

1. De-light: divide by a large blur (removes the light gradient of the photo), keep the mean colour.
2. Resize to 1024 x 1024.
3. Seamless: near each edge, cut over to the half-offset copy along a minimum-error seam,
   inside a band of 8..64 px (the method of prep_swatches.py, step 2 of plan/upscale.md).
The real width of the tile (cm) is set in testing.html (FABRICS[..].repeatCm).
"""
import sys
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageMath

src, out = sys.argv[1], sys.argv[2]
prev = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else None
f = Image.open(src).convert("RGB")

if "--no-delight" not in sys.argv:
    L = f.convert("L")
    mean = sum(i * c for i, c in enumerate(L.histogram())) / (f.size[0] * f.size[1])
    low = L.filter(ImageFilter.GaussianBlur(max(f.size) * 0.045)).convert("F")
    f = Image.merge("RGB", [ImageMath.lambda_eval(lambda a: a["c"] * (mean / (a["low"] + 1.0)),
                                                  c=c.convert("F"), low=low).convert("L") for c in f.split()])
flat = f.resize((1024, 1024), Image.LANCZOS)

BAND, MIN_OFF = 64, 8
N = flat.size[0]
shifted = ImageChops.offset(flat, N // 2, N // 2)


def seam_mask_top(a, b):
    """L mask, 255 above the seam (use b there). Seam row per column in [MIN_OFF, BAND]."""
    n = a.size[0]
    dp_ = ImageChops.difference(a, b).convert("L").load()
    rows = BAND - MIN_OFF + 1
    cost = [[dp_[x, MIN_OFF + r] ** 2 for r in range(rows)] for x in range(n)]
    acc, back = [cost[0][:]], [[0] * rows]
    for x in range(1, n):
        prev_, cur, bk = acc[-1], [0] * rows, [0] * rows
        for r in range(rows):
            best, bi = prev_[r], r
            if r > 0 and prev_[r - 1] < best: best, bi = prev_[r - 1], r - 1
            if r < rows - 1 and prev_[r + 1] < best: best, bi = prev_[r + 1], r + 1
            cur[r], bk[r] = best + cost[x][r], bi
        acc.append(cur); back.append(bk)
    r = min(range(rows), key=lambda i: acc[-1][i])
    path = [0] * n
    for x in range(n - 1, -1, -1):
        path[x] = r
        r = back[x][r]
    m = Image.new("L", (n, n), 0)
    ImageDraw.Draw(m).polygon([(0, 0), (n - 1, 0)] + [(x, MIN_OFF + path[x]) for x in range(n - 1, -1, -1)], fill=255)
    return m


mask = Image.new("L", (N, N), 0)
for k in range(4):                      # top, left, bottom, right
    ang = 90 * k
    mask = ImageChops.lighter(mask, seam_mask_top(flat.rotate(ang), shifted.rotate(ang)).rotate(-ang))
flat = Image.composite(shifted, flat, mask.filter(ImageFilter.GaussianBlur(1.5)))
flat.save(out, quality=92)
if prev:
    t = Image.new("RGB", (N * 3, N * 3))
    for i in range(3):
        for j in range(3):
            t.paste(flat, (i * N, j * N))
    t.resize((900, 900), Image.LANCZOS).save(prev)
print(out, flat.size)
