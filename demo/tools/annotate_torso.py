"""The torso view (torso-straight): points measured on source.png, both sides, as typed edges (StepA step 2).

Source: source.png, 1792 x 2400 (the AI image as received; it was assets/torso-base.png). The base: the sparkle mark (bottom right
wall) covered with wall from 200 px to the left and 40 px up, the exact 3:4 cut (1792 x 2389: 11 px of plain wall and stand off the
bottom), resized to 1200 x 1600 (x 0.669643, y 0.669736). This was tools/make_base.py.
As a module (tools/make_plate.py): base(plate_dir), measure(), review(P, base). Run alone: python3 tools/annotate_torso.py
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
sleeve_in_r = [(1222, 1374), (1216, 1350), (1210, 1330), (1204, 1300), (1198, 1270), (1193, 1250), (1188, 1220), (1185, 1200), (1184, 1190), (1180, 1159), (1173, 1117), (1171, 1109), (1170, 1100), (1161, 1062), (1161, 1055), (1158, 1031), (1158, 1024), (1162, 1015), (1158, 985), (1158, 977), (1155, 954), (1155, 946), (1152, 923), (1152, 915), (1151, 908), (1148, 900), (1148, 883), (1150, 880), (1150, 850), (1150, 800), (1153, 750), (1152, 705)]
armhole_r = [(1185, 441), (1178, 450), (1170, 460), (1165, 480), (1161, 500), (1158, 525), (1156, 550), (1153, 575), (1152, 600), (1152, 650), (1152, 705)]
body_l = [(613, 1185), (614, 1218), (610, 1258), (610, 1267), (608, 1275), (599, 1350), (597, 1391), (592, 1425), (592, 1433), (588, 1466), (588, 1474), (585, 1507), (585, 1538), (584, 1546), (585, 1561), (587, 1569), (586, 1585), (587, 1592), (587, 1639), (582, 1692), (582, 1731), (581, 1738), (580, 1762), (579, 1769), (579, 1785), (578, 1792), (579, 1800), (578, 1808), (578, 1838), (579, 1846), (578, 1854), (579, 1862), (578, 1877), (579, 1885), (578, 1892), (578, 1985), (580, 2009), (580, 2034), (583, 2067), (581, 2100), (581, 2141), (582, 2150)]
body_r = [(1184, 1190), (1190, 1235), (1190, 1242), (1203, 1350), (1203, 1358), (1213, 1442), (1214, 1458), (1214, 1492), (1215, 1500), (1216, 1531), (1217, 1538), (1217, 1554), (1216, 1562), (1217, 1577), (1216, 1592), (1217, 1600), (1217, 1623), (1218, 1631), (1217, 1646), (1218, 1654), (1218, 1700), (1219, 1708), (1219, 1746), (1220, 1754), (1219, 1762), (1219, 1800), (1217, 1808), (1216, 1839), (1214, 1854), (1216, 1902), (1216, 1950), (1215, 2000), (1214, 2050), (1213, 2100), (1212, 2133), (1212, 2150)]
hem_edge = [(582, 2150), (607, 2164), (614, 2167), (627, 2175), (635, 2178), (648, 2186), (657, 2190), (673, 2195),
            (690, 2199), (708, 2201), (717, 2198), (725, 2200), (742, 2202), (750, 2200), (758, 2200), (767, 2203),
            (800, 2203), (808, 2202), (825, 2202), (842, 2200), (858, 2200), (892, 2198), (908, 2198), (917, 2199),
            (933, 2199), (942, 2200), (958, 2200), (992, 2202), (1025, 2202), (1033, 2203), (1050, 2203), (1075, 2200),
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
GRID_L, GRID_R = (632, 950), (1168, 1000)               # a point of each front grid side under the sleeve (the grid lies outside the outline)


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


def clip_extend(centre, outline, reach=90):
    """Trim centre must stay inside the zone outline: drop outside end points, extend each end along its last segment."""
    c = [list(p) for p in centre]
    while c and not inside(c[0], outline): c.pop(0)
    while c and not inside(c[-1], outline): c.pop()
    for end in (0, -1):
        a, b = (c[1], c[0]) if end == 0 else (c[-2], c[-1])
        n = math.dist(a, b) or 1
        ux, uy = (b[0] - a[0]) / n, (b[1] - a[1]) / n
        t, last = 1.0, None
        while t <= reach and inside((b[0] + ux * t, b[1] + uy * t), outline):
            last = [round(b[0] + ux * t, 1), round(b[1] + uy * t, 1)]
            t += 1.0
        if last:
            c.insert(0, last) if end == 0 else c.append(last)
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
    # grids (the Coons patch, until StepA step 4): the outline cuts, so each grid edge lies on or OUTSIDE the outline
    side_l = [SH_L, GRID_L] + [(x - 6, y) for x, y in body_l[1:-1]] + [(HEM_L[0] - 6, HEM_L[1])]
    side_r = [SH_R, GRID_R] + [(x + 6, y) for x, y in body_r[1:-1]] + [(HEM_R[0] + 6, HEM_R[1])]
    zones = {
        "front": {"order": 1,
                  "outline": [["shoulder-l", 1], ["neck", 1], ["shoulder-r", 1], ["armhole-r", 1], ["sleeve-body-r", -1], ["body-r", 1],
                              ["hem", -1], ["body-l", -1], ["sleeve-body-l", 1], ["armhole-l", -1]],
                  "grid": {"top": T(shoulder_l + shoulder_r), "left": T(side_l), "right": T(side_r),
                           "bottom": T([side_l[-1]] + hem_edge[1:-1] + [side_r[-1]])}},
        "sleeve-l": {"order": 2,
                     "outline": [["outer-l", 1], ["cuff-l", 1], ["sleeve-gap-l", 1], ["sleeve-body-l", 1], ["armhole-l", -1]],
                     "grid": {"top": T([SH_L, SH_L]), "left": T(outer_l), "right": T(armhole_l + sleeve_in_l[::-1][1:]), "bottom": T(cuff_l)}},
        "sleeve-r": {"order": 2,
                     "outline": [["armhole-r", 1], ["sleeve-body-r", -1], ["sleeve-gap-r", -1], ["cuff-r", 1], ["outer-r", -1]],
                     "grid": {"top": T([SH_R, SH_R]), "left": T(armhole_r + sleeve_in_r[::-1][1:]), "right": T(outer_r), "bottom": T(cuff_r)}},
    }
    P = {"view": "torso", "variant": "straight-kurta", "viewBox": [1200, 1600], "mmPerPx": round(mm_per_px, 4),
         "scaleNote": "neck-l -> neck-r = 158 mm (the neck view's agreed value; the old assumption, shoulder width 370 mm, would give "
                      f"{round(370 / math.dist(L['shoulder-l'], L['shoulder-r']), 4)} mm/px)",
         "source": "source.png (was assets/torso-base.png), sparkle patched, cut to 1792 x 2389, resized to 1200 x 1600. "
                   "Points measured on source.png by Claude, both sides (StepA step 2).",
         "landmarks": L, "edges": edges, "zones": zones, "stitches": {}, "settings": {"shadeSmoothMm": 0}}
    O = {zn: platedat.outline(P, zn) for zn in zones}
    for zn in ("sleeve-l", "sleeve-r"):                    # the sleeve cap is a point: the fabric width = area / mean side length (until step 4)
        z = zones[zn]
        zones[zn]["widthPx"] = round(poly_area(O[zn]) / ((plen(z["grid"]["left"]) + plen(z["grid"]["right"])) / 2), 1)
    mm = mm_per_px
    tw = lambda w: w / mm
    neck = T(neck_edge)
    below = lambda pts: [p for p in pts]
    keep = lambda c, zone: [p for p in c if inside(p, O[zone])]
    hem_c = [p for p in keep(parallel(T(hem_edge), tw(15), T([(897, 2350)])[0]), "front") if L["hem-l"][0] <= p[0] <= L["hem-r"][0]]
    trims = {
        "neck": {"order": 3, "widthMm": 12, "type": "insertion", "edge": "neck", "offsetMm": 6,
                 "from": "neck-l", "to": "neck-r",                # ends below the corner anchors (person review 2026-11-22)
                 "centre": [p for p in keep(parallel(neck, tw(6), T([(CF_X, 300)])[0]), "front") if L["neck-l"][0] <= p[0] <= L["neck-r"][0]]},
        "cuff-l": {"order": 3, "widthMm": 25, "type": "edging", "edge": "cuff-l", "offsetMm": 12.5,
                   "centre": keep(parallel(T(cuff_l), tw(12.5), T([(490, 1500)])[0]), "sleeve-l")},
        "cuff-r": {"order": 3, "widthMm": 25, "type": "edging", "edge": "cuff-r", "offsetMm": 12.5,
                   "centre": keep(parallel(T(cuff_r), tw(12.5), T([(1300, 1500)])[0]), "sleeve-r")},
        "slit-l": {"order": 3, "widthMm": 8, "type": "insertion", "edge": "body-l", "offsetMm": 4, "from": "slit-l", "to": "hem-l",
                   "centre": keep(parallel(T([p for p in body_l if p[1] >= SLIT_L[1]]), tw(4), T([(400, 2000)])[0]), "front")},
        "slit-r": {"order": 3, "widthMm": 8, "type": "insertion", "edge": "body-r", "offsetMm": 4, "from": "slit-r", "to": "hem-r",
                   "centre": keep(parallel(T([p for p in body_r if p[1] >= SLIT_R[1]]), tw(4), T([(1400, 2000)])[0]), "front")},
        # the hem lace ends above the corner anchors (hem-l, hem-r), after the person review of 2026-11-22
        "hem": {"order": 3, "widthMm": 30, "type": "edging", "edge": "hem", "offsetMm": 15, "from": "hem-l", "to": "hem-r",
                "join": "over the slit trims", "centre": hem_c},
    }
    for n in trims:                                        # every 2 px is more than a trim needs: thin to 0.05 px
        trims[n]["centre"] = thin(trims[n]["centre"], 0.05)
    P["trims"] = trims
    return P


# ---- annotate.png: colour code on the exact base (annotate.md section 3)
RED, BLUE, PURPLE, ORANGE, GOLD, TEAL, GREEN = (229, 57, 53), (30, 99, 233), (142, 36, 170), (251, 140, 0), (199, 145, 0), (0, 137, 123), (46, 125, 50)


def review(P, base_img):
    img = base_img.copy()
    d = ImageDraw.Draw(img)

    def line(pts, col, w=2):
        d.line([tuple(p) for p in pts], fill=col, width=w, joint="curve")

    def dashed(pts, col, w=2, on=7, off=5):
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
    E = P["edges"]
    for n in ("armhole-l", "armhole-r"):                    # shared seams: red towards the body, blue towards the sleeve
        away = P["landmarks"]["cf-neck"]
        line(offset(E[n]["points"], 1.5, away), RED, 1)
        line(offset(E[n]["points"], -1.5, away), BLUE, 1)
    for n in ("shoulder-l", "shoulder-r", "body-l", "body-r", "hem"): line(E[n]["points"], RED)
    dashed(E["neck"]["points"], RED)
    for n in ("sleeve-body-l", "sleeve-body-r"):           # shared: red towards the body, blue towards the sleeve
        away = P["landmarks"]["cf-neck"]
        line(offset(E[n]["points"], 1.5, away), RED, 1)
        line(offset(E[n]["points"], -1.5, away), BLUE, 1)
    for n in ("outer-l", "cuff-l", "sleeve-gap-l", "outer-r", "cuff-r", "sleeve-gap-r"): line(E[n]["points"], BLUE)
    col = {"neck": PURPLE, "cuff-l": ORANGE, "cuff-r": ORANGE, "hem": GOLD, "slit-l": TEAL, "slit-r": TEAL}
    for n, t in P["trims"].items(): line(t["centre"], col[n], 1)
    L = P["landmarks"]
    line([L["neck-l"], L["neck-r"]], GREEN, 2)
    for x, y in L.values():
        d.ellipse((x - 4, y - 4, x + 4, y + 4), fill="black", outline="white", width=1)
    return img


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
    for zn, zv in P["zones"].items():
        g = zv["grid"]
        for a, b in ((g["top"][0], g["left"][0]), (g["top"][-1], g["right"][0]), (g["bottom"][0], g["left"][-1]), (g["bottom"][-1], g["right"][-1])):
            assert math.dist(a, b) < 0.05, (zn, a, b)
    print("grid corners meet: yes")
    for zn, o in O.items():
        n = len(o)
        X = sum(1 for i in range(n) for j in range(i + 2, n) if not (i == 0 and j == n - 1) and segs_cross(o[i], o[(i + 1) % n], o[j], o[(j + 1) % n]))
        print(f"outline {zn}: {n} points, {X} self-crossings")
        assert X == 0
    for tn, t in P["trims"].items():
        zone = "sleeve-l" if tn == "cuff-l" else "sleeve-r" if tn == "cuff-r" else "front"
        bad = [p for p in t["centre"] if not inside(p, O[zone])]
        print(f"trim {tn}: {len(bad)} of {len(t['centre'])} centre points outside the {zone} outline")
        assert not bad
    for side in ("left", "right"):
        e = P["zones"]["front"]["grid"][side]
        a, b = e[0], e[-1]
        Ln = math.dist(a, b)
        dev = max(abs((b[0] - a[0]) * (a[1] - p[1]) - (a[0] - p[0]) * (b[1] - a[1])) / Ln for p in e)
        print(f"front grid {side} bulge {dev:.0f} px = {100 * dev / Ln:.1f} % (must be <= 5 %)")
        assert dev / Ln <= 0.05
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
