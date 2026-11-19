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
