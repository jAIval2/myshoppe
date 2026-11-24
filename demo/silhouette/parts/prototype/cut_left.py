import sys, numpy as np
from PIL import Image, ImageFilter
S, P, V = sys.argv[1:4]; sys.path.insert(0, V)
import torso as T
E = Image.open(f"{P}/torso-straight-sleeve-bell.png").convert("RGB"); W, H = E.size
e = np.asarray(E.filter(ImageFilter.GaussianBlur(2)), float); L = e.mean(2); RB = e[..., 0] - e[..., 2]
R = np.asarray(Image.open(f"{S}/bell_mask_r.png")) > 0
ys = np.where(R.any(1))[0]; y_end = ys.max(); print("right bell: rows", ys.min(), "-", y_end)
def xs(pts, y):
    pts = sorted(pts, key=lambda p: p[1]); return np.interp(y, [p[1] for p in pts], [p[0] for p in pts])
ua, gap = T.armhole_l[-1], T.body_l[0]
pts = list(T.armhole_l) + [p for p in T.sleeve_in_l if ua[1] <= p[1] <= gap[1]] + list(T.body_l)
M = np.zeros((H, W), bool); outer = []
for y in range(int(T.SH_L[1]) - 20, y_end + 1):
    bx = int(xs(pts, y)); wl, wrb = np.median(L[y, 250:300]), np.median(RB[y, 250:300])
    d = (np.abs(L[y, 300:bx] - wl) > 18) | (np.abs(RB[y, 300:bx] - wrb) > 7)
    run = np.convolve(d.astype(int), np.ones(4, int), "valid") == 4
    if run.any(): x0 = 300 + int(np.argmax(run)); M[y, x0:bx] = True; outer.append((x0, y))
Mi = Image.fromarray(M.astype(np.uint8) * 255).filter(ImageFilter.MedianFilter(5)); Mi.save(f"{S}/bell_mask_l.png")
ov = Image.new("RGBA", E.size, (0, 0, 0, 0))
for f in ("l", "r"): ov.paste((255, 0, 0, 120), (0, 0), Image.open(f"{S}/bell_mask_{f}.png"))
Image.alpha_composite(E.convert("RGBA"), ov).resize((448, 600)).save(f"{S}/bell_mask.png")
Image.alpha_composite(E.convert("RGBA"), ov).crop((250, 350, 950, 1450)).resize((350, 550)).save(f"{S}/bell_mask_lzoom.png")
