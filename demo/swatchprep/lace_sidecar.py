"""Lace sidecar version 2 (StepC step 1): every number of a lace with its source, its class and its name. Pure Python.

usage: python3 swatchprep/lace_sidecar.py upgrade <lace.json> --name "<name>" --class <class> [--width-mm <mm> --src measured]
       python3 swatchprep/lace_sidecar.py check <lace.json> ...

Version 2 adds to the keys prep_lace.py writes (bandPx, edge, widthMm, edgeDepth, edging, periodPx, periods, periodRatio, motifCentrePx,
mirror, material ...):
  version      2
  name         the customer-facing name
  class        insertion | edging | border | gota | zari | pearl | mirror | latkan
  widthSrc     assumed | measured: the band's real width (widthMm). A real lace: a ruler across the band (swatchprep/README.md)
  repeatSrc    the repeat in cm is periodRatio x widthMm: "measured" only when the width is; the period itself is measured on the image
  materialFile the material map (R height, G metal, B pearl), or null
  endRule      how the lace ends where a trim ends on a whole motif (StepC step 3): "boundary" (the last motif boundary: no image)
The upgrade keeps every existing key (the band, the material map and their numbers do not change) and drops "widthMmNote" (its content
is now widthSrc).
"""
import json, os, sys

CLASSES = ("insertion", "edging", "border", "gota", "zari", "pearl", "mirror", "latkan")
SOURCES = ("assumed", "measured")


def upgrade(path, name, cls, width=None, src=None):
    m = json.load(open(path))
    if cls not in CLASSES: sys.exit(f"class {cls}: one of {CLASSES}")
    if width is not None: m["widthMm"] = float(width)
    m.pop("widthMmNote", None)
    m.update({"version": 2, "name": name, "class": cls, "widthSrc": src or m.get("widthSrc", "assumed")})
    m["repeatSrc"] = "measured" if m["widthSrc"] == "measured" else "assumed"
    m["materialFile"] = (m.get("material") or {}).get("file")
    m.setdefault("endRule", "boundary")
    json.dump(m, open(path, "w"), indent=1)
    print(f"{os.path.basename(path)}: v2, {cls}, width {m['widthMm']} mm ({m['widthSrc']})")


def check(paths):
    bad = 0
    for p in paths:
        m = json.load(open(p))
        prob = [k for k in ("version", "name", "class", "widthMm", "widthSrc", "repeatSrc", "endRule") if k not in m]
        if m.get("version") != 2: prob.append("version != 2")
        if m.get("class") not in CLASSES: prob.append(f"class {m.get('class')}")
        if m.get("widthSrc") not in SOURCES: prob.append(f"widthSrc {m.get('widthSrc')}")
        print(f"{'PASS' if not prob else 'FAIL'}  {os.path.basename(p)}" + ("" if not prob else "  " + "; ".join(prob)))
        bad += bool(prob)
    return 1 if bad else 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["check"]: sys.exit(check(a[1:]))
    if a[:1] != ["upgrade"] or len(a) < 2 or "--name" not in a or "--class" not in a: sys.exit(__doc__)
    opt = lambda k: a[a.index(k) + 1] if k in a else None
    upgrade(a[1], opt("--name"), opt("--class"), opt("--width-mm"), opt("--src"))
