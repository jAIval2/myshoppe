"""Before / after sheet and difference (StepB): two cdp_shot.mjs runs of the same queries, side by side, with the mean difference.

usage: python3 silhouette/checks/ba_sheet.py <out.png> <before-dir> <after-dir> [--labels a,b,...] [--width 300]
  Each dir holds canvas-<i>.png for the same queries (and its log.json). Prints, per query, the mean |difference| (0..255, the
  three channels) and the share of pixels that differ by more than 8 levels; the sheet puts before | after for each query in a row.
"""
import json, os, sys
from PIL import Image, ImageChops, ImageDraw, ImageStat


def main(a):
    out, bdir, adir = a[0], a[1], a[2]
    width = int(a[a.index("--width") + 1]) if "--width" in a else 300
    log = json.load(open(os.path.join(adir, "log.json")))
    labels = a[a.index("--labels") + 1].split(",") if "--labels" in a else [e["query"] for e in log]
    rows = []
    i = 0
    while os.path.exists(os.path.join(adir, f"canvas-{i}.png")):
        b = Image.open(os.path.join(bdir, f"canvas-{i}.png")).convert("RGB")
        f = Image.open(os.path.join(adir, f"canvas-{i}.png")).convert("RGB")
        d = ImageChops.difference(b, f)
        mean = sum(ImageStat.Stat(d).mean) / 3
        big = sum(d.convert("L").point(lambda v: 255 if v > 8 else 0).histogram()[255:]) / (d.width * d.height)
        lab = labels[i] if i < len(labels) else f"q{i}"
        print(f"{lab:48} mean |diff| {mean:6.3f}   > 8 levels: {100 * big:6.2f} %")
        h = round(b.height * width / b.width)
        rows.append((lab, b.resize((width, h), Image.LANCZOS), f.resize((width, h), Image.LANCZOS), mean))
        i += 1
    if not rows: sys.exit("no canvas-<i>.png in " + adir)
    h = rows[0][1].height
    sheet = Image.new("RGB", (2 * width + 10, len(rows) * (h + 20)), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    for k, (lab, b, f, mean) in enumerate(rows):
        y = k * (h + 20)
        d.text((4, y + 4), f"{lab}   before | after   (mean |diff| {mean:.2f})", fill=(0, 0, 0))
        sheet.paste(b, (0, y + 18)); sheet.paste(f, (width + 10, y + 18))
    sheet.save(out, optimize=True)
    print("->", out)


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 3: sys.exit(__doc__)
    main(a)
