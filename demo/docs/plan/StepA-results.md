# StepA results

Plan: `StepA.md`. Branch `stepA` (from `numeric` 430c3fd), worktree `../myshoppe-stepA`, port 8300. Reference: `numeric` on 8200.

## Step 0: Baseline, review set, closure in the render

**Done:**
1. Branch `stepA` and worktree `../myshoppe-stepA` from 430c3fd; the plan (`StepA.md`), `breather.md` and `DedhD.md` §11 committed here. Server on 8300.
2. `tools/plate_edges.py`: the edges of a plate for the review tools. At step 0 it classifies each zone outline geometrically (every 1 px): `frame` (within 0.6 px of the border), `seam` (2.5 px outward is inside another zone, or the point is under a zone drawn later), `cut` (the front's neck dip), `free` (the rest). Step 1 replaces the geometry with the typed edges of `plate.dat`.
3. `tools/edge_crops.py <canvas> <plate> <out> [--photo <off>]`: the review set. One crop at each landmark and one every 150 px along each free edge; each tile is the photo and the render of the same 40 × 40 plate px box, 3× with nearest pixels. Computed from the plate: no file of its own.
4. `tools/fringe.py <canvas> <plate> [--photo <off>] [--debug <png>]`: closure in the render. Uncovered = photo garment (saturation < 24, 3 × 3 median: the rule of `plate_invariants.py`) where the render is within 4 levels of the photo, within 10 px of rendered fabric, openings left out; pieces wider than 1 px = what survives a 2 × 2 erosion. Rim = free-edge samples whose brightest value between 1.5 px inside and 3.5 px outside is brighter by more than 8 levels than both 4 px inside and 6 px outside.
5. Shots: `node tools/cdp_shot.mjs <out> <port> "view=<v>&fabric=mocha&trims=none&stage=600"` (and `fabric=off`, `fabric=sage`). `stage=600` at DPR 2 gives a 1200 × 1600 canvas: one canvas px = one plate px, so every count below is in plate px. The photo for the comparison is the `fabric=off` render (the photo as the page draws it).
6. `demo/review/` is in `.gitignore` (review images are made on demand).

**Baseline on 8200 (`numeric`), 2026-11-21:**

| View | `plate_invariants.py` | Uncovered garment (render, mocha) | Pieces > 1 px | Rim, mocha | Rim, sage |
|---|---|---|---|---|---|
| torso | 2 FAIL: closure 809 px = 0.138 %, landmarks `slit-l`, `slit-r` | 1,221 px = 0.209 % | 794 px in 11 pieces | 463 / 3,770 px = 12.3 % | 16.3 % |
| neck | 2 FAIL: closure 3,239 px = 0.239 %, no gaps 249 px | 4,673 px = 0.345 % | 3,327 px in 35 pieces | 1,757 / 3,885 px = 45.2 % | 39.2 % |
| sleeve | 2 FAIL: closure 1,410 px = 0.097 %, trim offset `cuff-l` 39.3 px (37.0), std 5.8 px | 2,337 px = 0.160 % | 1,306 px in 36 pieces | 896 / 4,887 px = 18.3 % | 15.4 % |
| hem | 1 FAIL: closure 356 px = 0.026 %, one piece 43 px | 664 px = 0.048 % | 271 px in 10 pieces | 2,568 / 6,822 px = 37.6 % | 32.2 % |

Targets (steps 4 and 6): uncovered ≤ 0.02 %, no piece wider than 1 px; rim ≤ 0.5 %.

**The largest pieces found by `fringe.py`** (plate px, box x0 y0 x1 y1):

| View | Piece | What it is |
|---|---|---|
| torso | 705 px, 804 936 815 1128; 28 px, 815 1131 815 1158 | the body-side strip on the right (known: numeric step 11) |
| torso | 32 px, 688 252 699 256 | the right neck-corner speck (known: numeric step 9) |
| torso | 12 px, 800 305 806 311; 5 px, 468 270 472 271 | shoulder slivers at the sleeve caps (known: numeric step 9) |
| neck | 1,295 px, 1093 1040 1127 1202; 745 px, 1126 958 1142 1047; 723 px, 1092 1312 1097 1598 | the right underarm and body side: the photo's white between the front and the right sleeve |
| neck | 216 px, 1060 452 1151 489; 69 px, 1174 501 1198 527 | the right shoulder line |
| sleeve | 609 px, 322 768 409 891 | under the arm, at the gap |
| hem | 147 px, 406 1354 486 1358 (+ 19 px, 382 1353 398 1354) | the front hem's bottom edge (known: the 43 px piece of numeric step 11, here longer because the render shows the photo's soft edge too) |

The rim is a real one: at 4× the slit edges of the hem show a light line between the fabric and the form, and the neck view's sleeves a grey line along the wall (crops below).

**Review set** (photo left, render right, mocha, no lace): `img/stepA0-crops-torso.jpg`, `img/stepA0-crops-neck.jpg`, `img/stepA0-crops-sleeve.jpg`, `img/stepA0-crops-hem.jpg`. They show the white strip along the torso's right side (`front 1:74`, `1:222`), the grey rims along both torso sleeves, the stair-stepped hem corners and cuffs.

- [x] Baseline table (invariants, fringe, rim) and 4 crop sheets in the results.
- [x] `fringe.py` finds the known defects: the torso body-side strip, the hem's 43 px piece, the shoulder slivers (and the neck-corner speck).
