# StepB results

Plan: `StepB.md`. Branch `stepB` from `main` (`fbd2446`). Reference: worktree `../myshoppe-ref` at `fbd2446`, port 8200; this branch on 8300.

## Decisions taken at the go-ahead (2026-11-23)

The owner gave the go-ahead ("execute stepB") without answering §7 of the plan. The plan's proposals are used; each can be changed.

| §7 | Taken | Effect if changed later |
|---|---|---|
| 1. Tolerance; the photos' disagreement | **3 mm.** A landmark over the limit is **reported, not accepted**: only the owner adds to `acceptedResiduals` | none: a list in the plates |
| 2. Scale | **The agreed distance per view stays** (`mmPerPx` unchanged); the scale that fits the garment's landmarks best is **reported** for information | a fitted scale rebuilds every plate and moves the live neckline's mm |
| 3. Fabric per piece | data only (`print` per piece in the design record); one fabric texture in the shader | — |
| 4. Branch and push | `stepB`, one commit per step, merged at the close; **no push** | — |

Machine: Linux. Pillow 12.3.0, Node 22.11.0 and Chrome for Testing 131 (with `--no-sandbox`) were installed outside the repository for the tools. On this machine `rebuild_check.sh` gives **ALL IDENTICAL** for the 4 plates of `fbd2446`, and `page-check neck` gives the StepA numbers (uv max 0.00125 cm, rim 0.00 %, halo 95 % 4.2 %). So the gates mean here what they meant on the first machine.

## Step 0: baseline, the cross-view check, the registration fabric

**Done:**
- `silhouette/checks/xview_check.py`: each view's landmarks named as garment points (`VIEW_NAMES`), with the pieces each is a point of. They are compared in each view's fabric frame:
  - `uv`: cloth points (seam junctions, neck points, slit corners);
  - `v` only: points on a weft line (hem, cuff). The u of a silhouette point is a property of the view, not of the cloth.
  - "visible" adds the packing offset and wraps by the repeat, as the page samples the print.
- `silhouette/checks/xview_sheet.py`: 10 cm crops of each shared landmark in each view, rendered with the registration print.
- The registration print `assets/swatches/fabric-reg-1024.png` (`swatchprep/test_prints.py reg`; `prep.py test-print reg`):
  - a 30 cm tile with labelled 10 cm cells (A–C along u, 1–3 along v), lines every 1 and 5 cm, and a red crosshair at the tile origin;
  - `?fabric=reg` (`FABRICS.reg`, `test: true`); not in the picker (the picker's buttons are static).
- Housekeeping: `StepA-results.md` step 8 marked passed. `breather.md`: the branch, the machine notes, and the §7–§11 that its §13 referred to.

**Deviation:** `xview_check.py --page` (read the page's uv map) was not built. `maps_check.py` already proves the page's uv equals the build's within one 16-bit step, offset included (`page-check`). The page's phase is therefore computed from the plate: (u, v) + `uvOffsetCm`, modulo the repeat.

### Cross-view baseline (`xview_check.py`, the plates of `fbd2446`)

Spread over the views, mm. "Visible" is what the print shows at that point on a 30 cm repeat (u, v).

| Landmark | Piece | Views | Δu | Δv | Visible 30 cm (u, v) | Cause class |
|---|---|---|---|---|---|---|
| cf-neck | front | torso, neck | 0.0 | 7.1 | **110.0**, 2.9 | **F1** (offset); v: image (the known 7 mm) |
| neck-l | front | torso, neck, sleeve | 29.3 | 22.0 | 121.1, 18.0 | torso = neck (0 / 0); sleeve view: **model** (no yaw, F3) |
| neck-r | front | torso, neck, sleeve | 39.7 | 10.0 | 110.3, 50.0 | torso – neck 2 mm; sleeve view: **model** (F3) |
| shoulder-l | front | torso, neck, sleeve | 28.0 | 39.5 | 177.1, 8.9 | torso – neck 1 / 1 mm; sleeve view: **model** (F3) |
| shoulder-r | front | torso, neck | 5.5 | 1.5 | 104.5, 8.5 | image (5 mm) + F1 |
| underarm-l | front | torso, neck, sleeve | 20.7 | 56.5 | 170.7, 96.5 | **definition** (below) |
| underarm-r | front | torso, neck | 14.2 | 20.6 | 95.8, 10.6 | **definition** |
| shoulder-l | sleeve-l | torso, neck, sleeve | 105.1 | 0.0 | 106.1, 40.0 | **F2**: each view's sleeve axis is its own visible midline (u = 0 on a different line of the sleeve) |
| underarm-l | sleeve-l | torso, neck, sleeve | 96.1 | 79.2 | 171.8, 119.2 | F2 + definition |
| shoulder-r | sleeve-r | torso, neck | 1.2 | 0.0 | 108.8, 10.0 | **PASS** on the cloth; visible: F1 |
| underarm-r | sleeve-r | torso, neck | 27.0 | 18.3 | 83.0, 8.3 | definition |
| cuff-l line | sleeve-l | torso, sleeve | — | 91.5 | —, 61.5 | **image / scale**: sleeve length 54.2–54.6 cm in the torso view, 45.5–47.8 cm in the sleeve view (its 470 mm is the agreed value) |
| cuff-r line | sleeve-r | torso | — | 4.7 | — | the cuff is not one weft line in the torso frame (4.7 mm) |
| slit-top-r | front | torso, hem | 132.1 | 60.6 | 72.1, 100.6 | **F2** (the hem view's front axis is its own midline, v anchored at an assumed 91.1 cm) + **image**: the slit is 15.9 cm in the torso view and 23.9 cm (the agreed 240 mm) in the hem view |
| hem-slit-r | front | torso, hem | 155.8 | 140.6 | 95.8, 119.4 | F2 + image (as above) |
| hem-front line | front | torso, hem | — | 147.7 | —, 160.1 | F2 (hem view 115 cm, torso 101–105 cm); within the torso, the slit corners are 4 cm above the centre-front hem (**model**: the hem is not one weft line in the torso frame) |
| hem-back line | back | hem | — | 11.9 | — | within the hem view (back panels) |

1 PASS, 18 FAIL (limit 3 mm). Full table: `xview_check.py` (JSON in `demo/review/stepB/xview-step0.json`, not committed).

**The definition cases.**
- **underarm:** in each view the landmark is the visible junction of the sleeve's inner edge and the body's side, a silhouette point. The seam's real underarm point is hidden under the arm.
  - The neck view puts `underarm-l` 12.7 cm above `underarm-r` (937 vs 1064 px), and the torso view 2.6 cm apart.
  - The garment record (step 2) must name a true cloth point, or mark the underarm as v-only / not compared.
- **The hem corners at the slits** are where the hem turns into the slit facing. In the torso view they sit 4 cm above the centre-front hem. Either the photographed hem curves up at the slits (a garment fact for the record), or the torso frame's sag (fitted on the hem's middle 80 %) does not reach the corners (model).

**What this says for the next steps:**
- **F1 is the largest visible cause.** At `cf-neck` the cloth agrees to 0.0 mm in u and the print is 110 mm apart (A1 against C1 on the sheet). Step 1 removes it.
- **F2** (the hem view and the sleeves anchored on their own axes): step 3's fit, a u and v shift per zone from the garment's landmarks.
- **F3** (the sleeve view's turn): step 4.
- **Image and scale disagreements stay** after the fit, unless the owner chooses otherwise (decision 1): the slit length (8 cm), the sleeve length (7–9 cm), the neck depth (7 mm) and shoulder-r (5 mm).

**Registration sheet** (the views as they are, `?fabric=reg`): [`img/stepB-xview-step0.jpg`](img/stepB-xview-step0.jpg). Each row is a landmark and each column a view; the magenta cross is the landmark. The same cloth point shows different cells: cf-neck A1 / C1, neck-l C1 / B1 / C1, neck-r B1 / A1.

**Accept:**
- [x] The baseline table lists every shared landmark with Δu, Δv in mm and a cause class for each one over 3 mm.
- [x] The registration sheet shows F1.
- [x] `breather.md` is current (branch, paths, §7–§11).

## Step 1: the print's phase from the garment, not from the packing (F1, F8)

**Done:**
- **One packing for every plate:** `plate.dat` `uvPack` = `{rangeCm: 256, offsetCm: [128, 32]}` (`make_plate.py` `UV_PACK`). u runs from −128 to 128 cm and v from −32 to 224 cm, 16 bits (one step is 0.0039 cm). The build raises if a frame's (u, v) leaves that range.
- **`decisions.uvOffsetCm` is gone** (torso [36, 2], neck [25, 1], sleeve [40, 5], hem [12, −84]), and so is the hem view's `uvRangeCm` 40 (`views/hem.py`), which only the Python build read.
- **`maps.js`:** the frame pass packs with the plate's `uvPack`; the trim fields keep their own 128 cm (`TRIM_RANGE_CM`, until StepC). Without `uvPack` the page stops with a message (an old `plate.dat`).
- **The page:** `decodeF` = stored × range − offset, the true garment cm, used for the fabric, its gradients and the grain checker. The trim fields keep `decode`.
- **Test switch `?phase=view`:** the old per-view offsets (`PHASE_VIEW`), added back. Removed in step 7.
- `maps_check.py` reads the plate's `uvPack`. `platedat.py` and `plate.js` carry it.
- New: `silhouette/checks/ba_sheet.py` (before / after of two `cdp_shot` runs, with the mean difference).

**Measured:**

| Check | Result |
|---|---|
| `plate.dat` change (`--dump`, against step 0) | only `decisions.uvOffsetCm` removed, `uvPack` added (and the hem's `uvRangeCm`). Sizes 8,576 / 5,434 / 6,772 / 8,488 B (≤ 40 KB) |
| `rebuild-check` | ALL IDENTICAL |
| `check` (invariants, frame parity) | frame rules PASS on all zones; parity ≤ 2.8 × 10⁻¹⁴ cm. Closure FAILs = StepA's (torso 6 px, sleeve 0.0596 %, hem 10 px), unchanged |
| `page-check` uv (page against build) | max 0.00263 / 0.00220 / 0.00316 / 0.00211 cm (torso, neck, sleeve, hem); limit 0.01, one step 0.0039 ✔ |
| `page-check` coverage | torso: the 1 px at (821, 916) of StepA (open); others PASS |
| Rim / halo (mocha), against the reference on 8200 | equal on neck, sleeve, hem; torso rim 0.35 % vs 0.30 % (2 px: another part of the print at the edge) |
| `?phase=view` against the reference (8 renders) | mean difference 0.05–0.90 levels, ≤ 0.24 % of pixels over 8 levels (the finer 16-bit step): **the print only moved by the old offset** |
| After against before (8 renders: 4 views × mocha, mustard) | mean 1.9–20.2 levels: the print moved, as intended |
| Phase at the centre-front neck, torso against neck | 0.0 mm in u (was 110 mm visible on a 30 cm repeat); v 7.1 mm (the photos, open) |

`xview_check.py`: "visible" now equals the cloth's own difference on every row (no offset left). The torso and neck views agree on every shared front landmark except the known ones:
- cf-neck: Δv 7.1 mm;
- shoulder-r: Δu 5.5 mm;
- the underarms: definition (step 0).

**Registration sheet after step 1:** [`img/stepB-xview-step1.jpg`](img/stepB-xview-step1.jpg). The torso and neck columns show the same cell at every landmark (cf-neck on the C1 | A1 line, neck-l C1, neck-r A1, shoulder-l and shoulder-r B1). The sleeve and hem columns still differ (F2 and F3: steps 3 and 4).

**Before and after** (mocha, mustard, the 4 views): [`img/stepB-step1-before-after.jpg`](img/stepB-step1-before-after.jpg).

**Accept:**
- [x] The frame invariants and the parity hold; the page's maps match the build within one 16-bit step on all 4 views.
- [x] Phase table: the same tile phase at the centre-front neck in the torso and neck views (0.0 mm in u; v differs by the photos' 7.1 mm, an open item from StepA).
- [ ] **A person approves** the before / after sheet and the registration sheet (open: the owner).
- [x] `plate.dat` ≤ 40 KB.

## Step 2: the garment record and `plate.dat` version 3 (F2, F6), with the lace band and the join per trim

**Done:**
- **The garment record:** the block `garment` in `assets/looks/straight-kurta.json`; read by `silhouette/pipeline/garment.py` (`--check`, `--dump`).
  - **Pieces:** front, back, sleeve-l, sleeve-r, each with its grain, origin and u direction.
  - **13 landmarks in piece cm, each with its source:**
    - agreed: cf-neck depth 39.7 mm; the slit tops from the agreed 240 mm slit;
    - fitted, with their spread: neck points and shoulders from the torso and neck views;
    - measured: the hem points (torso);
    - assumed: the back's hem corner = the front's;
    - definition: the sleeve origins;
    - not compared: the underarms (silhouette points, step 0).
  - **2 lines:** the cuffs at v = 47.0 cm, agreed.
  - **Each view's zones → pieces and landmark names.** A landmark is a garment point, a point of a line, or `null` (not a garment point: an image border, the elbow).
  - Version 1, hash `cad2270f6b4dfa81`.
- **`BSP3`** (`platedat.py`, `plate.js`; only version 3 is read):
  - the `garment` header {look, version, hash};
  - each zone's `piece`;
  - **ids assigned by the build** (draw order, then name, from 1; at most 15 each);
  - each trim's `group` (the page's button), `field` (main | slit), `live` (on the cut edge: laid by the page on the live neckline), **`bandInMm` / `bandOutMm`** (default 56 / 8 mm from `trimfield.DEFAULT_BAND_MM`, overridable by the view's `settings.laceBandMm` or per trim) and **`join` {kind, with}** (the text joins of the torso and hem views became `{mitre, [slit-l, slit-r]}`, `{mitre, [slit-l]}`, `{mitre, [slit-r]}`; the rest `{open, []}`).
  - The validator checks all of them.
- **No id tables in code:** `ZONE_ID` and `TRIM_ID` (`make_plate.py`), `ZONE_ID` (`maps.js`), `TRIMS` and `GROUP` (`testing.html`) are gone.
  - The page reads them per view (`setTables`).
  - The shader's numbers became uniforms: the live neck trim and its zone (`uNeckTrim`, `uNeckZone`; were trim 1 and zone 1), the slits' two field slots (`uSlitA`, `uSlitB`; were 5 and 6), and the checker's colour per zone (`uZoneTint`, by piece; were zone ids 1, 4, 5).
  - Arrays sized 16.
  - The neck area's reach uses the live trim's `bandInMm` (was 56 in code).
- **The build refuses:**
  - a landmark the record does not name;
  - a zone without a piece;
  - a trim without a group, or with a bad join;
  - more than 15 zones or trims.
- `xview_check.py` and `xview_sheet.py` read the names from the record (their own table is gone). `xview_check.py` shows each view's residual against the record (column "record").
- Docs: `plate.md` (§1 table, §4 limits), `render.md`, `silhouette/README.md` (new tools), `breather.md`.

**Measured:**

| Check | Result |
|---|---|
| `plate.dat` against step 1 (`--dump`; the old file read with `fbd2446`'s reader) | Added: the garment header, pieces, groups, fields, live, bands, joins. Ids renumbered: torso trims cuff-l 1, cuff-r 2, hem 3, neck 4, slit-l 5, slit-r 6 (neck was 1); hem zones back 1, back-l 2, front 3 (front was 1). **No edge, frame or decision number changed**; `base.jpg` identical |
| Sizes | 9,342 / 5,668 / 7,098 / 9,110 B (≤ 40 KB) |
| `platedat.py --check`, `garment.py --check` | PASS (4 plates, the record) |
| **Render against step 1** (port 8201, 14 queries: 4 views × mocha + pearl, sage + geometric and the grain checker, all trims with the slits; the live neckline at 100 / 194 and 20 / 132 mm) | **pixel-identical** (mean difference 0.000 on every query); no console error |
| `page-check` (4 views) | as step 1: uv max 0.0021–0.0032 cm; trim fields s 0.0010 cm, t 0.0098 mm; torso coverage 1 px (StepA's) |
| `check` | frame rules PASS, parity ≤ 2.8 × 10⁻¹⁴ cm; closure FAILs = StepA's |
| `rebuild-check` | ALL IDENTICAL. With one garment value changed (hem-cf v 105.01 → 105.5): `DIFF neck-straight/plate.dat` (the hash) until rebuilt ✔ |
| An unnamed landmark (the sleeve view's `elbow` removed from the record) | the build stops: `sleeve: landmark elbow is not named in the garment record (views.sleeve.landmarks)` ✔ |
| `grep` for id tables in `make_plate.py`, `maps.js`, `testing.html` | none (`maps.js` builds its map from the plate) |

**Still name-based, until StepC:** the slits' field packing (`plate.js` / `trimfield.py` `SLIT_OFF_CM`: `slit-l` → s + 32, `slit-r` → s + 96). The page maps them to slots from the plate's `field` and the name.

**Accept:**
- [x] No zone or trim id table in `make_plate.py`, `maps.js` or `testing.html`.
- [x] The render is unchanged by this step (pixel-identical against step 1).
- [x] `rebuild_check.sh` passes; editing one garment value makes it fail until the plates are rebuilt.
- [x] `--dump` shows every garment value with its source (`garment.py --dump`).

## Step 3: frames fitted to the garment (F2, F4, F5)

**Done:**
- **`silhouette/pipeline/garmentfit.py`.** For each zone it decides which offsets are free, then fits them.
  - **u is fixed** when the zone's axis starts at a landmark whose garment u is 0 (the torso's and neck view's fronts: their axis runs through cf-neck).
  - **v is fixed** when the anchor is the piece's own v origin (the neck-point line; a sleeve's shoulder point).
  - Everything else is **free**: u as a new frame shift `uMm`, v through `vMm`.
  - **The fit:** weighted least squares over the zone's landmarks in the record. Weights: agreed and definition 4, fitted and measured 2, assumed 1.
  - **A zone with no landmark** is tied along a shared seam to a fitted zone: the same piece is continuous across a fold; two pieces get v equal (sewn) and u equal (assumed).
- **`uMm` in the frame maths, all three copies:** `plateframe.py`, `plate.js` `frameUV`, `maps.js` `FRAME_FS` (uniform `uUShiftMm`). The build writes `fit` into `plate.dat`: per zone the free offsets, how they were fitted, and each landmark's residual in mm; per view the scale that would fit best, for information.
- **The gate:** `plate_invariants.py` "garment fit". Each landmark within 3 mm, or listed by the owner in the record (`garment.views.<view>.acceptedResiduals`; empty: nothing accepted).
- **Record change:** the hem view's `back-l` is now a zone of the **front**, not the back. In that view the front runs from about u = +6 cm to the slit at +22 cm. A straight kurta has no seam near +6 cm, and no back panel can show on that side. So the shaded panel is read as the front turning away past a fold, and the print continues across it. **Open: the owner to confirm** (note in the record). Record hash `5f2de45e7f80c240`.

**The fit, per zone:**

| View | Zone | Free | uMm | vMm (was) | By |
|---|---|---|---|---|---|
| torso | front | – | 0 | 0 | fixed by definition |
| torso | sleeve-l / sleeve-r | u | −2.6 / +2.7 | 0 | shoulder point → u = 0 |
| neck | front | – | 0 | 0 | fixed |
| neck | sleeve-l / sleeve-r | u | −6.5 / +1.6 | 0 | shoulder point |
| sleeve | front | u | +13.5 | 0 | neck points, shoulder (turned view: step 4) |
| sleeve | sleeve-l | u | +98.6 | 0 | the shoulder point (the view sees the sleeve's outer side: its midline is about 10 cm of cloth from the torso view's) |
| hem | front | u, v | +140.0 | 769.7 (911) | slit-top, hem corner |
| hem | back | u, v | +251.3 | 771.8 (911) | the back's hem corner (assumed = the front's) |
| hem | back-l | u, v | +23.0 | 772.9 (911) | tied to the front across the left fold (spread along it 8.6 mm) |

**Residuals against the record** (`plate_invariants.py`, garment fit; FAIL = over 3 mm and not accepted):

| View | PASS | FAIL (mm) | Class (step 0) |
|---|---|---|---|
| neck | all 7 | – | – |
| torso | neck points, shoulders, hem corners, hem-cf, shoulder → sleeve | cf-neck dv −7.1; slit tops dv +145 / +81; cuffs dv +72 … +78 | image: the neck depth (7 mm), the slit length (torso 9.5 / 15.9 cm against the agreed 24 cm), the sleeve length (torso 54.4 cm against the agreed 47 cm) |
| sleeve | shoulder → sleeve | front: neck-l (−15.6, −21.8), neck-r (−25.5, +9.8), shoulder (+41.0, −39.0); cuffs dv −15 / +8 | model: the turned front (step 4); the cuff line is slanted in this view |
| hem | back's hem corner | front: slit-top du +7.9; hem corner du −15.8 | the slit edge leans 2.4 cm more in the hem view than in the torso; model (a turned view: step 4) or image |

**Cross-view** (`xview_check.py`), against step 1:
- hem-slit-r: Δv **0.7 mm** (was 140.6); Δu 15.8 mm (was 155.8);
- slit-top-r: Δu 7.9 mm (was 132.1); Δv 80.8 mm (the slit length: image);
- shoulder-l and shoulder-r on the sleeves: **0.0 / 0.0** (were 105 / 1.2 mm);
- the sleeve view's front: still off (step 4).

**Scale, for information** (the agreed scale stays, decision 2). The scale that fits the view's landmark distances:
- torso 0.8466 mm/px (0.965 ×, 45 pairs);
- neck 0.3030 (0.995 ×);
- sleeve 0.4241 (1.254 ×, but only 3 pairs and the turned front);
- hem 0.2233 (1.005 ×, 1 pair).

The torso and neck views agree with each other on the neck points and shoulders within 1–3 mm. The large disagreements are between photos: the torso's slits and sleeves against the hem and sleeve views' agreed lengths.

**Render** (against the page before the fit, port 8201):
- torso and neck: **0 pixels changed on the fronts**, including the live neckline at 100 / 194 mm; only the sleeves moved (mean 0.7–1.7 levels over the canvas);
- sleeve and hem views: the print moved (mean 17–27 levels).

Gates as before:
- frame parity ≤ 2.8 × 10⁻¹⁴ cm (`uMm` included);
- the page's maps against the build: uv ≤ 0.0033 cm, trims as before;
- rebuild ALL IDENTICAL;
- closure items: StepA's.

**Registration sheet after step 3:** [`img/stepB-xview-step3.jpg`](img/stepB-xview-step3.jpg) (the underarms are no longer rows: the record does not compare them). **Before and after:** [`img/stepB-step3-before-after.jpg`](img/stepB-step3-before-after.jpg).

**Accept:**
- [ ] `xview_check.py`: every shared landmark within 3 mm, except those the owner accepts. **Not met.** The FAILs above are image disagreements and the sleeve view's turn; none accepted (decision 1 is the owner's).
- [x] The scale of each view, the agreed against the fitted, with the residual: in `plate.dat` `fit.scale` and the invariants.
- [x] The frame invariants and the parity pass. The live neckline is untouched (the torso and neck fronts did not move: 0 pixels).
- [ ] **A person** checks the registration sheet (the owner).

## Step 4: yaw for turned views (F3)

**Done:**
- **`yawDeg` in the frame, all three copies:** `plateframe.py`, `plate.js` `frameUV`, `maps.js` `FRAME_FS` (`uYaw`).
  - The formula: R = h / |sin(±θ + φ) − sin φ| per side; u = R (asin(sin φ + r / R) − φ) inside the silhouette; slope 1 / cos(±θ + φ) past it.
  - With φ = 0 each copy runs StepA's arithmetic exactly (a separate branch).
- **`plate_invariants.py`:** the UV rate at the axis expects 1 / cos φ along u (a turned surface is foreshortened there).
- **`garmentfit.py` `fit_yaw`:** a grid over θ + |φ| ≤ 85°, then refined by 0.01°, with the u shift re-fitted at each turn. **Applied only when over-determined:** at least 4 u landmarks on both sides of the axis, |φ| > 2° and a lower residual. Otherwise the best turn is reported in `fit.zones.<z>.yaw` with the reason, and the frame keeps 0.

**What the fit found:**

| View, zone | Best turn | u rms at 0 / at best (mm) | Applied | Why not |
|---|---|---|---|---|
| torso, front | +0.16° | 0.79 / 0.72 | no | under 2°: **the front views are not turned** (confirms the model) |
| neck, front | −0.53° | 1.19 / 0.73 | no | under 2° |
| sleeve, front | −17.98° | 29.31 / 10.76 | **no** | under-determined: 3 u landmarks (neck-l, neck-r, shoulder) for the shift and the turn |
| hem, all | — | — | no | the u landmarks are on one side of each axis |

**Why the sleeve view's −18° is not applied.** It was applied first, then taken back.
- **The turn trades off against `thetaDeg`.** With the turn fitted at each θ, the rms stays 9.8–10.8 mm for every θ from 40° to 70°. At θ = 60° (the default for a front) the best turn is 0.6° (rms 9.89 mm). The ~10 mm is the three landmarks' own inconsistency, not something a turn removes.
- **The sign contradicts the photo.** The fitted −18° compresses the image-left side of the front. But in the photo the left half of the neck spans 279 px for 8.1 cm of cloth and the right half 125 px for 8.2 cm: the **right** side turns away.
- **The grain check failed with it:** 95 % within 5.01° (limit 3°; 2.94° without it).
- Sheet of the rejected turn, grain checker before | with −18°: [`img/stepB-step4-yaw-rejected.jpg`](img/stepB-step4-yaw-rejected.jpg).
- With the turn, the sleeve view's best-fitting scale was 0.994 × the agreed one (1.254 × without it), so a turn is likely real. **What is missing is data, not a model:** a centre-front point measured in the sleeve view (`cf-neck`, or a centre-front point lower down) would pin both the shift and the turn. **Open item:** measure it on `silhouette/sources/sleeve-straight.png` (`annotate.md`), name it in the record, rebuild; the fit then applies the turn by itself.

**Parity of the turned branch** (a scratch copy of the sleeve plate with the fitted −17.98° and its shift; not committed):
- `frame_check.mjs` max |du| 2.3 × 10⁻¹⁴ cm (limit 10⁻⁴);
- `page-check` uv (the GPU against the build) max 0.0033 cm (limit 0.01).

The three copies agree on the turned arithmetic.

**Plates:** only `yawDeg: 0` and the `fit...yaw` report were added (`--dump` against step 3). No frame number moved, so **the render equals step 3's**. `rebuild-check` ALL IDENTICAL; the invariants as in step 3 (the sleeve front's grain 2.94°).

**Accept:**
- [ ] Sleeve view: neck-l and neck-r within 3 mm of the garment's u. **Not met:** no turn is applied, so as step 3 (−15.6 / −25.5 mm). With the −18° turn they were −15.2 / +7.7 mm, also not met. Needs the measured centre-front point (open item).
- [x] No fold, grain within 3°, UV rate ±2 % at the axis (no turn applied; the turned branch passes parity).
- [ ] Before and after crops approved by a person: nothing to approve (no render change); the rejected turn's sheet is for the owner's information.

## The owner's decisions (2026-11-23, at the wrap-up)

- **"Let the photos disagree":** each residual that comes from the photos, or from the sleeve view's turn that 3 landmarks cannot fix, is **accepted** with its reason in the garment record (`views.<view>.acceptedResiduals`):
  - torso: cf-neck, slit-l, slit-r and the 4 cuff points;
  - sleeve: neck-l, neck-r, shoulder, cuff-out, cuff-in;
  - hem: slit-top, hem-slit.
- The gate prints them as `info … (accepted: …)` with their numbers. `xview_check.py` marks the rows ACCEPTED.
- **The local servers were stopped**, and the rest of StepB ran with short-lived servers (one per check run, stopped in the same command). This included a server on port 8765 that served the whole home directory: another tool's (Copilot), stopped at the owner's word "all".

## Step 5: swatches as data: sidecar, class, placement (F7)

**Done:**
- **`swatchprep/fabric_sidecar.py`** (`prep.py fabric-sidecar`) writes `fabric-<name>.json`: name, tile, tilePx, repeatCm and `repeatSrc`, class, oneWay, motifCentrePx (buta), borderBottomPx / borderTopPx (border), sheen, sheenWidth, antiTile, meanRgb, test.
  - Sage, mocha and mustard: `allover`, `repeatSrc: "assumed"` (30, 30, 20 cm as before). **Their tiles were not touched.**
- **Test prints** (`test_prints.py buta | border`, with sidecars, `?fabric=buta|border`): one 9 cm motif with a crosshair on a 5 cm grid; a hem border (8 cm band, its lower edge at the tile's bottom).
- **`FABRICS` holds only `src` and `meta`.** The page loads the sidecars at start (`fabricMeta`); the captions read the name from them.
- **Placement** (`placeOf`, `setPlacement`; shader `uPlace[16]`, `uTileAnchor`, `uBorderTop`): tile coordinate = (u, v − place[zone]) / repeat + anchor.
  - The place is per zone, from its piece and the garment record's new `placement` block:
    - buta at the centre front 25 cm below the neck-point line (an assumed bust line), and 15 cm down each sleeve's centre line;
    - border on each piece's `hemV`: front and back 105.01 cm (hem-cf), sleeves 47.0 cm (the cuff).
  - All-over prints have place 0 and anchor 0, so they did not move.
- **A border is one band.** Above the band only the ground repeats, wrapped 16 texels inside it so the filtering does not reach into the band. The first render showed the band repeating every 30 cm up the garment; fixed before the close.
- **The scale protocol** for a real swatch (a ruler and a colour card, `--src measured`): `swatchprep/README.md`.

**Measured** (short-lived servers):

| Check | Result |
|---|---|
| Regression against step 3: 4 views × mocha + pearl with all trims, 4 views × the registration print, the live neckline at 100 / 194 mm (9 renders) | **pixel-identical** (mean 0.000); no console error. After step 7's removal of the switch and the border fix: still 0.000 |
| buta, torso and neck views | the motif on the centre front at the bust line in both. Each sleeve has its motif on its centre line; in the sleeve view the motif sits where the fit put the sleeve's u. [`img/stepB-step5-placement.jpg`](img/stepB-step5-placement.jpg) (before the border fix: its border row still repeats) |
| border, 4 views | one band per piece: on the torso's hem and the sleeve view's cuff. [`img/stepB-step5-border.jpg`](img/stepB-step5-border.jpg) |
| border, known limits | **The torso's sleeves:** the band sits 7 cm above the cuff (the accepted sleeve-length disagreement: the record's 47 cm against the torso's 54 cm). **The hem view:** the band's lower 4 cm is cut at the slit corner. The band follows the frame's weft line at hemV 105.0 cm, and the photographed hem rises to 101 cm at the slits. Following the curved hem exactly needs the hem trim's field (StepC). |

**Accept:**
- [x] Mocha, mustard and sage render as at step 4 (pixel-identical), with their sidecars in place of `FABRICS`.
- [x] buta: the motif centre on the centre front at the bust line in the torso and neck views (by construction from the shared frame, whose fronts agree within 1–3 mm); on each sleeve's centre line.
- [ ] border: the same height above the hem (±3 mm) in the torso and hem views. **Not met at the slit corner** (the curved hem, up to 4 cm; StepC). It is met at the centre front, which the hem view does not show.
- [ ] oneway: the same direction on the front and the sleeves, at 2×: **for a person**; by construction v runs down every piece.

## Step 6: formats for the portal; person and device checks

**Done:**
- **`docs/formats.md`:** `BSP3` field by field (type, unit, meaning), the frame's arithmetic, the trims, the fit; the garment record; the fabric sidecar and the placement rule; the design record (with the reserved `print.offsetCm` and fabric per piece); versioning.
- Coverage check (a script over the 4 plates' header, zone, frame and trim keys against the document): **no undocumented field** (`source` and `scaleNote` were added to it).

**Not done here (the owner's):**
- the person checks: the registration sheets (steps 0, 1, 3), the before / after sheets (steps 1, 3) and the placement sheets (step 5);
- the device check (`?perf=1` on the phone and the laptop).

StepB adds per pixel only: one subtraction in `decodeF`, a per-zone placement lookup, and (for a border) a `mod`. In the frame pass it adds one shift; the turn's branch is not taken on these plates. No device budget is expected to move. Not measured.

## Step 7: close

**Done:**
- **`?phase=view` removed** (`PHASE_VIEW`, `uPhaseOff`). The render is unchanged (pixel-identical).
- **Docs:**
  - `breather.md`: §1, §2, the registries, §8, §9 (the open items), glossary (garment record, piece, fit, yaw, placement, sidecar);
  - `render.md` §11: the StepB entry;
  - `plate.md`: the tool limits (step 2);
  - `swatchprep/README.md`: sidecars, test prints, the scale protocol;
  - `silhouette/README.md`: the new checks and `garment.py`;
  - `DedhD.md` §11.7: B done;
  - `docs/formats.md`: new.
- **Housekeeping:** the reference worktrees `../myshoppe-ref` (fbd2446) and `../myshoppe-s1` (step 1) removed. `stepB` merged into `main` (a fast-forward), not pushed.

**Final gates:**

| Gate | Result |
|---|---|
| `rebuild-check` | ALL IDENTICAL |
| `platedat.py --check`, `garment.py --check` | PASS (4 plates; record v1 `d3703734e94314cd`) |
| frame parity (`frame_check.mjs`) | ≤ 2.8 × 10⁻¹⁴ cm on all 4 |
| `plate_invariants.py` | neck ALL PASS. Torso, sleeve, hem: only StepA's closure items fail (6 px, 0.0596 %, 10 px). Garment fit: every residual within 3 mm or accepted by the owner (7 / 5 / 2 accepted) |
| `xview_check.py` | 2 PASS, 8 ACCEPTED, 1 FAIL: shoulder-r on the front. The torso and neck views are 5.5 mm apart, each within 3 mm of the record (2.7 / 2.8 mm), so the plate gate passes. A photo split, as the accepted ones |

**Open items, carried to StepC and later:**
1. **Measure a centre-front point in the sleeve view** (`cf-neck` on `silhouette/sources/sleeve-straight.png`), name it in the record, rebuild. The fit then applies the turn (step 4) by itself, and the 5 accepted sleeve-view residuals should shrink.
2. **The hem view's shaded left panel** is mapped to the front (a fold); the owner to confirm (`garment.views.hem.note`).
3. **A border on a curved hem:** use the hem trim's field (`t` from the edge) instead of the frame's weft line (StepC).
4. **The slits' field** is still keyed by the names `slit-l` / `slit-r` (`SLIT_OFF_CM`); the trim field's s range is ±64 cm (StepC).
5. **The scales** of the AI swatches and laces are assumed; a real swatch needs the protocol in `swatchprep/README.md`.
6. **StepA's** closure items (torso 6 px, sleeve 0.0596 %, hem 10 px) and 1 px of torso coverage.
7. **The person and device checks** of step 6.
