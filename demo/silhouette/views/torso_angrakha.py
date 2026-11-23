"""The full-torso view of the angrakha wrap dress (torso-angrakha): measured on source.png (765 x 1024), 2026-11-23.

The silhouette is read from the image (silhouette/views/_kit.py: the background grown from the wall, the form excluded above the
measured neckline); the seams, the neckline and the landmarks were read by eye on gridded crops of source.png (silhouette/measure/
gridcrop.py, x2.2 .. x5). Source px; the plate is the 765 x 1020 crop, x 1.5686 -> 1200 x 1600.
Zones (draw order): front (the under panel, right of the wrap edge, 1), skirt (below the empire waist, 2), wrap (the over panel, 3),
sleeve-l, sleeve-r (4; the left sleeve lies on the skirt below the waist, the right one on the body all the way). Distinct orders: every
seam has a lower zone (its under-strip closes the hairline). The two front panels share one bodice frame (bodyOf).
A thin wall gap shows between the left sleeve and the body, y 285 .. 355 (a background seed there).
As a module (make_plate.py): base(path), measure(). Run alone: the kit's checks, and review/torso-angrakha/zones.png.
"""
import os, sys
sys.path[:0] = [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), d) for d in ("pipeline", "views")]
import _kit

PATCHES = [((640, 898, 684, 945), -60), ((695, 950, 742, 1000), -60)]      # the two sparkle marks on the floor, from 60 px left

NECK_L = [(337, 143), (338, 148), (340, 153), (342, 160), (347, 170), (352, 180), (358, 190), (364, 200), (370, 210), (377, 217),
          (383, 220)]                                                                                                     # neck-l -> V (x6 crop)
NECK_R = [(383, 220), (392, 210), (400, 200), (406, 190), (412, 180), (418, 170), (424, 160), (428, 150), (431, 143)]   # V -> neck-r
SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sources", "torso-angrakha.png")
# the neckline points refined along their rows to the photo's garment / form edge (silhouette/views/_kit.py refine_x); the corners stay
NECK_L = _kit.refine_x(SRC, NECK_L, keep=[NECK_L[0], NECK_L[-2], NECK_L[-1]])   # the point just above the V stays
NECK_R = _kit.refine_x(SRC, NECK_R, keep=[NECK_R[0], NECK_R[-1]])
FORM = [(326, 0), (445, 0), (445, 140)] + NECK_R[::-1] + NECK_L[::-1][1:] + [(326, 140)]                               # above the neckline

SEAMS = {
    "armhole-l": [(274, 150), (277, 163), (280, 180), (282, 200), (284, 230), (285, 260), (285, 280), (279, 305)],     # into the wall gap
    "sleeve-skirt-l": [(279, 350), (290, 358), (286, 400), (280, 440), (272, 480), (264, 503), (246, 510), (226, 524)],   # gap -> below the cuff, into the wall
    "waist": [(279, 350), (293, 356), (330, 357), (383, 357), (440, 354), (470, 351), (485, 352)],                    # empire waist
    "wrap": [(383, 215), (383, 220), (400, 233), (420, 251), (440, 272), (458, 298), (463, 312), (472, 325), (484, 338)],   # the wrap edge
    "armhole-r": [(495, 150), (492, 165), (489, 190), (487, 215), (486, 240), (485, 256), (479, 280), (481, 320), (483, 360),
                  (487, 400), (492, 440), (498, 480), (503, 510), (512, 525)],                                         # + the sleeve's inner edge
}
LM = {"neck-l": (337, 143), "neck-r": (431, 143), "cf-neck": (383, 220), "shoulder-l": (277, 163), "shoulder-r": (492, 165),
      "underarm-l": (287, 280), "underarm-r": (485, 256), "waist-l": (292, 356), "waist-r": (482, 352), "waist-cf": (383, 357),
      "hem-l": (223, 826), "hem-r": (544, 820), "hem-cf": (383, 845), "cuff-out-l": (198, 497), "cuff-in-l": (250, 505),
      "cuff-out-r": (566, 497), "cuff-in-r": (507, 513), "tie": (463, 312)}


def base(path=SRC):
    return _kit.base(path, PATCHES)


def spec():
    K, mm = _kit.K, 158.0 / ((LM["neck-r"][0] - LM["neck-l"][0]) * _kit.K)
    v_waist = round((LM["waist-cf"][1] - LM["neck-l"][1]) * K * mm, 1)       # the waist's v below the neck-point line (mm)
    front = {"axis": ["cf-neck", "waist-cf"], "anchor": {"line": ["neck-l", "neck-r"]}, "bodyOf": ["wrap", "front"]}   # one bodice
    return {
        "path": SRC, "patches": PATCHES, "view": "torso", "variant": "angrakha",
        "extra_seeds": [(281, 320)],                                           # the wall gap between the left sleeve and the body
        "bg_barriers": [[(262, 357), (296, 357)]],                              # the gap ends at the waist: the shaded skirt below is garment
        "exclude": [FORM, [(0, 856), (765, 856), (765, 1020), (0, 1020)]],      # the form above the neckline; the floor and the stand
        "seams": SEAMS,
        "zones": {
            "wrap": {"seed": (340, 280), "order": 3, "frame": front},
            "front": {"seed": (455, 215), "order": 1, "frame": front},
            "skirt": {"seed": (380, 600), "order": 2, "frame": {"axis": ["waist-cf", "hem-cf"], "anchor": {"point": "waist-cf", "vMm": v_waist}, "sagEdge": "hem"}},
            "sleeve-l": {"seed": (235, 350), "order": 4, "frame": {"axis": "midline", "anchor": {"point": "shoulder-l"}, "sagEdge": "cuff-l", "skipTop": 0.15}},
            "sleeve-r": {"seed": (525, 380), "order": 4, "frame": {"axis": "midline", "anchor": {"point": "shoulder-r"}, "sagEdge": "cuff-r", "skipTop": 0.15}},
        },
        "cuts": {"wrap": [("neck", NECK_L[0], NECK_L[-1])], "front": [("neck-v", NECK_R[0], NECK_R[-1])],
                 "sleeve-l": [("cuff-l", LM["cuff-out-l"], LM["cuff-in-l"])], "sleeve-r": [("cuff-r", LM["cuff-in-r"], LM["cuff-out-r"])],
                 "skirt": [("hem", LM["hem-l"], LM["hem-r"])]},
        "landmarks": LM,
        "scale": ("neck-l", "neck-r", 158.0, "neck-l -> neck-r = 158 mm (the straight kurta's agreed neck width: the same dress form)"),
        "settings": {"thetaDeg": {"wrap": 60, "front": 60, "skirt": 70, "sleeve-l": 70, "sleeve-r": 70}},
        "source_note": "silhouette/sources/torso-angrakha.png (765 x 1024, as received 2026-11-23), two sparkle marks patched, cut to "
                       "765 x 1020, resized to 1200 x 1600. Silhouette from the image (silhouette/views/_kit.py); seams, neckline and "
                       "landmarks measured on the source by Claude. Intake: 0.1 % of the garment over luminance 250 (owner's decision).",
        "trims": {
            "neck": {"order": 3, "type": "insertion", "group": "neck", "edge": "neck"},
            "neck-v": {"order": 3, "type": "insertion", "group": "neck", "edge": "neck-v"},
            "wrap": {"order": 3, "type": "insertion", "group": "neck", "edge": "seam-front-wrap"},
            "cuff-l": {"order": 3, "type": "edging", "group": "cuffs", "edge": "cuff-l", "bandInMm": 100.0},
            "cuff-r": {"order": 3, "type": "edging", "group": "cuffs", "edge": "cuff-r", "bandInMm": 100.0},
            "hem": {"order": 3, "type": "edging", "group": "hem", "edge": "hem", "bandInMm": 100.0, "smoothMm": 40.0},   # a gathered hem: the lace follows its mean line
        },
    }


def measure():
    return _kit.measure(spec())[0]


if __name__ == "__main__":
    P, X = _kit.measure(spec())
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "review", "torso-angrakha")
    os.makedirs(out, exist_ok=True)
    _kit.check(P, X, os.path.join(out, "zones.png"))
