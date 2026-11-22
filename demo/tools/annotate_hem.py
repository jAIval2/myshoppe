"""The hemline-and-slit view (hem-straight): points measured on source.png, as typed edges (StepA step 1).

Source points are in source.png pixels (2048 x 2048). The plate is the 3:4 crop x 214..1750, resized to 1200 x 1600 (factor
0.78125). The garment is 1583 px wide, the crop 1536: the crop keeps the whole back panel and its hem tip on the right, and cuts at
most 47 px of the shaded left panel (at the border). The sparkle mark (x 1920-2010) is outside the crop: no patch needed.
As a module (tools/make_plate.py): base(plate_dir), measure(). Run alone: python3 tools/annotate_hem.py
(the automatic checks of annotate.md 9.1; writes nothing).

Every list below was read on gridded crops of source.png (tools/gridcrop.py), or scanned and then confirmed on a crop:
  silhouettes: colour distance to the wall on the same row (blur 1.5)
  slit edges, form, hem edges, bar tack, stitches: gridded true-colour and high-contrast crops, x1.2 .. x3
Zones (back to front): back-l (shaded left panel, order 1), back (panel right of the slit, order 1), front (order 2).
Left outside every zone: the dress form in the slit, the pale inside of the far wall below the form, the stand.
"""
import math
from PIL import Image, ImageDraw

X0, K = 214, 1200 / 1536
XMAX = X0 + 1536


def base(D):
    src = Image.open(f"{D}/source.png").convert("RGB")
    return src.crop((X0, 0, XMAX, 2048)).resize((1200, 1600), Image.LANCZOS)


def C(pts):
    """clamp source points to the crop (edges on the border use the border coordinate exactly)"""
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


def measure():
    P = {"slit-top": SLIT_TOP, "hem-slit": HEM_SLIT, "hem-slit-back": HEM_SLIT_BACK, "hem-l": HEM_L,
         "hem-l-back": (214, 1613), "hem-back-r": (1750, 1653)}
    L = {k: T([v])[0] for k, v in P.items()}
    mm_per_px = 240 / math.dist(L["slit-top"], L["hem-slit"])      # scale: slit-top -> hem-slit = 240 mm
    edges = {
        "front-top": {"type": "frame", "points": T([(566, 0), (1479, 0)])},
        "side-seam": {"type": "seam", "zones": ["front", "back"], "points": T(seam_top)},          # above the slit
        "slit-front": {"type": "free", "points": T(slit_front)},
        "hem-front": {"type": "free", "points": T(front_hem)},
        "front-left-low": {"type": "free", "points": T(e_fl[i_join:])},                            # below the left panel's hem
        "left-seam": {"type": "seam", "zones": ["front", "back-l"], "points": T(e_fl[:i_join + 1])},
        "back-top": {"type": "frame", "points": T([(1479, 0), (1637, 0)])},
        "back-right": {"type": "free", "points": T(back_right)},
        "hem-back": {"type": "free", "points": T(back_hem)},
        "slit-back": {"type": "free", "points": T(slit_back)},
        "left-top": {"type": "frame", "points": T([(264, 0), (566, 0)])},
        "hem-left": {"type": "free", "points": T(left_hem)},
        "left-frame": {"type": "frame", "points": T(left_edge[-2:])},                              # cut by the crop border
        "left-edge": {"type": "free", "points": T(left_edge[:-1])},
    }
    zones = {
        "back-l": {"order": 1, "frame": {"axis": "midline", "anchor": {"point": "slit-top", "vMm": 911}, "sagEdge": "hem-left"}, "outline": [["left-top", 1], ["left-seam", 1], ["hem-left", -1], ["left-frame", -1], ["left-edge", -1]]},
        "back": {"order": 1, "frame": {"axis": "midline", "anchor": {"point": "slit-top", "vMm": 911}, "sagEdge": "hem-back"}, "outline": [["back-top", 1], ["back-right", 1], ["hem-back", -1], ["slit-back", -1], ["side-seam", -1]]},
        "front": {"order": 2, "frame": {"axis": "midline", "anchor": {"point": "slit-top", "vMm": 911}, "sagEdge": "hem-front"}, "outline": [["front-top", 1], ["side-seam", 1], ["slit-front", 1], ["hem-front", -1], ["front-left-low", -1], ["left-seam", -1]]},
    }
    # trims: each lace hangs on its garment edge between its anchors (the build derives the line: StepA extension, step L1). The
    # slits end square at the slit top (cut) and keep whole motifs from the hem corner (anchor "to"); a slit meets its hem in a mitre
    trims = {
        "slit-l": {"order": 3, "type": "insertion", "edge": "slit-front", "from": "slit-top", "to": "hem-slit", "anchor": "to", "cut": ["from"]},
        "slit-r": {"order": 3, "type": "insertion", "edge": "slit-back", "from": "slit-top", "to": "hem-slit-back", "anchor": "to", "cut": ["from"]},
        "hem": {"order": 3, "type": "edging", "edge": "hem-front", "from": "hem-l", "to": "hem-slit", "join": "mitre with slit-l"},
        "hem-bl": {"order": 3, "type": "edging", "edge": "hem-left"},
        "hem-br": {"order": 3, "type": "edging", "edge": "hem-back", "join": "mitre with slit-r"},
    }
    return {
        "view": "hem", "variant": "straight-kurta", "viewBox": [1200, 1600], "mmPerPx": round(mm_per_px, 4), "uvRangeCm": 40,
        "scaleNote": "slit-top -> hem-slit = 240 mm (agreed value, hem view)",
        "source": "source.png crop x 214..1750, resized x0.78125. Points measured on source.png by Claude. "
                  "Sparkle mark (x 1920-2010, y 1850-1950) is outside the crop.",
        "landmarks": L, "edges": edges, "zones": zones, "trims": trims,
        "stitches": {"slit-facing": T(facing_stitch), "bar-tack": T(bar_tack), "bar-tack-box": T(bar_tack_box),
                     "hem-topstitch": T(hem_stitch), "hem-topstitch-left-panel": T(left_hem_stitch)},
        # openings: the slit interior (the underskirt, bare garment on purpose)
        "invariants": {"openings": [[880, 250, 1130, 1330]]},
        "settings": {"thetaDeg": {"front": 45, "back": 60, "back-l": 65}},
    }




# ---- checks (annotate.md 9.1)
def xat(pts, y):
    for a, b in zip(pts, pts[1:]):
        if a[1] <= y <= b[1] and b[1] != a[1]:
            return a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1])


def segs_cross(p1, p2, p3, p4):
    def o(a, b, c): return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return o(p1, p2, p3) * o(p1, p2, p4) < 0 and o(p3, p4, p1) * o(p3, p4, p2) < 0


def checks(P):
    import platedat
    front_left, front_right, back_left = e_fl, seam_top + slit_front[1:], seam_top + slit_back[1:]
    mono = lambda pts: all(b[1] >= a[1] for a, b in zip(pts, pts[1:]))
    for nm, e in (("front.left", front_left), ("front.right", front_right), ("back.left", back_left), ("back.right", back_right),
                  ("back-l.left", left_edge), ("back-l.right", e_fl[:i_join + 1])):
        assert mono(e), f"{nm}: left/right edges must go top -> bottom"
    worst = max(xat(front_right, y) - xat(back_left, y) for y in range(10, 1740, 10)
                if xat(front_right, y) is not None and xat(back_left, y) is not None)
    print("front right edge minus back left edge (must be <= 1.6 where they touch; negative = the slit gap):", round(worst, 1))
    assert worst <= 1.6
    z = P["zones"]
    O = {zn: platedat.outline(P, zn) for zn in z}
    for zn, o in O.items():
        n = len(o)
        X = sum(1 for i in range(n) for j in range(i + 2, n) if not (i == 0 and j == n - 1) and segs_cross(o[i], o[(i + 1) % n], o[j], o[(j + 1) % n]))
        print(f"outline {zn}: {n} points, {X} self-crossings")
        assert X == 0
    L, mm = P["landmarks"], P["mmPerPx"]
    print("scale mm/px", mm, "| slit-top->hem-slit px", round(math.dist(L["slit-top"], L["hem-slit"]), 1),
          "| slit length mm", round(math.dist(L["slit-top"], L["hem-slit"]) * mm, 1))


if __name__ == "__main__":
    checks(measure())
