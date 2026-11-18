---
name: annotate-plate
description: Annotate one base image of the Bespoke Studio demo — measure garment edges, seams, gaps, objects in front (mannequin arm, stand) and landmarks on source.png with gridded crops, and write zones.json, a colour-coded annotate.png and a re-runnable tools/annotate_<view>.py with automatic checks. Use for step 4 of make-plate, when a base image arrives without a usable annotation, or when an annotation must be corrected after review.
---

# annotate-plate

The full procedure is **`demo/docs/annotate.md`**. Read it completely before you start. It is step 4 of `demo/docs/plate.md` (the `make-plate` skill). Work in `demo/`. Python 3 with Pillow only.

Start from the nearest template:
- `tools/annotate_neck.py`: front view, shared seams, gaps under the arms.
- `tools/annotate_sleeve.py`: turned view, mannequin-arm notch, `widthPx`, `clip_extend` for trims.

## Rules that are never broken

1. **Measure, do not guess.** Read every point on gridded crops of `source.png` (`tools/gridcrop.py`). Use true colour to tell a gap from a fold. Confirm automatic scans on a crop before you use them.
2. **A shared seam is one list.** The front and the sleeve use the same points.
3. **A grid edge is a smooth grain line.** A front side edge must not bulge more than 5 % from its chord. If the seam bulges more, the grid edge runs smoothly under the sleeve, and only the outline follows the seam. The grid top never follows the neck dip.
4. **Gaps and objects in front stay outside every zone** (wall under the arm, mannequin arm, stand).
5. **Trims stay inside their zone outline** (`clip_extend`). Stitches only where they are visible, at a measured distance.
6. **The script's automatic checks must pass** (annotate.md §9.1). Then **a person reviews `annotate.png`** before `make_plate.py` runs.
