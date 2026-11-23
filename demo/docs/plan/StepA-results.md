# StepA results

Plan: `StepA.md`. Branch `stepA` (from `numeric` 430c3fd), worktree `../myshoppe-stepA`, port 8300. Reference: `numeric` on 8200.

## Step 0: Baseline, review set, closure in the render

**Done:**
1. Branch `stepA` and worktree `../myshoppe-stepA` from 430c3fd; the plan (`StepA.md`), `breather.md` and `DedhD.md` §11 committed here. Server on 8300.
2. `silhouette/checks/plate_edges.py`: the edges of a plate for the review tools. At step 0 it classifies each zone outline geometrically (every 1 px): `frame` (within 0.6 px of the border), `seam` (2.5 px outward is inside another zone, or the point is under a zone drawn later), `cut` (the front's neck dip), `free` (the rest). Step 1 replaces the geometry with the typed edges of `plate.dat`.
3. `silhouette/checks/edge_crops.py <canvas> <plate> <out> [--photo <off>]`: the review set. One crop at each landmark and one every 150 px along each free edge; each tile is the photo and the render of the same 40 × 40 plate px box, 3× with nearest pixels. Computed from the plate: no file of its own.
4. `silhouette/checks/fringe.py <canvas> <plate> [--photo <off>] [--debug <png>]`: closure in the render. Uncovered = photo garment (saturation < 24, 3 × 3 median: the rule of `plate_invariants.py`) where the render is within 4 levels of the photo, within 10 px of rendered fabric, openings left out; pieces wider than 1 px = what survives a 2 × 2 erosion. Rim = free-edge samples whose brightest value between 1.5 px inside and 3.5 px outside is brighter by more than 8 levels than both 4 px inside and 6 px outside.
5. Shots: `node silhouette/checks/cdp_shot.mjs <out> <port> "view=<v>&fabric=mocha&trims=none&stage=600"` (and `fabric=off`, `fabric=sage`). `stage=600` at DPR 2 gives a 1200 × 1600 canvas: one canvas px = one plate px, so every count below is in plate px. The photo for the comparison is the `fabric=off` render (the photo as the page draws it).
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
1. `silhouette/pipeline/platedat.py`: `BSP2`. "BSP2", u16 version 2, u16 unit (100 = 0.1 px), u32 header length, a JSON header, int16 curve deltas. In the header every polyline is `{"@c": index}` and identical curves are stored once (the same rule as `BSP1`, now for any list of points: edges, grids, trims, stitches, occluders, the neck block). Reader, writer, validator (`--check`), `--dump` (one value per line, curves one point per line, sorted keys) and `legacy()`: the plate header and the zone data in the shapes the map code reads. The data model is in its docstring.
   - **edges** `{name: {type, points, zones (a seam), under (a hidden run)}}`; **zones** `{id, order, outline: [[edge, ±1], ...], grid, widthPx}`; **trims** `{id, order, widthMm, type, edge, offsetMm, join, centre}` in drawing order; **stitches, occluders, landmarks, invariants, settings** (`thetaDeg`, `tuck`, `shadeSmoothMm`), **decisions** (`shadeMedian`, `shadeSmoothMm/Px`, `shadeSpace`, `shadeEncoding`, the neck block, each trim's `side` / `lengthCm` / `vMax`, each zone's size in cm).
2. `annotate_neck.py`, `annotate_sleeve.py`, `annotate_hem.py` are modules: `base(plate)`, `measure()`, `review(P, base)`; run alone they run their checks and write nothing. The measured lists did not change; each outline is now written as a chain of named, typed edges. The hem's `hem-bl` / `hem-br` (made in numeric step 10 by `snap_outline.py edge-trim`) and the trim order (`trim-order`: the hem laces after the slit trims) are trim data in `annotate_hem.py`, as are the plate's `invariants`. The `edge` of each trim names the edge it hangs on (step 3 derives the centre lines from it).
3. `silhouette/pipeline/make_plate.py <plate> [--review] [--no-check] [--dump-mesh]` is the build: source → maps in memory (`rasterise`, the old arithmetic unchanged) → decisions → `base.jpg` + `plate.dat`. The base is encoded once as JPEG and the decisions are taken from the decoded JPEG, as the page sees it (taking them from the image before the JPEG moved the neck block's fill colours by 1 level). `--review` writes `annotate.png`, `check.png` and the edge crops (cut from `check.png`) into `demo/review/<plate>/`. As a module: `build()`, `maps_of(plate)` (the maps of a committed `plate.dat`, in memory), `rasterise()`.
4. The torso: a one-off converter (in the scratchpad, never committed) read its `zones.json` + `plate.json` and split each outline into typed edges by the geometry of step 0: front = `front-0` (left shoulder, free), `neck` (cut), `front-2` (right shoulder, free), `front-3` (under `sleeve-r`), `front-4` (body sides and hem, free), `front-5` (under `sleeve-l`); each sleeve one free edge. `make_plate.py` rebuilds the torso from this imported data (and keeps its `base.jpg`) until step 2.
5. Readers moved to `platedat.py` / `make_plate.maps_of`: `plate_invariants.py`, `plate_checks.py` (its size rule now counts what ships: `base.jpg` + `plate.dat`), `polish_metrics.py`, `reveal_metrics.py`, `map_diff.py`, `trim_match.py`, `mesh_check.mjs` (through `Plate.parseDat`), `plate_edges.py` (the typed edges in place of step 0's geometry), and the page: `Plate.parseDat` reads `BSP2` and gives the same `{ plate, zones }` as before; every view (the `?geom=maps` path too) reads `plate.dat`. Removed: `BSP1`, `make_dat.py`, `dat_check.mjs`, the page's `?dat=0`; `snap_outline.py` keeps only its helpers (its commands wrote `zones.json`). `extract_zones.py` and `fit_zones.py` (planned for step 2) are removed here: they wrote `zones.json` and cannot run any more.
6. Removed from the 4 plate folders: `zones.json`, `plate.json`, `annotate.png`, `check.png`. The map PNGs stay for `?geom=maps` until step 7 (they are frozen: the build no longer writes them).
7. `.gitattributes`: `demo/assets/plates/*/plate.dat diff=dat`; `tools/README.md` gives `git config diff.dat.textconv "python3 demo/tools/platedat.py --dump"`.
8. `silhouette/checks/rebuild_check.sh`: every plate rebuilt from its source into a scratch copy; `base.jpg` and `plate.dat` compared byte for byte.

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
1. `assets/torso-base.png` → `silhouette/sources/torso-straight.png` (`git mv`).
2. `silhouette/views/torso.py` (from the template of `annotate_neck.py`): `base()` is the old `make_base.py` (sparkle patch, 1792 × 2389 cut, 1200 × 1600), and the rebuilt `base.jpg` is byte-identical to the committed one. Every edge was read on gridded crops of `source.png` (2–3×, 10 px grid, true colour and raised contrast). The edges against the wall and the sleeve / body creases were then placed on the strongest luminance step within 6 px of the reading (a measuring aid; where the step is weak the reading stays) and checked again on overlay crops. From the reading only: the neck edge (the white front meets the grey band of the back neckline inside the opening: the aid jumped to the form's edge, 4–5 px higher), the right armhole (a faint line on lit white: the aid drifted 5 px), the right sleeve's inner edge below y 1200 (the gap to the body is 3–8 px and the aid put both on the body), the left cuff. How it was done is in the script's docstring.
   - Zones: `front` (shoulders free, `neck` cut, the armholes and then the sleeves' inner edges down to where the wall gap opens: **shared seams** with each sleeve (after review 3), the body sides free from there, the hem free); `sleeve-l`, `sleeve-r` (outer edge free, cuff free, inner edge free against the wall gap). The torso has no `under` run any more.
   - **A wall gap between each cuff and the body** (left from y 1185 source px, up to 23 px wide; right from y 1190, up to 16 px) was not in the traced plate: there the old front covered the wall (the body-side strip of numeric step 11 was the other half of that error).
   - Trims from the measured edges: neck 6 mm inside the neck edge, cuffs 12.5 mm above the cuff edges, slits 4 mm inside the body sides from the slit tops, hem 15 mm above the hem; the grid (until step 4): the shoulder runs as its top, the side edges 6 px outside the body sides (the outline cuts), the sleeves with their cap as a point and `widthPx` = area ÷ mean side length.
   - `make_base.py` is removed. `silhouette/checks/rebuild_check.sh` now rebuilds the folders that have a `source.png`.
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

## Step 3: Free edges snapped to the photo

**Done:**
1. `silhouette/pipeline/snap_edges.py`, a module of the build (alone: the report, writing nothing). For every `free` and `cut` edge: samples every 2 px with the outward normal; a local colour model (mean colour 3–8 px inside and outside; where that finds no contrast, 1.5–4 px: a gap narrower than 8 px) and the sub-pixel 50 % crossing of the projection between the two (±8 px, the crossing nearest the edge); a robust Whittaker fit of the displacement (data + λ 4 × the squared second difference at 2 px spacing, samples more than 1.2 px off dropped, 3 rounds), then the colour model again at the fitted edge and once more; points every 2 px, thinned to 0.05 px. A weak sample (inside and outside closer than 14 levels) keeps its measured position. A sample that a later zone covers, or that lies over another zone (4 px outward is that zone's fabric: a sleeve's edge over the body, white over white), also keeps it and is counted apart: it is not a contour against the background.
2. Corners: where edges meet, the corner is the mean of the snapped ends (kept on the border at the frame); a seam's end follows, and its first 12 px move with it (a linear taper). Seams are not moved otherwise. Grid points and landmarks that sat on a moved corner follow it; the sleeve view's occluder (the mannequin arm) is now a chain of the plate's edges (`arm-l`, `arm-r`, `front-under-cuff`), so it follows too.
3. `make_plate.py`: source → snap → **trims derived from their edges** (`derive_trims`: the parallel at `offsetMm` on the zone's side, normals averaged over ±8 px, a moving average over 4 mm, kept inside the zone and between the trim's anchors `from` / `to`; the annotate scripts now give only the edge, the offset and the anchors) → decisions → `plate.dat`. The hem view's `hem-bl` / `hem-br` are derived from the side pieces' hem edges like the others. Stitches are kept as measured (they are photographed lines, not trims).
4. The neck block takes its photographed edge from the `cut` edge (it was "the front outline below the grid top": a snapped corner no longer sits exactly on the grid top).
5. **Measuring corrections found by the snap's checks** (written in the annotate scripts):
   - neck view: where each wall gap under the arms closes again, the sleeve lies on the body; the two separate lists there (the body 2 px under the sleeve) are now ONE shared seam (`join-l`, `join-r`, the sleeve's edge), as the torso has since step 2;
   - neck view, right underarm (the 1,251 px piece of uncovered garment): read again on `source.png`. The front and the sleeve touch down to the apex of the wall wedge (source (1714, 1362): above it a white fold, not wall; `underarm-r` moved there from (1702, 1230)), the wedge closes at (1655, 1700); the body side of the wedge lay 5–10 px inside the photo's edge, beyond the snap's ±8 px reach.
6. The default neckline, re-measured from the snapped neck edge (depth below the corner line at the centre front): neck view **39.7 mm** (was 40.9; 130.4 px × 0.3046 mm), torso view 32.6 mm (was 29.9; the traced v1: 25.2). `assets/looks/straight-kurta.json`: `neck.depthMm.default` and its first stop 40.9 → 39.7. The two front photos now disagree by 7.1 mm (was 15.7 mm in `halfway` step 6); the image fix of `DedhD.md` §11.1 stays for step 8.
7. `plate_invariants.py --outline`: the coverage of the outlines alone, with the StepA limits (closure ≤ 0.02 %, no piece wider than 1 px by a 2 × 2 erosion; trim offset measured exactly against the trim's own edge, mean within 0.5 px, std ≤ 1.0 px).

**Edge accuracy** (plate px; the fit against the sub-pixel crossings of the last round; weak share of the contour samples; covered / over and dropped samples counted apart):

| View | Edge | Samples | Mean move | Fit vs crossing: median / 95 % / max | Weak | Covered / over | Dropped | |
|---|---|---|---|---|---|---|---|---|
| torso | `shoulder-l` | 59 | 0.66 | 0.06 / 0.22 / 0.55 | 0.0 % | 0 | 0 | PASS |
| torso | `neck` | 102 | 1.97 | 0.05 / 0.23 / 0.44 | 0.0 % | 0 | 1 | PASS |
| torso | `shoulder-r` | 57 | 0.19 | 0.05 / 0.13 / 0.17 | 0.0 % | 0 | 0 | PASS |
| torso | `body-l` | 325 | 0.52 | 0.04 / 0.15 / 0.38 | 0.0 % | 8 | 0 | PASS |
| torso | `body-r` | 323 | 0.42 | 0.03 / 0.15 / 1.18 | 2.4 % | 34 | 0 | PASS |
| torso | `hem` | 222 | 0.69 | 0.09 / 0.71 / 0.94 | 36.0 % | 0 | 15 | **FAIL** |
| torso | `outer-l` | 309 | 1.40 | 0.04 / 0.11 / 0.16 | 0.0 % | 0 | 0 | PASS |
| torso | `cuff-l` | 57 | 3.11 | 0.05 / 0.20 / 0.31 | 0.0 % | 0 | 0 | PASS |
| torso | `sleeve-gap-l` | 67 | 0.29 | 0.04 / 0.12 / 0.12 | 0.0 % | 8 | 1 | PASS |
| torso | `outer-r` | 311 | 0.20 | 0.04 / 0.09 / 0.17 | 0.0 % | 0 | 0 | PASS |
| torso | `cuff-r` | 57 | 1.58 | 0.05 / 0.16 / 0.77 | 0.0 % | 0 | 1 | PASS |
| torso | `sleeve-gap-r` | 64 | 1.13 | 0.09 / 0.63 / 0.66 | 0.0 % | 34 | 0 | PASS |
| neck | `shoulder-l` | 169 | 1.59 | 0.07 / 0.23 / 0.58 | 0.0 % | 0 | 0 | PASS |
| neck | `neck` | 317 | 1.04 | 0.07 / 0.49 / 1.00 | 0.0 % | 0 | 9 | PASS |
| neck | `shoulder-r` | 167 | 2.12 | 0.05 / 0.17 / 0.36 | 0.0 % | 0 | 0 | PASS |
| neck | `body-l` | 159 | 2.69 | 0.06 / 0.47 / 1.03 | 3.3 % | 38 | 5 | PASS |
| neck | `body-r` | 139 | 2.26 | 0.09 / 0.44 / 1.07 | 0.0 % | 4 | 1 | PASS |
| neck | `cap-l` | 23 | 3.80 | 0.05 / 0.27 / 0.36 | 0.0 % | 0 | 0 | PASS |
| neck | `sleeve-in-l` | 163 | 0.68 | 0.12 / 0.90 / 1.18 | 56.8 % | 38 | 5 | **FAIL** |
| neck | `cap-r` | 23 | 2.56 | 0.06 / 0.64 / 0.97 | 0.0 % | 0 | 0 | PASS |
| neck | `sleeve-in-r` | 138 | 1.96 | 0.09 / 0.67 / 1.15 | 35.1 % | 4 | 11 | **FAIL** |
| sleeve | `shoulder-top` | 108 | 1.94 | 0.13 / 0.54 / 1.10 | 10.2 % | 0 | 14 | **FAIL** |
| sleeve | `neck` | 235 | 1.21 | 0.09 / 0.32 / 0.63 | 0.0 % | 0 | 3 | PASS |
| sleeve | `far-shoulder` | 129 | 0.82 | 0.03 / 0.13 / 0.60 | 0.0 % | 0 | 0 | PASS |
| sleeve | `arm-r` | 161 | 0.80 | 0.18 / 0.70 / 1.17 | 47.2 % | 0 | 11 | **FAIL** |
| sleeve | `arm-l` | 118 | 1.04 | 0.28 / 0.72 / 1.16 | 6.8 % | 0 | 6 | **FAIL** |
| sleeve | `body-low` | 60 | 1.11 | 0.03 / 0.09 / 0.12 | 0.0 % | 0 | 0 | PASS |
| sleeve | `body-gap` | 168 | 2.01 | 0.04 / 0.13 / 0.22 | 0.0 % | 5 | 0 | PASS |
| sleeve | `cap` | 13 | 0.38 | 0.30 / 1.08 / 1.08 | 0.0 % | 0 | 1 | **FAIL** |
| sleeve | `outer` | 756 | 0.71 | 0.03 / 0.09 / 0.18 | 0.0 % | 0 | 0 | PASS |
| sleeve | `cuff` | 158 | 1.30 | 0.09 / 0.39 / 0.80 | 1.7 % | 43 | 2 | PASS |
| sleeve | `sleeve-in` | 340 | 1.45 | 0.05 / 0.30 / 0.79 | 0.0 % | 147 | 1 | PASS |
| hem | `slit-front` | 542 | 1.20 | 0.07 / 0.44 / 1.18 | 0.0 % | 6 | 9 | PASS |
| hem | `hem-front` | 329 | 1.66 | 0.07 / 0.42 / 1.11 | 0.6 % | 0 | 0 | PASS |
| hem | `front-left-low` | 37 | 0.94 | 0.05 / 0.16 / 0.33 | 2.8 % | 1 | 2 | PASS |
| hem | `back-right` | 648 | 1.61 | 0.03 / 0.09 / 0.15 | 0.0 % | 0 | 0 | PASS |
| hem | `hem-back` | 52 | 1.09 | 0.09 / 0.34 / 0.47 | 0.0 % | 0 | 0 | PASS |
| hem | `slit-back` | 538 | 1.52 | 0.05 / 0.16 / 0.50 | 0.0 % | 6 | 0 | PASS |
| hem | `hem-left` | 108 | 1.91 | 0.03 / 0.09 / 0.15 | 0.0 % | 1 | 0 | PASS |
| hem | `left-edge` | 281 | 0.27 | 0.02 / 0.07 / 0.10 | 0.0 % | 0 | 0 | PASS |

33 of 40 edges pass. The 7 that fail, and why (open items, with their measurement):
- **torso `hem`**, weak 36 % (x 527–690 at the bottom left: the white hem over the pale floor, no colour step) — kept as measured;
- **neck `sleeve-in-l`, `sleeve-in-r`**, weak 57 % / 35 %: the sleeves' side of the wall gaps is a shaded fold against a beige wall of nearly the same colour;
- **sleeve `arm-r`, `arm-l`**, weak 47 % / 7 %: the garment against the linen mannequin arm (same colour family);
- **sleeve `shoulder-top`**, weak 10 % (8 px at the shoulder point, where the cap meets);
- **sleeve `cap`** (13 samples, 26 px): 95 % 1.08 px > 0.75 (a short curved edge; max 1.08 ≤ 1.5).
The weak spans keep the measured points (as the plan says), so they are no worse than before; the plan's risk table applies ("AI images have soft or doubled edges in places: mark the span weak; review at 2×").

**Closure of the outlines** (`plate_invariants.py --outline`, in memory: the grid still limits the render until step 4):

| View | Uncovered garment | Pieces wider than 1 px | Trim offsets (exact, against their edges) | Other |
|---|---|---|---|---|
| torso | 18 px = **0.0031 %** | 5 px (small specks, x 406–812, y 836–1436) | all 6 PASS (`cuff-l` 14.23 against 14.25 px, std 0.03) | `hem` smoothness 0.82 px (limit 0.8) |
| neck | 282 px = 0.0208 % | 97 px: a soft grey half-shadow band, 2–3 px wide, on the body's side of the right wall wedge (x 1087–1109, y 1159–1320) | PASS | hairlines between zones 75 px (the outlines' own rasterising along shared seams: step 4's `underPx` covers them); `plate_checks.py` grain tilt 10.8° (the grid's right edge now has the wedge's kink: the grid goes in step 4) |
| sleeve | 626 px = 0.0429 % | 212 px (along the shoulder line and the arm notch: the weak spans above) | PASS (`cuff-l` 36.94 against 36.96 px, std 0.06) | |
| hem | 184 px = **0.0132 %** | 18 px at the front hem's bottom (x 309–470, y 1347–1359) | all 5 PASS | |

(Before the snap, step 0 / numeric step 11, grid × outline: torso 0.138 %, neck 0.239 %, sleeve 0.097 %, hem 0.026 %.)

| Check | Result |
|---|---|
| `rebuild_check.sh` | ALL IDENTICAL (the snap is deterministic) |
| `plate.dat`, 4 views | 30,256 B (torso 9,282, neck 5,970, sleeve 6,754, hem 8,250) |
| The page on 8300, the 12 `--numeric` queries (4 views; the neckline at depth 20 and 100 mm, width 132 and 194 mm) | all 12 drawn, no console errors |

- [ ] Edge accuracy for each free edge: 33 of 40 edges pass; 7 fail on weak spans or one short curved edge (listed above).
- [ ] Outline closure ≤ 0.02 %, no piece wider than 1 px, on all 4 plates: torso and hem within the share; neck 0.0208 %, sleeve 0.043 %; small wide pieces on all four (listed). Open.
- [x] Trim offset: mean within 0.5 px of the offset, std ≤ 1.0 px, every trim (`cuff-l` included). Trim smoothness: all pass but the torso `hem` (0.82 px).
- [x] `rebuild_check.sh` passes (the snap is deterministic).

## Step 4: The fabric frame replaces the Coons patch

**Done:** each zone's `frame` (axis, anchor, half-width cubics, θ, sag) is measured in its view and fitted by the build (`silhouette/pipeline/plateframe.py`). The map projects onto the axis with the normals interpolated along each segment, using a cylinder arc across (continued linearly past the silhouette) and arc length along. Coverage = the outline, plus 6 px under-strips at the seams (`tuck` gone). `Plate.frameUV` and `FRAME_FS` do the same arithmetic.

| Check (`plate_invariants.py`, all 4 plates, 2026-11-22) | Result |
|---|---|
| No fold (Jacobian > 0, the box + 16 px) | 0 points in every zone |
| Grain: constant-u lines within 3° of the axis (95 %) | 0.32–2.94° (worst: the sleeve view's front) |
| UV rate at the axis | 0.998–1.001 × face-on (limit ±2 %) |
| u = 0 through the centre-front landmarks | 0.00 px |
| Parity, `frame_check.mjs` | ≤ 3 × 10⁻¹⁴ cm (limit 10⁻⁴) |
| Neckline: a depth change of ±20 mm | neck view 20.01 / 19.70 mm, torso view 20.05 / 19.67 mm (±1 px); no hole at the range ends |
| Hairline gaps | 0 px on the neck view (the 249 px of `numeric` and the 87 px of step 7 are gone: extension item 6) |

**Cross-view** (information for the swatch plan): the landmarks seen in two views, with their (u, v) in cm in each view's frame:

| Landmark | Torso | Neck | Sleeve | Hem |
|---|---|---|---|---|
| `neck-l` | (−8.1, 0.0) | (−8.1, 0.0) | (−11.0, −2.2) | |
| `neck-r` | (8.1, 0.0) | (8.3, 0.0) | (4.3, 1.0) | |
| `cf-neck` | (0.0, 3.3) | (0.0, 4.0) | | |
| `shoulder-r` | (22.1, 3.7) | (22.6, 3.8) | | |
| `underarm-l` | (−18.6, 21.6) | (−18.9, 17.2) | | |
| `hem-l` | (−23.8, 101.0) | | | (−7.9, 115.7) |

The two front views agree on the neck points within 2 mm. The centre-front depth differs by 7 mm (the photos' own disagreement: step 8). `hem-l` names a different point in the torso view (the slit corner) than in the hem view. The sleeve view's front is a turned view, so its u differs.

**Person:** the silhouette was approved on the before / after sheet (2026-11-22). The grain checker at 2× was not reviewed on its own.

## Step 5: Exact maps on the page

**Done:**
- `maps.js`: one stencil pass per polygon and one `FRAME_FS` quad per zone.
- 16-bit packing (RG = u, BA = v, over 128 cm); `uOff` (0.5, 0.5): an integer coordinate is a pixel centre.
- The build fills by pixel centre, even-odd (`fill_exact`), as the GPU does.
- `?perf=1` and `?syncbuild=1`.
- Since the extension, the trims are the trim field (`TRIM_FS`).

| Check (2026-11-22) | Result |
|---|---|
| Coverage, page against build (`maps_check.py`) | Only the 1 px edge band differs on neck, sleeve and hem. On the torso, 1 px outside it at (821, 916), from before the extension (open) |
| uv | max 0.0013–0.0023 cm (limit 0.01; one 16-bit step is 0.0020) |
| Trims (the trim fields since the extension) | `s` 0.0010 cm, `t` 0.0098 mm on all 4 views |
| Build time, software renderer (`?syncbuild=1`) | torso 1114, neck 1048, sleeve 1095, hem 1194 ms (`numeric`: 1.4–3.0 s): PASS |
| `plate.dat`, 4 views | 29,178 B (limit 40 KB) |

## Step 6: Soft free edges

**Done:** id A = (d + 3) / 4 on a ribbon from 3 px outside to 1 px inside every free edge. The shader's coverage is clamp(0.5 + d), and beside the edge it takes the photo 3 px beyond it. Seams, frame edges and the neck cut stay hard.

| `fringe.py` (mocha / sage; limits: rim 0.5 %, halo 10 %) | Torso | Neck | Sleeve | Hem |
|---|---|---|---|---|
| Rim, mocha | 0.25 % | 0.00 % | **0.88 %** | **2.61 %** |
| Rim, sage | **1.13 %** | **2.11 %** | **0.94 %** | **2.69 %** |
| Halo, median / 95 % | 1.6 / **12.7 %** | 1.0 / 4.6 % | 2.4 / **235 %** | 1.9 / **12.6 %** |
| Step 0 rim, mocha | 5.7 % | 26 % | 7.0 % | 16.2 % |

The rim fell by 80–100 %. The limits are met on the torso and the neck view in mocha only, and the halo only on the neck view. The worst 5 % of the halo comes from weak spans: the sleeve view's arm edges, and the torso hem over the floor (FAILs, open).

## Step 7: Remove the old artifacts; docs and skills

**Done:** the Coons patch, the grids, `tuck`, `widthPx`, the map PNGs, the old switches and tools (StepA §5). The docs and both skills were rewritten. After the cleanup (`plan/cleanup.md`), a plate folder holds `base.jpg` + `plate.dat`, and the pipeline lives in `demo/silhouette/`.

| Check | Result |
|---|---|
| The removal search of step 7 | Only StepA's own plan and results, the history parts of `render.md`, `DedhD.md` and `breather.md`, and three names that only match the pattern: `uvOffsetCm`, `uUVOff` (the frame's 16-bit offset) and `widthPx0` (the live neckline's width) |
| `plate_invariants.py` | neck ALL PASS. Torso, sleeve and hem: one FAIL each, closure (torso: a 6 px piece; sleeve: 0.0596 %; hem: a 10 px piece) (open) |
| `rebuild-check` | ALL IDENTICAL |
| The skills' quick reference | runs as written (`python3 silhouette/plate.py ...`) |
| The review set, by a person | approved on the before / after sheet (2026-11-22) |

## Step 8: Device and person checks

**Passed** (the owner, 2026-11-23: "device checks have passed for the current html and works well"; the individual numbers were not supplied). The check was asked on a phone and a laptop of the published zip (2026-11-22). For each view, open `testing.html?step=<cloth|neck|sleeve|hem>&perf=1` and write here:

| Device | View | Build (ms, limit 50 laptop / 250 phone) | Draw (ms) | Drag (fps, ≥ 30) | Float render targets |
|---|---|---|---|---|---|
| | | | | | |

The neck-depth agreement of the two front views stays open: the photos disagree by 7 mm at the centre front (step 4 cross-view), and no new image was supplied.

## Step 9: Close

StepA is closed (2026-11-22), with step 8 pending on devices and the open items below. Commits: steps 0–2 `9b5bc58`, `20d8e68`, `b2af865`; steps 3–7 and the extension `da48bfc`; the cleanup `a6dc1be`, `30dff16`. All branches are consolidated into `main`.

| §1 item | Evidence | State |
|---|---|---|
| 1. Fabric to the photo's edge, no rim | Rim (mocha) 0.25 / 0.00 / 0.88 / 2.61 % (step 0: 5.7 / 26 / 7.0 / 16.2 %); leftover garment 0.008 / 0.003 / 0.038 / 0.001 % | Met on torso and neck; sleeve and hem open |
| 2. Seams: no hairline, step or double edge | Hairline gaps 0 px; the torso band beside the sleeve and the neck-view "holes" fixed (extension items 4, 6) | Met |
| 3. Soft free edges | The coverage ramp on every free edge; halo median 1.0–2.4 % | Met in the median; the 95th percentile is open on 3 views |
| 4. The print lies as cloth | No fold; grain ≤ 2.94°; rate ±0.2 %; u = 0 through the centre front; anchored at the centre front and the neck-point line | Met |
| 5. Laces | Real width and repeat; no wedge, streak or fan (trim fields complete, 0 seams within 30 mm); silhouette ends; slit / hem mitre; before / after approved | Met |
| 6. The live neckline | The lace hangs on the live edge; depth response ±1 px; reveal fills as before | Met |
| 7. A plate folder | `base.jpg` + `plate.dat`; the source in `silhouette/sources/` | Met (two files since the cleanup) |
| 8. Typed edges; trims derived | `platedat.py --check` passes; trim lines from their edges | Met |
| 9. Fabric frame, no Coons | Steps 4 and 7 | Met |
| 10. The torso measured | Step 2; hem, seam and slit corner read again in the extension | Met |
| 11. `plate_invariants.py` passes | neck ALL PASS; the others fail closure only, each written with its number | Open (3 closure FAILs) |
| 12. The shade on the GPU | Built in `maps.js`; float targets on devices: step 8 | Passed (step 8, 2026-11-23) |
| 13. Speed | Software 1.05–1.19 s per view (faster than `numeric`); device budgets: step 8 | Passed (step 8, 2026-11-23) |

**Open items, carried to the next plans:**
- Closure FAILs: the sleeve view 0.0596 %, and small pieces on the torso (6 px) and the hem (10 px).
- The rim on the sleeve and hem views; the halo's 95th percentile on the torso, sleeve and hem views (weak spans).
- 1 px of map coverage on the torso.
- Step 8 on devices.
- The neck-depth agreement (a new image).
- The lace widths: the pearl lace's 30 mm is an assumption (the swatch and lace plan).

## Extension (§8): the lace laid on the garment, and the last silhouette items

**Why:** the review of 2026-11-22 (the user's marked screenshots) found the lace layout to be the weak part. The measured causes and the decision (**the lace decides**: each lace keeps its own width and repeat) are in `StepA.md` §8.

**Done (steps L1–L4; not committed):**
1. **The trim field** (`silhouette/pipeline/trimfield.py`; `plate.js` `trimElements`; `maps.js` `TRIM_FS`).
   - A trim is its garment edge between its anchors (`line`, from `derive_trims`), not a centre line. For each pixel near it: `t` = mm from the edge (+ on the garment), `s` = the cloth length along the edge in the zone's fabric frame, 0 at the anchor.
   - One element per 2 px segment, between smooth normals (the chord over ±30 mm). Neighbouring elements share their normals, so there is no wedge and no overlap at a bend.
   - Two element types were tried first, nearest segment plus vertex wedges; they gave seams of `s` on the inner side of every bend, up to 1.6 cm, and were dropped.
   - The band runs from 8 mm outside the edge to 56 mm inside (the widest lace), so it does not depend on the lace chosen.
   - Open ends carry on and the outline cuts them; the slit top is a cut (square) end. The overhang exists only along the edge.
   - The slits are a field of their own (`uvts`), mitred against the hem in the shader by the nearer edge.
2. **Trim data** (the annotate scripts and `plate.dat`): `{edge, from, to, type, anchor, cut}` plus the derived `line`, `side` and `zone`. `widthMm`, `offsetMm`, the centre line, `vMax`, `outerV` and `FLIP` are gone.
3. **The page** (`testing.html`):
   - the lace at its own width; a motif centred at the frame's u = 0;
   - the slits with whole repeats from the hem corner;
   - the live neck lace hung on the live edge (`dL` and its arc length from the centre front; the neck area made wide and deep enough for the widest lace);
   - the overhang lit like the garment 3 px inside the edge;
   - the lace texture's transparent texels given its mean colour (its mipmaps no longer grey it);
   - the glow on the lace only.
4. **Silhouette** (`annotate_torso.py`, step L4 items 0–2, read again on `source.png`):
   - The hem over the stand: it ran straight at y 2200, but the garment rises to 2161 over the stand, so 20–37 px of the stand were fabric. This, not the overhang, was the black lace over the stand. The hem snap is now weak on 1.3 % of its length (was 36 %).
   - The right sleeve's inner edge, y 725–1085: 4–14 px to the right, on the sleeve's shaded side. This was the band beside the sleeve.
   - The right body side, y 1980–2140: 1–4 px inside the back panel's white folded edge. This was the strip at the slit corner.
5. **The neck view's fabric was flat** (the user, 2026-11-22: "neckline swatches are missing"). With the neck lace laid live, that view has no baked trim, so the page made a 1 × 1 placeholder for `uvt`. `flatTexture` bound it on the active unit, which was unit 2 (the fabric's `uv`), so the fabric's coordinates became one value. `flatTexture` now uses a scratch unit (15). The neck view's fringe, measured again: rim 3.29 % (mocha), 4.41 % (sage), as at step 7.
6. **Neck view, the two "gaps" between the arms and the body** (L4 item 3). The user's call: they are the kurta's own white fabric in shadow, not the wall. They close as garment: the sleeve's inner edge is now a seam shared by the front and the sleeve (`annotate_neck.py`), and the body-side "gap" edges are gone. Results:
   - the neck plate: ALL PASS. Closure was 0.0206 % and 87 px of hairlines; the false openings caused both.
   - render (`fringe.py`): uncovered 0.003 % with no piece over 1 px (was 0.013 %, 6 pieces); rim 0.00 % mocha (was 3.29 %), 2.11 % sage (was 4.41 %); halo 95 % 4.6 % (was 94 %: the grey half-shadow of the right wedge, open since step 3).

**Measured:**

| Check | Result |
|---|---|
| `rebuild_check.sh`; `plate.dat` | ALL IDENTICAL; 29,178 B for the 4 views (after item 6) |
| Trim line on its edge | mean 0.03–0.24 px, std ≤ 0.21 px (limits 0.3 / 0.5); smoothness ≤ 0.23 px (the torso hem's 0.82 px of step 7 is gone) |
| Trim field complete (1 px to 30 mm in) | 0 pixels without a value, on every trim of the 4 views |
| Seams of `s` within 30 mm of the edge | 0 everywhere. Deeper: the torso hem's bend over the stand (5) and the right cuff (1), which only the 40 mm and 53 mm laces reach |
| Page field against the build (`maps_check.py`) | `s` within 0.0010 cm, `t` within 0.0098 mm (one 16-bit step), on all 4 views |
| `frame_check.mjs` | ≤ 3 × 10⁻¹⁴ cm |
| Page | 17 queries (6 laces, slits on and off, neck depth 20–100 mm), no console error |
| Rim (mocha) | torso 0.25 % (step 7: 0.35 %); neck 0.00 % (was 3.29 %, item 6); sleeve and hem unchanged (0.9 / 3.1 %) |

**Before / after** of every area marked on 2026-11-22: [`img/stepA-lace-before-after.jpg`](img/stepA-lace-before-after.jpg). The changes it shows:
- the streaks in the hem view's lace are gone;
- the fan at the slit / hem corner is one lace;
- both ends of the cuffs and of the sleeve-view neck run out to the silhouette;
- the hem lace follows the hem over the stand;
- the lace is shown at its real 30 mm.

**Open:**
- ~~A person's approval of the before / after sheet~~: **approved** by the user, 2026-11-22.
- Closure FAILs from before the extension: sleeve 0.0596 %; small pieces on the torso (6 px) and the hem (10 px). (The neck's are fixed by item 6.)
- `maps_check.py` coverage on the torso: 1 px at (821, 916), from before the extension.
- The halo's 95th percentile is still over 10 % on the torso, sleeve and hem views (median 1.6–2.4 %); the neck view is now 4.6 %.
- The lace widths are the sidecars' (pearl 30 mm is still an assumption). At the lace's real width the neck lace is 30 mm (it was 12 mm).
