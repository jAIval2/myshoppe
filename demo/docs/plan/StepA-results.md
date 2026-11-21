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

## Step 1: One plate file (`plate.dat` version 2) with typed edges

**Done:**
1. `tools/platedat.py`: `BSP2`. "BSP2", u16 version 2, u16 unit (100 = 0.1 px), u32 header length, a JSON header, int16 curve deltas. In the header every polyline is `{"@c": index}` and identical curves are stored once (the same rule as `BSP1`, now for any list of points: edges, grids, trims, stitches, occluders, the neck block). Reader, writer, validator (`--check`), `--dump` (one value per line, curves one point per line, sorted keys) and `legacy()`: the plate header and the zone data in the shapes the map code reads. The data model is in its docstring.
   - **edges** `{name: {type, points, zones (a seam), under (a hidden run)}}`; **zones** `{id, order, outline: [[edge, ±1], ...], grid, widthPx}`; **trims** `{id, order, widthMm, type, edge, offsetMm, join, centre}` in drawing order; **stitches, occluders, landmarks, invariants, settings** (`thetaDeg`, `tuck`, `shadeSmoothMm`), **decisions** (`shadeMedian`, `shadeSmoothMm/Px`, `shadeSpace`, `shadeEncoding`, the neck block, each trim's `side` / `lengthCm` / `vMax`, each zone's size in cm).
2. `annotate_neck.py`, `annotate_sleeve.py`, `annotate_hem.py` are modules: `base(plate)`, `measure()`, `review(P, base)`; run alone they run their checks and write nothing. The measured lists did not change; each outline is now written as a chain of named, typed edges. The hem's `hem-bl` / `hem-br` (made in numeric step 10 by `snap_outline.py edge-trim`) and the trim order (`trim-order`: the hem laces after the slit trims) are trim data in `annotate_hem.py`, as are the plate's `invariants`. The `edge` of each trim names the edge it hangs on (step 3 derives the centre lines from it).
3. `tools/make_plate.py <plate> [--review] [--no-check] [--dump-mesh]` is the build: source → maps in memory (`rasterise`, the old arithmetic unchanged) → decisions → `base.jpg` + `plate.dat`. The base is encoded once as JPEG and the decisions are taken from the decoded JPEG, as the page sees it (taking them from the image before the JPEG moved the neck block's fill colours by 1 level). `--review` writes `annotate.png`, `check.png` and the edge crops (cut from `check.png`) into `demo/review/<plate>/`. As a module: `build()`, `maps_of(plate)` (the maps of a committed `plate.dat`, in memory), `rasterise()`.
4. The torso: a one-off converter (in the scratchpad, never committed) read its `zones.json` + `plate.json` and split each outline into typed edges by the geometry of step 0: front = `front-0` (left shoulder, free), `neck` (cut), `front-2` (right shoulder, free), `front-3` (under `sleeve-r`), `front-4` (body sides and hem, free), `front-5` (under `sleeve-l`); each sleeve one free edge. `make_plate.py` rebuilds the torso from this imported data (and keeps its `base.jpg`) until step 2.
5. Readers moved to `platedat.py` / `make_plate.maps_of`: `plate_invariants.py`, `plate_checks.py` (its size rule now counts what ships: `base.jpg` + `plate.dat`), `polish_metrics.py`, `reveal_metrics.py`, `map_diff.py`, `trim_match.py`, `mesh_check.mjs` (through `Plate.parseDat`), `plate_edges.py` (the typed edges in place of step 0's geometry), and the page: `Plate.parseDat` reads `BSP2` and gives the same `{ plate, zones }` as before; every view (the `?geom=maps` path too) reads `plate.dat`. Removed: `BSP1`, `make_dat.py`, `dat_check.mjs`, the page's `?dat=0`; `snap_outline.py` keeps only its helpers (its commands wrote `zones.json`). `extract_zones.py` and `fit_zones.py` (planned for step 2) are removed here: they wrote `zones.json` and cannot run any more.
6. Removed from the 4 plate folders: `zones.json`, `plate.json`, `annotate.png`, `check.png`. The map PNGs stay for `?geom=maps` until step 7 (they are frozen: the build no longer writes them).
7. `.gitattributes`: `demo/assets/plates/*/plate.dat diff=dat`; `tools/README.md` gives `git config diff.dat.textconv "python3 demo/tools/platedat.py --dump"`.
8. `tools/rebuild_check.sh`: every plate rebuilt from its source into a scratch copy; `base.jpg` and `plate.dat` compared byte for byte.

**One rule added to the plan's edge types** (the outlines had to stay the same points): a lower zone's run that lies hidden under a later zone is a `seam` with `"under": <the later zone>`, used by that one lower zone (the validator checks it is lower). There are 4: the sleeve view's `front-under-cuff` and `front-under-sleeve`, the torso's `front-3` and `front-5` (the tucked sides). Where an upper zone's contour lies over a lower zone (a sleeve's inner edge over the body), the contour is `free`. A visible-in-the-photo seam that two zones share is `seam` with `zones` (the armholes of the neck and sleeve views; the hem view's side seam and left seam). The torso has no shared seam until it is measured (step 2).

**Results:**

| Check | Result |
|---|---|
| One-time comparison (scratchpad, deleted): the build's `legacy()` of each new `plate.dat` against the old `zones.json` + `plate.json`: outlines (a repeated closing point aside), grids, orders, `widthPx`, trims (order, width, type, centre), landmarks, stitches, occluders, settings, invariants, and every number of `plate.json` | **0 differences** on all 4 plates (first run: neck fill colours ±1 level, fixed by deciding on the decoded JPEG) |
| Rebuilt `base.jpg` against the committed one | byte-identical (neck, sleeve, hem) |
| `platedat.py --check` | PASS on all 4: every seam used by exactly two zones (or one lower zone, `under`), every run typed, chains closed, frame points on the border |
| `rebuild_check.sh` | ALL IDENTICAL (`base.jpg` + `plate.dat`, 4 plates; the torso from its imported data) |
| Render 8300 against 8200, the 12 `--numeric` queries (`canvas_diff.py`) | mean 0.000, max 0 on all 12; `?geom=maps` (hem, neck) also 0.000 |
| `mesh_check.mjs` (plate.js against Python, through `parseDat` v2) | PASS on all 4 |
| `plate_invariants.py` | the same numbers as step 0 on all 4 (now from the maps in memory) |
| `plate.dat` sizes | torso 17,166 B, neck 3,544 B, sleeve 4,278 B, hem 4,902 B: 29.9 KB (`BSP1`: 24.8 KB; the typed edges, the grids and the decisions are stored separately) |
| `grep -lE "zones\.json|plate\.json"` over `tools/` and the page code | nothing |

- [x] Each plate folder holds `source.png`, `base.jpg`, `plate.dat` (and the map PNGs until step 7), nothing else. (The torso has no `source.png` until step 2.)
- [x] `--dump` of each new `plate.dat` gives back every number of the old `zones.json` + `plate.json` (the test compared them once, then was deleted).
- [x] The render at 8300 = 8200 (mean 0.000).
- [x] Each seam is referenced by exactly two zones (or is a hidden `under` run of one lower zone); each run of each outline has a type; the validator passes on all 4 plates.
- [x] `rebuild_check.sh`: neck, sleeve and hem byte-identical from their sources; torso from its imported data.
- [x] `git diff` on a changed `plate.dat` shows text.

Note: the 8200 server had stopped during this step; it was restarted on the `numeric` worktree (`python3 -m http.server 8200 --bind 127.0.0.1 --directory demo`).

## Step 2: The torso, measured

**Done:**
1. `assets/torso-base.png` → `assets/plates/torso-straight/source.png` (`git mv`).
2. `tools/annotate_torso.py` (from the template of `annotate_neck.py`): `base()` is the old `make_base.py` (sparkle patch, 1792 × 2389 cut, 1200 × 1600), and the rebuilt `base.jpg` is byte-identical to the committed one. Every edge was read on gridded crops of `source.png` (2–3×, 10 px grid, true colour and raised contrast). The edges against the wall and the sleeve / body creases were then placed on the strongest luminance step within 6 px of the reading (a measuring aid; where the step is weak the reading stays) and checked again on overlay crops. From the reading only: the neck edge (the white front meets the grey band of the back neckline inside the opening: the aid jumped to the form's edge, 4–5 px higher), the right armhole (a faint line on lit white: the aid drifted 5 px), the right sleeve's inner edge below y 1200 (the gap to the body is 3–8 px and the aid put both on the body), the left cuff. How it was done is in the script's docstring.
   - Zones: `front` (shoulders free, `neck` cut, the armholes and then the sleeves' inner edges down to where the wall gap opens: **shared seams** with each sleeve (after review 3), the body sides free from there, the hem free); `sleeve-l`, `sleeve-r` (outer edge free, cuff free, inner edge free against the wall gap). The torso has no `under` run any more.
   - **A wall gap between each cuff and the body** (left from y 1185 source px, up to 23 px wide; right from y 1190, up to 16 px) was not in the traced plate: there the old front covered the wall (the body-side strip of numeric step 11 was the other half of that error).
   - Trims from the measured edges: neck 6 mm inside the neck edge, cuffs 12.5 mm above the cuff edges, slits 4 mm inside the body sides from the slit tops, hem 15 mm above the hem; the grid (until step 4): the shoulder runs as its top, the side edges 6 px outside the body sides (the outline cuts), the sleeves with their cap as a point and `widthPx` = area ÷ mean side length.
   - `make_base.py` is removed. `tools/rebuild_check.sh` now rebuilds the folders that have a `source.png`.
3. **The scale.** Measured: neck-l → neck-r 180.1 plate px, shoulder-l → shoulder-r 388.4 plate px. 
   | Scale from | mm/px | Neck width | Shoulder width |
   |---|---|---|---|
   | the old assumption, shoulder width 370 mm | 0.9526 | 171.6 mm (the neck view says 158) | 370 mm |
   | **the neck view's agreed neck width, 158 mm (used)** | **0.8773** | 158 mm | 340.7 mm |
   | (the imported plate) | 0.8978 | | |
   The neck view's own shoulder-to-neck ratio (1137.5 ÷ 518.7 = 2.19) agrees with the torso's (388.4 ÷ 180.1 = 2.16) within 2 %, so the two front views agree with each other at 158 mm, and both disagree with 370 mm by 8 %. The torso now uses the neck width (so that a 2 cm square is the same size in both front views, §1 item 4); 370 mm stays an assumption to check against a real garment. **To confirm with you** (below).
4. `?torso=v1` (until step 7): the page reads `assets/plates/torso-v1/plate.dat` (the imported plate of step 1, frozen) with the same `base.jpg`.

**Landmarks** (plate px; mirror difference = left mirrored about the centre front x 600.7, minus right):

| Pair | Left | Right | dx | dy |
|---|---|---|---|---|
| shoulder-l / shoulder-r | 405.1, 298.7 | 793.5, 295.4 | +2.8 | +3.3 |
| neck-l / neck-r | 510.3, 253.2 | 690.4, 251.8 | +0.7 | +1.4 |
| underarm-l / underarm-r | 430.6, 502.3 | 771.4, 472.2 | −0.6 | **+30.1** |
| cuff-out-l / cuff-out-r | 271.2, 894.8 | 926.8, 897.4 | +3.4 | −2.6 |
| cuff-in-l / cuff-in-r | 383.7, 922.2 | 818.3, 920.2 | −0.6 | +2.0 |
| slit-l / slit-r | 388.4, 1329.4 | 812.9, 1252.4 | +0.1 | **+77.0** |
| hem-l / hem-r | 389.7, 1439.9 | 811.6, 1439.9 | +0.1 | 0.0 |

The photo differs from a mirror at the slit tops (the right slit opens 77 px = 68 mm higher) and the underarms (at the top of the underarm fold, where the sleeve leaves the body: the right fold starts 30 px higher). Against the imported plate the landmarks moved 0.4–5.5 px, except `slit-l` 112.7 px and `slit-r` 35.9 px (the imported ones were the mirror of one guess, 10 px outside the zone), `underarm-r` 32.9 px, and the hem corners 12–13 px (the imported hem corners were the corner of the traced outline, not of the garment).

**Results** (the old grid method still makes the fabric coordinates):

| Check | Imported (step 0) | Measured |
|---|---|---|
| `annotate_torso.py` checks (§9.1: top → bottom, wall gaps ≥ −1.6 px, grid corners, 0 self-crossings, trims inside, front grid bulge) | | all pass (bulge 2.1 / 1.6 %; gaps left 0.8–23.0 px, right −0.3–15.9 px) |
| `plate_invariants.py` closure | 0.138 %, wide pieces 339 px | first build 0.037 %, a 16 px wide piece (the right body side); after the reviews: **PASS** (all invariants PASS) |
| `plate_invariants.py` landmarks | FAIL (`slit-l`, `slit-r` outside) | PASS |
| `plate_invariants.py` trim smooth | PASS | first build: FAIL `slit-r` 2.63 px, `cuff-r` 1.06 px (plain offsets of the measured points); after review 4: PASS (true parallels of the smoothed edges) |
| `fringe.py` (render, mocha) uncovered | 1,221 px = 0.209 %, 794 px in wide pieces | **679 px = 0.117 %**, 186 px in wide pieces (118 px at x 811–814, y 1271–1323) |
| `fringe.py` rim, mocha / sage | 12.3 % / 16.3 % | 22.8 % / 31.8 % (more free edge: the sleeves' inner edges and the gaps; the outlines now lie on the photo's own edge pixel. Steps 3 and 6) |
| `rebuild_check.sh` | | ALL IDENTICAL (4 plates from their sources) |
| `?torso=v1` against 8200 | | identical (no pixel differs) |

- [x] The automatic checks of `annotate.md` §9.1 pass.
- [x] **A person approves the review image `annotate.png`**: `demo/review/torso-straight/annotate.png` and `crops.png` (made by `make_plate.py assets/plates/torso-straight --review`).
  - Review 1 (2026-11-22): **not yet**. "The left side arm has expanded outside the edge." Found: the left sleeve's outer edge lay 10–18 px out on the wall over most of its length (the shaded sleeve against the light wall is a weak step, so the first reading had stood, and the measuring aid kept it). Read again on 2.5–3× crops every 25–50 px; now within about 1 px of the photo's edge (the overlay crops). Corrected at the same time, found on my own 2× look: the right body side below y 1902 (a zig-zag: the aid had jumped between the front panel's edge and the back panel's strip; the outer silhouette is kept) and a 6 px hook at the left hem corner. After these: `plate_invariants.py` closure **PASS** (the only FAILs left are the smoothness of the `cuff-r` and `hem` centre lines, 1.06 and 0.81 px, which step 3 rebuilds).
  - Review 2 (2026-11-22): "the right side armhole anchor has to sit higher up". The right underarm had been put where the sleeve / body crease turns out (source (1150, 880)); the photo's underarm fold (the dark wedge where the sleeve leaves the body) starts at (1152, 705), as on the left (y 720–750). Moved there: the right armhole seam now ends at the fold, and the sleeve's inner edge continues from it. The underarms now differ from a mirror by 30 px (was 87).
  - Review 3 (2026-11-22): "the dotted red lines on both sides need rework". They were the body's runs hidden under the sleeves, drawn as a guessed diagonal through each sleeve (underarm → one guessed point → the gap top). Reworked: from the underarm down to where the wall gap opens, the body now ends on the sleeve's inner edge, the one measured line, shared by the front and the sleeve (`sleeve-body-l`, `sleeve-body-r`, seams); below that the sleeve's inner edge is free against the gap (`sleeve-gap-l/r`). No guessed point is left in an outline (the grid, until step 4, still passes under each sleeve through one point). Validator PASS, closure PASS.
  - Review 4 (2026-11-22): "the right and left sleeve-end lace lines are irregular; the purple line on the neck is misaligned; the left sleeve has an unusual curve between the anchors; have the hem lace line end at the anchors". Found and fixed:
    - the trim centre lines were vertex-normal offsets of a few measured points, then extended along their last segment: not parallel, with hooks at the ends. Now every trim is a true parallel (the edge densified every 2 px, each normal averaged over ±8 px of curve), cut where it leaves its zone; the hem lace and the neck lace end above / below their corner anchors (`hem-l`–`hem-r`, `neck-l`–`neck-r`; they had run on up the steep ends of the edge, past the anchors).
    - the armholes and the cuff folds were the measured points as they were (1–3 px wobble; the left armhole had a visible bump between the shoulder and underarm anchors). A seam and a cuff fold are smooth: each is now a least-squares fit through its measured points (armholes: cubic in y; cuffs: quadratic in x), the shared end points kept. It moved the points by 2.0–2.5 px on average (at most 6.2 px on the armholes, 5.1 px on the right cuff).
    - `plate_invariants.py` on the torso: **ALL PASS** (trim smoothness too).
  - Review 5 (2026-11-22): **approved**.
- [x] Every landmark of the torso is measured. The left and right landmarks differ from a mirror where the photo differs (table).
- [x] The plate builds from its source (`rebuild_check.sh`) and renders with the old grid method. `?torso=v1` gives back the imported plate.
