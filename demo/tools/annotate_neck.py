"""The neckline view (neck-straight): points measured on source.png, as typed edges (StepA step 1).

Source points are in source.png pixels (2048 x 2048). The plate is the centred 3:4 crop x 252..1788 (CF at x 1020), resized to
1200 x 1600 (factor 0.78125).
As a module (tools/make_plate.py): base(plate_dir) -> the base image, measure() -> the plate data (no decisions),
review(P, base) -> annotate.png. Run alone: python3 tools/annotate_neck.py   (the automatic checks; writes nothing)
"""
import math
from PIL import Image, ImageDraw

X0, K = 252, 1200 / 1536


def base(D):
    src = Image.open(f"{D}/source.png").convert("RGB")
    return src.crop((X0, 0, X0 + 1536, 2048)).resize((1200, 1600), Image.LANCZOS)


def T(pts):
    return [[round((x - X0) * K, 1), round(y * K, 1)] for x, y in pts]


# ---- measured on source.png
P_ = {
    "neck-l": (692, 478), "neck-r": (1356, 478), "cf-neck": (1020, 650),
    "shoulder-l": (294, 644), "shoulder-r": (1750, 639),
    "underarm-l": (352, 1200), "underarm-r": (1702, 1230),
    "cf-low": (1020, 2048),
}
neck_edge = [(692, 478), (705, 505), (718, 540), (735, 560), (754, 580), (782, 600), (823, 620),
             (870, 632), (916, 640), (1020, 650), (1118, 640), (1170, 632), (1217, 620), (1260, 600),
             (1290, 580), (1312, 560), (1329, 540), (1341, 520), (1351, 500), (1356, 478)]
# Armhole seam: ONE line for each side, shared by the front edge and the sleeve inner edge.
seam_l = [(294, 644), (300, 720), (305, 800), (318, 900), (333, 1017), (346, 1120), (352, 1200)]
seam_r = [(1750, 639), (1739, 728), (1728, 817), (1722, 917), (1715, 1020), (1708, 1130), (1702, 1230)]
# Below the underarm the wall shows between arm and body (left ~x300-395 y1350-1530,
# right ~x1650-1720 y1270-1820). Front edge = body edge; sleeve edge = the other side of the gap.
# Where they touch again, the sleeve overlaps the front by 2 px (no hairline gap).
body_l = [(365, 1300), (385, 1400), (395, 1500), (398, 1600), (402, 1800), (405, 2048)]
slv_l = [(348, 1290), (342, 1370), (346, 1450), (368, 1505), (392, 1535), (400, 1600), (404, 1800), (407, 2048)]
body_r = [(1690, 1330), (1665, 1430), (1652, 1500), (1648, 1600), (1650, 1800), (1650, 2048)]
slv_r = [(1714, 1300), (1706, 1400), (1693, 1500), (1681, 1600), (1667, 1700), (1656, 1800), (1650, 1900), (1648, 2048)]
# sleeves (outer edges leave the crop at x 252 / 1788)
sl_top = [(252, 682), (270, 660), (294, 644)]                     # outer border -> shoulder
sr_top = [(1750, 639), (1778, 667), (1788, 680)]                  # shoulder -> outer border


def offset(pts, d, away):
    out = []
    for i, (x, y) in enumerate(pts):
        a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        n = math.hypot(tx, ty) or 1
        nx, ny = -ty / n, tx / n
        if (x - away[0]) * nx + (y - away[1]) * ny < 0:
            nx, ny = -nx, -ny
        out.append([round(x + nx * d, 1), round(y + ny * d, 1)])
    return out


def measure():
    L = {k: T([v])[0] for k, v in P_.items()}
    mm_per_px = 158 / math.dist(L["neck-l"], L["neck-r"])  # scale: neck-l -> neck-r = 158 mm
    neck = T(neck_edge)
    opening = T([(1020, 440)])[0]
    edges = {
        "shoulder-l": {"type": "free", "points": T([P_["shoulder-l"], P_["neck-l"]])},          # the shoulder line against the wall
        "neck": {"type": "cut", "points": neck},                                                 # the live neck dip
        "shoulder-r": {"type": "free", "points": T([P_["neck-r"], P_["shoulder-r"]])},
        "armhole-l": {"type": "seam", "zones": ["front", "sleeve-l"], "points": T(seam_l)},
        "armhole-r": {"type": "seam", "zones": ["front", "sleeve-r"], "points": T(seam_r)},
        "body-l": {"type": "free", "points": T(seam_l[-1:] + body_l)},                          # the body side of the wall gap
        "body-r": {"type": "free", "points": T(seam_r[-1:] + body_r)},
        "front-bottom": {"type": "frame", "points": T([(405, 2048), (1020, 2048), (1650, 2048)])},
        "cap-l": {"type": "free", "points": T(sl_top)},
        "sleeve-in-l": {"type": "free", "points": T(seam_l[-1:] + slv_l)},                      # the arm side of the gap
        "sleeve-bottom-l": {"type": "frame", "points": T([(252, 2048), (407, 2048)])},
        "sleeve-side-l": {"type": "frame", "points": T([(252, 682), (252, 2048)])},
        "cap-r": {"type": "free", "points": T(sr_top)},
        "sleeve-side-r": {"type": "frame", "points": T([(1788, 680), (1788, 2048)])},
        "sleeve-bottom-r": {"type": "frame", "points": T([(1648, 2048), (1788, 2048)])},
        "sleeve-in-r": {"type": "free", "points": T(seam_r[-1:] + slv_r)},
    }
    left_e, right_e = T(seam_l + body_l), T(seam_r + body_r)
    zones = {
        "front": {"order": 1,
                  "outline": [["shoulder-l", 1], ["neck", 1], ["shoulder-r", 1], ["armhole-r", 1], ["body-r", 1],
                              ["front-bottom", -1], ["body-l", -1], ["armhole-l", -1]],
                  "grid": {"top": T([P_["shoulder-l"], P_["neck-l"], P_["neck-r"], P_["shoulder-r"]]), "right": right_e,
                           "bottom": T([(405, 2048), (1020, 2048), (1650, 2048)]), "left": left_e}},
        "sleeve-l": {"order": 2,
                     "outline": [["cap-l", 1], ["armhole-l", 1], ["sleeve-in-l", 1], ["sleeve-bottom-l", -1], ["sleeve-side-l", -1]],
                     "grid": {"top": T(sl_top), "left": T([(252, 682), (252, 2048)]),
                              "right": T([(294, 644)] + (seam_l + slv_l)[1:]), "bottom": T([(252, 2048), (402, 2048)])}},
        "sleeve-r": {"order": 2,
                     "outline": [["cap-r", 1], ["sleeve-side-r", 1], ["sleeve-bottom-r", -1], ["sleeve-in-r", -1], ["armhole-r", -1]],
                     "grid": {"top": T(sr_top), "left": T(seam_r + slv_r), "right": T([(1788, 680), (1788, 2048)]),
                              "bottom": T([(1662, 2048), (1788, 2048)])}},
    }
    return {
        "view": "neck", "variant": "straight-kurta", "viewBox": [1200, 1600], "mmPerPx": round(mm_per_px, 4),
        "scaleNote": "neck-l -> neck-r = 158 mm (agreed value, from the torso plate)",
        "source": "source.png crop x 252..1788, resized x0.78125. Points measured on source.png by Claude.",
        "landmarks": L, "edges": edges, "zones": zones,
        "trims": {"neck": {"order": 3, "widthMm": 12, "type": "insertion", "edge": "neck", "offsetMm": 6,
                           "centre": offset(neck, 6 / mm_per_px, opening)}},             # centre 6 mm inside the edge
        "stitches": {"neck-topstitch": offset(neck, 5.5 / mm_per_px, opening)},          # visible top-stitch line (measured)
        "settings": {},
    }


# ---- annotate.png: colour code on the exact base
RED, BLUE, PURPLE, GREY, GREEN = (229, 57, 53), (30, 99, 233), (142, 36, 170), (97, 97, 97), (46, 125, 50)


def review(P, base_img):
    img = base_img.copy()
    d = ImageDraw.Draw(img)

    def line(pts, col, w=3):
        d.line([tuple(p) for p in pts], fill=col, width=w, joint="curve")

    def dashed(pts, col, w=2, on=9, off=7):
        acc, draw = 0.0, True
        for a, b in zip(pts, pts[1:]):
            seg = math.dist(a, b)
            t = 0.0
            while t < seg:
                step = min((on if draw else off) - acc, seg - t)
                if draw:
                    d.line([(a[0] + (b[0] - a[0]) * t / seg, a[1] + (b[1] - a[1]) * t / seg),
                            (a[0] + (b[0] - a[0]) * (t + step) / seg, a[1] + (b[1] - a[1]) * (t + step) / seg)], fill=col, width=w)
                t += step
                acc += step
                if acc >= (on if draw else off):
                    acc, draw = 0.0, not draw
    # Shared edges: red 2.5 px towards the body and blue 2.5 px towards the sleeve, so both stay readable. The data keeps one line.
    centre = [600, 800]
    for z, v in P["zones"].items():
        for k, e in v["grid"].items():
            if z == "front":
                line(offset(e, -2.5, centre) if k in ("left", "right") else e, RED)
            else:
                inner = (z == "sleeve-l" and k == "right") or (z == "sleeve-r" and k == "left")
                line(offset(e, 2.5, centre) if inner else e, BLUE)
    dashed(P["edges"]["neck"]["points"], RED, 3)
    line(P["trims"]["neck"]["centre"], PURPLE)
    dashed(P["stitches"]["neck-topstitch"], GREY)
    L = P["landmarks"]
    line([L["neck-l"], L["neck-r"]], GREEN, 2)
    for x, y in L.values():
        d.ellipse((x - 6, y - 6, x + 6, y + 6), fill="black", outline="white", width=2)
    return img


def checks(P):
    L = P["landmarks"]
    print("mm/px", P["mmPerPx"], "| neck width px", round(math.dist(L["neck-l"], L["neck-r"]), 1))


if __name__ == "__main__":
    checks(measure())
