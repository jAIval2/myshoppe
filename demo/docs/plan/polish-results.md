# Polish results

Plan: `polish.md`. Harness: `DPR=2 tools/shoot_views.sh <dir> <the 8 queries>` → `tools/polish_metrics.py crops|fcr|fd|joins`.
All screenshots are 2× (canvas 860 × 1147 px in a 1800 × 1520 screenshot). Fixed review crops: `baseline-polish/` (before) and later `after-step*/`.
Crop boxes are frozen in `tools/polish_metrics.py` (`CROPS`), in plate px, above the caption pill of the stage (it covers plate y > 1466).

## Step 0: baseline (2026-11-19)

### Harness repeatability

Two full runs of the 8 queries. Mean pixel difference on the **stage canvas**: 0.0 for 7 of 8 shots, 0.0007 for query 7 (21 on a handful of pixels). Everything else that differs between runs is the load-time text line below the stage. ✔ (≤ 1)

### Fold contrast retention (FCR)

Defined in `tools/polish_metrics.py`. Two versions:
- **plain:** std/mean of L of the render ÷ std/mean of L of the photo, both blurred by 8 mm (the plan's definition, with the blur added).
- **exact (the one to use):** the fold map is *render ÷ the same render with the shade switched off* (`?shade=0`, a test switch added in this step; default output is unchanged). The pattern of the fabric divides out, so only the folds count.

| Crop | Query | FCR plain | **FCR exact** |
|---|---|---|---|
| bodice-q2 | torso, mocha, geometric | 1.093 | **1.089** |
| bodice-q3 | neck, mustard, leaf | 1.165 | **1.167** |
| bodice-q4 | neck, mocha, fine | 1.883 | **1.255** |

The plain value of the mocha neck view (1.88) is mostly the large embroidery of the fabric, not folds: this is why the exact version exists.

**Finding that matters for step 2:** at the bodice centre the folds are **not lost** on any fabric: the exact FCR is already above 1. That is also what the maths says: the render is `fabric × shade` with shade = L / median of the photo. Multiplying by the ratio of two sRGB values is the same as multiplying in linear light by the ratio raised to the gamma, so under a pure power-law gamma the product is identical in both spaces. The review complaint ("shadows too dark on dark fabrics") is not visible in this measurement. Step 2 can still change things where the *filtering and blending* differ (mipmaps, lace alpha, photo edge), and the plan's criterion (≥ 0.8) is met by the baseline already.

### Fine detail of the shade (FD)

`shade.png`, inside the garment, away from its edges. Variance of the band, and its share of the total variance of the shade (0..255 scale).

| Plate | mm/px | total var | fine (< 1.5 mm) var | fine share | fold (2–30 mm) share |
|---|---|---|---|---|---|
| torso-straight | 0.898 | 382.0 | 2.730 | 0.72 % | 18.8 % |
| neck-straight | 0.305 | 361.6 | 3.498 | 0.97 % | 12.4 % |
| sleeve-straight | 0.338 | 218.8 | 3.445 | 1.57 % | 22.2 % |
| hem-straight | 0.222 | 269.8 | 6.737 | 2.50 % | 27.8 % |

(8-bit quantisation alone gives a floor of 1/12 = 0.083.)

### Lace seams (mirror joins)

`MIRRORED_REPEAT` puts a mirror join at every multiple of the lace image length along a trim. Computed from the trim length, the trim width and the lace aspect (`polish_metrics.py joins`). **No person has counted joins**: this is a computed upper bound of what can be seen, because a symmetric motif hides its own join.

| Crop | Trim in the crop | Lace | Computed mirror joins |
|---|---|---|---|
| hem-lace-q2 | torso hem, 37.6 cm | geometric | 6 |
| neck-lace-q3 | neck view neckline, 20.7 cm | leaf | 8 |
| cuff-lace-q5 | sleeve cuff-l, 10.6 cm | geometric | 2 |
| **Total in crops 2, 3, 5** | | | **16** |

Join discontinuity of the lace images themselves (wrap difference ÷ neighbour-column difference; 1 = no visible join): fine 16.7, geometric 3.6, leaf 3.8, pearl 4.2. None of the four lace files has a sidecar yet. The pearl lace (730 KB) is over the 600 KB asset budget today.

### Draw time

Not measurable here (headless Chrome reports virtual time). The ≤ 5 ms budget is to be checked by hand in a normal browser at the end.

## Step 1: shadow of the lace on the fabric (accepted)

`testing.html`: where a trim is on, the lace alpha is read a second time, shifted by `uShadowMm` = (0.6, 0.9) mm to the right and down, 1.5 mip levels softer (gradients × 2.83), and the fabric is darkened by `uShadowStrength` (0.35) × shadow alpha × (1 − lace alpha). The lace itself is not darkened. Test switch: `?shadow=0` (off), `?shadow=<n>` (strength). Backup: `testing@1.html` (untracked, deleted in step 5).

**Deviation from the plan:** the offset is not fixed in lace coordinates. Along the neckline the trim direction turns through about 180°, so a lace-coordinate offset would put the shadow on the wrong side on half of the neck. The shader turns the screen offset into lace coordinates with the UV gradients it already has (`gradTrim`), so the shadow stays lower-right on every trim. Without the plate gradients (`?aniso=0`) it assumes U to the right and V down.

| Check | Result |
|---|---|
| Pixels changed outside the trims (trims grown by 4 mm), all 8 queries | **0** |
| Bodice crops against step 0 (crops 2, 3, 4) | identical, mean difference 0.0 (also proves the default render did not change with the `?shade=0` switch of step 0) |
| Maximum darkening of any pixel (L new ÷ L old), 8 queries | 16.9 % to 34.7 % (≤ 35 % ✔) |
| Soft dark rim, lower-right, in crops 2, 3, 5 | seen: `docs/plan/img/polish-step1-before-after.png` (before left, after right). My own look, not a person's. |
| Draw time ≤ 5 ms | **not measured** (headless reports virtual time). The shader adds one texture read per lace pixel. |

"No darkening where the lace alpha is 0 within 1.5 mm" is not tested numerically: the soft read (about 1.5 mip levels) plus the 1.08 mm offset spreads the shadow up to about 2 mm from a lace edge on the lower-right side, so a strict 1.5 mm limit would not hold exactly. By construction, nothing is darkened more than 35 %.

Crops: `after-polish-1/`.

### Harness changes made during this step

- `tools/shoot_views.sh`: `JOBS` (processes at a time), `TMO` (timeout), waits for its own Chrome processes only; use `PORT=<free port>` when another run is active (two runs on one port kill each other's server).
- `tools/shoot_set.py`: runs a query list two at a time, rejects a shot that is only the fallback photo (the page had not drawn yet) and retries it. Four parallel software-rendered Chromes timed out on this machine; use this for review sets.

## Order of steps 2 and 3

Step 2 was tried first. Its square-root encoding made `shade.png` 17–19 % larger (it spreads the photo noise of the dark values over more codes), and the sleeve plate went to **1064 KB, over the 1.0 MB budget**. Re-compressing did not help (563 KB either way). Dropping the lowest bit fitted (500 KB) but costs precision in the dark folds, which is what step 2 is for. The steps are independent (§4 of the plan), and step 3 removes exactly that noise, so **step 3 was done first, on the sRGB shade**, and step 2 is done on top of it. The step 2 plate code was parked and the plates restored before step 3 started.

## Step 3: shade without the cotton weave (accepted, torso by the fallback)

`make_plate.py`: an edge-preserving **guided filter** on the shade (the shade is its own guide), made of box sums only (running sums with `itertools.accumulate`, so Pillow and plain Python are enough). **Masked per zone**: the box sums count only the pixels of the zone, so nothing mixes across a zone edge or the gap to the wall. Radius in mm (`shadeSmoothMm`, default 1.2 → neck 4 px, sleeve 4 px, hem 5 px). ε in `shadeSmoothEps`, default **0.006** on the 0–2 shade. Settings per plate in `zones.json`; `plate.json` records `shadeSmoothMm` and `shadeSmoothPx`. Run time: about 12–14 s CPU per plate (wall time on this machine was much longer at times: the machine stalls, not the code).

**Tuning (2 attempts, as the plan allows):**

| ε, radius | sleeve fine | neck fine | torso fine | fold kept (sleeve / neck / torso) |
|---|---|---|---|---|
| 0.002, 1.2 mm (attempt 1) | −67 % ✘ | −77 % | −35 % ✘ | 97.7 / 98.0 / 99.2 % |
| **0.006, 1.2 mm (attempt 2, kept)** | **−75 %** | **−83 %** | −45 % ✘ | 97.0 / 97.2 / 99.0 % |
| 0.012, 1.2 mm | −78 % | −86 % | −53 % ✘ | 96.7 / 96.8 / 98.8 % |
| 0.006, 1.8 mm | −77 % | −87 % | −52 % ✘ | 95.8 / 95.3 / 97.7 % |

**Torso:** no setting reaches −70 %. At 0.9 mm/px the cotton weave (0.3–0.5 mm) cannot be resolved by the plate at all; what is left below 1.5 mm (1.7 px) is 1–2 px photo noise, and the "second weave" defect cannot appear in this view. The plan's fallback applies ("keep the weave on the torso plate and smooth only the close views"): the torso sets `"shadeSmoothMm": 0` in its `zones.json`, and its shade is unchanged.

**Final numbers** (FD as in step 0):

| Plate | fine < 1.5 mm, var | reduction (≥ 70 %) | fold 2–30 mm kept (≥ 90 %) | plate data |
|---|---|---|---|---|
| hem-straight | 6.737 → 0.674 | **−90 %** ✔ | 99.4 % ✔ | 785 → 424 KB ✔ |
| neck-straight | 3.498 → 0.583 | **−83 %** ✔ | 97.2 % ✔ | 668 → 343 KB ✔ |
| sleeve-straight | 3.445 → 0.861 | **−75 %** ✔ | 97.0 % ✔ | 975 → 677 KB ✔ |
| torso-straight | unchanged (fallback) | — | — | 396 KB ✔ |

**Rendered (8 queries + 3 flat-light, against step 1):**
- Mean luminance of every query unchanged (largest change 0.04 of 255). Mean |difference| 0.0–1.4 levels; the torso queries are identical (its shade did not change).
- FCR (exact): 1.089 / **1.180** / **1.264** (step 0: 1.089 / 1.167 / 1.255). The folds stay.
- Neck view, mustard, and sleeve cuff at 3× (`docs/plan/img/polish-step3-before-after.png`, before left): the folds, the seam lines and the cuff edge still show. At this zoom the mustard's own texture dominates, and I could not point to a second weave **in either** image. The "no second weave" item still needs a person's look; the plate numbers above are the measurable part.

`rebuild_check.sh`: only `shade.png` and `plate.json` (and the review image `check.png`, which is drawn with the shade) changed; `id.png`, `uv.png`, `uv_trim.png` identical. Copies: `shade@3.png`, `plate@3.json` in each plate folder (untracked, deleted at the close).

## Step 2: light maths in linear light (accepted, partly verified)

**Plates** (`make_plate.py`): after the step 3 smoothing (on the sRGB ratio, so its tuning stays exact), the shade is converted to the **linear** ratio `lin(L) / lin(median)` and stored as `sqrt(shade / 2) × 255`; `plate.json` gets `"shadeSpace": "linear"`, `"shadeEncoding": "sqrt"`. `zones.json` `"shadeSpace": "srgb"` keeps the old file. `check.png` converts back, so the review checker looks as before.

**Shader** (`testing.html`): photo, fabric and lace uploaded as `SRGB8_ALPHA8` (the GPU decodes them, mipmaps included); if `generateMipmap` fails on that format, the page re-uploads `RGBA8` and decodes in the shader (the plan's fallback). Multiply, shadow, lace mix and the photo edge mix are done in linear light, and the result is encoded to sRGB at the end (exact sRGB curve). The shader reads `shadeEncoding` and converts an old sRGB shade (or, with `?linear=0`, converts a new shade back) using `shadeMedian`. The 0.15 sRGB highlight becomes 0.05 in linear light (my estimate of the same sheen on mid to dark fabric); the lace light cap 1.05 / 1.15 becomes 1.05^2.4 / 1.15^2.4. Test switch: `?linear=0` (old sRGB maths, `RGBA8` textures).

| Check | Result |
|---|---|
| `rebuild_check.sh` | only `shade.png` and `plate.json` differ (plus the review image `check.png`) ✔ |
| Plate data | torso 430, neck 382, **sleeve 723**, hem 470 KB (≤ 1.0 MB ✔; without step 3 first the sleeve was 1064 KB) |
| Mean luminance of the render, against step 3 | torso sage +0.15 %, torso mocha +0.87 % (≤ 8 % ✔). Measured on the two queries rendered before the screenshot runs were stopped. |
| FCR (exact) | **not measured** at this step (the flat-light renders were stopped). The maths says it cannot fall: a multiply by the shade ratio is the same in sRGB and in linear light under a power-law gamma (step 0 finding), and the two torso renders above differ by < 1 % in mean. |
| `fabric=off` ≤ 1 level | **not measured** (stopped). The photo is decoded by the GPU and encoded again with the exact curve, which round-trips 8-bit values to within 1 level. |
| No banding in dark shadows | **not checked** in a render. The square-root code gives 0.4–2 % steps in linear light (finer than 8-bit linear, close to the old sRGB file). |
| `?linear=0` same as step 3 | **not checked** in a render. |

**Screenshot runs stopped here, at the owner's request**: each render set took 25–30 min on this machine (software rendering, a second session competing for the CPU). From step 2 on, steps are checked offline (plates, assets, computed numbers, code review); the items that need a real browser are listed for each step and collected under step 8.

## Step 4: real lace repeat, whole repeats, defined start (accepted with 2 recorded exceptions)

**`prep_lace.py --repeat`** (new mode, works on the existing bands; no lace source photos are in the repo):
1. Period = Pearson autocorrelation of the alpha along the band (columns, 1/4 size, refined at 1/2 size with a parabola).
   **Refinement of the plan's rule:** lags shorter than 0.3 × the band height are skipped (they are the mesh of the lace: the geometric lace peaks at 72 px = its net, not its motif), and the period is the first peak ≥ 0.6 **and** ≥ 0.9 × the best peak (the fine lace has peaks of 0.88–0.91 at 184, 256, 300, 360 px; the first is taken).
2. A whole number of periods, starting at a gap between motifs (least alpha), resampled to an exact integer width; the last 4 % cross-fades to the band just **before** the start, so the wrap is continuous by construction.
3. Sidecar `lace-<name>.json`: `periodPx`, `periods`, `periodRatio`, `motifCentrePx`, `corr`, `cutFromPx`, `blendPx`, `edge`, `widthMm` (assumption), and for step 5 `edgeDepth`, `bottomOpen`, `edging`, `flipped`.

| Lace | Period | corr | Tile | Asset (webp + json) | Wrap ratio (old → new) |
|---|---|---|---|---|---|
| pearl | 632.0 px = 1.417 × height | 0.69 | 2 periods, 1264 × 446 | **434 KB** (was 730: now within the 600 KB budget) | 5.1 → **1.04** |
| geometric | 177.7 px = 0.398 × height | 0.61 | 3 periods, 533 × 446 (the band is too short for 1024 px) | 158 KB | 3.9 → **1.18** |
| fine | 183.0 px = 0.410 × height | 0.88 | 6 periods, 1098 × 446 | 68 KB | 15.6 → **1.49** |
| leaf | **none** (best peak 0.27) | — | band kept, mirror kept | 326 KB | (mirror) |

Wrap ratio = premultiplied difference between the last and first column ÷ median neighbour-column difference (1 = no visible join). The metric now ignores the colour under fully transparent pixels (lossy WebP stores noise there; that had made the pearl read 3.1). Wrap previews: `docs/plan/img/polish-step4-wraps.png`.

**Exceptions:**
- **leaf:** no repeat (hand-made or irregular; the best autocorrelation peak is 0.27). Plan fallback: the mirror is kept, and on neck and hem the mirror axis is put at the **middle of the trim** (centre front), so the reflection is symmetric about the centre instead of at a random place.
- **geometric:** the diamonds repeat every 177.7 px, but the scallop edge repeats every **80 px** (measured on the scallop rows alone: corr 0.84). The two pitches have no common multiple inside the 875 px band (the nearest is ~716 px, which with the blend does not fit). The diamonds wrap seamlessly; the scallop row has a small soft jog at each wrap (every 3 diamonds). Better than the mirror (a reflection every 2.4–5.9 cm), but not seam-free. A longer photo of this lace would fix it.
- The geometric band was **turned 180°** (`--flip`): its clean, keyed scallops were at the top and its bottom was cut through the pattern; the convention is the decorative edge at the bottom (step 5 needs it).

**Page** (`testing.html`): `REPEAT` along the lace for laces with a period, `MIRRORED_REPEAT` for laces without one (or `?lacefit=0`). `laceFit()` computes, for every trim of the current view and lace, the number of whole repeats and the scale (`uTrimFit[7]`) and the start (`uTrimU0[7]`):
- `n = round(L / r)`, `fit = L / (n·r)`, kept only within ±5 % (±10 % on trims shorter than 3 repeats: plan fallback); otherwise the scale stays and the trim is listed.
- `neck`, `hem`: an **odd** `n` when that fits within the limit: then a motif is centred at the middle **and** both ends are motif boundaries (an even `n` can have only one of the two). The motif centre is put at the middle of the trim.
- `cuff-*`: a motif boundary at the start of the trim; `slit-*`: at the hem end. With whole repeats the other end is a boundary too.
- The result is written to `<html data-lacefit>` for inspection.

**Fit on every trim** (`polish_metrics.py fit`, the same rules as the page): 35 of 36 trims with a period fit within their limit; scale changes −5.0 % to +3.4 %.

| Exception | Why |
|---|---|
| hem view, `hem`, **pearl** | L / r = 3.43: 3 repeats need +14.5 %, 4 need −14 %. Scale kept; a motif is cut at one end. |
| neck view `neck` and sleeve view `neck`, **pearl** | Odd counts need ±6–10 %, so even n (12, 10) are used: whole motifs at both ends, but a **gap** (not a motif) at the centre front. |
| torso `cuff-l`, pearl | −5.0 %: inside the ±10 % limit of a short trim (2.85 repeats). |

Full table: below.

```
pearl     period 632.0 px = 1.417 x band height, 2 periods per image
   torso  neck    L  18.2 cm  repeat  1.70 cm  L/r  10.70  n  11  scale  0.973 ( -2.7 %, limit 5 %)  centred motif, whole motifs at both ends
   torso  cuff-l  L  10.1 cm  repeat  3.54 cm  L/r   2.85  n   3  scale  0.950 ( -5.0 %, limit 10 %)  whole motifs at both ends
   torso  cuff-r  L  10.3 cm  repeat  3.54 cm  L/r   2.91  n   3  scale  0.969 ( -3.1 %, limit 10 %)  whole motifs at both ends
   torso  hem     L  37.6 cm  repeat  4.25 cm  L/r   8.84  n   9  scale  0.983 ( -1.7 %, limit 5 %)  centred motif, whole motifs at both ends
   torso  slit-l  L  24.1 cm  repeat  1.13 cm  L/r  21.26  n  21  scale  1.012 ( +1.2 %, limit 5 %)  whole motifs at both ends
   torso  slit-r  L  23.4 cm  repeat  1.13 cm  L/r  20.64  n  21  scale  0.983 ( -1.7 %, limit 5 %)  whole motifs at both ends
   neck   neck    L  20.7 cm  repeat  1.70 cm  L/r  12.17  n  12  scale  1.014 ( +1.4 %, limit 5 %)  whole motifs at both ends
   sleeve neck    L  17.2 cm  repeat  1.70 cm  L/r  10.11  n  10  scale  1.011 ( +1.1 %, limit 5 %)  whole motifs at both ends
   sleeve cuff-l  L  10.6 cm  repeat  3.54 cm  L/r   2.99  n   3  scale  0.997 ( -0.3 %, limit 10 %)  whole motifs at both ends
   hem    hem     L  14.6 cm  repeat  4.25 cm  L/r   3.43  n   3  scale  1.145 (+14.5 %, limit 5 %)  NOT FITTED: scale kept, motif cut at one end
   hem    slit-l  L  23.5 cm  repeat  1.13 cm  L/r  20.73  n  21  scale  0.987 ( -1.3 %, limit 5 %)  whole motifs at both ends
   hem    slit-r  L  22.8 cm  repeat  1.13 cm  L/r  20.11  n  20  scale  1.006 ( +0.6 %, limit 5 %)  whole motifs at both ends
geometric period 177.667 px = 0.398 x band height, 3 periods per image
   torso  neck    L  18.2 cm  repeat  0.48 cm  L/r  38.07  n  39  scale  0.976 ( -2.4 %, limit 5 %)  centred motif, whole motifs at both ends
   torso  cuff-l  L  10.1 cm  repeat  1.00 cm  L/r  10.14  n  10  scale  1.014 ( +1.4 %, limit 5 %)  whole motifs at both ends
   torso  cuff-r  L  10.3 cm  repeat  1.00 cm  L/r  10.34  n  10  scale  1.034 ( +3.4 %, limit 5 %)  whole motifs at both ends
   torso  hem     L  37.6 cm  repeat  1.20 cm  L/r  31.46  n  31  scale  1.015 ( +1.5 %, limit 5 %)  centred motif, whole motifs at both ends
   torso  slit-l  L  24.1 cm  repeat  0.32 cm  L/r  75.62  n  76  scale  0.995 ( -0.5 %, limit 5 %)  whole motifs at both ends
   torso  slit-r  L  23.4 cm  repeat  0.32 cm  L/r  73.43  n  73  scale  1.006 ( +0.6 %, limit 5 %)  whole motifs at both ends
   neck   neck    L  20.7 cm  repeat  0.48 cm  L/r  43.30  n  43  scale  1.007 ( +0.7 %, limit 5 %)  centred motif, whole motifs at both ends
   sleeve neck    L  17.2 cm  repeat  0.48 cm  L/r  35.98  n  35  scale  1.028 ( +2.8 %, limit 5 %)  centred motif, whole motifs at both ends
   sleeve cuff-l  L  10.6 cm  repeat  1.00 cm  L/r  10.64  n  11  scale  0.968 ( -3.2 %, limit 5 %)  whole motifs at both ends
   hem    hem     L  14.6 cm  repeat  1.20 cm  L/r  12.22  n  12  scale  1.018 ( +1.8 %, limit 5 %)  whole motifs at both ends
   hem    slit-l  L  23.5 cm  repeat  0.32 cm  L/r  73.74  n  74  scale  0.996 ( -0.4 %, limit 5 %)  whole motifs at both ends
   hem    slit-r  L  22.8 cm  repeat  0.32 cm  L/r  71.54  n  72  scale  0.994 ( -0.6 %, limit 5 %)  whole motifs at both ends
leaf      no repeat: mirror kept, mirror axis at the middle of neck and hem
fine      period 183.0 px = 0.410 x band height, 6 periods per image
   torso  neck    L  18.2 cm  repeat  0.49 cm  L/r  36.96  n  37  scale  0.999 ( -0.1 %, limit 5 %)  centred motif, whole motifs at both ends
   torso  cuff-l  L  10.1 cm  repeat  1.03 cm  L/r   9.85  n  10  scale  0.985 ( -1.5 %, limit 5 %)  whole motifs at both ends
   torso  cuff-r  L  10.3 cm  repeat  1.03 cm  L/r  10.04  n  10  scale  1.004 ( +0.4 %, limit 5 %)  whole motifs at both ends
   torso  hem     L  37.6 cm  repeat  1.23 cm  L/r  30.55  n  31  scale  0.985 ( -1.5 %, limit 5 %)  centred motif, whole motifs at both ends
   torso  slit-l  L  24.1 cm  repeat  0.33 cm  L/r  73.42  n  73  scale  1.006 ( +0.6 %, limit 5 %)  whole motifs at both ends
   torso  slit-r  L  23.4 cm  repeat  0.33 cm  L/r  71.29  n  71  scale  1.004 ( +0.4 %, limit 5 %)  whole motifs at both ends
   neck   neck    L  20.7 cm  repeat  0.49 cm  L/r  42.04  n  43  scale  0.978 ( -2.2 %, limit 5 %)  centred motif, whole motifs at both ends
   sleeve neck    L  17.2 cm  repeat  0.49 cm  L/r  34.93  n  35  scale  0.998 ( -0.2 %, limit 5 %)  centred motif, whole motifs at both ends
   sleeve cuff-l  L  10.6 cm  repeat  1.03 cm  L/r  10.33  n  10  scale  1.033 ( +3.3 %, limit 5 %)  whole motifs at both ends
   hem    hem     L  14.6 cm  repeat  1.23 cm  L/r  11.86  n  12  scale  0.988 ( -1.2 %, limit 5 %)  whole motifs at both ends
   hem    slit-l  L  23.5 cm  repeat  0.33 cm  L/r  71.59  n  72  scale  0.994 ( -0.6 %, limit 5 %)  whole motifs at both ends
   hem    slit-r  L  22.8 cm  repeat  0.33 cm  L/r  69.46  n  69  scale  1.007 ( +0.7 %, limit 5 %)  whole motifs at both ends
```

**Acceptance:**

| Check | Result |
|---|---|
| A measured period for each lace, or a recorded reason | ✔ (leaf: reason recorded) |
| Lace seam count in crops 2, 3, 5 = 0 | **Not met.** Crops 2 and 5 (geometric): 0 mirror joins (were 6 and 2), but a soft scallop jog at each wrap. Crop 3 (leaf): mirror kept by the fallback (8 reflections, axis at centre front). Not counted by a person. |
| Whole motifs at both ends, motif centred at centre front within ±5 % of a repeat (torso neck and hem) | ✔ by construction for every fitted trim with odd n (all torso necks and hems: n = 11/9 pearl, 39/31 geometric, 37/31 fine); pearl on the neck and sleeve views: gap at centre front (listed above). **Not checked in a render.** |
| Scale change ≤ 5 % (or listed) | ✔ (1 trim listed) |
| Each lace asset ≤ 600 KB | ✔ (434 / 158 / 326 / 68 KB) |

Backups: `lace-*-2048@4.webp`, `testing@4.html` (untracked).

## Step 5: edging lace past the garment edge (accepted, offline checks only)

**Plates** (`make_plate.py`):
- Each trim has a `type`: `edging` (default for `hem`, `cuff-*`) or `insertion` (`neck`, `slit-*`); `zones.json` can set it per trim.
- Every strip is now written with **V = 0 at its inner side and V = 1 at the side of the garment edge it follows**, for every trim (`plate.json` `"outerV": 1`). The side is found by marching out along both normals (up to 60 px) and taking the side where the garment ends first. So the decorative edge of a lace points outward with **no manual `FLIP`** (the page uses `FLIP` only for plates without `outerV`).
- An edging strip is written to **V = 1.5** (`"vMax"`): the part past V = 1 lies outside the garment, where `id.png` R stays 0 and only G (trim id) and `uv_trim.png` are written. That part is clipped by `"occluders"` in `zones.json`; `annotate_sleeve.py` now writes the mannequin arm below the cuff as one (only that key changed: `base.jpg` and `annotate.png` byte-identical).

**Laces:** the sidecar's `edgeDepth` (share of the band height below the last row with ≥ 80 % alpha cover) and `edging` (true only if the bottom 5 % of the band is mostly open). Measured:

| Lace | edgeDepth | bottom 5 % open | edging |
|---|---|---|---|
| pearl | 0.096 | 77 % | **yes** |
| geometric (turned 180° in step 4) | 0.112 | 75 % | **yes** |
| fine | 0.0 | 0 % | no: the paper inside the loops was never keyed (alpha 1 everywhere) |
| leaf | 0.0 | 4 % | no: the tulle ground is partly opaque down to the bottom row |

This is the plan's fallback ("edging only on the laces with a clean key"), but the data picked **pearl and geometric**, not geometric and fine as the plan expected: the fine lace has the worst key of the four. Fine and leaf stay insertion until they are photographed (or keyed) again.

**Shader:** where the trim is edging **and** the lace allows it, the lace is shifted outward by `edgeDepth` (its decorative edge crosses the garment edge). Over the background (`zone == 0`) the lace is drawn over the photo, with its shadow on the photo **×1.5 longer and softer** (+0.5 mip). Outside the edging case the overhang pixels are ignored completely (as before the step). Test switch `?edging=0`.

**Checks (offline, on the plates; `polish_metrics`-style scans of id / uv_trim):**

| Check | Result |
|---|---|
| `rebuild_check.sh` | only `id.png`, `uv_trim.png`, `plate.json` differ (neck `id.png` unchanged: no edging trim) ✔ |
| Overhang written, outside the garment | torso: cuffs 1611 / 1682 px, hem 7287 px on the background; sleeve cuff 1195 px on the background + 3787 px over the bodice (the lace hangs in front of the body); hem view: 44559 px ✔ |
| Overhang on the mannequin arm (sleeve) | 0 px of overhang; 57 px of the **inner** strip lie on the rasterised edge of the arm polygon (on the garment side of the cuff edge) |
| Decorative edge outward, no FLIP, all trims | ✔ every edging trim (its V > 1 part lies outside the garment); every insertion trim: the V > 0.85 side is the one next to the garment edge (neck: 1.00 vs 0.02–0.05; hem-view slits: 0.97 vs 0.00–0.01; torso slits: V = 1 on the side away from the centre) |
| Overhang depth = decorative depth ± 1 mm | by construction: shift = edgeDepth × trim width (pearl on a 30 mm hem: 2.9 mm; geometric: 3.4 mm). **Not checked in a render.** |
| Holes in the overhang show the photo | by construction (the base colour there is the photo). **Not checked in a render.** |
| `fabric=off`, all lace off: identical to step 4 | by code: with no trim on, a background pixel returns the photo before any new code. **Not checked in a render.** |
| Plate data | torso 437, neck 381, sleeve 726, hem 481 KB ✔ |

Backups: `id@5.png`, `uv_trim@5.png`, `plate@5.json`, sleeve `zones@5.json`, `testing@5.html` (untracked).

## Step 6: lace relief, metal and pearl masks (accepted, offline checks only)

**Unit 7 freed:** `shade.png` is uploaded once, on unit 4, with LINEAR filtering. `texelFetch` ignores the filter mode (exact reads, as before) and `texture()` gives the smooth read for a canvas larger than the plate (was the second copy on unit 7). Unit 7 now holds the lace material map. **Pixel identity is by the GL rule, not checked in a render.**

**Material map** (`prep_lace.py --material`, lossless WebP at half the tile size: height and masks are smooth, and half size keeps the assets within budget):
- **R height:** lace luminance high-passed at 2 mm in lace scale, × alpha; 128 = flat.
- **G metal:** hue 20–60°, saturation ≥ 0.55, strong local brightness change, and the lace counts as metal only if ≥ 30 % of its opaque pixels pass (a zari lace is metallic through and through). Attempt 1 (saturation ≥ 0.40) marked 47 % of the geometric lace as metal; attempt 2 (≥ 0.50) still 16 %; the lace-level rule settles it.
- **B pearl:** the pearls in the pearl lace are **rings** (their bright centres were keyed out with the paper: the known problem in `render.md`). The detector finds round transparent holes (difference of Gaussians on the inverted alpha, hole radius 6 px) closed by a pale, bright, opaque ring (10–16 px), in the decorative edge (bottom 30 % of the band). Attempt 1 (a bright-blob detector on luminance) found 128 "pearls" per repeat, all in the lace mesh.

| Lace | metal (share of opaque px) | pearls per repeat | asset (band + map + json) |
|---|---|---|---|
| pearl | 0 (0.0) | **6.0** | 524 KB ✔ |
| geometric | 0 (0.08 < 0.30) ✔ | 0 | 211 KB ✔ |
| fine | **52.9 % of the tile** (0.54) | 0 | 179 KB ✔ |
| leaf | 0 (0.00) ✔ | 0 | 409 KB ✔ |

**Pearl count:** 6 per repeat, in both repeats of the tile, at the positions I counted on the tile (three large pearls hanging between three smaller ones). **My count, not a person's.**

**Shader** (on lace pixels, when the lace has a map; `?relief=0` turns it off): 3 reads of the map (centre, +1.5 canvas px in x and y, so the light is from the upper left on every trim whatever its direction), +1 read for metal.
- Relief: `lit = 1 + 0.15 × (∂h/∂x + ∂h/∂y)`, clamped to ±15 %. The gain was set offline: simulated on the tiles at stage scale, a gain of 1.5 clamped 70–85 % of the lace pixels (black-and-white noise), 0.25 still 5–24 %; 0.15 is used.
- Pearls: the dome fills the keyed-out centres with a pearl white, lighter on the upper-left half, darker rim on the lower right, and a small highlight. **This also fixes the "pearls show only as rings" problem.**
- Metal: a highlight tinted with the thread colour where the height is above its 3× along-the-lace average (stretched along the thread), stronger where the shade is above 1.

| Check | Result |
|---|---|
| Unit 7 freed, render unchanged | by the GL rule (texelFetch ignores filtering); **not checked in a render** |
| Mean lace colour change ≤ 5 % | relief term, simulated on the tiles: −0.5 to −2.1 % at gain 0.25 (gain 0.15 is smaller) ✔ |
| Metal only where the mask is set; none on geometric or leaf | ✔ (masks are 0 on geometric, leaf, pearl) |
| Pearl highlights only on the pearls; count within ± 10 % of a person's | 6 per repeat found = 6 counted (by me) |
| No change outside the trims | by code (all new shader code is inside the lace block) |
| Each lace asset ≤ 600 KB | ✔ (max 524 KB) |
| Relief visible on all 4 laces at 2× (person check) | **not done** |

Backups: `lace-*@6.json`, `testing@6.html` (untracked).

## Step 7: fabric displacement in folds, directional sheen, anti-tiling (accepted, offline checks only)

**Shader** (`testing.html`):
- **Displacement:** the shade gradient from the four neighbours at ±4 plate px, used only if all four are in the same zone (no tear at a zone edge), per mm. The fabric UV moves along it by `uDisplaceMm` (1.0 mm) at a strong fold slope (0.05 shade per mm), at most **1.5 mm**, mapped to UV with the plate gradients that `gradFabric` already gives. It is applied before both the fabric and the grain checker. `?displace=0`.
  The plan's `uv += k · ∇shade` has no unit for the gradient; the reference slope of 0.05 per mm makes "k = 1 mm" mean 1 mm in a strong fold.
- **Directional sheen:** `sheen`, `sheenWidth` in the `FABRICS` table. The highlight is the shade above 1, **averaged along the warp** (±2 samples, 6 plate px apart, in the direction in which V changes fastest: down the front, along the arm), so it is stretched along the grain. Sage, mocha and mustard are matte (`sheen: 0`); `?sheen=test` gives the current fabric a temporary sheen of 0.6. **The fixed 0.15 highlight is removed**; `?sheen=0` brings it back.
- **Anti-tiling:** hex tiling, `antiTile` in the `FABRICS` table (mocha, mustard: on; sage: off). Three reads at random **offsets only** (no rotation, so the grain stays), blended over a triangle grid with narrow zones (weights^7), with the contrast-preserving blend `mean + Σ wᵢ(cᵢ − mean) / √Σwᵢ²`; the mean is the top mip of the swatch. Reads: 3 + 1 instead of 1 (**3 extra**, the budget). `?antitile=0`.

**Checks (offline):**

| Check | Result |
|---|---|
| Displacement ≤ 1.5 mm | by the clamp. Same maths on the plates: median 0.14–0.19 mm, 90th percentile 0.49–0.73 mm, at the 1.5 mm cap on 0.9–2.3 % of the fabric pixels (the deepest folds) |
| No tear at zone edges | by construction (no displacement unless all four neighbours are in the zone) |
| Average square size unchanged (± 2 %) | displacement is a local shift of ≤ 1.5 mm with no mean scale; **not measured on a rendered checker** |
| Sheen: matte fabrics change only by the removed highlight | by code (`col = f · s`); along the grain with a test sheen: **not checked in a render** |
| Anti-tiling, mocha: autocorrelation at the tile period −50 % | simulated offline with the shader's maths on a flat 3 × 3 tile field: **1.000 → 0.005** (and mustard 1.000 → 0.011) ✔ |
| Sharpness ≥ 90 % | simulated: 100 % ✔ (the contrast-preserving blend keeps the motifs crisp) |
| No visible blending blur in the motifs | simulated image `docs/plan/img/polish-step7-antitile.png` (left plain, middle 1 cell per tile = used, right softer weights). 2 cells per tile was tried first: no blur, but more vines cut at the cell borders; 1 cell per tile kept. **Person check at 2× in a render not done.** |
| FCR ≥ 0.8 | **not measured** (needs renders). Displacement moves the pattern, not the light; removing the highlight lowers the lit side by ≤ 0.05 × (s − 1) in linear light |
| Draw time ≤ 5 ms | **not measured** (normal browser needed). This step adds the most reads: 4 shade + 4 id reads for displacement, 3 + 1 fabric reads for anti-tiling, 4 + 4 for a sheen fabric |

Backup: `testing@7.html` (untracked).
