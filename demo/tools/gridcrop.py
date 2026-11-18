"""Gridded crop of source.png in SOURCE px. usage: gridcrop.py <source> <out> x0 y0 x1 y1 [step] [contrast] [scale]"""
import sys
from PIL import Image, ImageEnhance, ImageDraw
src, out = Image.open(sys.argv[1]).convert("RGB"), sys.argv[2]
x0, y0, x1, y1 = map(int, sys.argv[3:7])
step = int(sys.argv[7]) if len(sys.argv) > 7 else 50
contrast = float(sys.argv[8]) if len(sys.argv) > 8 else 2.2
scale = float(sys.argv[9]) if len(sys.argv) > 9 else 1.0
c = ImageEnhance.Contrast(src.crop((x0, y0, x1, y1))).enhance(contrast)
c = c.resize((int(c.width * scale), int(c.height * scale)), Image.LANCZOS)
d = ImageDraw.Draw(c)
major = step * 2
for x in range((x0 // step + 1) * step, x1, step):
    X = (x - x0) * scale
    d.line([(X, 0), (X, c.height)], fill=(255, 0, 0) if x % major == 0 else (255, 170, 170))
    if x % major == 0: d.text((X + 2, 2), str(x), fill=(200, 0, 0))
for y in range((y0 // step + 1) * step, y1, step):
    Y = (y - y0) * scale
    d.line([(0, Y), (c.width, Y)], fill=(0, 0, 255) if y % major == 0 else (170, 170, 255))
    if y % major == 0: d.text((2, Y + 2), str(y), fill=(0, 0, 200))
c.save(out)
