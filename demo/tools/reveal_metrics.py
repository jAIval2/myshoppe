"""halfway.md step 3: numbers for "a person cannot point to the old neckline" and "no visible repeat or smear" in a render
of a DEEPER setting (the form fill), lace off. Pillow only.

usage: python3 tools/reveal_metrics.py <canvas.png> <plate-dir> [--canvas-w 860]

step:   mean luminance (canvas, a 5 px window) at 6 mm below the photographed edge (fill) minus 6 mm above it (real form),
        along the middle 60 % of the edge, against the same 12 mm step taken 6 and 18 mm above the edge (real form only:
        the light's own change over 12 mm). The old neckline shows if the first is much larger than the second.
repeat: the largest normalised autocorrelation of the fine detail (luminance minus a 9 px blur) at lags of 6-40 canvas px,
        in a square of the fill, against a square of the real form. A visible repeat is a clear peak (> 0.5).
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import platedat
from PIL import Image, ImageFilter, ImageStat

img = Image.open(sys.argv[1]).convert("L")
pd = sys.argv[2]
cw = float(sys.argv[sys.argv.index("--canvas-w") + 1]) if "--canvas-w" in sys.argv else img.width
plate = platedat.legacy(platedat.read(pd))[0]
k = cw / plate["viewBox"][0]
mm = plate["mmPerPx"]
edge = plate["neck"]["edge"]


def L(x, y, r=2):
    cx, cy = x * k, y * k
    return ImageStat.Stat(img.crop((int(cx - r), int(cy - r), int(cx + r) + 1, int(cy + r) + 1))).mean[0]


steps, ctrl = [], []
n = len(edge)
for i in range(int(0.2 * n), int(0.8 * n)):
    a, b = edge[i], edge[i + 1]
    tx, ty = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(tx, ty) or 1
    nx, ny = -ty / ln, tx / ln                      # into the garment (down)
    if ny < 0:
        nx, ny = -nx, -ny
    m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    at = lambda d: L(m[0] + nx * d / mm, m[1] + ny * d / mm)
    steps.append(at(6) - at(-6))
    ctrl.append(at(-6) - at(-18))
mean = lambda v: sum(v) / len(v)
print(f"step across the old edge: mean {mean(steps):+.2f}, mean |.| {mean([abs(s) for s in steps]):.2f} levels")
print(f"control (real form, same 12 mm): mean {mean(ctrl):+.2f}, mean |.| {mean([abs(s) for s in ctrl]):.2f} levels")


def acorr_peak(box):
    crop = img.crop(tuple(int(v * k) for v in box))
    hp = [a - b for a, b in zip(crop.getdata(), crop.filter(ImageFilter.BoxBlur(4)).getdata())]
    w, h = crop.size
    mu = sum(hp) / len(hp)
    hp = [v - mu for v in hp]
    var = sum(v * v for v in hp) / len(hp) or 1
    best = (0, None)
    for dy in range(0, 41, 2):
        for dx in range(-40, 41, 2):
            if abs(dx) < 6 and abs(dy) < 6:
                continue
            s = c = 0
            for y in range(0, h - dy, 2):
                row, row2 = y * w, (y + dy) * w
                for x in range(max(0, -dx), min(w, w - dx), 2):
                    s += hp[row + x] * hp[row2 + x + dx]
                    c += 1
            r = s / c / var if c else 0
            if r > best[0]:
                best = (r, (dx, dy))
    return best


cfx, cfy = plate["neck"]["cf"]
side = 20 / mm
fill_box = (cfx - side * 1.6, cfy + 4 / mm, cfx - side * 0.1, cfy + 4 / mm + side * 1.5)
p = plate["neck"]["formPatch"]
real_box = (p[0], p[1], p[2], p[3])
print("repeat (fill):      peak %.2f at lag %s" % acorr_peak(fill_box))
print("repeat (real form): peak %.2f at lag %s" % acorr_peak(real_box))
