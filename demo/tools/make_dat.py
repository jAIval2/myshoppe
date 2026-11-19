"""plate.dat: the curves and the decisions of one plate in one small binary file (numeric.md step 6). Pillow is not needed.

usage: python3 tools/make_dat.py <plate-dir> [--check]      reads zones.json + plate.json, writes <plate-dir>/plate.dat
       python3 tools/make_dat.py --all                      the 4 plates of assets/plates

What the page needs to build the maps of a view, and nothing else (the maps themselves are not shipped):
  the curves   every grid edge and outline of every zone, every trim centre line, the occluders, the neck edge: lists of (x, y) in plate px
  the numbers  everything plate.json says (scale, ranges, ids, trim lengths and sides, the shade median, the neck block: rectangle,
               fill colours, form patch ...) and what zones.json adds (order, widthPx, thetaDeg, tuck, trim widths and types,
               shadeSmoothEps). The decisions that make_plate.py takes by searching the image arrive here as numbers.

Format (little endian):
  "BSP1"            4 bytes
  u16 version (1)
  u16 unit          the coordinate unit in 1/1000 px (100 = 0.1 px: every coordinate of zones.json is a multiple of 0.1 px, checked)
  u32 hlen          length of the JSON header
  header            UTF-8 JSON, hlen bytes, padded with spaces to a multiple of 2
  curves            int16, all curves one after the other, each point as (dx, dy) from the previous point (the first one from 0, 0);
                    the header lists the number of points of each curve, in the same order.
The header holds the numbers and refers to a curve by its index in `curves` (identical curves are stored once: the grid top of the
front zone is also the neck's grid top, the neck trim centre is also the neck's centre).
plate.js parseDat() gives back { plate, zones } as plate.json / zones.json would, so that the page code is the same for both.
"""
import gzip, json, os, struct, sys

UNIT = 100                                   # 1/1000 px
MAGIC = b"BSP1"


def quant(v):
    i = round(v * 1000 / UNIT)
    if abs(i * UNIT / 1000 - v) > 1e-9:
        raise ValueError(f"{v} is not a multiple of {UNIT / 1000} px: this plate needs a finer unit (or the curve thinned and rounded)")
    return i


def build(pd):
    Z = json.load(open(os.path.join(pd, "zones.json")))
    P = json.load(open(os.path.join(pd, "plate.json")))
    curves, index = [], {}

    def curve(pts):
        key = tuple((quant(x), quant(y)) for x, y in pts)
        if key not in index:
            index[key] = len(curves)
            curves.append(key)
        return index[key]

    zones = {}
    for name, z in Z["zones"].items():
        g = z["grid"]
        zones[name] = {"order": z["order"], "grid": {k: curve(g[k]) for k in ("top", "left", "right", "bottom")}, "outline": curve(z["outline"])}
        if "widthPx" in z:
            zones[name]["widthPx"] = z["widthPx"]
    trims = {}
    for name, t in Z["trims"].items():
        trims[name] = {"order": t["order"], "widthMm": t["widthMm"], "centre": curve(t["centre"])}
        if "type" in t:
            trims[name]["type"] = t["type"]
    plate = {k: v for k, v in P.items() if k != "neck"}
    head = {"v": 1, "view": Z["view"], "mmPerPx": Z["mmPerPx"], "plate": plate, "zones": zones, "trims": trims}
    for k in ("thetaDeg", "tuck", "shadeSmoothEps", "shadeSmoothMm"):
        if k in Z:
            head[k] = Z[k]
    if Z.get("occluders"):
        head["occluders"] = [curve(o) for o in Z["occluders"]]
    if "neck" in P:
        nk = dict(P["neck"])
        # the three curves of the neck block: the photographed edge (its own), the trim centre line and the grid top (shared)
        head["neck"] = {**{k: v for k, v in nk.items() if k not in ("edge", "centre", "top")},
                        "edge": curve(nk["edge"]), "centre": curve(nk["centre"]), "top": curve(nk["top"])}
    head["curves"] = [len(c) for c in curves]
    hjson = json.dumps(head, separators=(",", ":")).encode("utf-8")
    hjson += b" " * (len(hjson) % 2)
    body = bytearray()
    for c in curves:
        px = py = 0
        for x, y in c:
            dx, dy = x - px, y - py
            if not (-32768 <= dx <= 32767 and -32768 <= dy <= 32767):
                raise ValueError("a step is larger than int16")
            body += struct.pack("<hh", dx, dy)
            px, py = x, y
    return MAGIC + struct.pack("<HHI", 1, UNIT, len(hjson)) + hjson + bytes(body), len(curves), sum(len(c) for c in curves)


def main():
    plates = sorted(os.path.join("assets/plates", d) for d in os.listdir("assets/plates") if d.endswith("-straight")) if "--all" in sys.argv else [sys.argv[1]]
    total = totalgz = 0
    for pd in plates:
        data, nc, npts = build(pd)
        open(os.path.join(pd, "plate.dat"), "wb").write(data)
        gz = len(gzip.compress(data, 9))
        raw_json = sum(os.path.getsize(os.path.join(pd, f)) for f in ("zones.json", "plate.json"))
        gj = sum(len(gzip.compress(open(os.path.join(pd, f), "rb").read(), 9)) for f in ("zones.json", "plate.json"))
        print(f"{os.path.basename(pd):16} {len(data):6} B  ({gz} B gzip)   {nc} curves, {npts} points   zones.json + plate.json: {raw_json} B ({gj} B gzip)")
        total += len(data)
        totalgz += gz
    print(f"{'total':16} {total:6} B  ({totalgz} B gzip)")


if __name__ == "__main__":
    main()
