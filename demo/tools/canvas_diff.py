"""Compare two runs of tools/cdp_shot.mjs, canvas by canvas.

usage: python3 tools/canvas_diff.py <run-a> <run-b> [--diff <out-dir>]
prints, per canvas: mean |a-b| over RGB (0..255), the share of px that differ by > 8 levels, the max; PASS when mean <= 0.5
(the halfway.md rule for "pixel-identical"). --diff writes an amplified difference image (x8) for each pair.
"""
import json, os, sys
from PIL import Image, ImageChops, ImageStat

a, b = sys.argv[1], sys.argv[2]
dout = sys.argv[sys.argv.index("--diff") + 1] if "--diff" in sys.argv else None
qa = json.load(open(os.path.join(a, "log.json")))
ok_all = True
for i, e in enumerate(qa):
    fa, fb = os.path.join(a, f"canvas-{i}.png"), os.path.join(b, f"canvas-{i}.png")
    if not (os.path.exists(fa) and os.path.exists(fb)):
        print(f"{i} missing  {e['query']}")
        ok_all = False
        continue
    A, B = Image.open(fa).convert("RGB"), Image.open(fb).convert("RGB")
    if A.size != B.size:
        print(f"{i} SIZE {A.size} vs {B.size}  {e['query']}")
        ok_all = False
        continue
    d = ImageChops.difference(A, B)
    mean = sum(ImageStat.Stat(d).mean) / 3
    g = d.convert("L")
    big = sum(g.point(lambda v: 255 if v > 8 else 0).histogram()[255:]) / (A.size[0] * A.size[1])
    mx = max(ImageStat.Stat(d).extrema[c][1] for c in range(3))
    ok = mean <= 0.5
    ok_all &= ok
    print(f"{i} mean {mean:.3f}  >8: {100 * big:.3f} %  max {mx:3d}  {'PASS' if ok else 'FAIL'}  {e['query']}")
    if dout:
        os.makedirs(dout, exist_ok=True)
        d.point(lambda v: min(255, v * 8)).save(os.path.join(dout, f"diff-{i}.png"))
print("ALL PASS" if ok_all else "SOME FAIL")
sys.exit(0 if ok_all else 1)
