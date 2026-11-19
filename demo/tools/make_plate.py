"""Plate maker (test version, Pillow only).

Reads base.jpg + zones.json. Writes into the same folder:
  id.png        R = fabric zone id, G = trim id (0 = none)
  uv.png        fabric UV in cm, 12-bit packed: R=U hi8, G=V hi8, B=(U lo4<<4)|V lo4
  uv_trim.png   trim UV: U = cm along the trim, V = 0..1 across (same packing)
  shade.png     garment luminance / median in LINEAR light, stored as sqrt(shade/2)*255 (plate.json "shadeEncoding": "sqrt");
                zones.json "shadeSpace": "srgb" = the old file, L/median stored as L/2*255 (128 = normal light)
  plate.json    ids, ranges, scale
  check.png     checkerboard test (2 cm squares) on the photo
"""
import json, math, os, sys
from PIL import Image, ImageChops, ImageDraw, ImageMath

DIR = sys.argv[1]
Z = json.load(open(os.path.join(DIR, "zones.json")))
base = Image.open(os.path.join(DIR, Z["base"])).convert("RGB")
W, H = base.size
MMPX = Z["mmPerPx"]
# UV range in cm for 12-bit packing. Optional zones.json "uvRangeCm": a close view (0.22 mm/px) needs a finer step than
# 128 cm / 4095 = 0.031 cm, or neighbouring pixels share a UV value (block ratio). It must stay above the largest UV
# value (zone width / height in cm, trim length in cm); pack() raises if it does not.
CM_RANGE = float(Z.get("uvRangeCm", 128.0))
STEP = 1.0  # quad size in px (one UV value per pixel)

ZONE_ID = {"front": 1, "sleeve-l": 2, "sleeve-r": 3, "back": 4, "back-l": 5}   # back: panel beside the slit; back-l: shaded side panel (hem view)
TRIM_ID = {"neck": 1, "cuff-l": 2, "cuff-r": 3, "hem": 4, "slit-l": 5, "slit-r": 6}
# Cylinder angle of each zone (half the visible arc). Per plate in zones.json "thetaDeg"; defaults below.
THETA_DEG = {"front": 60, "sleeve-l": 70, "sleeve-r": 70, **Z.get("thetaDeg", {})}
THETA = {k: math.radians(v) for k, v in THETA_DEG.items()}


def pack(u, v):
    """u, v in 0..1 of the range -> 12-bit each -> RGB."""
    if u > 1.0 or v > 1.0 or u < 0 or v < 0:
        raise ValueError(f"UV outside the range of {CM_RANGE} cm: set a larger uvRangeCm in zones.json ({u:.3f}, {v:.3f})")
    a = max(0, min(4095, round(u * 4095)))
    b = max(0, min(4095, round(v * 4095)))
    return (a >> 4, b >> 4, ((a & 15) << 4) | (b & 15))


def length(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def resample(pts, n):
    """n+1 points, equal arc length along the polyline."""
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total = sum(seg) or 1
    out, i, acc = [], 0, 0.0
    for k in range(n + 1):
        target = total * k / n
        while i < len(seg) - 1 and acc + seg[i] < target:
            acc += seg[i]
            i += 1
        f = (target - acc) / seg[i] if seg[i] else 0
        f = max(0.0, min(1.0, f))
        out.append((pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f,
                    pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f))
    return out


def coons(g, ns, nt):
    T, B = resample(g["top"], ns), resample(g["bottom"], ns)
    Lf, R = resample(g["left"], nt), resample(g["right"], nt)
    c00 = ((T[0][0] + Lf[0][0]) / 2, (T[0][1] + Lf[0][1]) / 2)
    c10 = ((T[-1][0] + R[0][0]) / 2, (T[-1][1] + R[0][1]) / 2)
    c01 = ((B[0][0] + Lf[-1][0]) / 2, (B[0][1] + Lf[-1][1]) / 2)
    c11 = ((B[-1][0] + R[-1][0]) / 2, (B[-1][1] + R[-1][1]) / 2)
    P = []
    for j in range(nt + 1):
        t = j / nt
        row = []
        for i in range(ns + 1):
            s = i / ns
            pt = []
            for k in (0, 1):
                v = ((1 - t) * T[i][k] + t * B[i][k] + (1 - s) * Lf[j][k] + s * R[j][k]
                     - ((1 - s) * (1 - t) * c00[k] + s * (1 - t) * c10[k]
                        + (1 - s) * t * c01[k] + s * t * c11[k]))
                pt.append(v)
            row.append(tuple(pt))
        P.append(row)
    return P


def tuck(p, t):
    """Push a front side point outward so the front goes UNDER the sleeves.
    Settings come from zones.json "tuck" (per plate). No "tuck" key = no push.
    Torso: 10 px at the shoulder tips, 40 px under the sleeves, then taper to 12 px below
    the cuffs (the traced sides sit ~12 px inside the real edge there: fit error)."""
    x, y = p
    if abs(x - t["cx"]) < t["centreBand"]:
        return [x, y]
    if y < t["tipY"]:
        d = t["tip"]
    elif y <= t["yFull"]:
        d = t["reach"]
    elif y <= t["yZero"]:
        d = t["reach"] + (t["below"] - t["reach"]) * (y - t["yFull"]) / (t["yZero"] - t["yFull"])
    else:
        d = t["below"]
    return [x + (d if x > t["cx"] else -d), y]


if "tuck" in Z:
    fz = Z["zones"]["front"]
    for k in ("left", "right"):
        fz["grid"][k] = [tuck(p, Z["tuck"]) for p in fz["grid"][k]]
    fz["outline"] = [tuck(p, Z["tuck"]) for p in fz["outline"]]


# ---- live neckline (halfway.md step 2): the photographed neck edge = the run of front-outline points BELOW the grid top
# (the dip), with the two outline points on the grid top at its ends (the neck corners). The neck AREA (id.png B = 1) is the
# part of the front grid that any setting in reach can turn into fabric, form or lace: from the grid top down to the deepest
# reach plus the trim and the blend band, and sideways to the widest reach. uv.png is written for the whole grid there.
NECK_REACH_DEEP_MM, NECK_REACH_WIDE_MM, NECK_BAND_MM = 70.0, 25.0, 30.0   # deeper than the photo; wider per side; trim + blend


def neck_edge(front):
    top, o = front["grid"]["top"], front["outline"]

    def topy(x):
        for a, b in zip(top, top[1:]):
            if a[0] != b[0] and min(a[0], b[0]) <= x <= max(a[0], b[0]):
                return a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0])
        return None
    below = [topy(p[0]) is not None and p[1] > topy(p[0]) + 0.5 for p in o]
    cfx = Z.get("landmarks", {}).get("cf-neck", [W / 2])[0]
    i = 0
    while i < len(o):
        if below[i]:
            j = i
            while j + 1 < len(o) and below[j + 1]:
                j += 1
            xs = [o[k][0] for k in range(i, j + 1)]
            if min(xs) < cfx < max(xs) and i > 0 and j + 1 < len(o):
                return [list(p) for p in o[i - 1:j + 2]], topy
            i = j + 1
        else:
            i += 1
    return None, topy


NECK = None
if "front" in Z["zones"] and Z.get("view") in ("neck", "torso") and "neck" in Z.get("trims", {}):
    edge, topy = neck_edge(Z["zones"]["front"])
    if edge:
        cfx = Z.get("landmarks", {}).get("cf-neck", [W / 2])[0]
        ylo = max(p[1] for p in edge)
        reach_w = NECK_REACH_WIDE_MM / MMPX + Z["trims"]["neck"]["widthMm"] / MMPX + 8
        rect = (max(0, int(edge[0][0] - reach_w)), int(min(p[1] for p in edge)) - 2,
                min(W, int(edge[-1][0] + reach_w) + 1), min(H, int(ylo + (NECK_REACH_DEEP_MM + NECK_BAND_MM) / MMPX) + 1))
        NECK = {"edge": edge, "rect": rect, "cfx": cfx}

id_img = Image.new("RGB", (W, H), (0, 0, 0))
uv_img = Image.new("RGB", (W, H), (0, 0, 0))
uvt_img = Image.new("RGB", (W, H), (0, 0, 0))
plate = {"viewBox": [W, H], "mmPerPx": MMPX, "uvRangeCm": CM_RANGE, "zones": {}, "trims": {}}

# ---- fabric zones, back to front
for name, zone in sorted(Z["zones"].items(), key=lambda kv: kv[1]["order"]):
    g = zone["grid"]
    # mean width of the patch. Optional zones.json "widthPx" overrides it for zones whose top edge is
    # much shorter than the body (sleeve cap): mean of top and bottom would under-count the fabric width.
    w_px = zone.get("widthPx") or (length(g["top"]) + length(g["bottom"])) / 2
    h_px = (length(g["left"]) + length(g["right"])) / 2
    ns, nt = max(8, round(w_px / STEP)), max(8, round(h_px / STEP))
    P = coons(g, ns, nt)
    th = THETA[name]
    width_cm = w_px * MMPX / 10 * th / math.sin(th)  # unrolled cylinder
    height_cm = h_px * MMPX / 10

    layer_uv = Image.new("RGB", (W, H), (0, 0, 0))
    layer_m = Image.new("L", (W, H), 0)
    du, dv = ImageDraw.Draw(layer_uv), ImageDraw.Draw(layer_m)
    for j in range(nt):
        tv = (j + 0.5) / nt
        for i in range(ns):
            s = (i + 0.5) / ns
            arc = (math.asin((2 * s - 1) * math.sin(th)) + th) / (2 * th)
            col = pack(arc * width_cm / CM_RANGE, tv * height_cm / CM_RANGE)
            quad = [P[j][i], P[j][i + 1], P[j + 1][i + 1], P[j + 1][i]]
            du.polygon(quad, fill=col, outline=col)
            dv.polygon(quad, fill=255, outline=255)
    # cut to the real outline (neck dip, slits)
    clip = Image.new("L", (W, H), 0)
    ImageDraw.Draw(clip).polygon([tuple(p) for p in zone["outline"]], fill=255)
    mask = ImageChops.multiply(layer_m, clip)
    if NECK and name == "front":                       # the whole grid in the neck area gets UV (the dip too)
        nr = Image.new("L", (W, H), 0)
        ImageDraw.Draw(nr).rectangle([NECK["rect"][0], NECK["rect"][1], NECK["rect"][2] - 1, NECK["rect"][3] - 1], fill=255)
        uv_img.paste(layer_uv, (0, 0), ImageChops.lighter(mask, ImageChops.multiply(layer_m, nr)))
        # neck area = (the cut garment + the dip under the corner line) in the rect: not the 1 px rim that the grid quads'
        # outlines add beyond the outline (it would put a row of fabric on the shoulder line)
        dip = Image.new("L", (W, H), 0)
        ImageDraw.Draw(dip).polygon([tuple(q) for q in NECK["edge"]], fill=255)
        NECK["grid"] = ImageChops.multiply(ImageChops.multiply(layer_m, nr), ImageChops.lighter(mask, dip))
    else:
        uv_img.paste(layer_uv, (0, 0), mask)
    id_img.paste((ZONE_ID[name], 0, 0), (0, 0), mask)
    if NECK and name != "front" and "grid" in NECK:    # a later zone (sleeve) on top: not neck area
        NECK["grid"] = ImageChops.subtract(NECK["grid"], mask)
    plate["zones"][name] = {"id": ZONE_ID[name], "widthCm": round(width_cm, 1),
                            "heightCm": round(height_cm, 1)}
    print(f"{name:9} grid {ns}x{nt}  {width_cm:.1f} x {height_cm:.1f} cm")

garment = id_img.split()[0].point(lambda p: 255 if p else 0)

# ---- trims (on top of everything)
# polish.md step 5. Every strip is written with V = 0 at its inner side and V = 1 at the side of the garment edge that it
# follows (plate.json "outerV": 1), so the decorative edge of a lace points outward with no manual FLIP.
# An EDGING trim ("type": "edging"; default for hem and cuffs) is written wider, to V = vMax (1.5 strip widths): the part past
# V = 1 lies OUTSIDE the garment (zone 0 in id.png R), where the lace hangs over the photo. That part is clipped only by
# objects in front ("occluders" in zones.json, e.g. the mannequin arm). The shader shifts each lace by its own edgeDepth.
EDGING_DEFAULT = {"hem", "cuff-l", "cuff-r"}
V_MAX_EDGING = 1.5
occl = Image.new("L", (W, H), 0)
for poly in Z.get("occluders", []):
    ImageDraw.Draw(occl).polygon([tuple(q) for q in poly], fill=255)
free = occl.point(lambda v: 0 if v else 255)
gpx = garment.load()
for name, trim in Z["trims"].items():
    c = trim["centre"]
    ttype = trim.get("type", "edging" if name in EDGING_DEFAULT else "insertion")
    vmax = V_MAX_EDGING if ttype == "edging" else 1.0
    half = trim["widthMm"] / 2 / MMPX
    n = max(4, round(length(c) / STEP))
    C = resample(c, n)
    len_cm = length(c) * MMPX / 10
    # which side of the centre line is the garment edge: march out along both normals (from the strip edge, up to 60 px)
    # and take the side where the garment ends first, by the median over the trim. A trim far from any edge on both
    # sides (none in the 4 plates) keeps +1.
    dpos, dneg = [], []
    for i in range(0, n, max(1, n // 60)):
        a, b = C[i], C[i + 1]
        tx, ty = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(tx, ty) or 1
        nx, ny = -ty / ln, tx / ln
        for sgn, acc in ((1, dpos), (-1, dneg)):
            d = 999
            for step in range(0, 61):
                x, y = a[0] + nx * sgn * (half + step), a[1] + ny * sgn * (half + step)
                if not (0 <= x < W and 0 <= y < H and gpx[int(x), int(y)]):
                    d = step
                    break
            acc.append(d)
    med = lambda l: sorted(l)[len(l) // 2]
    sg = -1 if med(dneg) < med(dpos) else 1
    steps_in = max(8, math.ceil(2 * half))              # one step per px across the strip
    steps = math.ceil(steps_in * vmax)
    layer = Image.new("RGB", (W, H), (0, 0, 0))
    m_in, m_out = Image.new("L", (W, H), 0), Image.new("L", (W, H), 0)
    dl, di, do = ImageDraw.Draw(layer), ImageDraw.Draw(m_in), ImageDraw.Draw(m_out)
    for i in range(n):
        a, b = C[i], C[i + 1]
        tx, ty = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(tx, ty) or 1
        nx, ny = -ty / ln * sg, tx / ln * sg             # now points to the garment edge
        for k in range(steps):
            f0, f1 = k / steps_in, min(vmax, (k + 1) / steps_in)   # V in strip widths, 0 = inner side
            v0, v1 = -half + 2 * half * f0, -half + 2 * half * f1
            quad = [(a[0] + nx * v0, a[1] + ny * v0), (b[0] + nx * v0, b[1] + ny * v0),
                    (b[0] + nx * v1, b[1] + ny * v1), (a[0] + nx * v1, a[1] + ny * v1)]
            col = pack((i + 0.5) / n * len_cm / CM_RANGE, (f0 + f1) / 2 / vmax)
            dl.polygon(quad, fill=col, outline=col)
            (di if k < steps_in else do).polygon(quad, fill=255, outline=255)
    m_in = ImageChops.multiply(m_in, garment)            # the strip itself: on the garment only (as before)
    m_out = ImageChops.multiply(m_out, free)             # the overhang: anywhere, except objects in front
    m = ImageChops.lighter(m_in, m_out)
    uvt_img.paste(layer, (0, 0), m)
    r, g_, b_ = id_img.split()
    g_.paste(TRIM_ID[name], (0, 0), m)
    id_img = Image.merge("RGB", (r, g_, b_))
    plate["trims"][name] = {"id": TRIM_ID[name], "lengthCm": round(len_cm, 1), "widthMm": trim["widthMm"],
                            "type": ttype, "outerV": 1, "vMax": vmax}

# ---- neck area: id.png B = 1 (halfway.md step 2)
if NECK and "grid" in NECK:
    r, g_, b_ = id_img.split()
    b_.paste(1, (0, 0), NECK["grid"])
    id_img = Image.merge("RGB", (r, g_, b_))

# ---- shade: luminance / median inside the garment
Lum = base.convert("L")
hist = Lum.histogram(garment)
total, acc, med = sum(hist), 0, 128
for v, h in enumerate(hist):
    acc += h
    if acc >= total / 2:
        med = v
        break
shade_f = ImageMath.lambda_eval(lambda a: a["l"] * (1.0 / med), l=Lum.convert("F"))     # shade as a float, 1.0 = normal light

# ---- smooth the shade without losing the folds (polish.md step 3)
# The base photo is a white cotton: its weave (0.3-0.5 mm) is stored in the shade, and a new fabric then shows a second weave on
# top of its own. An edge-preserving guided filter (the shade is its own guide) removes it and keeps the folds, seams and
# stitches. Radius in mm, not px. Masked per zone: nothing is mixed across a zone edge or across the gap to the wall.
# zones.json "shadeSmoothMm": radius in mm (default 1.2, 0 = off); "shadeSmoothEps": regularisation on the 0..2 shade (default 0.006; 0.002 left 33 % of the weave on the sleeve plate).
# The torso plate sets "shadeSmoothMm": 0: at 0.9 mm/px the weave cannot be resolved, and what is left below 1.5 mm is 1-2 px of photo noise.
SMOOTH_MM = float(Z.get("shadeSmoothMm", 1.2))
SMOOTH_EPS = float(Z.get("shadeSmoothEps", 0.006))


def box_rows(rows, r):
    """Sum over [i-r, i+r] in every row (zero outside), with running sums: C-speed list operations only."""
    out = []
    for row in rows:
        n = len(row)
        pre = [0.0]
        pre.extend(accumulate(row))
        pp = [0.0] * r + pre + [pre[-1]] * r
        out.append(list(map(sub, pp[2 * r + 1:2 * r + 1 + n], pp[:n])))
    return out


def box2d(rows, r):
    cols = [list(c) for c in zip(*box_rows(rows, r))]
    return [list(c) for c in zip(*box_rows(cols, r))]


def guided_masked(I, w, r, eps):
    """Guided filter (guide = the image itself) over the pixels where w = 1. I, w: lists of rows."""
    Iw = [[a * b for a, b in zip(ri, rw)] for ri, rw in zip(I, w)]
    I2w = [[a * a * b for a, b in zip(ri, rw)] for ri, rw in zip(I, w)]
    Wn, S1, S2 = box2d(w, r), box2d(Iw, r), box2d(I2w, r)
    Aw, Bw = [], []
    for rn, r1, r2, rw in zip(Wn, S1, S2, w):
        ra, rb = [], []
        for n, s1, s2, m in zip(rn, r1, r2, rw):
            if m and n > 0:
                mean = s1 / n
                var = s2 / n - mean * mean
                a_ = var / (var + eps) if var > 0 else 0.0
                ra.append(a_)
                rb.append(mean - a_ * mean)
            else:
                ra.append(0.0)
                rb.append(0.0)
        Aw.append(ra)
        Bw.append(rb)
    SA, SB = box2d(Aw, r), box2d(Bw, r)
    return [[(sa * i + sb) / n if n > 0 else i for sa, sb, i, n in zip(ra, rb, ri, rn)]
            for ra, rb, ri, rn in zip(SA, SB, I, Wn)]


if SMOOTH_MM > 0:
    from itertools import accumulate
    from operator import sub
    r_px = max(1, round(SMOOTH_MM / MMPX))
    id_r = id_img.split()[0]
    smooth = shade_f.copy()
    for zid in sorted(set(ZONE_ID[n] for n in Z["zones"])):
        zmask = id_r.point(lambda p, z=zid: 255 if p == z else 0)
        bb = zmask.getbbox()
        if not bb:
            continue
        bb = (max(0, bb[0] - r_px), max(0, bb[1] - r_px), min(W, bb[2] + r_px), min(H, bb[3] + r_px))
        zw, zh = bb[2] - bb[0], bb[3] - bb[1]
        vals = list(shade_f.crop(bb).getdata())
        msk = list(zmask.crop(bb).getdata())
        I = [vals[y * zw:(y + 1) * zw] for y in range(zh)]
        w = [[1.0 if m else 0.0 for m in msk[y * zw:(y + 1) * zw]] for y in range(zh)]
        res = guided_masked(I, w, r_px, SMOOTH_EPS)
        piece = Image.new("F", (zw, zh))
        piece.putdata([v for row in res for v in row])
        smooth.paste(piece, bb[:2], zmask.crop(bb))
    shade_f = smooth
    plate["shadeSmoothMm"], plate["shadeSmoothPx"] = SMOOTH_MM, r_px

# ---- store (polish.md step 2)
# Default: the LINEAR luminance ratio, lin(L) / lin(median), stored as sqrt(shade / 2) * 255 ("shadeEncoding": "sqrt";
# decoded shade = 2 * stored^2). The shader multiplies in linear light; the square root keeps precision in the dark folds.
# The smoothing above runs on the sRGB ratio (its tuning stays exact); the result is converted here.
# zones.json "shadeSpace": "srgb" keeps the old file: L / median * 127.5, 128 = normal light, no "shadeEncoding" key.
SHADE_SPACE = Z.get("shadeSpace", "linear")


def srgb_to_lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


if SHADE_SPACE == "linear":
    lin_med = srgb_to_lin(med / 255.0)
    m255 = med / 255.0
    # sRGB ratio -> sRGB value -> linear value -> linear ratio -> sqrt code. (The exact sRGB curve is piecewise; its linear
    # toe below 10/255 is replaced by the power law here: no garment pixel is that dark.)
    shade = ImageMath.lambda_eval(
        lambda a: (((((a["s"] * m255 + 0.055) / 1.055) ** 2.4) / lin_med / 2.0) ** 0.5) * 255.0, s=shade_f).convert("L")
    shade = Image.composite(shade, Image.new("L", (W, H), round(255 * math.sqrt(0.5))), garment)   # outside: shade 1.0
    plate["shadeSpace"], plate["shadeEncoding"] = "linear", "sqrt"

    def lin_to_srgb(c):
        return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    # check.png: stored code -> the sRGB ratio again, so that the checker looks as before
    k_of_stored = [min(2.0, 255 * lin_to_srgb(min(1.0, 2.0 * (v / 255.0) ** 2 * lin_med)) / med) for v in range(256)]
else:
    shade = ImageMath.lambda_eval(lambda a: a["s"] * 127.5, s=shade_f).convert("L")
    shade = Image.composite(shade, Image.new("L", (W, H), 128), garment)
    k_of_stored = [v / 127.5 for v in range(256)]
plate["shadeMedian"] = med


def offset_poly(pts, d, away):
    """The same vertex-normal offset as tools/annotate_neck.py (and the page): d px, away from the point `away`."""
    out = []
    for i, (x, y) in enumerate(pts):
        a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        n = math.hypot(tx, ty) or 1
        nx, ny = -ty / n, tx / n
        if (x - away[0]) * nx + (y - away[1]) * ny < 0:
            nx, ny = -nx, -ny
        out.append([x + nx * d, y + ny * d])
    return out


if NECK and "grid" in NECK:
    # shade in the dip: the garment's shade carried 8 px outward (mean of known neighbours), so that a smooth (LINEAR) read at
    # the photographed edge does not mix in the 1.0 of the background (the page reads the edge band there when it moves)
    x0, y0, x1, y1 = NECK["rect"]
    sp, gp, ngp = shade.load(), garment.load(), NECK["grid"].load()
    known = {(x, y) for y in range(y0, y1) for x in range(x0, x1) if gp[x, y]}
    for _ in range(8):
        new = {}
        for y in range(y0, y1):
            for x in range(x0, x1):
                if (x, y) in known or not ngp[x, y]:
                    continue
                vals = [sp[x + dx, y + dy] for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                        if (x + dx, y + dy) in known and x0 <= x + dx < x1 and y0 <= y + dy < y1]
                if vals:
                    new[(x, y)] = round(sum(vals) / len(vals))
        for (x, y), v in new.items():
            sp[x, y] = v
        known |= set(new)
    # colours for the plain fills (?revealfill=0) and the toile: median of the garment just below the edge band, and of the
    # form just above the edge
    edge = NECK["edge"]
    nk = Z["trims"]["neck"]
    tw = nk["widthMm"] / MMPX
    below_pts = offset_poly(edge, tw + 4 / MMPX, (NECK["cfx"], 0))
    above_pts = offset_poly(edge, -4 / MMPX, (NECK["cfx"], 0))
    bp = base.load()

    def med_rgb(pts):
        cols = [bp[int(x), int(y)] for x, y in pts[1:-1] if 0 <= x < W and 0 <= y < H]
        return [sorted(c[k] for c in cols)[len(cols) // 2] for k in range(3)] if cols else [200, 200, 200]
    st = Z.get("stitches", {}).get("neck-topstitch")
    stitch_mm = None
    if st:
        on = offset_poly(edge, 0, (NECK["cfx"], 0))
        stitch_mm = round(sum(min(math.dist(p, q) for q in on) for p in st[2:-2]) / max(1, len(st) - 4) * MMPX, 1)
    lm = Z.get("landmarks", {})
    # a clean square of the dress form inside the dip, beside the centre-front tape (the side with less detail): the page
    # tiles its fine detail (hex tiling) where a deeper setting shows the form (halfway.md step 3)
    c0, c1 = edge[0], edge[-1]
    cfy = lm.get("cf-neck", [NECK["cfx"], max(p[1] for p in edge)])[1]
    depth_px = cfy - (c0[1] + (c1[1] - c0[1]) * (NECK["cfx"] - c0[0]) / (c1[0] - c0[0]))
    P = min(25 / MMPX, 0.55 * depth_px)

    def edge_y(x):
        for a, b in zip(edge, edge[1:]):
            if a[0] <= x <= b[0]:
                return a[1] + (b[1] - a[1]) * (x - a[0]) / ((b[0] - a[0]) or 1)
        return cfy
    Lb = base.convert("L")
    best = None
    for sgn in (-1, 1):
        cx = NECK["cfx"] + sgn * (P / 2 + 3 / MMPX)
        bot = min(edge_y(cx - P / 2), edge_y(cx + P / 2)) - 3.5 / MMPX
        box = (round(cx - P / 2), round(bot - P), round(cx + P / 2), round(bot))
        crop = Lb.crop(box)
        hp = ImageChops.difference(crop, crop.resize((max(1, crop.width // 6), max(1, crop.height // 6))).resize(crop.size, Image.BILINEAR))
        var = sum(v * v * n for v, n in enumerate(hp.histogram())) / max(1, crop.width * crop.height)
        if best is None or var < best[0]:
            best = (var, box)
    plate["neck"] = {
        "formPatch": list(best[1]),
        "edge": [[round(x, 2), round(y, 2)] for x, y in edge],          # photographed edge, corner to corner, plate px
        "centre": nk["centre"],                                        # the trim centre line of the plate (uv_trim.png)
        "top": Z["zones"]["front"]["grid"]["top"],                     # grid top: the shoulder line and the neck-point line
        "cf": [NECK["cfx"], lm.get("cf-neck", [NECK["cfx"], max(p[1] for p in edge)])[1]],
        "trimWidthMm": nk["widthMm"], "stitchMm": stitch_mm,
        "reachDeepMm": NECK_REACH_DEEP_MM, "reachWideMm": NECK_REACH_WIDE_MM,
        "rect": list(NECK["rect"]),                                    # the neck area (id.png B = 1) lies inside
        "toileRGB": med_rgb(below_pts), "formRGB": med_rgb(above_pts),
    }

for img, fn in ((id_img, "id.png"), (uv_img, "uv.png"), (uvt_img, "uv_trim.png"), (shade, "shade.png")):
    img.save(os.path.join(DIR, fn), optimize=True)
json.dump(plate, open(os.path.join(DIR, "plate.json"), "w"), indent=1)

# ---- check.png: 2 cm checker on fabric, stripes on trims, times the shade
uvp, uvtp, idp, shp, bp = uv_img.load(), uvt_img.load(), id_img.load(), shade.load(), base.load()
out = base.copy()
op = out.load()
COL = {1: ((214, 72, 64), (245, 225, 210)), 2: ((44, 92, 190), (215, 228, 250)),
       3: ((44, 92, 190), (215, 228, 250)), 4: ((38, 150, 96), (215, 240, 222)),
       5: ((140, 80, 170), (232, 222, 244))}


def unpack(p):
    u = ((p[0] << 4) | (p[2] >> 4)) / 4095 * CM_RANGE
    v = ((p[1] << 4) | (p[2] & 15)) / 4095 * CM_RANGE
    return u, v


for y in range(H):
    for x in range(W):
        z, t = idp[x, y][0], idp[x, y][1]
        if not z:
            continue
        k = k_of_stored[shp[x, y]]
        if t:
            u, v = unpack(uvtp[x, y])
            v /= CM_RANGE
            on = int(u / 0.8) % 2 == 0 and 0.15 < v < 0.85
            c = (150, 40, 170) if on else (250, 200, 80)
        else:
            u, v = unpack(uvp[x, y])
            c = COL[z][(int(u / 2) + int(v / 2)) % 2]
        op[x, y] = tuple(min(255, int(ch * k)) for ch in c)
out.save(os.path.join(DIR, "check.png"), optimize=True)
print("done:", sorted(f for f in os.listdir(DIR)))
