---
name: annotate-plate
description: Annotate one base image of the Bespoke Studio demo — measure garment edges, seams, gaps, objects in front and landmarks on the photo, and write zones.json plus a colour-coded annotate.png review image, with automatic checks. Use for step 4 of the make-plate pipeline, when a base image arrives without a usable annotation, or when an annotation must be corrected.
---

# Skill: annotate a base image

This skill makes the **curve data** of a plate: `zones.json`, the review image `annotate.png`, and the script `tools/annotate_<view>.py` that makes them again.
It is **step 4** of `plate.md`. The pipeline, acceptance and view specifications are in `plate.md`.

**Why we annotate ourselves:** in this demo, every annotated image made by an image-generation tool was a **new picture**. The form, the neck and the garment moved 8–60 px. Lines drawn on such an image do not fit the base. So the default is: **measure on the base, write the data, and let a person review an overlay.**

All paths are relative to `demo/`. Python 3 with Pillow only.

---

## 1. Inputs and outputs

| In | Out |
|---|---|
| `assets/plates/<plate>/source.png` | `base.jpg` (1200 × 1600), if the script also makes the base (close views) |
| The view type and its specification (`plate.md` §5) | `zones.json` (contract: `plate.md` step 4) |
| Optional: an annotated image from someone else | `annotate.png`: the colour code on `base.jpg` |
| | `tools/annotate_<view>.py`: measured points, data, drawing and checks in one script |

Templates: `tools/annotate_neck.py` (front view, shared seams, gaps), `tools/annotate_sleeve.py` (turned view, arm notch, `widthPx`, trim clipping).

---

## 2. Data rules

1. **One frame:** 1200 × 1600 px, 3:4, origin at the top left.
2. **Measure on `source.png`**, at full resolution. Convert to the plate frame only at the end, with `T()` (§5).
3. **Edge directions:** `top` and `bottom` go left → right. `left` and `right` go top → bottom (y must not decrease). "Left" and "right" are as seen in the image.
4. **Corners meet exactly.** Each grid corner is the same point in its two edges.
5. **A shared seam is one list.** Where a sleeve meets the front, both zones use **the same points**. Never sample a seam two times.
6. **Gaps stay gaps.** If the wall shows between two parts, the gap is outside every zone. Where the parts touch again, the upper zone (the sleeve) covers the lower one by 2 px.
7. **Objects in front are notches.** The bare mannequin arm, the stand or a hand in front of the garment is cut out of the outline of every zone that it covers.
8. **The outline is the real visible edge**, closed and with no self-crossing. It cuts the neck dip, the slit opening, the armhole curve, gaps and notches.
9. **A grid edge is a smooth grain line, not a cut.**
   - The front side edges must not bulge more than **5 %** of their length from their straight chord. The good plates have 2.6–3.9 %.
   - If a seam bulges more (the armhole in a turned view: 10.7 %), the grid edge runs **smoothly under the neighbouring zone**, and only the outline follows the seam.
   - The grid top **never** follows the neck dip.
   - Edges that bend on purpose are permitted: the shoulder line rising to the neck points, and sleeve edges along the arm.
10. **Trims are centre lines**, half the trim width inside the garment edge, and **inside their zone outline** from end to end. Width is in mm.
11. **Scale comes from an agreed value** (`plate.md` §5), never from the image alone.
12. **Only what is in the photo.** Stitches, seams and darts that you cannot see are not data.
13. **No text** in the base or in `annotate.png`.

---

## 3. Colour code (`annotate.png`, and annotated images that you receive)

| Item | Colour | Line |
|---|---|---|
| Front / body grid edges | Red `#E53935` | solid, 3 px |
| Real outline (neck dip, slit opening, notches) | Red `#E53935` | dashed |
| Sleeve and back-panel grid edges | Blue `#1E63E9` | solid, 3 px |
| Neck / cuff / hem / slit trim centre | Purple `#8E24AA` / Orange `#FB8C00` / Dark gold `#C79100` / Teal `#00897B` | solid |
| Stitch lines (top-stitch, bar tack) | Grey `#616161` | dashed, 2 px |
| Landmarks and grid corners | Black dot (r = 6), white ring | — |
| Scale | Green `#2E7D32` | between its two landmarks |

On a shared seam, draw red 2.5 px towards the body and blue 2.5 px towards the sleeve. The data keeps one exact line.

---

## 4. Choose the path

```
Annotated image received?
├── no ─────────────────────────────────────────────► Path A: measure and write (§5–§9)
└── yes → alignment test (plate.md step 2)
          ├── aligned (every box ≤ 2) ───────────────► Path B
          └── not aligned ───────────────────────────► Path A. Use the image only as a layout guide.
```

**Path B:** `python3 tools/extract_zones.py <annotate.png> <base.jpg> <zones.json> <preview.png>`. Review the preview (§9.2). If a trace jumped to another line, give that edge as straight or measured points in the script. Then run the checks of §9.1. Do **not** use `tools/fit_zones.py`.

---

## 5. Base and frame (in the script)

```python
X0, K = left_edge_of_crop, 1200 / crop_w        # square 2048 source: crop_w = 1536, K = 0.78125
base = patched.crop((X0, 0, X0 + crop_w, 2048)).resize((1200, 1600), Image.LANCZOS)

def T(pts):                                      # source px -> plate px
    return [[round((x - X0) * K, 1), round(y * K, 1)] for x, y in pts]
```

- Patch the sparkle mark before the crop (`plate.md` step 3).
- Write the crop and the patch in `zones.json` → `"source"`.

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

- **Gap** (wall between an arm and the body): the front edge follows the body side, and the sleeve edge follows the arm side. Both start at the underarm. Do not make the gap wider than it is in the photo.
- **Object in front** (mannequin arm below a cuff): measure both of its edges, and cut it out of the front outline as a notch that starts and ends on the cuff edge.
- **Hidden edge** (the body edge behind the sleeve): interpolate it with a few points, and write it in the script. The sleeve covers it, so only the grid smoothness matters there (rule 9).

### 6.6 Number checks before you write

| Check | Front view | Turned view |
|---|---|---|
| Left and right symmetric about the centre front | ±10 px | does not apply |
| Shoulder → neck length | 107 mm ± 10 % (torso value) | does not apply (foreshortened: 72 mm on the sleeve plate) |
| Neck width (neck-l → neck-r) | 158 mm (the neck view's scale line) | ≈ 158 × cos(turn) mm (sleeve plate: 140 mm against 135 mm at 31°) |
| Every point inside the image, on the garment side of its edge | yes | yes |

---

## 7. Write the data

Copy the template that is nearest to the view. Change only the measured lists and the zone recipes.

### 7.1 Seams: one list, two users

```python
seam_l = [(294, 644), (300, 720), ...]     # shoulder -> underarm, measured ONE time
front_left_outline_part = seam_l + body_l  # the outline follows the seam
sleeve_inner            = seam_l + slv_l   # the sleeve edge follows the same seam
```

### 7.2 Zone recipes

| Zone | grid top | grid left | grid right | grid bottom | outline |
|---|---|---|---|---|---|
| `front` | shoulder-l → neck-l → **straight** → neck-r → shoulder-r | **smooth** line: the seam if it bulges ≤ 5 %, otherwise a smooth line under the sleeve | same rule, right side | hem or border | shoulders + neck dip + seams + gaps + notches + bottom |
| `sleeve-l` | cap (border or outer edge → shoulder; torso: shoulder → underarm) | outer edge, or border | inner edge = `seam_l + slv_l` | cuff edge, or border | top + inner + bottom + outer |
| `sleeve-r` | mirror of `sleeve-l` | inner edge = `seam_r + slv_r` | outer edge, or border | cuff edge, or border | — |
| `back` (hem view) | slit top | back edge of the slit | side or border | back hem | — |

**`widthPx`:** if a zone's top or bottom edge is much shorter than the zone (a sleeve cap of 50 px on a sleeve 300 px wide), `make_plate.py` takes their mean and stretches the fabric. Set:

```python
zone["widthPx"] = polygon_area(outline) / ((length(left) + length(right)) / 2)
```

On the sleeve plate this changed the sleeve from 7.8 to 12.3 cm wide, and the squares became 2 cm.

### 7.3 Trims

```python
centre = offset(edge, (width_mm / 2) / mm_per_px, point_outside_the_garment)
centre = clip_extend(centre, zone_outline)   # drop end points outside the outline, extend each end inside
```

| Trim | Width | Centre from the edge | Direction |
|---|---|---|---|
| `neck` | 12 mm | 6 mm | neck-l → neck-r |
| `cuff-l`, `cuff-r` | 25 mm | 12.5 mm | left → right as seen |
| `hem` | 30 mm | 15 mm | left → right |
| `slit-*` | 8 mm | 4 mm | slit top → hem |

`clip_extend` is in `tools/annotate_sleeve.py`. It is needed where the trim meets a corner (neck corners, cuff corners).

### 7.4 Stitches, landmarks, scale, settings

- **Stitches:** `"stitches": {name: polyline}`. **Measure** their distance from the edge on a zoom crop. Draw only the part that is visible (sleeve plate: the neck top-stitch only on the near half).
- **Landmarks:** a dict of named plate-px points. The names are in `plate.md` §5. Add a second centre-front point (`cf-low` or `cf-hem`) when the centre front is visible.
- **Scale:** `mm_per_px = agreed_mm / math.dist(L[a], L[b])`, and `"scaleNote"`.
- **Settings:** `thetaDeg` for turned bodies and zones cut by the frame; `tuck` only for the torso.

---

## 8. Draw `annotate.png`

Colour code §3, on `base.jpg`:
- Shared seams drawn offset: red towards the body, blue towards the sleeve.
- Outline parts that are not grid edges (neck dip, notches, slit opening) in dashed red.
- No text.

---

## 9. Check and review

### 9.1 Automatic: in the script, all must pass

| Check | Method |
|---|---|
| Left / right edges go top → bottom | y never decreases |
| Corners meet | distance < 0.05 px |
| No crossing on shared seams | for each y: sleeve-l inner x ≤ front-left x + 1.6; sleeve-r inner x ≥ front-right x − 1.6 |
| Outlines simple | 0 self-crossings (segment-intersection test) |
| Trim centres inside their zone outlines | point-in-polygon on every point (after `clip_extend`) |
| **Front side edges smooth** | bulge from the chord ≤ 5 % (the same test as `plate_checks.py`) |
| Scale cross-checks | §6.6 |

### 9.2 Visual: 2× zoom crops of `annotate.png`

| Area | Look for |
|---|---|
| Neck | Red dashed **on** the edge; purple inside; grey on the real stitches |
| Shoulder points | Dot on the corner; shoulder line on the edge |
| Armholes | Red and blue side by side on the seam; no crossing |
| Underarms | The gap between red and blue, not wider than in the photo |
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
| A grid edge follows a bulging seam | S-curves in `check.png`; grain tilt > 10° | Smooth grid edge; the outline follows the seam (rule 9) |
| A short cap edge, no `widthPx` | Fabric stretched across the sleeve | `widthPx` (§7.2) |
| Trim ends outside the outline | Lace on the wall at a corner | `clip_extend` (§7.3) |
| A gap missed | Fabric on the wall under the arm | True-colour crop of every underarm (§6.5) |
| An object in front not cut out | Fabric on the mannequin arm | Notch (rule 7) |
| The gap drawn too wide | Too much wall; the sleeve looks thin | Keep the sleeve edge on the real arm edge |
| The grid top follows the neck dip | Grain bends near the neck | Straight top; the outline cuts the dip |
| Stitches guessed | Grey line beside the real stitches | Measure on a zoom crop |
| Points measured on the plate image | Error × 1.3 after the crop | Measure on `source.png`, then `T()` |
| A front-view check used on a turned view | False alarm on shoulder → neck | §6.6, turned column |
| Saturation scan trusted for the mannequin arm | Wrong arm edge | Zoom crops (§6.2) |
| Lines from a regenerated annotation | 8–60 px error everywhere | Path A |

---

## 11. As a Claude Code skill

The project skill `.claude/skills/annotate-plate/SKILL.md` loads this file. Change the procedure **here**, not in the skill.
