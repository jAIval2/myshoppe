import sys, numpy as np
from PIL import Image, ImageFilter
S, P, V = sys.argv[1:4]; sys.path.insert(0, V)
import torso as T
SRC = Image.open(f"{P}/torso-straight-sleeve-bell.png").convert("RGB")
O = Image.open(f"{P}/torso-anarkali.png").convert("RGB")                       # the host with its own sleeves: where a sleeve sits, its light
N = Image.open(f"{P}/torso-anarkali-under-sleeveless.png").convert("RGB")      # the layer the new sleeve goes on
src, o, n = (np.asarray(x, float) for x in (SRC, O, N)); H, W = n.shape[:2]
lum = lambda a: a.mean(2)
def gblur(a, sig):                                     # separable gaussian at quarter size, then back up
    f = 4; h_, w_ = a.shape; sm_ = np.asarray(Image.fromarray(a.astype(np.float32), "F").resize((w_ // f, h_ // f), Image.BILINEAR), float)
    s_ = sig / f; r_ = int(3 * s_) + 1; k = np.exp(-0.5 * (np.arange(-r_, r_ + 1) / s_) ** 2); k /= k.sum()
    sm_ = np.apply_along_axis(lambda v: np.convolve(np.pad(v, r_, mode="edge"), k, "valid"), 1, sm_)
    sm_ = np.apply_along_axis(lambda v: np.convolve(np.pad(v, r_, mode="edge"), k, "valid"), 0, sm_)
    return np.asarray(Image.fromarray(sm_.astype(np.float32), "F").resize((w_, h_), Image.BILINEAR), float)
def nblur(v, m, sig):                                   # normalised blur: v averaged over the mask m only
    a = gblur(v * m, sig); b = gblur(m.astype(float), sig)
    return a / np.maximum(b, 1e-4), b
def edge_rows(mask, side, y0, y1, k=9):                # outer edge x for rows y0..y1 (min x on the left, max x on the right)
    pts = []
    for t in np.linspace(0, 1, k):
        y = int(y0 + t * (y1 - y0)); xs = np.nonzero(mask[y])[0]
        if len(xs): pts.append(((xs.min() if side == "l" else xs.max()), y, t))
    return pts
def end_centre(mask):
    ys = np.nonzero(mask.any(1))[0]; yb = ys.max(); band = mask[yb - 12:yb + 1]; xs = np.nonzero(band.any(0))[0]
    return ((xs.min() + xs.max()) / 2, yb)
def tps_fit(P_, Q_):                                    # thin-plate spline mapping P -> Q (each n x 2)
    n_ = len(P_); r = np.linalg.norm(P_[:, None] - P_[None], axis=2); K = np.where(r > 0, r * r * np.log(r + 1e-9), 0)
    Pm = np.hstack([np.ones((n_, 1)), P_]); A = np.zeros((n_ + 3, n_ + 3)); A[:n_, :n_] = K + 1e-3 * np.eye(n_); A[:n_, n_:] = Pm; A[n_:, :n_] = Pm.T
    b = np.zeros((n_ + 3, 2)); b[:n_] = Q_; return np.linalg.solve(A, b), P_
def tps_eval(model, X):
    w, P_ = model; out = np.zeros((len(X), 2))
    for i in range(0, len(X), 200000):
        x = X[i:i + 200000]; r = np.linalg.norm(x[:, None] - P_[None], axis=2); U = np.where(r > 0, r * r * np.log(r + 1e-9), 0)
        out[i:i + 200000] = U @ w[:-3] + w[-3] + x @ w[-2:]
    return out
comp = n.copy(); report = []
for side in "lr":
    sm = np.asarray(Image.open(f"{S}/bell_mask_{side}.png")) > 0
    hm = np.asarray(Image.open(f"{S}/host_mask_{side}.png")) > 0
    lim = 690 if side == "l" else 1095                    # the armholes' x on the anarkali: the sleeve lies outside them
    hm = hm & ((np.arange(W)[None] <= lim) if side == "l" else (np.arange(W)[None] >= lim))
    for y in np.nonzero(hm.any(1))[0]:
        xs_ = np.nonzero(hm[y])[0]; hm[y, xs_.min():xs_.max() + 1] = True
    s_sh, s_ua = (T.SH_L, T.UA_L) if side == "l" else (T.SH_R, T.UA_R)
    h_sh, h_ua = ((678, 335), (683, 558)) if side == "l" else ((1100, 333), (1100, 560))
    s_end, h_end = end_centre(sm), end_centre(hm)
    # the fitted part (shoulder to elbow): outer edge at the same share of the arm's length
    se = edge_rows(sm, side, s_sh[1] + 20, s_sh[1] + 0.45 * (s_end[1] - s_sh[1]))
    he = edge_rows(hm, side, h_sh[1] + 20, h_sh[1] + 0.45 * (h_end[1] - h_sh[1]))
    hostP = [h_sh, h_ua, h_end] + [(x, y) for x, y, _ in he]
    srcP = [s_sh, s_ua, s_end] + [(x, y) for x, y, _ in se]
    hP, sP = np.array(hostP, float), np.array(srcP, float)
    # one uniform scale + rotation (the sleeve keeps its shape), least squares over all anchors (Umeyama)
    mh, ms = hP.mean(0), sP.mean(0); X, Y = sP - ms, hP - mh
    U_, D_, Vt = np.linalg.svd(Y.T @ X / len(X)); R = U_ @ Vt
    if np.linalg.det(R) < 0: R = U_ @ np.diag([1, -1]) @ Vt
    sc = D_.sum() / (X ** 2).sum(1).mean()
    fwdS = lambda p_: (sc * (R @ (p_ - ms).T)).T + mh                        # source -> host
    invS = lambda p_: ((R.T @ (p_ - mh).T) / sc).T + ms                      # host -> source
    # a local bend near the shoulder only: the anchors' residuals, held at zero below the elbow
    res = sP - invS(hP)
    ax = np.array(h_end, float) - np.array(h_sh, float); L_ = np.linalg.norm(ax); u_ = ax / L_; v_ = np.array([-u_[1], u_[0]])
    zero = [np.array(h_sh) + u_ * L_ * t + v_ * d for t in (0.6, 0.8, 1.0, 1.15) for d in (-260, -130, 0, 130, 260)]
    model = tps_fit(np.vstack([hP, zero]), np.vstack([res, np.zeros((len(zero), 2))]))
    print(side, "scale %.3f  rotation %.1f deg  anchor residuals (px, source) max %.0f" % (sc, np.degrees(np.arctan2(R[1, 0], R[0, 0])), np.abs(res).max()))
    ys, xs = np.nonzero(sm); corners = fwdS(np.array([[xs.min(), ys.min()], [xs.max(), ys.min()], [xs.min(), ys.max()], [xs.max(), ys.max()]], float))
    x0, y0 = np.floor(corners.min(0)).astype(int) - 80; x1, y1 = np.ceil(corners.max(0)).astype(int) + 80
    x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, W), min(y1, H)
    gy, gx = np.mgrid[y0:y1, x0:x1]; G = np.stack([gx.ravel(), gy.ravel()], 1).astype(float)
    q = (invS(G) + tps_eval(model, G)).reshape(y1 - y0, x1 - x0, 2)
    qx, qy = np.clip(q[..., 0], 0, W - 1), np.clip(q[..., 1], 0, H - 1)
    def samp(a):                                    # bilinear sample of a source array at (qx, qy)
        x0_, y0_ = np.floor(qx).astype(int), np.floor(qy).astype(int); x1_, y1_ = np.minimum(x0_ + 1, W - 1), np.minimum(y0_ + 1, H - 1)
        fx, fy = qx - x0_, qy - y0_
        if a.ndim == 3: fx, fy = fx[..., None], fy[..., None]
        return (a[y0_, x0_] * (1 - fx) * (1 - fy) + a[y0_, x1_] * fx * (1 - fy) + a[y1_, x0_] * (1 - fx) * fy + a[y1_, x1_] * fx * fy)
    # relight: the bell's folds (its luminance over its own broad light), times the host sleeve's broad light, in the host's colour
    Ls = lum(src); lo_s, _ = nblur(Ls, sm, 45); hi = np.clip(np.where(sm, Ls / np.maximum(lo_s, 1), 1) ** 0.7, 0.75, 1.06)   # the hard light: fold contrast softened, highlights capped
    Lh = lum(o); lo_h, cov = nblur(Lh, hm, 45); lo_h2, _ = nblur(Lh, hm, 160)
    wgt = np.clip((cov - 0.15) / 0.35, 0, 1); wgt = wgt * wgt * (3 - 2 * wgt); light = lo_h * wgt + lo_h2 * (1 - wgt)                                       # beyond the host's own sleeve: its wider average
    tint = o[hm].mean(0) / Lh[hm].mean()
    hi_w = samp(hi); m_w = samp(sm.astype(float))
    newL = light[y0:y1, x0:x1] * hi_w; rgb = np.clip(newL[..., None] * tint, 0, 255)
    a = np.asarray(Image.fromarray((np.clip(m_w, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0)), float)[..., None] / 255
    comp[y0:y1, x0:x1] = comp[y0:y1, x0:x1] * (1 - a) + rgb * a
    report.append((side, hostP[:3], srcP[:3]))
# the sleeves' shadow on the bodice: the host's own (original / sleeveless), above the elbow, outside the new sleeves
ratio = np.clip(lum(o) / np.maximum(lum(n), 1), 0.55, 1.0); ratio = gblur(ratio, 6)
newm = np.abs(comp - n).mean(2) > 1
band = np.zeros((H, W), bool); band[330:760, 680:1105] = True
apply = band & ~newm & ~(np.asarray(Image.open(f"{S}/host_mask_l.png")) > 0) & ~(np.asarray(Image.open(f"{S}/host_mask_r.png")) > 0)
comp[apply] *= ratio[apply][:, None]
out = Image.fromarray(np.clip(comp, 0, 255).astype(np.uint8)); out.save(f"{S}/swap3_bell_on_anarkali.png")
for r in report: print(r)
w, hh = 448, 600; panel = Image.new("RGB", (w * 4, hh), "white")
for i, im in enumerate([SRC, O, Image.open(f"{S}/swap2_bell_on_anarkali.png"), out]): panel.paste(im.resize((w, hh)), (i * w, 0))
panel.save(f"{S}/swap3_panel.png")
z = Image.new("RGB", (1210, 640), "white")
for i, im in enumerate([Image.open(f"{S}/swap2_bell_on_anarkali.png"), out]): z.paste(im.crop((420, 250, 1380, 1530)).resize((480, 640)), (i * 610, 0))
z.save(f"{S}/swap3_zoom.png")
