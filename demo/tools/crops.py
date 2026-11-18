"""Cut 4 fixed crops from the 2x screenshot. usage: crops.py <shot-2x.png> <out-dir>
Crop centres are in plate px (1200 wide); the canvas is 860 px wide at x=540, y=64 in the 2x shot."""
import sys
from PIL import Image
CANVAS_X, CANVAS_Y, CANVAS_W, PLATE_W = 540, 64, 860, 1200
CROPS = {"neckline": (603, 269), "cuff-left": (332, 890), "bodice-centre": (578, 539), "hem": (603, 1375)}
HALF = 100  # canvas px -> 200x200 crops
def crop_box(c):
    k = CANVAS_W / PLATE_W
    x, y = CANVAS_X + c[0] * k, CANVAS_Y + c[1] * k
    return tuple(round(v) for v in (x - HALF, y - HALF, x + HALF, y + HALF))
if __name__ == "__main__":
    shot, out = Image.open(sys.argv[1]).convert("RGB"), sys.argv[2]
    import os; os.makedirs(out, exist_ok=True)
    for name, c in CROPS.items():
        shot.crop(crop_box(c)).save(f"{out}/{name}.png")
