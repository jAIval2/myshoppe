"""Lace photo on plain paper -> horizontal lace band with alpha, for the trim shader.

usage: python3 tools/prep_lace.py <in> <out.webp> <preview.png> [--flip] [--cut-bottom 0.12]

1. Paper colour = median of the image border.
2. Lace mask = chromaticity distance to the paper (hue, not brightness: shadows stay paper) (blurred), on a small copy.
3. Band angle = principal axis of the mask (PCA). Rotate so the band is horizontal.
4. Crop: rows where the band is (mask coverage > 15 %), columns where every such row is inside the photo.
5. Alpha = colour distance to the paper, smooth ramp. Lace net becomes semi-transparent.
Convention: the decorative edge (loops, scallops, pearls) at the BOTTOM. --flip turns the band 180 deg.
Output height 446 px, like lace-pearl-2048.webp.
"""
import math, statistics, sys
from PIL import Image, ImageFilter, ImageMath, ImageChops

src, out, prev = sys.argv[1:4]
flip = "--flip" in sys.argv
im = Image.open(src).convert("RGB")
W, H = im.size

# 1. paper colour from the border
border = [im.getpixel((x, y)) for x in range(0, W, 8) for y in (2, H - 3)] + \
         [im.getpixel((x, y)) for y in range(0, H, 8) for x in (2, W - 3)]
paper = tuple(statistics.median(c[i] for c in border) for i in range(3))


def distance(img):
    """Chromaticity distance to the paper, x 765. Brightness is ignored, so the paper's own
    shadow (same hue, darker) stays background; sand / sage / gold lace differ in hue."""
    r, g, b = [c.convert("F") for c in img.split()]
    s0 = sum(paper)
    pr, pg, pb = paper[0] / s0, paper[1] / s0, paper[2] / s0
    return ImageMath.lambda_eval(
        lambda a: (((a["r"] / (a["r"] + a["g"] + a["b"] + 1.0) - pr) ** 2
                    + (a["g"] / (a["r"] + a["g"] + a["b"] + 1.0) - pg) ** 2
                    + (a["b"] / (a["r"] + a["g"] + a["b"] + 1.0) - pb) ** 2) ** 0.5) * 765.0,
        r=r, g=g, b=b)


def to8(f):                                   # float distance -> 8-bit, clipped at 255
    return ImageMath.lambda_eval(lambda a: a["f"] * (a["f"] < 255) + 255 * (a["f"] >= 255), f=f).convert("L")


# 2. mask on a small copy
small = im.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(2))
d = to8(distance(small)).point(lambda v: 255 if v > 8 else 0)
pts = [(x, y) for y in range(d.height) for x in range(d.width) if d.getpixel((x, y))]
mx = sum(p[0] for p in pts) / len(pts)
my = sum(p[1] for p in pts) / len(pts)
sxx = sum((p[0] - mx) ** 2 for p in pts); syy = sum((p[1] - my) ** 2 for p in pts)
sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)
ang = 0.5 * math.degrees(math.atan2(2 * sxy, sxx - syy))   # band direction, image coords (y down)

# 3. rotate so the band is horizontal (PIL rotates counter-clockwise for positive angles)
rot = im.rotate(ang, resample=Image.BICUBIC, expand=True, fillcolor=(0, 0, 0))
valid = Image.new("L", im.size, 255).rotate(ang, resample=Image.NEAREST, expand=True, fillcolor=0)
dist = distance(rot)
mask = to8(dist).point(lambda v: 255 if v > 8 else 0)
mask = ImageChops.multiply(mask, valid)

# 4. rows of the band
RW, RH = rot.size
cover = [sum(1 for x in range(0, RW, 4) if mask.getpixel((x, y))) / (RW / 4) for y in range(RH)]
peak = max(cover)
rows = [y for y in range(RH) if cover[y] > 0.15 * peak]
y0, y1 = rows[0], rows[-1]
pad = round((y1 - y0) * 0.04)
y0, y1 = max(0, y0 - pad), min(RH - 1, y1 + pad)
# columns where every band row is inside the original photo
cols = [x for x in range(RW) if valid.getpixel((x, y0)) and valid.getpixel((x, y1))]
x0, x1 = cols[0] + 4, cols[-1] - 4
span = x1 - x0
x0, x1 = x0 + span // 10, x1 - span // 10          # middle 80 %: no curled or cut ends
# cut the shadow strip: the paper's shadow under the lace picks up a little warm colour.
# Keep rows down to the last one where strong lace colour (dist > 16) covers > 8 % of the row.
strong = to8(dist).point(lambda v: 255 if v > 16 else 0)
cov = [sum(1 for x in range(x0, x1, 3) if strong.getpixel((x, y))) / ((x1 - x0) / 3) for y in range(y0, y1)]
last = max(i for i, c in enumerate(cov) if c > 0.08)
first = min(i for i, c in enumerate(cov) if c > 0.08)
y0, y1 = y0 + max(0, first - 3), y0 + min(len(cov), last + 3)
cut = next((float(sys.argv[i + 1]) for i, v in enumerate(sys.argv) if v == "--cut-bottom"), 0.0)
y1 = y1 - round((y1 - y0) * cut)               # manual cut of the remaining shadow strip, measured on the preview
band = rot.crop((x0, y0, x1, y1))
a = dist.crop((x0, y0, x1, y1))

# 5. alpha: smooth ramp on the colour distance
alpha = to8(a).point(lambda v: max(0, min(255, (v - 4) * 24))).filter(ImageFilter.GaussianBlur(0.6))
band.putalpha(alpha)
if flip:
    band = band.rotate(180)
h = 446
band = band.resize((round(band.width * h / band.height), h), Image.LANCZOS)
band.save(out, quality=90, method=6)

pv = Image.new("RGB", band.size, (60, 90, 70))
pv.paste(band, (0, 0), band)
pv.save(prev)
print(f"{src.split('/')[-1]}: paper {tuple(round(c) for c in paper)}, angle {ang:.1f} deg, band {band.size}, aspect {band.width / band.height:.2f}")
