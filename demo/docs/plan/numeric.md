# Plan: numeric — curves and a `.dat` file in place of the map images

Status: **in progress**. Branch `numeric` (from `halfway`, 65d0be4), worktree `../myshoppe-numeric`.
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
- Reference: port 8100. Default render: mean difference ≤ 0.5 on the 8 polish review queries + the 4 halfway neckline queries (`tools/shoot_set.py`, a free `PORT`).
- **Map tests** (read back with `readPixels`, compare with the PNG of the same plate): `tools/map_diff.py` (new).
  - `uv`, `uv_trim`: ≤ 0.1 mm of fabric inside the zones; ≤ 0.5 px of edge position.
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
- [ ] Torso `id` R + B and `uv` pass the map tests.
- [ ] Torso render ≤ 0.5 against 8100, at the default neckline and at the 2 range ends.
- [ ] No hairline gap between zones (count of R = 0 pixels inside the garment outline = the count in `id.png`).

### Step 3: Trims as ribbons

**Do:**
1. Each trim: a strip of triangles along its centre line, u = cm along, v = 0–1 across (to `vMax` = 1.5 for edging), into `uv_trim` and `id` G.
2. The garment side (`outerV`, found by the march in Python) is stored per trim as a number. The page does not march.
3. Occluders (mannequin arm) clip the strip, by stencil.
4. The live neck trim (halfway step 5) stays analytic in the shader. Only its baked default comes from the ribbon.

**Accept:**
- [ ] All trims on the torso pass the map tests; edging past the edge included.
- [ ] Lace fit (`polish_metrics.py fit`) unchanged: the same whole repeats on every trim.

### Step 4: Shade from the photo, on the GPU

**Do:** per view load, in fragment passes on the offscreen texture:
1. Luminance of `base.jpg` ÷ the median (the median is stored in the `.dat`).
2. The guided filter, masked per zone (separable box passes), with the plate's `shadeSmoothMm` and `shadeSmoothEps`.
3. Linear light, square-root encoding.
4. The dip fill: the garment's shade carried 8 px outward (as `make_plate.py`).

A float texture is needed for the filter passes. If the phone has no `EXT_color_buffer_float`, use the fallback.

**Fallback:** ship the shade as an 8-bit greyscale WebP (about 30–60 KB per view). The download is then still ≥ 80 % smaller.

**Accept:**
- [ ] Torso and neck shade pass the map test (≤ 1 level in 99 %).
- [ ] Fine detail and fold band (`polish_metrics.py fd`) within 2 % of `shade.png`.
- [ ] Build ≤ 50 ms on a laptop.

### Step 5: Port the neck, sleeve and hem views

**Do:** steps 2–4 on the 3 close views. On the sleeve, check the front grid's left edge (bulge, grain tilt; `render.md`) and fix it in `zones.json`, for both paths at once.

**Accept:**
- [ ] All 4 views pass the map tests and the render comparison.
- [ ] Sleeve: grain tilt under the arm ≤ 5° (was 18.4°), only if the fix is made; else written as open.

### Step 6: The `.dat` file

**Do:**
1. `tools/make_dat.py <plate-dir>` → `plate.dat`, from `zones.json` + `plate.json` + the offline decisions.
2. Format (little-endian):
   - `"BSP1"`, `u16` version, `u32` length of a small JSON header (scales, ranges, trims, landmarks, decisions, the order of the curves).
   - Then all curves as `int16`, **delta-coded**, in 1/8 px (0.125 px step).
3. Thin the dense torso trace before packing (Douglas–Peucker, 0.1 px). The thinned curves must still pass the map tests.
4. Loader in the page. `?dat=0` reads JSON (`zones.json` + `plate.json`) instead, for debugging.

**Accept:**
- [ ] `.dat` for 4 views ≤ 40 KB raw; sizes raw and gzip in the results.
- [ ] The render from `.dat` = the render from JSON (identical).

### Step 7: Stop sending the maps

**Do:** the page downloads only `base.jpg` and `plate.dat` for each view. The PNG maps stay in the repo, made by `make_plate.py`, for the tests and `?geom=maps`. The preload (halfway step 1) keeps the `.dat` and the photo blob.

**Accept:**
- [ ] Network panel: per view only `base.jpg` + `plate.dat`.
- [ ] First visit, 4 views: ≤ 1.75 MB of plate data (was 3.73 MB).
- [ ] Journey steps still ≤ 1 s after the first visit (halfway step 7).

### Step 8 (optional): Draw the mesh directly

Only if phone memory needs it, or the stair-stepped edge is seen.

**Do:** draw each zone and trim as its own triangles on the screen, with (u, v) as vertex data. Coverage, gradients and shade means then come from the GPU itself (no neighbour reads of the maps). The 3 map textures are freed.

**Accept:**
- [ ] GPU memory per view ≤ 12 MB (was about 41 MB).
- [ ] Render ≤ 1.0 against 8100 (the edges change on purpose: smooth instead of stair-stepped).

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
| 2 Zone maps from the mesh (torso) | planned | | |
| 3 Trims as ribbons | planned | | |
| 4 Shade on the GPU | planned | | |
| 5 Neck, sleeve, hem | planned | | |
| 6 The `.dat` file | planned | | |
| 7 Stop sending the maps | planned | | |
| 8 Direct mesh draw (optional) | planned | | |
