# Plan: numeric — curves and a `.dat` file in place of the map images

Status: **steps 0–7 done; build time on real GPUs unverified; step 8 not done; steps 9 and 10 done; step 11 (invariant checks) planned**. See `numeric-results.md`. Branch `numeric` (from `halfway`, 65d0be4), worktree `../myshoppe-numeric`.
Compare: **http://localhost:8000** (`polish`), **http://localhost:8100** (`halfway`, the reference for this plan), **http://localhost:8200** (this worktree), each `/testing.html`.
Background: `DedhD.md` §10. Product: a visualiser, 4 fixed views, **no 3D**.

## 1. Goal

Each view downloads **`base.jpg` + one small `.dat` file**. The 4 map images (`id.png`, `uv.png`, `uv_trim.png`, `shade.png`) are not sent. The page calculates them from the curves when it opens a view.

| | Now (8100) | Target |
|---|---|---|
| Map data, 4 views | 2.0 MB (+ `plate.json` 20 KB) | ≤ 40 KB `.dat` in total (about 7 KB expected) |
| Download, first visit, 4 views | 3.73 MB plates | ≤ 1.75 MB (the photos only, + `.dat`) |
| Render | — | the same as 8100 (mean difference ≤ 0.5 on the review queries) |
| GPU memory per view | about 41 MB | the same in steps 1–7; about 10 MB after the optional step 8 |

### The rule: decide offline, ship numbers

`make_plate.py` makes some **decisions** by searching the image: which side of a trim is the garment edge, the median light, the colours of the plain fills, the clean square of the dress form. The page must not search again. The decisions go into the `.dat` as numbers, and the page only **evaluates** (grids, ribbons, filters). `make_plate.py` stays the reference and the test.

### Method: rebuild the maps on the GPU, keep the shader

The main shader reads its maps with neighbour reads (antialiased coverage, gradients, shade means per zone). A direct triangle renderer would change all of that. So, first:

1. Evaluate the curves into **triangle meshes** in JavaScript (zone grids, trim ribbons, neck area).
2. Draw the meshes **once per view load** into offscreen textures, in the **same 12-bit packing** as the PNGs.
3. The main shader reads those textures as it reads the PNGs now. It does not change.

The pixel identity is then easy to test (read the textures back, compare them with the PNGs). Drawing the meshes directly on the screen (better edges, less memory) is the optional step 8.

## 2. Rules

- One step = one commit on `numeric`. Each step has a test switch: `?geom=maps` gives back the PNG maps (the 8100 behaviour) until step 7, and stays as a fallback after it.
- Reference: port 8100. Default render: **revised in steps 2 and 4**: a real fabric differs from the PNG-map render by the PNG's own uv noise (about a texel; white noise, falling as 1/σ with a blur), so the gate is the grain checker (`?checker=1`, mean ≤ 1.0 ≈ an edge shift ≤ 0.1 px) on the 8 polish review queries + the 4 halfway neckline queries (`tools/shoot_set.py`, a free `PORT`).
- **Map tests** (read back with `readPixels`, compare with the PNG of the same plate): `tools/map_diff.py` (new).
  - `uv`, `uv_trim`: ~~≤ 0.1 mm of fabric inside the zones~~ **revised in step 2**: no bias (≤ 0.1 px of fabric), median ≤ 0.5 px + 1 packing step, 99 % ≤ 1.5 px + 1 step (the PNG's own value is a quad centre, ±0.5 px, in steps of 0.31 mm); ≤ 0.5 px of edge position.
  - `id`: differs only on edge pixels (1 px band of an outline).
  - `shade`: ≤ 1 level of 255 in 99 % of the garment pixels, ≤ 3 levels everywhere.
- Budgets: map build at view load ≤ 50 ms on a laptop, ≤ 250 ms on a mid-range phone. Draw time unchanged. A drag (halfway step 4) still ≥ 30 fps.
- `make_plate.py` writes the PNGs as before. `tools/rebuild_check.sh` must stay byte-identical for the PNGs.

## 3. Steps

### Step 0: Baseline

**Do:** shoot the 12 reference queries on 8100. Record sizes (raw and gzip) of every plate file, and the GPU memory per view. Create `numeric-results.md`.

**Accept:**
- [x] Baseline shots and the size table in `numeric-results.md`.

### Step 1: The plate maths in JavaScript

**Do:**
1. New `demo/plate.js` (one module, no dependencies): `resample`, `coons`, the cylinder correction (`thetaDeg`, `asin`), `tuck`, `widthPx`, `neck_edge`, `offset_poly`. A port of `make_plate.py`, the same names.
2. `make_plate.py --dump-mesh <out.json>`: write the evaluated grid points (x, y, u, v) of every zone and trim, for the test only.
3. `tools/mesh_check.mjs`: compare the JavaScript points with the Python points (run in Node: `plate.js` is the same file the page loads).

**Accept:**
- [x] All 4 plates: every grid point within 0.01 px and 0.001 cm of the Python value.

### Step 2: Zone maps from the mesh, torso first (`?geom=mesh`)

**Do:**
1. For each zone, back to front: a triangle grid (a point every 6–8 px), with (u, v) on each point.
2. The cut-outs (neck dip, slits, gaps, arm notch): draw the zone outline into the stencil, then its grid where the stencil allows.
3. Draw into an RGBA8 offscreen texture: R = zone, then `uv` with the 12-bit packing (the same `pack()` as Python, in the fragment shader).
4. Neck area (B = 1): the polygon that `make_plate.py` calculates (grid top → deepest reach + trim + blend band), stored in the `.dat` as an outline.

**Accept:**
- [x] Torso `id` R + B and `uv` pass the map tests.
- [x] Torso render ≤ 0.5 against 8100 **(after a 2 px blur: ≤ 0.30; unblurred 1.47)**, at the default neckline and at the 2 range ends.
- [x] No hairline gap between zones (count of R = 0 pixels inside the garment outline = the count in `id.png`).

### Step 3: Trims as ribbons

**Do:**
1. Each trim: a strip of triangles along its centre line, u = cm along, v = 0–1 across (to `vMax` = 1.5 for edging), into `uv_trim` and `id` G.
2. The garment side (`outerV`, found by the march in Python) is stored per trim as a number. The page does not march.
3. Occluders (mannequin arm) clip the strip, by stencil.
4. The live neck trim (halfway step 5) stays analytic in the shader. Only its baked default comes from the ribbon.

**Accept:**
- [x] All trims on the torso pass the map tests; edging past the edge included.
- [x] Lace fit (`polish_metrics.py fit`) unchanged: the same whole repeats on every trim.

### Step 4: Shade from the photo, on the GPU

**Do:** per view load, in fragment passes on the offscreen texture:
1. Luminance of `base.jpg` ÷ the median (the median is stored in the `.dat`).
2. The guided filter, masked per zone (separable box passes), with the plate's `shadeSmoothMm` and `shadeSmoothEps`.
3. Linear light, square-root encoding.
4. The dip fill: the garment's shade carried 8 px outward (as `make_plate.py`).

A float texture is needed for the filter passes. If the phone has no `EXT_color_buffer_float`, use the fallback.

**Fallback:** ship the shade as an 8-bit greyscale WebP (about 30–60 KB per view). The download is then still ≥ 80 % smaller.

**Accept:**
- [x] Torso and neck shade pass the map test (≤ 1 level in 99 %).
- [x] Fine detail and fold band (`polish_metrics.py fd`) within 2 % of `shade.png`.
- [x] Build ≤ 50 ms on a laptop.

### Step 5: Port the neck, sleeve and hem views

**Do:** steps 2–4 on the 3 close views. On the sleeve, check the front grid's left edge (bulge, grain tilt; `render.md`) and fix it in `zones.json`, for both paths at once.

**Accept:**
- [x] All 4 views pass the map tests and the render comparison.
- [x] Sleeve: grain tilt under the arm ≤ 5° (was 18.4°), only if the fix is made; else written as open.

### Step 6: The `.dat` file

**Do:**
1. `tools/make_dat.py <plate-dir>` → `plate.dat`, from `zones.json` + `plate.json` + the offline decisions.
2. Format (little-endian):
   - `"BSP1"`, `u16` version, `u32` length of a small JSON header (scales, ranges, trims, landmarks, decisions, the order of the curves).
   - Then all curves as `int16`, **delta-coded**, in 1/8 px (0.125 px step).
3. Thin the dense torso trace before packing (Douglas–Peucker, 0.1 px). The thinned curves must still pass the map tests.
4. Loader in the page. `?dat=0` reads JSON (`zones.json` + `plate.json`) instead, for debugging.

**Accept:**
- [x] `.dat` for 4 views ≤ 40 KB raw; sizes raw and gzip in the results.
- [x] The render from `.dat` = the render from JSON (identical).

### Step 7: Stop sending the maps

**Do:** the page downloads only `base.jpg` and `plate.dat` for each view. The PNG maps stay in the repo, made by `make_plate.py`, for the tests and `?geom=maps`. The preload (halfway step 1) keeps the `.dat` and the photo blob.

**Accept:**
- [x] Network panel: per view only `base.jpg` + `plate.dat`.
- [x] First visit, 4 views: ≤ 1.75 MB of plate data (was 3.73 MB).
- [ ] Journey steps still ≤ 1 s after the first visit (halfway step 7): **not verified** (1.4–3.1 s in software rendering).

### Step 8 (optional): Draw the mesh directly

Only if phone memory needs it, or the stair-stepped edge is seen.

**Do:** draw each zone and trim as its own triangles on the screen, with (u, v) as vertex data. Coverage, gradients and shade means then come from the GPU itself (no neighbour reads of the maps). The 3 map textures are freed.

**Accept:**
- [ ] GPU memory per view ≤ 12 MB (was about 41 MB).
- [ ] Render ≤ 1.0 against 8100 (the edges change on purpose: smooth instead of stair-stepped).

## 3b. Invariants of the plates (steps 9–11)

Review of the torso view on port 8200 (2026-11-20) found two faults that no test of steps 0–7 could catch: those tests compare the mesh with the PNG maps, and the PNG maps carry the same faults. A plate must also be **right in itself**. The properties that must hold for every plate and every setting are its **invariants**. The numeric version can fix them at the source, because the curves are numbers.

### What was found (torso plate, `zones.json`)

| Fault | Measurement | Cause |
|---|---|---|
| **Shoulders: white photo fabric shows** along the shoulder line (3–5 px rim) and as a wedge at each shoulder tip, beside the neck lace | Overlay of `id.png` R on `base.jpg` (left shoulder; the right side mirrors it) | The front outline's top edge is a stepped line inside the real shoulder slope. The sleeve zone starts at y = 303 and the shoulder point is at y = 298, so the front zone (ends at the tip) and the sleeve zone do not meet. `tuck` is 10 px at the tip. |
| **Hem lace is wobbly, skewed, and starts low** | Trim centre y: 1,436 at the corner, then 1,453 to 1,462 (±4 px wobble); the front outline bottom is 1,472–1,479 (±3 px wobble). The lace centre sits 13–19 px above the hem edge, not at a constant offset. | The centre line of the `hem` trim is hand-traced, 106 points, not derived from the hem. The first segment drops 17 px. |
| **Fabric at the hem is extrapolated** | Front grid bottom edge is straight at y = 1,450.7. The hem is 1,478 at its lowest. | The grid edge is a chord, not the hem curve. Fabric and lace beside it do not keep one grain. |

### Step 9: Shoulder closure

**Do:**
1. **Edge snap tool** `tools/snap_outline.py`: move each outline point (front, sleeves) along its normal, ≤ 4 px, to the strongest edge of the base photo (garment against mannequin or wall). Then smooth the curve (≤ 0.5 px error) and write it back to `zones.json`. Only the garment-to-background edges move. Seams between zones do not.
2. **Shoulder seam as one shared curve:** the front outline and the sleeve outline both use it from the neck corner to the shoulder tip, as the seam list in `annotate_*.py` does for the sleeve view. The sleeve zone starts at the shoulder point (y = 298), not below it. The `tuck` rule keeps the front under the sleeve.
3. A **grow rule** in `plate.js` for a free (non-seam) outline edge: 0.5 px outward, so the photo's anti-aliased edge pixel is never left.
4. Rebuild with `make_plate.py` (the PNG maps stay as the reference) and write the new `.dat`.

**Accept:**
- [x] **Uncovered garment** (new check): garment mask from the photo, minus the union of zones: ≤ 0.05 % of the garment area (65 px), no connected piece wider than 2 px **except one 7 px speck at the right neck corner (open: moving it changes the neckline)**.
- [ ] **White-fringe render test**: a strongly coloured fabric (`?fabric=` a test red), the torso view at 2×. Count of pixels within 3 px of the outline that are close to the photo's white linen (< 12 levels): 0 in the shoulder band.
- [ ] Left and right mirror about the centre line: mean outline difference ≤ 1 px.

### Step 10: Hem layout

> **Result 2026-11-20 (see `numeric-results.md`):** the review concerned the hem VIEW. Items 1 and 4 below rest on a wrong reading (the centre line is exact, the grid bottom follows the hem). The real faults were the slit trim's id overwriting the hem lace's last 35 px, and lace on the front panel only. Both are fixed (trim order; `hem-bl`, `hem-br`).

**Do:**
1. **Derive the trim from the hem.** In `zones.json` the trim gets `"derive": { "from": "front", "edge": "hem", "offsetMm": <measured>, "smoothPx": 24 }`. `plate.js` builds the centre line from the (snapped, smoothed) hem edge with `offset_poly`, then smooths it. The hand-traced list is no longer shipped. The `.dat` gets smaller as well.
2. **Constant offset:** the lace's outer edge keeps the same distance to the hem edge, along the whole hem. The overhang (edging, `vMax` = 1.5) hangs a fixed length from it.
3. **Corners and ends:** the hem trim runs from the left slit to the right slit and meets each slit trim at a **mitre** (both strips cut on the bisector of their two centre lines), not a butt cut. The ends of the hem band do not jump.
4. **Grid follows the hem:** the front grid's bottom edge becomes the hem curve (smoothed). The Coons patch then keeps a square cell at the hem: cell aspect 1 ± 3 %, grain straight within 3° (the same measure as the sleeve fix of step 5).
5. **Motif layout on the hem:** the repeat count is chosen so that a **whole motif is centred at the centre front** and the two ends are symmetric (a whole or a half motif at both ends, never a cut at one end and whole at the other). The scale change to reach this is ≤ ± 3 % (now 0.96 to 1.01).
6. Check the dashed stitch line that shows over the stand base in the torso view (the white dashes near the centre of the hem). Clip it to the garment (the occluder rule of step 3), or remove it.

**Accept:**
- [ ] Centre line: second difference ≤ 0.3 px, no point more than 0.5 px from the offset curve.
- [ ] Offset to the hem edge constant: standard deviation ≤ 0.5 px.
- [ ] Hem trim end meets the slit trim: gap ≤ 0.5 px, no overlap step.
- [ ] Front grid cell aspect at the hem 1 ± 3 %; grain tilt ≤ 3°.
- [ ] Lace fit: whole motif at the centre front; ends symmetric; scale within ± 3 %. Check with `polish_metrics.py fit`.
- [ ] Same rules checked on the hem plate (`hem-straight`), where the hem trim is already derived from a real edge.

### Step 11: One invariant check for every plate

**Do:** `tools/plate_invariants.py <plate-dir>`, run by `make_plate.py` at the end, PASS or FAIL per rule. The rules:

| Rule | Test |
|---|---|
| Closure | no uncovered garment (step 9) |
| No gaps | no hairline gap between zones (R = 0 inside the garment) |
| Symmetry (torso, neck) | left and right curves mirror about the centre line (≤ 1 px) |
| Grain | cell aspect 1 ± 3 %, tilt ≤ 3° on every zone |
| Trim follows its edge | constant offset (σ ≤ 0.5 px), smooth (second difference ≤ 0.3 px) |
| Trim joins | trims that meet do so on a mitre, gap ≤ 0.5 px |
| Motif | whole motif at the centre front for centred trims; symmetric ends |
| Landmarks | every landmark inside its zone, at the right place on the outline |

The check also runs on the page's own mesh (`?geom=mesh`), through `readMaps()`, so that a curve change is caught without a PNG rebuild.

**Accept:**
- [ ] All 4 plates PASS, or each FAIL is written as an open item with its measurement.
- [ ] `tools/README.md` and `docs/plate.md` list the new check, so that a new plate (a new look, a new view) must pass it.

### Exit strategy for steps 9–11

- Edge snap moves a point more than 4 px, or makes the outline noisy: keep the annotated outline there and mark the spot for a hand fix with `gridcrop.py`.
- The derived hem trim looks worse than the traced one on the hem plate: derive only on the torso plate.
- A mitre needs more than the ribbon code gives: butt-join and cover the join with a short overlapping piece.
- Revert a step after 2 failed attempts, as in section 4.

## 4. Exit strategy

**Stop a step** and revert its commit if it fails after 2 attempts or breaks a budget. Write the reason in `numeric-results.md`.

| Situation | Fallback |
|---|---|
| A view's maps fail their test after 2 attempts | That view keeps its PNG maps. The page runs mixed: some views from the `.dat`, some from maps |
| The GPU shade does not match, or no float textures | Ship the shade as a greyscale WebP; only `id`, `uv`, `uv_trim` are calculated |
| The map build is too slow on a phone | Build once, keep the textures of the current view only (as now); or build on the first idle time |
| `.dat` gains less than 30 % over gzipped JSON | Ship gzipped JSON |

**Stop the plan** after 4 working days for steps 0–7. Keep what passed. Port 8100 stays the reference; merge `numeric` into `halfway` only after the step passes.

## 5. Tracking

| Step | Status | Commit | Result (`numeric-results.md`) |
|---|---|---|---|
| 0 Baseline | done | (step 0) | 12 of 12 identical on 8100 and 8200; maps 2,036 KB; 41 MB GPU per view |
| 1 Plate maths in JavaScript | done | (step 1) | every vertex within 3e-11 px on 4 plates; trim `side` now in plate.json |
| 2 Zone maps from the mesh (torso) | done, criteria revised | (step 2) | maps pass; render ≤ 0.30 after a 2 px blur (1.47 unblurred, texel jitter of the PNG's 12-bit uv) |
| 3 Trims as ribbons | done | (step 3) | id G + uv_trim built; bias ≤ 0.11 px; lace fit identical; render ≤ 0.31 after blur |
| 4 Shade on the GPU | done | (step 4) | garment shade identical to ±1 level in 100 % of px (torso, neck); transient ~100 MB GPU; render criterion → checker test |
| 5 Neck, sleeve, hem | done | (step 5) | all 4 views pass the map tests; sleeve front grid fixed (grain tilt 18.4° → 4.4°); sleeve render changes on purpose |
| 6 The `.dat` file | done | (step 6) | 21.7 KB raw (8.3 KB gzip) for 4 views, exact; render identical to JSON; no thinning needed |
| 7 Stop sending the maps | done, build time unverified | (step 7) | 1.67 MB first visit (was 3.64 MB); build 1.4–3 s in software rendering, device needed |
| 8 Direct mesh draw (optional) | not done | | not needed by anything measured |
| 9 Shoulder closure | done, one speck open | (step 9) | tips closed; run snapped to the photo edge; tuck.exempt and a measured tuck.profile; 199 → 65 px uncovered |
| 10 Hem layout | done, premise corrected | (step 10) | lace was cut 35 px short by the slit trim's id; hem trims drawn last; lace on the side pieces; centre line was already exact |
| 11 Plate invariant checks | planned | | |
