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

# seamless: blend with a half-offset copy. The copy is continuous across the
# tile border, so it takes over near the edges; the original keeps the centre.
N = flat.size[0]
shifted = ImageChops.offset(flat, N // 2, N // 2)
ramp = Image.new("L", (N, N))
rp = ramp.load()
for y in range(N):
    for x in range(N):
        d = min(x, N - 1 - x, y, N - 1 - y) / (N / 2)  # 0 at the border, 1 at the centre
        rp[x, y] = int(255 * min(1.0, d * 2.2))
flat = Image.composite(flat, shifted, ramp)
flat.save(f"{out_dir}/fabric-sage-1024.jpg", quality=92)
flat.resize((256, 256)).save(f"{dbg}/fabric-flat-preview.png")

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
