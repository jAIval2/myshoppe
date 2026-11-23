"""A kit for views measured from a garment mask (the new looks: any source size, fit_to(path)). Pillow only, deterministic.
A view whose garment has the wall's colour on one side is read in parts (spec "parts", parts_labels): each part on its own crop,
with measured edges as barriers where the flood would leak (silhouette/views/torso_lehenga.py).

The straight kurta's views read every edge by eye on gridded crops (docs/annotate.md, Path A). These sources have a plain wall and a
white garment, so the kit reads the SILHOUETTE from the image and only the seams by eye:
  1. background(): the wall, floor, stand and form, grown from wall seed points; a pixel joins when the colour gradient there is
     under G and its colour within D of the running average of the path (that average follows a slow wall gradient, not an edge);
  2. garment(): what is left, without form-coloured and dark pixels; its largest component; small holes closed;
  3. zones(): the garment cut into zones by the measured seams (polylines, drawn as barriers), each zone flooded from a seed point;
  4. edges(): each zone's boundary traced along the pixel edges and split into runs by what lies across it: another zone (a seam:
     ONE list, used by both), the background (a free edge: the build snaps it to the photo), the image border (a frame edge). Free
     runs are cut at measured landmarks into named edges (neck, cuffs, hem), then simplified (Douglas-Peucker).
The measured data (seeds, seams, landmarks, the frame and trim specifications) stay in the view's own script, as in Path A; the
build (make_plate.py) does the rest exactly as for the straight kurta: snap, trims, frames, decisions.
"""
import math
from collections import deque
from PIL import Image, ImageChops, ImageDraw, ImageFilter

SRC_W, CROP_H = 765, 1020                  # the 765 x 1024 sources: 765 x 1020 is exactly 3:4
K = 1200 / SRC_W                           # source px -> plate px


def fit_to(path):
    """Set the crop and the scale from the source's own size (a 3:4 crop of the full width): 765 x 1024 -> 765 x 1020, 1792 x 2400
    -> 1792 x 2389. Called by a view before its base(), measure() or spec()."""
    global SRC_W, CROP_H, K
    SRC_W = Image.open(path).size[0]
    CROP_H = round(SRC_W * 4 / 3)
    K = 1200 / SRC_W


def T(pts):
    return [[round(x * K, 1), round(y * K, 1)] for x, y in pts]


def base(path, patches=()):
    """The plate photo: the sparkle marks covered (each patch: (box, dx): the box filled from the same rows dx px to the side),
    the 3:4 crop, 1200 x 1600."""
    im = Image.open(path).convert("RGB")
    for (x0, y0, x1, y1), dx in patches:
        im.paste(im.crop((x0 + dx, y0, x1 + dx, y1)), (x0, y0))
    return im.crop((0, 0, SRC_W, CROP_H)).resize((1200, 1600), Image.LANCZOS)


def source(path, patches=()):
    im = Image.open(path).convert("RGB")
    for (x0, y0, x1, y1), dx in patches:
        im.paste(im.crop((x0 + dx, y0, x1 + dx, y1)), (x0, y0))
    return im.crop((0, 0, SRC_W, CROP_H))


def gradmap(im):
    b = im.filter(ImageFilter.GaussianBlur(0.7))
    out = None
    for ch in b.split():
        gx = ch.filter(ImageFilter.Kernel((3, 3), [-1, 0, 1, -2, 0, 2, -1, 0, 1], scale=4, offset=128))
        gy = ch.filter(ImageFilter.Kernel((3, 3), [-1, -2, -1, 0, 0, 0, 1, 2, 1], scale=4, offset=128))
        g = ImageChops.add(gx.point(lambda v: abs(v - 128)), gy.point(lambda v: abs(v - 128)))
        out = g if out is None else ImageChops.lighter(out, g)
    return out


def background(im, seeds, G=7, D=5.0, A=0.08, barriers=()):
    """The background grown from wall seed points (source px). barriers: polylines the fill may not cross (a leak sealed by hand)."""
    W, H = im.size
    gm = gradmap(im)
    if barriers:
        d = ImageDraw.Draw(gm)
        for line in barriers: d.line([tuple(p) for p in line], fill=255, width=3)
    g = gm.load(); raw = im.load()
    seen = bytearray(W * H); ema = {}; q = deque()
    for x, y in seeds:
        if seen[y * W + x]: continue
        seen[y * W + x] = 1; ema[(x, y)] = tuple(map(float, raw[x, y])); q.append((x, y))
    while q:
        x, y = q.popleft(); e = ema.pop((x, y))
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < W and 0 <= ny < H and not seen[ny * W + nx] and g[nx, ny] < G:
                c = raw[nx, ny]
                if max(abs(c[0] - e[0]), abs(c[1] - e[1]), abs(c[2] - e[2])) <= D:
                    seen[ny * W + nx] = 1
                    ema[(nx, ny)] = tuple(e[k] + A * (c[k] - e[k]) for k in range(3))
                    q.append((nx, ny))
    # a barrier's own pixels are never filled: where a barrier (or a seam) runs through wall it would stay "not background", a thin
    # line of garment. Two 1 px passes give its pixels that touch the background to the background: a 3 px line in the wall goes,
    # and a line beside the cloth goes up to the cloth (a seam inside the garment loses at most 2 px at its end)
    if barriers:
        bm = Image.new("L", (W, H), 0); dm = ImageDraw.Draw(bm)
        for line in barriers: dm.line([tuple(p) for p in line], fill=255, width=3)
        b = bm.load()
        grown = []
        for _ in range(2):
            grow = [(x, y) for y in range(1, H - 1) for x in range(1, W - 1)
                    if b[x, y] and not seen[y * W + x]
                    and (seen[y * W + x - 1] or seen[y * W + x + 1] or seen[(y - 1) * W + x] or seen[(y + 1) * W + x])]
            for x, y in grow: seen[y * W + x] = 1
            grown += grow
        # ... but where a seam enters the cloth, its end pixel has cloth on three sides: it stays (no notch between two zones)
        back = [(x, y) for x, y in grown
                if (not seen[y * W + x - 1]) + (not seen[y * W + x + 1]) + (not seen[(y - 1) * W + x]) + (not seen[(y + 1) * W + x]) >= 3]
        for x, y in back: seen[y * W + x] = 0
    # the 3 px ring at the image border (its filter edge blocks the fill): each ring pixel takes the state of the pixel 3 px in, so
    # the wall reaches the border and a garment that runs off the frame (a close view) still does
    for y in range(H):
        for x in range(W):
            if 3 <= x < W - 3 and 3 <= y < H - 3: continue
            xi, yi = min(max(x, 3), W - 4), min(max(y, 3), H - 4)
            seen[y * W + x] = seen[yi * W + xi]
    return Image.frombytes("L", (W, H), bytes(255 if v else 0 for v in seen))


def components(mask):
    """{label: pixel count} and the label image (list) of the 4-connected components of a 0/255 L mask."""
    W, H = mask.size; m = mask.load()
    lab = [0] * (W * H); sizes = {}; n = 0
    for y in range(H):
        for x in range(W):
            if m[x, y] and not lab[y * W + x]:
                n += 1; q = deque([(x, y)]); lab[y * W + x] = n; c = 0
                while q:
                    a, b = q.popleft(); c += 1
                    for nx, ny in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                        if 0 <= nx < W and 0 <= ny < H and m[nx, ny] and not lab[ny * W + nx]:
                            lab[ny * W + nx] = n; q.append((nx, ny))
                sizes[n] = c
    return sizes, lab


def garment(im, bg, keep=1, max_chroma=34, min_l=110, close_holes=400, exclude=()):
    """The garment: not background, not form-coloured (chroma > max_chroma) and not dark; minus the exclude polygons (an object in
    front: the mannequin arm); its `keep` largest components; holes smaller than close_holes px closed."""
    W, H = im.size; raw = im.load(); b = bg.load()
    m = Image.new("L", (W, H), 0); mp = m.load()
    for y in range(H):
        for x in range(W):
            if b[x, y]: continue
            r, g, bb = raw[x, y]
            if max(r, g, bb) - min(r, g, bb) > max_chroma or 0.299 * r + 0.587 * g + 0.114 * bb < min_l: continue
            mp[x, y] = 255
    for poly in exclude: ImageDraw.Draw(m).polygon([tuple(p) for p in poly], fill=0)
    m = m.filter(ImageFilter.MedianFilter(3))
    sizes, lab = components(m)
    big = sorted(sizes, key=lambda k: -sizes[k])[:keep]
    out = Image.new("L", (W, H), 0); op = out.load()
    for i, v in enumerate(lab):
        if v in big: op[i % W, i // W] = 255
    inv = out.point(lambda v: 0 if v else 255)                       # holes: components of the inverse not touching the border
    s2, lab2 = components(inv)
    touch = {lab2[x] for x in range(W)} | {lab2[(H - 1) * W + x] for x in range(W)} | {lab2[y * W] for y in range(H)} | {lab2[y * W + W - 1] for y in range(H)}
    for i, v in enumerate(lab2):
        if v and v not in touch and s2[v] < close_holes: op[i % W, i // W] = 255
    return out


def zones(gmask, seeds, seams, strict=True, only_seams=False):
    """Label image {pixel index: zone name} of the garment cut by the seams (polylines; extended past the garment by the caller),
    each zone flooded from its seed; the seam pixels then join their nearest zone (so the zones touch along the seam), and so do
    stray garment px, unless only_seams (a part of a split view: the garment beyond its seams is another part's)."""
    W, H = gmask.size
    cut = gmask.copy(); d = ImageDraw.Draw(cut)
    for line in seams: d.line([tuple(p) for p in line], fill=0, width=2)
    c, g = cut.load(), gmask.load()
    lab = [None] * (W * H); q = deque()
    for name, (x, y) in seeds.items():
        if not c[x, y]: raise ValueError(f"seed of {name} at {(x, y)} is not on the garment (or on a seam)")
        if lab[y * W + x]:
            if strict: raise ValueError(f"seed of {name}: the zone of {lab[y * W + x]} (a seam does not close)")
            print(f"seed of {name}: in the zone of {lab[y * W + x]} (a seam does not close)"); continue
        lab[y * W + x] = name; q.append((x, y))
        while q:
            a, b = q.popleft()
            for nx, ny in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                if 0 <= nx < W and 0 <= ny < H and c[nx, ny] and lab[ny * W + nx] is None:
                    lab[ny * W + nx] = name; q.append((nx, ny))
    for name in seeds:                                               # a zone flooded into another one's seed: a leaking seam
        pass
    front = deque(i for i, v in enumerate(lab) if v is not None)
    while front:                                                     # the seam pixels (and stray garment px) join the nearest zone
        i = front.popleft(); x, y = i % W, i // W
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < W and 0 <= ny < H and g[nx, ny] and lab[ny * W + nx] is None and not (only_seams and c[nx, ny]):
                lab[ny * W + nx] = lab[i]; front.append(ny * W + nx)
    return lab


def _loops(lab, W, H, name):
    """The boundary loops of one zone along the pixel edges, each a list of (corner, across) with across = the neighbour's zone
    name, None (background) or "#" (the image border). The pixel square of (x, y) is [x, x + 1] x [y, y + 1]."""
    out_edges = {}
    def at(x, y):
        if x < 0 or y < 0 or x >= W or y >= H: return "#"
        return lab[y * W + x]
    for i, v in enumerate(lab):
        if v != name: continue
        x, y = i % W, i // W
        for (nx, ny), a, b in (((x, y - 1), (x, y), (x + 1, y)), ((x + 1, y), (x + 1, y), (x + 1, y + 1)),
                               ((x, y + 1), (x + 1, y + 1), (x, y + 1)), ((x - 1, y), (x, y + 1), (x, y))):
            o = at(nx, ny)
            if o != name: out_edges.setdefault(a, []).append((b, o))
    loops = []
    while out_edges:
        start = next(iter(out_edges)); cur = start; loop = []; prev_dir = None
        while True:
            opts = out_edges[cur]
            if len(opts) > 1 and prev_dir is not None:              # a pinch: turn right (keeps the loops apart)
                def turn(o):
                    dx, dy = o[0][0] - cur[0], o[0][1] - cur[1]
                    return (prev_dir[0] * dy - prev_dir[1] * dx)
                opts.sort(key=turn, reverse=True)
            nxt, o = opts.pop(0)
            if not opts: del out_edges[cur]
            loop.append((cur, o)); prev_dir = (nxt[0] - cur[0], nxt[1] - cur[1]); cur = nxt
            if cur == start: break
        loops.append(loop)
    return loops


def _area(pts):
    return 0.5 * sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))


def dp(pts, eps):
    """Douglas-Peucker, the ends kept."""
    if len(pts) < 3: return list(pts)
    a, b = pts[0], pts[-1]; dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1e-9
    best, k = -1.0, 0
    for i in range(1, len(pts) - 1):
        d = abs((pts[i][0] - a[0]) * dy - (pts[i][1] - a[1]) * dx) / L if L > 1e-9 else math.dist(pts[i], a)
        if d > best: best, k = d, i
    if best <= eps: return [a, b]
    return dp(pts[:k + 1], eps)[:-1] + dp(pts[k:], eps)


def smooth(pts, k=3):
    """A traced run along the pixel edges is a staircase of 1 px steps. Each inner corner becomes the mean of its neighbours within k
    corners on both sides (fewer near the ends; the ends stay). Where the build's snap keeps these points (a weak span, a measured
    line), a staircase gives the soft free edge a speckled rim (2026-11-24)."""
    n = len(pts)
    if n < 5: return list(pts)
    out = [pts[0]]
    for i in range(1, n - 1):
        w = min(k, i, n - 1 - i)
        seg = pts[i - w:i + w + 1]
        out.append((sum(p[0] for p in seg) / len(seg), sum(p[1] for p in seg) / len(seg)))
    return out + [pts[-1]]


def edges(lab, W, H, order, cuts, eps=0.9, holes_ok=False, smooth_k=0):
    """Typed edges and outline chains (plate px) of the zones in `order`.
    cuts: {zone: [(edge name, source point a, source point b), ...]}: a free run is cut at the boundary corners nearest a and b, and
    the part from a to b (along the outline's direction, whichever way round is shorter) gets the name. Returns (edges, outlines)."""
    E, O, seam_of = {}, {}, {}
    for zn in order:
        loops = _loops(lab, W, H, zn)
        if not loops: raise ValueError(f"zone {zn}: no pixels")
        loops.sort(key=lambda L: -abs(_area([p for p, _ in L])))
        if len(loops) > 1 and not holes_ok:
            raise ValueError(f"zone {zn}: {len(loops) - 1} hole(s) inside it (a gap enclosed by one zone): cut it with a seam or exclude it")
        loop = loops[0]
        # runs: maximal stretches with one 'across'
        n = len(loop)
        k0 = next((i for i in range(n) if loop[i][1] != loop[i - 1][1]), 0)
        loop = loop[k0:] + loop[:k0]
        runs, cur = [], [loop[0]]
        for item in loop[1:]:
            if item[1] == cur[-1][1]: cur.append(item)
            else: runs.append(cur); cur = [item]
        runs.append(cur)
        # each run's points: its corners + the start of the next run (the junction)
        chain = []
        corner_runs = []
        for j, r in enumerate(runs):
            nxt = runs[(j + 1) % len(runs)][0][0]
            pts = [p for p, _ in r] + [nxt]
            corner_runs.append((r[0][1], pts))
        # named cuts on free runs
        named = []
        for across, pts in corner_runs:
            if across is not None:
                named.append((across, None, pts)); continue
            pieces = [(None, pts)]
            for nm, a, b in cuts.get(zn, []):
                for pi, (pn, pp) in enumerate(pieces):
                    if pn is not None: continue
                    ia = min(range(len(pp)), key=lambda i: math.dist(pp[i], a)); ib = min(range(len(pp)), key=lambda i: math.dist(pp[i], b))
                    if math.dist(pp[ia], a) > 25 or math.dist(pp[ib], b) > 25: continue
                    lo, hi = min(ia, ib), max(ia, ib)
                    if hi - lo < 2: continue
                    rep = ([(None, pp[:lo + 1])] if lo > 0 else []) + [(nm, pp[lo:hi + 1])] + ([(None, pp[hi:])] if hi < len(pp) - 1 else [])
                    pieces[pi:pi + 1] = rep
                    break
            for pn, pp in pieces: named.append((None, pn, pp))
        free_k = 0
        for across, nm, pts in named:
            if across == "#":
                en = f"{zn}-frame-{free_k}"; free_k += 1
                E[en] = {"type": "frame", "points": T(dp(pts, eps))}
                chain.append([en, 1])
            elif across is None:
                en = nm or f"{zn}-free-{free_k}"; free_k += 0 if nm else 1
                if en in E: raise ValueError(f"edge {en} twice")
                E[en] = {"type": "free", "points": T(dp(smooth(pts, smooth_k) if smooth_k else pts, eps))}
                chain.append([en, 1])
            else:
                key = tuple(sorted([zn, across])) + (frozenset([pts[0], pts[-1]]),)
                if key in seam_of:
                    en, stored = seam_of[key]
                    chain.append([en, 1 if stored[0] == pts[0] else -1])
                else:
                    en = f"seam-{zn}-{across}" + (f"-{len(seam_of)}" if f"seam-{zn}-{across}" in E else "")
                    E[en] = {"type": "seam", "zones": [zn, across], "points": T(dp(smooth(pts, smooth_k) if smooth_k else pts, eps))}
                    seam_of[key] = (en, pts)
                    chain.append([en, 1])
        O[zn] = chain
    return E, O


def overlay(im, lab, colours, out):
    """A quick check image (source px): each zone tinted."""
    W, H = im.size
    ov = im.copy(); px = ov.load()
    for i, v in enumerate(lab):
        if v in colours:
            x, y = i % W, i // W; c = colours[v]; r, g, b = px[x, y]
            px[x, y] = ((r + c[0]) // 2, (g + c[1]) // 2, (b + c[2]) // 2)
    ov.save(out)


def border_seeds(im, step=8, min_chroma=20):
    """Wall seed points 3 px inside the border (the image border itself carries a filter edge), where the colour is wall-like."""
    W, H = im.size; raw = im.load(); out = []
    for x in range(3, W - 3, step): out += [(x, 3), (x, H - 4)]
    for y in range(3, H - 3, step): out += [(3, y), (W - 4, y)]
    return [(x, y) for x, y in out if max(raw[x, y]) - min(raw[x, y]) > min_chroma]


def parts_labels(im, spec):
    """The split measurement (spec "parts"): each part has a box (source px) and the zones it holds. Each part is read on its own
    crop: the wall flood starts on the box's border (wall-coloured points only) and may not leave the box; the garment is what is
    left in the box; the part's zones are flooded from their seeds inside it, cut by the seams. Its own thresholds ("G", "D") and
    its own barriers ("barriers": measured edges where the garment has the wall's colour, a few px outside the garment). The
    parts are merged in the order of the spec: a pixel already labelled by an earlier part keeps its label."""
    W, H = im.size
    lab = [None] * (W * H)
    for name, part in spec["parts"].items():
        x0, y0, x1, y1 = part["box"]
        c = im.crop((x0, y0, x1, y1)); cw, ch = c.size
        tr = lambda pts: [(x - x0, y - y0) for x, y in pts]
        box = [(0, 0), (cw - 1, 0), (cw - 1, ch - 1), (0, ch - 1), (0, 0)]
        barriers = ([box] + [tr(s) for s in spec.get("seams", {}).values()] + [tr(b) for b in spec.get("bg_barriers", ())]
                    + [tr(b) for b in part.get("barriers", ())])
        inside = lambda p: x0 <= p[0] < x1 and y0 <= p[1] < y1
        sides = part.get("seed_sides", "ltrb")       # only the box sides that lie on wall: a side across the garment would seed it
        seeds = [(x, y) for x, y in border_seeds(c)
                 if ("l" in sides and x == 3) or ("r" in sides and x == cw - 4) or ("t" in sides and y == 3) or ("b" in sides and y == ch - 4)]
        seeds += [(x - x0, y - y0) for x, y in spec.get("extra_seeds", ()) if inside((x, y))]
        bgp = background(c, seeds, G=part.get("G", 7), D=part.get("D", 5.0), barriers=barriers)
        gmp = garment(c, bgp, max_chroma=255, min_l=spec.get("min_l", 70),
                      exclude=[tr(p) for p in spec.get("exclude", ())], close_holes=spec.get("close_holes", 400))
        zs = {z: (spec["zones"][z]["seed"][0] - x0, spec["zones"][z]["seed"][1] - y0) for z in part["zones"]}
        lc = zones(gmp, zs, [tr(s) for s in spec.get("seams", {}).values()], only_seams=True)
        for i, v in enumerate(lc):
            if v is None: continue
            j = (i // cw + y0) * W + (i % cw + x0)
            if lab[j] is None: lab[j] = v
    gm = Image.new("L", (W, H), 0); g = gm.load()
    for i, v in enumerate(lab):
        if v is not None: g[i % W, i // W] = 255
    return lab, gm, None


def measure(spec):
    """The plate data of a view from its spec (all points in SOURCE px):
      path, patches                the source and its sparkle patches
      seeds | border, extra_seeds  the background's seed points (border: seed along the image border); extra: gaps, the form
      exclude                      polygons that are not garment (the form above the neckline, the floor, an object in front)
      seams                        {name: polyline}: the cuts between zones (extended past the garment)
      zones                        {zone: {"seed": (x, y), "order": n, "frame": {...}}}
      cuts                         {zone: [(edge name, a, b)]}: free runs named (neck, cuffs, hem)
      landmarks                    {name: (x, y)}
      scale                        (landmark a, landmark b, mm, note)
      trims, settings, occluders (source polygons), view, variant, source_note
      measured                     polylines measured on the source where the garment has the background's colour: the build's snap
                                   keeps the edge there (P["measured"])
      smooth_k, dp_eps             the traced runs smoothed over k corners (0: as traced), then simplified (Douglas-Peucker, eps px)
    Returns (P, extras) with P as the straight kurta's views return it (plate px)."""
    im = source(spec["path"], spec.get("patches", ()))
    W, H = im.size
    if spec.get("parts"):
        lab, gm, bg = parts_labels(im, spec)
    else:
        seeds = (border_seeds(im) if spec.get("border", True) else []) + [tuple(p) for p in spec.get("extra_seeds", ())]
        bg = background(im, seeds, barriers=spec.get("bg_barriers", ()))
        gm = garment(im, bg, max_chroma=255, min_l=spec.get("min_l", 70), exclude=spec.get("exclude", ()),
                     close_holes=spec.get("close_holes", 400))
        lab = zones(gm, {z: tuple(v["seed"]) for z, v in spec["zones"].items()}, list(spec.get("seams", {}).values()))
    order = sorted(spec["zones"], key=lambda z: (spec["zones"][z]["order"], z))
    E, O = edges(lab, W, H, order, spec.get("cuts", {}), eps=spec.get("dp_eps", 0.9), smooth_k=spec.get("smooth_k", 0))
    L = {k: [round(x * K, 1), round(y * K, 1)] for k, (x, y) in spec["landmarks"].items()}
    a, b, mm, note = spec["scale"]
    mm_per_px = mm / math.dist(L[a], L[b])
    Z = {z: {"order": v["order"], "frame": v["frame"], "outline": O[z]} for z, v in spec["zones"].items()}
    P = {"view": spec["view"], "variant": spec["variant"], "viewBox": [1200, 1600], "mmPerPx": round(mm_per_px, 4),
         "scaleNote": note, "source": spec["source_note"], "landmarks": L, "edges": E, "zones": Z, "stitches": {},
         "settings": spec.get("settings", {}), "trims": spec.get("trims", {})}
    if spec.get("occluders"): P["occluders"] = [T(p) for p in spec["occluders"]]
    if spec.get("measured"): P["measured"] = [T(p) for p in spec["measured"]]      # lines the build's snap keeps (snap_edges.py)
    return P, {"im": im, "bg": bg, "garment": gm, "labels": lab, "W": W, "H": H}


def check(P, extras=None, out=None):
    """The automatic checks of annotate.md 9.1 that apply: the plate validates, outlines simple, the zones' pixel counts; a tinted
    check image of the zones (source px) when out is given."""
    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pipeline"))
    import platedat
    def cross(p1, p2, p3, p4):
        def o(a, b, c): return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        return o(p1, p2, p3) * o(p1, p2, p4) < 0 and o(p3, p4, p1) * o(p3, p4, p2) < 0
    for zn in P["zones"]:
        o = platedat.outline(P, zn); n = len(o)
        X = sum(1 for i in range(n) for j in range(i + 2, n) if not (i == 0 and j == n - 1) and cross(o[i], o[(i + 1) % n], o[j], o[(j + 1) % n]))
        print(f"outline {zn:10} {n:4} points, {X} self-crossings, area {abs(_area(o)):9.0f} px2")
        assert X == 0, f"{zn}: self-crossing outline"
    for tn, t in P.get("trims", {}).items():
        assert t["edge"] in P["edges"], f"trim {tn}: edge {t['edge']} not cut (a cut point too far from the outline?)"
    print("edges:", ", ".join(f"{n}({e['type'][0]})" for n, e in P["edges"].items()))
    if extras and out:
        cols = [(230, 60, 60), (40, 110, 220), (40, 170, 90), (200, 140, 30), (150, 60, 190), (30, 170, 170), (220, 90, 160)]
        overlay(extras["im"], extras["labels"], {z: cols[i % len(cols)] for i, z in enumerate(P["zones"])}, out)


def refine_x(path, pts, win=8, keep=(), patches=()):
    """Each measured point moved along its row to the strongest brightness step within +-win px (the garment / form edge of a
    neckline, read by eye to +-4 px). Points listed in keep (ends, corners) stay."""
    im = source(path, patches).convert("L").filter(ImageFilter.GaussianBlur(0.8)); px = im.load(); W, H = im.size
    out = []
    for p in pts:
        x, y = p
        if tuple(p) in {tuple(k) for k in keep} or not (win + 1 <= x < W - win - 1): out.append(p); continue
        best = max(range(x - win, x + win + 1), key=lambda xx: abs(px[xx + 1, y] - px[xx - 1, y]))
        out.append((best, y))
    return out
