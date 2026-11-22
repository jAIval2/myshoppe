"""The plate build (StepA step 1), Pillow only: the source of a plate -> base.jpg + plate.dat. Deterministic.

usage: python3 tools/make_plate.py <plate-dir> [--review] [--no-check]

  source     source.png + tools/annotate_<view>.py (the measured points, typed edges, trims, frame specifications; base(), measure()).
             A plate without an annotate script is rebuilt from the source part of its own plate.dat (the "imported" data) and keeps
             its base.jpg (the torso used this from StepA step 1 to step 2; no plate does now).
  snap       (StepA step 3) the free and cut edges snapped to the photo (tools/snap_edges.py); then each trim's line derived from its
             edge (derive_trims: the edge smoothed over 4 mm, between its anchors; StepA extension, step L1)
  build      the data -> the maps IN MEMORY (rasterise: id, uv, the trim field, shade, as the page builds them) -> the decisions that are
             taken from the image (each trim's side, the shade median, the neck block's colours and form patch, zone sizes) ->
             plate.dat (tools/platedat.py). No map file is written.
  --review   annotate.png, check.png (2 cm checker on the fabric, stripes on the trims, times the shade) and the edge crops (the
             review set of tools/edge_crops.py, cut from check.png) into demo/review/<plate>/ (not committed).
  At the end: tools/plate_invariants.py on the plate (printed, not fatal); --no-check skips it.

As a module: build(plate_dir) -> P (the data with its decisions), maps_of(plate_dir) -> {id, uv, field, shade, plate, zones, k_of_stored}
(the maps of the committed plate.dat, in memory), rasterise(zones, base) -> the same from the zone data.

Maps (in memory; the page builds the same on the GPU):
  id        R = fabric zone id, G = trim id (0 = none), B = 1 in the neck area
  uv        fabric UV in cm, 12-bit packed: R=U hi8, G=V hi8, B=(U lo4<<4)|V lo4
  field     the trim field: s = cloth cm along the trim's edge (0 at its anchor), t = px from the edge (+ on the garment)
  shade     garment luminance / median in LINEAR light, stored as sqrt(shade/2)*255 ("shadeEncoding": "sqrt");
            "shadeSpace": "srgb" = the old encoding, L/median stored as L/2*255 (128 = normal light)
"""
import copy, importlib, json, math, os, sys
from PIL import Image, ImageChops, ImageDraw, ImageMath

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import platedat, plateframe

STEP = 1.0  # quad size in px (one UV value per pixel)
ZONE_ID = {"front": 1, "sleeve-l": 2, "sleeve-r": 3, "back": 4, "back-l": 5}   # back: panel beside the slit; back-l: shaded side panel (hem view)
TRIM_ID = {"neck": 1, "cuff-l": 2, "cuff-r": 3, "hem": 4, "slit-l": 5, "slit-r": 6, "hem-bl": 7, "hem-br": 8}


def pack(u, v):
    """u, v in 0..1 of the range -> 12-bit each -> RGB."""
    if u > 1.0 or v > 1.0 or u < 0 or v < 0:
        raise ValueError(f"UV outside the packing range: set a larger uvRangeCm for this view ({u:.3f}, {v:.3f})")
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


def fill_exact(img, poly, value=255):
    """Fill a polygon into an L image by the rule of the GPU: a pixel is in when its centre (an integer plate coordinate) is inside,
    even-odd, an edge row half-open (y0 <= y < y1), a span [xa, xb) (StepA step 5: Pillow's polygon fill goes up to a pixel wider)."""
    W_, H_ = img.size
    px = img.load()
    n = len(poly)
    ys = [p[1] for p in poly]
    for y in range(max(0, math.ceil(min(ys))), min(H_, math.floor(max(ys)) + 1)):
        xs = []
        for i in range(n):
            (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for a, b in zip(xs[0::2], xs[1::2]):
            for x in range(max(0, math.ceil(a)), min(W_, math.ceil(b))):
                px[x, y] = value


def rasterise(Z, base):
    """The maps of one plate from its zone data Z (the shape tools/platedat.py legacy() gives), in memory.
    Returns {id, uv, field, shade, plate (the decisions, as the plate header), k_of_stored, base, garment}.
    field = {"main": {pixel index: (trim id, s cm, t px)}, "slit": {...}}: the trim field (tools/trimfield.py).
    Every zone has a fabric frame (StepA step 4): its (u, v) at each pixel, its coverage = its outline and its under-strips."""
    Z = copy.deepcopy(Z)
    W, H = base.size
    MMPX = Z["mmPerPx"]
    # UV range in cm for 12-bit packing ("uvRangeCm"): a close view (0.22 mm/px) needs a finer step than 128 cm / 4095 = 0.031 cm,
    # or neighbouring pixels share a UV value (block ratio). It must stay above the largest UV value; pack() raises if it does not.
    CM_RANGE = float(Z.get("uvRangeCm", 128.0))
    # Cylinder angle of each zone (half the visible arc): "thetaDeg" of the view; defaults below.
    THETA_DEG = {"front": 60, "sleeve-l": 70, "sleeve-r": 70, **Z.get("thetaDeg", {})}
    THETA = {k: math.radians(v) for k, v in THETA_DEG.items()}
    # ---- live neckline (halfway.md step 2): the photographed neck edge = the front's cut edge (StepA), corner to corner. The neck
    # AREA (id B = 1) is the part of the front that any setting in reach can turn into fabric, form or lace: from the corners down to
    # the deepest reach plus the trim and the blend band, and sideways to the widest reach. The frame's uv is written for all of it.
    NECK_REACH_DEEP_MM, NECK_REACH_WIDE_MM, NECK_BAND_MM = 70.0, 25.0, 60.0   # deeper than the photo; wider per side; the widest lace + blend


    NECK = None
    if "front" in Z["zones"] and Z.get("view") in ("neck", "torso") and "neck" in Z.get("trims", {}):
        edge = [list(p) for p in Z["neckEdge"]] if Z.get("neckEdge") else None   # the cut edge (StepA step 3)
        if edge:
            cfx = Z.get("landmarks", {}).get("cf-neck", [W / 2])[0]
            ylo = max(p[1] for p in edge)
            reach_w = (NECK_REACH_WIDE_MM + 56.0) / MMPX + 8      # the widest lace (tools/trimfield.py LACE_IN_MM) past the widest reach
            rect = (max(0, int(edge[0][0] - reach_w)), int(min(p[1] for p in edge)) - 2,
                    min(W, int(edge[-1][0] + reach_w) + 1), min(H, int(ylo + (NECK_REACH_DEEP_MM + NECK_BAND_MM) / MMPX) + 1))
            NECK = {"edge": edge, "rect": rect, "cfx": cfx}

    id_img = Image.new("RGB", (W, H), (0, 0, 0))
    uv_img = Image.new("RGB", (W, H), (0, 0, 0))
    plate = {"viewBox": [W, H], "mmPerPx": MMPX, "uvRangeCm": CM_RANGE, "zones": {}, "trims": {}}

    # ---- StepA step 4: the fabric frame. Each zone's (u, v) from its frame (tools/plateframe.py), evaluated over the zone's box
    # + 16 px (and, for the front, the whole neck area): exactly on the even pixels, bilinear between them. Coverage = the outline
    # (and the lower zone's strips under the upper one at its seams). The 12-bit packing needs u, v >= 0: an offset for the whole view
    # (decisions "uvOffsetCm"), the same in the page.
    FRAMES = {n: z for n, z in Z["zones"].items() if z.get("frame")}
    for n in Z["zones"]:
        if n not in FRAMES: raise ValueError(f"zone {n} has no fabric frame")
    FMAP = {}
    for name, zone in FRAMES.items():
        polys = [zone["outline"]] + zone.get("under", [])
        xs = [p[0] for q in polys for p in q]; ys = [p[1] for q in polys for p in q]
        x0, y0 = max(0, int(min(xs)) - 16), max(0, int(min(ys)) - 16)
        x1, y1 = min(W - 1, int(max(xs)) + 17), min(H - 1, int(max(ys)) + 17)
        if NECK and name == "front":
            x0, y0 = min(x0, NECK["rect"][0]), min(y0, NECK["rect"][1])
            x1, y1 = max(x1, NECK["rect"][2] - 1), max(y1, NECK["rect"][3] - 1)
        F = zone["frame"]
        lx = list(range(x0, x1 + 2, 2)); ly = list(range(y0, y1 + 2, 2))
        LU = [[0.0] * len(lx) for _ in ly]; LV = [[0.0] * len(lx) for _ in ly]
        for j, y in enumerate(ly):
            for i, x in enumerate(lx):
                LU[j][i], LV[j][i] = plateframe.uv(F, MMPX, x, y)
        bw, bh = x1 - x0 + 1, y1 - y0 + 1
        U, V = [0.0] * (bw * bh), [0.0] * (bw * bh)
        for yy in range(bh):
            j, fy = divmod(yy, 2)
            ru, rv = LU[j], LV[j]
            if fy:
                ru = [(a + b) / 2 for a, b in zip(LU[j], LU[j + 1])]; rv = [(a + b) / 2 for a, b in zip(LV[j], LV[j + 1])]
            base_i = yy * bw
            for xx in range(bw):
                i, fx = divmod(xx, 2)
                if fx: U[base_i + xx], V[base_i + xx] = (ru[i] + ru[i + 1]) / 2, (rv[i] + rv[i + 1]) / 2
                else: U[base_i + xx], V[base_i + xx] = ru[i], rv[i]
        FMAP[name] = ((x0, y0, x1 + 1, y1 + 1), U, V)
    if FMAP:
        umin = min(min(m[1]) for m in FMAP.values()); vmin = min(min(m[2]) for m in FMAP.values())
        umax = max(max(m[1]) for m in FMAP.values()); vmax_ = max(max(m[2]) for m in FMAP.values())
        U0, V0 = float(math.floor(-umin) + 1), float(math.floor(-vmin) + 1)
        if umax + U0 >= CM_RANGE or vmax_ + V0 >= CM_RANGE:
            raise ValueError(f"the frame's (u, v) span {umin:.1f}..{umax:.1f}, {vmin:.1f}..{vmax_:.1f} cm: more than uvRangeCm {CM_RANGE}")
        UV_OFF = [U0, V0]
    else:
        UV_OFF = [0.0, 0.0]

    # ---- fabric zones, back to front
    for name, zone in sorted(Z["zones"].items(), key=lambda kv: kv[1]["order"]):
        if name in FMAP:
            (bx0, by0, bx1, by1), U, V = FMAP[name]
            layer_uv = Image.new("RGB", (bx1 - bx0, by1 - by0))
            layer_uv.putdata([pack((u + UV_OFF[0]) / CM_RANGE, (v + UV_OFF[1]) / CM_RANGE) for u, v in zip(U, V)])
            full_uv = Image.new("RGB", (W, H), (0, 0, 0)); full_uv.paste(layer_uv, (bx0, by0))
            mask = Image.new("L", (W, H), 0)
            fill_exact(mask, zone["outline"])
            for strip in zone.get("under", []): fill_exact(mask, strip)
            if NECK and name == "front":                   # the frame's uv in the whole neck area (the dip too)
                nr = Image.new("L", (W, H), 0)
                ImageDraw.Draw(nr).rectangle([NECK["rect"][0], NECK["rect"][1], NECK["rect"][2] - 1, NECK["rect"][3] - 1], fill=255)
                uv_img.paste(full_uv, (0, 0), ImageChops.lighter(mask, nr))
                dip = Image.new("L", (W, H), 0)
                fill_exact(dip, NECK["edge"])
                NECK["area"] = ImageChops.multiply(nr, ImageChops.lighter(mask, dip))
            else:
                uv_img.paste(full_uv, (0, 0), mask)
            id_img.paste((ZONE_ID[name], 0, 0), (0, 0), mask)
            if NECK and name != "front" and "area" in NECK:
                NECK["area"] = ImageChops.subtract(NECK["area"], mask)
            F = zone["frame"]
            plate["zones"][name] = {"id": ZONE_ID[name], "heightCm": round(F["L"] * MMPX / 10, 1),
                                    "widthCm": round((plateframe.cubic(F["half"]["left"], 0.5) + plateframe.cubic(F["half"]["right"], 0.5)) * MMPX / 10, 1)}
            print(f"{name:9} frame  axis {F['L']:.0f} px, theta {F['thetaDeg']}")

    garment = id_img.split()[0].point(lambda p: 255 if p else 0)

    # ---- trims (StepA extension, step L1): the trim field of tools/trimfield.py, exact. The main field holds every trim but the
    # slits, one group per zone, back to front (inside a group the nearest edge wins: a mitre where two trims meet); the slits have
    # a field of their own (the page turns them on and off apart and mitres them against the hem). The neck of a view with the live
    # neckline is laid by the page from the live edge, so it is not in the field. id G = the main field's trim.
    import trimfield as TF
    occl = Image.new("L", (W, H), 0)
    for poly in Z.get("occluders", []):
        ImageDraw.Draw(occl).polygon([tuple(q) for q in poly], fill=255)
    zpx, opx = id_img.load(), occl.load()
    zorder = {ZONE_ID[n]: z["order"] for n, z in Z["zones"].items()}
    groups = {"main": {}, "slit": {}}
    for name, trim in Z["trims"].items():
        zn = trim["zone"]
        els, tin, tout, length_cm = TF.trim_elements(trim, Z["zones"][zn]["frame"], MMPX)
        plate["trims"][name] = {"id": TRIM_ID[name], "type": trim["type"], "lengthCm": round(length_cm, 2), "side": trim["side"],
                                "zone": zn, "anchor": trim.get("anchor", "cf")}
        if name == "neck" and NECK: continue
        groups["slit" if name in TF.SLIT_OFF_CM else "main"].setdefault(ZONE_ID[zn], []).append((TRIM_ID[name], els, tin, tout))
    FIELD = {k: TF.rasterise(sorted(g.items(), key=lambda kv: zorder[kv[0]]), W, H, lambda x, y: zpx[x, y][0], zorder,
                             lambda x, y: opx[x, y] > 0) for k, g in groups.items()}
    gch = Image.new("L", (W, H), 0)
    gpx = gch.load()
    for i, (tid, _, _) in FIELD["main"].items(): gpx[i % W, i // W] = tid
    r_, _, b_ = id_img.split()
    id_img = Image.merge("RGB", (r_, gch, b_))

    # ---- neck area: id.png B = 1 (halfway.md step 2)
    if NECK and "area" in NECK:
        r, g_, b_ = id_img.split()
        b_.paste(1, (0, 0), NECK["area"])
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
    # Settings "shadeSmoothMm": radius in mm (default 1.2, 0 = off); "shadeSmoothEps": regularisation on the 0..2 shade (default 0.006; 0.002 left 33 % of the weave on the sleeve plate).
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
    # Settings "shadeSpace": "srgb" keeps the old file: L / median * 127.5, 128 = normal light, no "shadeEncoding" key.
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
    if FMAP: plate["uvOffsetCm"] = UV_OFF


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


    if NECK and "area" in NECK:
        # shade in the dip: the garment's shade carried 8 px outward (mean of known neighbours), so that a smooth (LINEAR) read at
        # the photographed edge does not mix in the 1.0 of the background (the page reads the edge band there when it moves)
        x0, y0, x1, y1 = NECK["rect"]
        sp, gp, ngp = shade.load(), garment.load(), NECK["area"].load()
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
        tw = 12.0 / MMPX                                   # the photographed garment's own edge band (the toile colour is read below it)
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
            # the corner line: the anchor's neck-point line through neck-l and neck-r, across the plate (StepA step 4)
            "top": ([[0.0, round(nl[1] + (nr[1] - nl[1]) * (0 - nl[0]) / (nr[0] - nl[0]), 3)], [float(W), round(nl[1] + (nr[1] - nl[1]) * (W - nl[0]) / (nr[0] - nl[0]), 3)]]
                    if (nl := lm.get("neck-l")) and (nr := lm.get("neck-r")) else None),
            "cf": [NECK["cfx"], lm.get("cf-neck", [NECK["cfx"], max(p[1] for p in edge)])[1]],
            "stitchMm": stitch_mm,
            "reachDeepMm": NECK_REACH_DEEP_MM, "reachWideMm": NECK_REACH_WIDE_MM,
            "rect": list(NECK["rect"]),                                    # the neck area (id B = 1) lies inside
            "toileRGB": med_rgb(below_pts), "formRGB": med_rgb(above_pts),
        }

    return {"id": id_img, "uv": uv_img, "field": FIELD, "shade": shade, "plate": plate, "k_of_stored": k_of_stored,
            "base": base, "garment": garment}


def check_image(M):
    """check.png: a 2 cm checker on the fabric, times the shade; on the trims, a 30 mm lace as stripes every cm along (purple on
    gold, the overhang orange), the mitres and the ends as the field lays them."""
    uv_img, id_img, shade, base, k_of_stored = M["uv"], M["id"], M["shade"], M["base"], M["k_of_stored"]
    W, H = base.size
    MM = M["plate"]["mmPerPx"]
    uvp, idp, shp = uv_img.load(), id_img.load(), shade.load()
    out = base.copy()
    op = out.load()
    COL = {1: ((214, 72, 64), (245, 225, 210)), 2: ((44, 92, 190), (215, 228, 250)),
           3: ((44, 92, 190), (215, 228, 250)), 4: ((38, 150, 96), (215, 240, 222)),
           5: ((140, 80, 170), (232, 222, 244))}

    def unpack(p):
        u = ((p[0] << 4) | (p[2] >> 4)) / 4095 * M["plate"]["uvRangeCm"]
        v = ((p[1] << 4) | (p[2] & 15)) / 4095 * M["plate"]["uvRangeCm"]
        return u, v

    for y in range(H):
        for x in range(W):
            z = idp[x, y][0]
            if not z: continue
            u, v = unpack(uvp[x, y])
            op[x, y] = tuple(min(255, int(ch * k_of_stored[shp[x, y]])) for ch in COL[z][(int(u / 2) + int(v / 2)) % 2])
    for key in ("main", "slit"):
        for i, (tid, s_, t) in M["field"][key].items():
            x, y = i % W, i // W
            tm = t * MM
            if tm < -3.0 or tm > 30.0: continue
            c = (251, 140, 0) if tm < 0 else (150, 40, 170) if int(math.floor(s_)) % 2 == 0 else (250, 200, 80)
            k = k_of_stored[shp[x, y]] if idp[x, y][0] else 1.0
            op[x, y] = tuple(min(255, int(ch * k)) for ch in c)
    return out


def review_image(P, base):
    """annotate.png (docs/annotate.md section 3) from the typed edges: free edges in the zone's colour (the front red, the others blue),
    a seam as red and blue side by side, the neck cut dashed red, frame edges not drawn; each zone's fabric axis in dashed green; trims
    (neck purple, cuffs orange, hem gold, slits teal), stitches dashed grey, landmarks as black dots."""
    RED, BLUE, PURPLE, ORANGE, GOLD, TEAL, GREY, GREEN = (229, 57, 53), (30, 99, 233), (142, 36, 170), (251, 140, 0), (199, 145, 0), (0, 137, 123), (97, 97, 97), (46, 125, 50)
    img = base.copy()
    d = ImageDraw.Draw(img)

    def dashed(pts, col, w=2, on=8, off=6):
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

    def shifted(pts, dist):
        out = []
        for i, (x, y) in enumerate(pts):
            a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
            tx, ty = b[0] - a[0], b[1] - a[1]; n = math.hypot(tx, ty) or 1
            out.append((x - ty / n * dist, y + tx / n * dist))
        return out
    colour = {zn: (RED if zn == "front" else BLUE) for zn in P["zones"]}
    for n, e in P["edges"].items():
        pts = [tuple(p) for p in e["points"]]
        users = [zn for zn, z in P["zones"].items() if any(m == n for m, _ in z["outline"])]
        if e["type"] == "frame": continue
        if e["type"] == "cut": dashed(pts, RED, 3); continue
        if e["type"] == "seam" and len(users) == 2 and "under" not in e:
            d.line(shifted(pts, 1.5), fill=colour[users[0]], width=2); d.line(shifted(pts, -1.5), fill=colour[users[1]], width=2)
        elif e.get("under"):
            dashed(pts, colour[users[0]], 1, 3, 4)
        else:
            d.line(pts, fill=colour[users[0]] if users else RED, width=2, joint="curve")
    for zn, z in P["zones"].items():
        F = z.get("frame")
        if F and F.get("axis"): dashed([tuple(p) for p in F["axis"]], GREEN, 1, 10, 8)
    tcol = lambda n: PURPLE if n == "neck" else ORANGE if n.startswith("cuff") else TEAL if n.startswith("slit") else GOLD
    for n, t in P.get("trims", {}).items():
        if t.get("line"): d.line([tuple(p) for p in t["line"]], fill=tcol(n), width=2)
    for pts in P.get("stitches", {}).values(): dashed([tuple(p) for p in pts], GREY, 1, 6, 5)
    for x, y in P.get("landmarks", {}).values():
        d.ellipse((x - 4, y - 4, x + 4, y + 4), fill="black", outline="white", width=1)
    return img


def view_of(pd):
    return os.path.basename(os.path.normpath(pd)).split("-")[0]


def annotate_module(pd):
    name = "annotate_" + view_of(pd)
    if not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), name + ".py")): return None
    return importlib.import_module(name)


def derive_trims(P):
    """Each trim's line (StepA extension, step L1): its garment edge, resampled every px, smoothed over 4 mm (a moving average whose
    window shrinks toward the ends), and cut between its anchors (from / to: the landmarks' nearest points on it), running from `from`
    to `to`; thinned to 0.05 px. Also the trim's zone (the one whose outline holds the edge) and `side`: the sign that turns the line's
    left normal toward that zone (a vote 3 px in). The lace itself (its width, its repeat) is the lace's (tools/trimfield.py)."""
    import snap_edges as SE
    mm = P["mmPerPx"]
    O = {zn: platedat.outline(P, zn) for zn in P["zones"]}
    for tn, t in P.get("trims", {}).items():
        if "edge" not in t: continue
        e = P["edges"][t["edge"]]["points"]
        zn = next(z for z, zz in P["zones"].items() if any(n == t["edge"] for n, _ in zz["outline"]))
        C = SE.resample(e, 1.0)
        h = max(1, round(2.0 / mm))                       # 4 mm window, symmetric: it shrinks toward the ends (no kink at an end)
        sm = []
        for i in range(len(C)):
            k = min(h, i, len(C) - 1 - i)
            w = C[i - k:i + k + 1]
            sm.append([sum(p[0] for p in w) / len(w), sum(p[1] for p in w) / len(w)])
        C = sm
        L = P.get("landmarks", {})
        if t.get("from") in L and t.get("to") in L:
            ia = min(range(len(C)), key=lambda i: math.dist(C[i], L[t["from"]]))
            ib = min(range(len(C)), key=lambda i: math.dist(C[i], L[t["to"]]))
            C = C[ia:ib + 1] if ia <= ib else C[ib:ia + 1][::-1]
        N = SE.normals(C, 8)
        votes = sum(1 if SE.inside((x + nx * 3, y + ny * 3), O[zn]) else -1 for (x, y), (nx, ny) in zip(C[::5], N[::5]))   # N: left normals
        t["zone"], t["side"] = zn, (1 if votes >= 0 else -1)
        t["line"] = [[round(x, 2), round(y, 2)] for x, y in SE.dp(C, 0.05)]
        t.pop("centre", None)


def fit_frames(P):
    """StepA step 4: each zone's frame from its specification (the annotate script: "axis" = two or more landmarks or "midline";
    "anchor" = {"line": [landmark, landmark]} (the neck-point line) or {"point": landmark} (+ "vMm"); "sagEdge"; "skipTop"):
    the axis (two landmarks or points: a line; more: x as a polynomial of y through them, degree "axisDegree" (default 2), sampled
    as 16 segments; a midline: the same, fitted to the middle of the zone's span on every 10th row from 5 to 95 % of its height;
    beyond its ends it runs on straight), the half widths (rays ending on an occluder's edge count as not a silhouette), its length, the
    anchor's position on it, the half widths (cubics fitted to rays from the axis to the zone's outline), thetaDeg, the sag."""
    import snap_edges as SE
    S = P.get("settings", {})
    thd = {"front": 60, "sleeve-l": 70, "sleeve-r": 70, **S.get("thetaDeg", {})}
    for zn, z in P["zones"].items():
        spec = z.get("frame")
        if not spec: continue
        spec = {k: v for k, v in spec.items() if k in ("axisFrom", "anchor", "sagEdge", "skipTop", "axisDegree")} if "axisFrom" in spec else {
            "axisFrom": spec["axis"], **{k: v for k, v in spec.items() if k in ("anchor", "sagEdge", "skipTop", "axisDegree")}}
        O = platedat.outline(P, zn)
        a = spec["axisFrom"]
        if a == "midline":
            rows = []
            ys = [p[1] for p in O]
            y_top, y_bot = min(ys), max(ys)                 # 5 % .. 95 % of the height: the end rows cut the hem / the cap themselves
            for y in range(int(y_top + 0.05 * (y_bot - y_top)), int(y_bot - 0.05 * (y_bot - y_top)), 10):
                xs = sorted(x0 + (y - y0_) * (x1 - x0) / (y1 - y0_) for (x0, y0_), (x1, y1) in zip(O, O[1:] + O[:1]) if (y0_ <= y < y1) or (y1 <= y < y0_))
                if len(xs) >= 2: rows.append([(xs[0] + xs[-1]) / 2, float(y)])
            # a smooth axis: x = a polynomial of y (degree "axisDegree", default 2) through the rows' midpoints, sampled every 8 px
            deg = spec.get("axisDegree", 2)
            ymid = (rows[0][1] + rows[-1][1]) / 2; yh = (rows[-1][1] - rows[0][1]) / 2 or 1.0
            c = plateframe.lstsq([(r[1] - ymid) / yh for r in rows], [r[0] for r in rows], deg)
            ny = 16
            axis = []
            for i in range(ny + 1):
                y = rows[0][1] + (rows[-1][1] - rows[0][1]) * i / ny
                t = (y - ymid) / yh
                axis.append([sum(c[k] * t ** k for k in range(deg + 1)), y])
        else:                                               # landmarks or points; more than 2: a smooth curve through them
            pts = [list(P["landmarks"][n]) if isinstance(n, str) else list(n) for n in a]
            if len(pts) > 2:
                deg = min(len(pts) - 1, spec.get("axisDegree", 2))
                ymid = (pts[0][1] + pts[-1][1]) / 2; yh = (pts[-1][1] - pts[0][1]) / 2 or 1.0
                c = plateframe.lstsq([(p[1] - ymid) / yh for p in pts], [p[0] for p in pts], deg)
                axis = []
                for i in range(17):
                    y = pts[0][1] + (pts[-1][1] - pts[0][1]) * i / 16
                    t = (y - ymid) / yh
                    axis.append([sum(c[k] * t ** k for k in range(deg + 1)), y])
            else:
                axis = pts
        axis = [[round(x, 1), round(y, 1)] for x, y in axis]
        L = plateframe.axis_length(axis)
        an = spec.get("anchor", {})
        if "line" in an:                                    # where the axis crosses the line through two landmarks
            p1, p2 = P["landmarks"][an["line"][0]], P["landmarks"][an["line"][1]]
            side = lambda q: (p2[0] - p1[0]) * (q[1] - p1[1]) - (p2[1] - p1[1]) * (q[0] - p1[0])
            s0, prev = None, None
            for i in range(-800, int(L * 2) + 801):
                s = i / 2
                q = axis_at(axis, s)
                v = side(q)
                if prev is not None and (prev[1] <= 0) != (v <= 0):
                    s0 = prev[0] + (s - prev[0]) * prev[1] / (prev[1] - v); break
                prev = (s, v)
            if s0 is None: raise ValueError(f"{zn}: the axis does not cross the anchor line")
        else:
            s0 = plateframe.project(axis, P["landmarks"][an["point"]])[0]
        segs = []
        occl = {n for o in P.get("occluders", []) if o and isinstance(o[0][0], str) for n, _ in o}   # an object in front is no silhouette
        for name, d in z["outline"]:
            pts = P["edges"][name]["points"]
            segs += [(p, q, "frame" if name in occl else P["edges"][name]["type"]) for p, q in zip(pts, pts[1:])]
        half, info = plateframe.fit_half(axis, segs, spec.get("skipTop", 0.0))
        F = {**spec, "axis": axis, "L": round(L, 3), "s0": round(s0, 3), "vMm": an.get("vMm", 0.0), "thetaDeg": thd[zn], "half": half,
             "sag": plateframe.fit_sag(axis, P["edges"][spec["sagEdge"]]["points"], s0) if spec.get("sagEdge") else {"c": 0.0, "s1": round(s0, 3)}}
        z["frame"] = F
        print(f"frame {zn:9} axis {len(axis)} points, L {L:.0f} px, s0 {s0:.1f}, half rays (good / all) {info}, sag {F['sag']}")


def axis_at(axis, s):
    """The point at arc length s on the axis; before 0 and past the end, along the end segments."""
    acc = 0.0
    for i, (a, b) in enumerate(zip(axis, axis[1:])):
        L = math.dist(a, b) or 1e-9
        if s <= acc + L or i == len(axis) - 2:
            if i == 0 and s < 0: f = s / L
            else: f = (s - acc) / L
            return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        acc += L


def source(pd):
    """(P without decisions, base image, the annotate module or None)."""
    mod = annotate_module(pd)
    if mod:                                                 # the base as the page sees it: encoded once as base.jpg, decoded again
        import io
        buf = io.BytesIO()
        mod.base(pd).save(buf, "JPEG", quality=94, subsampling=0)
        base = Image.open(io.BytesIO(buf.getvalue())).convert("RGB")
        base.jpeg = buf.getvalue()
        return mod.measure(), base, mod
    P = platedat.read(pd)                                   # imported data (the torso until StepA step 2)
    P.pop("decisions", None)
    return P, Image.open(os.path.join(pd, "base.jpg")).convert("RGB"), None


def decide(P, base):
    """The decisions of the plate (taken from the image), with the maps that they came from."""
    for n, z in P["zones"].items(): z["id"] = ZONE_ID[n]
    for n, t in P.get("trims", {}).items(): t["id"] = TRIM_ID[n]
    _, Z = platedat.legacy(P)
    M = rasterise(Z, base)
    pl = M["plate"]
    D = {k: pl[k] for k in ("shadeSmoothMm", "shadeSmoothPx", "shadeSpace", "shadeEncoding", "shadeMedian", "neck", "uvOffsetCm") if k in pl}
    D["zones"] = {n: {"widthCm": v["widthCm"], "heightCm": v["heightCm"]} for n, v in pl["zones"].items()}
    D["trims"] = {n: {"lengthCm": v["lengthCm"]} for n, v in pl["trims"].items()}
    P["decisions"] = D
    return P, M


def build(pd, report=None):
    P, base, mod = source(pd)
    if mod:                                                 # StepA step 3: free and cut edges snapped to the photo, trims from the edges
        import snap_edges
        rep = snap_edges.snap(P, base)
        if report is not None: report.update(rep)
        # the centre front of the neck lies ON the (snapped) neck edge: the live neckline scales its depth from there (StepA step 4)
        cut = next((e["points"] for e in P["edges"].values() if e["type"] == "cut"), None)
        if cut and "cf-neck" in P.get("landmarks", {}):
            x = P["landmarks"]["cf-neck"][0]
            for a, b in zip(cut, cut[1:]):
                if (a[0] - x) * (b[0] - x) <= 0 and a[0] != b[0]:
                    P["landmarks"]["cf-neck"] = [x, round(a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]), 2)]
                    break
        derive_trims(P)
        fit_frames(P)                                       # StepA step 4: the fabric frame of each zone
    P, M = decide(P, base)
    return P, M, base, mod


def maps_of(pd):
    """The maps of the committed plate.dat, in memory (for the checks: plate_invariants.py, maps_check.py, polish_metrics.py ...)."""
    P = platedat.read(pd)
    plate, Z = platedat.legacy(P)
    M = rasterise(Z, Image.open(os.path.join(pd, "base.jpg")).convert("RGB"))
    M["P"], M["zones"] = P, Z
    return M


def main():
    a = sys.argv[1:]
    pd = a[0].rstrip("/")
    rep = {}
    P, M, base, mod = build(pd, rep)
    if rep:
        import snap_edges
        print("\n".join("snap  " + l for l in snap_edges.summary(rep)))
    bad = platedat.validate(P)
    if bad: sys.exit("plate.dat would not validate:\n  " + "\n  ".join(bad))
    if mod: open(os.path.join(pd, "base.jpg"), "wb").write(base.jpeg)
    data = platedat.write(pd, P)
    print(f"{os.path.basename(pd)}: base.jpg + plate.dat ({len(data)} B)")
    if "--review" in a:
        rd = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "review", os.path.basename(pd))
        os.makedirs(rd, exist_ok=True)
        review_image(P, base).save(os.path.join(rd, "annotate.png"), optimize=True)
        chk = check_image(M)
        chk.save(os.path.join(rd, "check.png"), optimize=True)
        import subprocess
        subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "edge_crops.py"),
                        os.path.join(rd, "check.png"), pd, os.path.join(rd, "crops.png"), "--photo", os.path.join(pd, "base.jpg")])
        print("review:", os.path.normpath(rd))
    # the invariants of the plate itself (closure, gaps, symmetry, trim offset, smoothness, landmarks). Printed, not fatal.
    if "--no-check" not in a:
        import subprocess as _sp
        _r = _sp.run([sys.executable, "-W", "ignore", os.path.join(os.path.dirname(os.path.abspath(__file__)), "plate_invariants.py"), pd], capture_output=True, text=True)
        print("invariants:", "; ".join(l[5:].strip()[:140] for l in _r.stdout.splitlines() if l.startswith("FAIL")) or "none failing", "|", (_r.stdout.strip().splitlines() or ["?"])[-1])


if __name__ == "__main__":
    main()
