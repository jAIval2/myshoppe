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
    uv_img.paste(layer_uv, (0, 0), mask)
    id_img.paste((ZONE_ID[name], 0, 0), (0, 0), mask)
    plate["zones"][name] = {"id": ZONE_ID[name], "widthCm": round(width_cm, 1),
                            "heightCm": round(height_cm, 1)}
    print(f"{name:9} grid {ns}x{nt}  {width_cm:.1f} x {height_cm:.1f} cm")

garment = id_img.split()[0].point(lambda p: 255 if p else 0)

# ---- trims (on top of everything, but only on the garment)
for name, trim in Z["trims"].items():
    c = trim["centre"]
    half = trim["widthMm"] / 2 / MMPX
    n = max(4, round(length(c) / STEP))
    C = resample(c, n)
    len_cm = length(c) * MMPX / 10
    across = max(8, math.ceil(2 * half))  # one step per px across the trim
    layer = Image.new("RGB", (W, H), (0, 0, 0))
    m = Image.new("L", (W, H), 0)
    dl, dm = ImageDraw.Draw(layer), ImageDraw.Draw(m)
    for i in range(n):
        a, b = C[i], C[i + 1]
        tx, ty = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(tx, ty) or 1
        nx, ny = -ty / ln, tx / ln
        for k in range(across):
            v0, v1 = -half + 2 * half * k / across, -half + 2 * half * (k + 1) / across
            quad = [(a[0] + nx * v0, a[1] + ny * v0), (b[0] + nx * v0, b[1] + ny * v0),
                    (b[0] + nx * v1, b[1] + ny * v1), (a[0] + nx * v1, a[1] + ny * v1)]
            col = pack((i + 0.5) / n * len_cm / CM_RANGE, (k + 0.5) / across)
            dl.polygon(quad, fill=col, outline=col)
            dm.polygon(quad, fill=255, outline=255)
    m = ImageChops.multiply(m, garment)
    uvt_img.paste(layer, (0, 0), m)
    r, g_, b_ = id_img.split()
    g_.paste(TRIM_ID[name], (0, 0), m)
    id_img = Image.merge("RGB", (r, g_, b_))
    plate["trims"][name] = {"id": TRIM_ID[name], "lengthCm": round(len_cm, 1),
                            "widthMm": trim["widthMm"]}

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
