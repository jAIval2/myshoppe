"""The anarkali with short puff sleeves (torso-anarkali-puff): the owner's edit of torso-anarkali.png (2026-11-24, "change only both
sleeves into short puff sleeves ..."). The edit lines up with its base (0 px at 7 landmarks; the body differs by 2 / 255), so this
view takes the base's measurements (torso_anarkali.py) and measures only what the edit changed:
  - the puffs: each ends in a band (y 645 .. 690); the armhole seams run down the puffs' inner creases to the band's inner corner;
  - the bare linen arms below the puffs (not garment: excluded);
  - the body's sides that the long sleeves hid. Left: per row, the first 3 px with chroma >= 31 going left from the body (the wall in
    the gap, or the arm); right: the arm's left edge (light cloth against the dark linen), read on a x1.5 crop and checked against a
    per-row trace where it hit the arm (y 785 .. 1115), then the base's skirt edge below the arm (the same in both images).
The edit also lit the strip the long sleeve had shaded on the right (the base's gap): here the cloth reaches the arm.
Source px; the plate is the 1792 x 2389 crop, x 0.6696 -> 1200 x 1600.
"""
import os, sys
sys.path[:0] = [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), d) for d in ("pipeline", "views")]
import _kit
import torso_anarkali as A

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sources", "torso-anarkali-puff.png")
PATCHES = A.PATCHES

# the body's left side below the band (wall in the gap, then the arm beside and behind the skirt)
BODY_L = [(715, 695), (716, 710), (717, 725), (718, 740), (717, 755), (713, 770), (710, 785), (706, 800), (700, 815), (696, 830),
          (692, 845), (688, 860), (684, 875), (681, 890), (678, 905), (674, 920), (670, 935), (666, 950), (662, 965), (660, 980),
          (657, 995), (654, 1010), (651, 1025), (646, 1040), (645, 1055), (644, 1070), (640, 1085), (637, 1100), (631, 1115),
          (627, 1130), (624, 1145), (621, 1160)]
ARM_L = [(480, 692), (712, 692)] + BODY_L + [(621, 1166), (480, 1166)]
# the body's right side below the band: the arm's left edge, then the skirt against the wall in shadow down to the base's edge
BODY_R = [(1118, 695), (1121, 710), (1124, 740), (1127, 770), (1129, 785), (1133, 815), (1135, 830), (1137, 850), (1140, 875),
          (1142, 890), (1145, 905), (1148, 920), (1152, 935), (1154, 950), (1157, 965), (1159, 980), (1160, 995), (1160, 1020),
          (1160, 1050), (1160, 1080), (1160, 1110), (1162, 1125)]
BODY_R_WEAK = BODY_R[-7:]                             # y 995 .. 1125: shaded cloth against the wall in shadow (the snap keeps these)
RIGHT = BODY_R + A.EDGE_R + A.HEM_R
RIGHT_WALL = RIGHT + [(1000, 1966), (1000, 2110), (1792, 2110), (1792, 692), (1125, 692)]
BARRIER_R = A.offset(RIGHT, 2.0)

SEAMS = {
    # the shoulder point, down the puff's inner crease to the band's inner corner, then into the wall in the gap below it
    "armhole-l": [(664, 322), (674, 334), (677, 370), (679, 400), (680, 440), (681, 480), (683, 520), (686, 555), (694, 600),
                  (700, 640), (703, 660), (705, 688), (705, 700)],
    # the empire seam, from the wall at the left to the arm at the right
    "waist": [(705, 705), (716, 705), (760, 708), (800, 711), (850, 712), (900, 712), (950, 711), (1000, 709), (1050, 706),
              (1086, 704), (1124, 706)],
    # the shoulder point, down the puff's inner crease, the band's inner end, into the arm
    "armhole-r": [(1140, 320), (1126, 334), (1122, 370), (1118, 420), (1112, 470), (1106, 520), (1102, 545), (1098, 600),
                  (1094, 640), (1100, 665), (1112, 690), (1120, 697)],
}
LM = dict(A.LM)
LM.update({"underarm-l": (703, 660), "underarm-r": (1100, 665), "waist-l": (716, 705), "waist-r": (1120, 706),
           "cuff-out-l": (559, 662), "cuff-in-l": (689, 683), "cuff-out-r": (1226, 667), "cuff-in-r": (1118, 693)})   # the band edges' ends


def base(path=SRC):
    _kit.fit_to(path)
    return _kit.base(path, PATCHES)


def spec():
    _kit.fit_to(SRC)
    s = A.spec()
    s.update({
        "path": SRC, "patches": PATCHES, "variant": "anarkali",
        "exclude": [A.FORM, ARM_L, RIGHT_WALL, A.STAND, A.FLOOR],
        "bg_barriers": [BARRIER_R] + list(SEAMS.values()),
        "measured": [A.EDGE_R, A.HEM_R_WEAK, BODY_R_WEAK],
        "seams": SEAMS,
        "landmarks": LM,
        "source_note": "silhouette/sources/torso-anarkali-puff.png (1792 x 2400, the owner's edit of torso-anarkali.png, 2026-11-24: short "
                       "puff sleeves), the sparkle mark patched, cut to 1792 x 2389, resized to 1200 x 1600. The base's measurements "
                       "(torso_anarkali.py) where the edit did not change the garment; the puffs, the arms and the body's sides measured "
                       "on this source by Claude.",
    })
    s["zones"] = {k: dict(v) for k, v in s["zones"].items()}
    s["zones"]["sleeve-l"]["seed"] = (620, 500)
    s["zones"]["sleeve-r"]["seed"] = (1160, 500)
    for z in ("sleeve-l", "sleeve-r"):
        s["zones"][z]["frame"] = dict(s["zones"][z]["frame"], skipTop=0.25)
    s["cuts"] = dict(s["cuts"])
    s["cuts"]["sleeve-l"] = [("cuff-l", LM["cuff-out-l"], LM["cuff-in-l"])]
    s["cuts"]["sleeve-r"] = [("cuff-r", LM["cuff-in-r"], LM["cuff-out-r"])]
    # no cuff lace: the puff's band is about 20 mm deep, the cuff laces 25 mm wide (a 30 mm field folded inside the gathered puff:
    # 13 .. 17 seams of s, 2026-11-24). A narrow band lace is later work.
    s["trims"] = {k: v for k, v in s["trims"].items() if k not in ("cuff-l", "cuff-r")}
    return s


def measure():
    _kit.fit_to(SRC)
    return _kit.measure(spec())[0]


if __name__ == "__main__":
    P, X = _kit.measure(spec())
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "review", "torso-anarkali-puff")
    os.makedirs(out, exist_ok=True)
    _kit.check(P, X, os.path.join(out, "zones.png"))
