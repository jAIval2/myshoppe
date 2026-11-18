"""Review crops: zoom one area of an image, or put the same area of several images side by side.

usage: python3 tools/zoom.py <out.png> x0,y0,x1,y1 <image> [image ...] [--scale 2] [--nearest]

One image  -> the area enlarged (2x by default). Use it for annotate.png / check.png review.
Several    -> the same area of each image, side by side with a red gap. Use it to compare
              a base with an annotated image, or a plate before and after a change.
--nearest keeps hard pixels (for checker / id maps); the default is LANCZOS.
"""
import sys
from PIL import Image

args = sys.argv[1:]
scale = float(args[args.index("--scale") + 1]) if "--scale" in args else 2.0
resample = Image.NEAREST if "--nearest" in args else Image.LANCZOS
args = [a for i, a in enumerate(args) if a not in ("--scale", "--nearest") and (i == 0 or args[i - 1] != "--scale")]
out, box, paths = args[0], tuple(map(int, args[1].split(","))), args[2:]
tiles = []
for p in paths:
    c = Image.open(p).convert("RGB").crop(box)
    tiles.append(c.resize((round(c.width * scale), round(c.height * scale)), resample))
gap = 8
sheet = Image.new("RGB", (sum(t.width for t in tiles) + gap * (len(tiles) - 1), max(t.height for t in tiles)), (220, 30, 30))
x = 0
for t in tiles:
    sheet.paste(t, (x, 0))
    x += t.width + gap
sheet.save(out)
print(out, sheet.size)
