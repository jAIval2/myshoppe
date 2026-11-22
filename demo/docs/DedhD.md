# Combination analysis: how many plates the boutique needs

Date: 2026-11-18. Status: analysis, for decisions with the atelier.
Source of the option counts: the Salon code (`C_GROUPS`, `C_FIELDS_BY_SILHOUETTE` in the Bespoke Studio — 2 demo).
Related: `render.md` (method), `upscale.md` (git history, `da48bfc`) (quality).

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
7. The direction after the current silhouette: options A–E in §11.7.

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

## 11. Review: tools, cost, the 2.5D proposal, the Amber model, and the direction

Date: 2026-11-21. Status: findings and options, no plan. Scope: the 4 fixed views. **No 3D, no pan, no zoom in the product.**

Agreed order: close the current silhouette (straight kurta) → perfect the swatches and laces on its 4 views → merge to `main` → more clothes.

### 11.1 Facts that change the reading of earlier sections

1. **All images are AI-generated:** the 4 base images, the swatches and the laces. They work well in the renderer. Consequences:
   - The neck-depth mismatch between the torso and the neckline views (25.2 mm against 40.9 mm, `halfway-results.md` (git history, `da48bfc`) step 6) does not come from the camera height. Two generated images disagree. Fix it by editing or regenerating one view to agree with the other. No re-shoot is needed.
   - The swatches have no measured scale. "1024 px per 30 cm" and each lace's `widthMm` are assumptions. A real swatch needs a flat scan with a ruler, and a colour card.
   - §5 still holds: AI images redraw the form and the light, so bands joined at fixed lines (§5 A) are risky with them.
2. **The fabric has no shared frame.** `make_plate.py` starts each zone's (u, v) at the zone's own grid corner (u along the top edge with the cylinder correction, v downward). So:
   - the same point of the garment has different fabric coordinates in each view: a motif is not at the same place in the torso view and the neckline view;
   - the print does not continue from the front onto the sleeve.

   §5 C (U from the centre-front line, V from the neck point) was proposed but not built.
3. **Every plate fails closure** (`numeric-results.md` (git history, `da48bfc`) step 11): the traced outlines sit 1–3 px inside the real edge. Together with the shoulders (numeric step 9), this is now the main defect in the demarcation.
4. **Branches.** `main` is `polish` step 8 (ba978fe). `halfway` and `numeric` are 20 commits ahead, and `main` is their ancestor, so the merge is a fast-forward. The `polish` checkout has an uncommitted copy of §10, which is already committed on `numeric`.

### 11.2 Off-the-shelf tools: none to drop in

| Kind | Examples | Fit |
|---|---|---|
| Swatch onto a garment photo | Hosted services (Photta, Segmind, Pixa). No open-source tool found. | The same idea as ours, but closed and paid for each render |
| 3D configurator in the browser | three.js demos (a texture swap on a UV-mapped model) | Needs a 3D garment; looks computer-made; against `render.md` §2 |
| AI try-on, texture transfer | CatVTON, IDM-VTON (non-commercial licence), FabricDiffusion | No control of lace repeats or motif placement; a GPU for each render |

Our method (photo + id, uv and shade maps, or their curves) is the standard 2D method. The compositor is not where the cost is. The plates are.

### 11.3 The 3D route (CLO3D or Blender) and its cost

Estimates of 2026-11-19, to check with quotes:

| Item | Estimate |
|---|---|
| Blender | Free |
| 7 base silhouettes, by an Indian CLO3D freelancer | ₹5–15k each → ₹35k–1.05 L |
| ≈ 30 part variants (necklines, sleeves, lengths, bottoms, dupattas, backs) | ₹1–3k each → ₹30–90k |
| CLO3D licence (only to edit the garments ourselves) | ≈ $50 a month; Marvelous Designer $280 a year |
| **Total** | **≈ ₹70k–2.1 L, one time** |

- Ready-made Indian garments in 3D: almost none on the marketplaces (one men's kurta found). Custom work from the master's paper patterns (DXF into CLO3D) gives the boutique's own cut.
- Use: offline only, to render base, id, uv and shade for each view (exact to the pixel, no annotation). Never in the browser.
- Not needed while the AI images work.

### 11.4 The "2.5D parametric garment" proposal (external, 2026-11-21)

Most of it exists already:

| Proposal | In the repo |
|---|---|
| Measurements in mm, one design record → 4 views | `halfway` (the Amber model, `state.neck`, `mmPerPx` for each view) |
| Parametric neckline | `halfway` steps 2–6 |
| Anchors | Landmarks, for the neckline only |
| Fabric frame (repeat in mm, grain) | Partly: `uvRangeCm`, zone sizes in cm, `thetaDeg`, the grain checker. No shared origin (§11.1, item 2). |
| Z relief separate from the layer order | `polish` steps 6–7 (relief, metal and pearl masks, displacement in folds, sheen); `order` in the `.dat` |
| Extend the `.dat` | `numeric` step 6 holds zones, trims, order and curves. The proposed `garment/` folder is not needed. |

The new parts, with an estimate of how likely each is to work:

| Item | Likely | Why |
|---|---|---|
| Shorter hem, slit length | High | The neckline method: move a curve, the trims follow, fill the revealed area |
| Longer hem (≤ 50 mm) | Medium | The fabric extends, but the image has no folds or shade there |
| Sleeve length | Medium | The form has no arms: in a ¾ view the revealed area is background |
| The same motif place in all views | Medium | Needs the shared frame (§11.1, item 2) and views that agree (§11.1, item 1) |
| Local deformation (bust, shoulder, flare, waist) | Low to medium | The folds and the light are in the image: small changes only. Large changes need new images. |

### 11.5 The Amber model, read again

The analogy of `halfway.md` (git history, `da48bfc`) §1 holds beyond the neckline. Amber splits its files: the parameters for each atom type (`parm10.dat`, with overrides in `frcmod`), the topology (`prmtop`), and the coordinates (`inpcrd`). The same split fits here.

| Amber | Here | Now |
|---|---|---|
| Atom types, `parm*.dat` | Material classes. Fabric: repeat in mm, direction, sheen, print type. Lace: period, edging or insertion, metal, pearl. | Partly (`lace-*.json`) |
| `frcmod` (overrides) | A swatch's own values over its class | No |
| Residues with head and tail atoms (LEaP libraries) | Parts (neckline, sleeve, hem band) with connection anchors | Counted in §5, not built |
| Topology (bonds) | Zones, seams, trims, draw order | Yes, but the seams are not listed |
| Cartesian coordinates | Curves in plate px, one set for each view | Yes |
| Internal coordinates (Z-matrix) | Design parameters in mm | The neckline only |
| Flat-bottom restraints (r1 < r2 ≤ r3 < r4: free from r2 to r3, harmonic outside, then linear) | Ranges with a soft wall | Hard stops now |
| Constraints (SHAKE: fixed bond lengths) | A fixed lace width; whole repeats on each trim | Yes (`polish` step 4) |
| Periodic boundary conditions, minimum image | The fabric repeat is the unit cell; the cell's offset sets where the motif sits | The repeat yes, the offset no |
| Energy minimisation | Fit an outline to the edge (data + smoothness terms); deform the mesh "as rigid as possible" | `snap_outline.py` (a robust cubic) |
| Trajectory (`mdcrd`) | A series of design states: transitions, undo, the journey record | No |
| 3D force field (bonds = stretch, angles = shear, dihedrals = bending, non-bonded = collision) | Cloth simulation (mass-spring, XPBD) | Rejected for the product (§10.7); offline only |

**The three coordinates, here:**
- **x, y:** the plate px of each view (one set for each view).
- **u, v:** the fabric in cm, one frame for the whole garment (to build: §11.1, item 2).
- **z:** two separate things. **Relief** is continuous (shade, folds, the height of lace, zari and pearls). **Layer** is discrete (draw order). A normal for each pixel can come offline from the AI base, with a monocular normal estimator (StableNormal, Marigold, DSINE). The "Textureshop" method uses such normals to compress the print where the surface turns away.

### 11.6 The process so far

What works:
- One step = one commit, test switches, reference ports, measured gates, results written with their failures.
- `plate_invariants.py` (`numeric` step 11): a new plate must pass it or say why.

What costs us:
- **Unverified checks pile up.** Not done on a real device or by a person: draw time ≤ 5 ms; build time (1.4–3.1 s in software rendering); drag ≥ 30 frames per second; the 10-second tests; lace relief at 2×; anti-tiling at 2×; a person on a phone.
- **Identity gates keep old defects.** "Pixel-identical to the previous port" protected the refactors, but the outlines inside the real edge and the trim order that cut the hem lace short were found only by eye, and late (`numeric` steps 9–10).
- **Each plate is made by hand, view by view.** 4 annotations and their fixes for each silhouette is the bottleneck for more clothes.
- **Three worktrees, three copies of the docs.**

### 11.7 Options from here

| Option | Covers | Effort | Risk |
|---|---|---|---|
| **A. Close the demarcation** | Silhouette | Small to medium | **Done** (2026-11-22): `plan/StepA.md`, results `plan/StepA-results.md` |
| **B. One fabric frame** | Swatches | Medium | Medium (depends on A) |
| **C. Lace as parts** | Laces | Medium | Low to medium |
| **D. Interactions on the design record** | Interactions | Medium | Low; needs a real phone |
| **E. Catalogue factory** | More clothes | Large | Medium; pays back from the 2nd silhouette |

**A. Close the demarcation** — **done** 2026-11-22 (open items in `plan/StepA-results.md` step 9). Plan: `plan/StepA.md` (it also replaces the Coons patch with a fabric frame, and measures the torso again).
- Snap every free edge of every outline, with the seams excluded. This needs an explicit seam list. Target: the 4 plates pass closure.
- The open items of `numeric` step 11: the neck plate's 249 px of thin gaps; the torso's slit landmarks and body side; the sleeve's `cuff-l` offset; the hem's 43 px piece; the speck at the right neck corner.
- Make the two front views agree: edit the torso or neckline image so that the neckline depth agrees within ±3 mm, then re-annotate.
- Option: soft edges (alpha) from a matting model (SAM 2 with ZIM or SAM2Matting) in place of hard outlines.

**B. One fabric frame for the garment**
- (u, v) from the centre front and the neck point (§5 C), the same in all 4 views. Front, sleeve and back pieces keep their own grain but join at the seams.
- Placement: the motif offset is a design value (a buta on the centre front, a border at the hem): the minimum-image rule.
- Swatch classes: all-over, border (daaman), buta, one-way print, irregular (bandhani, ikat); sheen (cotton, silk, velvet); metal (zari); relief (chikankari).
- Scale: a swatch sidecar with mm per px from a ruler scan; colour from a card.
- Optional: normals from the base image, to compress the print where the surface turns away.

**C. Lace as parts**
- Corner and end pieces, as in a pattern brush (side, outer corner, inner corner, start, end tiles): V and square necklines, slit tops, the hem-to-slit join (a butt join now).
- A join type for each seam: butt, mitre, overlap.
- A repeat rule while dragging: keep the motif count inside a small scale band (as SHAKE keeps a length), change the count only past a threshold (hysteresis), so that motifs do not jump.
- Indian trim classes: gota patti, zari border, pearl, mirror work, tassel edging (latkan).

**D. Interactions on the design record**
- Flat-bottom ranges: free inside, resistance near the limit, then the stop. Detents at the look's `stops`.
- Coupled rules (lace narrower than the neck depth) shown as feedback, not as a refusal.
- Handles for hem rise and slit length (§11.4).
- Drag the print: the customer sets where the motif sits (needs B).
- Trajectory: smooth transitions between presets, undo, and the design record as an order sheet in mm for the atelier.

**E. Catalogue factory**
- Generate the 4 views of a new silhouette from one reference image with a shared layout, so that the landmarks agree.
- Outlines from SAM 2 (Apache 2.0) as the first trace. Landmarks named in the DeepFashion2 style (x, y, visibility). Then the `annotate-plate` checks, with `plate_invariants.py` as the gate.
- Parts and anchors (§5), so that silhouettes share necklines and sleeves.

**For all options:** the device and person checks of §11.6; one branch after the merge.

### 11.8 Sources

- Amber file formats: https://ambermd.org/FileFormats.php; LEaP: https://ambermd.org/tutorials/pengfei/index.php; restraints r1–r4: https://structbio.vanderbilt.edu/archives/amber-archive/2003/1917.php
- Textureshop (Fang and Hart, 2004): https://history.siggraph.org/?p=116167; retexturing with folds (White and Forsyth, 2005): https://www2.eecs.berkeley.edu/Pubs/TechRpts/2005/EECS-2005-4.html
- Normals from one image: StableNormal https://arxiv.org/abs/2406.16864, Marigold https://arxiv.org/abs/2505.09358
- Intrinsic decomposition (Careaga and Aksoy, academic licence): https://github.com/compphoto/Intrinsic
- As-rigid-as-possible deformation (Igarashi et al., 2005): https://www-ui.is.s.u-tokyo.ac.jp/~takeo/research/rigid
- Pattern brush tiles: https://www.adobe.com/learn/illustrator/web/illustrator-create-pattern-brush
- Matching prints at seams: https://www.seamwork.com/articles/how-to-match-plaids-stripes-and-large-patterns
- DeepFashion2 landmarks: https://github.com/switchablenorms/DeepFashion2; SAM 2 matting: https://arxiv.org/abs/2606.27339
- Browser cloth (XPBD, WebGPU): https://github.com/jspdown/cloth
- Try-on model licences: https://fashn.ai/blog/comparing-the-top-4-open-source-virtual-try-on-viton-models
- CLO3D and Marvelous Designer prices: https://www.xp-pen.com/blog/clothing-design-software.html, https://www.cgchannel.com/?p=178281
- CLO3D freelance budgets in India: https://www.freelancer.com.bd/projects/fashion-design/clo-designer-for-outfit-collection
