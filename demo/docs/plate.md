---
name: make-plate
description: Make a garment plate (base, zones, id/uv/uv_trim/shade maps, checker) for one fixed view of the Bespoke Studio demo — torso, neckline, sleeve or hem — from one base image. Use when a new base image arrives for a view, or when a plate must be rebuilt or checked.
---

# Skill: make a plate

A **plate** is one fixed view of one garment variant. It is the input of `testing.html`.
This file is the **pipeline**: intake, base, annotation (→ `annotate.md`), plate, acceptance, record.
Background: `render.md` (method), `DedhD.md` (why plates, how many).

All paths are relative to `demo/`. All tools use Python 3 with Pillow only.

| File | Job |
|---|---|
| `plate.md` (this file) | The pipeline, acceptance checks, view specifications, plate-level failures |
| `annotate.md` | Measuring the photo, data rules, colour code, `zones.json`, review |

---

## 1. Output

One folder for each plate: `assets/plates/<view>-<variant>/`, for example `assets/plates/hem-straight/`.

| File | Made in | Ships to the page |
|---|---|---|
| `source.png` | step 1 (the image as received) | no |
| `base.jpg` | step 3 | yes |
| `zones.json`, `annotate.png` | step 4 (`annotate.md`) | no |
| `id.png`, `uv.png`, `uv_trim.png`, `shade.png`, `plate.json` | step 5, `tools/make_plate.py` | yes |
| `check.png` | step 5 (review image) | no |
| `tools/annotate_<view>.py` | step 4 | no (it makes the plate again) |

The plate is **done** only when step 6 passes completely, **and** a person has looked at `annotate.png` and `check.png`.

---

## 2. Pipeline

```
1 Intake ──► 2 Alignment test ──► 3 Base ──► 4 Annotate ──► 5 Make plate ──► 6 Accept ──► 7 Record
  (reject?)    (only if an          1200×1600   annotate.md     make_plate.py    plate_checks.py   render.md §11
                annotation came)                                                 + person
```

| Tool | Step | Job |
|---|---|---|
| `tools/make_base.py` | 3 | Torso only: sparkle patch, 3:4 cut, resize |
| `tools/gridcrop.py` | 4 | Gridded crops of `source.png` for measuring |
| `tools/annotate_<view>.py` | 3–4 | Base crop, measured points, `zones.json`, `annotate.png`, automatic checks |
| `tools/extract_zones.py` | 4 | Only for an **aligned** colour annotation (Path B in `annotate.md`) |
| `tools/make_plate.py` | 5 | The plate maps and `check.png` |
| `tools/plate_checks.py` | 6 | Acceptance numbers, PASS / FAIL |
| `tools/fit_zones.py` | — | Legacy: the torso only. Do not use for new plates. |

---

## 3. Steps

### Step 1: Intake check

Copy the image as received to `source.png`. Then **reject** it, and ask for a new one, if:

- [ ] It is **not the same garment** as the other views. The straight kurta is plain white, smooth matte cotton, with a high round neck (no slit, no placket), full sleeves, calf length and side slits. No embroidery, lace or print.
- [ ] It is **not the same scene**: natural-linen dress form, dark wood knob and stand, warm beige wall, soft light from the upper left.
- [ ] **Garment highlights are clipped:** the maximum luminance in the garment must be ≤ 250.
- [ ] The framing does not match the view (§5).

**Not** a reason to reject (fix them in step 3):
- A square image, or a wrong aspect ratio.
- A sparkle mark or watermark, on the wall **or on the garment**.

### Step 2: Alignment test (only if an annotated image came with the base)

```python
from PIL import Image, ImageChops, ImageStat
a = Image.open("annotated.png").convert("RGB"); b = Image.open("source.png").convert("RGB")
assert a.size == b.size
for box in [(40, 40, 400, 300), (900, 60, 1140, 220), (820, 380, 1100, 470)]:   # wall, knob, form neck
    print(box, sum(ImageStat.Stat(ImageChops.difference(a.crop(box), b.crop(box))).mean) / 3)
```

- Every box **≤ 2**: aligned. Use Path B in `annotate.md`.
- Any box **> 5**, or the form neck different: **regenerated**. In this demo, **every** tool-made annotation was regenerated (8–60 px off). Use Path A in `annotate.md`, and use the received image only as a layout guide.

### Step 3: Make `base.jpg` (1200 × 1600)

- **Torso:** `python3 tools/make_base.py <source> assets/plates/<plate>/base.jpg /tmp/corner.png`.
- **Close views:** in `tools/annotate_<view>.py`:
  1. **Sparkle mark:** cover it with a feathered patch from the **same rows**, 150–200 px to the side. Take wall for a mark on the wall, and garment for a mark on the garment.
  2. **Crop to 3:4** around the subject. For the front views, centre on the centre-front line. If the garment runs off one side, put the crop against that side. For a 2048 × 2048 source: crop width 1536, factor `K` = 0.78125.
  3. Resize to 1200 × 1600 with LANCZOS, and save as JPEG quality 94, no chroma subsampling.

### Step 4: Annotate

Follow **`annotate.md`**. Result: `zones.json` + `annotate.png` + `tools/annotate_<view>.py`, with its automatic checks passing.

`zones.json` contract (what `make_plate.py` reads):

| Key | Required | Contents |
|---|---|---|
| `base`, `viewBox`, `mmPerPx` | yes | `"base.jpg"`, `[1200, 1600]`, scale |
| `zones.<name>.order`, `.grid.{top,left,right,bottom}`, `.outline` | yes | names: `front`, `sleeve-l`, `sleeve-r` (`back` needs a tool change, §4) |
| `trims.<name>.{order, widthMm, centre}` | if trims | names: `neck`, `cuff-l`, `cuff-r`, `hem`, `slit-l`, `slit-r` |
| `zones.<name>.widthPx` | optional | fabric width of a zone whose top/bottom edges are much shorter than the zone (sleeve cap) |
| `uvRangeCm` | optional | UV range of the 12-bit packing, default 128. **Use a smaller range (32) when the scale is finer than about 0.3 mm/px**, or neighbouring pixels share a UV value. It must stay above the largest zone size and trim length in cm. |
| `thetaDeg` | optional | cylinder angles; defaults front 60°, sleeves 70° |
| `tuck` | optional | the torso only (fit error) |
| `landmarks`, `stitches`, `scaleNote`, `source` | recommended | for review and later work |

### Step 5: Make the plate

```sh
python3 tools/make_plate.py assets/plates/<plate>          # 5–12 s
```

If you changed `make_plate.py`, rebuild **every other plate** into a scratch copy and `cmp` the shipped maps. They must be **byte-identical**.

### Step 6: Acceptance

```sh
python3 tools/plate_checks.py assets/plates/<plate>
```

| Check (`plate_checks.py`) | Pass | Values of the good plates (torso / neck) |
|---|---|---|
| Front side-edge bulge from its chord | ≤ 5 % | 3.9 % / 2.6 % |
| Front grain tilt, 95 % of points | ≤ 10° | 10.0° / 8.7° |
| UV rate (fabric cm per px ÷ face-on rate), each zone, U and V | 0.8–1.6 | 0.94–1.58 |
| Block ratio | ≤ 0.05 | 0.027 / 0.029 |
| Plate data (`id` + `uv` + `uv_trim` + `shade`) | ≤ 1.0 MB | 396 / 668 KB |

Then look at `check.png` (whole, and 2× zooms of every seam, underarm, cuff, slit):

- [ ] Squares ≈ 2 cm: the same real size as in the other views.
- [ ] Columns of squares are straight on the front. **No S-curves** across the chest.
- [ ] Squares narrower towards the sides that turn away. Not narrower at a frame edge where the body does not turn.
- [ ] No hairline gap or overlap on shared seams.
- [ ] Gaps (wall) and objects in front (mannequin arm, stand) stay photo.
- [ ] Trims follow their curves and stay inside the garment.

**A person must approve `annotate.png` and `check.png`.** An agent's own look is not the approval.

### Step 7: Record

Add an entry to `render.md` §11: source and crop, script, scale and its cross-check, zones (cm, settings), trims and stitches, gaps and notches, tool changes, the `plate_checks.py` output, known problems.

---

## 4. Tool limits

| Limit | Affects | Fix |
|---|---|---|
| `ZONE_ID` knows `front`, `sleeve-l`, `sleeve-r`, `back` (4), `back-l` (5; done for the hem plate). | Hem view | `testing.html` still colours every zone except 1 blue in the checker. |
| `TRIM_ID` names are fixed. | Hem view (two edges of one slit, two hems) | Use `slit-l` = front edge, `slit-r` = back edge, or add names and update `TRIMS` / `FLIP` in `testing.html`. |
| Lace pearls point to the V = 1 side of the strip. | Every trim | Check in the page. If the pearls point inward, add the trim to `FLIP`. |
| One symmetric cylinder for each zone. | Turned views, zones cut by the frame | Use `thetaDeg`. It is an approximation. |
| `testing.html` loads one plate (`PLATE`). | Viewing the close views | Add a view switch (one plate for each journey step). |
| `make_base.py` is torso-specific. | Close views | Crop in `annotate_<view>.py`. |

---

## 5. View specifications

| | Torso | Neckline | Sleeve | Hem |
|---|---|---|---|---|
| **Plate** | `torso-straight` | `neck-straight` | `sleeve-straight` | `hem-straight` |
| **Status** | done | done | **built, fails step 6** (see below) | built, step 6 passes; awaiting review |
| **Framing** | Full form, front | Front, centred at neck height; knob cap may be cut; ≈ 10 cm below the neck dip; shoulder seams just inside | Form turned 30–35°; the sleeve at the left seen from its outer side; just above the shoulder to ≈ 5 cm below the cuff | Front, turned 10–15°; one slit at the right, slightly open; ≈ 35 cm above to ≈ 8 cm below the hem; no bottom garment |
| **Zones** | `front`, `sleeve-l`, `sleeve-r` | `front`, `sleeve-l`, `sleeve-r` (cut by the frame) | `front` (turned bodice), `sleeve-l` | `front`, `back` (needs §4) |
| **Trims** | neck 12, cuffs 25, hem 30, slits 8 mm | neck 12 mm | neck 12, cuff-l 25 mm | hem 30 (front, and back if visible), slit edges 8 mm |
| **Stitches** | — | neck top-stitch 5.5 mm | neck top-stitch 5.3 mm (near half), cuff top-stitch 18.5 mm | hem top-stitch, slit facings, bar tack |
| **Gaps / notches** | — | wall under both arms | wall under the arm; **mannequin arm below the cuff** (notch in the front) | the stand through the slit |
| **Scale** | shoulder-l → shoulder-r = 370 mm (assumption) | neck-l → neck-r = 158 mm | shoulder → cuff-out = 470 mm | slit-top → hem-slit = 240 mm |
| **mm/px** | 0.898 | 0.305 | 0.338 | 0.222 |
| **Scale cross-check** | — | shoulder → neck 102 mm (torso 107) | neck width 140 mm vs 158 × cos 31° = 135 mm | slit length on the torso plate: 24 cm |
| **Settings** | `tuck` | none | `thetaDeg` front 40°, sleeve 70°; `widthPx` sleeve 278.8 | `thetaDeg` front 45°, back 60°, back-l 65°; **`uvRangeCm` 32** |
| **Script** | (legacy: `extract_zones.py` + `fit_zones.py`) | `tools/annotate_neck.py` | `tools/annotate_sleeve.py` | `tools/annotate_hem.py` |

### Sleeve plate: what must change

`plate_checks.py`: front side-edge bulge **10.7 %**, grain tilt **18.4°**. (Fixed in numeric step 5: `annotate_sleeve.py` `smooth_under`; 0.0 % and 4.4°.) The columns of the checker make an S-curve across the chest.

**Cause:** the front grid's left edge follows the armhole seam, and that seam bulges 161 px from its chord in the turned view. The Coons patch carries the bulge into the whole bodice.

**Correction:** make the front grid's left edge a **smooth line under the sleeve**, for example from the shoulder point to the body edge at the bottom. Keep the armhole seam **only in the outline**, and in the sleeve's inner edge. The sleeve is on top, so the outline still cuts the correct shape. This is the same rule as "the grid top does not follow the neck dip" (`annotate.md` §2, rule 9).

Everything else on this plate is good: the measured edges, the gap, the arm notch, the trims, `widthPx`, and a byte-identical rebuild.

---

## 6. Failure cases

| Symptom | Cause | Action |
|---|---|---|
| Lines fit the annotated image but not the base | Regenerated annotation | Step 2, then Path A |
| S-curves in the checker columns; grain tilt > 10° | A grid edge follows a bulging seam | Smooth grid edge under the neighbouring zone; the outline cuts the seam |
| Fabric stretched across a sleeve (squares wider than 2 cm) | The zone's top edge is much shorter than its body (sleeve cap) | `widthPx` = outline area ÷ mean side-edge length |
| Squares narrower at a frame edge | One symmetric cylinder on a zone cut by the frame | Smaller `thetaDeg`, or accept and record |
| Hairline gap or zigzag between front and sleeve | The seam was sampled two times | One shared list |
| White strip of the original garment along a side | The traced edge is inside the real edge | Correct the points; `tuck` only as the last choice |
| Fabric on the wall, or on the mannequin arm | A gap or an object in front is inside a zone | Gap / notch in the outline |
| Squares of a different real size than in other views | Wrong scale value or landmark | §5 scale values and cross-checks |
| Folds missing in the render | Clipped highlights | Step 1: reject |
| Lace pearls point inward | Trim direction | `FLIP` in `testing.html` |
| Plate data near 1 MB | Large garment area, turned UV, `shade.png` | Accept up to 1.0 MB; above it, crop the plate tighter |

---

## 7. As a Claude Code skill

The project skill `.claude/skills/make-plate/SKILL.md` loads this file. Change the procedure **here**, not in the skill.
