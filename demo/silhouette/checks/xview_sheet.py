"""The cross-view review sheet (StepB step 0): for each garment landmark seen in two or more views (xview_check.py), a crop of the
same real size around it in each view, side by side. Render the views with the registration print (?fabric=reg): where the views
agree, each row shows the same cell label at the same place relative to the 1 cm lines.

usage: python3 silhouette/checks/xview_sheet.py <out.png> <shots-dir> [--mm 100] [--px 200]
  <shots-dir>: canvas-0..3.png from cdp_shot.mjs at --dpr 2 and stage=600 (one canvas px = one plate px) for the queries
               "view=torso&fabric=reg&trims=none&stage=600", then neck, sleeve, hem, in that order.
"""
import os, sys
from PIL import Image, ImageDraw

sys.path[:0] = [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), d) for d in ("pipeline", "checks")]
import garment as GM, platedat

DEMO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VIEWS = ["torso", "neck", "sleeve", "hem"]


def main(a):
    out, shots = a[0], a[1]
    mm = float(a[a.index("--mm") + 1]) if "--mm" in a else 100.0
    px = int(a[a.index("--px") + 1]) if "--px" in a else 200
    rows = {}
    plates = {}
    for i, v in enumerate(VIEWS):
        pd = os.path.join(DEMO, "assets", "plates", f"{v}-straight")
        P = platedat.read(pd)
        img = Image.open(os.path.join(shots, f"canvas-{i}.png")).convert("RGB")
        if img.size != tuple(P["viewBox"]): img = img.resize(tuple(P["viewBox"]), Image.LANCZOS)
        plates[v] = (P, img)
        G = GM.load(P["garment"]["look"])
        for lm, xy in P.get("landmarks", {}).items():
            name, _ = GM.landmark(G, v, lm)
            if name and G["landmarks"][name]["compare"] == "uv": rows.setdefault(name, {})[v] = xy
    rows = {k: r for k, r in sorted(rows.items()) if len(r) >= 2}
    lab = 120
    sheet = Image.new("RGB", (lab + px * len(VIEWS), 24 + px * len(rows)), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    for j, v in enumerate(VIEWS): d.text((lab + j * px + 6, 6), v, fill=(0, 0, 0))
    for i, (name, per) in enumerate(rows.items()):
        y0 = 24 + i * px
        d.text((6, y0 + px // 2 - 6), name, fill=(0, 0, 0))
        for j, v in enumerate(VIEWS):
            if v not in per: continue
            P, img = plates[v]
            r = mm / 2 / P["mmPerPx"]                  # half the crop in plate px
            x, y = per[v]
            crop = img.crop((round(x - r), round(y - r), round(x + r), round(y + r))).resize((px, px), Image.LANCZOS)
            sheet.paste(crop, (lab + j * px, y0))
            c = (lab + j * px + px // 2, y0 + px // 2)
            d.line([(c[0] - 8, c[1]), (c[0] + 8, c[1])], fill=(255, 0, 255), width=2)
            d.line([(c[0], c[1] - 8), (c[0], c[1] + 8)], fill=(255, 0, 255), width=2)
            d.rectangle([lab + j * px, y0, lab + (j + 1) * px - 1, y0 + px - 1], outline=(180, 180, 180))
    sheet.save(out, optimize=True)
    print(f"{len(rows)} landmarks x {len(VIEWS)} views ({mm:.0f} mm crops) -> {out}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2: sys.exit(__doc__)
    main(a)
