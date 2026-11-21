"""The edges of a plate, for the review tools (StepA step 0): which parts of each zone outline are free (garment against wall,
form or mannequin arm), seam (another zone on the other side), frame (the image border) or cut (the live neck dip).

Step 0 reads zones.json (with the torso's tuck applied, as make_plate.py does) and classifies the outline geometrically:
  frame   the sample lies within 0.6 px of the image border
  seam    the point 2.5 px outward lies inside another zone (the other side is fabric), or the sample lies inside a zone drawn
          later (a part that runs under the sleeve)
  cut     the front's neck dip (the run below the grid top, make_plate.py neck_edge), on the neck and torso views
  free    everything else
Pillow only. Used by tools/edge_crops.py and tools/fringe.py.
"""
import json, math, os
from PIL import Image, ImageDraw

W, H = 1200, 1600


def tuck(p, t):
    """make_plate.py tuck(): push a front side point outward (the torso only)."""
    x, y = p
    if abs(x - t["cx"]) < t["centreBand"]:
        return [x, y]
    pr = t.get("profile")
    if isinstance(pr, dict): pr = pr["right" if x > t["cx"] else "left"]
    if pr and y <= pr[-1][0]:
        d = pr[0][1]
        for (ya, da), (yb, db) in zip(pr, pr[1:]):
            if ya <= y <= yb: d = da + (db - da) * (y - ya) / (yb - ya) if yb > ya else db
        if y < pr[0][0]: d = 0.0
    elif y < t["tipY"]: d = t["tip"]
    elif y <= t["yFull"]: d = t["reach"]
    elif y <= t["yZero"]: d = t["reach"] + (t["below"] - t["reach"]) * (y - t["yFull"]) / (t["yZero"] - t["yFull"])
    else: d = t["below"]
    return [x + (d if x > t["cx"] else -d), y]


def load(pd):
    """zones.json of a plate with the tuck applied to the front outline (the outline the maps are cut with)."""
    Z = json.load(open(os.path.join(pd, "zones.json")))
    if "tuck" in Z:
        ex = Z["tuck"].get("exempt", {})
        skip = lambda i: any(a <= i <= b for a, b in ex.get("outline", []))
        fz = Z["zones"]["front"]
        fz["outline"] = [list(p) if skip(i) else tuck(p, Z["tuck"]) for i, p in enumerate(fz["outline"])]
    return Z


def masks(Z):
    out = {}
    for n, z in Z["zones"].items():
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).polygon([tuple(p) for p in z["outline"]], fill=255)
        out[n] = m.load()
    return out


def resample_closed(o, step=1.0):
    pts = o + [o[0]]
    out = []
    for a, b in zip(pts, pts[1:]):
        n = max(1, int(math.ceil(math.dist(a, b) / step)))
        for i in range(n):
            out.append((a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n))
    return out


def area(o):
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(o, o[1:] + o[:1])) / 2


def neck_dip(Z):
    """The front outline's points below the grid top, around the centre front (make_plate.py neck_edge), or []."""
    if Z.get("view") not in ("neck", "torso") or "front" not in Z["zones"]: return []
    f = Z["zones"]["front"]; top, o = f["grid"]["top"], f["outline"]

    def topy(x):
        for a, b in zip(top, top[1:]):
            if a[0] != b[0] and min(a[0], b[0]) <= x <= max(a[0], b[0]):
                return a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0])
    cfx = Z.get("landmarks", {}).get("cf-neck", [W / 2])[0]
    below = [topy(p[0]) is not None and p[1] > topy(p[0]) + 0.5 for p in o]
    i = 0
    while i < len(o):
        if below[i]:
            j = i
            while j + 1 < len(o) and below[j + 1]: j += 1
            xs = [o[k][0] for k in range(i, j + 1)]
            if min(xs) < cfx < max(xs): return o[i - 1:j + 2]
            i = j + 1
        else: i += 1
    return []


def seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]; L2 = dx * dx + dy * dy or 1.0
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def classify(Z, step=1.0):
    """{zone: [(x, y, nx, ny, type)]}: the outline every `step` px with its outward normal and its edge type."""
    M = masks(Z)
    order = {n: z["order"] for n, z in Z["zones"].items()}
    dip = neck_dip(Z)
    out = {}
    for n, z in Z["zones"].items():
        o = z["outline"]
        sgn = 1.0 if area(o) > 0 else -1.0                        # y down: area > 0 = clockwise on screen
        S = resample_closed(o, step)
        res = []
        for i, p in enumerate(S):
            a, b = S[i - 1], S[(i + 1) % len(S)]
            tx, ty = b[0] - a[0], b[1] - a[1]; L = math.hypot(tx, ty) or 1.0
            nx, ny = -ty / L * sgn, tx / L * sgn                   # outward
            q = (p[0] + 2.5 * nx, p[1] + 2.5 * ny)
            inside = lambda m, pt: 0 <= pt[0] < W and 0 <= pt[1] < H and m[int(pt[0]), int(pt[1])]
            if p[0] < 0.6 or p[1] < 0.6 or p[0] > W - 0.6 or p[1] > H - 0.6: t = "frame"
            elif any(inside(M[m], q) for m in M if m != n) or any(order[m] > order[n] and inside(M[m], p) for m in M if m != n): t = "seam"
            elif n == "front" and dip and min(seg_dist(p, u, v) for u, v in zip(dip, dip[1:])) < 0.3: t = "cut"
            else: t = "free"
            res.append((p[0], p[1], nx, ny, t))
        out[n] = res
    return out


def runs(samples, kind="free", min_len=6):
    """Consecutive samples of one type: [[(x, y, nx, ny), ...], ...], wrapping at the closure."""
    k = [s[4] == kind for s in samples]
    if all(k): return [[s[:4] for s in samples]]
    start = next(i for i in range(len(k)) if not k[i])
    rot = samples[start:] + samples[:start]
    out, cur = [], []
    for s in rot:
        if s[4] == kind: cur.append(s[:4])
        elif cur: out.append(cur); cur = []
    if cur: out.append(cur)
    return [r for r in out if len(r) >= min_len]
