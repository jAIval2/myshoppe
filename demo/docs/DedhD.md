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
6. Numeric plates (§10): build the mesh from the curves, beside the current renderer, before polish step 5 (edging lace) starts.

## 10. Numeric plates: curves in place of coordinate images

Date: 2026-11-19. Status: analysis, not started. Scope: the 4 fixed views only. **No 3D.**

### 10.1 Idea

Each view has parts that never change when the customer changes the fabric or the lace: its outlines, seams, zone grids, trim lines and folds. Today they are shipped as images. They are all **calculated** from two inputs, so the page can calculate them itself:

| Image now | Calculated from | Numeric replacement |
|---|---|---|
| `uv.png` (fabric coordinates, cm) | Coons patch of the zone curves in `zones.json` | Zone grid evaluated in JavaScript, drawn as triangles with (x, y) and (u, v) on each point |
| `uv_trim.png` (lace coordinates) | Trim centre lines + widths | Ribbon of triangles along each line: u = cm along, v = 0–1 across |
| `id.png` (zone, trim) | Zone outlines | The outlines themselves (stencil); draw order for layers |
| `shade.png` (folds) | The base photo: luminance ÷ median | Calculated on the GPU from `base.jpg`, once per view |

Each view then ships **`base.jpg` + its curves** (a few KB). Fabrics and laces stay the shared swatches.

### 10.2 Coordinate frames

- **Screen frame:** 2D Cartesian, 1200 × 1600 plate px, origin top left, x right, y down. All curves are in this frame (as now).
- **Fabric frame:** u, v in **centimetres** along the cloth (as now).
- **The map:** the Coons patch takes a grid point (s, t) ∈ [0, 1]² to both (x, y) and (u, v).
- The page needs screen → fabric. Do **not** invert the patch per pixel in the shader (slow, fragile). Evaluate the patch at a grid every 6–8 px in JavaScript and let the GPU's triangle interpolation do the screen → fabric lookup.

### 10.3 Measured savings (the 4 plates of 2026-11-19)

| View | Maps now (id + uv + uv_trim + shade) | Curves (`zones.json`, gzip) |
|---|---|---|
| Torso | 436 KB | 18 KB (dense trace; ≈ 3 KB after thinning) |
| Neckline | 381 KB | 1 KB |
| Sleeve | 725 KB | 3 KB |
| Hem | 480 KB | 3 KB |
| **All 4 views** | **2.0 MB** | **≈ 25 KB (−99 %)** |

| Cost per view | Now | Numeric |
|---|---|---|
| Download | photo + maps (≈ 0.7–1.1 MB) | photo only (≈ 0.3–0.45 MB) |
| GPU memory | ≈ 41 MB (photo with mipmaps + 4 RGBA8 data textures of 7.68 MB) | ≈ 10 MB photo + < 1 MB vertices |
| Data reads per pixel | ≈ 20 texels (zone checks, 4-texel smoothing, neighbour gradients) | none for coordinates; only fabric, lace, photo |

### 10.4 What improves besides size

| Now | Numeric |
|---|---|
| Stair-stepped garment edge (binary 1200 px mask) | Triangle edges with antialiasing |
| 12-bit UV | Floating-point UV |
| Zone-edge workarounds in the shader (`gradFabric`, `gradTrim`) | Not needed: each zone drawn alone, so the GPU's own gradients are correct |
| Edging lace past the edge needs a plate rebuild | Wider ribbon, no rebuild |
| A curve change needs new PNG maps | Change `zones.json` and reload |

### 10.5 Risks and controls

1. **Cut-outs** (neck dip, gaps under the arms, mannequin-arm notch): draw each outline into the stencil buffer, then the zone grid where the stencil allows.
2. **Two copies of the maths** (Python `make_plate.py`, JavaScript page): keep `make_plate.py` as the reference. Test: render the JavaScript mesh UV into an image and compare with `uv.png`, `uv_trim.png`, `id.png` on all 4 plates. **Pass: ≤ 0.5 px, ≤ 0.1 mm of fabric.**
3. **Plate rules move to JavaScript:** `tuck`, `thetaDeg`, `widthPx` (≈ 150 lines with Coons and resampling).
4. **Shade from the photo** must match `shade.png`: pass ≤ 1 level of 255. The weave removal (polish step 3) runs once per view on the GPU.
5. **Click hit-testing** becomes point-in-polygon on the outlines.
6. **Polish plan:** steps 2–4 carry over; step 5 (edging) becomes simpler. Decide before step 5.

### 10.6 Memory problem found on the way (independent of §10)

`testing.html` keeps the **decoded** images of all 4 views (`fetchView` cache) and preloads all of them: 4 views × 5 images × 7.68 MB ≈ **150 MB** of CPU memory, besides the GPU copies. Risk of a tab crash on phones. Fix without §10: keep the compressed files, decode only the current view (or at most 2). With §10 the problem mostly goes away (one photo per view).

Also: RGB8 does not save memory on most GPUs (stored as RGBA). R8 (shade) and RG8 (id) do.

### 10.7 What was considered and rejected

A 3D garment model with cloth physics (XPBD) rendered from 4 cameras ("PGF v2"). Rejected:
- Our 4 base images are separate photographs, not 4 cameras on one scene: no single 3D state matches all of them.
- Computed light replaces the photo's light: the cloth looks CG, and photo realism is the product.
- The brief is fixed views, no motion.
- It rebuilds CLO3D, which was already judged too large.

Kept from it: separate textile coordinates (u, v in cm) from screen position, and the split into surface / parameter / topology changes (the same as `render.md` §5).

### 10.8 Order

1. Mesh from curves beside the current renderer (`?geom=mesh`), torso first; compare with the maps (≤ 0.5 px), no seam gaps.
2. Shade from the photo; compare with `shade.png`.
3. Port neckline, sleeve, hem; same comparisons.
4. Stop shipping the 4 maps. Keep `make_plate.py` as the offline reference and the test.
