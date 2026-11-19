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
