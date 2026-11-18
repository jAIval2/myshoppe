# Plan: higher quality for the fabric and lace overlay

Status: **done** (steps 0–4 and 6; step 5 skipped). Results: `upscale-results.md`.
Scope: `demo/` only (the torso plate `assets/plates/torso-straight/`, the swatches, `testing.html`, `tools/`).
Background: `../render.md`, section 11 ("Known problems" and "Next steps").

## 1. Problem

The fabric and the lace on the stage look soft and blocky. These are the causes, in order of effect:

| # | Cause | Where |
|---|---|---|
| C1 | The fabric UV is stored in 2 × 2 px blocks. Four pixels read the same point of the swatch. | `tools/make_plate.py`, `STEP = 2` |
| C2 | Each trim has only 12 steps across its width. Along the trim, it has 2 px steps. | `tools/make_plate.py`, `across = 12` |
| C3 | The seamless blend makes two motifs overlap near the tile edges, so the embroidery looks soft and doubled. | `tools/prep_swatches.py` |
| C4 | The shader always uses a full mip level (no bias, no anisotropic filtering), so the fabric is softer than necessary. On the oblique sides of the body, it becomes very soft. | `testing.html`, fragment shader |
| C5 | The canvas is limited to the plate size (1200 px). On large 2× screens, the browser enlarges the canvas. | `testing.html`, `resize()` |
| C6 | The sources are small: base photo 1200 px wide (from 1792), fabric 1024 px for 30 cm. | `tools/make_base.py`, `tools/prep_swatches.py` |

**One limit is correct and stays:** at real scale, 1 plate px ≈ 0.9 mm. Embroidery stitches smaller than that cannot show in the torso view. The close views (neckline, sleeve, hem) show that detail. This plan does not try to show sub-millimetre detail in the torso view.

## 2. Rules for all steps

- **Do one step at a time.** Each step is its own commit, and each step can be reverted alone.
- **Keep the last good plate.** Before a step changes plate files, copy `assets/plates/torso-straight/` to `assets/plates/torso-straight@<step>/`. Delete the copies only at the end of the plan.
- **Measure before and after**, with the same harness (step 0). Do not accept a step on visual judgement alone.
- **Budgets for the whole view:**

| Budget | Limit |
|---|---|
| Plate data (`id`, `uv`, `uv_trim`, `shade`) | ≤ 1.0 MB in total (now ≈ 370 KB) |
| Swatch files | ≤ 600 KB each |
| Draw time for one frame, desktop GPU | ≤ 5 ms |
| `make_plate.py` run time | ≤ 60 s |

## 3. Steps

### Step 0: Baseline and test harness

**Do:**
1. Add `tools/shoot.sh`. It starts headless Chrome on `http://localhost:<port>/testing.html` and saves screenshots at 1× (900 × 760 window) and 2× (1400 × 1800 window, `--force-device-scale-factor=2`). Use `--use-angle=swiftshader`, `--virtual-time-budget=15000`, and a 100 s time limit.
2. Add `tools/crops.py`. It cuts 4 fixed crops from the 2× screenshot: **neckline, left cuff, bodice centre, hem**. It saves them as `baseline/<name>.png`.
3. Add `tools/metrics.py`. For each crop, it records:
   - **Block ratio:** inside the garment, the share of pixels where the decoded UV is the same as the pixel on the right. Read it from `uv.png`, not from the screenshot.
   - **Sharpness:** the variance of `ImageFilter.FIND_EDGES` on the bodice-centre crop.
   - **Draw time:** from the stat line of the page.
   - **File sizes** of the plate and the swatches.
4. Save the numbers in `docs/plan/upscale-results.md`.

**Acceptance criteria:**
- [ ] Two runs of the harness give the same crops (pixel difference ≤ 1 on average).
- [ ] The baseline numbers are recorded. Expected: block ratio ≈ 0.5 or higher (2 × 2 blocks).

### Step 1: One UV value for each pixel (C1, C2)

**Do:**
1. In `make_plate.py`, set the fabric quads to 1 px (`STEP = 1`).
2. For trims: one step for each px along the trim, and `across = ceil(width_px)` (minimum 8).
3. If the run time is longer than 60 s, change the quads to a per-pixel calculation: for each pixel in the zone bounding box, find (s, t) with a few Newton steps on the Coons patch. Do not add NumPy unless necessary. If NumPy is added, write it in the doc.

**Acceptance criteria:**
- [ ] Block ratio inside the garment ≤ 0.05.
- [ ] Lace crops show no visible steps across the strip at 2×.
- [ ] `check.png` shows the same grid as before. Corners move ≤ 1 px. (The geometry must not change.)
- [ ] Plate data ≤ 1.0 MB, and the run time ≤ 60 s.

### Step 2: Better swatch tiling (C3)

**Do:**
1. In `prep_swatches.py`, change the seamless blend: blend only in a narrow band (≤ 64 px of 1024) at the tile edges, with a soft cut that follows low-contrast areas of the swatch. Do not blend the whole tile.
2. Keep the de-light step as it is.
3. Make a 3 × 3 tiled preview for review.

**Acceptance criteria:**
- [ ] On the 3 × 3 preview, a reviewer cannot point to a tile edge in 10 seconds.
- [ ] Doubled motifs only in the band (≤ 6 % of the tile area).
- [ ] Sharpness of the swatch ≥ 90 % of the de-lit swatch before the blend.

### Step 3: Mip level and filtering (C4)

**Do:**
1. In the shader, add a mip bias of −0.5 to the fabric and lace levels. Make it a uniform, so we can test it.
2. If `EXT_texture_filter_anisotropic` is available, use it on the swatch textures (maximum 8). Change `textureLod` to `textureGrad`, with gradients from the known scale, so that the GPU can use anisotropic filtering on the sides of the body.
3. Keep the rule from `render.md`: no automatic derivatives across zone edges.

**Acceptance criteria:**
- [ ] Sharpness of the bodice crop ≥ 120 % of the baseline.
- [ ] No shimmer: screenshots at 3 canvas widths (430, 600, 860 px) show no moiré in the fabric. A reviewer checks this.
- [ ] No seam lines at zone edges.
- [ ] Draw time ≤ 5 ms.

### Step 4: Canvas to device resolution (C5)

**Do:**
1. Permit a canvas up to 2 × the plate size (DPR ≤ 2).
2. When the canvas is larger than the plate, interpolate the UV in the shader. Decode the 4 neighbouring texels, and interpolate only when all 4 are in the same zone (or the same trim). If not, use the nearest texel.
3. Interpolate the shade the same way (it is smooth data, so normal linear filtering is permitted on a second copy of `shade.png`).

**Acceptance criteria:**
- [ ] On a 2× screen, the garment has no 2 × 2 steps, and the edges are as soft as the photo edges.
- [ ] Zone edges stay sharp: no colour mixing between the front and the sleeves.
- [ ] Draw time ≤ 5 ms at the largest canvas.

### Step 5: Larger sources (C6), optional

Do this step only if steps 1–4 pass and the result is still too soft on large screens.

**Do:**
1. Make the plate at the full source size, 1792 × 2389, from `torso-base.png`. Scale `zones.json` by 1.4933.
2. Make the fabric swatch 2048 px for 30 cm.

**Acceptance criteria:**
- [ ] All budgets in section 2 still pass. If not, keep the 1200 px plate.
- [ ] Sharpness of the bodice crop at 2× ≥ 110 % of the step 4 result.

### Step 6: Close and record

**Do:**
1. Run the harness one more time and update `upscale-results.md` with before/after crops and numbers.
2. Delete the `@<step>` plate copies.
3. Update `render.md` section 11 with the new state and the remaining problems.

**Acceptance criteria:**
- [ ] All the accepted steps are committed, each with its numbers.
- [ ] `render.md` agrees with the code.

## 4. Exit strategy

### Stop a step

Stop a step and **revert it** (restore its `@<step>` copy and revert its commit) if **one** of these is true:

- It fails its acceptance criteria after **2 attempts**.
- It breaks a budget in section 2, and no simple change fixes it.
- It changes the geometry (`check.png` corners move > 1 px).

Write the reason in `upscale-results.md`. Then continue with the next step. The steps do not depend on each other, except that step 4 needs step 1.

### Stop the plan

Stop the whole plan if **one** of these is true:

- **The source is the limit.** Steps 1–3 pass, and the result is as sharp as the swatch photo at that scale. Then more pipeline work cannot help. Detail must come from the close views or better swatch photos.
- **Time box:** steps 0–4 take longer than **3 working days** in total.
- **Steps 1 and 3 both fail.** Then the browser method is not the problem we thought.

### Fallbacks if the plan stops

| Situation | Fallback |
|---|---|
| The browser result is still too soft | Make the image on the server: the same remap in Python (Pillow + NumPy) at full resolution, saved as WebP for each choice and cached. The page shows images and needs no WebGL. |
| The swatch tiling cannot be made seamless | Photograph larger swatches (≥ 60 cm), so that a tile edge is rare on the garment. |
| Draw time or file size is too high on phones | Keep the 1200 px plate and steps 1–2 only. On phones, limit DPR to 1.5. |
| None of the above is sufficient | Move to pre-rendered layers: one finished transparent image for each zone and each material, stacked in the page. The image count is a sum, not a product (for example 11 fabrics + 3 trims × 6 laces = 29 images for each view). |

### Always safe

The last good plate and `testing.html` stay usable after every step. If the plan stops at any point, the demo still works.

## 5. Tracking

| Step | Status | Commit | Result (link to `upscale-results.md`) |
|---|---|---|---|
| 0 Baseline and harness | done | not committed | `upscale-results.md` |
| 1 One UV for each pixel | done | not committed | `upscale-results.md` |
| 2 Swatch tiling | done | not committed | `upscale-results.md` |
| 3 Mip level and filtering | done (draw time unverified) | not committed | `upscale-results.md` |
| 4 Canvas to device resolution | done (draw time unverified) | not committed | `upscale-results.md` |
| 5 Larger sources (optional) | skipped | not committed | `upscale-results.md` |
| 6 Close and record | done | not committed | `upscale-results.md` |
