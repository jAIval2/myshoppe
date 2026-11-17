"""Throwaway: torso-base.png -> exact 3:4, sparkle removed, 1200x1600 JPEG."""
import sys
from PIL import Image, ImageDraw, ImageFilter

src, out, corner = sys.argv[1:4]
im = Image.open(src).convert("RGB")  # 1792 x 2400

# 1. sparkle mark (bottom right wall): cover with wall from 200 px to the left
box = (1600, 2200, 1780, 2390)
w, h = box[2] - box[0], box[3] - box[1]
dx, dy = 200, 40  # the floor-light edge slopes ~0.2: follow it
patch = im.crop((box[0] - dx, box[1] - dy, box[2] - dx, box[3] - dy))
feather = Image.new("L", (w, h), 0)
ImageDraw.Draw(feather).rectangle((12, 12, w - 12, h - 12), fill=255)
im.paste(patch, box[:2], feather.filter(ImageFilter.GaussianBlur(6)))

# 2. exact 3:4: 1792 x 2389, cut 11 px from the bottom (plain wall/stand)
im = im.crop((0, 0, 1792, 2389))

# 3. resize
im = im.resize((1200, 1600), Image.LANCZOS)
im.save(out, quality=94, subsampling=0)
im.crop((900, 1300, 1200, 1600)).save(corner)
print(out, im.size)
