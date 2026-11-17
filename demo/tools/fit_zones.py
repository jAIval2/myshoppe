"""Throwaway: fit each zone of zones.json onto base.jpg with one affine (least squares)."""
import json, sys
from PIL import Image, ImageDraw

ZJ, BASE, PREVIEW = sys.argv[1:4]
z = json.load(open(ZJ))
L = z["landmarks"]

# real positions on base.jpg (right side measured, left side mirrored about x=600)
REAL = {
    "neck-l": (512, 252), "neck-r": (688, 252),
    "shoulder-l": (402, 298), "shoulder-r": (798, 298),
    "underarm-l": (426, 505), "underarm-r": (774, 505),
    "cuff-out-l": (273, 900), "cuff-in-l": (382, 920),
    "cuff-in-r": (818, 920), "cuff-out-r": (927, 900),
    "hem-l": (397, 1450), "hem-r": (803, 1450), "hem-cf": (600, 1476),
}
GROUPS = {
    "front": ["neck-l", "neck-r", "shoulder-l", "shoulder-r", "underarm-l", "underarm-r",
              "hem-l", "hem-r", "hem-cf"],
    "sleeve-l": ["shoulder-l", "underarm-l", "cuff-out-l", "cuff-in-l"],
    "sleeve-r": ["shoulder-r", "underarm-r", "cuff-in-r", "cuff-out-r"],
}
TRIM_ZONE = {"neck": "front", "hem": "front", "slit-l": "front", "slit-r": "front",
             "cuff-l": "sleeve-l", "cuff-r": "sleeve-r"}


def solve3(A, b):
    """Gaussian elimination for a 3x3 system."""
    M = [row[:] + [v] for row, v in zip(A, b)]
    for i in range(3):
        piv = max(range(i, 3), key=lambda r: abs(M[r][i]))
        M[i], M[piv] = M[piv], M[i]
        for r in range(3):
            if r != i:
                f = M[r][i] / M[i][i]
                M[r] = [a - f * c for a, c in zip(M[r], M[i])]
    return [M[i][3] / M[i][i] for i in range(3)]


def fit(src, dst):
    """x' = a x + b y + c ; y' = d x + e y + f"""
    A = [[0.0] * 3 for _ in range(3)]
    bx, by = [0.0] * 3, [0.0] * 3
    for (x, y), (u, v) in zip(src, dst):
        r = (x, y, 1.0)
        for i in range(3):
            for j in range(3):
                A[i][j] += r[i] * r[j]
            bx[i] += r[i] * u
            by[i] += r[i] * v
    return solve3(A, bx), solve3(A, by)


def apply(T, pts):
    (a, b, c), (d, e, f) = T
    return [[round(a * x + b * y + c, 1), round(d * x + e * y + f, 1)] for x, y in pts]


T = {}
for zone, keys in GROUPS.items():
    T[zone] = fit([L[k] for k in keys], [REAL[k] for k in keys])
    res = [((p[0] - REAL[k][0]) ** 2 + (p[1] - REAL[k][1]) ** 2) ** 0.5
           for k, p in zip(keys, apply(T[zone], [L[k] for k in keys]))]
    print(f"{zone:9} residual px: max {max(res):.1f}, mean {sum(res)/len(res):.1f}")

for zone, v in z["zones"].items():
    v["grid"] = {k: apply(T[zone], e) for k, e in v["grid"].items()}
    v["outline"] = apply(T[zone], v["outline"])
for k, v in z["trims"].items():
    v["centre"] = apply(T[TRIM_ZONE[k]], v["centre"])

# shared corners: the front grid sides must start at the sleeve shoulders exactly
for k in REAL:
    L[k] = list(REAL[k])
for side in ("l", "r"):
    pass
z["landmarks"] = L
z["alignNote"] = "Traced from annotate.png, then fitted onto base.jpg with one affine per zone."
json.dump(z, open(ZJ, "w"), indent=1)

base = Image.open(BASE).convert("RGB")
d = ImageDraw.Draw(base)
col = {"front": (229, 57, 53), "sleeve-l": (30, 99, 233), "sleeve-r": (30, 99, 233)}
for name, v in z["zones"].items():
    for e in v["grid"].values():
        d.line([tuple(p) for p in e], fill=col[name], width=2)
tc = {"neck": (142, 36, 170), "cuff-l": (251, 140, 0), "cuff-r": (251, 140, 0),
      "hem": (199, 145, 0), "slit-l": (0, 137, 123), "slit-r": (0, 137, 123)}
for k, v in z["trims"].items():
    d.line([tuple(p) for p in v["centre"]], fill=tc[k], width=2)
for x, y in REAL.values():
    d.ellipse((x - 4, y - 4, x + 4, y + 4), fill="black", outline="white", width=1)
base.save(PREVIEW)
