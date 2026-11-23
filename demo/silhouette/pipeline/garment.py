"""The garment record (StepB step 2): the block "garment" of assets/looks/<look>.json. Pure Python, no Pillow.

usage: python3 silhouette/pipeline/garment.py --check [look]     validate the record (default look: straight-kurta)
       python3 silhouette/pipeline/garment.py --dump [look]      every value with its source, one per line
As a module: load(look) -> G, validate(G) -> [problems], ghash(G) -> 16 hex, header(look) -> {look, version, hash},
landmark(G, view, name) -> (garment landmark | None, line | None), piece(G, view, zone) -> piece, expected(G, name, piece) -> (u, v) | None.

The record (docs/formats.md):
  version      an integer; raise it when a value changes meaning
  pieces       {piece: {grain, origin, u, v}}: what the piece's fabric frame is (u, v in cm)
  landmarks    {name: {compare: uv | v | none, at: {piece: {u, v, src, views?, spreadMm?, note?}}, note?}}
  lines        {name: {piece, v, src, note?}}: a weft line (a hem, a cuff): only v is a property of the cloth
  views        {view: {zones: {zone: piece}, landmarks: {view name: garment name | {line: name} | null (not a garment point)},
                acceptedResiduals: {view name: reason}}}: a landmark whose residual over 3 mm the OWNER accepts (StepB step 3)
  placement    {buta: {piece: {u, v, src}}, border: {piece: {hemV, src}}}: where a placed print sits (StepB step 5; the page)
  src          agreed | measured | fitted | assumed | definition
The hash covers the whole block (sorted keys): a plate built against another record is stale (rebuild_check.sh, make_plate.py).
"""
import hashlib, json, os, sys

DEMO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOURCES = ("agreed", "measured", "fitted", "assumed", "definition")
COMPARE = ("uv", "v", "none")
UV_LIMIT_CM = (128.0, 224.0)              # |u| and v inside the page's packing (make_plate.py UV_PACK)


def path(look):
    return os.path.join(DEMO, "assets", "looks", look + ".json")


def load(look="straight-kurta"):
    G = json.load(open(path(look))).get("garment")
    if G is None: raise ValueError(f"{path(look)}: no garment record")
    return G


def ghash(G):
    return hashlib.sha256(json.dumps(G, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def header(look="straight-kurta"):
    G = load(look)
    return {"look": look, "version": G["version"], "hash": ghash(G)}


def landmark(G, view, name):
    """(garment landmark, line) of a view's landmark: (name, None), (None, line) or (None, None) for 'not a garment point'.
    KeyError if the record does not name it."""
    m = G["views"][view]["landmarks"][name]
    if m is None: return None, None
    if isinstance(m, dict): return None, m["line"]
    return m, None


def piece(G, view, zone):
    return G["views"][view]["zones"][zone]


def expected(G, name, pc):
    at = G["landmarks"].get(name, {}).get("at", {}).get(pc)
    return (at["u"], at["v"]) if at else None


def validate(G):
    bad = []
    if not isinstance(G.get("version"), int): bad.append("version: not an integer")
    P = G.get("pieces", {})
    for pn, p in P.items():
        for k in ("grain", "origin", "u", "v"):
            if k not in p: bad.append(f"piece {pn}: no {k}")
    for ln, l in G.get("landmarks", {}).items():
        if l.get("compare") not in COMPARE: bad.append(f"landmark {ln}: compare {l.get('compare')}")
        if l.get("compare") != "none" and not l.get("at"): bad.append(f"landmark {ln}: compared but no value")
        for pn, a in l.get("at", {}).items():
            if pn not in P: bad.append(f"landmark {ln}: unknown piece {pn}")
            if a.get("src") not in SOURCES: bad.append(f"landmark {ln} on {pn}: src {a.get('src')}")
            for k in ("u", "v"):
                if not isinstance(a.get(k), (int, float)): bad.append(f"landmark {ln} on {pn}: {k} not a number")
            if isinstance(a.get("u"), (int, float)) and isinstance(a.get("v"), (int, float)):
                if abs(a["u"]) > UV_LIMIT_CM[0] or not (-32.0 <= a["v"] <= UV_LIMIT_CM[1]): bad.append(f"landmark {ln} on {pn}: outside the packing")
            if a.get("src") == "fitted" and not a.get("views"): bad.append(f"landmark {ln} on {pn}: fitted from no views")
    for ln, l in G.get("lines", {}).items():
        if l.get("piece") not in P: bad.append(f"line {ln}: unknown piece {l.get('piece')}")
        if l.get("src") not in SOURCES: bad.append(f"line {ln}: src {l.get('src')}")
        if not isinstance(l.get("v"), (int, float)): bad.append(f"line {ln}: v not a number")
    for cls, per in G.get("placement", {}).items():
        if cls == "note": continue
        for pn, a in per.items():
            if pn not in P: bad.append(f"placement {cls}: unknown piece {pn}")
            if a.get("src") not in SOURCES: bad.append(f"placement {cls} {pn}: src {a.get('src')}")
            keys = ("u", "v") if cls == "buta" else ("hemV",)
            if any(not isinstance(a.get(k), (int, float)) for k in keys): bad.append(f"placement {cls} {pn}: {keys} not numbers")
    for vn, v in G.get("views", {}).items():
        for zn, pn in v.get("zones", {}).items():
            if pn not in P: bad.append(f"view {vn}: zone {zn} -> unknown piece {pn}")
        for lm, m in v.get("landmarks", {}).items():
            if m is None: continue
            if isinstance(m, dict):
                if m.get("line") not in G.get("lines", {}): bad.append(f"view {vn}: {lm} -> unknown line {m.get('line')}")
            elif m not in G.get("landmarks", {}): bad.append(f"view {vn}: {lm} -> unknown landmark {m}")
        for lm, why in v.get("acceptedResiduals", {}).items():
            if lm not in v.get("landmarks", {}): bad.append(f"view {vn}: accepted residual of unknown landmark {lm}")
            if not str(why).strip(): bad.append(f"view {vn}: accepted residual of {lm} without a reason")
    return bad


def dump(G):
    out = [f"version = {G['version']}", f"hash = {ghash(G)}"]
    for pn, p in sorted(G["pieces"].items()): out.append(f"piece {pn}: grain {p['grain']}; origin {p['origin']}; u {p['u']}")
    for ln, l in sorted(G["landmarks"].items()):
        if not l.get("at"): out.append(f"landmark {ln:16} {l['compare']:4}  (not compared) {l.get('note', '')}")
        for pn, a in sorted(l.get("at", {}).items()):
            extra = (f" from {','.join(a['views'])}" if a.get("views") else "") + (f" spread {a['spreadMm']} mm" if a.get("spreadMm") else "")
            out.append(f"landmark {ln:16} {l['compare']:4} {pn:9} u {a['u']:8.2f}  v {a['v']:8.2f}  {a['src']}{extra}")
    for ln, l in sorted(G.get("lines", {}).items()):
        out.append(f"line     {ln:16} v    {l['piece']:9} v {l['v']:8.2f}  {l['src']}")
    for vn, v in sorted(G["views"].items()):
        out.append(f"view {vn}: zones " + ", ".join(f"{z} -> {p}" for z, p in v["zones"].items()))
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] not in ("--check", "--dump"): sys.exit(__doc__)
    look = a[1] if len(a) > 1 else "straight-kurta"
    G = load(look)
    if a[0] == "--dump":
        sys.stdout.write(dump(G))
    else:
        bad = validate(G)
        print(f"{'PASS' if not bad else 'FAIL'}  {look} garment v{G['version']} {ghash(G)}" + "".join(f"\n      {b}" for b in bad))
        sys.exit(1 if bad else 0)
