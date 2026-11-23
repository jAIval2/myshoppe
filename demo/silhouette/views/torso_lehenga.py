"""The full-torso view of the crop top and flared skirt (torso-lehenga), measured on source.png (1792 x 2400), 2026-11-23 (the
white-cotton lehenga; it replaces the 765 x 1024 image of the same day).

Read in parts (_kit.parts_labels): the top, the sleeves and the skirt each on their own crop, with their own wall flood, then merged.
The lit left side has a strong edge against the wall (20 .. 43 levels), so the flood finds it. The shaded right side has the wall's
own colour (sleeve L 170 / chroma 34 against wall L 167 / 34), so its outer edges are measured and given as barriers 2 px outside
the garment: the right sleeve from the profiles across its edge, the skirt from the strongest step on each row (the cloth ends on a
thin shadow line, the wall beyond it has chroma 37 .. 41).
Measured on gridded crops of source.png (x0.8 .. x2.6, contrast 1.4 .. 3), row profiles and step scans. Source px; the plate is the
1792 x 2389 crop, x 0.6696 -> 1200 x 1600.
Zones (draw order): skirt (1), top (the crop top's body, 2), sleeve-l, sleeve-r (3: each lies over the skirt below the underarm).
Background inside the garment: the bare midriff between the top's hem and the waistband, which joins a wedge of wall between the left
sleeve and the skirt (x 683 .. 740, y 730 .. 910), and the two underarm gaps (slivers of wall between each sleeve and the top). Not
garment: the form above the neckline, the floor and the stand.
As a module (make_plate.py): base(path), measure(). Run alone: the kit's checks, and review/torso-lehenga/zones.png.
"""
import os, sys
sys.path[:0] = [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), d) for d in ("pipeline", "views")]
import _kit

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sources", "torso-lehenga.png")
PATCHES = [((1625, 2232, 1735, 2342), -170)]          # the sparkle mark on the floor (x 1632 .. 1727, y 2240 .. 2335), from 170 px left

NECK = [(803, 292), (811, 310), (833, 323), (861, 331), (900, 334), (940, 331), (969, 323), (990, 309), (1001, 292)]   # neck-l -> neck-r
FORM = [(795, 200), (1010, 200), (1010, 290)] + NECK[::-1] + [(795, 290)]           # the form above the neckline
# the bare form between the top's hem and the waistband. Its top is the hem, per column where the chroma reaches the form's (>= 33;
# the cloth has 18 .. 28) at x 742 .. 994; right of it the cloth is shaded to the form's chroma: the luminance drop, then the corner
MIDRIFF = [(742, 727), (754, 724), (766, 721), (778, 717), (838, 717), (898, 715), (994, 716), (1006, 716), (1030, 723), (1050, 729),
           (1058, 734), (1058, 774), (744, 774)]
FLOOR = [(0, 2104), (1792, 2104), (1792, 2400), (0, 2400)]                          # the floor and the stand below the hem
# under the lit left half of the hem: sunlit wall and floor as bright as the cloth (L 229 .. 237, chroma 26 .. 33), which the flood
# does not reach through the sunlight's streaks. Its top is the hem's stepped panel bottoms (read on a x1.2 crop, checked against
# the column profiles at x 380 .. 880 within 3 px), 2 px below the cloth
UNDER_HEM_L = [(330, 1984), (373, 1982), (432, 2007), (434, 2024), (511, 2044), (513, 2048), (514, 2060), (523, 2060), (560, 2071), (615, 2071),
               (617, 2080), (640, 2084), (698, 2087), (700, 2096), (760, 2099), (880, 2101), (915, 2102), (915, 2104), (330, 2104)]
# the wedge of wall between the left sleeve and the skirt, which joins the midriff. The sleeve's side: where its shading ends on the
# wall's plateau (L 192 .. 193), per row at y 730 .. 835; below, the run of wall-coloured px (chroma >= 33), tapering along the skirt's
# edge (6 px wide at y 896, 2 px at y 920). Its tip at y 904: cut flat it showed as a blunt block of wall, and where it is under 5 px
# wide the soft edge takes its background from the skirt across it (a white speck); below y 904 the dark line stays as a crease. The
# skirt's side: the skirt's upper-left edge (a strong step, 233 over 192). Its right part overlaps the midriff (the bare form)
WEDGE_L = [(716, 726), (711, 731), (707, 745), (703, 760), (707, 775), (704, 790), (701, 805), (699, 820), (695, 835), (694, 840),
           (684, 860), (682, 880), (680, 896), (681, 904), (686, 896), (693, 880),
           (703, 860), (708, 840), (720, 835), (731, 820),
           (734, 805), (735, 790), (738, 780), (746, 776), (746, 729), (737, 729)]
WEDGE_L_SLEEVE = WEDGE_L[:14]                         # its sleeve side (the shaded cloth against the wall: measured, not snapped)
# The left underarm has no gap: what shows there is a crease (a dark line 1 .. 3 px wide), where the sleeve meets the bodice. The
# armhole seam runs down it (the darkest px per row), and the fabric keeps its shading as a fold.
# The RIGHT sleeve hangs apart from the body: wall shows between them from the armpit (1108, 505) down to the notch under the cuff's
# inner corner (7 .. 40 px wide; in shadow: wall L 152 .. 175 / chroma 32 .. 41, the deepest part L 89 .. 138 by the armpit). Per row:
# the sleeve's side where the wall's chroma (>= 32.5) gives way to the sleeve's (25 .. 31), smoothed (y 520 .. 600 read on a x2 plain
# crop, where the sleeve's shaded side has the wall's chroma); the body's side: the top's shaded side on the x2 crop down to the
# top's hem corner, then the midriff and the waistband's end, then the skirt's lit edge (chroma 22 .. 28) where the wall run begins.
GAP_R_BODY = [(1108, 505), (1104, 515), (1094, 540), (1087, 560), (1086, 580), (1084, 600), (1079, 620), (1078, 640), (1076, 660),
              (1073, 680), (1070, 700), (1067, 720), (1062, 733), (1056, 736), (1056, 776), (1064, 778), (1065, 790), (1070, 800),
              (1069, 810), (1067, 820), (1074, 830), (1081, 840), (1090, 850), (1096, 860), (1102, 870), (1106, 880), (1108, 890),
              (1112, 900), (1116, 910), (1119, 920), (1122, 930), (1124, 940), (1128, 950), (1130, 960), (1133, 970), (1136, 980),
              (1138, 990), (1142, 1000), (1143, 1010), (1147, 1020), (1151, 1030), (1154, 1040), (1158, 1050), (1161, 1060),
              (1162, 1070), (1164, 1080), (1165, 1090), (1166, 1100), (1168, 1112), (1170, 1124)]
GAP_R_SLEEVE = [(1114, 510), (1111, 520), (1108, 540), (1107, 560), (1104, 580), (1101, 600), (1102, 620), (1101, 640), (1102, 660),
                (1101, 680), (1097, 700), (1096, 720), (1094, 740), (1093, 760), (1098, 780), (1100, 800), (1102, 820), (1105, 840),
                (1108, 850), (1109, 860), (1112, 870), (1115, 880), (1119, 890), (1122, 900), (1128, 910), (1130, 920), (1134, 930),
                (1137, 940), (1142, 950), (1145, 960), (1147, 970), (1151, 980), (1156, 990), (1159, 1000), (1160, 1010), (1164, 1020),
                (1167, 1030), (1167, 1040), (1170, 1050), (1176, 1060), (1176, 1070), (1179, 1080), (1179, 1090), (1181, 1100),
                (1183, 1124)]
GAP_R = GAP_R_BODY + GAP_R_SLEEVE[::-1]

# the shaded right side: the garment's edge where it has the wall's colour, measured on the source. The shoulder per column (wall L 180
# / chroma 32 over cloth L 175 .. 181 / chroma 24 .. 28: where the chroma steps); the sleeve from profiles across it; the cuff on a
# x0.9 crop; under the cuff's inner corner a notch of wall (x 1170 .. 1183); the skirt from the dark line where the cloth ends, per
# row (y 1130 .. 1205), then the strongest step per row; the hem per column (at x 1280 .. 1300
# the cloth is 3 .. 8 levels above the wall: interpolated). Left of x 1110 the hem stands on the dark floor line (113 .. 145).
EDGE_R = [(1005, 292), (1020, 298), (1035, 301), (1050, 309), (1065, 317), (1080, 323), (1095, 329), (1110, 335), (1125, 340),
          (1140, 345), (1155, 362), (1166, 400), (1190, 500), (1210, 600), (1230, 700), (1247, 800), (1265, 900), (1282, 1000),
          (1295, 1080), (1300, 1098), (1241, 1111), (1183, 1124), (1171, 1127), (1170, 1130), (1171, 1140), (1172, 1150),
          (1175, 1160), (1178, 1175), (1182, 1190), (1187, 1205), (1230, 1300), (1260, 1400),
          (1290, 1500), (1319, 1600), (1349, 1700), (1380, 1800), (1410, 1900), (1430, 1970), (1430, 1992), (1425, 1999),
          (1410, 2002), (1390, 2010), (1370, 2018), (1350, 2036), (1330, 2042), (1310, 2044), (1290, 2056), (1270, 2068),
          (1250, 2072), (1230, 2075), (1210, 2076), (1190, 2077), (1170, 2080), (1150, 2082), (1130, 2084), (1110, 2088)]
# everything right of / below it is background: the garment's edge is the measured line itself (an exclusion, not a flood)
RIGHT_WALL = EDGE_R + [(1110, 2104), (1792, 2104), (1792, 200), (1005, 200)]
def offset(line, d):
    """The polyline moved d px to the left of its direction of travel (image y down): for EDGE_R, onto the wall."""
    out = []
    for i, (x, y) in enumerate(line):
        a, b = line[max(i - 1, 0)], line[min(i + 1, len(line) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]; n = (dx * dx + dy * dy) ** 0.5 or 1.0
        out.append((round(x + d * dy / n, 1), round(y - d * dx / n, 1)))
    return out


# and a barrier 2 px outside it, so that the wall's flood cannot enter the shaded cloth anywhere along it
BARRIER_R = offset(EDGE_R, 2.0)

SEAMS = {                                             # each runs from background to background (wall, a gap, the midriff)
    # the shoulder, the armhole, then the crease (the darkest px per row) into the wedge / the midriff
    "armhole-l": [(664, 322), (676, 340), (673, 400), (676, 450), (683, 500), (688, 525), (690, 540), (692, 560), (695, 580),
                  (699, 600), (703, 620), (711, 640), (716, 660), (717, 680), (717, 700), (716, 720), (722, 742)],
    "armhole-r": [(1150, 325), (1136, 344), (1120, 400), (1108, 460), (1109, 500), (1109, 514)],    # the shoulder -> the gap
    "sleeve-skirt-l": [(682, 898), (681, 912), (679, 924), (676, 932), (672, 940), (664, 960), (657, 980), (651, 1000), (645, 1020), (639, 1040),
                       (633, 1060), (627, 1080), (621, 1100), (615, 1120), (611, 1128), (596, 1142)],
}
LM = {"neck-l": (803, 292), "neck-r": (1001, 292), "cf-neck": (900, 334),
      "shoulder-l": (676, 340), "shoulder-r": (1136, 344),
      "underarm-l": (690, 540), "underarm-r": (1108, 505),
      "top-hem-l": (737, 730), "top-hem-r": (1062, 733), "top-hem-cf": (900, 718),
      "waist-l": (742, 777), "waist-r": (1060, 777), "waist-cf": (900, 778),
      "hem-l": (373, 1980), "hem-r": (1429, 1992), "hem-cf": (900, 2099),
      "cuff-out-l": (500, 1102), "cuff-in-l": (611, 1128), "cuff-out-r": (1300, 1098), "cuff-in-r": (1183, 1124)}


def base(path=SRC):
    _kit.fit_to(path)
    return _kit.base(path, PATCHES)


def spec():
    _kit.fit_to(SRC)
    mm = 158.0 / ((LM["neck-r"][0] - LM["neck-l"][0]) * _kit.K)
    v_waist = round((LM["waist-cf"][1] - LM["neck-l"][1]) * _kit.K * mm, 1)
    return {
        "path": SRC, "patches": PATCHES, "view": "torso", "variant": "lehenga",
        "exclude": [FORM, MIDRIFF, WEDGE_L, GAP_R, UNDER_HEM_L, RIGHT_WALL, FLOOR],   # measured polygons, not seeds (a seed leaks into the cloth)
        "bg_barriers": [BARRIER_R],                   # a true garment edge: it holds in every part
        "measured": [EDGE_R, WEDGE_L_SLEEVE, GAP_R_BODY, GAP_R_SLEEVE],         # the build's snap keeps these (the photo's nearest step there is a fold)
        "smooth_k": 3,                                # the traced runs smoothed (no staircase where the snap keeps them)
        "seams": SEAMS,
        "parts": {                                    # merged in this order
            "top": {"box": (600, 200, 1200, 790), "zones": ["top"], "seed_sides": "t"},   # down past the waistband: the side strip
            "sleeves": {"box": (440, 300, 1340, 1150), "zones": ["sleeve-l", "sleeve-r"], "seed_sides": "lr"},
            "skirt": {"box": (300, 760, 1500, 2112), "zones": ["skirt"], "seed_sides": "lrb"},
        },
        "zones": {
            "top": {"seed": (900, 500), "order": 2, "frame": {"axis": ["cf-neck", "top-hem-cf"], "anchor": {"line": ["neck-l", "neck-r"]}}},
            "skirt": {"seed": (900, 1500), "order": 1, "frame": {"axis": ["waist-cf", "hem-cf"], "anchor": {"point": "waist-cf", "vMm": v_waist}, "sagEdge": "hem"}},
            "sleeve-l": {"seed": (600, 800), "order": 3, "frame": {"axis": "midline", "anchor": {"point": "shoulder-l"}, "sagEdge": "cuff-l", "skipTop": 0.15}},
            "sleeve-r": {"seed": (1200, 800), "order": 3, "frame": {"axis": "midline", "anchor": {"point": "shoulder-r"}, "sagEdge": "cuff-r", "skipTop": 0.15}},
        },
        "cuts": {"top": [("neck", LM["neck-l"], LM["neck-r"]), ("top-hem", LM["top-hem-l"], LM["top-hem-r"])],
                 "skirt": [("waist", LM["waist-l"], LM["waist-r"]), ("hem", LM["hem-l"], LM["hem-r"])],
                 "sleeve-l": [("cuff-l", LM["cuff-out-l"], LM["cuff-in-l"])], "sleeve-r": [("cuff-r", LM["cuff-in-r"], LM["cuff-out-r"])]},
        "landmarks": LM,
        "scale": ("neck-l", "neck-r", 158.0, "neck-l -> neck-r = 158 mm (the straight kurta's agreed neck width: the same dress form); "
                  "an assumption, not a measurement of this garment"),
        "settings": {"thetaDeg": {"top": 60, "skirt": 70, "sleeve-l": 70, "sleeve-r": 70}},
        "source_note": "silhouette/sources/torso-lehenga.png (1792 x 2400, as received 2026-11-23, the white-cotton lehenga), the sparkle "
                       "mark patched, cut to 1792 x 2389, resized to 1200 x 1600. Read in parts (silhouette/views/_kit.py); the right "
                       "side's outer edges, the seams, neckline, midriff and landmarks measured on the source by Claude.",
        "trims": {
            "neck": {"order": 3, "type": "insertion", "group": "neck", "edge": "neck"},
            "top-hem": {"order": 3, "type": "edging", "group": "hem", "edge": "top-hem"},
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
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "review", "torso-lehenga")
    os.makedirs(out, exist_ok=True)
    _kit.check(P, X, os.path.join(out, "zones.png"))
