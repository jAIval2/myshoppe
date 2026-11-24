import sys, numpy as np
from PIL import Image, ImageFilter
S, P, V = sys.argv[1:4]; t = float(sys.argv[4]); k = float(sys.argv[5]); sys.path.insert(0, V); sys.path.insert(0, S)
import torso as T; from segment import grow
E = Image.open(f"{P}/torso-straight-sleeve-bell.png").convert("RGB"); W0, H0 = E.size
F = 2; e = np.asarray(E.resize((W0 // F, H0 // F)).filter(ImageFilter.GaussianBlur(1)), float); H, W = e.shape[:2]
def g2(c):
    gx = np.zeros_like(c); gy = np.zeros_like(c); gx[:, 1:-1] = (c[:, 2:] - c[:, :-2]) / 2; gy[1:-1] = (c[2:] - c[:-2]) / 2; return np.hypot(gx, gy)
g = np.hypot(g2(e.mean(2)), k * g2(e[..., 0] - e[..., 2]))
yy, xx = np.mgrid[0:H, 0:W]
def xs(pts, y):
    pts = sorted(pts, key=lambda p: p[1]); return np.interp(y, [p[1] for p in pts], [p[0] for p in pts])
ov = Image.new("RGBA", E.size, (0, 0, 0, 0)); sizes = {}
for side, seeds in {"l": [(590, 700), (520, 1150)], "r": [(1200, 700), (1290, 1150)]}.items():
    arm, sin, body, sh = (T.armhole_l, T.sleeve_in_l, T.body_l, T.SH_L) if side == "l" else (T.armhole_r, T.sleeve_in_r, T.body_r, T.SH_R)
    ua, gap = arm[-1], body[0]
    pts = list(arm) + [p for p in sin if ua[1] <= p[1] <= gap[1]] + list(body)
    bx = np.array([xs(pts, y * F) / F for y in range(H)])
    region = ((xx < bx[:, None]) if side == "l" else (xx > bx[:, None])) & (yy >= sh[1] / F - 15) & (yy < 1420 / F)
    m = grow((g < t * F) & region, [(x // F, y // F) for x, y in seeds])
    M = Image.fromarray(m.astype(np.uint8) * 255).resize((W0, H0), Image.BILINEAR).point(lambda v: 255 if v > 127 else 0)
    M = M.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5)); M.save(f"{S}/bell_mask_{side}.png")
    ov.paste((255, 0, 0, 120), (0, 0), M); sizes[side] = int((np.asarray(M) > 0).sum())
Image.alpha_composite(E.convert("RGBA"), ov).resize((448, 600)).save(f"{S}/bell_mask.png"); print(t, k, sizes)
