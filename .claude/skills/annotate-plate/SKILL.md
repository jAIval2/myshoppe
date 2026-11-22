---
name: annotate-plate
description: Annotate one base image of the Bespoke Studio demo — measure garment edges, seams, gaps, objects in front (mannequin arm, stand) and landmarks on source.png with gridded crops, and write them as typed edges, zones with fabric-frame specifications and trims in a re-runnable tools/annotate_<view>.py with automatic checks; make_plate.py --review draws the colour-coded annotate.png. Use for step 4 of make-plate, when a base image arrives without a usable annotation, or when an annotation must be corrected after review.
---

# annotate-plate

The full procedure is **`demo/docs/annotate.md`**. Read it completely before you start. It is step 4 of `demo/docs/plate.md` (the `make-plate` skill). Work in `demo/`. Python 3 with Pillow only.

Start from the nearest template:
- `tools/annotate_neck.py`: front view, shared seams, wall gaps that close again.
- `tools/annotate_torso.py`: full front view, both sides measured, wall gaps at the cuffs, smooth fits of seams.
- `tools/annotate_sleeve.py`: turned view, the mannequin arm as an occluder, an axis through measured centres.
- `tools/annotate_hem.py`: three pieces, slits, an anchor at a known distance.

## Rules that are never broken

1. **Measure, do not guess.** Read every point on gridded crops of `source.png` (`tools/gridcrop.py`). Use true colour to tell a gap from a fold. Confirm automatic scans on a crop before you use them. Both sides are measured; nothing is mirrored.
2. **Every edge has a type** (`free`, `seam`, `frame`, `cut`), and **a shared seam is one list** used by both zones.
3. **Each zone has a fabric-frame specification** (axis, anchor, optional sag edge); no grid edges. The axis runs down the middle of the piece, along its grain.
4. **Gaps and objects in front stay outside every zone** (wall under the arm, mannequin arm as an occluder, stand).
5. **Trims are specifications** (edge, type, anchors `from` / `to`, `anchor` for the motif, `cut` for a real square end): the build derives each trim's line (its edge between the anchors). No width or offset: a lace keeps its own width. Stitches only where they are visible, at a measured distance.
6. **The script's automatic checks must pass** (annotate.md §9.1). Then **a person reviews `annotate.png`** (from `make_plate.py <plate> --review`) before the plate is accepted.
