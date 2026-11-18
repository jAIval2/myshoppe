# Plan: polish of the fabric and lace overlay (steps 1–4)

Status: **planned**, not started.
Scope: `demo/` only: `testing.html`, `tools/make_plate.py`, `tools/prep_lace.py`, the plates in `assets/plates/`, the swatches in `assets/swatches/`.
Background: the review of 2026-11-19 (lace looks like a sticker, mirrored seams, motifs cut at the ends, a second weave in the fabric, shadows too dark on dark fabrics). Earlier quality work: `upscale.md`.

## 1. Problem and scope

| # | Defect | Cause | Step |
|---|---|---|---|
| D1 | Lace looks flat, like a sticker | No shadow from the lace on the fabric under it | 1 |
| D2 | Shadows too dark; dark fabrics (mocha) lose their folds | Light maths in sRGB, not in linear light | 2 |
| D3 | A faint second weave in every new fabric | `shade.png` keeps the weave of the white cotton of the base photo | 3 |
| D4 | Symmetric seams along the lace; motifs cut at the ends and at centre front | `MIRRORED_REPEAT`; lace length not matched to the trim length; no start point | 4 |

**Not in this plan:** edging lace that hangs past the garment edge, lace relief, metal and pearl masks, fabric displacement in folds, directional sheen, anti-tiling, new photography. They are steps 5–8 of the review and need their own plan.

## 2. Rules for all steps

- **One step at a time.** Each step is its own commit and can be reverted alone.
- **Measure before and after** with the same harness (step 0). A step is not accepted on visual judgement alone.
- **Keep a copy** of every file that a step changes, as `<name>@<step>`, until step 6. Delete the copies at the end.
- **Plates:** if a step changes `make_plate.py`, run `tools/rebuild_check.sh`. Only the files that the step is meant to change may differ. Step 2 and step 3 change `shade.png`, and nothing else.
- **Test switch for each step**, so that before and after can be compared in the same page: `?shadow=0`, `?linear=0`, `?lacefit=0`. The old behaviour stays available until step 6.
- **Budgets:**

| Budget | Limit |
|---|---|
| Plate data for each view | ≤ 1.0 MB |
| Each lace asset (`.webp` + `.json`) | ≤ 600 KB |
| Draw time for one frame, desktop GPU | ≤ 5 ms (measure in a normal browser; headless Chrome reports virtual time) |
| Shader texture units | ≤ 8 (now 8 are in use: do not add a texture unit without removing one) |

## 3. Steps

### Step 0: Baseline

**Do:**
1. Fixed review set: 8 queries, with the same order every time.

   | # | Query | Looks at |
   |---|---|---|
   | 1 | `view=torso&fabric=sage&lace=pearl` | whole garment |
   | 2 | `view=torso&fabric=mocha&lace=geometric` | dark fabric, hem lace |
   | 3 | `view=neck&fabric=mustard&lace=leaf` | neckline curve, tulle |
   | 4 | `view=neck&fabric=mocha&lace=fine` | dark fabric, zari |
   | 5 | `view=sleeve&fabric=sage&lace=geometric` | cuff |
   | 6 | `view=hem&fabric=mocha&lace=geometric` | hem, slit |
   | 7 | `view=hem&fabric=mustard&lace=pearl` | hem, light fabric |
   | 8 | `view=neck&fabric=off` | photo only: control |

2. Run `tools/shoot_views.sh baseline-polish <the 8 queries>`.
3. Cut fixed crops with `tools/zoom.py`: the neck lace (3, 4), the cuff lace (5), the hem lace (2, 6, 7), the bodice centre (2, 3).
4. Measure and record in `plan/polish-results.md`:
   - **Fold contrast retention** (FCR), for queries 2, 3, 4 on the bodice crop: `(std/mean of L in the render) ÷ (std/mean of shade in the same crop)`. 1.0 = the folds of the photo are kept exactly.
   - **Fine detail of the shade** (FD), for each plate: the energy of `shade.png` in the band below 1.5 mm (difference of two Gaussian blurs, at radius 0 and 1.5 mm ÷ `mmPerPx`), as a share of the total. Also the fold band 2–30 mm.
   - **Lace seam count:** the number of mirror joins that a person can point to in crops 2, 3, 5 in 10 seconds.

**Acceptance:**
- [ ] Two runs give the same crops (mean pixel difference ≤ 1).
- [ ] All baseline numbers recorded.

### Step 1: Shadow from the lace on the fabric (D1)

**Do:**
1. In the fragment shader, where a trim is on, read the lace alpha a second time **at an offset** in lace texture coordinates. The offset is the shadow direction, down and to the right, away from the key light at the upper left: `uShadowMm` = (0.6, 0.9) mm. Convert it to lace coordinates with the trim width (`uTrimWcm`) and the lace aspect.
2. Read it at a **higher mip level** (+1.5), so the shadow is soft (about 1 mm).
3. Darken the fabric under the lace: `fabric *= 1.0 - uShadowStrength * shadowAlpha * (1.0 - laceAlpha)`. Start with `uShadowStrength` = 0.35. The lace itself is not darkened by its own shadow.
4. This step works **inside the trim strip only** (the holes and the gaps between the motifs). The shadow past the strip edge needs a wider strip, and belongs with "edging lace" (not in this plan).
5. Test switch `?shadow=0`.

**Acceptance:**
- [ ] In crops 2, 3, 5, the fabric shows a soft dark rim on the lower-right side of the motifs and inside the holes.
- [ ] Maximum darkening ≤ 35 %. No darkening where the lace alpha is 0 within 1.5 mm.
- [ ] No change outside the trims: crops of the bodice centre are pixel-identical to step 0.
- [ ] Draw time ≤ 5 ms (normal browser).

### Step 2: Light maths in linear light (D2)

**Do:**
1. **Colour textures in linear light:** upload the photo, the fabric and the lace as `SRGB8_ALPHA8`. The GPU then decodes them to linear values, also for the mipmaps.
2. **Shade in linear light:** in `make_plate.py`, compute the shade from linear luminance: `shade = lin(L) ÷ median(lin(L))`. Write `"shadeSpace": "linear"` in `plate.json`. The shader reads the key, and converts an old sRGB shade if the key is missing.
3. **Precision:** linear values are darker in the 8-bit file. Store `shade` with a square-root curve (`stored = sqrt(shade / 2)`, decoded `shade = 2 · stored²`), and record `"shadeEncoding": "sqrt"`.
4. Do the multiply and the mix in linear light. Encode to sRGB at the end of the shader.
5. Rebuild all plates. `rebuild_check.sh`: only `shade.png` and `plate.json` may differ.
6. Test switch `?linear=0`.

**Acceptance:**
- [ ] FCR for mocha (query 2, 4) **≥ 0.8**, and for sage and mustard ≥ 0.85. Record the before and after values.
- [ ] Mean luminance of the fabric area changes by ≤ 8 % against step 1, for each fabric (the colour of the cloth must not shift).
- [ ] `fabric=off` (query 8) is visually the same as before (the photo is decoded and encoded again: mean pixel difference ≤ 1).
- [ ] No visible banding in the shadows of the dark fabric at 2× zoom.

### Step 3: Remove the cotton weave from the shade (D3)

**Do:**
1. In `make_plate.py`, after the shade is computed and before it is stored, apply an **edge-preserving smoothing**: a guided filter (box blurs only, so Pillow is enough). The guide is the shade itself.
2. **Radius in millimetres**, not pixels: 1.2 mm ÷ `mmPerPx` (torso ≈ 1 px, neck ≈ 4 px, sleeve ≈ 4 px, hem ≈ 5 px). Regularization ε chosen so that fold edges stay: start with ε = 0.002 on the 0–2 shade range, tune on the neck plate.
3. Apply it only inside the garment mask. Do not mix across zone edges or across the gap to the wall.
4. Settings in `zones.json` → `"shadeSmoothMm"` (default 1.2), so a plate can turn it off (0).
5. Rebuild all plates. Only `shade.png` (and `plate.json`) may differ.

**Acceptance:**
- [ ] Fine detail (FD, below 1.5 mm) in `shade.png` reduced by **≥ 70 %**, on every plate.
- [ ] Fold band (2–30 mm) energy kept **≥ 90 %**.
- [ ] Neck view, mustard fabric, 2× crop: no second weave visible (person check against step 2).
- [ ] In the rendered fabric, the seams, the neck top-stitch and the turned cuff edge still show as soft lines. (`fabric=off` shows the photo, which this step does not change.)
- [ ] Plate data ≤ 1.0 MB.

### Step 4: Real lace repeat, whole repeats, defined start (D4)

**Do:**
1. **Find the repeat** in `prep_lace.py`: autocorrelation of the band's alpha along its length. The period is the first strong peak after zero (peak ≥ 0.6 of the zero-lag value). If no peak is found, keep the mirror and record it.
2. **Cut a seamless repeat:** crop a whole number of periods (1–3, enough for ≥ 1024 px), and blend the cut over the last 4 % of the length with the matching part of the next period.
3. **Sidecar** `lace-<name>.json`: `periodPx`, `periodRatio` (period ÷ band height), `edge` ("bottom"), `widthMm` (the real band width; an assumption until measured).
4. **Shader:** `REPEAT` along the lace, in place of `MIRRORED_REPEAT`.
5. **Whole repeats on each trim:** in `testing.html`, for each trim, with `L` = `plate.trims[name].lengthCm` and `r` = the repeat length in cm at the trim width:
   - `n = max(1, round(L / r))`; `fit = L / (n · r)`.
   - If `0.95 ≤ fit ≤ 1.05`, scale the lace along the trim by `fit`. Otherwise, keep the scale and record the trim.
6. **Start point:**
   - `neck`, `hem`: a motif **centred at the middle of the trim** (centre front for the neck; the middle of the visible hem).
   - `cuff-*`, `slit-*`: a whole motif **at the visible end** (the cuff corner, the hem end of the slit).
   - Send the offset to the shader as a uniform for each trim (`uTrimU0[7]`).
7. Rebuild the four laces. Test switch `?lacefit=0` (old mirror, no fit).

**Acceptance:**
- [ ] Each of the four laces has a measured period (or a recorded reason why not).
- [ ] Lace seam count in crops 2, 3, 5: **0** (against the step 0 count).
- [ ] On every trim with a fit inside 0.95–1.05: a whole motif at both ends (torso neck and hem), and a motif centred at the centre front within ±5 % of one repeat.
- [ ] Scale change on each trim ≤ 5 %. Trims outside that range are listed in the results.
- [ ] Each lace asset ≤ 600 KB.

### Step 5: Close and record

**Do:**
1. Run the step 0 harness again. Record all numbers in `plan/polish-results.md`, with before and after crops.
2. Remove the test switches that are no longer needed, or keep them and document them in `tools/README.md`.
3. Delete the `@<step>` copies.
4. Add an entry to `render.md` §11.

**Acceptance:**
- [ ] Each accepted step is committed with its numbers.
- [ ] `render.md` and `tools/README.md` agree with the code.

## 4. Exit strategy

### Stop a step

Revert the step (restore its `@<step>` copies, revert its commit) if **one** of these is true:

- It fails its acceptance criteria after **2 attempts**.
- It breaks a budget in §2, and no simple change fixes it.
- It changes a file that it must not change (`rebuild_check.sh`), or it changes `fabric=off`.

Write the reason in `polish-results.md`, then continue. The steps do not depend on each other, with one exception: if step 2 is reverted, run step 3 with the sRGB shade.

### Fallbacks

| Situation | Fallback |
|---|---|
| Step 1: the shadow looks dirty on light laces over dark fabric | Tint the shadow with the fabric colour (darker fabric, not grey), or lower the strength for each lace in its sidecar |
| Step 2: banding in dark shadows | 16-bit shade in two channels (high and low byte), like the UV packing |
| Step 2: `SRGB8_ALPHA8` mipmaps fail on a browser | Decode with `pow(c, 2.2)` in the shader, and accept slightly wrong mip averages |
| Step 3: folds become soft before the weave is gone | Smaller radius, or keep the weave on the torso plate (1 px radius) and smooth only the close views |
| Step 4: a lace has no clear period (hand-made, irregular) | Keep the mirror for that lace, and hide the joins at the trim ends: start the mirror at the centre front |
| Step 4: the fit is outside 0.95–1.05 on short trims (cuffs) | Allow up to ±10 % on trims shorter than 3 repeats |

### Stop the plan

Stop if steps 1–4 take more than **3 working days**, or if steps 1 and 4 both fail. Then the lace needs real photography (review step 8) before more shader work.

### Always safe

Each step has a test switch for the old behaviour, so the demo works after every step.

## 5. Tracking

| Step | Status | Commit | Result (`polish-results.md`) |
|---|---|---|---|
| 0 Baseline | not started | | |
| 1 Lace shadow | not started | | |
| 2 Linear light | not started | | |
| 3 Shade without the weave | not started | | |
| 4 Lace repeat and placement | not started | | |
| 5 Close and record | not started | | |
