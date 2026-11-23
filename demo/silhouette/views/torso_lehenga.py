"""The full-torso view of the crop top and flared skirt (torso-lehenga): measured on source.png (765 x 1024), 2026-11-23.

The silhouette is read from the image (silhouette/views/_kit.py); the neckline, the seams, the midriff and the landmarks were read by
eye on gridded crops of source.png (x1.7 .. x2). Source px; the plate is the 765 x 1020 crop, x 1.5686 -> 1200 x 1600.
Zones (draw order): skirt (1), top (the crop top's body, 2), sleeve-l, sleeve-r (3: each lies on the skirt below the top).
Not garment: the form above the neckline and the bare midriff (both excluded), the floor and the stand.
The right sleeve's shaded outer side is close to the wall's colour: a barrier along its edge keeps the background fill out.
As a module (make_plate.py): base(path), measure(). Run alone: the kit's checks, and review/torso-lehenga/zones.png.
"""
import os, sys
sys.path[:0] = [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), d) for d in ("pipeline", "views")]
import _kit

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sources", "torso-lehenga.png")
PATCHES = [((625, 895, 662, 935), -60)]                                       # the sparkle mark on the floor, from 60 px left

NECK = [(338, 121), (345, 126), (355, 130), (370, 133), (385, 134), (400, 133), (415, 130), (425, 126), (431, 121)]   # neck-l -> neck-r
FORM = [(326, 0), (444, 0), (444, 119)] + NECK[::-1] + [(326, 119)]          # the form above the neckline
MIDRIFF = [(299, 309), (477, 309), (477, 322), (299, 322)]                     # the bare form between the top and the waistband, seam to seam

SEAMS = {
    "armhole-l": [(285, 128), (288, 140), (293, 160), (296, 190), (298, 215), (301, 238), (302, 270), (302, 300), (301, 330),
                  (296, 370), (288, 410), (278, 450), (266, 483), (256, 486), (248, 499)],                 # + the inner edge, to the wall
    "armhole-r": [(470, 128), (468, 140), (472, 160), (475, 190), (475, 215), (473, 240), (472, 270), (473, 300), (475, 330),
                  (479, 370), (485, 410), (491, 450), (497, 483), (515, 480), (523, 495)],
}
BARRIERS = [[(478, 126), (491, 159), (502, 200), (508, 240), (515, 280), (520, 320), (525, 360), (529, 400), (537, 440), (543, 470), (546, 478)],
            [(499, 478), (505, 520), (510, 560), (516, 600), (525, 640)]]      # the right sleeve's and the skirt's shaded right edges
LM = {"neck-l": (339, 124), "neck-r": (430, 124), "cf-neck": (385, 134), "shoulder-l": (290, 143), "shoulder-r": (468, 140),
      "underarm-l": (301, 238), "underarm-r": (473, 240), "top-hem-l": (306, 307), "top-hem-r": (459, 307), "top-hem-cf": (385, 308),
      "waist-l": (306, 324), "waist-r": (459, 324), "waist-cf": (385, 324), "hem-l": (182, 866), "hem-r": (600, 858), "hem-cf": (385, 890),
      "cuff-out-l": (213, 476), "cuff-in-l": (266, 483), "cuff-out-r": (541, 472), "cuff-in-r": (497, 483)}


def base(path=SRC):
    return _kit.base(path, PATCHES)


def spec():
    mm = 158.0 / ((LM["neck-r"][0] - LM["neck-l"][0]) * _kit.K)
    v_waist = round((LM["waist-cf"][1] - LM["neck-l"][1]) * _kit.K * mm, 1)
    return {
        "path": SRC, "patches": PATCHES, "view": "torso", "variant": "lehenga",
        "extra_seeds": [(385, 316), (200, 890), (620, 888), (300, 905), (480, 905), (180, 900), (590, 900),   # midriff; the sunlit floor
                        (150, 880), (170, 885), (140, 870), (620, 875), (640, 880), (650, 865)],               # the sunlit wall beside the hem
        "bg_barriers": BARRIERS,
        "exclude": [FORM, MIDRIFF, [(0, 887), (178, 887), (188, 897), (592, 897), (602, 887), (765, 887), (765, 1020), (0, 1020)]],   # the floor: up to y 887 beside the hem
        "seams": SEAMS,
        "zones": {
            "top": {"seed": (385, 220), "order": 2, "frame": {"axis": ["cf-neck", "top-hem-cf"], "anchor": {"line": ["neck-l", "neck-r"]}}},
            "skirt": {"seed": (385, 600), "order": 1, "frame": {"axis": ["waist-cf", "hem-cf"], "anchor": {"point": "waist-cf", "vMm": v_waist}, "sagEdge": "hem"}},
            "sleeve-l": {"seed": (255, 330), "order": 3, "frame": {"axis": "midline", "anchor": {"point": "shoulder-l"}, "sagEdge": "cuff-l", "skipTop": 0.15}},
            "sleeve-r": {"seed": (500, 330), "order": 3, "frame": {"axis": "midline", "anchor": {"point": "shoulder-r"}, "sagEdge": "cuff-r", "skipTop": 0.15}},
        },
        "cuts": {"top": [("neck", LM["neck-l"], LM["neck-r"]), ("top-hem", LM["top-hem-l"], LM["top-hem-r"])],
                 "skirt": [("waist", LM["waist-l"], LM["waist-r"]), ("hem", LM["hem-l"], LM["hem-r"])],
                 "sleeve-l": [("cuff-l", LM["cuff-out-l"], LM["cuff-in-l"])], "sleeve-r": [("cuff-r", LM["cuff-in-r"], LM["cuff-out-r"])]},
        "landmarks": LM,
        "scale": ("neck-l", "neck-r", 158.0, "neck-l -> neck-r = 158 mm (the straight kurta's agreed neck width: the same dress form)"),
        "settings": {"thetaDeg": {"top": 60, "skirt": 70, "sleeve-l": 70, "sleeve-r": 70}},
        "source_note": "silhouette/sources/torso-lehenga.png (765 x 1024, as received 2026-11-23), the sparkle mark patched, cut to "
                       "765 x 1020, resized to 1200 x 1600. Silhouette from the image (silhouette/views/_kit.py); seams, neckline, midriff "
                       "and landmarks measured on the source by Claude.",
        "trims": {
            "neck": {"order": 3, "type": "insertion", "group": "neck", "edge": "neck"},
            "top-hem": {"order": 3, "type": "edging", "group": "hem", "edge": "top-hem"},
            "cuff-l": {"order": 3, "type": "edging", "group": "cuffs", "edge": "cuff-l", "bandInMm": 100.0},
            "cuff-r": {"order": 3, "type": "edging", "group": "cuffs", "edge": "cuff-r", "bandInMm": 100.0},
            "hem": {"order": 3, "type": "edging", "group": "hem", "edge": "hem", "bandInMm": 100.0, "smoothMm": 40.0},
        },
    }


def measure():
    return _kit.measure(spec())[0]


if __name__ == "__main__":
    P, X = _kit.measure(spec())
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "review", "torso-lehenga")
    os.makedirs(out, exist_ok=True)
    _kit.check(P, X, os.path.join(out, "zones.png"))
