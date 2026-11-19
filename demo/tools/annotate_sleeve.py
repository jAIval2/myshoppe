"""Throwaway: annotate the shoulder-and-sleeve view (sleeve-straight) from points measured on source.png.

Source points are in source.png pixels (2048 x 2048). The plate is the 3:4 crop x 512..2048
(the garment runs off the right border), resized to 1200 x 1600 (factor 0.78125).
Writes base.jpg, zones.json, annotate.png into the plate folder, and runs the checks of annotate.md 7.1.

Every list below was read on gridded crops of source.png (tools/gridcrop.py), not guessed:
  silhouette (outer sleeve, far shoulder): colour distance to the wall, checked on crops
  armhole seam, wall gap under the arm, cuff edge, mannequin arm: gridded true-colour and x2.4 crops
  neckline and its top-stitch: x3 crops
usage: python3 tools/annotate_sleeve.py assets/plates/sleeve-straight
"""
import json, math, sys
from PIL import Image, ImageDraw, ImageFilter

D = sys.argv[1]
X0, K = 512, 1200 / 1536
src = Image.open(f"{D}/source.png").convert("RGB")

# ---- the base: patch the sparkle mark (it sits on the white garment, bottom right), crop, resize
patched = src.copy()
box = (1868, 1868, 2010, 2010)
feather = Image.new("L", (box[2] - box[0], box[3] - box[1]), 0)
ImageDraw.Draw(feather).rectangle((12, 12, feather.width - 12, feather.height - 12), fill=255)
patched.paste(src.crop((box[0] - 190, box[1], box[2] - 190, box[3])), box[:2], feather.filter(ImageFilter.GaussianBlur(8)))
base = patched.crop((X0, 0, X0 + 1536, 2048)).resize((1200, 1600), Image.LANCZOS)
base.save(f"{D}/base.jpg", quality=94, subsampling=0)


def T(pts):
    return [[round((x - X0) * K, 1), round(y * K, 1)] for x, y in pts]


# ---- landmarks, measured on source.png
S = (1003, 117)          # shoulder point: the armhole seam meets the top silhouette
A = (974, 127)           # sleeve cap, on the silhouette, left of S
NECK_L, NECK_R = (1262, 32), (1780, 150)
UNDERARM = (1042, 977)   # the sleeve leaves the body; the wall shows from here
ELBOW = (554, 1150)      # outer edge at the elbow fold
CUFF_OUT = (884, 1892)   # outer corner of the cuff opening
CUFF_IN = (1239, 1706)   # inner end of the cuff edge, where it meets the sleeve inner edge
P = {"neck-l": NECK_L, "neck-r": NECK_R, "shoulder": S, "underarm": UNDERARM,
     "elbow": ELBOW, "cuff-out": CUFF_OUT, "cuff-in": CUFF_IN}

# ---- armhole seam: ONE list. Front left edge and sleeve inner edge both use it.
seam = [(1024, 126), (1049, 133), (1069, 144), (1086, 156), (1099, 173), (1113, 188), (1127, 205),
        (1141, 224), (1152, 247), (1172, 327), (1190, 400), (1193, 482), (1191, 555), (1186, 610),
        (1167, 673), (1147, 713), (1127, 747), (1107, 807), (1093, 860), (1073, 907), (1053, 960), UNDERARM]
# Below the underarm the wall shows between the arm and the body (gap closes at (1050, 1399)).
# Front edge = body side of the gap. Sleeve edge = arm side. Both start at UNDERARM.
body_gap = [(1051, 998), (1063, 1048), (1072, 1086), (1076, 1115), (1072, 1152), (1067, 1190),
            (1065, 1232), (1060, 1249), (1055, 1308), (1053, 1354), (1050, 1399)]
# hidden behind the sleeve down to where the body re-appears under the cuff
body_hidden = [(936, 1899)]
body_low = [(932, 1917), (926, 1955), (922, 1997), (920, 2048)]
slv_gap = [(1022, 994), (997, 1036), (963, 1086), (934, 1123), (920, 1148), (934, 1157), (949, 1173),
           (959, 1194), (963, 1223), (964, 1249), (975, 1281), (1000, 1299), (1016, 1326),
           (1030, 1358), (1050, 1399), (1071, 1422), (1098, 1458), (1121, 1499), (1139, 1526),
           (1153, 1558), (1192, 1608), (1218, 1660), CUFF_IN]

# sleeve outer edge (silhouette against the wall), shoulder -> elbow -> cuff
outer = [A, (952, 144), (930, 160), (899, 200), (874, 250), (852, 300), (835, 350), (820, 400), (798, 450),
         (776, 500), (754, 550), (734, 600), (714, 650), (695, 700), (676, 750), (657, 800), (640, 850),
         (623, 900), (606, 950), (591, 1000), (577, 1050), (565, 1100), ELBOW, (560, 1200), (580, 1250),
         (600, 1300), (621, 1350), (644, 1400), (666, 1450), (690, 1500), (714, 1550), (739, 1600),
         (764, 1650), (789, 1700), (816, 1750), (840, 1800), (864, 1850), CUFF_OUT]
# cuff edge (the sleeve end), outer corner -> inner end
cuff_edge = [CUFF_OUT, (905, 1880), (930, 1863), (963, 1842), (1001, 1822), (1040, 1801), (1100, 1767),
             (1150, 1746), (1200, 1721), CUFF_IN]

# top silhouette of the shoulder, shoulder point -> neck-l
shoulder_top = [S, (1022, 109), (1049, 100), (1077, 92), (1102, 86), (1124, 80), (1155, 72), (1200, 50),
                (1235, 38), NECK_L]
neck_edge = [NECK_L, (1285, 34), (1300, 38), (1330, 47), (1350, 57), (1375, 72), (1400, 85), (1427, 100),
             (1450, 113), (1477, 128), (1503, 143), (1530, 151), (1550, 156), (1600, 172), (1625, 183),
             (1650, 188), (1673, 192), (1700, 197), (1733, 200), (1760, 200), (1778, 194), (1785, 180),
             (1784, 165), NECK_R]
far_shoulder = [NECK_R, (1800, 161), (1825, 175), (1850, 188), (1875, 205), (1900, 221), (1925, 236),
                (1950, 251), (1975, 267), (2000, 287), (2025, 311), (2048, 335)]
# mannequin arm below the cuff: in FRONT of the body, so it stays outside every zone (a notch in the front)
arm_right = [(2048, 2048), (1450, 2048), (1445, 2020), (1437, 1998), (1425, 1973), (1409, 1951), (1391, 1926),
             (1368, 1901), (1360, 1896), (1354, 1874), (1341, 1846), (1332, 1821), (1320, 1803), (1302, 1781),
             (1282, 1760), (1262, 1737), CUFF_IN]
arm_left = [(1040, 1801), (1047, 1849), (1063, 1867), (1080, 1897), (1097, 1922), (1117, 1947), (1138, 1972),
            (1159, 1997), (1184, 2026), (1201, 2048)]
# visible cuff top-stitch
cuff_stitch = [(875, 1812), (917, 1788), (967, 1758), (1025, 1729), (1067, 1708), (1100, 1687)]

# ---- plate-frame data
L = {k: T([v])[0] for k, v in P.items()}
mm_per_px = 470 / math.dist(L["shoulder"], L["cuff-out"])     # scale: shoulder -> cuff-out = 470 mm
neck = T(neck_edge)


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


opening = T([(1550, 60)])[0]                    # inside the neck opening (the form's neck)
below_cuff = T([(1000, 2000)])[0]               # outside the garment, below the cuff edge
neck_trim = offset(neck, 6 / mm_per_px, opening)               # centre 6 mm inside the edge
cuff_trim = offset(T(cuff_edge), 12.5 / mm_per_px, below_cuff)  # centre 12.5 mm above the edge
# neck top-stitch: measured 20 px (5.3 mm) inside the edge on the x3 crop; visible only on the near half
stitch_src = [p for p in neck_edge if p[0] <= 1600]
neck_stitch = offset(T(stitch_src), 20 * K, opening)

front_left = [S] + seam + body_gap + body_hidden + body_low
sleeve_right = seam + slv_gap
front_top = [S, NECK_L, NECK_R] + far_shoulder[1:]
front_outline = (shoulder_top + neck_edge[1:] + far_shoulder[1:] + arm_right[:1] + arm_right[1:]
                 + cuff_edge[5:][::-1][1:] + arm_left[1:] + [(920, 2048)] + body_low[::-1][1:]
                 + body_hidden[::-1] + body_gap[::-1] + seam[::-1])
sleeve_outline = outer + cuff_edge[1:] + slv_gap[::-1][1:] + seam[::-1] + [S]

def inside(pt, poly):
    c = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > pt[1]) != (y2 > pt[1]) and pt[0] < (x2 - x1) * (pt[1] - y1) / (y2 - y1) + x1:
            c = not c
    return c


def clip_extend(centre, outline, reach=90):
    """Trim centre must stay inside the zone outline. Near corners the offset line leaves it:
    drop the outside end points, then extend each end along its last segment while still inside."""
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


neck_trim = clip_extend(neck_trim, T(front_outline))
cuff_trim = clip_extend(cuff_trim, T(sleeve_outline))

def poly_area(pts):
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))) / 2


def plen(pts):
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


# The sleeve cap is only ~50 px wide, but the sleeve is ~300 px wide below it. make_plate.py would take the mean
# of top and bottom (too small) and stretch the fabric across the sleeve. Use area / mean edge length instead.
sleeve_widthpx = round(poly_area(T(sleeve_outline)) / ((plen(T(outer)) + plen(T(sleeve_right))) / 2), 1)

data = {
    "view": "sleeve",
    "variant": "straight-kurta",
    "viewBox": [1200, 1600],
    "base": "base.jpg",
    "mmPerPx": round(mm_per_px, 4),
    "scaleNote": "shoulder -> cuff-out = 470 mm (agreed value, sleeve view)",
    "source": "source.png crop x 512..2048, resized x0.78125. Points measured on source.png by Claude. "
              "Sparkle mark on the garment (1888-1985, 1888-1985) covered with a patch of garment from 190 px to the left.",
    "thetaDeg": {"front": 40, "sleeve-l": 70},
    "landmarks": L,
    "zones": {
        "front": {
            "order": 1,
            "grid": {"top": T(front_top), "left": T(front_left), "right": T([(2048, 335), (2048, 2048)]),
                     "bottom": T([(920, 2048), (2048, 2048)])},
            "outline": T(front_outline),
        },
        "sleeve-l": {
            "order": 2,
            "widthPx": sleeve_widthpx,
            "grid": {"top": T([A, S, seam[0]]), "left": T(outer), "right": T(sleeve_right),
                     "bottom": T(cuff_edge)},
            "outline": T(sleeve_outline),
        },
    },
    "trims": {"neck": {"order": 3, "widthMm": 12, "centre": neck_trim},
              "cuff-l": {"order": 3, "widthMm": 25, "centre": cuff_trim}},
    "stitches": {"neck-topstitch": neck_stitch, "cuff-topstitch": T(cuff_stitch)},
    # objects in front of the garment (polish.md step 5): an edging lace hanging past the cuff must not cover the arm
    "occluders": [T(arm_left + arm_right[1:] + cuff_edge[cuff_edge.index((1040, 1801)) + 1:-1][::-1])],
}
json.dump(data, open(f"{D}/zones.json", "w"), indent=1)

# ---- annotate.png: colour code on the exact base
RED, BLUE, PURPLE, ORANGE, GREY, GREEN = (229, 57, 53), (30, 99, 233), (142, 36, 170), (251, 140, 0), (97, 97, 97), (46, 125, 50)
img = base.copy()
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
                p0 = (a[0] + (b[0] - a[0]) * t / seg, a[1] + (b[1] - a[1]) * t / seg)
                p1 = (a[0] + (b[0] - a[0]) * (t + step) / seg, a[1] + (b[1] - a[1]) * (t + step) / seg)
                d.line([p0, p1], fill=col, width=w)
            t += step
            acc += step
            if acc >= (on if draw else off):
                acc, draw = 0.0, not draw


front_ref = T([(1500, 700)])[0]      # a point deep in the front: red goes towards it, blue away from it
seam_p = T([S] + seam)
line(offset(seam_p, -2.5, front_ref), RED)
line(offset(seam_p, 2.5, front_ref), BLUE)
z = data["zones"]
line(T(body_gap[::-1][::-1]) if False else T([UNDERARM] + body_gap + body_hidden + body_low), RED)   # front body edge
line(z["front"]["grid"]["top"], RED)
line(z["front"]["grid"]["right"], RED)
line(z["front"]["grid"]["bottom"], RED)
line(z["sleeve-l"]["grid"]["top"], BLUE)
line(z["sleeve-l"]["grid"]["left"], BLUE)
line(T([UNDERARM] + slv_gap), BLUE)                                                      # sleeve inner edge below the underarm
line(z["sleeve-l"]["grid"]["bottom"], BLUE)
dashed(neck, RED, 3)                                                                     # real outline: neck dip
dashed(T(arm_right[1:] + arm_left[::-1][:0]), RED, 3)                                    # real outline: the arm notch
dashed(T(arm_left), RED, 3)
line(neck_trim, PURPLE)
line(cuff_trim, ORANGE)
dashed(neck_stitch, GREY)
dashed(T(cuff_stitch), GREY)
line([L["shoulder"], L["cuff-out"]], GREEN, 2)
for x, y in L.values():
    d.ellipse((x - 6, y - 6, x + 6, y + 6), fill="black", outline="white", width=2)
img.save(f"{D}/annotate.png", optimize=True)

# ---- checks (annotate.md 7.1)
def xat(pts, y):
    for a, b in zip(pts, pts[1:]):
        if a[1] <= y <= b[1] and b[1] != a[1]:
            return a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1])


def mono(pts):
    return all(b[1] >= a[1] for a, b in zip(pts, pts[1:]))


assert mono(front_left) and mono(sleeve_right), "left/right edges must go top -> bottom"
worst = -1e9
for y in range(S[1] + 20, 1399, 10):     # above the junction: sleeve stays on its side of the front
    worst = max(worst, xat(sleeve_right, y) - xat(front_left, y))
print("crossings (sleeve right edge minus front left edge, must be <= 1.6):", round(worst, 2))
assert worst <= 1.6
for zn, zv in z.items():                  # corners meet exactly
    g = zv["grid"]
    for a, b in ((g["top"][0], g["left"][0]), (g["top"][-1], g["right"][0]),
                 (g["bottom"][0], g["left"][-1]), (g["bottom"][-1], g["right"][-1])):
        assert math.dist(a, b) < 0.05, (zn, a, b)
print("corners meet: yes")


for tn, tv in data["trims"].items():
    zone = "front" if tn == "neck" else "sleeve-l"
    bad = [p for p in tv["centre"] if not inside(p, z[zone]["outline"])]
    print("   outside:", bad, "of", tv["centre"][0], "...", tv["centre"][-1])
    print(f"trim {tn}: {len(bad)} of {len(tv['centre'])} centre points outside the {zone} outline")


def segs_cross(p1, p2, p3, p4):
    def o(a, b, c): return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return o(p1, p2, p3) * o(p1, p2, p4) < 0 and o(p3, p4, p1) * o(p3, p4, p2) < 0


for zn, zv in z.items():                  # outline closed (first != last is fine, it is closed by the fill) and simple
    o = zv["outline"]
    n = len(o)
    X = sum(1 for i in range(n) for j in range(i + 2, n) if not (i == 0 and j == n - 1)
            and segs_cross(o[i], o[(i + 1) % n], o[j], o[(j + 1) % n]))
    print(f"outline {zn}: {n} points, {X} self-crossings")
    assert X == 0
print("sleeve widthPx (area / mean edge length):", sleeve_widthpx)
print("mm/px", round(mm_per_px, 4), "| shoulder->cuff-out px", round(math.dist(L['shoulder'], L['cuff-out']), 1),
      "| neck-l->neck-r mm", round(math.dist(L['neck-l'], L['neck-r']) * mm_per_px, 1),
      "| shoulder->neck-l mm", round(math.dist(L['shoulder'], L['neck-l']) * mm_per_px, 1))
