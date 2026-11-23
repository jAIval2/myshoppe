"""Test prints (StepB): fabrics made by a script, not photographed, to prove the fabric frame and the placement. Pillow only.
They are test fabrics of the page (?fabric=<name>), not in the picker, and each has a sidecar like a real fabric.

usage: python3 swatchprep/test_prints.py reg | buta | border <out.png>
       python3 swatchprep/test_prints.py lace-reg <out.webp> <sidecar.json>
  reg   the registration print: a 30 cm tile, 1024 px. Each 10 cm cell has its own tint and its label (column A-C along u, row
        1-3 along v: "A1" holds u 0..10, v 0..10 cm of the tile). A thin line every 1 cm, a thicker one every 5 cm, and a red
        crosshair at the tile origin (u = v = 0 mod 30 cm). Where a garment point shows the same cell, the same label and the same
        offset from the cell's lines in two views, the two views give it the same fabric (u, v) to within the line spacing.
  buta  one placed motif (StepB step 5): a 30 cm tile, a 9 cm round motif with a crosshair at the tile's centre (512, 512) on a pale
        ground with a 5 cm grid. Placed with the motif on the garment record's placement point of each piece.
  border  a border print (StepB step 5): a 30 cm tile, a plain ground above an 8 cm band (stripes, a zigzag, "HEM") whose lower
        edge is the tile's bottom (borderBottomPx 1024). Placed with that edge on each piece's hem line.
  lace-reg  the registration lace (StepC step 0): a band 446 px tall, 4 motifs of 300 px (a tile of 1200 px), each numbered 1-4 with
        an arrow pointing to the decorative edge (the band's bottom), a dark line at every motif boundary, a scalloped bottom edge.
        It shows the lace's direction, its phase, its whole repeats and its ends at a glance (?lace=reg). Sidecar version 2, a test.
"""
import sys
from PIL import Image, ImageDraw, ImageFont

TILE_CM, PX = 30, 1024
TINTS = [(244, 226, 222), (222, 236, 246), (228, 242, 224), (246, 240, 214), (236, 226, 244), (220, 240, 238),
         (246, 230, 238), (232, 232, 232), (240, 234, 222)]


def font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:                                     # an old Pillow without the sized default font
        return ImageFont.load_default()


def reg(out):
    k = PX / TILE_CM                                      # px per cm
    img = Image.new("RGB", (PX, PX))
    d = ImageDraw.Draw(img)
    for j in range(3):
        for i in range(3):
            d.rectangle([round(i * 10 * k), round(j * 10 * k), round((i + 1) * 10 * k) - 1, round((j + 1) * 10 * k) - 1], fill=TINTS[j * 3 + i])
    for c in range(TILE_CM):
        p = round(c * k)
        w, col = (5, (40, 40, 40)) if c % 10 == 0 else (3, (90, 90, 90)) if c % 5 == 0 else (1, (150, 150, 150))
        d.rectangle([p - w // 2, 0, p + (w - 1) // 2, PX - 1], fill=col)
        d.rectangle([0, p - w // 2, PX - 1, p + (w - 1) // 2], fill=col)
    f = font(150)
    for j in range(3):
        for i in range(3):
            d.text((round((i * 10 + 5) * k), round((j * 10 + 5) * k)), "ABC"[i] + str(j + 1), fill=(30, 30, 30), font=f, anchor="mm")
    r = round(2.5 * k)                                    # the origin crosshair: red, 5 cm across, on the tile's corner (it wraps)
    for ox in (0, PX):
        for oy in (0, PX):
            d.rectangle([ox - r, oy - 6, ox + r, oy + 6], fill=(214, 40, 40))
            d.rectangle([ox - 6, oy - r, ox + 6, oy + r], fill=(214, 40, 40))
    img.save(out, optimize=True)
    print(f"reg -> {out} ({PX} px = {TILE_CM} cm)")


def buta(out):
    k = PX / TILE_CM
    img = Image.new("RGB", (PX, PX), (246, 240, 226))
    d = ImageDraw.Draw(img)
    for c in range(0, TILE_CM, 5):
        p = round(c * k)
        d.line([(p, 0), (p, PX)], fill=(222, 212, 192), width=2); d.line([(0, p), (PX, p)], fill=(222, 212, 192), width=2)
    cx = cy = PX // 2
    for r_cm, col in ((4.5, (128, 30, 60)), (3.5, (214, 150, 40)), (2.4, (128, 30, 60)), (1.2, (30, 90, 120))):
        r = round(r_cm * k)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    d.rectangle([cx - 2, cy - round(5.5 * k), cx + 2, cy + round(5.5 * k)], fill=(20, 20, 20))
    d.rectangle([cx - round(5.5 * k), cy - 2, cx + round(5.5 * k), cy + 2], fill=(20, 20, 20))
    img.save(out, optimize=True)
    print(f"buta -> {out} (motif centre {cx}, {cy} px)")


def border(out):
    k = PX / TILE_CM
    img = Image.new("RGB", (PX, PX), (240, 236, 228))
    d = ImageDraw.Draw(img)
    top = round((TILE_CM - 8) * k)
    d.rectangle([0, top, PX, PX], fill=(36, 70, 110))
    for y_cm, col in ((22.6, (214, 170, 60)), (29.2, (214, 170, 60))):
        y = round(y_cm * k); d.rectangle([0, y - 6, PX, y + 6], fill=col)
    zig = [(x, round((25.6 + (1.2 if (x // 64) % 2 else -1.2)) * k)) for x in range(0, PX + 64, 64)]
    d.line(zig, fill=(240, 236, 228), width=8)
    d.text((PX // 2, round(27.6 * k)), "HEM", fill=(240, 236, 228), font=font(70), anchor="mm")
    img.save(out, optimize=True)
    print(f"border -> {out} (the band's lower edge at the tile's bottom, {PX} px)")


def lace_reg(out, out_json):
    import json
    H, P, N = 446, 300, 4
    img = Image.new("RGBA", (P * N, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cols = [(150, 40, 60), (40, 90, 150), (40, 120, 70), (170, 110, 30)]
    for i in range(N):
        x0 = i * P
        d.rectangle([x0, 0, x0 + P - 1, H - 60], fill=(240, 232, 214, 255))                         # the band
        for k in range(3):                                                                         # scallops at the decorative edge
            cx = x0 + P // 6 + k * P // 3
            d.ellipse([cx - P // 6, H - 110, cx + P // 6, H - 10], fill=(240, 232, 214, 255))
        d.rectangle([x0, 0, x0 + 5, H - 60], fill=(30, 30, 30, 255))                               # the motif boundary
        d.text((x0 + P // 2, 150), str(i + 1), fill=cols[i] + (255,), font=font(170), anchor="mm")
        ax = x0 + P // 2                                                                           # the arrow to the edge
        d.rectangle([ax - 8, 260, ax + 8, 330], fill=cols[i] + (255,))
        d.polygon([(ax - 34, 330), (ax + 34, 330), (ax, 378)], fill=cols[i] + (255,))
    img.save(out, lossless=True)
    meta = {"version": 2, "name": "Registration lace (test)", "source": out.split("/")[-1], "bandPx": [P * N, H], "edge": "bottom",
            "widthMm": 30.0, "widthSrc": "measured", "repeatSrc": "measured", "class": "insertion", "edgeDepth": 0.0,
            "bottomOpen": 0.0, "edging": False, "periodPx": float(P), "periods": N, "periodRatio": round(P / H, 5),
            "motifCentrePx": P / 2, "mirror": False, "test": True,
            "note": "a test lace made by swatchprep/test_prints.py: its scale is exact by construction"}
    json.dump(meta, open(out_json, "w"), indent=1)
    print(f"lace-reg -> {out} + {out_json} ({N} motifs of {P} px, band {H} px = 30 mm)")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["lace-reg"] and len(a) == 3: lace_reg(a[1], a[2]); sys.exit()
    if len(a) != 2 or a[0] not in ("reg", "buta", "border"): sys.exit(__doc__)
    {"reg": reg, "buta": buta, "border": border}[a[0]](a[1])
