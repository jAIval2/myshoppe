"""Throwaway: prepare the two test swatches for the shader.

fabric-sage-640.png (2048^2): remove sparkle, de-light (divide by large blur), 1024^2 JPEG
lace-pearl-640.png (3168x1344): crop to the lace band, key the white background to alpha
"""
import sys
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageMath

src_dir, out_dir, dbg = sys.argv[1:4]

# ---- fabric
f = Image.open(f"{src_dir}/fabric-sage-640.png").convert("RGB")
box = (1860, 1760, 2048, 1960)  # sparkle mark, bottom right
w, h = box[2] - box[0], box[3] - box[1]
patch = f.crop((box[0] - 320, box[1], box[2] - 320, box[3]))
feather = Image.new("L", (w, h), 0)
ImageDraw.Draw(feather).rectangle((14, 14, w - 1, h - 14), fill=255)
f.paste(patch, box[:2], feather.filter(ImageFilter.GaussianBlur(7)))

L = f.convert("L")
mean = sum(i * c for i, c in enumerate(L.histogram())) / (f.size[0] * f.size[1])
low = L.filter(ImageFilter.GaussianBlur(90)).convert("F")
ratio = ImageMath.lambda_eval(lambda a: a["low"], low=low)  # keep as F image
chans = []
for c in f.split():
    chans.append(ImageMath.lambda_eval(
        lambda a: a["c"] * (mean / (a["low"] + 1.0)), c=c.convert("F"), low=low
    ).convert("L"))
flat = Image.merge("RGB", chans).resize((1024, 1024), Image.LANCZOS)

# seamless: the half-offset copy is continuous across the tile border (its own
# border is the original's centre). Near each edge we cut over to that copy along a
# minimum-error seam, found by dynamic programming inside a narrow band (BAND px).
# The cut follows places where both copies already agree, so it needs no wide blend.
BAND, MIN_OFF = 64, 8
N = flat.size[0]
shifted = ImageChops.offset(flat, N // 2, N // 2)
pre_blend = flat


def seam_mask_top(a, b):
    """L mask, 255 above the seam (use b there). Seam row per column in [MIN_OFF, BAND]."""
    n = a.size[0]
    d = ImageChops.difference(a, b).convert("L")
    dp_ = d.load()
    rows = BAND - MIN_OFF + 1
    cost = [[(dp_[x, MIN_OFF + r] ** 2) for r in range(rows)] for x in range(n)]
    acc = [cost[0][:]]
    back = [[0] * rows]
    for x in range(1, n):
        prev, cur, bk = acc[-1], [0] * rows, [0] * rows
        for r in range(rows):
            best, bi = prev[r], r
            if r > 0 and prev[r - 1] < best: best, bi = prev[r - 1], r - 1
            if r < rows - 1 and prev[r + 1] < best: best, bi = prev[r + 1], r + 1
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
for k in range(4):  # top, left, bottom, right: rotate so each edge is "top"
    ang = 90 * k
    m = seam_mask_top(flat.rotate(ang), shifted.rotate(ang))
    mask = ImageChops.lighter(mask, m.rotate(-ang))
mask = mask.filter(ImageFilter.GaussianBlur(1.5))
flat = Image.composite(shifted, flat, mask)
flat.save(f"{out_dir}/fabric-sage-1024.jpg", quality=92)
flat.resize((256, 256)).save(f"{dbg}/fabric-flat-preview.png")
tile3 = Image.new("RGB", (N * 3, N * 3))
for i in range(3):
    for j in range(3):
        tile3.paste(flat, (i * N, j * N))
tile3.resize((1536, 1536), Image.LANCZOS).save(f"{dbg}/fabric-tile3x3.png")
tile3.crop((N - 400, N - 400, N + 400, N + 400)).save(f"{dbg}/fabric-tile-corner.png")  # a tile corner, full res
band_px = sum(1 for v in mask.getdata() if v > 8)
print(f"swatch band area {band_px / N / N:.1%} of tile")
import statistics
def sharp(im): return statistics.pvariance(list(im.convert("L").filter(ImageFilter.FIND_EDGES).getdata()))
print("sharpness pre-blend", round(sharp(pre_blend), 1), "post", round(sharp(flat), 1))
if len(sys.argv) > 4 and sys.argv[4] == "fabric":
    sys.exit(0)

# ---- lace
lace = Image.open(f"{src_dir}/lace-pearl-640.png").convert("RGB")
lace = lace.crop((0, 360, 3168, 1050))  # heading edge .. pearls
r, g, b = lace.split()
# background is near-white and neutral; lace is cream (blue channel lower).
# alpha from "how much darker or warmer than the white background"
# paper and its shadows are neutral grey; lace and pearls are warm cream.
# key on warmth (red - blue) only, so paper shadows do not become white halos.
warm = ImageMath.lambda_eval(
    lambda a: ((a["r"] - a["b"]) - 9.0) * 14.0, r=r.convert("F"), b=b.convert("F")
).convert("L")
# pearls are neutral but clearly darker than the paper (~205 vs ~241)
dark = ImageMath.lambda_eval(
    lambda a: (226.0 - a["l"]) * 10.0, l=lace.convert("L").convert("F")
).convert("L")
alpha = ImageChops.lighter(warm, dark).filter(ImageFilter.GaussianBlur(0.6))
lace_rgba = lace.copy()
lace_rgba.putalpha(alpha)
lace_rgba = lace_rgba.resize((2048, round(2048 * lace.size[1] / lace.size[0])), Image.LANCZOS)
lace_rgba.save(f"{out_dir}/lace-pearl-2048.png", optimize=True)
prev = Image.new("RGB", lace_rgba.size, (60, 90, 70))
prev.paste(lace_rgba, (0, 0), lace_rgba)
prev.resize((1024, lace_rgba.size[1] // 2)).save(f"{dbg}/lace-keyed-preview.png")
print("fabric", flat.size, "lace", lace_rgba.size, "lace aspect", round(lace_rgba.size[0] / lace_rgba.size[1], 3))
