"""plate.dat version 2 (BSP2): every number of one view in one small binary file (StepA step 1). Pillow is not needed.

usage: python3 tools/platedat.py --dump <plate-dir | plate.dat>     the file as text, in a stable order (git diff uses it: diff=dat)
       python3 tools/platedat.py --check <plate-dir> ...           read and validate
As a module: read(path) -> P, write(path, P) -> bytes, encode(P) -> bytes, validate(P) -> [problems], outline(P, zone) -> points,
dump(P) -> text, legacy(P) -> (plate, zones): the two objects the page and the old tools know (the plate header and the zone data).

Format (little endian):
  "BSP2"     4 bytes
  u16 version (2), u16 unit (coordinate unit in 1/1000 px: 100 = 0.1 px), u32 hlen
  header     UTF-8 JSON, hlen bytes (padded with spaces to a multiple of 2)
  curves     int16 (dx, dy) per point, every curve one after the other, the first point from (0, 0); "curves" in the header lists the
             number of points of each curve, in the same order.
In the header every polyline (a list of 2 or more [x, y] pairs) is replaced by {"@c": index}; identical curves are stored once.
A curve's points are rounded to the unit when written.

The header P (what a plate is; StepA.md section 1, items 7-8):
  v, view, variant, viewBox, mmPerPx, uvRangeCm, scaleNote, source
  edges      {name: {type: free | seam | frame | cut, points, zones: [a, b] (a seam)}}.  A seam is ONE list used by two zones.
             A lower zone's run that lies hidden under a later zone (the sleeve view's body under the sleeve; the torso's front under
             the sleeves) is a seam with "under": <the later zone>, used by that one lower zone.
             free = a visible contour (snapped to the photo, StepA step 3); frame = the image border; cut = the live neck dip.
  zones      {name: {id, order, outline: [[edge, +1 | -1], ...], grid: {top, left, right, bottom} (until step 7), widthPx (until step 4)}}
             The outline is the chain of its edges; a join point shared by two consecutive edges is written once.
  trims      {name: {id, order, widthMm, type, edge, centre, ...}}: drawn in this order (a later trim wins)
  stitches   {name: points};  occluders: [points];  landmarks {name: [x, y]};  invariants {openings, skipTrimOffset}
  settings   view settings: thetaDeg, tuck (torso v1 only), shadeSmoothMm, shadeSmoothEps, shadeSpace
  decisions  what tools/make_plate.py takes from the image: shadeMedian, shadeSmoothPx, shadeEncoding, the neck block, each trim's
             side / length / vMax, each zone's size in cm
"""
import json, math, os, struct, sys

MAGIC, VERSION, UNIT = b"BSP2", 2, 100
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
    if data[:4] != MAGIC: raise ValueError("plate.dat: not BSP2")
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
    for k in ("view", "viewBox", "mmPerPx", "edges", "zones"):
        if k not in P: bad.append(f"no {k}")
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
        if "centre" not in t: bad.append(f"trim {tn}: no centre")
        if t.get("edge") and t["edge"] not in E: bad.append(f"trim {tn}: unknown edge {t['edge']}")
    return bad


def legacy(P):
    """(plate, zones): the plate header and the zone data in the shapes that the map code reads (the plate header and the zone data), which the page and
    the map code read. Nothing is computed here."""
    D = P.get("decisions", {}); S = P.get("settings", {})
    plate = {"viewBox": P["viewBox"], "mmPerPx": P["mmPerPx"], "uvRangeCm": P.get("uvRangeCm", 128.0),
             "zones": {n: {"id": z["id"], **D.get("zones", {}).get(n, {})} for n, z in P["zones"].items()},
             "trims": {}}
    for n, t in P.get("trims", {}).items():
        plate["trims"][n] = {"id": t["id"], **{k: v for k, v in D.get("trims", {}).get(n, {}).items() if k == "lengthCm"},
                             "widthMm": t["widthMm"], "type": t["type"], "outerV": 1,
                             **{k: v for k, v in D.get("trims", {}).get(n, {}).items() if k != "lengthCm"}}
    for k in ("shadeSmoothMm", "shadeSmoothPx", "shadeSpace", "shadeEncoding", "shadeMedian", "neck"):
        if k in D: plate[k] = D[k]
    Z = {"view": P["view"], "mmPerPx": P["mmPerPx"], "viewBox": P["viewBox"], "zones": {}, "trims": {}}
    for k in ("thetaDeg", "tuck", "shadeSmoothEps", "shadeSmoothMm", "shadeSpace"):
        if k in S: Z[k] = S[k]
    if "uvRangeCm" in P: Z["uvRangeCm"] = P["uvRangeCm"]
    for n, z in P["zones"].items():
        Z["zones"][n] = {"order": z["order"], "grid": z["grid"], "outline": outline(P, n)}
        if "widthPx" in z: Z["zones"][n]["widthPx"] = z["widthPx"]
    for n, t in P.get("trims", {}).items():
        Z["trims"][n] = {"order": t["order"], "widthMm": t["widthMm"], "type": t["type"], "centre": t["centre"]}
    for k in ("landmarks", "stitches", "occluders", "invariants"):
        if k in P: Z[k] = P[k]
    return plate, Z


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
