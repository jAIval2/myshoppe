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
