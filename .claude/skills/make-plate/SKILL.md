---
name: make-plate
description: Make or rebuild a garment plate (base.jpg, zones.json, id/uv/uv_trim/shade maps, check.png) for one fixed view of the Bespoke Studio demo — torso, neckline, sleeve or hem — from one base image, and run its acceptance checks. Use when a new base image arrives for a view of a look, when a plate must be rebuilt after a tool change, or when asked to check a plate.
---

# make-plate

The full procedure is **`demo/docs/plate.md`**. Read it completely before you start, and follow its steps in order. Work in `demo/`. All tools are Python 3 with Pillow only.

For step 4 (annotation), also read **`demo/docs/annotate.md`**, or use the `annotate-plate` skill.

## Rules that are never broken

1. **Never use lines from a regenerated annotation.** Run the alignment test (plate.md step 2). In this project every tool-made annotation was a new picture, 8–60 px off.
2. **Measure on `source.png`**, then convert to the 1200 × 1600 plate frame.
3. **A plate is done only when** `python3 tools/plate_checks.py assets/plates/<plate>` prints `ALL PASS` **and a person** has approved `annotate.png` and `check.png`. Your own look is not the approval.
4. **If you change `tools/make_plate.py`**, rebuild every other plate into a scratch copy and `cmp` the shipped maps: they must be byte-identical.
5. **Record** the plate in `demo/docs/render.md` §11, with the `plate_checks.py` output and the known problems.

## Quick reference

| Step | Command |
|---|---|
| Gridded crop for measuring | `python3 tools/gridcrop.py <source> <out> x0 y0 x1 y1 [step] [contrast] [scale]` |
| Base + data + review image | `python3 tools/annotate_<view>.py assets/plates/<plate>` |
| Plate maps + checker | `python3 tools/make_plate.py assets/plates/<plate>` |
| Acceptance | `python3 tools/plate_checks.py assets/plates/<plate>` |

View specifications, scale values and known plate problems: `demo/docs/plate.md` §5.
