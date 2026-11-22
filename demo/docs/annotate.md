---
name: annotate-plate
description: Annotate one base image of the Bespoke Studio demo — measure garment edges, seams, gaps, objects in front and landmarks on the photo, and write them as typed edges, zones with fabric-frame specifications and trims in tools/annotate_<view>.py, with automatic checks and a colour-coded annotate.png review image. Use for step 4 of the make-plate pipeline, when a base image arrives without a usable annotation, or when an annotation must be corrected.
---

# Skill: annotate a base image

This skill makes the **measured data** of a plate: the script `tools/annotate_<view>.py` (the base crop, the measured points as typed edges, the zones with their fabric-frame specifications, the trims, the landmarks). `tools/make_plate.py` builds the plate from it, and draws the review image `annotate.png` (`--review`).
It is **step 4** of `plate.md`. The pipeline, acceptance and view specifications are in `plate.md`.

**Why we annotate ourselves:** in this demo, every annotated image made by an image-generation tool was a **new picture**. The form, the neck and the garment moved 8–60 px. Lines drawn on such an image do not fit the base. So the default is: **measure on the base, write the data, and let a person review an overlay.**

All paths are relative to `demo/`. Python 3 with Pillow only.

---

## 1. Inputs and outputs

| In | Out |
|---|---|
| `assets/plates/<plate>/source.png` | `tools/annotate_<view>.py`: `base(plate)` (the crop), `measure()` (the data below), the automatic checks when run alone |
| The view type and its specification (`plate.md` §5) | After `make_plate.py <plate> --review`: `base.jpg`, `plate.dat`, and `demo/review/<plate>/annotate.png` for the review |
| Optional: an annotated image from someone else | (a layout guide only, §4) |

Templates: `tools/annotate_neck.py` (front view, shared seams, gaps that close again), `tools/annotate_sleeve.py` (turned view, an arm notch as an occluder, an axis through measured centres), `tools/annotate_torso.py` (full front view, both sides measured, wall gaps at the cuffs), `tools/annotate_hem.py` (three pieces, slits, an anchor at a known distance).

---

## 2. Data rules

1. **One frame:** 1200 × 1600 px, 3:4, origin at the top left.
2. **Measure on `source.png`**, at full resolution. Convert to the plate frame only at the end, with `T()` (§5).
3. **Directions:** an edge's points run in one direction (top → bottom or left → right as named); a zone's outline is a chain of edges, each `+1` (as stored) or `-1` (reversed), that closes.
4. **Corners meet exactly:** consecutive edges of an outline share their end point (the validator checks it).
5. **A shared seam is one list.** Where two zones meet on a seam (an armhole; a sleeve lying on the body where a gap closes), both use **the same edge** (`"type": "seam", "zones": [a, b]`). Never sample a seam two times. The lower zone runs 6 px under the upper one automatically.
6. **Every edge has a type:** `free` (garment against wall, form or mannequin arm: the build snaps it to the photo), `seam` (one list, two zones), `frame` (the image border), `cut` (the live neck dip). A lower zone's run hidden under a later zone is a `seam` with `"under": <the later zone>`.
7. **Gaps stay gaps.** If the wall shows between two parts, both edges are `free` and the gap is outside every zone. Measure where the wall really shows: a white fold is garment, not wall.
8. **Objects in front are notches and occluders.** The bare mannequin arm or the stand in front of the garment is cut out of the outline, and listed as an occluder (a chain of its edges): an edging lace does not hang over it.
9. **Each zone has a fabric frame specification** (`"frame"`): `axis` (two landmarks for a straight centre front; or measured centre points through a bend; or `"midline"`), `anchor` (`{"line": ["neck-l", "neck-r"]}`, `{"point": "shoulder"}`, or `{"point": "slit-top", "vMm": ...}` at a known distance), optional `sagEdge` (the hem or the cuff: a weft line), `skipTop` (a sleeve cap), `axisDegree`. The build fits the half widths and the sag. The outline alone decides where the fabric shows; no grid edges.
10. **Trims are specifications:** `edge` (the garment edge the lace is sewn to), `type` (`insertion`: the lace lies from the edge inward; `edging`: an edging lace's decorative edge hangs past it), optional anchors `from` / `to` (landmarks: the trim's line runs between their nearest points on the edge), `anchor` (where the motif sits: `cf`, the default, the frame's u = 0; or `from` / `to`, a whole motif at that end) and `cut` (the ends that are real, square ends: the slit top). No width and no offset: the lace's own width is used (StepA extension). The build derives the line (`derive_trims`).
11. **Scale comes from an agreed value** (`plate.md` §5), never from the image alone.
12. **Only what is in the photo.** Stitches, seams and darts that you cannot see are not data. A seam or a cuff fold may be made smooth by a fit through its measured points (the torso's armholes and cuffs).
13. **No text** in the base.

---

## 3. Colour code (`annotate.png`, and annotated images that you receive)

| Item | Colour | Line |
|---|---|---|
| Front / body edges | Red `#E53935` | solid, 2 px |
| The neck cut (`cut`) | Red `#E53935` | dashed |
| Sleeve and back-panel edges | Blue `#1E63E9` | solid, 2 px |
| A fabric axis | Green `#2E7D32` | dashed, 1 px |
| Neck / cuff / hem / slit trim centre | Purple `#8E24AA` / Orange `#FB8C00` / Dark gold `#C79100` / Teal `#00897B` | solid |
| Stitch lines (top-stitch, bar tack) | Grey `#616161` | dashed, 2 px |
| Landmarks | Black dot, white ring | — |

On a shared seam, draw red 2.5 px towards the body and blue 2.5 px towards the sleeve. The data keeps one exact line.

---

## 4. Choose the path

```
Annotated image received?
├── no ─────────────────────────────────────────────► Path A: measure and write (§5–§9)
└── yes → alignment test (plate.md step 2)
          └── either way ────────────────────────────► Path A. Use the image only as a layout guide.
```

The traced torso plate of 2026-11-18 (`extract_zones.py`, one affine per zone, the left side mirrored) was replaced by a measured one in StepA step 2: a received annotation is never the data.

---

## 5. Base and frame (in the script)

```python
X0, K = left_edge_of_crop, 1200 / crop_w        # square 2048 source: crop_w = 1536, K = 0.78125
base = patched.crop((X0, 0, X0 + crop_w, 2048)).resize((1200, 1600), Image.LANCZOS)

def T(pts):                                      # source px -> plate px
    return [[round((x - X0) * K, 1), round(y * K, 1)] for x, y in pts]
```

- Patch the sparkle mark before the crop (`plate.md` step 3).
- Write the crop and the patch in the data's `"source"` text.

---

## 6. Measure

### 6.1 Gridded crops: the main instrument

```sh
python3 tools/gridcrop.py <source.png> <out.png> x0 y0 x1 y1 [step=50] [contrast=2.2] [scale=1.0]
```

- Labels are in **source px**, so read the points directly.
- **Contrast 2.2–2.4:** seams, stitches, fold lines.
- **Contrast 1.0 (true colour):** is a dark area a **gap** (wall: warm tan) or a **fold** (garment: grey-white)? Is it the **mannequin arm** (linen beige, with texture)?
- **Zoom (scale 2.4–3.6, step 20–25):** corners, the shoulder point, the edges of the mannequin arm, stitches.
- Read 6–12 points along each line, more on curves. If two crops give different values for the same edge, cut a third, closer crop. Do not take the mean.

### 6.2 Automatic scans: only as a start

| Scan | Use | Limit |
|---|---|---|
| Garment mask `S < 22 and V > 170` (HSV, 5 px median) | silhouette, neck opening | Fails in shadow. Mirror from the lit side, and write `"mirrored"`. |
| Colour distance to a wall sample on the same row (blur 1.5, distance > 38) | silhouette against the wall | Only where the wall is behind the edge |
| Saturation | mannequin arm against the garment | **Unreliable:** shaded garment is as saturated as the linen arm. Confirm on zoom crops. |

Always confirm a scan on a gridded crop before you use its points.

### 6.3 Neck opening and centre front

For each row from the neck corners down to below the dip, find the gap in the garment mask around the centre:
- **Centre front:** the middle of the gap, the same (±3 px) on every row. In a turned view, there is no symmetric gap. Use the neck dip and the form's centre seam.
- **`cf-neck`:** the lowest row with a gap.
- **Neck corners:** the top of the opening. Confirm on a zoom crop.

### 6.4 What to measure for each view

| View | Points and lines |
|---|---|
| All | neck edge and corners; shoulder points; armhole seams (shoulder → underarm); underarm points |
| Torso | + body sides to the hem; sleeve outer edges; cuff edges; slit tops; hem; hem corners |
| Neck | + body edges below the underarms to the border; the neck top-stitch (its distance from the edge) |
| Sleeve | + cap; outer edge (with the elbow corner); inner edge; cuff edge and cuff top-stitch; **mannequin arm** edges below the cuff; the turned bodice silhouette |
| Hem | + slit front and back edges; slit top; bar tack; hem lines of the front and back panels; hem top-stitch; the stand |

### 6.5 Gaps and objects in front

- **Gap** (wall between an arm and the body): the front edge follows the body side, and the sleeve edge follows the arm side, both `free`. They start where the wall really shows (a white fold above it is garment: the front and the sleeve share a seam down to there), and where the gap closes again the sleeve lying on the body is one shared seam. Do not make the gap wider than it is in the photo.
- **Object in front** (mannequin arm below a cuff): measure both of its edges, cut it out of the front outline as a notch, and list it as an occluder (a chain of those edges).
- **Hidden edge** (the body edge behind the sleeve): where the sleeve lies on the body, the body ends on the sleeve's edge (a shared seam). Where the body runs on under the sleeve out of sight, write its run as a `seam` with `"under"`: only its ends matter.

### 6.6 Number checks before you write

| Check | Front view | Turned view |
|---|---|---|
| Left and right symmetric about the centre front | ±10 px | does not apply |
| Shoulder → neck length | 107 mm ± 10 % (torso value) | does not apply (foreshortened: 72 mm on the sleeve plate) |
| Neck width (neck-l → neck-r) | 158 mm (the neck view's scale line) | ≈ 158 × cos(turn) mm (sleeve plate: 140 mm against 135 mm at 31°) |
| Every point inside the image, on the garment side of its edge | yes | yes |

---

## 7. Write the data

Copy the template that is nearest to the view. Change only the measured lists, the edges, the zones and the trims.

### 7.1 Edges: one list, typed

```python
seam_l = [(294, 644), (300, 720), ...]                  # shoulder -> underarm, measured ONE time
edges = {
    "armhole-l": {"type": "seam", "zones": ["front", "sleeve-l"], "points": T(seam_l)},
    "body-l":    {"type": "free", "points": T(seam_l[-1:] + body_l)},     # the body side of the wall gap
    "neck":      {"type": "cut",  "points": T(neck_edge)},
    "front-bottom": {"type": "frame", "points": T([(405, 2048), (1650, 2048)])},
}
```

### 7.2 Zones: an outline chain and a frame

```python
zones = {
    "front": {"order": 1,
              "frame": {"axis": ["cf-neck", "cf-low"], "anchor": {"line": ["neck-l", "neck-r"]}},
              "outline": [["shoulder-l", 1], ["neck", 1], ["shoulder-r", 1], ["armhole-r", 1], ["body-r", 1],
                          ["front-bottom", -1], ["body-l", -1], ["armhole-l", -1]]},
    "sleeve-l": {"order": 2, "frame": {"axis": "midline", "anchor": {"point": "shoulder-l"}, "sagEdge": "cuff-l", "skipTop": 0.15},
                 "outline": [...]},
}
```

| Zone | Axis | Anchor |
|---|---|---|
| `front` (front view) | the centre front: `cf-neck` → `cf-low` / `hem-cf` | the neck-point line (`neck-l`, `neck-r`) |
| `front` (turned view) | a vertical line halfway between the armhole and the far side (or the frame) | the neck-point line |
| `sleeve-*` | `"midline"` for a straight sleeve; measured centres (upper arm, elbow, cuff) for a bent one | the shoulder point |
| `back`, `back-l` (hem view) | `"midline"` | the slit top at its distance from the neck-point line (`vMm`) |

### 7.3 Trims

```python
trims = {"hem": {"order": 3, "type": "edging", "edge": "hem", "from": "hem-l", "to": "hem-r"},
         "slit-l": {"order": 3, "type": "insertion", "edge": "body-l", "from": "slit-l", "to": "hem-l", "anchor": "to", "cut": ["from"]}}
```

| Trim | Width | Offset from its edge | Anchors |
|---|---|---|---|
| `neck` | 12 mm | 6 mm | `neck-l` → `neck-r` |
| `cuff-l`, `cuff-r` | 25 mm | 12.5 mm | — (inside the sleeve) |
| `hem`, `hem-bl`, `hem-br` | 30 mm | 15 mm | the hem corners |
| `slit-*` | 8 mm | 4 mm | the slit top → the hem corner |

### 7.4 Stitches, landmarks, scale, settings

- **Stitches:** `"stitches": {name: polyline}`. **Measure** their distance from the edge on a zoom crop. Draw only the part that is visible.
- **Landmarks:** a dict of named plate-px points (`plate.md` §5). A corner landmark that is an edge's end follows the snap; `cf-neck` is put on the snapped neck edge by the build.
- **Scale:** `mm_per_px = agreed_mm / math.dist(L[a], L[b])`, and `"scaleNote"`.
- **Settings:** `thetaDeg` for turned bodies and zones cut by the frame.

---

## 8. The review image `annotate.png`

`make_plate.py <plate> --review` draws it from the plate (colour code §3): free edges in the zone's colour (the front red, the others blue), a seam as red and blue side by side, the neck cut dashed, each zone's fabric axis dashed green, trims, stitches, landmarks. It also writes `check.png` (a 2 cm checker on the fabric) and the edge crops.

---

## 9. Check and review

### 9.1 Automatic: in the script, all must pass

| Check | Method |
|---|---|
| Side edges go top → bottom | y never decreases |
| Gaps not crossed | where a sleeve and the body face a wall gap: the sleeve's edge stays on its side (an overlap ≤ 1.6 px) |
| Outlines simple | 0 self-crossings (segment-intersection test) |
| The plate validates (`make_plate.py` runs `platedat.validate`) | every edge typed; chains closed; a seam used by exactly two zones (or one lower zone, `under`); frame points on the border |
| Scale cross-checks | §6.6 |
| After the build (`plate.md` step 6) | trims inside their zones and at their offset; the frame rules; closure |

### 9.2 Visual: 2× zoom crops of `annotate.png`

| Area | Look for |
|---|---|
| Neck | Red dashed **on** the edge; purple inside, ending below the corner anchors; grey on the real stitches |
| Shoulder points | Dot on the corner; shoulder line on the edge |
| Armholes | Red and blue side by side on the seam; no crossing |
| Underarms | The gap between red and blue, not wider than in the photo; the underarm landmark at the top of the underarm fold |
| Axes | Green dashed down the middle of each piece, along its grain |
| Cuffs | Edge on the real edge; orange inside; grey on the real stitch |
| Notches | Dashed red on the edges of the mannequin arm or the stand |
| Hem, slit | Edges, trims, bar tack on the real features |

### 9.3 A person reviews

Show `annotate.png` and the zoom crops to the owner of the look. Typical feedback in this demo: "the blue is too far from the red at the left underarm". Correct the measured lists, run the script, and review again. Then continue with `plate.md` step 5.

---

## 10. Common errors

| Error | Seen as | Correct |
|---|---|---|
| A seam sampled two times | Red and blue cross; zigzag | One list (rule 5) |
| An axis off the middle of a piece, or through a notch | Columns of squares bend or tilt (frame grain > 3°) | Axis through measured centres (rule 9) |
| A shaded edge against a light wall read too far out | Fabric on the wall along a sleeve | Read it again on a 2.5–3× crop; the snap keeps a weak edge |
| Trim past its corner | Lace runs up the steep end of an edge | `from` / `to` anchors (rule 10) |
| A gap missed | Fabric on the wall under the arm | True-colour crop of every underarm (§6.5) |
| An object in front not cut out | Fabric on the mannequin arm | Notch (rule 7) |
| The gap drawn too wide | Too much wall; the sleeve looks thin | Keep the sleeve edge on the real arm edge |
| Stitches guessed | Grey line beside the real stitches | Measure on a zoom crop |
| Points measured on the plate image | Error × 1.3 after the crop | Measure on `source.png`, then `T()` |
| A front-view check used on a turned view | False alarm on shoulder → neck | §6.6, turned column |
| Saturation scan trusted for the mannequin arm | Wrong arm edge | Zoom crops (§6.2) |
| Lines from a regenerated annotation | 8–60 px error everywhere | Path A |

---

## 11. As a Claude Code skill

The project skill `.claude/skills/annotate-plate/SKILL.md` loads this file. Change the procedure **here**, not in the skill.
