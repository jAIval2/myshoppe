"""Is an annotated image drawn on the exact base, or was it regenerated? (plate.md step 2). Read-only.

usage: python3 silhouette/measure/align_check.py <annotated.png> <source.png> [x0,y0,x1,y1 ...]

Compares boxes WITHOUT lines (default: wall top-left, wall top-right, knob, form neck).
Mean abs difference per box: <= 2 aligned, > 5 regenerated. Exit code 0 = aligned, 1 = not.
Pick your own boxes if the defaults cross a line.
"""
import sys
from PIL import Image, ImageChops, ImageStat

a = Image.open(sys.argv[1]).convert("RGB")
b = Image.open(sys.argv[2]).convert("RGB")
if a.size != b.size:
    print(f"FAIL  sizes differ: {a.size} vs {b.size} (a regenerated or resized image)")
    sys.exit(1)
W, H = a.size
boxes = [tuple(map(int, s.split(","))) for s in sys.argv[3:]] or [
    (int(W * .02), int(H * .02), int(W * .19), int(H * .15)),   # wall, top left
    (int(W * .80), int(H * .02), int(W * .98), int(H * .15)),   # wall, top right
    (int(W * .44), int(H * .03), int(W * .56), int(H * .11)),   # knob
    (int(W * .40), int(H * .19), int(W * .54), int(H * .23)),   # form neck
]
worst = 0.0
for box in boxes:
    d = sum(ImageStat.Stat(ImageChops.difference(a.crop(box), b.crop(box))).mean) / 3
    worst = max(worst, d)
    print(f"{'ok  ' if d <= 2 else 'BAD '} box {box}: mean diff {d:.1f}")
verdict = "ALIGNED" if worst <= 2 else ("UNSURE (2..5): pick line-free boxes" if worst <= 5 else "REGENERATED: do not use the lines")
print(verdict)
sys.exit(0 if worst <= 2 else 1)
