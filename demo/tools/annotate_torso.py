"""The torso view (torso-straight): points measured on source.png, both sides, as typed edges (StepA step 2).

Source: source.png, 1792 x 2400 (the AI image as received; it was assets/torso-base.png). The base: the sparkle mark (bottom right
wall) covered with wall from 200 px to the left and 40 px up, the exact 3:4 cut (1792 x 2389: 11 px of plain wall and stand off the
bottom), resized to 1200 x 1600 (x 0.669643, y 0.669736). This was tools/make_base.py.
As a module (tools/make_plate.py): base(plate_dir), measure(). Run alone: python3 tools/annotate_torso.py
(the automatic checks of annotate.md 9.1; writes nothing).

How the lists were measured (2026-11-21): every edge was read on gridded crops of source.png (2-3x, 10 px grid, true colour and
contrast 1.5-2.6). The edges against the wall (shoulders, sleeve outer edges, the gaps between the cuffs and the body, the body sides,
the hem) and the sleeve / body creases were then placed on the strongest luminance step within 6 px of the reading (a measuring aid;
a weak step kept the reading) and checked again on crops; the lists below are those points every ~8 px, thinned to 0.5 px. Corrected by reading after the first review: the right body side
below y 1902 (the aid had jumped between the front panel's edge and the back panel's strip beside it: the outer silhouette is kept)
and the left body side's last 50 px (a 6 px hook at the hem corner). After the person review ("the left arm has expanded outside
the edge"): the left sleeve's outer edge was read again on 2.5x crops, every 25-50 px (it lay 10-18 px out on the wall: the shaded
sleeve against the light wall is a weak step, so the first reading had stood).
From the reading only (the step there is weak or double): the neck edge (the white front meets the grey band of the back neckline
inside the opening, below the form's edge), the right armhole (a faint line on lit white), the right sleeve's inner edge below
y 1200 (the gap to the body is 3-8 px) and the left cuff.
Both sides are measured; nothing is mirrored. Where the photo is not symmetric the data is not either:
  slit tops   left (580, 1985), right (1214, 1870): where the back panel shows beside the front as a light strip
  underarms   at the top of the underarm fold, where the sleeve leaves the body: left (643, 750), right (1152, 705). (The first
              right one, (1150, 880), followed the crease further down; the person review moved it up to the fold.)
"""
import math
from PIL import Image, ImageDraw, ImageFilter

KX, KY = 1200 / 1792, 1600 / 2389


def base(D):
    im = Image.open(f"{D}/source.png").convert("RGB")
    box = (1600, 2200, 1780, 2390)                       # the sparkle mark: wall from 200 px to the left, 40 px up (the floor light slopes)
    w, h = box[2] - box[0], box[3] - box[1]
    patch = im.crop((box[0] - 200, box[1] - 40, box[2] - 200, box[3] - 40))
    feather = Image.new("L", (w, h), 0)
    ImageDraw.Draw(feather).rectangle((12, 12, w - 12, h - 12), fill=255)
    im.paste(patch, box[:2], feather.filter(ImageFilter.GaussianBlur(6)))
    return im.crop((0, 0, 1792, 2389)).resize((1200, 1600), Image.LANCZOS)


def T(pts):
    return [[round(x * KX, 1), round(y * KY, 1)] for x, y in pts]


# ---- measured on source.png (source px). Directions: top -> bottom, left -> right, as named.
neck_edge = [(762, 378), (768, 386), (775, 396), (788, 405), (800, 413), (825, 420), (850, 425), (875, 427), (897, 428),
             (925, 427), (950, 423), (975, 416), (990, 411), (1000, 406), (1012, 396), (1022, 386), (1031, 376)]
shoulder_l = [(605, 446), (619, 434), (641, 425), (648, 423), (655, 419), (684, 407), (692, 405), (699, 401), (737, 386),
              (752, 379), (762, 378)]
shoulder_r = [(1031, 376), (1038, 380), (1045, 382), (1052, 386), (1075, 394), (1083, 396), (1127, 414), (1135, 416),
              (1157, 425), (1172, 432), (1179, 436), (1185, 441)]
outer_l = [(605, 446), (597, 455), (590, 467), (583, 482), (576, 500), (569, 525), (562, 550), (556, 575), (550, 600), (545, 625),
           (540, 650), (536, 675), (532, 700), (528, 725), (524, 750), (517, 775), (510, 800), (502, 850), (493, 900), (485, 950),
           (476, 1000), (466, 1050), (454, 1100), (445, 1150), (437, 1200), (428, 1250), (420, 1300), (410, 1341)]
cuff_l = [(410, 1341), (450, 1347), (500, 1360), (540, 1369), (573, 1377)]
sleeve_in_l = [(573, 1377), (575, 1370), (576, 1362), (581, 1349), (586, 1316), (590, 1300), (592, 1283), (603, 1233), (604, 1225), (613, 1185), (616, 1175), (620, 1150), (623, 1143), (631, 1113), (632, 1105), (636, 1090), (642, 1057), (648, 1033), (651, 1024), (653, 1008), (658, 983), (659, 967), (662, 950), (662, 925), (664, 917), (664, 900), (663, 891), (660, 883), (657, 867), (654, 859), (653, 850), (651, 842), (652, 833), (646, 783), (641, 767), (641, 759), (643, 750)]
armhole_l = [(605, 446), (611, 462), (613, 471), (619, 486), (621, 494), (621, 502), (623, 509), (624, 518), (626, 526),
             (633, 533), (639, 541), (641, 549), (642, 566), (638, 575), (641, 600), (642, 617), (642, 633), (640, 642),
             (641, 650), (640, 658), (645, 683), (644, 692), (644, 742), (643, 750)]
outer_r = [(1185, 441), (1192, 445), (1198, 451), (1207, 470), (1210, 478), (1212, 487), (1221, 516), (1222, 523), (1228, 544),
           (1229, 552), (1240, 601), (1244, 624), (1248, 639), (1255, 677), (1259, 693), (1269, 747), (1273, 762), (1277, 785),
           (1281, 800), (1283, 816), (1290, 847), (1292, 862), (1296, 877), (1306, 931), (1310, 946), (1318, 993),
           (1320, 1000), (1324, 1024), (1326, 1031), (1336, 1085), (1340, 1100), (1345, 1131), (1350, 1154), (1352, 1170),
           (1354, 1177), (1361, 1216), (1363, 1223), (1364, 1231), (1372, 1269), (1378, 1308), (1384, 1340)]
cuff_r = [(1222, 1374), (1230, 1375), (1238, 1373), (1277, 1368), (1293, 1364), (1317, 1360), (1333, 1356), (1356, 1352),
          (1370, 1348), (1378, 1347), (1384, 1340)]
# y 725-1085 read again (StepA extension, step L4, 2026-11-22: "the long band beside the sleeve"): the first reading lay 4-14 px to the
# right, on the sleeve's shaded side, so the body's fabric covered a strip of it (a dark stripe through the body's pattern). Each row:
# the 50 % crossing of the first fall of >= 14 levels going right from the lit body (blur 1.2 px). Below y 1100 the two agreed (2 px).
sleeve_in_r = [(1222, 1374), (1216, 1350), (1210, 1330), (1204, 1300), (1198, 1270), (1193, 1250), (1188, 1220), (1185, 1200), (1184, 1190), (1180, 1159), (1173, 1117), (1171, 1109), (1170, 1100),
               (1166.0, 1085), (1162.9, 1070), (1159.5, 1055), (1155.9, 1040), (1153.2, 1025), (1149.5, 1010), (1147.0, 995),
               (1144.9, 980), (1143.5, 965), (1143.1, 950), (1142.5, 935), (1142.9, 920), (1142.2, 905), (1141.6, 890), (1141.5, 875),
               (1141.3, 860), (1140.6, 845), (1140.0, 830), (1138.4, 815), (1137.8, 800), (1140.6, 785), (1144.0, 770), (1147.5, 755),
               (1147.8, 740), (1149.0, 725), (1152, 705)]
armhole_r = [(1185, 441), (1178, 450), (1170, 460), (1165, 480), (1161, 500), (1158, 525), (1156, 550), (1153, 575), (1152, 600), (1152, 650), (1152, 705)]
body_l = [(613, 1185), (614, 1218), (610, 1258), (610, 1267), (608, 1275), (599, 1350), (597, 1391), (592, 1425), (592, 1433), (588, 1466), (588, 1474), (585, 1507), (585, 1538), (584, 1546), (585, 1561), (587, 1569), (586, 1585), (587, 1592), (587, 1639), (582, 1692), (582, 1731), (581, 1738), (580, 1762), (579, 1769), (579, 1785), (578, 1792), (579, 1800), (578, 1808), (578, 1838), (579, 1846), (578, 1854), (579, 1862), (578, 1877), (579, 1885), (578, 1892), (578, 1985), (580, 2009), (580, 2034), (583, 2067), (581, 2100), (581, 2141), (582, 2150)]
body_r = [(1184, 1190), (1190, 1235), (1190, 1242), (1203, 1350), (1203, 1358), (1213, 1442), (1214, 1458), (1214, 1492), (1215, 1500), (1216, 1531), (1217, 1538), (1217, 1554), (1216, 1562), (1217, 1577), (1216, 1592), (1217, 1600), (1217, 1623), (1218, 1631), (1217, 1646), (1218, 1654), (1218, 1700), (1219, 1708), (1219, 1746), (1220, 1754), (1219, 1762), (1219, 1800), (1217, 1808), (1216, 1839), (1214, 1854), (1216, 1902), (1216, 1950),
          # y 1980-2140 read again (StepA extension, step L4: "the strip of white beside the slit"): the outer 50 % crossing of the back
          # panel's white folded edge against the wall (blur 0.8 px); the first reading lay 1-4 px inside it. The corner stays.
          (1216.7, 1980), (1215.7, 2000), (1215.6, 2020), (1216.7, 2040), (1217.6, 2060), (1216.7, 2080), (1215.6, 2100),
          (1214.6, 2110), (1213.6, 2120), (1212.6, 2130), (1213.0, 2140), (1212, 2150)]
# x 760-1060 read again (StepA extension, step L4, 2026-11-22): the hem rises over the stand (the first reading ran straight across at
# y 2200 and the front covered 20-37 px of the stand's top). Each column: the garment's last luminance step going down (blur 1.2 px,
# central difference >= 10 levels): white -> floor at x 760-840, white -> stand at 850-960, the hem's shaded fold -> floor at 970-1060.
# x 720-750: no step (the garment's shade there equals the floor's): the first reading stays.
hem_edge = [(582, 2150), (607, 2164), (614, 2167), (627, 2175), (635, 2178), (648, 2186), (657, 2190), (673, 2195),
            (690, 2199), (708, 2201), (717, 2198), (725, 2200), (742, 2202), (750, 2200), (760, 2199), (770, 2196),
            (780, 2193), (790, 2189), (800, 2185), (810, 2181), (820, 2177), (830, 2172), (840, 2169), (850, 2168), (860, 2166),
            (870, 2164), (880, 2163), (890, 2162), (900, 2162), (910, 2161), (920, 2162), (930, 2163), (940, 2164), (950, 2166),
            (960, 2168), (970, 2170), (980, 2172), (990, 2176), (1000, 2180), (1010, 2185), (1020, 2188), (1030, 2192),
            (1040, 2194), (1050, 2197), (1060, 2200), (1075, 2200),
            (1110, 2200), (1118, 2199), (1152, 2190), (1160, 2186), (1176, 2180), (1192, 2171), (1197, 2166), (1201, 2159),
            (1206, 2154), (1212, 2150)]

def fit_smooth(pts, along, degree):
    """A smooth curve through measured points: least-squares polynomial of the other coordinate against `along` (0 = x, 1 = y),
    the two end points kept exactly (a linear correction), evaluated at the measured positions. For seams and cuff folds, which are
    smooth: the measured points wobble by 1-3 px."""
    o = 1 - along
    t = [p[along] for p in pts]; v = [p[o] for p in pts]
    n = degree + 1
    A = [[sum(ti ** (i + j) for ti in t) for j in range(n)] for i in range(n)]
    b = [sum(vi * ti ** i for ti, vi in zip(t, v)) for i in range(n)]
    for i in range(n):                                   # Gauss elimination
        piv = max(range(i, n), key=lambda r: abs(A[r][i])); A[i], A[piv] = A[piv], A[i]; b[i], b[piv] = b[piv], b[i]
        for r in range(i + 1, n):
            f = A[r][i] / A[i][i]
            for c in range(i, n): A[r][c] -= f * A[i][c]
            b[r] -= f * b[i]
    c = [0.0] * n
    for i in range(n - 1, -1, -1): c[i] = (b[i] - sum(A[i][k] * c[k] for k in range(i + 1, n))) / A[i][i]
    f = lambda x: sum(c[k] * x ** k for k in range(n))
    e0, e1 = v[0] - f(t[0]), v[-1] - f(t[-1])
    out = []
    for i, ti in enumerate(t):
        w = (ti - t[0]) / ((t[-1] - t[0]) or 1)
        val = v[i] if i in (0, len(t) - 1) else round(f(ti) + e0 + (e1 - e0) * w, 1)
        out.append((ti, val) if along == 0 else (val, ti))
    return out


# the measured seams and cuff folds, made smooth (after the person review of 2026-11-22: "an unusual curve" on the left armhole,
# "irregular" cuff lace lines); the shared ends stay exactly where they were measured
armhole_l, armhole_r = fit_smooth(armhole_l, 1, 3), fit_smooth(armhole_r, 1, 3)
cuff_l, cuff_r = fit_smooth(cuff_l, 0, 2), fit_smooth(cuff_r, 0, 2)

SH_L, SH_R = shoulder_l[0], shoulder_r[-1]                # shoulder points: the armhole seam meets the top silhouette
NECK_L, NECK_R = neck_edge[0], neck_edge[-1]
UA_L, UA_R = armhole_l[-1], armhole_r[-1]               # underarms (see above)
CUFF_OUT_L, CUFF_IN_L, CUFF_OUT_R, CUFF_IN_R = cuff_l[0], cuff_l[-1], cuff_r[-1], cuff_r[0]
GAP_L, GAP_R = body_l[0], body_r[0]                     # where the body side comes out from under the sleeve (the wall gap begins)
HEM_L, HEM_R = hem_edge[0], hem_edge[-1]
SLIT_L, SLIT_R = (580, 1985), (1214, 1870)
CF_X = 897                                              # the form's centre-front tape
# From the underarm down to where the wall gap opens, the body ends on the sleeve's inner edge: ONE list, shared by the front and
# the sleeve (a seam). Below it the sleeve's inner edge is free (against the gap) and the body side is free.
I_GAP_L, I_GAP_R = sleeve_in_l.index(GAP_L), sleeve_in_r.index(GAP_R)
sleeve_gap_l, sleeve_body_l = sleeve_in_l[:I_GAP_L + 1], sleeve_in_l[I_GAP_L:]      # cuff-in -> gap top, gap top -> underarm
sleeve_gap_r, sleeve_body_r = sleeve_in_r[:I_GAP_R + 1], sleeve_in_r[I_GAP_R:]


def y_at(pts, x):
    for a, b in zip(pts, pts[1:]):
        if min(a[0], b[0]) <= x <= max(a[0], b[0]) and a[0] != b[0]:
            return a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0])


def x_at(pts, y):
    for a, b in zip(pts, pts[1:]):
        if min(a[1], b[1]) <= y <= max(a[1], b[1]) and a[1] != b[1]:
            return a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1])


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


def parallel(pts, d, away, step=2.0, k=4):
    """The curve at distance d from pts (plate px), on the side away from `away`: pts densified every `step` px, each normal from
    the points k steps before and after (a smooth normal: no swing at a vertex or at an end)."""
    D = [list(pts[0])]
    for a, b in zip(pts, pts[1:]):
        n = max(1, round(math.dist(a, b) / step))
        D += [[a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n] for i in range(1, n + 1)]
    out = []
    for i, (x, y) in enumerate(D):
        a, b = D[max(0, i - k)], D[min(len(D) - 1, i + k)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        n = math.hypot(tx, ty) or 1
        nx, ny = -ty / n, tx / n
        if (x - away[0]) * nx + (y - away[1]) * ny < 0: nx, ny = -nx, -ny
        out.append([round(x + nx * d, 1), round(y + ny * d, 1)])
    return out


def inside(pt, poly):
    c = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > pt[1]) != (y2 > pt[1]) and pt[0] < (x2 - x1) * (pt[1] - y1) / (y2 - y1) + x1:
            c = not c
    return c


def thin(pts, tol):
    """Douglas-Peucker."""
    if len(pts) < 3: return pts
    a, b = pts[0], pts[-1]; dx, dy = b[0] - a[0], b[1] - a[1]; n = math.hypot(dx, dy) or 1
    k, dm = 0, 0.0
    for i in range(1, len(pts) - 1):
        dd = abs((pts[i][0] - a[0]) * dy - (pts[i][1] - a[1]) * dx) / n
        if dd > dm: k, dm = i, dd
    return [a, b] if dm <= tol else thin(pts[:k + 1], tol)[:-1] + thin(pts[k:], tol)


def poly_area(pts):
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))) / 2


def plen(pts):
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


def measure():
    import platedat
    LM = {"neck-l": NECK_L, "neck-r": NECK_R, "cf-neck": (CF_X, y_at(neck_edge, CF_X)), "shoulder-l": SH_L, "shoulder-r": SH_R,
          "underarm-l": UA_L, "underarm-r": UA_R, "cuff-out-l": CUFF_OUT_L, "cuff-in-l": CUFF_IN_L, "cuff-in-r": CUFF_IN_R,
          "cuff-out-r": CUFF_OUT_R, "slit-l": SLIT_L, "slit-r": SLIT_R, "hem-l": HEM_L, "hem-r": HEM_R, "hem-cf": (CF_X, y_at(hem_edge, CF_X))}
    L = {k: T([v])[0] for k, v in LM.items()}
    # scale: the neck view's agreed neck width (neck-l -> neck-r = 158 mm), so that the two front views have the same scale
    # (StepA step 2.3; the old assumption, shoulder width 370 mm, is written in the results with this one)
    mm_per_px = 158 / math.dist(L["neck-l"], L["neck-r"])
    edges = {
        "shoulder-l": {"type": "free", "points": T(shoulder_l)},
        "neck": {"type": "cut", "points": T(neck_edge)},
        "shoulder-r": {"type": "free", "points": T(shoulder_r)},
        "armhole-l": {"type": "seam", "zones": ["front", "sleeve-l"], "points": T(armhole_l)},
        "armhole-r": {"type": "seam", "zones": ["front", "sleeve-r"], "points": T(armhole_r)},
        "sleeve-body-l": {"type": "seam", "zones": ["front", "sleeve-l"], "points": T(sleeve_body_l)},   # the sleeve over the body
        "sleeve-body-r": {"type": "seam", "zones": ["front", "sleeve-r"], "points": T(sleeve_body_r)},
        "body-l": {"type": "free", "points": T(body_l)},
        "body-r": {"type": "free", "points": T(body_r)},
        "hem": {"type": "free", "points": T(hem_edge)},
        "outer-l": {"type": "free", "points": T(outer_l)},
        "cuff-l": {"type": "free", "points": T(cuff_l)},
        "sleeve-gap-l": {"type": "free", "points": T(sleeve_gap_l)},
        "outer-r": {"type": "free", "points": T(outer_r)},
        "cuff-r": {"type": "free", "points": T(cuff_r)},
        "sleeve-gap-r": {"type": "free", "points": T(sleeve_gap_r)},
    }
    zones = {
        "front": {"order": 1, "frame": {"axis": ["cf-neck", "hem-cf"], "anchor": {"line": ["neck-l", "neck-r"]}, "sagEdge": "hem"},
                  "outline": [["shoulder-l", 1], ["neck", 1], ["shoulder-r", 1], ["armhole-r", 1], ["sleeve-body-r", -1], ["body-r", 1],
                              ["hem", -1], ["body-l", -1], ["sleeve-body-l", 1], ["armhole-l", -1]]},
        "sleeve-l": {"order": 2, "frame": {"axis": "midline", "anchor": {"point": "shoulder-l"}, "sagEdge": "cuff-l", "skipTop": 0.15},
                     "outline": [["outer-l", 1], ["cuff-l", 1], ["sleeve-gap-l", 1], ["sleeve-body-l", 1], ["armhole-l", -1]]},
        "sleeve-r": {"order": 2, "frame": {"axis": "midline", "anchor": {"point": "shoulder-r"}, "sagEdge": "cuff-r", "skipTop": 0.15},
                     "outline": [["armhole-r", 1], ["sleeve-body-r", -1], ["sleeve-gap-r", -1], ["cuff-r", 1], ["outer-r", -1]]},
    }
    P = {"view": "torso", "variant": "straight-kurta", "viewBox": [1200, 1600], "mmPerPx": round(mm_per_px, 4),
         "scaleNote": "neck-l -> neck-r = 158 mm (the neck view's agreed value; the old assumption, shoulder width 370 mm, would give "
                      f"{round(370 / math.dist(L['shoulder-l'], L['shoulder-r']), 4)} mm/px)",
         "source": "source.png (was assets/torso-base.png), sparkle patched, cut to 1792 x 2389, resized to 1200 x 1600. "
                   "Points measured on source.png by Claude, both sides (StepA step 2).",
         "landmarks": L, "edges": edges, "zones": zones, "stitches": {}, "settings": {"shadeSmoothMm": 0}}
    O = {zn: platedat.outline(P, zn) for zn in zones}
    mm = mm_per_px
    tw = lambda w: w / mm
    neck = T(neck_edge)
    below = lambda pts: [p for p in pts]
    # trims: each lace hangs on its garment edge between its anchors (the build derives the line: StepA extension, step L1); the
    # lace's own width and repeat are the lace's. anchor: where the motif is placed (default the frame's u = 0); cut: a real end
    trims = {
        "neck": {"order": 3, "type": "insertion", "edge": "neck", "from": "neck-l", "to": "neck-r"},
        "cuff-l": {"order": 3, "type": "edging", "edge": "cuff-l"},
        "cuff-r": {"order": 3, "type": "edging", "edge": "cuff-r"},
        "slit-l": {"order": 3, "type": "insertion", "edge": "body-l", "from": "slit-l", "to": "hem-l", "anchor": "to", "cut": ["from"]},
        "slit-r": {"order": 3, "type": "insertion", "edge": "body-r", "from": "slit-r", "to": "hem-r", "anchor": "to", "cut": ["from"]},
        "hem": {"order": 3, "type": "edging", "edge": "hem", "from": "hem-l", "to": "hem-r", "join": "mitre with the slits"},
    }
    P["trims"] = trims
    return P




# ---- checks (annotate.md 9.1)
def segs_cross(p1, p2, p3, p4):
    def o(a, b, c): return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return o(p1, p2, p3) * o(p1, p2, p4) < 0 and o(p3, p4, p1) * o(p3, p4, p2) < 0


def checks(P):
    import platedat
    mono = lambda pts: all(b[1] >= a[1] for a, b in zip(pts, pts[1:]))
    for nm, e in (("armhole-l", armhole_l), ("armhole-r", armhole_r), ("body-l", body_l), ("body-r", body_r), ("outer-l", outer_l), ("outer-r", outer_r)):
        assert mono(e), f"{nm}: must go top -> bottom"
    # the sleeves stay on their side of the body where they meet it: sleeve inner edge vs the body edge in the wall gaps
    ys_l, ys_r = range(GAP_L[1] + 5, CUFF_IN_L[1] - 5, 5), range(GAP_R[1] + 5, CUFF_IN_R[1] - 5, 5)
    gap_l = [x_at(body_l, y) - x_at(sleeve_in_l, y) for y in ys_l]       # > 0: the wall shows between the sleeve and the body
    gap_r = [x_at(sleeve_in_r, y) - x_at(body_r, y) for y in ys_r]
    print(f"wall gap sleeve -> body: left {min(gap_l):.1f} .. {max(gap_l):.1f} px, right {min(gap_r):.1f} .. {max(gap_r):.1f} px (an overlap must be <= 1.6)")
    assert min(gap_l) >= -1.6 and min(gap_r) >= -1.6
    O = {zn: platedat.outline(P, zn) for zn in P["zones"]}
    for zn, o in O.items():
        n = len(o)
        X = sum(1 for i in range(n) for j in range(i + 2, n) if not (i == 0 and j == n - 1) and segs_cross(o[i], o[(i + 1) % n], o[j], o[(j + 1) % n]))
        print(f"outline {zn}: {n} points, {X} self-crossings")
        assert X == 0
    L, mm = P["landmarks"], P["mmPerPx"]
    sw = math.dist(L["shoulder-l"], L["shoulder-r"]) * mm
    print(f"scale {mm} mm/px (neck width 158 mm) | shoulder width {sw:.0f} mm (assumed 370) | shoulder -> neck: left "
          f"{math.dist(L['shoulder-l'], L['neck-l']) * mm:.0f} mm, right {math.dist(L['shoulder-r'], L['neck-r']) * mm:.0f} mm")
    # left / right against a mirror about the centre front (information: the photo is not symmetric)
    cx = L["cf-neck"][0]
    for a, b in (("shoulder-l", "shoulder-r"), ("neck-l", "neck-r"), ("underarm-l", "underarm-r"), ("cuff-out-l", "cuff-out-r"),
                 ("cuff-in-l", "cuff-in-r"), ("slit-l", "slit-r"), ("hem-l", "hem-r")):
        pa, pb = L[a], L[b]
        print(f"  {a:10} / {b:10}  mirror difference dx {(2 * cx - pa[0]) - pb[0]:+6.1f} px, dy {pa[1] - pb[1]:+6.1f} px")


if __name__ == "__main__":
    checks(measure())
