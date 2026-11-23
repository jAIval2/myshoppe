"""plate.dat version 4 (BSP4; StepC step 2): every number of one view in one small binary file (StepA step 1). Pillow is not needed.
Version 3 (StepB) = version 2 + the garment header, each zone's piece, the zone and trim tables (ids, groups, roles), each trim's lace
band and join. Version 4 = version 3 + the trim fields' packing (trimPack), each trim's field slot, its ends and its corners; the
slits' field is the "open" field. Only version 4 is read: rebuild an older plate from its source (silhouette/plate.py build <view>).

usage: python3 silhouette/pipeline/platedat.py --dump <plate-dir | plate.dat>     the file as text, in a stable order (git diff uses it: diff=dat)
       python3 silhouette/pipeline/platedat.py --check <plate-dir> ...           read and validate
As a module: read(path) -> P, write(path, P) -> bytes, encode(P) -> bytes, validate(P) -> [problems], outline(P, zone) -> points,
dump(P) -> text, legacy(P) -> (plate, zones): the two objects the page and the old tools know (the plate header and the zone data).

Format (little endian):
  "BSP4"     4 bytes
  u16 version (4), u16 unit (coordinate unit in 1/1000 px: 100 = 0.1 px), u32 hlen
  header     UTF-8 JSON, hlen bytes (padded with spaces to a multiple of 2)
  curves     int16 (dx, dy) per point, every curve one after the other, the first point from (0, 0); "curves" in the header lists the
             number of points of each curve, in the same order.
In the header every polyline (a list of 2 or more [x, y] pairs) is replaced by {"@c": index}; identical curves are stored once.
A curve's points are rounded to the unit when written.

The header P (what a plate is; StepA.md section 1, items 7-8):
  v, view, variant (the look), viewBox, mmPerPx, scaleNote, source
  garment    {look, version, hash}: the garment record the plate was built against (silhouette/pipeline/garment.py)
  trimPack   {rangeCm, mainSOffCm, openSOffCm: [slot 0, slot 1], tOffMm}: the page's 16-bit packing of the trim fields (StepC step 2)
  uvPack     {rangeCm, offsetCm: [u, v]}: the 16-bit packing of the fabric (u, v) on the page, the same for every plate (StepB step 1);
             the page decodes (u, v) = stored - offsetCm
  edges      {name: {type: free | seam | frame | cut, points, zones: [a, b] (a seam)}}.  A seam is ONE list used by two zones.
             A lower zone's run that lies hidden under a later zone (the sleeve view's body under the sleeve and the cuff) is a seam with "under": <the later zone>, used by that one lower zone.
             free = a visible contour (snapped to the photo, StepA step 3); frame = the image border; cut = the live neck dip.
  zones      {name: {id, order, piece, outline: [[edge, +1 | -1], ...], frame}}: id by draw order, then name, from 1 (at most 15);
             piece = the garment record's piece the zone shows (views.<view>.zones); the frame (silhouette/pipeline/plateframe.py) = axis, L, s0, vMm,
             thetaDeg, half, sag, and its specification (axisFrom, anchor, sagEdge, skipTop, axisDegree)
             The outline is the chain of its edges; a join point shared by two consecutive edges is written once.
  trims      {name: {id, order, type (edging | insertion), group, field, live, bandInMm, bandOutMm, join, edge, from, to, anchor, cut,
             line, side, zone}}: a lace hangs on its edge; id as the zones'; group = the page's button (neck | cuffs | hem | slits);
             field = main | open (the slits' own field, 2 slots: slot); ends = {from, to}: runout | cut | piece; corners = [{at,
             deg, side}] (the line turns over 35 deg within 5 mm); live = the page lays it on the live neckline (its edge is the cut edge);
             bandInMm / bandOutMm = the depth the trim field covers inward and (an edging) outward; join = {kind: mitre | butt | overlap
             | open, with: [trims]};
             line = the edge between the anchors (derived in the build), side = the sign of the inward normal, zone = the edge's zone;
             anchor = where the motif sits (cf: the frame's u = 0; from / to: an end); cut = the real (square) ends (StepA extension)
  stitches   {name: points};  occluders: [chain of edges [[edge, +-1], ...] (or points)];  landmarks {name: [x, y]};  invariants {openings}
  settings   view settings: thetaDeg, shadeSmoothMm, shadeSmoothEps, shadeSpace
  decisions  what silhouette/pipeline/make_plate.py takes from the image: shadeMedian, shadeSmoothPx, shadeEncoding, the neck block, each trim's
             cloth length (lengthCm), each zone's size in cm
"""
import json, math, os, struct, sys

MAGIC, VERSION, UNIT = b"BSP4", 4, 100
GROUPS, JOINS, FIELDS = ("neck", "cuffs", "hem", "slits"), ("mitre", "butt", "overlap", "open"), ("main", "open")
ENDS = ("runout", "cut", "piece")
MAX_IDS = 15
EDGE_TYPES = ("free", "seam", "frame", "cut")


def is_curve(v):
    return (isinstance(v, list) and len(v) >= 2
            and all(isinstance(p, (list, tuple)) and len(p) == 2 and all(isinstance(c, (int, float)) and not isinstance(c, bool) for c in p) for p in v))


def q(v):
    return int(round(v * 1000 / UNIT))


def encode(P):
    curves, index = [], {}

    def walk(v):
        if is_curve(v):
            key = tuple((q(x), q(y)) for x, y in v)
            if key not in index:
                index[key] = len(curves); curves.append(key)
            return {"@c": index[key]}
        if isinstance(v, dict): return {k: walk(x) for k, x in v.items()}
        if isinstance(v, list): return [walk(x) for x in v]
        return v
    head = walk(P)
    head["curves"] = [len(c) for c in curves]
    hj = json.dumps(head, separators=(",", ":")).encode("utf-8")
    hj += b" " * (len(hj) % 2)
    body = bytearray()
    for c in curves:
        px = py = 0
        for x, y in c:
            dx, dy = x - px, y - py
            if not (-32768 <= dx <= 32767 and -32768 <= dy <= 32767): raise ValueError("a curve step is larger than int16")
            body += struct.pack("<hh", dx, dy); px, py = x, y
    return MAGIC + struct.pack("<HHI", VERSION, UNIT, len(hj)) + hj + bytes(body)


def decode(data):
    if data[:4] != MAGIC: raise ValueError(f"plate.dat: {data[:4]!r}, not BSP4 (rebuild the plate from its source)")
    version, unit, hlen = struct.unpack("<HHI", data[4:12])
    if version != VERSION: raise ValueError(f"plate.dat: version {version}")
    head = json.loads(data[12:12 + hlen].decode("utf-8"))
    off, curves = 12 + hlen, []
    for n in head.pop("curves"):
        x = y = 0; pts = []
        for i in range(n):
            dx, dy = struct.unpack_from("<hh", data, off); off += 4
            x += dx; y += dy
            pts.append([x * unit / 1000, y * unit / 1000])
        curves.append(pts)

    def walk(v):
        if isinstance(v, dict):
            if set(v) == {"@c"}: return [list(p) for p in curves[v["@c"]]]
            return {k: walk(x) for k, x in v.items()}
        if isinstance(v, list): return [walk(x) for x in v]
        return v
    return walk(head)


def read(path):
    if os.path.isdir(path): path = os.path.join(path, "plate.dat")
    return decode(open(path, "rb").read())


def write(path, P):
    if os.path.isdir(path): path = os.path.join(path, "plate.dat")
    data = encode(P)
    open(path, "wb").write(data)
    return data


def outline(P, zone):
    """The outline of a zone: its edges one after the other, a join point written once."""
    out = []
    for name, d in P["zones"][zone]["outline"]:
        pts = P["edges"][name]["points"]
        pts = pts if d > 0 else pts[::-1]
        out += pts[1:] if out and out[-1] == pts[0] else pts
    if len(out) > 1 and out[0] == out[-1]: out.pop()
    return [list(p) for p in out]


def validate(P):
    bad = []
    for k in ("view", "viewBox", "mmPerPx", "edges", "zones", "garment", "uvPack", "trimPack"):
        if k not in P: bad.append(f"no {k}")
    g = P.get("garment", {})
    if not (g.get("look") and isinstance(g.get("version"), int) and len(str(g.get("hash", ""))) == 16): bad.append(f"garment header {g}")
    for kind, items in (("zone", P.get("zones", {})), ("trim", P.get("trims", {}))):
        ids = sorted(x.get("id", 0) for x in items.values())
        if ids != list(range(1, len(ids) + 1)) or len(ids) > MAX_IDS: bad.append(f"{kind} ids {ids} (1..n, at most {MAX_IDS})")
    for zn, z in P.get("zones", {}).items():
        if not z.get("piece"): bad.append(f"zone {zn}: no piece")
    E = P.get("edges", {})
    refs = {n: set() for n in E}
    for zn, z in P.get("zones", {}).items():
        ch = z.get("outline", [])
        if not ch: bad.append(f"zone {zn}: no outline"); continue
        for name, d in ch:
            if name not in E: bad.append(f"zone {zn}: unknown edge {name}"); continue
            if d not in (1, -1): bad.append(f"zone {zn}: direction {d} of {name}")
            refs[name].add(zn)
        pts = [(n, E[n]["points"] if d > 0 else E[n]["points"][::-1]) for n, d in ch if n in E]
        for (a, pa), (b, pb) in zip(pts, pts[1:] + pts[:1]):            # consecutive edges meet (closed chain)
            if math.dist(pa[-1], pb[0]) > 1e-6 and not (len(pts) == 1):
                bad.append(f"zone {zn}: {a} does not end where {b} starts ({pa[-1]} / {pb[0]})")
    for n, e in E.items():
        t = e.get("type")
        if t not in EDGE_TYPES: bad.append(f"edge {n}: type {t}")
        if len(e.get("points", [])) < 2: bad.append(f"edge {n}: fewer than 2 points")
        if not refs[n]: bad.append(f"edge {n}: used by no zone")
        if t == "seam":
            zs = set(e.get("zones", []))
            if "under" in e:                                                 # a lower zone's run hidden under a later zone
                up, zo = e["under"], P.get("zones", {})
                if len(refs[n]) != 1 or up not in zo or any(zo[up]["order"] <= zo[r]["order"] for r in refs[n]):
                    bad.append(f"seam {n}: under {up}, used by {sorted(refs[n])} (one lower zone)")
            elif refs[n] != zs or len(zs) != 2:
                bad.append(f"seam {n}: used by {sorted(refs[n])}, declared {sorted(zs)} (must be exactly two zones)")
        elif len(refs[n]) != 1:
            bad.append(f"edge {n} ({t}): used by {sorted(refs[n])} (only a seam is shared)")
        if t == "frame":
            W, H = P["viewBox"]
            for x, y in e["points"]:
                if not (min(x, W - x) < 0.05 or min(y, H - y) < 0.05): bad.append(f"frame edge {n}: point {x, y} not on the border"); break
    for tn, t in P.get("trims", {}).items():
        for k in ("line", "side", "zone"):
            if k not in t: bad.append(f"trim {tn}: no {k}")
        if t.get("zone") and t["zone"] not in P.get("zones", {}): bad.append(f"trim {tn}: unknown zone {t['zone']}")
        if t.get("type") not in ("edging", "insertion"): bad.append(f"trim {tn}: type {t.get('type')}")
        if t.get("edge") and t["edge"] not in E: bad.append(f"trim {tn}: unknown edge {t['edge']}")
        if t.get("group") not in GROUPS: bad.append(f"trim {tn}: group {t.get('group')}")
        if t.get("field") not in FIELDS: bad.append(f"trim {tn}: field {t.get('field')}")
        if not isinstance(t.get("live"), bool): bad.append(f"trim {tn}: live {t.get('live')}")
        if not (isinstance(t.get("bandInMm"), (int, float)) and t["bandInMm"] > 0): bad.append(f"trim {tn}: bandInMm {t.get('bandInMm')}")
        if not (isinstance(t.get("bandOutMm"), (int, float)) and t["bandOutMm"] >= 0): bad.append(f"trim {tn}: bandOutMm {t.get('bandOutMm')}")
        if t.get("field") == "open" and t.get("slot") not in (0, 1): bad.append(f"trim {tn}: open field slot {t.get('slot')}")
        if set((t.get("ends") or {}).keys()) != {"from", "to"} or any(k not in ENDS for k in t["ends"].values()): bad.append(f"trim {tn}: ends {t.get('ends')}")
        if not isinstance(t.get("corners"), list): bad.append(f"trim {tn}: corners {t.get('corners')}")
        j = t.get("join") or {}
        if j.get("kind") not in JOINS or any(w not in P.get("trims", {}) for w in j.get("with", [])): bad.append(f"trim {tn}: join {j}")
    return bad


def legacy(P):
    """(plate, zones): the plate header and the zone data in the shapes that the map code reads (the plate header and the zone data), which the page and
    the map code read. Nothing is computed here."""
    D = P.get("decisions", {}); S = P.get("settings", {})
    plate = {"viewBox": P["viewBox"], "mmPerPx": P["mmPerPx"], "uvPack": P.get("uvPack"),
             "zones": {n: {"id": z["id"], "piece": z.get("piece", n), **D.get("zones", {}).get(n, {})} for n, z in P["zones"].items()},
             "trims": {}}
    for n, t in P.get("trims", {}).items():
        plate["trims"][n] = {"id": t["id"], "type": t["type"], **D.get("trims", {}).get(n, {}), "side": t["side"], "zone": t["zone"],
                             "anchor": t.get("anchor", "cf"), **{k: t[k] for k in ROLE_KEYS if k in t}}
    for k in ("shadeSmoothMm", "shadeSmoothPx", "shadeSpace", "shadeEncoding", "shadeMedian", "neck"):
        if k in D: plate[k] = D[k]
    Z = {"view": P["view"], "mmPerPx": P["mmPerPx"], "viewBox": P["viewBox"], "zones": {}, "trims": {}}
    for k in ("thetaDeg", "shadeSmoothEps", "shadeSmoothMm", "shadeSpace"):
        if k in S: Z[k] = S[k]
    if "uvPack" in P: Z["uvPack"] = P["uvPack"]
    if "trimPack" in P: Z["trimPack"] = P["trimPack"]
    for n, z in P["zones"].items():
        Z["zones"][n] = {"order": z["order"], "outline": outline(P, n), "id": z.get("id"), "piece": z.get("piece", n)}
        if "frame" in z and "L" in z["frame"]: Z["zones"][n]["frame"] = z["frame"]
    for n, strips in under_strips(P).items(): Z["zones"][n]["under"] = strips
    for n, t in P.get("trims", {}).items():
        Z["trims"][n] = {k: t[k] for k in ("order", "type", "line", "side", "zone", "anchor", "cut", "id", *ROLE_KEYS) if k in t}
    for k in ("landmarks", "stitches", "invariants"):
        if k in P: Z[k] = P[k]
    if P.get("occluders"): Z["occluders"] = [chain(P, o) if o and isinstance(o[0][0], str) else o for o in P["occluders"]]
    cuts = [n for n, e in P["edges"].items() if e["type"] == "cut"]
    if cuts:
        Z["neckEdge"] = P["edges"][cuts[0]]["points"]
        Z["neckZone"] = next((zn for zn, z in P["zones"].items() if any(e == cuts[0] for e, _ in z["outline"])), None)
    return plate, Z


ROLE_KEYS = ("group", "field", "slot", "live", "bandInMm", "bandOutMm", "join", "ends", "corners")   # a trim's tables and roles (StepB, StepC)
UNDER_PX = 6.0


def under_strips(P):
    """StepA step 4: at a seam the LOWER zone runs UNDER_PX px under the upper one (the upper zone ends on the seam), so that no
    hairline of the photo shows between them. {lower zone: [strip polygons]}: each strip is the seam and the seam moved UNDER_PX
    toward the upper zone (each point along its own normal)."""
    out = {}
    Zs = P["zones"]
    for n, e in P["edges"].items():
        if e["type"] != "seam" or "under" in e or len(e.get("zones", [])) != 2: continue
        a, b = e["zones"]
        if Zs[a]["order"] == Zs[b]["order"]: continue
        lo, up = (a, b) if Zs[a]["order"] < Zs[b]["order"] else (b, a)
        pts = e["points"]
        if len(pts) < 2: continue
        upo = outline(P, up)

        def normal(i):
            p, q = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
            tx, ty = q[0] - p[0], q[1] - p[1]; L = math.hypot(tx, ty) or 1.0
            return -ty / L, tx / L
        m = len(pts) // 2
        nx, ny = normal(m)
        mid = ((pts[m][0] + pts[max(0, m - 1)][0]) / 2, (pts[m][1] + pts[max(0, m - 1)][1]) / 2) if len(pts) > 2 else ((pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2)
        sgn = 1.0 if _inside((mid[0] + 2 * nx, mid[1] + 2 * ny), upo) else -1.0
        off = []
        for i, p in enumerate(pts):
            nx, ny = normal(i)
            off.append([p[0] + sgn * nx * UNDER_PX, p[1] + sgn * ny * UNDER_PX])
        out.setdefault(lo, []).append([list(p) for p in pts] + off[::-1])
    return out


def _inside(pt, poly):
    c = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > pt[1]) != (y2 > pt[1]) and pt[0] < (x2 - x1) * (pt[1] - y1) / (y2 - y1) + x1: c = not c
    return c


def chain(P, ch):
    """The points of a chain of edges [[edge, +1 | -1], ...] (an occluder): a join point written once; no closure required."""
    out = []
    for name, d in ch:
        pts = P["edges"][name]["points"]
        pts = pts if d > 0 else pts[::-1]
        out += pts[1:] if out and out[-1] == pts[0] else pts
    return [list(p) for p in out]


def dump(P):
    """Text, one number per place, stable: curves one point per line, every other value as JSON."""
    out = []

    def walk(v, path):
        if is_curve(v):
            out.append(f"{path} = curve {len(v)}")
            out.extend(f"  {x:.1f} {y:.1f}" for x, y in v)
        elif isinstance(v, dict):
            for k in sorted(v): walk(v[k], f"{path}.{k}" if path else k)
        elif isinstance(v, list) and any(isinstance(x, (dict, list)) for x in v):
            for i, x in enumerate(v): walk(x, f"{path}[{i}]")
        else:
            out.append(f"{path} = {json.dumps(v)}")
    walk(P, "")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] not in ("--dump", "--check"): sys.exit(__doc__)
    if a[0] == "--dump":
        try:
            sys.stdout.write(dump(read(a[1])))
        except ValueError as e:                                              # an older file (BSP1): say so, for git diff
            sys.stdout.write(f"{e} ({os.path.getsize(a[1])} B)\n")
    else:
        nb = 0
        for p in a[1:]:
            bad = validate(read(p))
            print(f"{'PASS' if not bad else 'FAIL'}  {p}" + "".join(f"\n      {b}" for b in bad))
            nb += bool(bad)
        sys.exit(1 if nb else 0)
