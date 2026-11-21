"""The shoulder-and-sleeve view (sleeve-straight): points measured on source.png, as typed edges (StepA step 1).

Source points are in source.png pixels (2048 x 2048). The plate is the 3:4 crop x 512..2048 (the garment runs off the right border),
resized to 1200 x 1600 (factor 0.78125).
As a module (tools/make_plate.py): base(plate_dir), measure(), review(P, base). Run alone: python3 tools/annotate_sleeve.py
(the automatic checks of annotate.md 9.1; writes nothing).

Every list below was read on gridded crops of source.png (tools/gridcrop.py), not guessed:
  silhouette (outer sleeve, far shoulder): colour distance to the wall, checked on crops
  armhole seam, wall gap under the arm, cuff edge, mannequin arm: gridded true-colour and x2.4 crops
  neckline and its top-stitch: x3 crops
"""
import math
from PIL import Image, ImageDraw, ImageFilter

X0, K = 512, 1200 / 1536


def base(D):
    src = Image.open(f"{D}/source.png").convert("RGB")
    # patch the sparkle mark (it sits on the white garment, bottom right), crop, resize
    patched = src.copy()
    box = (1868, 1868, 2010, 2010)
    feather = Image.new("L", (box[2] - box[0], box[3] - box[1]), 0)
    ImageDraw.Draw(feather).rectangle((12, 12, feather.width - 12, feather.height - 12), fill=255)
    patched.paste(src.crop((box[0] - 190, box[1], box[2] - 190, box[3])), box[:2], feather.filter(ImageFilter.GaussianBlur(8)))
    return patched.crop((X0, 0, X0 + 1536, 2048)).resize((1200, 1600), Image.LANCZOS)


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
P_ = {"neck-l": NECK_L, "neck-r": NECK_R, "shoulder": S, "underarm": UNDERARM,
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
I_ARM = cuff_edge.index((1040, 1801))    # from here to CUFF_IN the mannequin arm is below the cuff

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


def smooth_under(pts, k=0.0):
    """The grid edge of a seam that bulges (the armhole of a turned view: 161 px = 10.7 % from its chord, limit 5 %): every point
    is pulled toward the chord, at the same arc-length fraction, to k of its distance, so the edge runs smoothly UNDER the sleeve
    and the outline (which keeps the seam) cuts it (docs/annotate.md rule 9). k = 0: a straight edge. (Removed with the grid, StepA step 7.)"""
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    tot, acc, out = sum(seg), 0.0, []
    for i, p in enumerate(pts):
        t = acc / tot
        c = (pts[0][0] + (pts[-1][0] - pts[0][0]) * t, pts[0][1] + (pts[-1][1] - pts[0][1]) * t)
        out.append((c[0] + k * (p[0] - c[0]), c[1] + k * (p[1] - c[1])))
        acc += seg[i] if i < len(seg) else 0
    return out


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


def poly_area(pts):
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))) / 2


def plen(pts):
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


def measure():
    L = {k: T([v])[0] for k, v in P_.items()}
    mm_per_px = 470 / math.dist(L["shoulder"], L["cuff-out"])     # scale: shoulder -> cuff-out = 470 mm
    neck = T(neck_edge)
    edges = {
        "shoulder-top": {"type": "free", "points": T(shoulder_top)},
        "neck": {"type": "free", "points": neck},                                  # not live in this view: a free edge (the form inside)
        "far-shoulder": {"type": "free", "points": T(far_shoulder)},
        "front-side": {"type": "frame", "points": T([(2048, 335), (2048, 2048)])},
        "front-bottom-r": {"type": "frame", "points": T([(1450, 2048), (2048, 2048)])},
        "arm-r": {"type": "free", "points": T(arm_right[1:])},                     # the front against the mannequin arm
        "front-under-cuff": {"type": "seam", "under": "sleeve-l", "points": T(cuff_edge[I_ARM:])},   # hidden under the cuff, above the arm
        "arm-l": {"type": "free", "points": T(arm_left)},
        "front-bottom-l": {"type": "frame", "points": T([(920, 2048), (1201, 2048)])},
        "body-low": {"type": "free", "points": T(body_hidden + body_low)},        # the body where it comes out below the cuff
        "front-under-sleeve": {"type": "seam", "under": "sleeve-l", "points": T([body_gap[-1]] + body_hidden)},
        "body-gap": {"type": "free", "points": T([UNDERARM] + body_gap)},          # the body side of the wall gap
        "armhole": {"type": "seam", "zones": ["front", "sleeve-l"], "points": T([S] + seam)},
        "cap": {"type": "free", "points": T([A, S])},
        "outer": {"type": "free", "points": T(outer)},
        "cuff": {"type": "free", "points": T(cuff_edge)},
        "sleeve-in": {"type": "free", "points": T([UNDERARM] + slv_gap)},          # the arm side of the gap, then over the body
    }
    front_outline_src = (shoulder_top + neck_edge[1:] + far_shoulder[1:] + arm_right[:1] + arm_right[1:]
                         + cuff_edge[5:][::-1][1:] + arm_left[1:] + [(920, 2048)] + body_low[::-1][1:]
                         + body_hidden[::-1] + body_gap[::-1] + seam[::-1])
    sleeve_outline_src = outer + cuff_edge[1:] + slv_gap[::-1][1:] + seam[::-1] + [S]
    neck_trim = clip_extend(offset(neck, 6 / mm_per_px, T([(1550, 60)])[0]), T(front_outline_src))              # centre 6 mm inside the edge
    cuff_trim = clip_extend(offset(T(cuff_edge), 12.5 / mm_per_px, T([(1000, 2000)])[0]), T(sleeve_outline_src))   # 12.5 mm above the edge
    # neck top-stitch: measured 20 px (5.3 mm) inside the edge on the x3 crop; visible only on the near half
    neck_stitch = offset(T([p for p in neck_edge if p[0] <= 1600]), 20 * K, T([(1550, 60)])[0])
    # The sleeve cap is only ~50 px wide, but the sleeve is ~300 px wide below it: width = area / mean edge length (until step 4)
    sleeve_widthpx = round(poly_area(T(sleeve_outline_src)) / ((plen(T(outer)) + plen(T(seam + slv_gap))) / 2), 1)
    zones = {
        "front": {"order": 1,
                  "outline": [["shoulder-top", 1], ["neck", 1], ["far-shoulder", 1], ["front-side", 1], ["front-bottom-r", -1],
                              ["arm-r", 1], ["front-under-cuff", -1], ["arm-l", 1], ["front-bottom-l", -1], ["body-low", -1],
                              ["front-under-sleeve", -1], ["body-gap", -1], ["armhole", -1]],
                  "grid": {"top": T([S, NECK_L, NECK_R] + far_shoulder[1:]), "left": T(smooth_under([S] + seam + body_gap + body_hidden + body_low)),
                           "right": T([(2048, 335), (2048, 2048)]), "bottom": T([(920, 2048), (2048, 2048)])}},
        "sleeve-l": {"order": 2, "widthPx": sleeve_widthpx,
                     "outline": [["outer", 1], ["cuff", 1], ["sleeve-in", -1], ["armhole", -1], ["cap", -1]],
                     "grid": {"top": T([A, S, seam[0]]), "left": T(outer), "right": T(seam + slv_gap), "bottom": T(cuff_edge)}},
    }
    return {
        "view": "sleeve", "variant": "straight-kurta", "viewBox": [1200, 1600], "mmPerPx": round(mm_per_px, 4),
        "scaleNote": "shoulder -> cuff-out = 470 mm (agreed value, sleeve view)",
        "source": "source.png crop x 512..2048, resized x0.78125. Points measured on source.png by Claude. "
                  "Sparkle mark on the garment (1888-1985, 1888-1985) covered with a patch of garment from 190 px to the left.",
        "landmarks": L, "edges": edges, "zones": zones,
        "trims": {"neck": {"order": 3, "widthMm": 12, "type": "insertion", "edge": "neck", "offsetMm": 6, "centre": neck_trim},
                  "cuff-l": {"order": 3, "widthMm": 25, "type": "edging", "edge": "cuff", "offsetMm": 12.5, "centre": cuff_trim}},
        "stitches": {"neck-topstitch": neck_stitch, "cuff-topstitch": T(cuff_stitch)},
        # objects in front of the garment (polish.md step 5): an edging lace hanging past the cuff must not cover the arm
        "occluders": [T(arm_left + arm_right[1:] + cuff_edge[I_ARM + 1:-1][::-1])],
        "settings": {"thetaDeg": {"front": 40, "sleeve-l": 70}},
    }


# ---- annotate.png: colour code on the exact base
RED, BLUE, PURPLE, ORANGE, GREY, GREEN = (229, 57, 53), (30, 99, 233), (142, 36, 170), (251, 140, 0), (97, 97, 97), (46, 125, 50)


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
    front_ref = T([(1500, 700)])[0]      # a point deep in the front: red goes towards it, blue away from it
    seam_p = T([S] + seam)
    line(offset(seam_p, -2.5, front_ref), RED)
    line(offset(seam_p, 2.5, front_ref), BLUE)
    z = P["zones"]
    line(T([UNDERARM] + body_gap + body_hidden + body_low), RED)                            # front body edge
    for k in ("top", "right", "bottom"): line(z["front"]["grid"][k], RED)
    for k in ("top", "left", "bottom"): line(z["sleeve-l"]["grid"][k], BLUE)
    line(T([UNDERARM] + slv_gap), BLUE)                                                      # sleeve inner edge below the underarm
    dashed(P["edges"]["neck"]["points"], RED, 3)                                             # real outline: neck dip
    dashed(T(arm_right[1:]), RED, 3)                                                         # real outline: the arm notch
    dashed(T(arm_left), RED, 3)
    line(P["trims"]["neck"]["centre"], PURPLE)
    line(P["trims"]["cuff-l"]["centre"], ORANGE)
    for s in P["stitches"].values(): dashed(s, GREY)
    L = P["landmarks"]
    line([L["shoulder"], L["cuff-out"]], GREEN, 2)
    for x, y in L.values():
        d.ellipse((x - 6, y - 6, x + 6, y + 6), fill="black", outline="white", width=2)
    return img


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
    front_left, sleeve_right = [S] + seam + body_gap + body_hidden + body_low, seam + slv_gap
    mono = lambda pts: all(b[1] >= a[1] for a, b in zip(pts, pts[1:]))
    assert mono(front_left) and mono(sleeve_right), "left/right edges must go top -> bottom"
    worst = max(xat(sleeve_right, y) - xat(front_left, y) for y in range(S[1] + 20, 1399, 10))
    print("crossings (sleeve right edge minus front left edge, must be <= 1.6):", round(worst, 2))
    assert worst <= 1.6
    for zn, zv in P["zones"].items():                  # grid corners meet exactly
        g = zv["grid"]
        for a, b in ((g["top"][0], g["left"][0]), (g["top"][-1], g["right"][0]), (g["bottom"][0], g["left"][-1]), (g["bottom"][-1], g["right"][-1])):
            assert math.dist(a, b) < 0.05, (zn, a, b)
    print("corners meet: yes")
    O = {zn: platedat.outline(P, zn) for zn in P["zones"]}
    for tn, tv in P["trims"].items():
        zone = "front" if tn == "neck" else "sleeve-l"
        bad = [p for p in tv["centre"] if not inside(p, O[zone])]
        print(f"trim {tn}: {len(bad)} of {len(tv['centre'])} centre points outside the {zone} outline")
    for zn, o in O.items():
        n = len(o)
        X = sum(1 for i in range(n) for j in range(i + 2, n) if not (i == 0 and j == n - 1) and segs_cross(o[i], o[(i + 1) % n], o[j], o[(j + 1) % n]))
        print(f"outline {zn}: {n} points, {X} self-crossings")
        assert X == 0
    L = P["landmarks"]
    print("sleeve widthPx (area / mean edge length):", P["zones"]["sleeve-l"]["widthPx"])
    print("mm/px", P["mmPerPx"], "| shoulder->cuff-out px", round(math.dist(L['shoulder'], L['cuff-out']), 1),
          "| neck-l->neck-r mm", round(math.dist(L['neck-l'], L['neck-r']) * P["mmPerPx"], 1),
          "| shoulder->neck-l mm", round(math.dist(L['shoulder'], L['neck-l']) * P["mmPerPx"], 1))


if __name__ == "__main__":
    checks(measure())
