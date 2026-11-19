# Plan: polish of the fabric and lace overlay (steps 1–7)

Status: **in progress**: steps 0 and 1 done (see `polish-results.md`); steps 5–7 added on 2026-11-19.
**Numbering note:** the close step was step 5 before 2026-11-19, and is now **step 8**. In `polish-results.md`, "deleted in step 5" means the close step.
Scope: `demo/` only: `testing.html`, `tools/make_plate.py`, `tools/prep_lace.py`, `tools/prep_fabric.py`, the plates in `assets/plates/`, the swatches in `assets/swatches/`.
Background: the review of 2026-11-19 (lace looks like a sticker, mirrored seams, motifs cut at the ends, a second weave in the fabric, shadows too dark on dark fabrics). Earlier quality work: `upscale.md`.

## 1. Problem and scope

| # | Defect | Cause | Step |
|---|---|---|---|
| D1 | Lace looks flat, like a sticker | No shadow from the lace on the fabric under it | 1 |
| D2 | Shadows too dark; dark fabrics (mocha) lose their folds | Light maths in sRGB, not in linear light | 2 |
| D3 | A faint second weave in every new fabric | `shade.png` keeps the weave of the white cotton of the base photo | 3 |
| D4 | Symmetric seams along the lace; motifs cut at the ends and at centre front | `MIRRORED_REPEAT`; lace length not matched to the trim length; no start point | 4 |
| D5 | Scallops, loops and pearls stop at the garment edge; they never hang past the hem or cuff | Every trim strip is clipped to the garment outline; no lace over the background | 5 |
| D6 | Lace has no relief; zari and pearls look like flat beige paint | One light model for all lace; no height, metal or pearl information in the lace asset | 6 |
| D7 | Fabric motifs ignore small folds; satin and silk have no sheen along the grain; the tile repeat of irregular embroidery is visible | UV follows only the annotated curves; fixed 0.15 highlight; plain `REPEAT` | 7 |

**Not in this plan:** new lace and swatch photography (review step 8), measured `repeatCm` and lace widths, soft alpha at the garment silhouette, print placement controls (centre a motif, mirror the bodice).

## 2. Rules for all steps

- **One step at a time.** Each step is its own commit and can be reverted alone.
- **Measure before and after** with the same harness (step 0). A step is not accepted on visual judgement alone.
- **Keep a copy** of every file that a step changes, as `<name>@<step>`, until step 8. Delete the copies at the end.
- **Plates:** if a step changes `make_plate.py`, run `tools/rebuild_check.sh`. Only the files that the step is meant to change may differ. Step 2 and step 3 change `shade.png`, and nothing else. Step 5 changes `id.png`, `uv_trim.png` and `plate.json`, and nothing else.
- **Test switch for each step**, so that before and after can be compared in the same page: `?shadow=0`, `?linear=0`, `?lacefit=0`, `?edging=0`, `?relief=0`, `?displace=0`, `?sheen=0`, `?antitile=0`. The old behaviour stays available until step 8.
- **Budgets:**

| Budget | Limit |
|---|---|
| Plate data for each view | ≤ 1.0 MB |
| Each lace asset (`.webp` + `.json`) | ≤ 600 KB |
| Draw time for one frame, desktop GPU | ≤ 5 ms (measure in a normal browser; headless Chrome reports virtual time) |
| Shader texture units | ≤ 8. All 8 are in use now, but units 4 and 7 both hold `shade.png`. `texelFetch` ignores the filter mode, so **one LINEAR shade texture can serve both**: step 6 frees unit 7 this way, and uses it for the lace material map. |
| Texture reads for each fabric pixel (step 7) | ≤ 3 extra (anti-tiling) |

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

### Step 5: Edging lace past the garment edge (D5)

**Do:**
1. **Trim type** in `zones.json`, for each trim: `"type": "edging"` (the decorative edge hangs past the garment edge) or `"insertion"` (fully inside, as now). Defaults: `hem`, `cuff-*` = edging; `neck`, `slit-*` = insertion.
2. **Lace sidecar** (from step 4, `lace-<name>.json`): add `"edgeDepth"`, the share of the band height that is the decorative edge (loops, scallops, pearls). `prep_lace.py` measures it: the rows below the last row where the lace alpha covers ≥ 80 % of the width.
3. **Plate maker** (`make_plate.py`):
   - For an edging trim, place the strip so that its inner `1 − edgeDepth` sits inside the garment, and its outer part hangs past the edge. With no sidecar value, use an overhang of 35 % of the trim width.
   - Write the trim id (`id.png` G) and `uv_trim.png` **also outside the garment** for the overhang. `id.png` R stays 0 there (no fabric).
   - Clip the overhang against objects in front: the mannequin arm, the stand. They stay photo.
   - Write `"outerV": 0 | 1` for each trim in `plate.json`: the side of the strip that points away from the garment. The shader uses it in place of the manual `FLIP` table.
4. **Shader:** where `zone == 0` and `trim > 0`, draw the lace over the **photo** (wall, form, stand). Its shadow falls on the photo too, softer and with a larger offset (×1.5), because the background is farther behind the lace than the fabric is.
5. Rebuild all plates. `rebuild_check.sh`: only `id.png`, `uv_trim.png` and `plate.json` may differ.
6. Test switch `?edging=0`: edging trims are clipped as before.

**Acceptance:**
- [ ] In the torso, sleeve and hem views, the scallops and loops of the geometric and fine laces hang past the hem and cuff edges by their decorative depth (± 1 mm).
- [ ] Inside the lace holes in the overhang, the photo (wall, stand) shows, not fabric.
- [ ] The overhang never covers the mannequin arm in the sleeve view, or the stand where it is in front of the hem.
- [ ] Every trim's decorative edge points outward with **no manual `FLIP`** entries (check all 4 laces × all trims).
- [ ] `fabric=off` with all lace off: pixel-identical to step 4.
- [ ] Plate data ≤ 1.0 MB.

### Step 6: Lace relief, metal and pearl masks (D6)

**Do:**
1. **Free texture unit 7:** one shade texture with LINEAR filtering. Keep `texelFetch` for exact reads and `texture()` for the smooth read. Check that the render is pixel-identical before you go on.
2. **Lace material map**, made by `prep_lace.py`, the same size as the lace band: `lace-<name>-mat.webp`, lossless:
   - **R = height:** the luminance of the lace, high-pass filtered (radius ≈ 2 mm in lace scale) and weighted by alpha, normalized to 0–255.
   - **G = metal:** zari and metallic thread. Hue between gold and brass, and strong local brightness variation. Only the fine lace is expected to have a metal mask.
   - **B = pearl:** small, bright, round blobs (difference-of-Gaussians blob detector at the pearl size). Only the pearl lace is expected to have one.
3. **Shader**, on lace pixels:
   - Normal from the height gradient (two extra reads of the material map), and diffuse light from the upper left: a lighter side towards the light and a darker side away from it, ± 15 % at most.
   - Metal: a specular highlight tinted with the lace colour, stronger where the garment shade is above 1 (where the photo was lit), and stretched along the thread.
   - Pearl: a small round highlight at the upper left of each pearl, and a little darker rim at the lower right.
4. Test switch `?relief=0`.

**Acceptance:**
- [ ] Unit 7 freed with no change to the render (mean pixel difference 0.0 on all 8 queries).
- [ ] Relief visible on all 4 laces at 2× (person check), with no change to the mean colour of the lace by more than 5 %.
- [ ] Metal highlights only where the metal mask is set: no highlight on the geometric or leaf lace.
- [ ] Pearl highlights only on the pearls of the pearl lace. The number of detected pearls in one repeat matches a count by a person within ± 10 %.
- [ ] No change outside the trims (as in step 1).
- [ ] Each lace asset (band + material + sidecar) ≤ 600 KB. The pearl lace must first get under the budget (it is 730 KB now).

### Step 7: Fabric: displacement in folds, directional sheen, anti-tiling (D7)

**Do:**
1. **Displacement in folds:**
   - Shift the fabric UV along the gradient of the shade: `uv += k · ∇shade`, with `k` in millimetres, clamped to ≤ 1.5 mm.
   - Compute the gradient only from neighbours in the same zone (like `gradFabric`), so no tear appears at a zone edge.
   - Start with `k` = 1.0 mm. One value for all fabrics.
2. **Directional sheen** for each fabric, in the `FABRICS` table: `sheen` (strength, 0 = matte) and `sheenWidth`.
   - The highlight follows the shade above 1 (lit areas of the photo), and is stretched **along the grain**: the warp direction is the V gradient of the UV, which the shader already has.
   - Sage, mocha and mustard are matte (`sheen` = 0) until a satin or silk swatch is added. Test the effect with a temporary sheen on sage.
   - The fixed 0.15 highlight is removed. Matte fabrics then have no extra highlight.
3. **Anti-tiling** for each fabric, `antiTile: true | false`:
   - Hex tiling (three offset reads blended over a hexagonal grid, with contrast-preserving blending). **Offsets only, no rotation**, so the grain direction stays correct.
   - Use it only for irregular fabrics (mocha embroidery, crinkled gauze). A regular print or a woven check keeps an exact repeat (`antiTile: false`).
   - 3 extra reads for each fabric pixel, with the same gradients as now.
4. Test switches `?displace=0`, `?sheen=0`, `?antitile=0`.

**Acceptance:**
- [ ] Displacement: on the checker (`?checker` test button), column lines bend into the large folds by ≤ 1.5 mm, with no tear at zone edges and no change in the average square size (± 2 %).
- [ ] Sheen: with `sheen` = 0, the render of matte fabrics changes only by the removed 0.15 highlight. With a test sheen, the highlight runs along the grain on the front and along the arm on the sleeve.
- [ ] Anti-tiling on mocha: the autocorrelation peak of the bodice crop at the tile period drops by **≥ 50 %**; sharpness of the crop ≥ 90 % of step 6; no visible blending blur in the motifs (person check at 2×).
- [ ] FCR (exact) stays ≥ 0.8 on queries 2, 3, 4.
- [ ] Draw time ≤ 5 ms (normal browser): this step adds the most reads.

### Step 8: Close and record

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

Write the reason in `polish-results.md`, then continue. Dependencies:
- If step 2 is reverted, run step 3 with the sRGB shade.
- Step 5 uses the `edgeDepth` and the sidecar of step 4. Without step 4, use the 35 % default overhang.
- Step 6 needs unit 7 freed (its first task). If that fails, step 6 stops; steps 5 and 7 do not depend on it.

### Fallbacks

| Situation | Fallback |
|---|---|
| Step 1: the shadow looks dirty on light laces over dark fabric | Tint the shadow with the fabric colour (darker fabric, not grey), or lower the strength for each lace in its sidecar |
| Step 2: banding in dark shadows | 16-bit shade in two channels (high and low byte), like the UV packing |
| Step 2: `SRGB8_ALPHA8` mipmaps fail on a browser | Decode with `pow(c, 2.2)` in the shader, and accept slightly wrong mip averages |
| Step 3: folds become soft before the weave is gone | Smaller radius, or keep the weave on the torso plate (1 px radius) and smooth only the close views |
| Step 4: a lace has no clear period (hand-made, irregular) | Keep the mirror for that lace, and hide the joins at the trim ends: start the mirror at the centre front |
| Step 4: the fit is outside 0.95–1.05 on short trims (cuffs) | Allow up to ±10 % on trims shorter than 3 repeats |
| Step 5: the overhang shows paper colour or shadow at the lace edge | Use edging only on the laces with a clean key (geometric, fine); keep the others as insertion until they are photographed again |
| Step 5: the overhang meets the photo badly (wrong light on the wall) | Lower the lace's light on the background to the wall's luminance, and keep the shadow on the wall soft |
| Step 6: the relief looks noisy on the keyed laces | Smooth the height map more, or use relief only on the metal and pearl masks |
| Step 6: no texture unit can be freed | Pack the height into the lace's alpha-weighted luminance (no new texture): relief only, no metal or pearl |
| Step 7: hex tiling blurs the motifs | Larger hex cells (fewer blends), or use anti-tiling only on the crinkled gauze |
| Step 7: draw time above 5 ms | Anti-tiling off on phones (`devicePixelRatio` > 1.5 and a small screen); keep displacement and sheen |

### Stop the plan

Stop if steps 1–4 take more than **3 working days**, or steps 5–7 take more than **4 more working days**, or if steps 1 and 4 both fail. Then the lace needs real photography (review step 8) before more shader work.

### Always safe

Each step has a test switch for the old behaviour, so the demo works after every step.

## 5. Tracking

| Step | Status | Commit | Result (`polish-results.md`) |
|---|---|---|---|
| 0 Baseline | done | 09c78b4 | Step 0 |
| 1 Lace shadow | done | 3946728 | Step 1 |
| 2 Linear light | not started | | |
| 3 Shade without the weave | not started | | |
| 4 Lace repeat and placement | not started | | |
| 5 Edging lace past the edge | not started | | |
| 6 Lace relief, metal and pearl | not started | | |
| 7 Fabric displacement, sheen, anti-tiling | not started | | |
| 8 Close and record | not started | | |
