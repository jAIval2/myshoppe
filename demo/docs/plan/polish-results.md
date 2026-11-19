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
