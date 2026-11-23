"""A fabric's sidecar (StepB step 5): what the page and the portal need to know of a fabric tile, next to the tile. Pillow only.

usage: python3 swatchprep/fabric_sidecar.py <tile> <out.json> --name "<name>" --repeat-cm <cm> [--src assumed|measured]
          [--class allover|oneway|buta|border|irregular] [--motif x,y] [--border-bottom <px> --border-top <px>] [--sheen <0..1>] [--sheen-width <n>]
          [--anti-tile] [--test]

The sidecar (docs/formats.md):
  name, tile (file name), tilePx [w, h], repeatCm (the tile's real width) + repeatSrc (assumed: the AI swatches; measured: a ruler scan,
  swatchprep/README.md), class, oneWay (the print has an up: it runs down the grain, v increasing, on every piece), motifCentrePx
  (buta: the motif's centre in the tile), borderBottomPx / borderTopPx (border: the band's lower edge in the tile, the line that sits
  on the hem, and its upper edge: above the band the page repeats only the ground, the tile's rows 0 .. borderTopPx),
  sheen, sheenWidth, antiTile, meanRgb (the tile's mean colour, sRGB), test (a test print, not offered to the customer).
The page places the print by class (testing.html placeOf): allover / irregular / oneway at the garment's origin; buta with the motif
on the garment record's placement point of each piece; border with borderBottomPx on each piece's hem line.
"""
import json, os, sys
from PIL import Image, ImageStat

CLASSES = ("allover", "oneway", "buta", "border", "irregular")


def main(a):
    if len(a) < 2 or "--name" not in a or "--repeat-cm" not in a: sys.exit(__doc__)
    tile, out = a[0], a[1]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    cls = opt("--class", "allover")
    if cls not in CLASSES: sys.exit(f"class {cls}: one of {CLASSES}")
    im = Image.open(tile).convert("RGB")
    S = {"name": opt("--name"), "tile": os.path.basename(tile), "tilePx": list(im.size), "repeatCm": float(opt("--repeat-cm")),
         "repeatSrc": opt("--src", "assumed"), "class": cls, "oneWay": cls in ("oneway", "border", "buta"),
         "sheen": float(opt("--sheen", 0)), "sheenWidth": float(opt("--sheen-width", 1)), "antiTile": "--anti-tile" in a,
         "meanRgb": [round(c) for c in ImageStat.Stat(im).mean]}
    if cls == "buta":
        if not opt("--motif"): sys.exit("a buta needs --motif x,y (the motif's centre in tile px)")
        S["motifCentrePx"] = [float(v) for v in opt("--motif").split(",")]
    if cls == "border":
        if not opt("--border-bottom") or not opt("--border-top"):
            sys.exit("a border needs --border-bottom <px> and --border-top <px> (the band's lower and upper edges in the tile)")
        S["borderBottomPx"], S["borderTopPx"] = float(opt("--border-bottom")), float(opt("--border-top"))
    if "--test" in a: S["test"] = True
    json.dump(S, open(out, "w"), indent=1)
    print(f"{os.path.basename(out)}: {S['class']}, {S['repeatCm']} cm ({S['repeatSrc']}), tile {S['tilePx']}")


if __name__ == "__main__":
    main(sys.argv[1:])
