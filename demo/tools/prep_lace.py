"""Lace photo on plain paper -> horizontal lace band with alpha, for the trim shader.

usage: python3 tools/prep_lace.py <in> <out.webp> <preview.png> [--flip] [--cut-bottom 0.12]
       python3 tools/prep_lace.py --repeat <band.webp> <out.webp> <out.json> <preview.png> [--width-mm 30] [--flip]

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
from PIL import Image, ImageFilter, ImageMath, ImageChops

REPEAT = "--repeat" in sys.argv


def make_band(src, out, prev):
    flip = "--flip" in sys.argv
    im = Image.open(src).convert("RGB")
    W, H = im.size

    # 1. paper colour from the border
    border = [im.getpixel((x, y)) for x in range(0, W, 8) for y in (2, H - 3)] + \
             [im.getpixel((x, y)) for y in range(0, H, 8) for x in (2, W - 3)]
    paper = tuple(statistics.median(c[i] for c in border) for i in range(3))


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
    d = to8(distance(small)).point(lambda v: 255 if v > 8 else 0)
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
    mask = to8(dist).point(lambda v: 255 if v > 8 else 0)
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
    strong = to8(dist).point(lambda v: 255 if v > 16 else 0)
    cov = [sum(1 for x in range(x0, x1, 3) if strong.getpixel((x, y))) / ((x1 - x0) / 3) for y in range(y0, y1)]
    last = max(i for i, c in enumerate(cov) if c > 0.08)
    first = min(i for i, c in enumerate(cov) if c > 0.08)
    y0, y1 = y0 + max(0, first - 3), y0 + min(len(cov), last + 3)
    cut = next((float(sys.argv[i + 1]) for i, v in enumerate(sys.argv) if v == "--cut-bottom"), 0.0)
    y1 = y1 - round((y1 - y0) * cut)               # manual cut of the remaining shadow strip, measured on the preview
    band = rot.crop((x0, y0, x1, y1))
    a = dist.crop((x0, y0, x1, y1))

    # 5. alpha: smooth ramp on the colour distance
    alpha = to8(a).point(lambda v: max(0, min(255, (v - 4) * 24))).filter(ImageFilter.GaussianBlur(0.6))
    band.putalpha(alpha)
    if flip:
        band = band.rotate(180)
    h = 446
    band = band.resize((round(band.width * h / band.height), h), Image.LANCZOS)
    band.save(out, quality=90, method=6)

    pv = Image.new("RGB", band.size, (60, 90, 70))
    pv.paste(band, (0, 0), band)
    pv.save(prev)
    print(f"{src.split('/')[-1]}: paper {tuple(round(c) for c in paper)}, angle {ang:.1f} deg, band {band.size}, aspect {band.width / band.height:.2f}")



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
            "widthMmNote": "assumption: the real band width is not measured yet"}
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


if __name__ == "__main__":
    if REPEAT:
        i = sys.argv.index("--repeat")
        a_src, a_out, a_json, a_prev = sys.argv[i + 1:i + 5]
        wmm = float(sys.argv[sys.argv.index("--width-mm") + 1]) if "--width-mm" in sys.argv else None
        make_repeat(a_src, a_out, a_json, a_prev, wmm, flip="--flip" in sys.argv)
    else:
        make_band(*sys.argv[1:4])
