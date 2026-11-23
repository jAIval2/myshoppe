"""Lace photo on plain paper -> horizontal lace band with alpha, for the trim shader.

usage: python3 swatchprep/prep_lace.py <in> <out.webp> <preview.png> [--flip] [--cut-bottom 0.12] [--paper R,G,B] [--key 8]
       python3 swatchprep/prep_lace.py --repeat <band.webp> <out.webp> <out.json> <preview.png> [--width-mm 30] [--flip]
       python3 swatchprep/prep_lace.py --material <tile.webp> <sidecar.json> <out-mat.webp> <preview.png> [--pearls]

--material (polish.md step 6): R = height, G = metal mask, B = pearl mask, lossless WebP the size of the tile. See make_material().

--repeat (polish.md step 4): an existing band (the output of the first mode) -> a seamless repeat of whole periods:
  1. Period = autocorrelation of the alpha along the band (Pearson, on columns, at 1/4 size, refined at 1/2 size).
     Lags shorter than 0.3 x the band height are the mesh of the lace, not its repeat, and are skipped. The period is the
     first peak that is >= 0.6 and >= 0.9 x the best peak. No such peak: no period; the lace keeps the mirror.
  2. Cut n whole periods (n·P >= 1024 px when the band is long enough), starting at a gap between motifs, resampled so
     that the tile is an integer width with exactly n periods. The last 4 % cross-fades to the band just before the start,
     so the wrap is continuous.
  3. Sidecar json: periodPx, periods, periodRatio (period / band height), edge, widthMm (assumption), motifCentrePx, corr,
     edgeDepth (share of the height below the last row with >= 80 % alpha cover: the decorative edge; step 5).

1. Paper colour = median of the image border.
2. Lace mask = chromaticity distance to the paper (hue, not brightness: shadows stay paper) (blurred), on a small copy.
3. Band angle = principal axis of the mask (PCA). Rotate so the band is horizontal.
4. Crop: rows where the band is (mask coverage > 15 %), columns where every such row is inside the photo.
5. Alpha = colour distance to the paper, smooth ramp. Lace net becomes semi-transparent.
Convention: the decorative edge (loops, scallops, pearls) at the BOTTOM. --flip turns the band 180 deg.
Output height 446 px, like lace-pearl-2048.webp.
"""
import json, math, statistics, sys
from PIL import Image, ImageDraw, ImageFilter, ImageMath, ImageChops

REPEAT = "--repeat" in sys.argv


def make_band(src, out, prev):
    flip = "--flip" in sys.argv
    T = float(sys.argv[sys.argv.index("--key") + 1]) if "--key" in sys.argv else 8.0   # key threshold (noisy dark paper: 20)
    im = Image.open(src).convert("RGB")
    W, H = im.size

    # 1. paper colour from the border
    border = [im.getpixel((x, y)) for x in range(0, W, 8) for y in (2, H - 3)] + \
             [im.getpixel((x, y)) for y in range(0, H, 8) for x in (2, W - 3)]
    paper = tuple(statistics.median(c[i] for c in border) for i in range(3))
    if "--paper" in sys.argv:                        # lace that runs out of the frame at the sides: the border is not all paper
        paper = tuple(float(v) for v in sys.argv[sys.argv.index("--paper") + 1].split(","))


    def distance(img):
        """Chromaticity distance to the paper, x 765. Brightness is ignored, so the paper's own
        shadow (same hue, darker) stays background; sand / sage / gold lace differ in hue."""
        r, g, b = [c.convert("F") for c in img.split()]
        s0 = sum(paper)
        pr, pg, pb = paper[0] / s0, paper[1] / s0, paper[2] / s0
        return ImageMath.lambda_eval(
            lambda a: (((a["r"] / (a["r"] + a["g"] + a["b"] + 1.0) - pr) ** 2
                        + (a["g"] / (a["r"] + a["g"] + a["b"] + 1.0) - pg) ** 2
                        + (a["b"] / (a["r"] + a["g"] + a["b"] + 1.0) - pb) ** 2) ** 0.5) * 765.0,
            r=r, g=g, b=b)


    def to8(f):                                   # float distance -> 8-bit, clipped at 255
        return ImageMath.lambda_eval(lambda a: a["f"] * (a["f"] < 255) + 255 * (a["f"] >= 255), f=f).convert("L")


    # 2. mask on a small copy
    small = im.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(2))
    d = to8(distance(small)).point(lambda v: 255 if v > T else 0)
    pts = [(x, y) for y in range(d.height) for x in range(d.width) if d.getpixel((x, y))]
    mx = sum(p[0] for p in pts) / len(pts)
    my = sum(p[1] for p in pts) / len(pts)
    sxx = sum((p[0] - mx) ** 2 for p in pts); syy = sum((p[1] - my) ** 2 for p in pts)
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)
    ang = 0.5 * math.degrees(math.atan2(2 * sxy, sxx - syy))   # band direction, image coords (y down)

    # 3. rotate so the band is horizontal (PIL rotates counter-clockwise for positive angles)
    rot = im.rotate(ang, resample=Image.BICUBIC, expand=True, fillcolor=(0, 0, 0))
    valid = Image.new("L", im.size, 255).rotate(ang, resample=Image.NEAREST, expand=True, fillcolor=0)
    dist = distance(rot)
    mask = to8(dist).point(lambda v: 255 if v > T else 0)
    mask = ImageChops.multiply(mask, valid)

    # 4. rows of the band
    RW, RH = rot.size
    cover = [sum(1 for x in range(0, RW, 4) if mask.getpixel((x, y))) / (RW / 4) for y in range(RH)]
    peak = max(cover)
    rows = [y for y in range(RH) if cover[y] > 0.15 * peak]
    y0, y1 = rows[0], rows[-1]
    pad = round((y1 - y0) * 0.04)
    y0, y1 = max(0, y0 - pad), min(RH - 1, y1 + pad)
    # columns where every band row is inside the original photo
    cols = [x for x in range(RW) if valid.getpixel((x, y0)) and valid.getpixel((x, y1))]
    x0, x1 = cols[0] + 4, cols[-1] - 4
    span = x1 - x0
    x0, x1 = x0 + span // 10, x1 - span // 10          # middle 80 %: no curled or cut ends
    # cut the shadow strip: the paper's shadow under the lace picks up a little warm colour.
    # Keep rows down to the last one where strong lace colour (dist > 16) covers > 8 % of the row.
    strong = to8(dist).point(lambda v: 255 if v > 2 * T else 0)
    cov = [sum(1 for x in range(x0, x1, 3) if strong.getpixel((x, y))) / ((x1 - x0) / 3) for y in range(y0, y1)]
    last = max(i for i, c in enumerate(cov) if c > 0.08)
    first = min(i for i, c in enumerate(cov) if c > 0.08)
    y0, y1 = y0 + max(0, first - 3), y0 + min(len(cov), last + 3)
    cut = next((float(sys.argv[i + 1]) for i, v in enumerate(sys.argv) if v == "--cut-bottom"), 0.0)
    y1 = y1 - round((y1 - y0) * cut)               # manual cut of the remaining shadow strip, measured on the preview
    band = rot.crop((x0, y0, x1, y1))
    a = dist.crop((x0, y0, x1, y1))

    # 5. alpha: smooth ramp on the colour distance
    alpha = to8(a).point(lambda v: max(0, min(255, (v - T / 2) * 24))).filter(ImageFilter.GaussianBlur(0.6))
    band.putalpha(alpha)
    if flip:
        band = band.rotate(180)
    src_h = band.height                             # source px of the band height (for widthMm from a ruler)
    h = 446
    band = band.resize((round(band.width * h / band.height), h), Image.LANCZOS)
    band.save(out, quality=90, method=6)

    pv = Image.new("RGB", band.size, (60, 90, 70))
    pv.paste(band, (0, 0), band)
    pv.save(prev)
    print(f"{src.split('/')[-1]}: paper {tuple(round(c) for c in paper)}, angle {ang:.1f} deg, band {band.size}, aspect {band.width / band.height:.2f}, source band height {src_h} px")



def columns(a_img, scale):
    """Alpha columns at 1/scale size, mean removed: list of columns (lists)."""
    w, h = a_img.size
    a = a_img.resize((max(8, round(w / scale)), max(8, round(h / scale))), Image.BOX)
    px, W2, H2 = a.load(), a.size[0], a.size[1]
    cols = [[px[x, y] for y in range(H2)] for x in range(W2)]
    m = sum(map(sum, cols)) / (W2 * H2)
    return [[v - m for v in c] for c in cols]


def corr(cols, lag):
    from operator import mul
    n = len(cols) - lag
    num = sum(sum(map(mul, cols[x], cols[x + lag])) for x in range(n))
    d1 = sum(sum(map(mul, cols[x], cols[x])) for x in range(n))
    d2 = sum(sum(map(mul, cols[x + lag], cols[x + lag])) for x in range(n))
    return num / math.sqrt(d1 * d2 + 1e-9)


def find_period(band):
    a = band.split()[3]
    W, H = a.size
    sc = 4
    cols = columns(a, sc)
    lo, hi = max(2, int(0.3 * H / sc)), int(len(cols) * 0.75)
    cs = {l: corr(cols, l) for l in range(lo - 1, hi + 1)}
    peaks = [(l, cs[l]) for l in range(lo, hi) if cs[l] > cs[l - 1] and cs[l] >= cs[l + 1]]
    if not peaks:
        return None, 0.0, []
    best = max(c for _, c in peaks)
    ok = [(l, c) for l, c in peaks if c >= 0.6 and c >= 0.9 * best]
    if not ok:
        return None, best, peaks
    l0 = min(ok)[0]
    # refine at 1/2 size around the coarse peak, then a parabola through the best three lags
    sc2 = 2
    cols2 = columns(a, sc2)
    c2 = {l: corr(cols2, l) for l in range(l0 * 2 - 5, l0 * 2 + 6)}
    lb = max(c2, key=c2.get)
    if lb - 1 in c2 and lb + 1 in c2:
        y0, y1, y2 = c2[lb - 1], c2[lb], c2[lb + 1]
        den = y0 - 2 * y1 + y2
        off = 0.5 * (y0 - y2) / den if den else 0.0
    else:
        off = 0.0
    return (lb + off) * sc2 * W / (len(cols2) * sc2), c2[lb], peaks


def edge_depth(band):
    """Share of the band height that is the decorative edge (polish.md step 5): the rows below the last row where the lace
    alpha covers >= 80 % of the width (alpha > 50 %). None if no row is that full (an open lace): then the 35 % default."""
    a = band.split()[3]
    W, H = a.size
    px = a.load()
    full = [y for y in range(H) if sum(1 for x in range(0, W, 2) if px[x, y] > 127) >= 0.8 * len(range(0, W, 2))]
    if not full:
        return None, [round(sum(1 for x in range(0, W, 2) if px[x, y] > 127) / len(range(0, W, 2)), 2) for y in range(0, H, H // 10)]
    return round((H - 1 - full[-1]) / H, 3), None


def make_repeat(src, out, out_json, prev, width_mm, flip=False):
    band = Image.open(src).convert("RGBA")
    if flip:                                           # decorative edge was at the top: turn it to the bottom (the convention)
        band = band.rotate(180)
    W, H = band.size
    P, c, peaks = find_period(band)
    info = {"source": src.split("/")[-1], "bandPx": [W, H], "edge": "bottom", "widthMm": width_mm,
            "widthSrc": "assumed"}                          # then swatchprep/lace_sidecar.py upgrade: version 2 (name, class, sources)
    ed, cover = edge_depth(band)
    info["edgeDepth"] = ed
    if flip:
        info["flipped"] = True
    # an edging lace hangs past the garment edge (step 5): only if the bottom of the band is open (keyed), else paper shows
    abot = band.split()[3].crop((0, round(band.height * 0.95), band.width, band.height))
    open_share = sum(1 for v in abot.getdata() if v < 128) / (abot.width * abot.height)
    info["bottomOpen"] = round(open_share, 3)
    info["edging"] = bool(ed is not None and open_share >= 0.5)
    if not info["edging"]:
        info["edgingNote"] = ("bottom 5 % of the band is mostly opaque (paper or ground not keyed): insertion only, "
                              "until the lace is photographed and keyed again")
    if ed is None:
        info["edgeDepthNote"] = "no row with >= 80 % alpha cover (an open lace): the shader uses the 35 % default"
    if P is None:
        info.update({"periodPx": None, "mirror": True,
                     "reason": f"no repeat found: best autocorrelation peak {c:.2f} (< 0.6). Hand-made or irregular lace: "
                               "keep the mirrored repeat, with a mirror axis at the middle of neck and hem trims."})
        json.dump(info, open(out_json, "w"), indent=1)
        band.save(out, quality=90, method=6)
        print(f"{src.split('/')[-1]}: NO PERIOD (best peak {c:.2f}); mirror kept, band copied")
        return
    # blend length, whole periods that fit
    B_frac = 0.04
    n = max(1, math.ceil(1024 / P))
    while n > 1 and n * P * (1 + B_frac) + P + 2 > W:
        n -= 1
    span = n * P
    B_src = B_frac * span
    # start at a gap between motifs: the column of least alpha (smoothed over 3 % of the period) in [B_src, B_src + P)
    prof = [sum(col) for col in zip(*[[band.getpixel((x, y))[3] for x in range(W)] for y in range(0, H, 4)])]
    k = max(1, round(P * 0.03))
    sm = [sum(prof[max(0, i - k):i + k + 1]) / len(prof[max(0, i - k):i + k + 1]) for i in range(W)]
    start_lo = math.ceil(B_src) + 1
    start_hi = min(int(start_lo + P), int(W - span - 1))
    x0 = min(range(start_lo, start_hi + 1), key=lambda i: sm[i])
    L = round(span)                                    # tile width in px: exactly n periods after the resample
    tile = band.resize((L, H), Image.LANCZOS, box=(x0, 0, x0 + span, H))
    B = max(4, round(B_frac * L))
    kx = span / L
    # last B px: cross-fade to the band just before the start (the same place one tile earlier) -> continuous wrap
    alt = band.resize((B, H), Image.LANCZOS, box=(x0 + (L - B) * kx - span, 0, x0 + L * kx - span, H))
    cur = tile.crop((L - B, 0, L, H))
    ramp = Image.new("L", (B, 1))
    ramp.putdata([round(255 * (i + 0.5) / B) for i in range(B)])
    ramp = ramp.resize((B, H))
    tile.paste(Image.composite(alt, cur, ramp), (L - B, 0))
    tile.save(out, quality=90, method=6)
    Pt = L / n
    info.update({"periodPx": round(Pt, 3), "periods": n, "periodRatio": round(Pt / H, 5), "motifCentrePx": round(Pt / 2, 2),
                 "corr": round(c, 3), "cutFromPx": round(x0, 1), "blendPx": B, "mirror": False,
                 "note": "the tile starts at a gap between motifs: motif boundaries at multiples of periodPx, centres in between"})
    json.dump(info, open(out_json, "w"), indent=1)
    pv = Image.new("RGB", (L * 2, H), (60, 90, 70))
    pv.paste(tile, (0, 0), tile)
    pv.paste(tile, (L, 0), tile)
    pv.save(prev)
    print(f"{src.split('/')[-1]}: period {Pt:.1f} px in the tile ({P:.1f} in the band), corr {c:.2f}, n {n}, tile {L} x {H}, "
          f"start {x0}, blend {B} px")


def find_pearls(tile, hole=6.0, ring=(10, 16), ymin=0.7):
    """Pearls in a keyed lace are RINGS: their bright centres were keyed out with the paper (render.md, known problem).
    A pearl = a round transparent hole (difference of Gaussians on the inverted alpha, at the hole size) closed by a pale,
    bright, opaque ring, in the decorative edge (centre in the bottom 30 % of the band)."""
    W, H = tile.size
    a = tile.split()[3]
    ap = a.load()
    Lp = tile.convert("RGB").convert("L").load()
    Sp = tile.convert("RGB").convert("HSV").split()[1].load()
    inv = a.point(lambda v: 255 - v)
    dog = ImageMath.lambda_eval(lambda x: x["p"] - x["q"], p=inv.filter(ImageFilter.GaussianBlur(hole / 1.6)).convert("F"),
                                q=inv.filter(ImageFilter.GaussianBlur(hole * 2.0)).convert("F"))
    dl = ImageMath.lambda_eval(lambda x: x["d"] + 128.0, d=dog).convert("L")
    mx = dl.filter(ImageFilter.MaxFilter(int(hole * 2) | 1))
    dp, mp = dl.load(), mx.load()
    r0, r1 = ring
    cand = [(dp[x, y], x, y) for y in range(max(r1 + 1, int(ymin * H)), H - r1 - 1) for x in range(r1 + 1, W - r1 - 1)
            if dp[x, y] == mp[x, y] and dp[x, y] > 145 and ap[x, y] < 100]
    keep = []
    for _, x, y in sorted(cand, reverse=True):
        n = o = 0
        lum, sat = [], []
        for k in range(32):
            th = 2 * math.pi * k / 32
            for rr in (r0, (r0 + r1) / 2, r1):
                xx, yy = int(x + rr * math.cos(th)), int(y + rr * math.sin(th))
                n += 1
                if ap[xx, yy] > 160:
                    o += 1
                    lum.append(Lp[xx, yy])
                    sat.append(Sp[xx, yy])
        if o / n < 0.65 or not lum:
            continue
        ds = []                                            # roundness: centre -> first opaque pixel, 16 directions
        for k in range(16):
            th = 2 * math.pi * k / 16
            d = r1 + 4
            for rr in range(1, r1 + 4):
                if ap[int(x + rr * math.cos(th)), int(y + rr * math.sin(th))] > 160:
                    d = rr
                    break
            ds.append(d)
        m = sum(ds) / len(ds)
        cv = (sum((d - m) ** 2 for d in ds) / len(ds)) ** 0.5 / m
        if cv > 0.35 or sum(lum) / len(lum) < 160 or sum(sat) / len(sat) > 45:
            continue
        if all((x - bx) ** 2 + (y - by) ** 2 > (2 * r1) ** 2 for bx, by in keep):
            keep.append((x, y))
    return keep


def make_material(tile_path, meta_path, out_path, prev_path=None):
    """Lace material map (polish.md step 6), lossless WebP at HALF the size of the lace tile (height and masks are smooth;
    half size keeps every lace asset under 600 KB). The shader samples it with the same coordinates as the lace.
    R = height: lace luminance high-passed at 2 mm (in lace scale), weighted by alpha; 128 = flat.
    G = metal: zari / metallic thread: hue 20..60 deg (gold .. brass), saturation >= 0.55, strong local brightness change.
    B = pearl: a dome on each pearl found by find_pearls() (pearl radius = the outer ring radius)."""
    tile = Image.open(tile_path).convert("RGBA")
    meta = json.load(open(meta_path))
    W, H = tile.size
    width_mm = meta.get("widthMm") or 30.0
    px_per_mm = H / width_mm
    a = tile.split()[3]
    L = tile.convert("RGB").convert("L")
    r = max(2.0, 2.0 * px_per_mm)
    hp = ImageMath.lambda_eval(lambda x: (x["l"] - x["b"]) * x["a"] / 255.0, l=L.convert("F"),
                               b=L.filter(ImageFilter.GaussianBlur(r)).convert("F"), a=a.convert("F"))
    vals = sorted(v for v, al in zip(hp.getdata(), a.getdata()) if al > 128)
    lo, hi = vals[int(len(vals) * 0.01)], vals[int(len(vals) * 0.99)]
    span = max(abs(lo), abs(hi), 1e-3)
    height = ImageMath.lambda_eval(lambda x: 128.0 + x["h"] * (127.0 / span), h=hp).convert("L")
    hsv = tile.convert("RGB").filter(ImageFilter.GaussianBlur(1.0)).convert("HSV")
    hh, ss, vv = hsv.split()
    hue_ok = hh.point(lambda v: 255 if 14 <= v <= 42 else 0)
    sat_ok = ss.point(lambda v: 255 if v >= 140 else 0)                     # >= 0.55: geometric beige reaches 0.48 at p90
    var = ImageChops.difference(L, L.filter(ImageFilter.GaussianBlur(max(2.0, 0.5 * px_per_mm)))).filter(ImageFilter.GaussianBlur(2))
    var_ok = var.point(lambda v: 255 if v >= 6 else 0)
    metal = ImageChops.multiply(ImageChops.multiply(ImageChops.multiply(hue_ok, sat_ok), var_ok),
                                a.point(lambda v: 255 if v > 128 else 0))
    metal = metal.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1.5))
    # a zari lace is metallic through and through; a few saturated crevices in a cotton lace are not metal:
    # keep the mask only if >= 30 % of the opaque lace passes the pixel test
    opaque = sum(1 for v in a.getdata() if v > 128) or 1
    metal_share = sum(1 for v, al in zip(metal.getdata(), a.getdata()) if v > 64 and al > 128) / opaque
    if metal_share < 0.30:
        metal = Image.new("L", (W, H), 0)
    pearl = Image.new("L", (W, H), 0)
    blobs = []
    if meta.get("pearls"):
        p = meta["pearls"]
        blobs = find_pearls(tile, p.get("holePx", 6), tuple(p.get("ringPx", (10, 16))), p.get("ymin", 0.7))
        pr = p.get("ringPx", (10, 16))[1]
        d = ImageDraw.Draw(pearl)
        for x, y in blobs:                               # a dome: 255 at the centre, 0 at the pearl's outer radius
            for k in range(int(pr), 0, -1):
                d.ellipse((x - k, y - k, x + k, y + k), fill=round(255 * (1 - (k / pr) ** 2) ** 0.5))
    mat = Image.merge("RGB", (height, metal, pearl)).resize((W // 2, H // 2), Image.BOX)
    mat.save(out_path, lossless=True, method=6)
    cover = lambda im: round(sum(1 for v in im.getdata() if v > 64) / (W * H) * 100, 2)
    info = {"file": out_path.split("/")[-1], "size": [W // 2, H // 2], "heightRadiusPx": round(r, 1),
            "metalCoverPct": cover(metal), "metalPixelShare": round(metal_share, 3), "pearls": len(blobs),
            "pearlsPerRepeat": round(len(blobs) / meta["periods"], 2) if meta.get("periods") else None}
    meta["material"] = info
    json.dump(meta, open(meta_path, "w"), indent=1)
    if prev_path:
        pv = Image.new("RGB", (W, H * 4), (40, 40, 40))
        bg = Image.new("RGB", (W, H), (60, 90, 70))
        bg.paste(tile, (0, 0), tile)
        pv.paste(bg, (0, 0)); pv.paste(height.convert("RGB"), (0, H)); pv.paste(metal.convert("RGB"), (0, 2 * H)); pv.paste(pearl.convert("RGB"), (0, 3 * H))
        pv.save(prev_path)
    print(f"{tile_path.split('/')[-1]}: height r {r:.1f} px, metal {info['metalCoverPct']} % of the tile, pearls {len(blobs)}"
          + (f" ({info['pearlsPerRepeat']} per repeat)" if info["pearlsPerRepeat"] is not None else "") + f", map {W // 2} x {H // 2}")

if __name__ == "__main__":
    if "--material" in sys.argv:
        i = sys.argv.index("--material")
        m_tile, m_json, m_out, m_prev = sys.argv[i + 1:i + 5]
        if "--pearls" in sys.argv:                        # this lace has pearls: hole radius, ring radii in tile px (measured)
            meta = json.load(open(m_json))
            meta["pearls"] = {"holePx": 6, "ringPx": [10, 16], "ymin": 0.7}
            json.dump(meta, open(m_json, "w"), indent=1)
        make_material(m_tile, m_json, m_out, m_prev)
    elif REPEAT:
        i = sys.argv.index("--repeat")
        a_src, a_out, a_json, a_prev = sys.argv[i + 1:i + 5]
        wmm = float(sys.argv[sys.argv.index("--width-mm") + 1]) if "--width-mm" in sys.argv else None
        make_repeat(a_src, a_out, a_json, a_prev, wmm, flip="--flip" in sys.argv)
    else:
        make_band(*sys.argv[1:4])
