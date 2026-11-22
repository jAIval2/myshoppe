---
name: make-plate
description: Make or rebuild a garment plate (base.jpg + plate.dat, from its source image in demo/silhouette/sources) for one fixed view of the Bespoke Studio demo — torso, neckline, sleeve or hem — from one base image, and run its acceptance checks. Use when a new base image arrives for a view of a look, when a plate must be rebuilt after a tool change, or when asked to check a plate.
---

# make-plate

The full procedure is **`demo/docs/plate.md`**. Read it completely before you start, and follow its steps in order. Work in `demo/`. Everything is in `demo/silhouette/` (its `README.md`), with one entry point: `python3 silhouette/plate.py <command> <view>`. Python 3 with Pillow only (Node for the `.mjs` checks).

For step 4 (annotation), also read **`demo/docs/annotate.md`**, or use the `annotate-plate` skill.

## Rules that are never broken

1. **A plate folder holds `base.jpg` and `plate.dat` only**; the source image is `silhouette/sources/<plate>.png`. Nothing in it is edited by hand: change `silhouette/views/<view>.py` (or a tool), then run `silhouette/pipeline/make_plate.py`.
2. **Measure on the source image** (`silhouette/sources/<plate>.png`), never on a regenerated annotation (plate.md step 2: every tool-made annotation was a new picture, 8–60 px off).
3. **A plate is done only when** `python3 silhouette/checks/plate_invariants.py assets/plates/<plate>` passes (or each FAIL is written with its number and reason) **and a person** has approved `annotate.png`, `check.png` and the edge crops. Your own look is not the approval.
4. **If you change a tool**, run `silhouette/checks/rebuild_check.sh`: every plate must rebuild byte-identical, or the change is meant and the plates are rebuilt and checked again.
5. **Record** the plate in `demo/docs/render.md` §11, with its numbers and the known problems.

## Quick reference

| Step | Command |
|---|---|
| Gridded crop for measuring | `python3 silhouette/measure/gridcrop.py <source> <out> x0 y0 x1 y1 [step] [contrast] [scale]` |
| The measured view's checks | `python3 silhouette/plate.py measure <view>` |
| Build (snap, trims, frames, decisions) + review images | `python3 silhouette/plate.py build <view> --review` |
| The plate's invariants + frame parity | `python3 silhouette/plate.py check <view>` |
| The page against the plate (page served on 8300) | `python3 silhouette/plate.py page-check <view>` |
| A plate as text | `python3 silhouette/pipeline/platedat.py --dump assets/plates/<plate>` |
| Every plate = its source | `python3 silhouette/plate.py rebuild-check` |
| The render: closure, rim, halo; 2× crops | `silhouette/checks/fringe.py`, `silhouette/checks/edge_crops.py` (plate.md step 6) |

View specifications, scale values and failure cases: `demo/docs/plate.md` §5–6.
