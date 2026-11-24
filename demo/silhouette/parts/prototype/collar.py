import sys, numpy as np
from PIL import Image, ImageFilter
S, P, V = sys.argv[1:4]; sys.path.insert(0, V)
import torso as T
_src = open(f"{S}/place2.py").read(); exec(_src[_src.index("lum = lambda a"):_src.index("comp = n.copy()")])   # gblur, nblur, tps_fit, tps_eval
SRC = Image.open(f"{P}/torso-straight-part-mandarin.png").convert("RGB"); src = np.asarray(SRC, float); H, W = src.shape[:2]
raw = np.asarray(Image.open(f"{S}/collar_mask_raw.png")) > 0
yy, xx = np.mgrid[0:H, 0:W]
band = raw & (yy >= 310) & (yy <= 445) & (xx >= 745) & (xx <= 1050)                 # the collar band
slit = (xx >= 884) & (xx <= 912) & (yy >= 420) & (yy <= 785)                        # the front slit (placket)
cm = np.asarray(Image.fromarray(((band | slit) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))) > 0
ne = np.array(T.neck_edge, float); ny = np.interp(xx, ne[:, 0], ne[:, 1]); inx = (xx >= ne[:, 0].min()) & (xx <= ne[:, 0].max())
below = yy - ny
strip = np.where(inx & (below >= -6) & (below <= 55), np.clip((55 - below) / 32, 0, 1), 0)
soft = np.maximum(cm.astype(float), strip); cm = soft > 0
# anchors: the kurta's neckline (measured on its plate) <-> the anarkali's neckline (read on its photo)
def resample(pts, k):
    pts = np.array(pts, float); d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]; t = np.linspace(0, d[-1], k)
    return np.stack([np.interp(t, d, pts[:, 0]), np.interp(t, d, pts[:, 1])], 1)
sP = resample(T.neck_edge, 11)
hP = resample([(788, 292), (790, 296), (805, 316), (820, 330), (835, 338), (850, 343), (865, 346), (880, 347), (895, 347), (910, 347), (925, 348), (940, 346), (955, 344), (970, 338), (985, 329), (1000, 319), (1015, 306), (1020, 298)], 11)   # measured: first cloth-coloured run per column
mh, ms = hP.mean(0), sP.mean(0); X, Y = sP - ms, hP - mh
U_, D_, Vt = np.linalg.svd(Y.T @ X / len(X)); R = U_ @ Vt; sc = D_.sum() / (X ** 2).sum(1).mean()
invS = lambda p_: ((R.T @ (p_ - mh).T) / sc).T + ms; fwdS = lambda p_: (sc * (R @ (p_ - ms).T)).T + mh
res = sP - invS(hP)
zero = [(x, y) for x in (760, 830, 900, 970, 1040) for y in (200, 230)] + [(x, y) for x in (850, 900, 950) for y in (520, 620, 720)]
model = tps_fit(np.vstack([hP, zero]), np.vstack([res, np.zeros((len(zero), 2))]))
print("collar: scale %.3f  rotation %.1f deg  neckline residual max %.1f px" % (sc, np.degrees(np.arctan2(R[1, 0], R[0, 0])), np.abs(res).max()))
lum = lambda a: a.mean(2)
def place_collar(host_img, O_ref, out_name):
    h = np.asarray(host_img, float).copy(); o = np.asarray(O_ref, float)
    # light: the collar's folds over its own broad light, times the host garment's broad light around the neckline
    Ls = lum(src); lo_s, _ = nblur(Ls, cm, 30); hi = np.where(cm, Ls / np.maximum(lo_s, 1), 1) ** 0.75   # the hard light's fold contrast, softened
    gar_h = np.zeros((H, W), bool); gar_h[300:470, 760:1040] = True; gar_h &= lum(o) > 200            # the anarkali's garment near its neck
    gar_h &= ~((yy < 300) | ((xx > 780) & (xx < 1020) & (yy < 340)))                                  # not the form's neck
    lo_h, cov = nblur(lum(o), gar_h, 30); lo_h2, _ = nblur(lum(o), gar_h, 120)
    wgt = np.clip((cov - 0.15) / 0.35, 0, 1); light = lo_h * wgt + lo_h2 * (1 - wgt)
    gar_s = np.zeros((H, W), bool); gar_s[440:600, 780:1020] = True                                   # the kurta's garment below the collar
    tint_s = src[gar_s].mean(0) / lum(src)[gar_s].mean(); tint_h = o[gar_h].mean(0) / lum(o)[gar_h].mean()
    rel = src / np.maximum(lum(src), 1)[..., None] / tint_s; chroma = (1 + 0.5 * (rel - 1)) * tint_h   # half the source's colour cast                               # keeps the slit's form colour relative to the cloth
    x0, y0, x1, y1 = 700, 200, 1100, 700
    gy, gx = np.mgrid[y0:y1, x0:x1]; G = np.stack([gx.ravel(), gy.ravel()], 1).astype(float)
    q = (invS(G) + tps_eval(model, G)).reshape(y1 - y0, x1 - x0, 2); qx, qy = np.clip(q[..., 0], 0, W - 1), np.clip(q[..., 1], 0, H - 1)
    def samp(a):
        x0_, y0_ = np.floor(qx).astype(int), np.floor(qy).astype(int); x1_, y1_ = np.minimum(x0_ + 1, W - 1), np.minimum(y0_ + 1, H - 1)
        fx, fy = qx - x0_, qy - y0_
        if a.ndim == 3: fx, fy = fx[..., None], fy[..., None]
        return a[y0_, x0_] * (1 - fx) * (1 - fy) + a[y0_, x1_] * fx * (1 - fy) + a[y1_, x0_] * (1 - fx) * fy + a[y1_, x1_] * fx * fy
    rgb = np.clip((light[y0:y1, x0:x1] * samp(hi))[..., None] * samp(chroma), 0, 255)
    a = np.asarray(Image.fromarray((np.clip(samp(soft), 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), float)[..., None] / 255
    h[y0:y1, x0:x1] = h[y0:y1, x0:x1] * (1 - a) + rgb * a
    out = Image.fromarray(np.clip(h, 0, 255).astype(np.uint8)); out.save(f"{S}/{out_name}.png"); return out
O = Image.open(f"{P}/torso-anarkali.png").convert("RGB")
A = place_collar(O, O, "swap_mandarin_on_anarkali")
B = place_collar(Image.open(f"{S}/swap3_bell_on_anarkali.png").convert("RGB"), O, "swap_bell_mandarin_on_anarkali")
w, hh = 448, 600; panel = Image.new("RGB", (w * 4, hh), "white")
for i, im in enumerate([SRC, O, A, B]): panel.paste(im.resize((w, hh)), (i * w, 0))
panel.save(f"{S}/swap_collar_panel.png")
z = Image.new("RGB", (1220, 500), "white")
for i, im in enumerate([SRC.crop((660, 260, 1140, 660)), A.crop((720, 200, 1080, 500)), B.crop((720, 200, 1080, 500))]): z.paste(im.resize((400, int(400 * im.height / im.width))), (i * 410, 0))
z.save(f"{S}/swap_collar_zoom.png")
