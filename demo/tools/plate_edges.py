"""The edges of a plate, for the review tools (StepA step 0): which parts of each zone outline are free (garment against wall,
form or mannequin arm), seam (another zone on the other side), frame (the image border) or cut (the live neck dip).

Since step 1 the type of each outline segment is the type of its edge in plate.dat (tools/platedat.py). A free-edge sample that lies inside a zone drawn later (a free edge that runs under
a sleeve for a few px) counts as hidden ("seam").
Pillow only. Used by tools/edge_crops.py and tools/fringe.py.
"""
import json, math, os, sys
from PIL import Image, ImageDraw

W, H = 1200, 1600


def load(pd):
    """The zone data of a plate (platedat.legacy) and "types": {zone: [type of the segment from vertex i to i + 1]}."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import platedat
    P = platedat.read(pd)
    _, Z = platedat.legacy(P)
    types = {}
    for zn in P["zones"]:
        t = []
        for name, d in P["zones"][zn]["outline"]:
            n = len(P["edges"][name]["points"]) - 1
            t += [P["edges"][name]["type"]] * n
        types[zn] = t[:len(Z["zones"][zn]["outline"])] if len(t) >= len(Z["zones"][zn]["outline"]) else t + [t[-1]]
    Z["types"] = types
    return Z


def masks(Z):
    out = {}
    for n, z in Z["zones"].items():
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).polygon([tuple(p) for p in z["outline"]], fill=255)
        out[n] = m.load()
    return out


def area(o):
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(o, o[1:] + o[:1])) / 2


def seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]; L2 = dx * dx + dy * dy or 1.0
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def classify(Z, step=1.0):
    """{zone: [(x, y, nx, ny, type)]}: the outline every `step` px with its outward normal and its edge type."""
    M = masks(Z)
    order = {n: z["order"] for n, z in Z["zones"].items()}
    out = {}
    for n, z in Z["zones"].items():
        o, ty = z["outline"], Z["types"][n]
        sgn = 1.0 if area(o) > 0 else -1.0                        # y down: area > 0 = clockwise on screen
        res = []
        for k in range(len(o)):
            a, b = o[k], o[(k + 1) % len(o)]
            L = math.dist(a, b)
            if L == 0: continue
            nx, ny = (b[1] - a[1]) / L * sgn, -(b[0] - a[0]) / L * sgn     # outward (y down: area > 0 = clockwise on screen)
            m = max(1, int(math.ceil(L / step)))
            for i in range(m):
                p = (a[0] + (b[0] - a[0]) * i / m, a[1] + (b[1] - a[1]) * i / m)
                t = ty[k] if k < len(ty) else ty[-1]
                if t == "free" and any(order[u] > order[n] and 0 <= p[0] < W and 0 <= p[1] < H and M[u][int(p[0]), int(p[1])] for u in M if u != n):
                    t = "seam"
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
