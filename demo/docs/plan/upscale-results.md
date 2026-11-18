# Upscale results

Harness: `tools/shoot.sh <dir>` → `tools/crops.py <dir>/shot-2x.png <dir>/crops` → `tools/metrics.py <dir>`.
Baseline crops: `baseline/` (neckline, cuff-left, bodice-centre, hem, full 2× shot).

## Step 0: baseline (2026-11-18)

| Metric | Value |
|---|---|
| Harness repeatability (mean pixel difference, 2 runs, 4 crops) | 0.0 |
| Block ratio (fabric UV equal to right neighbour) | 0.431 |
| Sharpness, bodice crop (variance of FIND_EDGES) | 855.6 |
| Plate data (id, uv, uv_trim, shade) | 362 KB |
| Swatches | fabric 405 KB, lace 713 KB |
| Canvas at 2× | 860 × 1147 |

Notes:
- **Draw time is not measurable in this harness.** `--virtual-time-budget` makes `performance.now()` virtual, so the page reports 0.0 ms (and a Load time of about 15000 ms). Draw-time criteria (≤ 5 ms) need a real GPU in a normal browser; check them by hand.
- The lace swatch (713 KB) is already over the 600 KB budget in section 2. Not caused by this plan. Step 5 must not grow it, and it needs a decision.
- No NumPy installed (Pillow 12.3 only), so step 1 should stay in Pillow.

(The hem crop centre moved from y=1455 to y=1375, because the caption pill covered it. Baseline hem crop was re-cut from the saved baseline shot.)

## Step 1: one UV per pixel (accepted)

`STEP = 1`; trims: one step per px along, `across = max(8, ceil(width_px))`. Crops: `after-step1/`.

| Metric | Baseline | Step 1 |
|---|---|---|
| Block ratio | 0.431 | **0.027** (≤ 0.05 ✔) |
| Sharpness, bodice | 855.6 | 787.8 (the old value was inflated by block-edge aliasing) |
| Plate data | 362 KB | 396 KB (≤ 1.0 MB ✔) |
| `make_plate.py` run time | n/a | 6 s (≤ 60 s ✔) |
| Geometry | | 470 of 1.9 M id px differ, all on zone edges; bbox of change is the garment edge. Corner positions are unchanged by construction (same grid, finer quads) ✔ |

Lace and fabric steps are gone in the hem crop. Backup: `assets/plates/torso-straight@1/`.

## Step 2: swatch tiling (accepted, one known blemish)

`prep_swatches.py` now cuts over to the half-offset copy along a minimum-error seam (dynamic programming, Pillow only), inside a band of 8–64 px from each tile edge, then feathers the cut by a 1.5 px blur. The old blend crossfaded about 233 px at each edge (about 70 % of the tile). Run `prep_swatches.py <src> <out> <dbg> fabric` to rebuild only the fabric.

| Check | Result |
|---|---|
| Doubled motifs | Only inside the 1.5 px feather of the cut (well under 6 %). Area replaced by the shifted copy: 15 % of the tile. |
| Sharpness vs de-lit swatch before blend | 4871 vs 4854 (100 %, ≥ 90 % ✔) |
| Swatch size | fabric ≤ 600 KB ✔ (see below) |
| 3 × 3 preview | `docs/plan/img/fabric-tile3x3.png`: no tile edge stands out. |
| Tile corner, full res | `docs/plan/img/fabric-tile-corner.png`: one petal near the tile corner is slightly clipped where two seams meet. Not visible at garment scale. |

The 10-second reviewer test needs a person; this is my own look, not a sign-off. Backup: `assets/swatches/fabric-sage-1024@2.jpg`.

## Step 3: mip bias and filtering (accepted; draw time unverified)

`testing.html`: `textureLod` → `textureGrad`. Gradients come from the plate itself: central difference of the decoded UV over ±4 plate px (±1 px is too noisy with 12-bit UV). They are used only if all four neighbours are in the same zone (fabric) or the same trim (lace); otherwise the round footprint from the known scale is used, so no derivative crosses a zone edge. Uniform `uMipBias` = −0.5 (footprint × 2^−0.5). `EXT_texture_filter_anisotropic` is enabled on the swatches (max 8) when present. Test switches: `?bias=<n>`, `?aniso=0`. Backup: `testing@3.html`.

| Metric | Baseline | Step 1 | Step 3 |
|---|---|---|---|
| Sharpness, bodice | 855.6 | 787.8 | **1334.8** (156 % of baseline, ≥ 120 % ✔) |
| Same code with `?bias=0&aniso=0` | | | 939.8 |

- Moiré: screenshots at canvas widths 430, 602, 860 px (`docs/plan/img/step3-widths.png`) show none. This is my own look; a reviewer should confirm.
- Zone edges: no seam lines seen (front/sleeve).
- Draw time ≤ 5 ms: **not measured.** Headless virtual time reports 0.0 ms. Check in a normal browser with the stat line. The shader adds 8 `texelFetch` per fabric px and 8 per lace px, plus the gradient maths.
- Whether headless SwiftShader exposes the anisotropic extension is unknown. The sharpness gain therefore comes from the bias and the plate gradients at least; anisotropic filtering may add more on a real GPU.

## Step 4: canvas to device resolution (accepted; draw time unverified)

`resize()` now allows a canvas up to 2 × the plate (DPR ≤ 2). When the canvas is larger than the plate (`k < 1`), the shader reads the 4 nearest plate texels and interpolates the fabric UV only if all four have the same zone id, and the trim UV only if all four have the same trim id; otherwise it uses the nearest texel. Shade is read from a second, LINEAR copy of `shade.png` (texture unit 7). Edge coverage is the bilinear mix of the binary garment mask (the 3 × 3 box is kept for `k ≥ 1`). Backup: `testing@4.html`.

The demo stage is at most 430 css px wide (860 px at 2×), so the canvas never exceeds the plate there. Test switch: `?stage=<css px>` widens the stage. Run at `?stage=700` with a 2× device scale (canvas 1400 × 1867, k = 0.857): `docs/plan/img/step4-1.17x-detail.png`.

- Fabric and lace have no 2 × 2 steps at 1.17× ✔.
- Zone edges stay sharp: front/sleeve boundary shows no colour mixing ✔ (own look).
- Regression: at the normal 860 px stage the four crops are pixel-identical to step 3 (difference 0.0).
- **Limit:** the garment silhouette still shows stair-steps, because the mask is a 1200 px binary raster; interpolating it gives a 1-plate-px feather, not photo-soft edges. A smoother silhouette needs a soft alpha in the plate (not part of this plan).
- Draw time ≤ 5 ms at the largest canvas: **not measured** (same reason as step 3). At 2400 × 3200 the fragment count is 4× the normal stage; check on real hardware.

## Step 5: larger sources: skipped

The plan says to do this only if steps 1–4 pass and the result is still too soft on large screens. The stage in the demo never exceeds 860 px, so there is no evidence of that. Also the lace swatch is already 713 KB against the 600 KB budget. Not done.

## Step 6: close

Final run (same harness) = the step 4 run: block ratio 0.027, bodice sharpness 1334.8 (baseline 855.6), plate data 396 KB, fabric swatch 427 KB, lace swatch 713 KB. Crops: `baseline/` (before), `after-step1/`, `after-step3/` (= final at the normal stage). The `@<step>` backup copies are deleted. `render.md` section 11 is updated.

**Not verified:** draw time (≤ 5 ms) on a real GPU, and the human review criteria (10-second tile-edge test, moiré check). Open: lace swatch is over the 600 KB budget (713 KB, unchanged by this plan).
