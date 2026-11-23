"""The neckline view of the anarkali (neck-anarkali): measured on source.png (765 x 1024), 2026-11-23.

The cloth is a warm white against a warm wall at low contrast, so the outer silhouette was read by eye (gridded crops, x0.95 .. x1.3)
and set as a barrier 3 px outside the edge: the background fill cannot enter the garment, and the build's snap brings the free edges
onto the photo (silhouette/views/_kit.py). Seams, the neckline, the underarm gaps and the landmarks: read by eye on the crops.
Source px; the plate is the 765 x 1020 crop, x 1.5686 -> 1200 x 1600. The garment runs off the bottom of the frame.
Zones (draw order): skirt (below the empire waist, 1), front (the bodice, 2), sleeve-l, sleeve-r (3; each lies on the skirt below a
narrow underarm gap: left x 217 .. 239, y 396 .. 480, then the sleeve's inner edge on a fold; right x 540 .. 550, y 385 .. 440).
As a module (make_plate.py): base(path), measure(). Run alone: the kit's checks, and review/neck-anarkali/zones.png.
"""
import os, sys
sys.path[:0] = [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), d) for d in ("pipeline", "views")]
import _kit

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sources", "neck-anarkali.png")
PATCHES = [((630, 885, 685, 945), 65)]                                        # the sparkle mark on the wall, from 65 px right (wall)

NECK = [(295, 203), (305, 215), (320, 226), (340, 234), (384, 238), (428, 234), (448, 226), (463, 215), (476, 203)]   # neck-l -> neck-r
FORM = [(280, 0), (490, 0), (490, 200)] + NECK[::-1] + [(280, 200)]
OUTER = [   # the silhouette against the wall, 3 px outside the edge (a barrier for the background fill)
    [(295, 199), (250, 219), (196, 238), (155, 346), (118, 494), (89, 662), (66, 810), (56, 845), (108, 859), (163, 869), (157, 940), (153, 1019)],
    [(476, 199), (520, 219), (567, 238), (594, 388), (631, 599), (712, 790), (720, 843), (700, 850), (660, 858), (614, 867), (613, 940), (609, 1019)],
]
SEAMS = {
    "armhole-l": [(196, 236), (198, 243), (201, 280), (205, 320), (211, 355), (220, 385), (227, 420)],                  # into the gap
    "sleeve-skirt-l": [(233, 462), (238, 480), (240, 510), (242, 534), (242, 560), (230, 620), (220, 680), (210, 730), (200, 780), (185, 830), (166, 864), (148, 885)],
    "waist": [(240, 534), (247, 534), (300, 535), (384, 535), (470, 535), (530, 534), (548, 533)],
    "armhole-r": [(566, 236), (563, 243), (565, 280), (563, 320), (556, 355), (546, 385), (545, 412)],
    "sleeve-body-r": [(545, 430), (548, 440), (543, 500), (545, 560), (552, 640), (560, 700), (570, 760), (585, 820), (604, 862),
                      (614, 870), (626, 885)],
}
LM = {"neck-l": (297, 206), "neck-r": (474, 206), "cf-neck": (384, 238), "cf-low": (384, 1019), "shoulder-l": (201, 246),
      "shoulder-r": (561, 246), "underarm-l": (221, 388), "underarm-r": (546, 388), "waist-l": (247, 535), "waist-r": (540, 535),
      "waist-cf": (384, 535), "cuff-out-l": (63, 841), "cuff-in-l": (170, 867), "cuff-out-r": (716, 844), "cuff-in-r": (612, 863)}


def base(path=SRC):
    return _kit.base(path, PATCHES)


def spec():
    mm = 158.0 / ((LM["neck-r"][0] - LM["neck-l"][0]) * _kit.K)
    v_waist = round((LM["waist-cf"][1] - LM["neck-l"][1]) * _kit.K * mm, 1)
    return {
        "path": SRC, "patches": PATCHES, "view": "neck", "variant": "anarkali", "border": False,
        "extra_seeds": [(30, 100), (735, 100), (100, 10), (650, 10), (20, 600), (745, 600), (15, 950), (750, 950), (200, 60), (560, 60),
                        (100, 1000), (700, 1000), (226, 430), (545, 415), (110, 885), (660, 885)],              # the wall; the two underarm gaps
        "bg_barriers": OUTER,
        "exclude": [FORM,
                    [(217, 396), (225, 396), (231, 425), (236, 455), (239, 480), (236, 481), (229, 455), (221, 425)],   # the left underarm gap (y 396 .. 480; below it a fold)
                    [(539, 384), (551, 384), (549, 440), (542, 441)]],        # the right one
        "seams": SEAMS,
        "zones": {
            "front": {"seed": (384, 400), "order": 2, "frame": {"axis": ["cf-neck", "waist-cf"], "anchor": {"line": ["neck-l", "neck-r"]}}},
            "skirt": {"seed": (384, 800), "order": 1, "frame": {"axis": ["waist-cf", "cf-low"], "anchor": {"point": "waist-cf", "vMm": v_waist}}},
            "sleeve-l": {"seed": (150, 600), "order": 3, "frame": {"axis": "midline", "anchor": {"point": "shoulder-l"}, "sagEdge": "cuff-l", "skipTop": 0.15}},
            "sleeve-r": {"seed": (610, 600), "order": 3, "frame": {"axis": "midline", "anchor": {"point": "shoulder-r"}, "sagEdge": "cuff-r", "skipTop": 0.15}},
        },
        "cuts": {"front": [("neck", LM["neck-l"], LM["neck-r"])],
                 "sleeve-l": [("cuff-l", LM["cuff-out-l"], LM["cuff-in-l"])], "sleeve-r": [("cuff-r", LM["cuff-in-r"], LM["cuff-out-r"])]},
        "landmarks": LM,
        "scale": ("neck-l", "neck-r", 158.0, "neck-l -> neck-r = 158 mm (the straight kurta's agreed neck width: the same dress form)"),
        "settings": {"thetaDeg": {"front": 60, "skirt": 70, "sleeve-l": 70, "sleeve-r": 70}},
        "source_note": "silhouette/sources/neck-anarkali.png (765 x 1024, as received 2026-11-23), the sparkle mark patched, cut to "
                       "765 x 1020, resized to 1200 x 1600. The outer silhouette read by eye as a barrier; seams, neckline and landmarks "
                       "measured on the source by Claude.",
        "trims": {
            "neck": {"order": 3, "type": "insertion", "group": "neck", "edge": "neck"},
            "cuff-l": {"order": 3, "type": "edging", "group": "cuffs", "edge": "cuff-l", "bandInMm": 100.0},
            "cuff-r": {"order": 3, "type": "edging", "group": "cuffs", "edge": "cuff-r", "bandInMm": 100.0},
        },
    }


def measure():
    return _kit.measure(spec())[0]


if __name__ == "__main__":
    P, X = _kit.measure(spec())
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "review", "neck-anarkali")
    os.makedirs(out, exist_ok=True)
    _kit.check(P, X, os.path.join(out, "zones.png"))
