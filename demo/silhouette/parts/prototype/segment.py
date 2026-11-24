import sys, numpy as np
from PIL import Image, ImageFilter
def grad(im, blur=1.5):
    l = np.asarray(im.convert("L").filter(ImageFilter.GaussianBlur(blur)), float)
    gx = np.zeros_like(l); gy = np.zeros_like(l)
    gx[:, 1:-1] = (l[:, 2:] - l[:, :-2]) / 2; gy[1:-1] = (l[2:] - l[:-2]) / 2
    return np.hypot(gx, gy)
def grow(allowed, seeds, iters=3000):
    m = np.zeros(allowed.shape, bool)
    for x, y in seeds: m[y, x] = True
    M = Image.fromarray(m.astype(np.uint8) * 255); A = allowed
    for i in range(iters):
        n = (np.asarray(M.filter(ImageFilter.MaxFilter(3))) > 0) & A
        if i % 20 == 0 and (n == (np.asarray(M) > 0)).all(): break
        M = Image.fromarray(n.astype(np.uint8) * 255)
    return np.asarray(M) > 0
