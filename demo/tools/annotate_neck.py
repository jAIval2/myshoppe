"""The neckline view (neck-straight): points measured on source.png, as typed edges (StepA step 1).

Source points are in source.png pixels (2048 x 2048). The plate is the centred 3:4 crop x 252..1788 (CF at x 1020), resized to
1200 x 1600 (factor 0.78125).
As a module (tools/make_plate.py): base(plate_dir) -> the base image, measure() -> the plate data (no decisions). Run alone: python3 tools/annotate_neck.py   (the automatic checks; writes nothing)
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
    "underarm-l": (352, 1200), "underarm-r": (1714, 1362),
    "cf-low": (1020, 2048),
}
neck_edge = [(692, 478), (705, 505), (718, 540), (735, 560), (754, 580), (782, 600), (823, 620),
             (870, 632), (916, 640), (1020, 650), (1118, 640), (1170, 632), (1217, 620), (1260, 600),
             (1290, 580), (1312, 560), (1329, 540), (1341, 520), (1351, 500), (1356, 478)]
# Armhole seam: ONE line for each side, shared by the front edge and the sleeve inner edge.
seam_l = [(294, 644), (300, 720), (305, 800), (318, 900), (333, 1017), (346, 1120), (352, 1200)]
seam_r = [(1750, 639), (1739, 728), (1728, 817), (1722, 917), (1715, 1020), (1708, 1130), (1702, 1230), (1706, 1300), (1714, 1362)]
# Below the underarm, between arm and body (left ~x300-395 y1350-1530, right ~x1650-1720 y1270-1820): the kurta's own white fabric
# in shadow, NOT the wall (the user, 2026-11-22, StepA extension step L4: "it is the white fabric layer itself ... part of the kurta").
# So there is no opening: the front runs under the sleeve up to the sleeve's inner edge, which is the visible boundary there (a seam
# shared by the front and the sleeve). body_l / body_r (the old reading of the body side of a "gap") are kept for the record only.
body_l = [(365, 1300), (385, 1400), (395, 1500), (398, 1600), (402, 1800), (405, 2048)]
slv_l = [(348, 1290), (342, 1370), (346, 1450), (368, 1505), (392, 1535), (400, 1600), (404, 1800), (407, 2048)]
# The right side was read again in StepA step 3 (1.4x crop, source y 1180-1860): the front and the sleeve touch down to the apex of
# the wall wedge (1714, 1362) (above it a white fold, not wall); the wedge closes at (1655, 1700); below it the sleeve lies on the body.
body_r = [(1700, 1375), (1686, 1394), (1675, 1466), (1654, 1537), (1645, 1573), (1644, 1609), (1648, 1650), (1652, 1680)]
slv_r = [(1725, 1394), (1718, 1466), (1707, 1537), (1693, 1609), (1680, 1644), (1665, 1680)]
low_r = [(1650, 1800), (1650, 1900), (1648, 2048)]                # the sleeve on the body, below the wedge
# where the gap closes again (StepA step 3): below these points the sleeve lies on the body, one shared list (the sleeve's edge)
JOIN_L, JOIN_R = (400, 1600), (1655, 1700)
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
        # where the gap closes, the sleeve lies on the body: ONE list, shared (the sleeve's edge, which is on top)
        "join-l": {"type": "seam", "zones": ["front", "sleeve-l"], "points": T([JOIN_L] + slv_l[6:])},
        "join-r": {"type": "seam", "zones": ["front", "sleeve-r"], "points": T([JOIN_R] + low_r)},
        "front-bottom": {"type": "frame", "points": T([slv_l[-1], (1020, 2048), low_r[-1]])},
        "cap-l": {"type": "free", "points": T(sl_top)},
        "sleeve-in-l": {"type": "seam", "zones": ["front", "sleeve-l"], "points": T(seam_l[-1:] + slv_l[:5] + [JOIN_L])},   # the sleeve's inner edge over the shaded body
        "sleeve-bottom-l": {"type": "frame", "points": T([(252, 2048), (407, 2048)])},
        "sleeve-side-l": {"type": "frame", "points": T([(252, 682), (252, 2048)])},
        "cap-r": {"type": "free", "points": T(sr_top)},
        "sleeve-side-r": {"type": "frame", "points": T([(1788, 680), (1788, 2048)])},
        "sleeve-bottom-r": {"type": "frame", "points": T([(1648, 2048), (1788, 2048)])},
        "sleeve-in-r": {"type": "seam", "zones": ["front", "sleeve-r"], "points": T(seam_r[-1:] + slv_r + [JOIN_R])},
    }
    left_e, right_e = T(seam_l + body_l), T(seam_r + body_r + [JOIN_R] + low_r)
    zones = {
        "front": {"order": 1, "frame": {"axis": ["cf-neck", "cf-low"], "anchor": {"line": ["neck-l", "neck-r"]}},
                  "outline": [["shoulder-l", 1], ["neck", 1], ["shoulder-r", 1], ["armhole-r", 1], ["sleeve-in-r", 1], ["join-r", 1],
                              ["front-bottom", -1], ["join-l", -1], ["sleeve-in-l", -1], ["armhole-l", -1]]},
        "sleeve-l": {"order": 2, "frame": {"axis": "midline", "anchor": {"point": "shoulder-l"}},
                     "outline": [["cap-l", 1], ["armhole-l", 1], ["sleeve-in-l", 1], ["join-l", 1], ["sleeve-bottom-l", -1], ["sleeve-side-l", -1]]},
        "sleeve-r": {"order": 2, "frame": {"axis": "midline", "anchor": {"point": "shoulder-r"}},
                     "outline": [["cap-r", 1], ["sleeve-side-r", 1], ["sleeve-bottom-r", -1], ["join-r", -1], ["sleeve-in-r", -1], ["armhole-r", -1]]},
    }
    return {
        "view": "neck", "variant": "straight-kurta", "viewBox": [1200, 1600], "mmPerPx": round(mm_per_px, 4),
        "scaleNote": "neck-l -> neck-r = 158 mm (agreed value, from the torso plate)",
        "source": "source.png crop x 252..1788, resized x0.78125. Points measured on source.png by Claude.",
        "landmarks": L, "edges": edges, "zones": zones,
        # trims: the lace hangs on the neck edge between the corners (the build derives the line: StepA extension, step L1)
        "trims": {"neck": {"order": 3, "type": "insertion", "edge": "neck", "from": "neck-l", "to": "neck-r"}},
        "stitches": {"neck-topstitch": offset(neck, 5.5 / mm_per_px, opening)},          # visible top-stitch line (measured)
        "settings": {},
    }




def checks(P):
    L = P["landmarks"]
    print("mm/px", P["mmPerPx"], "| neck width px", round(math.dist(L["neck-l"], L["neck-r"]), 1))


if __name__ == "__main__":
    checks(measure())
