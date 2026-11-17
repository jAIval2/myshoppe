"""Throwaway: read the colour-coded annotate.png -> zones.json (1200x1600 space).

Corrections for known drawing errors:
- trims were drawn ON the edge -> centre lines are moved inward by width/2
- grid top across the neck is missing -> straight line between neck points
- cuff edge = orange line (drawn at the edge); the red cuff lines are ignored
- hem edge = orange+gold line
- scale: the 100 mm wall bar is not on the garment -> use shoulder width
  370 mm (standard size M) as the known length (ASSUMPTION)
"""
import json, math, sys
from PIL import Image, ImageDraw

ANN, BASE, OUT, PREVIEW = sys.argv[1:5]
im = Image.open(ANN).convert("RGB")
W, H = im.size
px = im.load()
K = 1200 / W  # 1086 -> 1200 (same factor for y: 1448 -> 1600)


def cls(r, g, b):
    if r > 150 and g < 110 and b < 110 and r - g > 80:
        return "red"
    if b > 140 and r < 110 and b - r > 60:
        return "blue"
    if r > 110 and b > 110 and g < 90:
        return "purple"
    if r > 140 and 100 < g < 185 and b < 80 and r - b > 120:
        return "hem"  # orange + gold together
    if r < 80 and g > 100 and b > 90 and g - r > 60:
        return "teal"
    return None


grid = [[None] * W for _ in range(H)]
for y in range(H):
    row = grid[y]
    for x in range(W):
        row[x] = cls(*px[x, y])


def has(c, x, y):
    return 0 <= x < W and 0 <= y < H and grid[y][x] == c


def trace(c, a, b, axis, win=10):
    """Follow colour c from landmark a to b. axis='y': step in y, find x."""
    (x0, y0), (x1, y1) = a, b
    if axis == "y":
        s0, s1, p0, p1 = y0, y1, x0, x1
    else:
        s0, s1, p0, p1 = x0, x1, y0, y1
    step = 1 if s1 >= s0 else -1
    n = abs(s1 - s0)
    slope = (p1 - p0) / n if n else 0
    pts, prev, hist = [], p0, []
    for i in range(n + 1):
        s = s0 + i * step
        pred = prev + (sum(hist[-8:]) / len(hist[-8:]) if hist else slope)
        cands = [q for q in range(round(pred) - win, round(pred) + win + 1)
                 if (has(c, q, s) if axis == "y" else has(c, s, q))]
        if cands:
            # centre of the run nearest to the prediction
            q = min(cands, key=lambda q: abs(q - pred))
            run = [r for r in cands if abs(r - q) <= 3]
            q = sum(run) / len(run)
        else:
            q = pred  # gap: continue on the prediction
        hist.append(q - prev)
        prev = q
        pts.append((q, s) if axis == "y" else (s, q))
    # force the end onto the landmark; spread the error linearly
    ex, ey = b[0] - pts[-1][0], b[1] - pts[-1][1]
    pts = [(x + ex * i / n, y + ey * i / n) for i, (x, y) in enumerate(pts)] if n else pts
    # light smoothing
    sm = []
    for i in range(len(pts)):
        seg = pts[max(0, i - 3): i + 4]
        sm.append((sum(p[0] for p in seg) / len(seg), sum(p[1] for p in seg) / len(seg)))
    sm[0], sm[-1] = pts[0], pts[-1]
    return sm


def simplify(pts, every=4):
    out = pts[::every]
    if out[-1] != pts[-1]:
        out.append(pts[-1])
    return [[round(x * K, 1), round(y * K, 1)] for x, y in out]


# landmarks (1086 space, from the dot detection)
P = {
    "neck-l": (449, 233), "neck-r": (626, 233),
    "shoulder-l": (353, 268), "shoulder-r": (726, 268),
    "underarm-l": (368, 462), "underarm-r": (713, 462),
    "cuff-out-l": (215, 875), "cuff-in-l": (327, 891),
    "cuff-in-r": (754, 891), "cuff-out-r": (860, 875),
    "slit-l": (338, 1102), "slit-r": (744, 1102),
    "hem-l": (333, 1343), "hem-r": (752, 1343), "hem-cf": (543, 1366),
}

T = {}
def straight(a, b, n=24):
    return [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]


def smooth(pts, r):
    out = []
    for i in range(len(pts)):
        seg = pts[max(0, i - r): i + r + 1]
        out.append((sum(p[0] for p in seg) / len(seg), sum(p[1] for p in seg) / len(seg)))
    out[0], out[-1] = pts[0], pts[-1]
    return out


# shoulders are short and almost straight: the trace jumped lines here
T["shoulder-l"] = straight(P["shoulder-l"], P["neck-l"])
T["shoulder-r"] = straight(P["neck-r"], P["shoulder-r"])
T["neck"] = trace("purple", P["neck-l"], P["neck-r"], "x", win=6)
T["side-l"] = trace("red", P["shoulder-l"], P["hem-l"], "y", win=6)
T["side-r"] = trace("red", P["shoulder-r"], P["hem-r"], "y", win=6)
T["hem"] = smooth(trace("hem", P["hem-l"], P["hem-r"], "x"), 25)  # remove the V at the centre dot
T["cap-l"] = trace("blue", P["shoulder-l"], P["underarm-l"], "y", win=6)
T["outer-l"] = trace("blue", P["shoulder-l"], P["cuff-out-l"], "y", win=8)
T["inner-l"] = trace("blue", P["underarm-l"], P["cuff-in-l"], "y", win=6)
T["cuff-l"] = trace("hem", P["cuff-out-l"], P["cuff-in-l"], "x")
T["cap-r"] = trace("blue", P["underarm-r"], P["shoulder-r"], "y", win=6)[::-1][::-1]
T["outer-r"] = trace("blue", P["shoulder-r"], P["cuff-out-r"], "y", win=8)
T["inner-r"] = trace("blue", P["underarm-r"], P["cuff-in-r"], "y", win=6)
T["cuff-r"] = trace("hem", P["cuff-in-r"], P["cuff-out-r"], "x")
T["slit-l"] = trace("teal", P["slit-l"], P["hem-l"], "y", win=6)
T["slit-r"] = trace("teal", P["slit-r"], P["hem-r"], "y", win=6)
# cap-r is traced underarm -> shoulder (bottom -> top); grid top must go left -> right:
# underarm-r (x 713) is left of shoulder-r (x 726), so this order is already correct.

S = {k: simplify(v) for k, v in T.items()}
L = {k: [round(x * K, 1), round(y * K, 1)] for k, (x, y) in P.items()}

shoulder_px = math.dist(L["shoulder-l"], L["shoulder-r"])
mm_per_px = 370 / shoulder_px


def rev(p):
    return p[::-1]


def offset(pts, d_px, toward):
    """Move a polyline d_px along its normal, to the side of point `toward`."""
    out = []
    for i, (x, y) in enumerate(pts):
        a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        n = math.hypot(tx, ty) or 1
        nx, ny = -ty / n, tx / n
        if (toward[0] - x) * nx + (toward[1] - y) * ny < 0:
            nx, ny = -nx, -ny
        out.append([round(x + nx * d_px, 1), round(y + ny * d_px, 1)])
    return out


inside = [600, 800]
trims = {}
for key, src, mm, toward in [
    ("neck", "neck", 12, inside),
    ("cuff-l", "cuff-l", 25, [300, 600]),
    ("cuff-r", "cuff-r", 25, [800, 600]),
    ("hem", "hem", 30, inside),
    ("slit-l", "slit-l", 8, inside),
    ("slit-r", "slit-r", 8, inside),
]:
    trims[key] = {"order": 3, "widthMm": mm,
                  "centre": offset(S[src], mm / 2 / mm_per_px, toward)}

top_front = S["shoulder-l"] + S["neck"][-1:][:0] + [L["neck-r"]] + S["shoulder-r"][1:]
data = {
    "view": "torso",
    "variant": "straight-kurta",
    "viewBox": [1200, 1600],
    "base": "base.jpg",
    "mmPerPx": round(mm_per_px, 4),
    "scaleNote": "ASSUMPTION: shoulder width = 370 mm (size M). Replace with a real measure.",
    "alignNote": "Traced from annotate.png, whose photo is a redraw of base.jpg: expect 8-23 px error.",
    "landmarks": L,
    "zones": {
        "front": {
            "order": 1,
            "grid": {
                "top": top_front,  # shoulder-l -> neck-l -> (straight) -> neck-r -> shoulder-r
                "right": S["side-r"],
                "bottom": S["hem"],
                "left": S["side-l"],
            },
            "outline": S["shoulder-l"] + S["neck"][1:] + S["shoulder-r"][1:]
            + S["side-r"][1:] + rev(S["hem"])[1:] + rev(S["side-l"])[1:],
        },
        "sleeve-l": {
            "order": 2,
            "grid": {"top": S["cap-l"], "left": S["outer-l"], "right": S["inner-l"], "bottom": S["cuff-l"]},
            "outline": S["cap-l"] + S["inner-l"][1:] + rev(S["cuff-l"])[1:] + rev(S["outer-l"])[1:],
        },
        "sleeve-r": {
            "order": 2,
            "grid": {"top": S["cap-r"], "left": S["inner-r"], "right": S["outer-r"], "bottom": S["cuff-r"]},
            "outline": S["cap-r"] + S["outer-r"][1:] + rev(S["cuff-r"])[1:] + rev(S["inner-r"])[1:],
        },
    },
    "trims": trims,
}
with open(OUT, "w") as f:
    json.dump(data, f, indent=1)

# preview on base.jpg
base = Image.open(BASE).convert("RGB")
d = ImageDraw.Draw(base)
col = {"front": (229, 57, 53), "sleeve-l": (30, 99, 233), "sleeve-r": (30, 99, 233)}
for z, v in data["zones"].items():
    for e in v["grid"].values():
        d.line([tuple(p) for p in e], fill=col[z], width=3)
tc = {"neck": (142, 36, 170), "cuff-l": (251, 140, 0), "cuff-r": (251, 140, 0),
      "hem": (199, 145, 0), "slit-l": (0, 137, 123), "slit-r": (0, 137, 123)}
for k, v in trims.items():
    d.line([tuple(p) for p in v["centre"]], fill=tc[k], width=3)
for x, y in L.values():
    d.ellipse((x - 5, y - 5, x + 5, y + 5), fill="black", outline="white", width=2)
base.save(PREVIEW)
print("mm/px", round(mm_per_px, 3), "| edges:", {k: len(v) for k, v in S.items()})
