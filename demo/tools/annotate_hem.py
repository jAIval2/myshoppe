"""Annotate the hemline-and-slit view (hem-straight) from points measured on source.png.

Source points are in source.png pixels (2048 x 2048). The plate is the 3:4 crop x 214..1750,
resized to 1200 x 1600 (factor 0.78125). The garment is 1583 px wide, the crop 1536: the crop keeps the whole
back panel and its hem tip on the right, and cuts at most 47 px of the shaded left panel (at the border).
The sparkle mark (x 1920-2010) is outside the crop: no patch needed.

Every list below was read on gridded crops of source.png (tools/gridcrop.py), or scanned and then confirmed on a crop:
  silhouettes: colour distance to the wall on the same row (blur 1.5)
  slit edges, form, hem edges, bar tack, stitches: gridded true-colour and high-contrast crops, x1.2 .. x3
Zones (back to front): back-l (shaded left panel, order 1), back (panel right of the slit, order 1), front (order 2).
Left outside every zone: the dress form in the slit, the pale inside of the far wall below the form, the stand.
usage: python3 tools/annotate_hem.py assets/plates/hem-straight
"""
import json, math, sys
from PIL import Image, ImageDraw

D = sys.argv[1]
X0, K = 214, 1200 / 1536
XMAX = X0 + 1536
src = Image.open(f"{D}/source.png").convert("RGB")
base = src.crop((X0, 0, XMAX, 2048)).resize((1200, 1600), Image.LANCZOS)
base.save(f"{D}/base.jpg", quality=94, subsampling=0)


def C(pts):
    """clamp source points to the crop (grid edges on the border use the border coordinate exactly)"""
    return [(min(max(x, X0), XMAX), y) for x, y in pts]


def T(pts):
    return [[round((x - X0) * K, 1), round(y * K, 1)] for x, y in C(pts)]


# ---- shared lists
SLIT_TOP = (1480, 372)                                   # apex of the slit, just under the bar tack
seam_top = [(1479, 0), (1479, 200), SLIT_TOP]            # side seam above the slit (vertical, dark seam line)
# front panel's right edge below the slit top (the slit front edge)
slit_front = [SLIT_TOP, (1475, 405), (1471, 447), (1465, 497), (1462, 524), (1453, 559), (1447, 618), (1441, 694),
              (1432, 765), (1424, 847), (1412, 935), (1405, 1000), (1391, 1075), (1381, 1137), (1378, 1200),
              (1374, 1250), (1371, 1300), (1369, 1325), (1356, 1375), (1349, 1456), (1344, 1506), (1337, 1550),
              (1328, 1650), (1322, 1700), (1320, 1746)]
HEM_SLIT = (1320, 1746)                                  # front hem corner at the slit
# back panel's left edge (the slit back edge): beside the form, then beside the pale inside of the far wall
slit_back = [SLIT_TOP, (1487, 405), (1498, 442), (1508, 476), (1517, 520), (1521, 559), (1524, 618), (1523, 676),
             (1521, 720), (1522, 760), (1527, 780), (1533, 803), (1540, 833), (1545, 860), (1550, 887), (1553, 920),
             (1557, 961), (1560, 1000), (1561, 1021), (1568, 1057), (1579, 1086), (1587, 1121), (1594, 1157),
             (1596, 1200), (1597, 1236), (1598, 1271), (1598, 1350), (1609, 1425), (1625, 1487), (1634, 1550),
             (1637, 1612), (1644, 1675), (1646, 1731)]
HEM_SLIT_BACK = (1646, 1731)                             # hem tip of the back panel
# front panel's left edge = right edge of the shaded left panel (ONE list). (488, 1612) is where the left panel's hem meets it.
e_fl = [(566, 0), (561, 100), (553, 300), (544, 500), (536, 700), (528, 889), (522, 1011), (514, 1122), (505, 1233),
        (502, 1345), (500, 1456), (494, 1530), (489, 1603), (488, 1612), (485, 1639), (482, 1680), (483, 1703)]
i_join = e_fl.index((488, 1612))
HEM_L = (483, 1703)                                      # front hem, left corner
# front hem (bottom edge), left -> right; between x 873 and 1115 it lies on the top of the stand
front_hem = [HEM_L, (500, 1706), (560, 1716), (607, 1727), (690, 1731), (773, 1733), (873, 1741), (940, 1745),
             (1115, 1748), (1190, 1750), (1273, 1750), HEM_SLIT]
# shaded left panel: silhouette (cut by the crop border below y 715), hem
left_edge = [(264, 0), (260, 50), (257, 100), (253, 150), (249, 200), (246, 250), (241, 300), (239, 350), (235, 400),
             (231, 450), (227, 500), (223, 550), (219, 600), (217, 650), (216, 700), (214, 715), (214, 1613)]
left_hem = [(214, 1613), (266, 1616), (357, 1616), (448, 1612), (488, 1612)]
# back panel's right edge: silhouette against the wall; (1750, ...) is the crop border
back_right = [(1637, 0), (1641, 50), (1645, 100), (1649, 150), (1651, 200), (1653, 250), (1656, 300), (1661, 350),
              (1665, 400), (1668, 450), (1671, 500), (1674, 550), (1674, 600), (1674, 650), (1677, 700), (1682, 750),
              (1687, 800), (1693, 850), (1696, 900), (1700, 950), (1703, 1000), (1708, 1050), (1714, 1100),
              (1718, 1150), (1722, 1200), (1726, 1250), (1729, 1300), (1734, 1350), (1737, 1400), (1741, 1450),
              (1744, 1500), (1746, 1550), (1747, 1600), (1750, 1650), (1750, 1653)]
back_hem = [HEM_SLIT_BACK, (1672, 1709), (1697, 1694), (1725, 1675), (1750, 1653)]

# stitches visible in the photo (measured on zoom crops)
facing_stitch = [(1416, 372), (1413, 399), (1409, 438), (1405, 476), (1401, 515), (1397, 553), (1393, 592), (1390, 626),
                 (1388, 649), (1379, 685), (1374, 731), (1367, 776), (1363, 822), (1358, 867), (1351, 913), (1345, 958),
                 (1340, 995), (1328, 1087), (1320, 1174), (1311, 1261), (1298, 1348), (1285, 1452), (1276, 1522),
                 (1267, 1609)]
bar_tack = [(1423, 359), (1497, 359)]
bar_tack_box = [(1425, 367), (1479, 367)]
hem_stitch = [(520, 1651), (548, 1653), (607, 1660), (690, 1668), (800, 1676), (900, 1680), (1000, 1682),
              (1090, 1683), (1180, 1682), (1273, 1681)]
left_hem_stitch = [(214, 1560), (300, 1560), (400, 1556), (485, 1553)]

# ---- zones (source px)
front_top = [(566, 0), (1479, 0)]
front_left = e_fl
front_right = seam_top + slit_front[1:]
front_bottom = front_hem
front_outline = front_top + front_right[1:] + front_bottom[::-1][1:] + front_left[::-1][1:-1]

back_top = [(1479, 0), (1637, 0)]
back_left = seam_top + slit_back[1:]
back_right_e = back_right
back_bottom = back_hem
back_outline = back_top + back_right_e[1:] + back_bottom[::-1][1:] + back_left[::-1][1:-1]

bl_top = [(264, 0), (566, 0)]
bl_left = left_edge
bl_right = e_fl[:i_join + 1]
bl_bottom = left_hem
bl_outline = bl_top + bl_right[1:] + bl_bottom[::-1][1:] + bl_left[::-1][1:-1]

# ---- landmarks and scale
P = {"slit-top": SLIT_TOP, "hem-slit": HEM_SLIT, "hem-slit-back": HEM_SLIT_BACK, "hem-l": HEM_L,
     "hem-l-back": (214, 1613), "hem-back-r": (1750, 1653)}
L = {k: T([v])[0] for k, v in P.items()}
mm_per_px = 240 / math.dist(L["slit-top"], L["hem-slit"])      # scale: slit-top -> hem-slit = 240 mm


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


def poly_area(pts):
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))) / 2


def plen(pts):
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


O = {"front": T(front_outline), "back": T(back_outline), "back-l": T(bl_outline)}
below_hem = T([(900, 2000)])[0]                    # outside the garment, below the hem (on the stand)
in_slit_f = T([(1500, 900)])[0]                    # inside the slit, right of the front edge (on the form)
in_slit_b = T([(1450, 900)])[0]                    # inside the slit, left of the back edge
# clip_extend reach = half the trim width: a slit trim must not run past the slit top, a hem trim stops at the corners
hem_trim = clip_extend(offset(T(front_hem), 15 / mm_per_px, below_hem), O["front"], 15 / mm_per_px)      # centre 15 mm above the edge
slit_l_trim = clip_extend(offset(T(slit_front), 4 / mm_per_px, in_slit_f), O["front"], 4 / mm_per_px)   # centre 4 mm inside the front edge
slit_r_trim = clip_extend(offset(T(slit_back), 4 / mm_per_px, in_slit_b), O["back"], 4 / mm_per_px)     # centre 4 mm inside the back edge

# a slit trim starts at the slit top: cut it at the apex row (clip_extend reached up along the shared seam)
apex_y = L["slit-top"][1]
slit_l_trim = [p for p in slit_l_trim if p[1] >= apex_y]
slit_r_trim = [p for p in slit_r_trim if p[1] >= apex_y]

data = {
    "view": "hem",
    "variant": "straight-kurta",
    "viewBox": [1200, 1600],
    "base": "base.jpg",
    "mmPerPx": round(mm_per_px, 4),
    "scaleNote": "slit-top -> hem-slit = 240 mm (agreed value, hem view)",
    "source": "source.png crop x 214..1750, resized x0.78125. Points measured on source.png by Claude. "
              "Sparkle mark (x 1920-2010, y 1850-1950) is outside the crop.",
    "thetaDeg": {"front": 45, "back": 60, "back-l": 65},
    "uvRangeCm": 32,   # close view: 0.22 mm/px needs a finer UV step than the default 128 cm range gives
    "landmarks": L,
    "zones": {
        "back-l": {"order": 1, "grid": {"top": T(bl_top), "left": T(bl_left), "right": T(bl_right), "bottom": T(bl_bottom)},
                   "outline": O["back-l"]},
        "back": {"order": 1, "grid": {"top": T(back_top), "left": T(back_left), "right": T(back_right_e), "bottom": T(back_bottom)},
                 "outline": O["back"]},
        "front": {"order": 2, "grid": {"top": T(front_top), "left": T(front_left), "right": T(front_right), "bottom": T(front_bottom)},
                  "outline": O["front"]},
    },
    "trims": {"hem": {"order": 3, "widthMm": 30, "centre": hem_trim},
              "slit-l": {"order": 3, "widthMm": 8, "centre": slit_l_trim},
              "slit-r": {"order": 3, "widthMm": 8, "centre": slit_r_trim}},
    "stitches": {"slit-facing": T(facing_stitch), "bar-tack": T(bar_tack), "bar-tack-box": T(bar_tack_box),
                 "hem-topstitch": T(hem_stitch), "hem-topstitch-left-panel": T(left_hem_stitch)},
}
json.dump(data, open(f"{D}/zones.json", "w"), indent=1)

# ---- annotate.png: colour code on the exact base
RED, BLUE, GOLD, TEAL, GREY, GREEN = (229, 57, 53), (30, 99, 233), (199, 145, 0), (0, 137, 123), (97, 97, 97), (46, 125, 50)
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


front_ref = T([(900, 800)])[0]
shared_l = T(e_fl[:i_join + 1])                  # front / left panel
line(offset(shared_l, -2.5, front_ref), RED)
line(offset(shared_l, 2.5, front_ref), BLUE)
line(T(e_fl[i_join:]), RED)                      # front left edge below the left panel's hem
shared_s = T(seam_top)                           # front / back, above the slit
line(offset(shared_s, -2.5, T([(1700, 700)])[0]), RED)
line(offset(shared_s, 2.5, T([(1700, 700)])[0]), BLUE)
z = data["zones"]
for k in ("top",):
    line(z["front"]["grid"][k], RED)
    line(z["back"]["grid"][k], BLUE)
    line(z["back-l"]["grid"][k], BLUE)
line(T(slit_front), RED)                         # front slit edge
line(z["front"]["grid"]["bottom"], RED)
line(T(slit_back), BLUE)                         # back slit edge
line(z["back"]["grid"]["right"], BLUE)
line(z["back"]["grid"]["bottom"], BLUE)
line(z["back-l"]["grid"]["left"], BLUE)
line(z["back-l"]["grid"]["bottom"], BLUE)
line(hem_trim, GOLD)
line(slit_l_trim, TEAL)
line(slit_r_trim, TEAL)
for name, pts in data["stitches"].items():
    dashed(pts, GREY)
line([L["slit-top"], L["hem-slit"]], GREEN, 2)
for x, y in L.values():
    d.ellipse((x - 6, y - 6, x + 6, y + 6), fill="black", outline="white", width=2)
img.save(f"{D}/annotate.png", optimize=True)


# ---- checks (annotate.md 9.1)
def xat(pts, y):
    for a, b in zip(pts, pts[1:]):
        if a[1] <= y <= b[1] and b[1] != a[1]:
            return a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1])


def mono(pts):
    return all(b[1] >= a[1] for a, b in zip(pts, pts[1:]))


for nm, e in (("front.left", front_left), ("front.right", front_right), ("back.left", back_left), ("back.right", back_right_e),
              ("back-l.left", bl_left), ("back-l.right", bl_right)):
    assert mono(e), f"{nm}: left/right edges must go top -> bottom"
worst = max(xat(front_right, y) - xat(back_left, y) for y in range(10, 1740, 10)
            if xat(front_right, y) is not None and xat(back_left, y) is not None)
print("front right edge minus back left edge (must be <= 1.6 where they touch; negative = the slit gap):", round(worst, 1))
assert worst <= 1.6
for y in range(0, 1612, 10):                     # shared edge between front and left panel: the same line
    assert abs(xat(front_left, y) - xat(bl_right, y)) < 1e-6
for zn, zv in z.items():
    g = zv["grid"]
    for a, b in ((g["top"][0], g["left"][0]), (g["top"][-1], g["right"][0]),
                 (g["bottom"][0], g["left"][-1]), (g["bottom"][-1], g["right"][-1])):
        assert math.dist(a, b) < 0.05, (zn, a, b)
print("corners meet: yes")


def segs_cross(p1, p2, p3, p4):
    def o(a, b, c): return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return o(p1, p2, p3) * o(p1, p2, p4) < 0 and o(p3, p4, p1) * o(p3, p4, p2) < 0


for zn, zv in z.items():
    o = zv["outline"]
    n = len(o)
    X = sum(1 for i in range(n) for j in range(i + 2, n) if not (i == 0 and j == n - 1)
            and segs_cross(o[i], o[(i + 1) % n], o[j], o[(j + 1) % n]))
    print(f"outline {zn}: {n} points, {X} self-crossings")
    assert X == 0
for tn, tv in data["trims"].items():
    zone = "back" if tn == "slit-r" else "front"
    bad = [p for p in tv["centre"] if not inside(p, z[zone]["outline"])]
    print(f"trim {tn}: {len(bad)} of {len(tv['centre'])} centre points outside the {zone} outline")
    assert not bad
for side in ("left", "right"):                    # front side edges smooth: bulge from the chord <= 5 %
    e = z["front"]["grid"][side]
    a, b = e[0], e[-1]
    Ln = math.dist(a, b)
    dev = max(abs((b[0] - a[0]) * (a[1] - p[1]) - (a[0] - p[0]) * (b[1] - a[1])) / Ln for p in e)
    print(f"front.{side} bulge {dev:.0f} px = {100 * dev / Ln:.1f} % (must be <= 5 %)")
    assert dev / Ln <= 0.05
width_cm = (T([(566, 0)])[0][0], T([(1479, 0)])[0][0])
print("scale mm/px", round(mm_per_px, 4), "| slit-top->hem-slit px", round(math.dist(L["slit-top"], L["hem-slit"]), 1),
      "| slit length mm", round(math.dist(L["slit-top"], L["hem-slit"]) * mm_per_px, 1),
      "| front panel width at the top (cm)", round((width_cm[1] - width_cm[0]) * mm_per_px / 10, 1),
      "| all visible garment (cm)", round((1750 - 214) * K * mm_per_px / 10, 1))
