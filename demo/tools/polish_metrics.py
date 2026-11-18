"""Numbers for docs/plan/polish.md. Pillow only.

usage:
  python3 tools/polish_metrics.py fd   [plate ...]            fine detail of shade.png (step 0, 3)
  python3 tools/polish_metrics.py crops <shot-dir> <out-dir>  cut the fixed review crops from a shoot_views.sh run (DPR=2)
  python3 tools/polish_metrics.py fcr  <shot-dir> [flat-dir]  fold contrast retention for queries 2, 3, 4 (step 0, 2); flat-dir = run of FLAT_QUERIES
  python3 tools/polish_metrics.py joins                       lace repeat: mirror joins and join discontinuity (step 0, 4)

FD  (fine detail): variance of shade in the band below 1.5 mm = shade - G(1.5 mm), and in the fold band 2..30 mm =
    G(2 mm) - G(30 mm), as a share of the variance of the whole shade, inside the garment (zone mask), away from its
    edges (normalised blur: the 128 grey outside the garment never enters). G is a Gaussian blur; sigma = mm / mmPerPx.
    The shade is read as stored (shade.png), decoded by plate.json "shadeEncoding" when present.
FCR (fold contrast retention): (std/mean of L in the render) / (std/mean of L of the photo base.jpg), same plate box,
    both blurred by 8 mm first. The blur removes the pattern of the fabric (3-10 mm), so only the folds (> 20 mm) count.
    1.0 = the folds of the photo are kept exactly. The photo is the reference because shade = photo L / median, so the two
    have the same std/mean (std/mean does not change with the scale of a signal).
"""
import json, math, os, sys
from PIL import Image, ImageChops, ImageFilter, ImageMath, ImageStat

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
PLATES = os.path.join(ROOT, "assets", "plates")
SWATCHES = os.path.join(ROOT, "assets", "swatches")

# ---- the fixed review set (polish.md step 0), same order every time
QUERIES = [
    "view=torso&fabric=sage&lace=pearl",
    "view=torso&fabric=mocha&lace=geometric",
    "view=neck&fabric=mustard&lace=leaf",
    "view=neck&fabric=mocha&lace=fine",
    "view=sleeve&fabric=sage&lace=geometric",
    "view=hem&fabric=mocha&lace=geometric",
    "view=hem&fabric=mustard&lace=pearl",
    "view=neck&fabric=off",
]
PLATE_OF = {"torso": "torso-straight", "neck": "neck-straight", "sleeve": "sleeve-straight", "hem": "hem-straight"}
# the canvas of the stage in a DPR 2 screenshot of a 900 x 760 window: x 64, y 64, 860 px wide (plate 1200 -> 0.7167)
CANVAS_X, CANVAS_Y, CANVAS_W = 64, 64, 860
# fixed crops, in PLATE px (x0, y0, x1, y1): name -> (query index, box). Set from the trim bounding boxes in id.png,
# above the caption pill of the stage (it covers plate y > ~1466). Frozen at step 0: never changed.
CROPS = {
    "neck-lace-q3": (2, (300, 350, 910, 560)),        # neckline lace, mustard + leaf
    "neck-lace-q4": (3, (300, 350, 910, 560)),        # neckline lace, mocha + fine
    "cuff-lace-q5": (4, (200, 1230, 620, 1465)),      # cuff lace, sage + geometric
    "hem-lace-q2": (1, (380, 1395, 830, 1465)),       # hem lace, torso, mocha + geometric
    "hem-lace-q6": (5, (200, 1170, 900, 1390)),       # hem lace, hem view, mocha + geometric
    "hem-lace-q7": (6, (200, 1170, 900, 1390)),       # hem lace, hem view, mustard + pearl
    "bodice-q2": (1, (430, 600, 730, 900)),           # bodice centre, torso, mocha
    "bodice-q3": (2, (400, 760, 800, 1160)),          # bodice centre, neck view, mustard
    "bodice-q4": (3, (400, 760, 800, 1160)),          # bodice centre, neck view, mocha
}
FCR_CROPS = ["bodice-q2", "bodice-q3", "bodice-q4"]
FCR_PLATE = {"bodice-q2": "torso", "bodice-q3": "neck", "bodice-q4": "neck"}


def plate_json(p):
    return json.load(open(os.path.join(PLATES, p, "plate.json")))


def decode_shade(img, pj):
    """L image of the stored shade -> same L image as the shade value 0..2 scaled to 0..255 (so that blur and stats keep 8 bit)."""
    enc = pj.get("shadeEncoding", "srgb")
    if enc == "sqrt":     # shade = 2 * stored^2, stored 0..1  ->  value/2 = stored^2
        return img.point(lambda v: round(255 * (v / 255) ** 2))
    return img


def blur_norm(img, mask, sigma):
    """Normalised Gaussian blur of an L image inside a 0/255 mask: blur(img*m) / blur(m). Returns (F image, F weight)."""
    num = ImageChops.multiply(img, mask).filter(ImageFilter.GaussianBlur(sigma)).convert("F")   # mask is 0/255: img * mask / 255
    den = mask.filter(ImageFilter.GaussianBlur(sigma)).convert("F")
    return ImageMath.lambda_eval(lambda a: a["n"] * 255.0 / (a["d"] + 1e-3), n=num, d=den), den


def mean_of(f, w):
    """Mean of F image f over the pixels where weight image w is 1, with one resize to 1 x 1 (Pillow has no numpy)."""
    fw = ImageMath.lambda_eval(lambda a: a["f"] * a["w"], f=f, w=w)
    s = fw.resize((1, 1), Image.BOX).getpixel((0, 0))
    n = w.resize((1, 1), Image.BOX).getpixel((0, 0))
    return s / n


def var_of(f, w):
    m = mean_of(f, w)
    return mean_of(ImageMath.lambda_eval(lambda a: (a["f"] - m) ** 2, f=f), w)


def fd(plate):
    pj = plate_json(plate)
    mm = pj["mmPerPx"]
    d = os.path.join(PLATES, plate)
    shade = decode_shade(Image.open(os.path.join(d, "shade.png")).convert("L"), pj)
    idr = Image.open(os.path.join(d, "id.png")).convert("RGB").split()[0]
    garment = idr.point(lambda v: 255 if v else 0)
    # evaluate only where a 30 mm blur is made of garment (> 98 %): no edge effects
    s30 = 30 / mm
    _, den = blur_norm(shade, garment, s30)
    inside = ImageMath.lambda_eval(lambda a: 1.0 * (a["d"] > 250.0), d=den)
    sf = shade.convert("F")
    tot = var_of(sf, inside)
    g15, _ = blur_norm(shade, garment, 1.5 / mm)
    g2, _ = blur_norm(shade, garment, 2.0 / mm)
    g30, _ = blur_norm(shade, garment, s30)
    hp = ImageMath.lambda_eval(lambda a: a["s"] - a["g"], s=sf, g=g15)
    fold = ImageMath.lambda_eval(lambda a: a["a"] - a["b"], a=g2, b=g30)
    n = inside.resize((1, 1), Image.BOX).getpixel((0, 0)) * shade.width * shade.height
    return {"plate": plate, "mmPerPx": mm, "px_evaluated": round(n), "var_total": round(tot, 3),
            "fine_<1.5mm_var": round(var_of(hp, inside), 4), "fine_share": round(var_of(hp, inside) / tot, 5),
            "fold_2-30mm_var": round(var_of(fold, inside), 3), "fold_share": round(var_of(fold, inside) / tot, 4)}


def cmd_fd(plates):
    for p in plates or sorted(os.listdir(PLATES)):
        if os.path.isdir(os.path.join(PLATES, p)):
            print(json.dumps(fd(p)))


def shot_box(box):
    k = CANVAS_W / 1200
    return tuple(round(v * k + o) for v, o in zip(box, (CANVAS_X, CANVAS_Y, CANVAS_X, CANVAS_Y)))


def cmd_crops(shots, out):
    os.makedirs(out, exist_ok=True)
    for name, (qi, box) in CROPS.items():
        im = Image.open(os.path.join(shots, f"shot-{qi}.png")).convert("RGB")
        im.crop(shot_box(box)).save(os.path.join(out, name + ".png"))
        print(name, shot_box(box))


def cv(im_l):
    st = ImageStat.Stat(im_l)
    return st.stddev[0] / st.mean[0]


FLAT_QUERIES = [QUERIES[1] + "&shade=0", QUERIES[2] + "&shade=0", QUERIES[3] + "&shade=0"]      # shoot these for fcr-flat


def cmd_fcr(shots, flat=None):
    """flat = a shoot_views.sh run of FLAT_QUERIES (shot-0..2 = queries 2, 3, 4 with ?shade=0). With it, the fold map of the
    render is render L / flat L (the pattern of the fabric divides out), which is the exact version of the FCR."""
    for fi, name in enumerate(FCR_CROPS):
        qi, box = CROPS[name]
        view = PLATE_OF[FCR_PLATE[name]]
        mm = plate_json(view)["mmPerPx"]
        sig = 8 / mm * (CANVAS_W / 1200)                         # 8 mm, in screenshot px
        render = Image.open(os.path.join(shots, f"shot-{qi}.png")).convert("L").crop(shot_box(box))
        photo = Image.open(os.path.join(PLATES, view, "base.jpg")).convert("L").crop(box)
        photo = photo.resize(render.size, Image.BOX)             # same grid as the screenshot
        pb = photo.filter(ImageFilter.GaussianBlur(sig))
        m = round(sig * 1.5)                                     # crop the blurred images inside, so the blur edge does not count
        inner = (m, m, render.width - m, render.height - m)
        b = cv(pb.crop(inner))
        row = {"crop": name, "query": QUERIES[qi], "mean_L_render": round(ImageStat.Stat(render).mean[0], 1)}
        a = cv(render.filter(ImageFilter.GaussianBlur(sig)).crop(inner))
        row.update({"cv_render": round(a, 4), "cv_photo": round(b, 4), "FCR_plain": round(a / b, 3)})
        if flat:
            fl = Image.open(os.path.join(flat, f"shot-{fi}.png")).convert("L").crop(shot_box(box))
            ratio = ImageMath.lambda_eval(lambda x: x["r"] / (x["f"] + 1.0), r=render.convert("F"), f=fl.convert("F"))
            r8 = ratio.point(lambda v: v * 128.0).convert("L") if False else None
            # blur the ratio: ImageFilter needs L, so scale the ratio (0..2) to 0..255 first
            rl = ImageMath.lambda_eval(lambda x: x["q"] * 127.5, q=ratio).convert("L").filter(ImageFilter.GaussianBlur(sig)).crop(inner)
            c = cv(rl)
            row.update({"cv_fold_map": round(c, 4), "FCR": round(c / b, 3)})
        print(json.dumps(row))


def lace_info(name):
    im = Image.open(os.path.join(SWATCHES, f"lace-{name}-2048.webp")).convert("RGBA")
    meta_path = os.path.join(SWATCHES, f"lace-{name}.json")
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else None
    return im, meta


def join_jump(im):
    """Discontinuity at the wrap: mean abs RGBA difference between the last and the first column,
    divided by the median difference between neighbouring columns. ~1 = no visible join; >> 1 = a join."""
    w, h = im.size
    px = im.load()
    def col(x): return [px[x, y] for y in range(h)]
    def diff(a, b): return sum(abs(p[i] - q[i]) for p, q in zip(a, b) for i in range(4)) / (4 * h)
    wrap = diff(col(w - 1), col(0))
    neigh = sorted(diff(col(x), col(x + 1)) for x in range(0, w - 1, max(1, w // 200)))
    return wrap, neigh[len(neigh) // 2]


def cmd_joins():
    # (lace, trim, view): every trim a review crop shows
    trims = {"torso": ["neck", "cuff-l", "cuff-r", "hem"], "neck": ["neck"], "sleeve": ["neck", "cuff-l"], "hem": ["hem", "slit-l", "slit-r"]}
    laces = sorted({q.split("lace=")[1] for q in QUERIES if "lace=" in q})
    for lace in laces:
        im, meta = lace_info(lace)
        w, h = im.size
        wrap, neigh = join_jump(im)
        row = {"lace": lace, "size": [w, h], "wrap_jump": round(wrap, 2), "neighbour_jump": round(neigh, 2),
               "wrap_ratio": round(wrap / max(neigh, 1e-6), 2), "sidecar": bool(meta)}
        print(json.dumps(row))
        for view, names in trims.items():
            pj = plate_json(PLATE_OF[view])
            for t in names:
                if t not in pj["trims"]:
                    continue
                L, wmm = pj["trims"][t]["lengthCm"], pj["trims"][t]["widthMm"]
                tile_cm = wmm / 10 * w / h                         # one image of the lace along this trim
                mirror_joins = int(L // tile_cm)                   # MIRRORED_REPEAT: one mirror join at every multiple of the tile
                rep = (meta["periodRatio"] * wmm / 10) if meta else None
                print(f"   {view:6} {t:7} length {L:5.1f} cm  width {wmm:2d} mm  tile {tile_cm:5.1f} cm  "
                      f"mirror joins (computed) {mirror_joins}" + (f"  repeat {rep:.2f} cm  n={L / rep:.2f}" if rep else ""))


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    {"fd": lambda: cmd_fd(a[1:]), "crops": lambda: cmd_crops(a[1], a[2]), "fcr": lambda: cmd_fcr(a[1], a[2] if len(a) > 2 else None),
     "joins": cmd_joins}[a[0]]()
