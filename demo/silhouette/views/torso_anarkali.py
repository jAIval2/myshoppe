"""The full-torso view of the anarkali (torso-anarkali), measured on source.png (1792 x 2400, as received 2026-11-24: the white-cotton
anarkali, a fitted bodice with an empire seam, a pleated flared skirt with a slit at the image right, full sleeves).

Read with the kit (_kit.py, as torso_lehenga.py): the wall flooded from the image border, the garment what is left, cut into zones by
the measured seams. The neckline was measured per column where the form's linen (R-B 35 .. 41) turns into the cloth (17 .. 22), then
read on a x2.6 crop; the seams, the landmarks and the right-hand gap on gridded crops of the source (x1 .. x2.6, contrast 1 .. 2.4).
Source px; the plate is the 1792 x 2389 crop, x 0.6696 -> 1200 x 1600.
Zones (draw order): skirt (1), front (the bodice, 2), sleeve-l, sleeve-r (3: each lies over the skirt below the empire seam).
The left sleeve lies on the body all the way down (a crease, then the sleeve's inner edge over the skirt: seams). The right sleeve
hangs apart from the body: wall shows between them below the underarm (a gap, both edges free).
As a module (make_plate.py): base(path), measure(). Run alone: the kit's checks, and review/torso-anarkali/zones.png.
"""
import os, sys
sys.path[:0] = [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), d) for d in ("pipeline", "views")]
import _kit

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sources", "torso-anarkali.png")
PATCHES = [((1625, 2232, 1735, 2342), -170)]          # the sparkle mark on the floor, from 170 px left

# neck-l -> neck-r: per column, the first cloth-coloured run going down (R-B < 28 over 4 px), the corners read on a x2.6 crop
NECK = [(797, 296), (805, 312), (820, 328), (835, 337), (850, 343), (865, 346), (880, 347), (895, 347), (910, 347), (925, 347),
        (940, 346), (955, 343), (970, 337), (985, 328), (998, 316), (1008, 296)]
FORM = [(780, 150), (1030, 150), (1030, 294)] + NECK[::-1] + [(780, 294)]           # the form above the neckline
FLOOR = [(0, 2110), (1792, 2110), (1792, 2400), (0, 2400)]                          # the floor below the stand's feet
STAND = [(845, 1952), (915, 1952), (960, 2110), (800, 2110)]                         # the stand's column below the hem (dark wood)

# The RIGHT sleeve hangs apart from the body: a narrow run of wall in shadow (chroma >= 35, L < 165; the shaded cloth beside it has
# chroma 24 .. 33) from the underarm down to the cuff's inner corner, 6 .. 22 px wide. Per row (every 10 px, blur 1.0): its left end
# (the body's side) and its right end (the sleeve's side), smoothed by eye where a row read a fold (y 720 .. 780: the waist seam).
GAP_R_BODY = [(1100, 565), (1093, 570), (1091, 590), (1089, 610), (1085, 630), (1083, 650), (1082, 670), (1081, 690), (1080, 700),
              (1079, 710), (1082, 730), (1088, 750), (1094, 770), (1100, 790), (1102, 810), (1104, 830), (1107, 850), (1110, 870),
              (1116, 885), (1124, 900), (1128, 915), (1130, 935), (1134, 950), (1136, 965), (1140, 980), (1144, 1000), (1147, 1020),
              (1149, 1040), (1152, 1060), (1155, 1075), (1157, 1090), (1160, 1110), (1162, 1125), (1164, 1136)]
GAP_R_SLEEVE = [(1108, 565), (1112, 575), (1107, 590), (1103, 610), (1099, 630), (1097, 650), (1095, 670), (1093, 690),
                (1094, 710), (1096, 730), (1098, 750), (1100, 770), (1105, 790), (1108, 810), (1113, 830), (1119, 850),
                (1125, 870), (1129, 890), (1132, 905), (1138, 920), (1143, 940), (1147, 960), (1150, 980), (1155, 1000),
                (1159, 1020), (1162, 1040), (1165, 1060), (1169, 1080), (1173, 1100), (1177, 1120), (1180, 1132)]
GAP_R = GAP_R_BODY + GAP_R_SLEEVE[::-1]
# the skirt's right edge below the cuff, against the wall in shadow (wall chroma 34 .. 42): per row, the first run of 4 px coming in
# from the wall with chroma 4 under and L 6 over the wall's (blur 1.0); y 1200 .. 1260 and 1820 .. 1932 read on a x1.6 crop (the
# cuff's shadow on the wall, the back panel beyond the slit to the hem corner)
EDGE_R = [(1164, 1136), (1166, 1160), (1168, 1180), (1172, 1200), (1176, 1220), (1179, 1240), (1182, 1260), (1185, 1280),
          (1189, 1300), (1194, 1340), (1201, 1380), (1206, 1420), (1212, 1460), (1218, 1500), (1221, 1540), (1225, 1580),
          (1228, 1620), (1231, 1660), (1235, 1700), (1237, 1740), (1239, 1780), (1241, 1800), (1245, 1840), (1250, 1870),
          (1256, 1890), (1263, 1910), (1268, 1932)]
# the hem of the shaded right part, per column the strongest drop going down (blur 1.2): strong at x 1005 .. 1080 (23 .. 47 levels) and
# 1215 .. 1268 (19 .. 27), weak at 1095 .. 1185 (3 .. 10: shaded cloth over shaded floor), there a straight run between the two
HEM_R = [(1262, 1933), (1245, 1928), (1230, 1925), (1215, 1923), (1203, 1924), (1199, 1935), (1175, 1941), (1150, 1948),
         (1125, 1954), (1100, 1958), (1080, 1961), (1050, 1962), (1020, 1960), (1000, 1958)]
HEM_R_WEAK = HEM_R[5:11]
RIGHT_WALL = EDGE_R + HEM_R + [(1000, 1966), (1000, 2110), (1792, 2110), (1792, 1136)]


def offset(line, d):
    """The polyline moved d px to the left of its direction of travel (image y down)."""
    out = []
    for i, (x, y) in enumerate(line):
        a, b = line[max(i - 1, 0)], line[min(i + 1, len(line) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]; n = (dx * dx + dy * dy) ** 0.5 or 1.0
        out.append((round(x + d * dy / n, 1), round(y - d * dx / n, 1)))
    return out


# barriers 2 px outside the cloth, so that the wall's flood cannot enter the shaded cloth: along the skirt's right edge (onto the
# wall: +d moves a line that goes down towards +x) and along the gap's body side (into the gap)
BARRIER_R = offset(EDGE_R + HEM_R, 2.0)
BARRIER_GAP = offset(GAP_R_BODY, 2.0)

SEAMS = {                                             # each runs from background to background, or into another seam
    # the shoulder point, down the armhole to the underarm crease, then the crease where the sleeve lies on the bodice, to the waist
    "armhole-l": [(664, 322), (674, 334), (677, 370), (679, 400), (680, 440), (681, 480), (682, 520), (685, 560), (692, 600),
                  (700, 640), (708, 680), (716, 705)],
    # the sleeve's inner edge lying over the skirt, from the empire seam to the cuff's inner corner, then on into the wall below it
    "sleeve-skirt-l": [(716, 705), (712, 730), (700, 780), (688, 830), (675, 880), (660, 940), (648, 990), (641, 1020),
                       (636, 1050), (632, 1080), (629, 1110), (628, 1135), (620, 1150)],
    # the empire seam, from the left junction into the gap at the right
    "waist": [(716, 705), (760, 708), (800, 711), (850, 712), (900, 712), (950, 711), (1000, 709), (1050, 706), (1075, 704),
              (1086, 704)],
    "armhole-r": [(1140, 320), (1126, 334), (1122, 370), (1118, 420), (1112, 470), (1106, 520), (1103, 545), (1103, 568)],
}
LM = {"neck-l": (797, 296), "neck-r": (1008, 296), "cf-neck": (900, 347),
      "shoulder-l": (674, 334), "shoulder-r": (1126, 334),
      "underarm-l": (685, 560), "underarm-r": (1103, 566),
      "waist-l": (716, 705), "waist-r": (1080, 704), "waist-cf": (900, 712),
      "hem-l": (523, 1925), "hem-r": (1268, 1932), "hem-cf": (900, 1945),
      "slit-r": (1197, 1460), "hem-slit-r": (1200, 1921),
      "cuff-out-l": (485, 1103), "cuff-in-l": (628, 1135), "cuff-out-r": (1280, 1110), "cuff-in-r": (1180, 1132)}


def base(path=SRC):
    _kit.fit_to(path)
    return _kit.base(path, PATCHES)


def spec():
    _kit.fit_to(SRC)
    mm = 158.0 / ((LM["neck-r"][0] - LM["neck-l"][0]) * _kit.K)
    v_waist = round((LM["waist-cf"][1] - LM["neck-l"][1]) * _kit.K * mm, 1)
    return {
        "path": SRC, "patches": PATCHES, "view": "torso", "variant": "anarkali",
        "exclude": [FORM, GAP_R, RIGHT_WALL, STAND, FLOOR],   # measured polygons, not seeds (a seed leaks into the shaded cloth)
        "bg_barriers": [BARRIER_R, BARRIER_GAP] + list(SEAMS.values()),   # the seams too: they reach the wall at the shoulders
        "measured": [EDGE_R, HEM_R_WEAK, GAP_R_BODY, GAP_R_SLEEVE],   # the build's snap keeps these (the cloth has the wall's colour there)
        "smooth_k": 3,
        "seams": SEAMS,
        "zones": {
            "front": {"seed": (900, 500), "order": 2, "frame": {"axis": ["cf-neck", "waist-cf"], "anchor": {"line": ["neck-l", "neck-r"]}}},
            "skirt": {"seed": (900, 1500), "order": 1, "frame": {"axis": ["waist-cf", "hem-cf"], "anchor": {"point": "waist-cf", "vMm": v_waist}, "sagEdge": "hem"}},
            "sleeve-l": {"seed": (600, 800), "order": 3, "frame": {"axis": "midline", "anchor": {"point": "shoulder-l"}, "sagEdge": "cuff-l", "skipTop": 0.15}},
            "sleeve-r": {"seed": (1200, 800), "order": 3, "frame": {"axis": "midline", "anchor": {"point": "shoulder-r"}, "sagEdge": "cuff-r", "skipTop": 0.15}},
        },
        "cuts": {"front": [("neck", LM["neck-l"], LM["neck-r"])],
                 "skirt": [("hem", LM["hem-l"], LM["hem-r"])],
                 "sleeve-l": [("cuff-l", LM["cuff-out-l"], LM["cuff-in-l"])], "sleeve-r": [("cuff-r", LM["cuff-in-r"], LM["cuff-out-r"])]},
        "landmarks": LM,
        "scale": ("neck-l", "neck-r", 158.0, "neck-l -> neck-r = 158 mm (the straight kurta's agreed neck width: the same dress form); "
                  "an assumption, not a measurement of this garment"),
        "settings": {"thetaDeg": {"front": 60, "skirt": 70, "sleeve-l": 70, "sleeve-r": 70}},
        "source_note": "silhouette/sources/torso-anarkali.png (1792 x 2400, as received 2026-11-24, the white-cotton anarkali), the sparkle "
                       "mark patched, cut to 1792 x 2389, resized to 1200 x 1600. Read with silhouette/views/_kit.py; the seams, the "
                       "neckline and the landmarks measured on the source by Claude.",
        "trims": {
            "neck": {"order": 3, "type": "insertion", "group": "neck", "edge": "neck"},
            "cuff-l": {"order": 3, "type": "edging", "group": "cuffs", "edge": "cuff-l", "bandInMm": 100.0},
            "cuff-r": {"order": 3, "type": "edging", "group": "cuffs", "edge": "cuff-r", "bandInMm": 100.0},
            "hem": {"order": 3, "type": "edging", "group": "hem", "edge": "hem", "bandInMm": 100.0, "smoothMm": 20.0},
        },
    }


def measure():
    _kit.fit_to(SRC)
    return _kit.measure(spec())[0]


if __name__ == "__main__":
    P, X = _kit.measure(spec())
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "review", "torso-anarkali")
    os.makedirs(out, exist_ok=True)
    _kit.check(P, X, os.path.join(out, "zones.png"))
