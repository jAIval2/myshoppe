"""Print RGB, HSV, luminance and chromaticity at points. Use it to set mask thresholds
(garment vs wall vs form, lace vs paper, gap vs fold) before you trust a scan.

usage: python3 silhouette/measure/sample.py <image> x,y [x,y ...] [--blur 1.5] [--name label=x,y ...]
"""
import sys
from PIL import Image, ImageFilter

args = sys.argv[1:]
blur = float(args[args.index("--blur") + 1]) if "--blur" in args else 0.0
args = [a for i, a in enumerate(args) if a != "--blur" and (i == 0 or args[i - 1] != "--blur")]
im = Image.open(args[0]).convert("RGB")
if blur:
    im = im.filter(ImageFilter.GaussianBlur(blur))
hsv, L = im.convert("HSV"), im.convert("L")
print(f"{'point':>18}  {'RGB':>15}  {'HSV':>15}  {'L':>3}  chroma r/g/b")
for a in args[1:]:
    label, _, xy = a.rpartition("=")
    x, y = map(int, xy.split(","))
    c = im.getpixel((x, y)); s = sum(c) or 1
    print(f"{(label or '') + f' ({x},{y})':>18}  {str(c):>15}  {str(hsv.getpixel((x, y))):>15}  {L.getpixel((x, y)):>3}  "
          + "/".join(f"{v / s:.3f}" for v in c))
