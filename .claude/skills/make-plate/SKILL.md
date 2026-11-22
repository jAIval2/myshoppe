---
name: make-plate
description: Make or rebuild a garment plate (source.png, base.jpg, plate.dat) for one fixed view of the Bespoke Studio demo — torso, neckline, sleeve or hem — from one base image, and run its acceptance checks. Use when a new base image arrives for a view of a look, when a plate must be rebuilt after a tool change, or when asked to check a plate.
---

# make-plate

The full procedure is **`demo/docs/plate.md`**. Read it completely before you start, and follow its steps in order. Work in `demo/`. All tools are Python 3 with Pillow only (Node for the `.mjs` checks).

For step 4 (annotation), also read **`demo/docs/annotate.md`**, or use the `annotate-plate` skill.

## Rules that are never broken

1. **A plate folder holds `source.png`, `base.jpg` and `plate.dat` only.** Nothing in it is edited by hand: change `tools/annotate_<view>.py` (or a tool), then run `tools/make_plate.py`.
2. **Measure on `source.png`**, never on a regenerated annotation (plate.md step 2: every tool-made annotation was a new picture, 8–60 px off).
3. **A plate is done only when** `python3 tools/plate_invariants.py assets/plates/<plate>` passes (or each FAIL is written with its number and reason) **and a person** has approved `annotate.png`, `check.png` and the edge crops. Your own look is not the approval.
4. **If you change a tool**, run `tools/rebuild_check.sh`: every plate must rebuild byte-identical, or the change is meant and the plates are rebuilt and checked again.
5. **Record** the plate in `demo/docs/render.md` §11, with its numbers and the known problems.

## Quick reference

| Step | Command |
|---|---|
| Gridded crop for measuring | `python3 tools/gridcrop.py <source> <out> x0 y0 x1 y1 [step] [contrast] [scale]` |
| The annotate script's checks | `python3 tools/annotate_<view>.py` |
| Build (snap, trims, frames, decisions) + review images | `python3 tools/make_plate.py assets/plates/<plate> --review` |
| The plate's invariants | `python3 tools/plate_invariants.py assets/plates/<plate> [--debug uncovered.png]` |
| A plate as text | `python3 tools/platedat.py --dump assets/plates/<plate>` |
| Every plate = its source | `tools/rebuild_check.sh` |
| The render: closure, rim, halo; 2× crops | `tools/fringe.py`, `tools/edge_crops.py` (plate.md step 6) |

View specifications, scale values and failure cases: `demo/docs/plate.md` §5–6.
