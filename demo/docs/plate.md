---
name: make-plate
description: Make a garment plate (source.png, base.jpg, plate.dat) for one fixed view of the Bespoke Studio demo — torso, neckline, sleeve or hem — from one base image. Use when a new base image arrives for a view, or when a plate must be rebuilt or checked.
---

# Skill: make a plate

A **plate** is one fixed view of one garment variant. It is the input of `testing.html`.
This file is the **pipeline**: intake, base, annotation (→ `annotate.md`), build, acceptance, record.
Background: `render.md` §6 (method), `DedhD.md` (why plates, how many), `plan/StepA.md` (why a plate is what it is now).

All paths are relative to `demo/`. All tools use Python 3 with Pillow only (Node for the `.mjs` checks).

| File | Job |
|---|---|
| `plate.md` (this file) | The pipeline, acceptance checks, view specifications, plate-level failures |
| `annotate.md` | Measuring the photo: typed edges, landmarks, trims, frames; the review image |

---

## 1. Output

One folder for each plate: `assets/plates/<view>-<variant>/`, for example `assets/plates/hem-straight/`. **It holds three files, nothing else.**

| File | What it is | Ships |
|---|---|---|
| `source.png` | The image as received (the input; it is measured) | No |
| `base.jpg` | The 1200 × 1600 photo, made from `source.png` | Yes |
| `plate.dat` | Every number of the view (`tools/platedat.py`, `BSP2`): typed edges, zone outlines and fabric frames, trims, stitches, landmarks, occluders, scale, settings, and the decisions taken from the image | Yes |

- The **source** of a plate is `source.png` + `tools/annotate_<view>.py` (the measured points). `tools/make_plate.py <plate>` builds `base.jpg` and `plate.dat` from them, deterministically.
- **Nothing is edited by hand in a plate.** A change is a change to the annotate script (or to a tool), then `make_plate.py <plate>`.
- `python3 tools/platedat.py --dump <plate>` prints a `plate.dat` as text; `git diff` shows that text once per clone: `git config diff.dat.textconv "python3 demo/tools/platedat.py --dump"`.
- Review images (`annotate.png`, `check.png`, the edge crops) are made on demand into `demo/review/<plate>/` (not committed): `make_plate.py <plate> --review`.

The plate is **done** only when step 6 passes, **and** a person has looked at `annotate.png` and `check.png`.

---

## 2. Pipeline

```
1 Intake ──► 2 Alignment test ──► 3 Base ──► 4 Annotate ──► 5 Build ──► 6 Accept ──► 7 Record
  (reject?)    (only if an          crop in     annotate.md    make_plate.py  plate_invariants.py  render.md §11
                annotation came)    the script                                + the page + person
```

| Tool | Step | Job |
|---|---|---|
| `tools/gridcrop.py` | 4 | Gridded crops of `source.png` for measuring |
| `tools/annotate_<view>.py` | 3–4 | `base()` (the crop), `measure()` (typed edges, zones and frame specifications, trims, landmarks); run alone: the automatic checks |
| `tools/make_plate.py` | 5 | The build: free edges snapped to the photo (`snap_edges.py`), trims derived from their edges, frames fitted, the maps in memory, the decisions → `base.jpg` + `plate.dat`; `--review` |
| `tools/plate_invariants.py` | 6 | Closure of the garment, hairline gaps, trim line (on its edge, smooth) and trim field (complete, no seam), landmarks, the fabric frame rules |
| `tools/rebuild_check.sh` | 6 | Every plate = what its source makes (byte for byte) |
| `tools/frame_check.mjs`, `tools/maps_check.py` | 6 | The page's maths against Python: the frames (10,000 points), the maps the page builds |
| `tools/fringe.py`, `tools/edge_crops.py` | 6 | The render: photo garment still showing, the rim along the free edges, the halo; the fixed 2× crops |

---

## 3. Steps

### Step 1: Intake check

Copy the image as received to `source.png`. Then **reject** it, and ask for a new one, if:

- [ ] It is **not the same garment** as the other views. The straight kurta is plain white, smooth matte cotton, with a high round neck (no slit, no placket), full sleeves, calf length and side slits. No embroidery, lace or print.
- [ ] It is **not the same scene**: natural-linen dress form, dark wood knob and stand, warm beige wall, soft light from the upper left.
- [ ] **Garment highlights are clipped:** the maximum luminance in the garment must be ≤ 250.
- [ ] The framing does not match the view (§5).

**Not** a reason to reject (fix them in step 3): a square image or a wrong aspect ratio; a sparkle mark or watermark, on the wall **or on the garment**.

### Step 2: Alignment test (only if an annotated image came with the base)

```python
from PIL import Image, ImageChops, ImageStat
a = Image.open("annotated.png").convert("RGB"); b = Image.open("source.png").convert("RGB")
assert a.size == b.size
for box in [(40, 40, 400, 300), (900, 60, 1140, 220), (820, 380, 1100, 470)]:   # wall, knob, form neck
    print(box, sum(ImageStat.Stat(ImageChops.difference(a.crop(box), b.crop(box))).mean) / 3)
```

Every box **≤ 2**: aligned, use it as a layout guide for the measuring. Any box **> 5**: **regenerated** (every tool-made annotation in this demo was, 8–60 px off): use it only as a layout guide. Points are always measured on `source.png` (`annotate.md`).

### Step 3: The base (1200 × 1600), in `annotate_<view>.py` `base()`

1. **Sparkle mark:** cover it with a feathered patch from the **same rows**, 150–200 px to the side (wall for a mark on the wall, garment for a mark on the garment).
2. **Crop to 3:4** around the subject. For the front views, centre on the centre-front line. If the garment runs off one side, put the crop against that side.
3. Resize to 1200 × 1600 with LANCZOS. `make_plate.py` saves it as JPEG quality 94, no chroma subsampling, and takes its decisions from the decoded JPEG (what the page sees).

### Step 4: Annotate

Follow **`annotate.md`**. Result: `tools/annotate_<view>.py` with its automatic checks passing, and a person's approval of `annotate.png` (made by step 5 `--review`).

### Step 5: Build

```sh
python3 tools/make_plate.py assets/plates/<plate> --review     # 10-30 s; prints the snap report and the invariants
```

What the build does, in order:
1. **Snap** every `free` and `cut` edge to the photo (`tools/snap_edges.py`): a local colour model on each normal, the sub-pixel 50 % crossing, a robust smooth fit. Weak spans (no colour step: white over white, garment against the linen arm) keep their measured points and are listed. Corners and seam ends follow.
2. **Trims** from their edges (`derive_trims`): the trim's `line` = its edge, smoothed over 4 mm, between the trim's anchors (from `from` to `to`); its `zone` and `side` (the sign that turns the line's left normal onto the zone). The lace hangs on the line at the lace's own width (`tools/trimfield.py`: the trim field, StepA extension).
3. **Frames** (`fit_frames`): each zone's axis, anchor, half-width profile, `thetaDeg`, sag.
4. **Decisions** from the image (trim sides, the shade median, the neck block) and `plate.dat`.

If you changed a tool, run `tools/rebuild_check.sh`: every plate must rebuild byte-identical (or the change is meant, and the plates are rebuilt and checked again).

### Step 6: Acceptance

```sh
python3 tools/plate_invariants.py assets/plates/<plate> [--debug uncovered.png]   # magenta = photo garment that no zone covers
python3 tools/plateframe.py --samples assets/plates/<plate> /tmp/s.json && node tools/frame_check.mjs assets/plates/<plate> /tmp/s.json
node tools/cdp_shot.mjs <out> <port> --eval 'return window.__studio.readMapsRaw()' "view=<v>"; python3 tools/maps_check.py assets/plates/<plate> <out>/log.json
node tools/cdp_shot.mjs <out> <port> "view=<v>&fabric=mocha&trims=none&stage=600" "view=<v>&fabric=off&trims=none&stage=600"
python3 tools/fringe.py <out>/canvas-0.png assets/plates/<plate> --photo <out>/canvas-1.png
python3 tools/edge_crops.py <out>/canvas-0.png assets/plates/<plate> crops.png --photo <out>/canvas-1.png
```

| Check | Pass |
|---|---|
| Closure (`plate_invariants.py`) | photo garment no zone covers ≤ 0.02 % of the zones, no piece wider than 1 px |
| No gaps | thin enclosed gaps (a hairline between zones) ≤ 8 px |
| Trim offset / smoothness | centre to its edge = the offset ± 0.5 px, std ≤ 1.0 px; local quadratic residual ≤ 0.8 px |
| Frame | no fold; constant-u lines within 3° of the axis in 95 % of the zone; UV rate at the axis within 2 % of face-on; u = 0 through the centre-front landmarks within 1 px |
| Snap (printed by the build) | fit against the crossing: median ≤ 0.3, 95 % ≤ 0.75, max ≤ 1.5 px; weak spans ≤ 5 % of each edge, listed |
| `frame_check.mjs` | ≤ 10⁻⁴ cm |
| `maps_check.py` | coverage = Python's except a 1 px edge band; uv within 0.01 cm; trims within 0.05 px or one 16-bit step |
| Render (`fringe.py`, mocha and sage) | uncovered ≤ 0.02 %, no piece wider than 1 px; rim ≤ 0.5 % of the free-edge length; halo ≤ 10 % |

Then look at `check.png` and the edge crops at 2× (`demo/review/<plate>/`):

- [ ] Squares ≈ 2 cm: the same real size as in the other views.
- [ ] Columns of squares are straight down the front and along each sleeve. **No S-curves**, no stretch at a sleeve cap.
- [ ] Squares narrower towards the sides that turn away.
- [ ] No hairline gap or overlap on shared seams; no white or grey rim along the free edges.
- [ ] Gaps (wall) and objects in front (mannequin arm, stand) stay photo.
- [ ] Trims follow their edges and stay inside the garment.

**A person must approve `annotate.png`, `check.png` and the crops.** An agent's own look is not the approval.

### Step 7: Record

Add an entry to `render.md` §11: source and crop, script, scale and its cross-check, zones and frames, trims and stitches, gaps and notches, tool changes, the step 6 numbers, known problems (weak spans, open closure pieces).

---

## 4. Tool limits

| Limit | Affects | Fix |
|---|---|---|
| Zone names are fixed in `make_plate.py` `ZONE_ID` (front 1, sleeve-l 2, sleeve-r 3, back 4, back-l 5) and the shader's checker colours | New pieces | Add a name and an id in both |
| Trim names are fixed (`TRIM_ID`, the page's `TRIMS`) | New trims | Add a name and an id in both |
| One cylinder for each zone (`thetaDeg`, symmetric about the axis) | Turned views, zones cut by the frame | The axis and `thetaDeg` of the turned zone; a side whose rays end on the frame takes the other side's profile |
| An axis has at most 33 points (the shader's arrays) | Very bent zones | A polynomial axis through a few measured centres (16 segments) |
| The snap needs a colour step | Garment against the linen mannequin arm, white over white | Weak spans keep the measured points; measure them carefully |
| The shade needs float render targets | Old phones | Flat light there (StepA step 8 decides a `shade.webp` fallback) |

---

## 5. View specifications

| | Torso | Neckline | Sleeve | Hem |
|---|---|---|---|---|
| **Plate** | `torso-straight` | `neck-straight` | `sleeve-straight` | `hem-straight` |
| **Framing** | Full form, front | Front, centred at neck height; ≈ 10 cm below the neck dip; shoulder seams just inside | Form turned 30–35°; the sleeve at the left seen from its outer side; just above the shoulder to ≈ 5 cm below the cuff | Front, turned 10–15°; one slit at the right, slightly open; ≈ 35 cm above to ≈ 8 cm below the hem |
| **Zones** | `front`, `sleeve-l`, `sleeve-r` | `front`, `sleeve-l`, `sleeve-r` (cut by the frame) | `front` (turned bodice), `sleeve-l` | `back-l`, `back`, `front` |
| **Frames** (axis; anchor) | front: `cf-neck` → `hem-cf`, neck-point line; sleeves: midline, shoulder point; sag from the hem and the cuffs | front: `cf-neck` → `cf-low`, neck-point line; sleeves: midline, shoulder point | front: vertical, halfway between the armhole and the frame, neck-point line; sleeve: through the upper arm, elbow and cuff centres, shoulder point; sag from the cuff | midlines; the slit top at 911 mm from the neck-point line (the torso's mean); sag from each hem |
| **Trims** | neck 12, cuffs 25, hem 30, slits 8 mm | neck 12 mm | neck 12, cuff-l 25 mm | hem 30 (front and both back pieces), slit edges 8 mm |
| **Stitches** | — | neck top-stitch 5.5 mm | neck top-stitch 5.3 mm (near half), cuff top-stitch | hem top-stitch, slit facings, bar tack |
| **Gaps / notches** | wall between each cuff and the body | wall under both arms | wall under the arm; **mannequin arm below the cuff** (an occluder) | the stand through the slit (an opening) |
| **Scale** | neck-l → neck-r = 158 mm (the neck view's value; shoulder width then 341 mm) | neck-l → neck-r = 158 mm | shoulder → cuff-out = 470 mm | slit-top → hem-slit = 240 mm |
| **mm/px** | 0.877 | 0.305 | 0.338 | 0.222 |
| **Settings** | — | — | `thetaDeg` front 40°, sleeve 70° | `thetaDeg` front 45°, back 60°, back-l 65° |
| **Script** | `tools/annotate_torso.py` | `tools/annotate_neck.py` | `tools/annotate_sleeve.py` | `tools/annotate_hem.py` |

---

## 6. Failure cases

| Symptom | Cause | Action |
|---|---|---|
| Lines fit the annotated image but not the base | Regenerated annotation | Step 2; measure on `source.png` |
| White or grey rim of the original garment along an edge | The measured edge is more than 8 px off (beyond the snap), or the edge is weak | Measure the edge again on gridded crops; check the snap report's weak spans |
| A strip of photo garment beside a wall gap | The gap was measured too wide or starting too high | Measure where the wall really shows (true colour, 2–3×) |
| Columns of squares bend or tilt (frame grain > 3°) | The axis does not follow the zone (a midline through a notch or a bend) | Give the axis from measured centres; leave occluder edges out of the half widths |
| A fold or a jump in the squares | A kinked axis | A smooth axis (polynomial, 16 segments) |
| Squares of a different real size than in other views | Wrong scale value or landmark | §5 scale values and cross-checks |
| Lace twisted at an end, or past the corner | The trim's anchors or its edge | `from` / `to` anchors; the trim's `edge` |
| Fabric on the wall, or on the mannequin arm | A gap or an object in front is inside a zone | A gap in the outline; an occluder |
| Folds missing in the render | Clipped highlights, or no float render targets | Step 1: reject; `?perf=1` shows the float targets |

---

## 7. As a Claude Code skill

The project skill `.claude/skills/make-plate/SKILL.md` loads this file. Change the procedure **here**, not in the skill.
