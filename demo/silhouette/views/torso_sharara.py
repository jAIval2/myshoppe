"""The full-torso view of the kurta and tiered sharara (torso-sharara): measured on source.png (765 x 1024), 2026-11-23.

The silhouette is read from the image (silhouette/views/_kit.py); the neckline, the seams and the landmarks were read by eye on
gridded crops of source.png (x2). Source px; the plate is the 765 x 1020 crop, x 1.5686 -> 1200 x 1600.
Zones (draw order): leg-l (1), leg-r (2; the sharara's legs, touching on the centre line), kurta (3; it lies on the sharara),
sleeve-l, sleeve-r (4; each lies against the kurta's body down to its cuff).
Not garment: the form above the neckline, the floor and the sunlit wall beside the sharara's hem, the stand.
As a module (make_plate.py): base(path), measure(). Run alone: the kit's checks, and review/torso-sharara/zones.png.
"""
import os, sys
sys.path[:0] = [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), d) for d in ("pipeline", "views")]
import _kit

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sources", "torso-sharara.png")
PATCHES = [((625, 895, 662, 935), -60)]                                       # the sparkle mark on the floor, from 60 px left

NECK = [(342, 124), (350, 129), (360, 132), (372, 134), (385, 135), (398, 134), (410, 132), (420, 129), (427, 124)]   # neck-l -> neck-r
FORM = [(330, 0), (440, 0), (440, 122)] + NECK[::-1] + [(330, 122)]          # the form above the neckline
SEAMS = {
    "armhole-l": [(274, 136), (277, 147), (281, 160), (283, 180), (285, 200), (286, 220), (287, 238), (287, 260), (285, 300),
                  (281, 340), (277, 380), (272, 420), (266, 460), (262, 480), (252, 490)],          # + the sleeve's inner edge, to the wall
    "armhole-r": [(496, 136), (493, 148), (489, 160), (487, 180), (486, 200), (485, 220), (484, 238), (485, 260), (487, 300),
                  (490, 340), (492, 380), (495, 420), (498, 460), (500, 482), (510, 492)],
    "kurta-hem": [(254, 598), (263, 597), (300, 597), (385, 598), (470, 597), (497, 597), (508, 596)],   # the kurta lies on the sharara
    "legs": [(385, 598), (385, 700), (385, 800), (385, 925)],                                          # the legs meet on the centre line
}
LM = {"neck-l": (342, 126), "neck-r": (427, 126), "cf-neck": (385, 135), "shoulder-l": (279, 150), "shoulder-r": (491, 151),
      "underarm-l": (287, 238), "underarm-r": (484, 238), "kurta-hem-l": (267, 594), "kurta-hem-r": (496, 596), "kurta-hem-cf": (385, 597),
      "cuff-out-l": (210, 475), "cuff-in-l": (262, 480), "cuff-out-r": (562, 471), "cuff-in-r": (500, 482),
      "leg-l-top": (325, 602), "leg-r-top": (445, 602), "leg-l-out": (205, 884), "leg-r-out": (558, 883), "legs-cf": (385, 893)}


def base(path=SRC):
    return _kit.base(path, PATCHES)


def spec():
    mm = 158.0 / ((LM["neck-r"][0] - LM["neck-l"][0]) * _kit.K)
    v_hem = round((LM["kurta-hem-cf"][1] - LM["neck-l"][1]) * _kit.K * mm, 1)     # the sharara's visible top, below the neck-point line
    leg = lambda s: {"axis": "midline", "anchor": {"point": f"leg-{s}-top", "vMm": v_hem}, "sagEdge": f"hem-leg-{s}"}
    return {
        "path": SRC, "patches": PATCHES, "view": "torso", "variant": "sharara",
        "extra_seeds": [(150, 870), (170, 880), (140, 860), (620, 870), (640, 880), (650, 860)],      # the sunlit wall beside the hem
        "exclude": [FORM, [(0, 886), (198, 886), (205, 916), (560, 916), (568, 886), (765, 886), (765, 1020), (0, 1020)]],
        "seams": SEAMS,
        "zones": {
            "kurta": {"seed": (385, 400), "order": 3, "frame": {"axis": ["cf-neck", "kurta-hem-cf"], "anchor": {"line": ["neck-l", "neck-r"]}}},
            "leg-l": {"seed": (300, 750), "order": 1, "frame": leg("l")},
            "leg-r": {"seed": (470, 750), "order": 2, "frame": leg("r")},
            "sleeve-l": {"seed": (245, 350), "order": 4, "frame": {"axis": "midline", "anchor": {"point": "shoulder-l"}, "sagEdge": "cuff-l", "skipTop": 0.15}},
            "sleeve-r": {"seed": (525, 350), "order": 4, "frame": {"axis": "midline", "anchor": {"point": "shoulder-r"}, "sagEdge": "cuff-r", "skipTop": 0.15}},
        },
        "cuts": {"kurta": [("neck", LM["neck-l"], LM["neck-r"])],
                 "sleeve-l": [("cuff-l", LM["cuff-out-l"], LM["cuff-in-l"])], "sleeve-r": [("cuff-r", LM["cuff-in-r"], LM["cuff-out-r"])],
                 "leg-l": [("hem-leg-l", LM["leg-l-out"], LM["legs-cf"])], "leg-r": [("hem-leg-r", LM["legs-cf"], LM["leg-r-out"])]},
        "landmarks": LM,
        "scale": ("neck-l", "neck-r", 158.0, "neck-l -> neck-r = 158 mm (the straight kurta's agreed neck width: the same dress form)"),
        "settings": {"thetaDeg": {"kurta": 60, "leg-l": 70, "leg-r": 70, "sleeve-l": 70, "sleeve-r": 70}},
        "source_note": "silhouette/sources/torso-sharara.png (765 x 1024, as received 2026-11-23), the sparkle mark patched, cut to "
                       "765 x 1020, resized to 1200 x 1600. Silhouette from the image (silhouette/views/_kit.py); seams, neckline and "
                       "landmarks measured on the source by Claude.",
        "trims": {
            "neck": {"order": 3, "type": "insertion", "group": "neck", "edge": "neck"},
            "cuff-l": {"order": 3, "type": "edging", "group": "cuffs", "edge": "cuff-l", "bandInMm": 100.0},
            "cuff-r": {"order": 3, "type": "edging", "group": "cuffs", "edge": "cuff-r", "bandInMm": 100.0},
            "kurta-hem-l": {"order": 3, "type": "edging", "group": "hem", "edge": "seam-leg-l-kurta"},
            "kurta-hem-r": {"order": 3, "type": "edging", "group": "hem", "edge": "seam-leg-r-kurta"},
            "hem-leg-l": {"order": 3, "type": "edging", "group": "hem", "edge": "hem-leg-l", "bandInMm": 100.0, "smoothMm": 40.0},
            "hem-leg-r": {"order": 3, "type": "edging", "group": "hem", "edge": "hem-leg-r", "bandInMm": 100.0, "smoothMm": 40.0},
        },
    }


def measure():
    return _kit.measure(spec())[0]


if __name__ == "__main__":
    P, X = _kit.measure(spec())
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "review", "torso-sharara")
    os.makedirs(out, exist_ok=True)
    _kit.check(P, X, os.path.join(out, "zones.png"))
