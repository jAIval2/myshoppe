import sys, numpy as np
from PIL import Image, ImageFilter
S, P = sys.argv[1:3]
O = Image.open(f"{P}/torso-anarkali.png").convert("RGB"); N = Image.open(f"{P}/torso-anarkali-under-sleeveless.png").convert("RGB")
o = np.asarray(O.filter(ImageFilter.GaussianBlur(1.5)), float); n = np.asarray(N.filter(ImageFilter.GaussianBlur(1.5)), float)
g = o[300:900, 100:400].reshape(-1, 3).mean(0) / n[300:900, 100:400].reshape(-1, 3).mean(0)   # the wall's tone change between the two
d = np.abs(o - n * g).mean(2)
H, W = d.shape
for side, (x0, x1) in {"l": (300, 900), "r": (900, 1500)}.items():
    m = np.zeros((H, W), bool); m[250:1400, x0:x1] = d[250:1400, x0:x1] > 14
    M = Image.fromarray(m.astype(np.uint8) * 255)
    M = M.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(7))
    # keep the largest blob: grow from its densest column
    a = np.asarray(M) > 0; ys, xs = np.nonzero(a); print(side, "px", a.sum(), "rows", ys.min(), ys.max(), "cols", xs.min(), xs.max())
    M.save(f"{S}/host_mask_{side}.png")
ov = Image.new("RGBA", O.size, (0, 0, 0, 0))
for s in "lr": ov.paste((0, 120, 255, 120), (0, 0), Image.open(f"{S}/host_mask_{s}.png"))
Image.alpha_composite(O.convert("RGBA"), ov).resize((448, 600)).save(f"{S}/host_mask.png")
