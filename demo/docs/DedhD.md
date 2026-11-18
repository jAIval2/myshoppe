# Combination analysis: how many plates the boutique needs

Date: 2026-11-18. Status: analysis, for decisions with the atelier.
Source of the option counts: the Salon code (`C_GROUPS`, `C_FIELDS_BY_SILHOUETTE` in the Bespoke Studio — 2 demo).
Related: `render.md` (method), `plan/upscale.md` (quality).

## 1. Summary

| Method | Count |
|---|---|
| A finished image for every combination (shape × cloth × lace) | ≈ 1.5 million (≈ 4.7 million with two borders) |
| Shapes only (cloth and lace are applied in the shader) | 21,378 |
| Layers, with shared parts | ≈ 84 plates |
| Layers on an anchored model | ≈ 77 plates (≈ 89 with 4 shoulder variations; ≈ 160 without anchoring) |
| Source photos (layers combined in the photos) | ≈ 52–57 |

The decision with the most effect is **which options each house look permits**. It changes the count more than any technical short-circuit.

## 2. Options in the Salon now

| Option | Count | Applies to |
|---|---|---|
| Silhouette | 7 | Straight, A-line, Anarkali, Angrakha, Kurta & sharara, Lehenga & choli, Saree blouse |
| Neckline | 7 | All |
| Sleeves | 6 | All (sleeveless, cap, elbow, ¾, full, bell) |
| Length | 4 | Straight, A-line, Angrakha, Anarkali |
| Worn with (bottom) | 6 (5 + none) | Straight, A-line, Angrakha, Anarkali |
| Dupatta | 5 (4 + none) | All except the saree blouse |
| Back | 4 | Lehenga & choli, saree blouse |
| Cloth | 10 | Surface |
| Border / lace | 6 | Surface. The code permits more than one. |

## 3. All combinations

| Silhouette group | Shape options | Shape combinations |
|---|---|---|
| Straight, A-line, Angrakha, Anarkali | 7 × 6 × 4 × 6 × 5 | 5,040 each → 20,160 |
| Kurta & sharara | 7 × 6 × 5 | 210 |
| Lehenga & choli | 7 × 6 × 4 × 5 | 840 |
| Saree blouse | 7 × 6 × 4 | 168 |
| **Total shapes** | | **21,378** |

With cloth and lace: 21,378 × 10 × 7 ≈ 1.5 million finished images. Pre-rendering every combination (the CLO3D / Cylindo method) is not possible.

## 4. Short-circuits

1. **Surface options cost nothing.** The shader applies cloth and lace. 1.5 million → 21,378 shapes.
2. **Layers, not combinations.** Each part is its own layer, so the count is a **sum** of part variants, not a product.
3. **Shared geometry.**
   - The 5 kurta-type silhouettes have the same shoulder, armhole and upper bodice. The choli and the blouse share another. So there are **2 bodice families** for necklines and sleeves.
   - Plain, bordered and embroidered dupattas have the same drape. Only the tassels add geometry.
   - In the hem view, the camera follows the hem, so length does not multiply.
   - "None" options need no layer.
4. **One photo carries several layers.** Combine the variants across the photos (for example, each torso photo uses a different neckline and sleeve). Then the number of photos is close to the largest variant group, not the sum of the layers.

### Plates with short-circuits 1–3

| View | Layers | Plates |
|---|---|---|
| Torso | Body: 4 kurta types × 4 lengths + sharara + lehenga + blouse = 19. Necklines: 7 × 2 families = 14. Sleeves: 5. Bottoms: 5. Dupatta ≈ 3. | ≈ 46 |
| Neckline | 7 × 2 families | 14 |
| Sleeve | 6 × 2 families | 12 |
| Hem | 7 hem types + 5 bottoms | ≈ 12 |
| Back (5th view, optional) | 4 backs + 1 kurta back | ≈ 5 |
| **Total** | | **≈ 84–89** |

## 5. Anchored model

**Anchored** means: one dress form, one locked camera for each view, fixed light, and **one set of landmarks for all photos** (neck points, shoulder points, underarm, bust line, waist line, hem lines for each length).

### Where the silhouettes differ

| Region | Straight / Angrakha | A-line | Anarkali | Kurta & sharara | Choli / Blouse |
|---|---|---|---|---|---|
| Shoulder → underarm | same | same | same | same | own |
| Underarm → waist | loose, straight | starts to flare | fitted bodice, waist seam | loose, straight | ends at or above the waist |
| Waist → hem | straight | cone | pleated flare | short kurta | lehenga skirt / saree drape |

Above the bust, an anarkali and a kurta are the same. The neckline and sleeve views cannot show the difference.

### What anchoring adds

- **A. Bands that join at fixed lines** (underarm line, waist line): upper band 2, middle band 4, lower band 6.
- **B. Length is a cut, not a photo.** Use the ankle-length version of each lower band. Cut it at the hem line for hip, knee and calf, and add one hem-edge strip for each flare type. Correct for straight and A-line (straight lines and cones). Approximate for an anarkali: ask the atelier.
- **C. One UV frame anchored to the form.** U from the centre-front line, V from the neck point. Grain and prints continue across all band joins, for every silhouette.
- **D. Annotation reuse.** Shared bands and landmarks are drawn one time. No fit step. Scale measured one time. Work for each plate: ≈ 1–1.5 h → ≈ 20–40 min.

### Shoulder variations

Not in the current options. Split each sleeve at a fixed line on the arm (for example the bicep line):
- **Cap layer:** the shoulder variation (set-in, dropped, puff, cold-shoulder, raglan). One for each variation × 2 families.
- **Lower-sleeve layer:** the length and shape. Shared by all families (same arm on the form).

| With 4 shoulder variations | Without the split | With the split |
|---|---|---|
| Torso view, sleeves | 48 | 14 |
| Sleeve view | 48 | 14 |

Limit: the join must be below the lowest shoulder seam. A very full shape (big puff, bell from the shoulder) can need a complete sleeve.

### Counts

| | Not anchored | Anchored, current options | Anchored + 4 shoulder variations |
|---|---|---|---|
| Torso body | 19 | 15 (2 + 4 + 6 + 3 hem strips) | 15 |
| Torso necklines | 14 | 14 | 14 |
| Torso sleeves | 5 | 7 (2 caps + 5 lower) | 13 |
| Torso bottoms + dupatta | 8 | 8 | 8 |
| Neckline view | 14 | 14 | 14 |
| Sleeve view | 12 | 8 | 14 |
| Hem view | 12 | 11 | 11 |
| **Total (no back view)** | **≈ 84** | **≈ 77** | **≈ 89** (≈ 160 not anchored) |

For the current options, anchoring saves little. It keeps the total almost flat when options are added, and it halves the work for each plate.

### Costs and limits of anchoring

- **Light must match between photos.** Each join needs a feather band of 10–20 px. AI-generated photos cannot do this reliably: each one redraws the form and the light. In one test, the error was 8–60 px.
- **Real drape is not fully separable.** A heavy anarkali skirt changes small wrinkles above the waist. Small in a boutique viewer, but the atelier must look at it.
- **New engineering:** a compositor that joins bands, cuts lengths, and keeps the shared UV frame. `testing.html` handles one plate now.

## 6. Effort and storage

| Work | Unit cost | Total |
|---|---|---|
| Annotate and check one plate | 1–1.5 h (≈ 20–40 min anchored) | ≈ 85–130 h (≈ 30–50 h anchored) |
| Swatch preparation | ≈ 15 min each | 16 swatches ≈ 4 h |
| Photography (real rig) | — | 52–57 shots, ≈ 2–3 days with styling |
| Engineering | — | Layer compositor, registry / manifest |

Storage: ≈ 0.4 MB for each full plate, ≈ 35 MB in total. Layers can be cropped to their part. A client loads only the current view: ≈ 1–2 MB.

## 7. What makes the count larger or smaller

**Larger:**
- Layers that depend on each other (a dupatta over a lehenga skirt, a neckline that changes with the sleeve). Each such pair becomes a product again.
- Two borders at the same time.
- Shoulder variations without anchoring.

**Smaller:**
- **Limit the options for each house look.** The Salon has 9 house looks. With 3 necklines × 3 sleeves × 2 lengths each, a look needs ≈ 10–15 plates. Easier to photograph and to check one look at a time.
- Remove pairs that the atelier does not make (for example the angrakha wrap on a choli).
- **Start with 1 look × 4 views** (≈ 12–15 plates) to prove the layer compositor first.

## 8. Open problem: "worn with" on a form without legs

The view spec says the form has no head, arms or legs. A form without legs cannot wear churidar, palazzo, sharara or dhoti. Choose one:

- **(a)** A full-body form with legs, only for the bottom layers. Same torso and camera.
- **(b)** The bottom as a separate flat-lay or inset image.
- **(c)** In the torso view, only a short part of the bottom below the hem, painted or cut from a flat-lay.

Decide with the atelier before photography.

## 9. Decisions needed

1. The editable options for each house look.
2. Real photography on a fixed rig, or AI-generated images (alignment risk for layers).
3. Shoulder variations: yes or no, and which.
4. "Worn with": (a), (b) or (c).
5. Anarkali lengths as cuts: acceptable or not.
