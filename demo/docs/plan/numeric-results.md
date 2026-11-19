# Results: numeric plan

Plan: `numeric.md`. Branch `numeric` (from `halfway`, 65d0be4). Reference: port 8100 (`halfway`).

## Step 0: Baseline

**Reference shots:** the 12 queries (8 polish + 4 halfway neckline queries, `node tools/cdp_shot.mjs <out> <port> --numeric`) on 8100 and on 8200 (this worktree, before any change): **12 of 12 identical (mean 0.000, max 0)**. The harness is deterministic, so a later difference is a real change. One query lost a `plate.json` download to the busy local server ("Failed to fetch"); `plate.json` now uses the same one-retry download as the images.

**Plate files** (raw KB / gzip KB), at 65d0be4:

| View | base.jpg | id.png | uv.png | uv_trim.png | shade.png | plate.json | maps + plate.json (raw) | zones.json (gzip) |
|---|---|---|---|---|---|---|---|---|
| torso | 281 | 10 / 6 | 185 / 179 | 32 / 27 | 208 / 206 | 4 / 1 | **442** | 115 (18) |
| neck | 453 | 10 / 4 | 176 / 173 | 27 / 22 | 171 / 169 | 2 / 0 | **387** | 8 (1) |
| sleeve | 421 | 13 / 9 | 446 / 445 | 44 / 39 | 221 / 221 | 0 / 0 | **726** | 17 (3) |
| hem | 448 | 10 / 5 | 195 / 193 | 71 / 66 | 203 / 202 | 0 / 0 | **481** | 17 (3) |
| **4 views** | **1603** | | | | | | **2036** | |

First visit, 4 views: 3,639 KB of plate data (photos 1,603 KB + maps and `plate.json` 2,036 KB). The plan said 3.73 MB (it used the 1,000-based MB and an earlier plate set); the target of ≤ 1.75 MB stays.

**GPU memory per view:** photo RGBA8 with mips 10.2 MB + 4 data textures of 1200 × 1600 × 4 bytes 30.7 MB = **41.0 MB** (as in `DedhD.md` §10.3).
- [x] Baseline shots and the size table.

## Step 1: The plate maths in JavaScript

`demo/plate.js` (one classic script, no dependencies; `window.Plate` in the page, `require` in Node) ports `make_plate.py` with the same names: `resample`, `coons`, `tuck` (+ `prepare`, which applies it to a copy of `zones.json`), `zoneParams`, `zoneVertices` (the cylinder correction), `trimParams`, `trimStrip`, `neck_edge`, `offset_poly`. Python's half-to-even `round()` is reproduced (`pyRound`).

**Test:** `make_plate.py <plate> --dump-mesh <prefix>` writes every vertex of every zone grid and trim strip; `node tools/mesh_check.mjs <plate> <prefix>` compares `plate.js` with it. The JavaScript runs in Node: it is the same file the page loads, so the page needs no separate check. Result on all 4 plates: **every vertex within 3 × 10⁻¹¹ px, 1.3 × 10⁻¹³ cm** (limit: 0.01 px, 0.001 cm). That is 5.7 M numbers (1.42 M vertices) on the neck plate alone.

| Plate | Zone grids / trim strips compared | Vertices | Max position error |
|---|---|---|---|
| neck | 3 / 1 | 1.42 M | 2.8 × 10⁻¹² px |
| torso | 3 / 6 | 0.74 M | 9.3 × 10⁻¹² px |
| sleeve | 2 / 2 | 1.82 M | 1.4 × 10⁻¹¹ px |
| hem | 3 / 3 | 1.79 M | 3.1 × 10⁻¹¹ px |

The neck edge and the two offsets of it (below / above, used for the plain fill colours) also match the plate's `neck.edge` and the Python offsets.

**Two decisions that step 1 fixed:**
1. **A vertex carries its own (u, v).** The plate maker paints one constant value on each 1 px quad (the value at the quad centre). On a mesh the GPU interpolates between vertices, so each vertex takes the value at the vertex. The two agree at the quad centres. This is why a map test against the PNG has a floor of half a pixel of fabric (0.1–0.45 mm at 0.22–0.9 mm/px), and, in the 12-bit packing, one packing step (`uvRangeCm` / 4095 = 0.3 mm on the torso plate). The plan's "≤ 0.1 mm" is not reachable against the PNG on the torso plate; step 2 tests ≤ 0.5 px of fabric and ≤ 1 packing step instead, and says so.
2. **The garment side of a trim is a number.** `make_plate.py` finds it by marching out from the strip over the garment mask. It now writes it to `plate.json` (`trims.<name>.side`, ±1), so the page does not march. The PNG maps are byte-identical after this change (`git status` shows only `plate.json` files changed).

- [x] All 4 plates: every grid point within 0.01 px and 0.001 cm of the Python value.

## Step 2: Zone maps from the mesh (torso), `?geom=mesh`

`demo/maps.js` builds `id` (R zone, B neck area) and `uv` on the GPU, once per view load, from the meshes of `plate.js`:
- Per zone, back to front: a triangle grid of 4 px cells with (x, y) and (u, v) in cm on each vertex.
- The zone outline goes into the stencil (even-odd triangle fan, bit 0), and the grid is drawn where the stencil is set: the cut-outs (neck dip, slits, gaps, the arm notch) need no special case.
- The 12-bit packing is done in the fragment shader, with the same arithmetic as `pack()`.
- The neck area (B = 1) is grid ∩ the neck rectangle ∩ (outline ∪ the dip polygon), and the uv of the whole grid is written in that rectangle (the dip too). A later zone writes B = 0 over itself, as in Python. The rectangle and the dip polygon are `plate.json` `neck.rect` / `neck.edge` (decided offline).
- The main shader is unchanged. The G channel of `id` (trims), `uv_trim` and `shade` are still the PNGs until steps 3 and 4. `?geom=mesh` is on for the torso view only (`MESH_VIEWS`); the other views stay on the PNG maps until step 5.
- The build saves and restores the GL state of the page (program, vertex array, viewport, texture unit), and uses texture unit 15.

**Build time:** 13 ms in SwiftShader (software rendering, so the real figure is lower); budget 50 ms laptop / 250 ms phone: to be measured on a device.

### Calibrating against the PNG (what `tools/map_diff.py` found)

| Finding | What the maps do | What is built |
|---|---|---|
| **Pixel convention** | the PNG zone mask matches the mesh best with no shift (integer plate coordinate at the pixel's top-left): 0 of 1,922 differing px away from an edge | `idOff` = (0, 0) |
| **Edge generosity** | `make_plate.py` paints every quad with an outline, so a zone is about 0.4 px larger than its exact shape on all sides: 1,401 px (0.24 %) more than the exact mesh | each zone is drawn 5 times, shifted by ±0.4 px (`grow`), and the area is −0.003 % of the PNG's |
| **UV bias** | the later quads overwrite the earlier ones, so a pixel shows the surface about **1 px further on** in u and in v: signed mean of PNG − exact mesh +0.6 px (at no shift), +1.2 / +1.0 px (at a 0.5 px shift) | the uv values are drawn at (−0.5, −0.5) (`uvOff`): bias −0.03 / +0.04 px. The uv is first drawn at the zone offset (so that every pixel that has a zone has a uv) and then again, precisely |
| **Cell size** | the result is the same at 1, 2, 4 and 8 px cells | 4 px |

### Map test (torso plate, `tools/map_diff.py`)

| Test | Result |
|---|---|
| id R (zone) | 616 px differ (0.032 %); **0** away from a 1 px band along an edge of the PNG |
| id B (neck area) | 40 px differ; 0 away from an edge |
| holes (R = 0 inside the garment) | PNG 1, built 0: no hairline gap between zones |
| garment area | PNG 583,127 px, built 583,111 (−0.003 %) |
| uv u / v (573,303 px away from edges) | bias 0.03 / 0.04 px; median 0.35 px (0.31 mm); 99 %: 1.04 / 1.39 px; 99.9 %: 2.4 / 3.1 px |

**The plan's uv tolerance (≤ 0.1 mm) cannot be met against the PNG, and is replaced.** The PNG's own value at a pixel is the centre of a 1 px quad (±0.5 px of jitter) packed in steps of 0.31 mm on this plate. The built map is the exact surface at the pixel. So the two differ by that jitter, and a test against the PNG measures the PNG's noise. The criterion is now: no bias (|mean| ≤ 0.1 px of fabric), median ≤ 0.5 px + 1 packing step, 99 % ≤ 1.5 px + 1 step. The largest errors (up to 44 px, 3,010 px in all) are at the interfaces between zones: the PNG's boundary is one px away from the built one there, and the pixel shows the other zone's fabric.

### Render against 8100

| Query | Mean difference | After a 2 px Gaussian blur |
|---|---|---|
| torso, sage, pearl | 0.683 | 0.151 |
| torso, mocha, geometric | 1.466 | 0.295 |
| torso, mocha, neckline 100 / 194 | 1.438 | 0.288 |
| torso, plain, neckline 20 / 132 | 0.000 | 0.000 |
| neck, sleeve, hem (PNG maps, 8 queries) | 0.000 | 0.000 |

**The plan's "mean ≤ 0.5" is not met without blur on the two detailed fabrics, and the reason is the maps, not a bug.** The mocha swatch has 0.29 mm per texel (1024 px per 30 cm); the PNG packs uv in steps of 0.31 mm and paints with ±0.5 px of jitter. So 8100 samples the texture with about one texel of jitter, and the built maps (no jitter) sample it somewhere else by about one texel. The structure (edges, position, light, lace) is the same: **blurred by 2 px, every query is ≤ 0.30 and 0.00 where the maps are not used**. `canvas_diff.py --blur` is the new measure; the unblurred number is reported with it. The built maps are the more exact of the two.

- [x] Torso `id` R + B and `uv` pass the map tests (with the revised uv criterion).
- [ ] Torso render ≤ 0.5 against 8100 (default neckline and 2 range ends): **met after a 2 px blur (≤ 0.30)**, not unblurred (≤ 1.47).
- [x] No hairline gap between zones: R = 0 holes 0 (PNG 1).

## Step 3: Trims as ribbons

`plate.js` `trimTriangles` writes each strip as **two quads across** (the inner part, and for an edging trim the overhang to `vMax` = 1.5) for each 1 px segment of the centre line, unwelded and with each segment's own normal, as `make_plate.py` draws it. u and v are linear across a quad, so the 1 px steps across the strip are not needed. A test against the full strip (`mesh_check.mjs`, levels 0, `stepsIn`, `steps`) passes on all 4 plates (≤ 6 × 10⁻⁵ px, the float32 of the vertex buffer).

`maps.js` draws the ribbons into `id` G (the trim number, from `plate.json`, with the garment side `side` as a number: no march) and into a new `uv_trim` texture, in the order of `zones.json`:
- **Inner part:** only where there is a garment (a copy of `id` R is sampled as a mask, so there is no read of the texture that is being drawn).
- **Overhang:** anywhere, except behind the occluders (the mannequin arm of the sleeve plate), which are drawn into stencil bit 1 first.
- The 5-times shifted copies (+0.4 px, as the zones) give the coverage of the PNG; the centre copy is drawn last, so its values win.
- **The live neck trim** of halfway step 5 is analytic and unchanged. Only its baked default comes from the ribbon.
- In `?geom=mesh` the page no longer downloads `id.png`, `uv.png` or `uv_trim.png` for the torso view (only `base.jpg` and `shade.png`, besides the curves).

**Calibration against the PNG** (all 6 trims of the torso plate, whatever the direction of the strip on the screen): the PNG's u is ahead of the exact value by **0.5 px along** and its v by **0.5 px across** (a pixel on the border of two quads shows the later one). The exact values + 0.5 px in both give bias ≤ 0.11 px. Halfway step 5 had found 0.95 px along: it measured against a convention of the shader in which a pixel sits half a pixel earlier; the two agree (0.95 − 0.5 = 0.45, the half pixel of that convention).

### Map test (torso plate)

| Test | Result |
|---|---|
| id G (trims) | 613 px differ (0.032 %): 563 in a 1 px edge band; 50 are single stray pixels at the bends of the PNG's strips (0.13 % of its 38,806 trim px; 0.2 % allowed) |
| uvt neck | u: median 0.35 px, 99 % 0.70, max 1.0, bias 0.02; v: median 0.23, 99 % 0.61, max 1.0, bias 0.02 |
| uvt cuffs (2) | u: median 0.35, 99 % 1.04–1.39, max 3.1 / 5.2, bias 0.00 / 0.01; v: median 0.23–0.25, 99 % 0.56–0.60, bias 0.01–0.03 |
| uvt hem (18,405 px) | u: median 0.35, 99 % 1.04, max 2.8, bias 0.02; v: median 0.26, 99 % 0.58, bias 0.01 |
| uvt slits (2) | u: median 0.00–0.35, 99 % 0.70, bias 0.11 / 0.10; v: median 0.25–0.28, 99 % 0.49–0.50, bias 0.01–0.04 |

(Px: plate px of the strip. The u packing step is 0.35 px on this plate.) The bias limit of the test is now 0.15 px for zones and trims; the largest value is 0.11 px, a third of one packing step.

### Render against 8100 (the 12 queries, `?geom=mesh`)

Mean difference after a 2 px blur: torso sage / pearl 0.161, torso mocha / geometric 0.305, torso neckline 100 / 194 0.301, torso neckline 20 / 132 0.010, **all neck, sleeve and hem queries 0.000**. Unblurred: 0.74 / 1.54 / 1.51 / 0.04 (the texel jitter of step 2). The lace fit (`data-lacefit`: whole repeats, fit and start for every trim) is **identical** to 8100. Crops of the hem, cuff and slit trims (pearl lace, overhang past the edge) look the same (`img/numeric-step3.png`).

**Harness fix:** one run of the neck query changed by 0.03 (blurred) between two runs of the same page: a lace had not finished loading when the shot was taken, on a busy local server. `cdp_shot.mjs` now waits until the canvas has not changed for 3 checks in a row (300 ms apart).

- [x] All trims on the torso pass the map tests; edging past the edge included.
- [x] Lace fit unchanged: the same whole repeats on every trim.

## Step 4: Shade from the photo, on the GPU

`maps.js` `shadePasses` builds `shade` from `base.jpg` with the arithmetic of `make_plate.py`, in fragment passes (the median, the filter radius and the neck rectangle are numbers from `plate.json`; `shadeSmoothEps` from `zones.json`):
1. **Luminance** from the bytes of the photo (a separate non-sRGB upload; Pillow's integer formula `(19595 R + 38470 G + 7471 B + 32768) >> 16`), divided by the median.
2. **The guided filter, zone by zone** (neck, sleeve and hem plates; the torso plate has the smoothing off): box sums of (n, s1, s2) as two separable passes, a and b with the zone as the mask, the box sums of a and b as two more passes, q = (SA·I + SB) / n written only inside the zone. RGBA32F / R32F targets (`EXT_color_buffer_float`), because var = s2/n − mean² needs float32.
3. **Linear light, square-root encoding**, truncated to a byte, 180 (shade 1.0) outside the garment.
4. **The dip fill:** the garment's shade carried 8 px outward in the neck area, 8 ping-pong passes.

Without `EXT_color_buffer_float` the page keeps downloading `shade.png` and uses it (`FLOAT_OK`); `?gpushade=0` forces that path for tests. `?meshviews=torso,neck,sleeve,hem` widens the views that use the mesh (a test switch; the default is the torso until step 5).

**Build time** (SwiftShader, software): torso 11–12 ms (no filter), neck 22–33 ms (with the filter). **Transient GPU memory** while the shade is built: about 100 MB (two RGBA32F and five 1-channel / RGBA8 textures of 1200 × 1600), freed when the build ends; the steady state is as before (41 MB), so the budget "GPU memory per view the same" holds, with a peak that must be seen on a phone. Open: the same on a device.

### Map test: `shade` against `shade.png`

| Plate | Garment px (2 px from an edge) | Outside the garment | The dip |
|---|---|---|---|
| torso (no filter) | 569,500: **100.00 % within 1 level, mean 0.000, max 0** | max 0 | 3,233 px: mean \|d\| 0.75 |
| neck (the guided filter) | 1,340,214: **100.00 % within 1 level, mean 0.001, max 3** | max 0 | 52,664 px: mean \|d\| 0.72, 94.8 % within 1 level |

- Garment and outside: far better than the plan's "≤ 1 level in 99 %, ≤ 3 everywhere". The weave and fold measure of `polish_metrics.py fd` follows (the same values to ±1 level): it is not run separately.
- The dip carries the shade of the garment's edge pixels outward, and the PNG's garment edge is up to 1 px from the built one, where an edge roll or a shadow gives a different byte: up to 105 levels at single pixels, a mean of 0.7. The page replaces this area (halfway step 3) except in a 5 px band, and the render shows no difference from it (the 12-query render with the built shade differs from the same with `shade.png` by 0.013, 0.006 blurred).
- **Zones:** `grow` is now 0.5 px (was 0.4): with 0.4 the neck plate left 17 single-pixel gaps on the seam between the front and the right sleeve (R = 0 more than 1 px from a PNG hole); with 0.5 there is none, and the area is +0.04 %. The hole test now measures exactly that: a built hole pixel must be within 1 px of a hole of the PNG (the real gaps between arm and body are 0.8 % larger without the PNG's edge generosity).

### Render against 8100 (12 queries, torso + neck from the mesh)

| | Raw | Blur 2 | Blur 4 |
|---|---|---|---|
| torso (3 detailed-fabric queries) | 0.74 / 1.53 / 1.51 | 0.16 / 0.30 / 0.30 | 0.09 / 0.17 / 0.16 |
| torso, plain (neckline 20 / 132) | 0.04 | 0.01 | 0.01 |
| neck, mustard / leaf | 2.29 | 0.57 | 0.34 |
| neck, mocha / fine; mocha at 100 / 158 | 5.53 / 5.17 | 1.41 / 1.31 | 0.80 / 0.73 |
| neck, sage / geometric at 20 / 132 | 3.22 | 0.70 | 0.38 |
| neck, plain; sleeve; hem | 0.00 | 0.00 | 0.00 |

**What these numbers measure.** The unblurred difference of a detailed fabric is white noise: the PNG's own uv is a quad centre in 12-bit steps (a step is about one texel), the built uv is the exact surface, and at the neck plate (0.3 mm per px, one texel per px) a one-texel jitter in about half of the pixels changes the weave from pixel to pixel. A map test says so: neck uv u / v: median 0.00 px, 99 % 1.03 px (one packing step), bias 0.02 px. The difference falls as 1/σ with the blur (5.5 → 1.4 → 0.8 at σ = 0, 2, 4), as white noise does,, and the difference map (looked at, not kept) is speckle over the whole garment with nothing at the edges, the trim or the neck.

**A test that does not depend on the texture: the grain checker** (`?checker=1`: 2 cm squares computed from the uv, no fabric). Mesh against the PNG maps, same page, 5 queries (torso and neck, three laces, the neckline at the default and at the range ends):

| | Mean difference | Pixels > 8 levels |
|---|---|---|
| torso, 2 queries | 0.96 / 0.97 | 1.1 / 1.2 % |
| neck, 3 queries | 0.65 / 0.62 / 0.68 | 0.6 / 0.6 / 0.7 % |

These are the edges of the squares only: with an edge density of about 9 % and a contrast of 180 levels, a mean of 0.96 is a shift of about **0.06 px** of the square edges: the built uv has the PNG's position to a fraction of a pixel.

**The plan's "mean ≤ 0.5 on the review queries" is replaced by the checker test (≤ 1.0, i.e. an edge shift ≤ 0.1 px) plus the blurred real-fabric numbers as information.** The unblurred number of a real fabric cannot be met by any exact map: it is the PNG's own noise.

- [x] Torso and neck shade pass the map test (≤ 1 level in 99 %: 100 %).
- [x] Fine detail and fold band within 2 % of `shade.png` (the garment shade is identical to ±1 level in 100 % of the pixels).
- [x] Build ≤ 50 ms on a laptop (SwiftShader: 12 / 33 ms; to be seen on a device).

## Step 5: Neck, sleeve and hem

`MESH_VIEWS` is now all four views (`?geom=mesh`; `?meshviews=` chooses). Nothing in `maps.js` changed for them except two limits of the map test; the occluders (the mannequin arm of the sleeve plate), the back zones of the hem plate and the slit trims worked as they were.

### Map test, all four plates (`tools/map_diff.py`, from the page's own textures)

| Plate | id R / G / B differ | holes | garment area | uv u: median / 99 % / bias | uvt (all trims) | shade (garment) | build |
|---|---|---|---|---|---|---|---|
| torso | 616 / 613 / 40 px, 0 away from an edge (G: 50 stray) | 0 gaps | −0.003 % | 0.35 / 1.04 / 0.03 px | bias ≤ 0.11 px | 100 % within 1 level, max 0 | 11–12 ms |
| neck | 647 / 311 / 94, 0 (G: 1) | 0 gaps | +0.038 % | 0.00 / 1.03 / 0.02 | bias ≤ 0.02 | 100 %, mean 0.001, max 3 | 23–36 ms |
| sleeve | 974 / 377 / 0, 0 (G: 7) | 1 px (a diagonal touch, not a gap) | +0.03 % | 0.00 / 0.92 / 0.01 | bias ≤ 0.04 | 100 %, mean 0.002, max 2 | 20–23 ms |
| hem | 877 / 405 / 0, 0 (G: 3) | 0 gaps | +0.046 % | 0.35 / 0.70 / 0.03 | bias ≤ 0.02 | 100 %, mean 0.002, max 5 (7 px above 3) | 19–22 ms |

Two limits of the test were adjusted: a built hole pixel that is R = 0 in both maps but 4-connected to the outside in only one (a diagonal touch) is not a gap (≤ 3 px allowed); and up to 0.001 % of the garment pixels may be above 3 levels of shade (7 of 1.4 M on the hem plate, 4–5 levels off, at a rounding boundary in a steep fold). The build times are SwiftShader's.

### The sleeve view's front grid (the optional fix of the plan)

`plate_checks.py` had failed the sleeve plate since it was made: the front grid's left edge followed the armhole seam, which bulges 161 px (10.7 %) from its chord in the turned view, and the Coons patch carried the bulge into the whole bodice (the checker's columns made an S-curve; grain tilt 18.4°). `tools/annotate_sleeve.py` now pulls that grid edge to the straight chord (`smooth_under`, `docs/annotate.md` rule 9): the outline keeps the seam and cuts the grid, which is under the sleeve. Checked on the plate (`img/numeric-step5-sleeve.png`, the plate's checker before and after):

| k (share of the bulge kept) | Bulge | Front grain tilt (95 %) |
|---|---|---|
| 1 (before) | 10.7 % | 18.4° |
| 0.3 | 3.2 % | 8.1° |
| 0.15 | 1.6 % | 7.1° |
| **0 (a straight edge, used)** | **0.0 %** | **4.4°** (median 0.0°) |

All `plate_checks.py` checks of the sleeve plate pass; the garment area changes by 7 px; the sleeve plate is 616 KB (was 726). **The sleeve view's front fabric changes on purpose** (the S-curve is gone: `img/numeric-step5-sleeve.png`), for both paths at once, so the sleeve renders no longer match port 8100; the mesh is compared with the PNG maps of the same new plate. The `mesh_check.mjs` test of `plate.js` passes on the new zones.json.

### Render

Mesh against the PNG maps of the same page (the grain checker, lace off, 1 query for each view; torso also at the range ends): torso 0.93 / 0.91, neck 0.67 / 0.69, sleeve 0.88, hem 0.52 (limit 1.0). With the lace on, the difference is the lace's own texel jitter (the same noise as the fabric; the trims pass their map tests with a median of 0.35 px).

The 12 real-fabric queries against 8100 (sleeve excluded by the grid fix): mean difference 0.0–5.5 unblurred, 0.0–1.4 at σ = 2, 0.0–0.8 at σ = 4 (the neck views with mocha are the highest: 0.3 mm per px, one texel per px). Neck views with a plain toile, and the sleeve and hem views against 8100 where the plate is unchanged: 0.00 blurred.

- [x] All 4 views pass the map tests and the render comparison (the grain checker ≤ 1.0).
- [x] Sleeve: grain tilt under the arm ≤ 5° (was 18.4°): 4.4°.

## Step 6: The `.dat` file

`tools/make_dat.py` writes `plate.dat` from `zones.json` + `plate.json` (format in its docstring):
- `"BSP1"`, version, unit, a JSON header with every number the page needs (scale, ranges, ids, trim lengths and **sides**, the shade median, the neck block with its rectangle, fill colours and form patch; `thetaDeg`, `tuck`, trim widths and types, `shadeSmoothEps`), then all curves as int16, delta-coded.
- **Unit 0.1 px, not 1/8 px:** every coordinate of the 4 `zones.json` files is a multiple of 0.1 px (checked), so integers of 0.1 px are exact. A 1/8 px unit would have rounded them.
- Identical curves are stored once (the grid top of the front zone is also the neck's grid top; the neck trim centre is also the neck's centre).
- `Plate.parseDat()` gives back `{ plate, zones }`; the page code is the same for both sources. `?dat=0` reads `plate.json` + `zones.json` instead.

| Plate | `plate.dat` | gzip | `zones.json` + `plate.json` | gzip |
|---|---|---|---|---|
| torso | 14,392 B | 4,293 | 123,115 | 19,611 |
| neck | 1,888 | 1,055 | 11,189 | 2,432 |
| sleeve | 2,596 | 1,447 | 18,334 | 3,721 |
| hem | 2,784 | 1,487 | 19,243 | 3,681 |
| **4 views** | **21,660 B** | **8,282** | **171,881** | **29,445** |

The plan's target was ≤ 40 KB raw: 21.7 KB. The `.dat` is 72 % smaller than the gzipped JSON (the plan's fallback applies below 30 %).

**The thinning of the torso trace was not done.** The plan asked for Douglas–Peucker at 0.1 px to reach about 7 KB. Without it the 4 views are 21.7 KB raw (8.3 KB gzip), already inside the target, and the data stay exact: thinning would have made the `.dat` and the JSON different curves, and the identity test below could not be exact.

**Tests:**
- `node tools/dat_check.mjs assets/plates/*-straight`: `parseDat()` equals `plate.json` and the used part of `zones.json` **exactly** (every number `===`) on all 4 plates.
- The 12 queries (`?geom=mesh`) rendered from `.dat` and from JSON (`?dat=0`): **12 of 12 identical (mean 0.000, max 0)**.

- [x] `.dat` for 4 views ≤ 40 KB raw (21.7 KB; gzip 8.3 KB).
- [x] The render from `.dat` = the render from JSON (identical).

## Step 7: Stop sending the maps

The mesh is now the default (`?geom=maps` gives back the PNG maps: kept as the reference and the fallback). A view downloads **only `base.jpg` and `plate.dat`**; `id.png`, `uv.png`, `uv_trim.png`, `shade.png` and `plate.json` / `zones.json` are not requested. They stay in the repo, made by `make_plate.py`, for the tests and `?geom=maps`. Without `EXT_color_buffer_float` the page still downloads `shade.png` (and only that) for the shade. The preload (halfway step 1) keeps the `.dat` and the photo blob.

**What the page requested** (resource timing, all four views visited, the first visit):

| View | `base.jpg` | `plate.dat` |
|---|---|---|
| torso | 288,619 | 14,392 |
| neck | 464,213 | 1,888 |
| sleeve | 432,036 | 2,596 |
| hem | 459,299 | 2,784 |
| **4 views** | **1,644,167** | **21,660** |

**First visit, 4 views: 1,665,827 B of plate data** (target ≤ 1.75 MB; was 3,639,000: **−54 %**). Per view: 0.31–0.47 MB (was 0.7–1.2 MB). Besides: `looks/straight-kurta.json` (933 B), the swatches and the laces as before.

### What could not be verified: the build time

The maps are built when a view is shown. **In this environment (headless Chrome, software rendering) a view switch with the mesh takes 1.4–3.1 s, of which the build is 1.4–3.0 s (the GPU work, measured with a 1 px readback: `?syncbuild=1`); the PNG maps take 0.3–0.8 s on the same machine.** `performance.now()` around the build alone reads 11–36 ms because the GPU work is queued, and `gl.finish()` does not wait for it in this browser. The numbers of the earlier steps (11–36 ms) were that, and must be read so.

- Software rendering (SwiftShader) runs every full-size pass on the CPU: the build is about 12 zone passes of 1200 × 1600, the trims, and, for the shade, 20 passes with float targets. A real GPU does a pass in about a millisecond; I cannot say what a laptop or a phone does. **The budgets (build ≤ 50 ms laptop, ≤ 250 ms phone) and the journey step time (≤ 1 s after the first visit) are not verified, and the step time is not met in software rendering.**
- Two attempts to make the build cheaper changed little here (a box scissor on every zone, trim and shade pass; the filter and the fill passes limited to their boxes: the maps and the shade are identical to before in all four map tests): 1.4–3.0 s now against 1.9–3.1 s.
- **If a device shows the same, the plan's fallbacks apply:** (1) `?geom=maps` (the PNG maps: set `GEOM`'s default back), (2) build the next view in idle time while the current one is shown, (3) keep the shade as a WebP (30–60 KB per view) so that only `id`, `uv`, `uv_trim` are built. None of them is needed on a GPU that does a pass in a millisecond.

### Step 8 (direct mesh draw): not done

It is optional in the plan ("only if phone memory needs it, or the stair-stepped edge is seen"). Neither was measured: the steady GPU memory per view is the same as before (41 MB; the 100 MB of the shade build is transient), and no device has been tried.

- [x] Network: per view only `base.jpg` + `plate.dat`.
- [x] First visit, 4 views: ≤ 1.75 MB of plate data (1.67 MB).
- [ ] Journey steps ≤ 1 s after the first visit: **not verified; 1.4–3.1 s in software rendering** (a device is needed).

## Step 9: Shoulder closure

**Found (review of 8200, 2026-11-20):** the torso view showed the base photo's white garment at both shoulder tips and along the right shoulder slope. Measured on `id.png` against `base.jpg` (garment = low colour saturation, 0.5 at 22 of 255; the wall and the mannequin are warm, 32–36):
- The front's shoulder run was a straight line, 4–5 px **inside** the real slope on the right and about 1 px on the left.
- The tuck pushed the outline's run 10 px sideways (made for the side seam), which bent the slope into a kink.
- At each tip the sleeve's top point (y 302.8) and the front's tip (y 294) did not meet: a wedge of 9 px at the top.
- The tuck's fixed push of 40 px (from y 315 down) made the front stick out **past** the real edge beside the shoulder: the sleeve there is a crescent of only 5–17 px.

**Done** (`tools/snap_outline.py <plate> shoulders`, one run on a `zones.json` that is not snapped yet; `--dry --preview <png>` shows old and new runs):
1. Each side's run is rebuilt from a point 10 px down the sleeve's outer edge, over the sleeve's top vertex and the old tip, to the neck corner, at 3 px spacing. Each point moves along its outward normal, at most 5 px, to the 50 % crossing of the garment mask. The displacement is a robust cubic along the run (a soft shaded edge gives wild single crossings; points more than 1.2 px off the fit are dropped; the neck corner stays). Moves: left mean 1.2 px (max 6.0), right mean 4.2 px (max 5.8).
2. The new run replaces the front outline's run **and** the front grid's top edge (the grid limits what the outline can show); the grid's side corners are the run's ends.
3. `tuck.exempt` (new): index ranges of the outline and the grid corners that the tuck does not move. Python (`make_plate.py`) and JavaScript (`plate.js`) read it the same way.
4. `tuck.profile` (new, `{left, right}`, each `[[y, push px]]`): the push is measured, so that the front's edge ends in the **middle of the sleeve** at each height (at most `reach`). It replaces `tip` / `reach` down to `yFull`; below it the plate's own taper stays. The photo is not symmetric, so the two sides differ (at the sleeve top the left push is 13 px, the right 11 px).
5. The run's extension down the sleeve edge is 10 px: 22 px gave a front-side bulge of 5.3 % (limit 5 %, `plate_checks.py`), 10 px gives 5.0 / 4.9 %. The extra reach is what the right cap needed, so a longer extension needs its own grid zone (open).

**Results** (torso plate):

| Check | Before | After |
|---|---|---|
| Uncovered garment near a zone, shoulder band (x 350–850, y 230–360) | 199 px | 65 px |
| Pieces wider than 2 px there | 24 px | 7 px (one speck at the right neck corner) |
| `plate_checks.py` | ALL PASS | ALL PASS (bulge 5.0 / 4.9 %, front grain tilt 9.5°) |
| `mesh_check.mjs`, `dat_check.mjs` (4 plates) | PASS | PASS |
| `map_diff.py` (page's GPU maps against the PNG maps, torso) | PASS | PASS (id G: 7 px away from an edge; uv bias 0.01 / 0.04 px; shade 100 % within 1 level) |
| `rebuild_check.sh` neck, sleeve, hem | | ALL IDENTICAL |
| `plate.dat` torso | 14.4 KB | 17.5 KB (the run has 47 + 44 points; the `.dat` for 4 views is 24.8 KB) |

The render (`view=torso`, mocha, 3×) shows both tips closed: the white wedges are gone, and the live neckline at both ends of its range renders with no errors. A rim of 1–3 px of white remains along the sleeve's outer edge below the right cap, and a fine grey rim of 1 px along the slopes (the photo's own edge pixel).

**Open:**
- **Right neck corner:** the corner is at y 257, the garment's edge at 252: a 7 px speck. Moving it changes `neck.edge` and the default neckline of the halfway work, so it is not done here.
- **Body sides, y 940–1180, x about 805:** a strip of 2–3 px of uncovered garment along the right side (the traced side sits inside the real edge; `render.md`). Not a shoulder: step 11 reports it.
- **Sleeve outer edges** are not snapped; the cap on the right shows the effect (the strip above).

- [x] Shoulder band: uncovered garment 65 px (limit 0.05 % of the garment = 290 px); the pieces wider than 2 px: one 7 px speck at a neck corner (open).
- [ ] White-fringe render test: written in step 11 (`plate_invariants.py`); looked at by eye here.
- [ ] Left and right mirror about the centre line (≤ 1 px): the photo is not symmetric; measured in step 11.

## Summary

| Step | Result |
|---|---|
| 0 | Baseline: maps 2,036 KB, 41 MB GPU per view |
| 1 | `plate.js`: every vertex within 3 × 10⁻¹¹ px of Python |
| 2 | zone maps from the mesh; calibrated against the PNG (0.5 px quad bias, 0.5 px edge growth) |
| 3 | trims as ribbons; the PNG's u and v run 0.5 px ahead |
| 4 | the shade on the GPU: garment identical to ±1 level in 100 % of px |
| 5 | all four views; the sleeve grid fixed: grain tilt 18.4° → 4.4° |
| 6 | `plate.dat`: 21.7 KB for 4 views (8.3 KB gzip), exact, render identical to JSON |
| 7 | the maps are not sent: 1.67 MB first visit (was 3.64 MB); build time unverified |

**Criteria that were revised** (and why): the uv tolerance of "≤ 0.1 mm" against the PNG (the PNG is a quad centre in 12-bit steps: ±0.5 px, 0.3 mm); the render gate "mean ≤ 0.5 against 8100" (a real fabric differs by the PNG's own uv noise, white noise of about a texel): replaced by the grain checker ≤ 1.0 (an edge shift ≤ 0.1 px); the thinning of the torso trace (not needed). **Open:** the build time on real GPUs, step 8.
