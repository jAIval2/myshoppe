"""Swatch and lace prep: one entry point (Python 3 + Pillow). Sources in swatchprep/sources (they do not ship); the page reads the
results from demo/assets/swatches. Paths are relative to where you run it. Run from anywhere.

usage: python3 demo/swatchprep/prep.py <command> <args ...>

  fabric <in> <out.jpg> [preview_3x3.png] [--no-delight]
                       a flat fabric photo -> a de-lit, seamless 1024 px tile (prep_fabric.py); its real width (repeatCm) is set
                       in testing.html FABRICS
  lace <in> <out.webp> <preview.png> [--flip] [--cut-bottom 0.12] [--paper R,G,B] [--key 8]
                       a lace photo on plain paper -> a horizontal band with alpha, its decorative edge at the bottom (prep_lace.py)
  lace-repeat <band.webp> <out.webp> <out.json> <preview.png> [--width-mm 30] [--flip]
                       the band -> a seamless tile of whole periods + its sidecar lace-<name>.json (period, edgeDepth, widthMm)
  lace-material <tile.webp> <sidecar.json> <out-mat.webp> <preview.png> [--pearls]
                       the material map: R height, G metal, B pearl
  first-swatches <src-dir> <out-dir> <debug-dir>
                       the first sage fabric and pearl lace, from sources/fabric-sage-640.png and lace-pearl-640.png
                       (prep_swatches.py: the record of how those two were made)
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = {"fabric": ("prep_fabric.py", []), "lace": ("prep_lace.py", []), "lace-repeat": ("prep_lace.py", ["--repeat"]),
        "lace-material": ("prep_lace.py", ["--material"]), "first-swatches": ("prep_swatches.py", [])}


def main(a):
    if not a or a[0] not in TOOL:
        print(__doc__, file=sys.stderr if a else sys.stdout)
        return 0 if not a or a[0] in ("-h", "--help") else 2
    script, pre = TOOL[a[0]]
    return subprocess.run([sys.executable, os.path.join(HERE, script), *pre, *a[1:]]).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
