# Plan: StepB — one fabric frame for the garment, and swatches as data

Status: **closed** (2026-11-23). The §7 decisions taken, the owner's acceptances and the open items are in `StepB-results.md`. The data contract: `docs/formats.md`.
Read first: `docs/breather.md`, then `DedhD.md` §11 (option B, §11.1 item 2, §11.5) and `plan/StepA-results.md` (step 4: the cross-view table).
Base: `main` = `origin/main` (`fbd2446`, StepA closed). StepA step 8 (phone and laptop) **passed** (the owner, 2026-11-23).
Scope: the straight kurta, 4 views (torso, neck, sleeve, hem), its fabrics. **Laces are StepC.** No new silhouette. Product rules unchanged: 4 fixed views, **no 3D, no pan, no zoom**.

**Why this plan matters beyond the demo.** The demo is the test bed for the portal. What the portal takes from it is **data**: the plate file, the garment record and the swatch sidecar. StepB makes those three files exact and self-describing. A point of the cloth must have one fabric coordinate in every view. The plate must say which garment and which pieces it maps. A swatch must carry its own scale, class and placement. Every number must carry its source and its residual.

## 1. Final expected behaviour

When StepB is closed, this is true:

**What the customer sees**
1. **The print is in the same place in every view.** A motif at the centre front, just under the neck, is the same motif, at the same place (within the tolerance of item 9), in the torso and neckline views. A motif on the sleeve is the same in the torso and sleeve views. A motif at the hem is the same in the torso and hem views.
2. **The print is placed by design, not by chance.** Each fabric has a defined placement: for example, a motif centred on the centre front at the bust line, or a border sitting on the hem. A one-way print runs down the body and down each sleeve.
3. Everything StepA delivered still holds: the fabric to the photo's edge, seams, soft edges, laces, the live neckline, and the build-time budgets on the same devices.

**What the data is**

4. **A garment record** in the look file (`assets/looks/straight-kurta.json`, block `garment`) lists the garment's **pieces** (front, back, sleeve-l, sleeve-r). For each piece it gives:
   - its grain axis and its origin;
   - its landmarks in **piece cm** (neck points, centre-front neck, shoulder, underarm, slit top, hem corners, cuff);
   - its hem line (v of the hem), for border prints;
   - for **every number, its source**: `agreed` (a value the atelier gave), `measured` (one view), `fitted` (several views, with a residual) or `assumed`.
5. **`plate.dat` version 3 (`BSP3`)** adds:
   - the garment it was built against (look, version and a hash of the `garment` block);
   - for each zone, its **piece**;
   - **the zone and trim tables** (name → id, order, group): the page and the tools read them from the plate, not from tables written in code;
   - each frame's **fitted parameters and residuals**: the landmark residuals in mm, and the scale with its source.

   The per-view packing offset (`uvOffsetCm`) is gone. One fixed garment offset is used, the same for every plate.
6. **A fabric sidecar** `assets/swatches/fabric-<name>.json` per fabric, written by `swatchprep`. It holds:
   - `repeatCm` with its source (`assumed` for the three AI swatches) and the tile size in px;
   - `class`: `allover`, `oneway`, `buta` (a placed motif), `border` or `irregular`;
   - `motifCentrePx`, `sheen`, `sheenWidth`, `antiTile`.

   `FABRICS` in `testing.html` keeps only `src` and `meta`.
7. **The design record** (`state`, in the URL) gains the fabric placement, `print.offsetCm` per piece. The defaults come from the fabric's class.
8. **A format document**, `docs/formats.md`, specifies `BSP3`, the garment record, the fabric sidecar and the design record for the portal: each field, its unit, its range and its source.

**How exact**

9. **Cross-view agreement.** For every landmark seen in two or more views, the fabric (u, v) of the views differ by **≤ 3 mm** (§7, decision 1). Each landmark over the limit is written with its cause: the image (the photos disagree), the definition (two views name different points) or the model (the frame is wrong).
10. Every frame invariant of StepA still passes:
    - no fold;
    - grain within 3°;
    - UV rate ±2 %;
    - parity, `plate.js` against the build, ≤ 10⁻⁴ cm;
    - the page's maps against the build: uv within one 16-bit step (0.0039 cm over 256 cm).
11. `rebuild_check.sh`: every plate is byte-identical to what its source and the garment record make. A plate built against an older garment record is refused.

## 2. What is wrong now (measured or read in the code, 2026-11-23)

| # | Finding | Where | Effect |
|---|---|---|---|
| F1 | **The packing offset sets the print's phase.** The frame's (u, v) is stored with a per-view offset (`uvOffsetCm`: torso [36, 2], neck [25, 1], sleeve [40, 5], hem [12, −84] cm) so that it packs as ≥ 0. The page never subtracts it: `fabricAt(uv / uFabricCm)`. | `maps.js:97`, `testing.html:861` | On mocha (30 cm repeat), the centre front under the neck is 6 cm into the tile in the torso view and 25 cm in the neck view: the motifs differ by 11 cm (mod 30). On mustard (20 cm) the shift is also 11 cm. This is the largest cause of "not the same motif", and it is not the photos. |
| F2 | **No garment record.** Each view's frame is anchored on its own (`s0`, `vMm`), and nothing ties a sleeve or a back piece to the front. | `plate.dat` frames | There is no single answer to "where is this cloth point" across views. |
| F3 | **Turned views have no yaw.** The cylinder is symmetric about the axis. Left and right half-widths differ, but the arc is not rotated. | `plateframe.py` | In the sleeve view, `neck-l` is at u = −11.0 cm and `neck-r` at 4.3 cm. In the front views they are at ∓8.1. That is a 2.9 cm error on the left. |
| F4 | **The photos disagree.** | StepA step 4 cross-view | The centre-front neck depth differs by 7 mm between the torso and neck views. `underarm-l` has v 21.6 cm in the torso view against 17.2 cm in the neck view (a 4.4 cm difference: image or definition, to find out in step 0). `hem-l` names different points in the torso and hem views. |
| F5 | **Each scale comes from one agreed distance.** The torso borrows the neck view's 158 mm, which puts the shoulders at 341 mm against the old 370 mm assumption. | `plate.md` §5 | A scale error moves every motif in that view, and nothing reports it. |
| F6 | **The id tables are written 3 times, with fixed names.** Zones: at most 7 (`uOrderOf[8]`). Trims: 8 of 8 used (`uTrim*[9]`). | `make_plate.py:34-35`, `maps.js:496`, `testing.html:410` | A new piece or trim means editing three files in step. The portal cannot read the meaning of an id from the data. |
| F7 | **The swatch facts are in page code.** `repeatCm`, `sheen` and `antiTile` sit in `FABRICS`, all assumed and not marked as such. There is no class and no placement. | `testing.html:395` | The portal would have to copy page code to know a swatch. |
| F8 | **128 cm range per view.** It fits the kurta only because each view picks its own offset (F1). | `maps.js:416` | With one garment-wide offset, the front (v from about −2 to 110 cm, u ±40 cm) and a longer garment later need a larger range. |

## 3. Rules

- **Branch `stepB` from `main` (`fbd2446`).** One checkout, port 8300. The reference is a worktree of `fbd2446` on port 8200, for before and after views; it is deleted at the close.
- **One step = one commit**, with its results in `docs/plan/StepB-results.md`. A FAIL is written with its number, as an open item.
- **This plan changes the render on purpose** (F1 moves the print in every view). Each such step shows before and after crops, and a person approves the sheet. There is no pixel-identity gate against `fbd2446`.
- **A test switch for the old behaviour** exists until step 7, which removes it: `?phase=view` (the per-view offset phase of F1).
- **Nothing is edited by hand** in a plate or in a sidecar. A change is a change to a view's measurements, the garment record or a tool, followed by a rebuild.
- **Every number has a source.** No unlabelled constant may enter the garment record, a plate or a sidecar.
- `make_plate.py` (Python, Pillow only) stays the reference. `plate.js` and `FRAME_FS` are copies of its maths, kept equal by `frame_check.mjs`.
- Review shots: `node silhouette/checks/cdp_shot.mjs <out> <free port> "<query>"`. Review images go to `demo/review/` (not committed); an image cited in the results is copied to `docs/plan/img/`.

## 4. Steps

### Step 0: Baseline, the cross-view check, a registration fabric, housekeeping

**Do:**
1. Branch `stepB`. Worktree `../myshoppe-ref` at `fbd2446`, port 8200. Create `StepB-results.md`.
2. **Housekeeping:**
   - record step 8 as passed in `StepA-results.md` (with the device numbers, if the owner supplies them);
   - bring `breather.md` up to date: the checkout path, the "not pushed" note, §2, and the missing §7–§11 that §13 refers to.
3. **`silhouette/checks/xview_check.py`** (numbers only, no render). For every landmark in two or more views:
   - (u, v) from each view's frame, after the packing offset is removed;
   - the differences in mm;
   - with `--page <port>`, the same values read from the page's uv map (`window.__studio.readMapsRaw()`), and the phase each view gives the print: (u, v) mod `repeatCm`.
4. **The registration fabric** `assets/swatches/fabric-reg-1024.png` (made by a script, not drawn):
   - a 30 cm tile with a 1 cm grid, labelled 5 cm marks and one coloured crosshair per 10 cm cell;
   - available as `?fabric=reg` (a test fabric, not in the picker).
5. **Baseline:**
   - `xview_check.py` on all 4 plates;
   - the 4 views side by side with `fabric=reg` (one sheet);
   - the phase table of F1 for mocha and mustard.
6. **Classify each cross-view difference over 3 mm:**
   - **image:** the photos disagree;
   - **definition:** two views name different points (the hem-l case);
   - **model:** the frame is wrong (the sleeve-view yaw).

   The underarm's 4.4 cm is settled here.

**Accept:**
- [ ] The baseline table lists every shared landmark: Δu and Δv in mm, and the cause class of each one over 3 mm.
- [ ] The registration sheet shows F1: different crosshairs at the centre-front neck in the torso and neck views.
- [ ] `breather.md` is current: every path and branch named in it exists.

### Step 1: The print's phase from the garment, not from the packing (F1, F8)

**Do:**
1. Fabric uv packing: one fixed **garment offset**, the same for every plate: u + 128, v + 32 cm, over a **256 cm** range. One 16-bit step is 0.0039 cm, which is 5.7 steps per px on the finest plate (0.222 mm/px). The constants are written in `plate.dat` (`uvPack`). `maps.js` and the page read them from there.
2. The page subtracts the offset when it decodes. From then on, `uv` in the shader is the true garment cm.
3. `uvOffsetCm` is removed from the views and from `make_plate.py`. A range check (`pack()` raises in the build, and `platedat.py --check` too) replaces it.
4. The trim fields (`uvt`, `uvts`) keep their own packing (128 cm) until StepC: separate constants, named so.
5. `?phase=view` gives back the old offsets (switch until step 7).

**Accept:**
- [ ] The frame invariants and the parity hold. The page's maps match the build within one 16-bit step on all 4 views.
- [ ] Phase table: at the centre-front neck, the torso and neck views give the same tile phase within 1 mm. The registration sheet shows the same crosshair there.
- [ ] Before and after crops of all 4 views (mocha, mustard). The print moves by the offset and nothing else changes. A person approves the sheet.
- [ ] `plate.dat` for the 4 views stays ≤ 40 KB.

### Step 2: The garment record and `plate.dat` version 3 (F2, F6)

**Do:**
1. **Garment record:** the `garment` block in `assets/looks/straight-kurta.json`.
   - **Pieces** `front`, `back`, `sleeve-l`, `sleeve-r`:
     - front and back: u from the centre front (centre back), v from the neck-point line;
     - each sleeve: u from its centre line, v from the shoulder point along the arm.
   - **Landmarks per piece**, in cm, each with its source. Start from the agreed measures (neck width 158 mm, neck depth 39.7 mm, shoulder → cuff 470 mm, slit 240 mm). Take the rest from the views (measured), or from their mean where two views see the point (fitted, with the spread).
   - **The hem line per piece** (for border prints), and the slit tops.
   - **Landmark names are unique and defined once.** The hem-l case of step 0 gets two names.
   - `garmentVersion`. `swatchprep`-style validation: units, ranges, every value has a source.
2. **`BSP3`** (`platedat.py`):
   - header: `look`, `garmentVersion`, `garmentHash`;
   - `pieces` per zone;
   - the **zone table** (`name → id, order, piece`) and the **trim table** (`name → id, group`);
   - the ids are assigned by the build; the code tables go;
   - the page's arrays are sized by one `MAX_ZONES = 15` and `MAX_TRIMS = 15`, checked at load.
   - **the lace band per trim** (`bandInMm`, `bandOutMm`): the depth inward and the overhang outward that the trim field covers. It replaces the constants `LACE_IN_MM` / `LACE_OUT_MM` (`plate.js`, `trimfield.py`) and the 56 mm in the neck area's reach (`make_plate.py`). Each value comes from the plate's settings, defaulting to today's 56 / 8 mm, so StepC can widen one trim (a hem border) without a code change;
   - **the join of each trim as structured data**: `{kind: mitre | butt | overlap | open, with: <trim> | null}` in place of today's text (`join = "mitre with slit-l"`). The page and the build read the kind, not the text;
   - `--dump` and `--check` extended; `BSP2` is read once by a converter, deleted in the same commit.
3. `make_plate.py` refuses to build if a view's landmark is not in the garment record. `rebuild_check.sh` also fails if a plate's `garmentHash` is not the current one.

**Accept:**
- [ ] `grep` finds no zone or trim id table in `make_plate.py`, `maps.js` or `testing.html`.
- [ ] The render at 8300 is unchanged by this step (mean difference ≤ 0.5 against step 1): it moves data, not maths.
- [ ] `rebuild_check.sh` passes. Editing one garment value makes it fail until the plates are rebuilt.
- [ ] `--dump` shows every garment value with its source.

### Step 3: Frames fitted to the garment (F2, F4, F5)

**Do:**
1. For each zone, the build solves the frame's free parameters so that the view's landmarks land on the garment's cm. The free parameters are the anchor `vMm`, a u shift (0 on the front by construction) and, by §7 decision 2, the view's `mmPerPx`. This is weighted least squares: agreed landmarks weigh more than measured ones.
2. The residual of each landmark (mm) and the fitted values with their source go into `plate.dat` (`fit`).
3. `plate_invariants.py` gains the **cross-view gate**: every landmark residual ≤ 3 mm, or listed in the plate's `decisions.acceptedResiduals` with its cause class from step 0. An agent may not add to this list; the owner does.
4. The live neckline uses the fitted scale. Its depth and width response is checked again (±1 px, as StepA step 4).

**Accept:**
- [ ] `xview_check.py`: every shared landmark within 3 mm, except the ones the owner accepted (expected: the 7 mm neck depth, unless decision 1 says otherwise).
- [ ] The scale of each view, old against fitted, with the residual. The torso's shoulder width is reported in mm.
- [ ] The frame invariants and the parity pass. The live neckline response is ±1 px.
- [ ] Registration sheet: the same crosshair at each shared landmark in each pair of views.

### Step 4: Yaw for turned views (F3)

**Do:**
1. The frame gains `yawDeg`, the turn of the body about its axis in that view. With x the signed distance from the axis and R the radius on that side, `u = R (asin(sin φ + x / R) − φ)`. With φ = 0 this is today's formula. It is continued linearly past the silhouette, as now.
2. `yawDeg` is fitted with the step 3 parameters, for the sleeve view's front and the hem view's pieces. The front views keep 0 unless the fit says otherwise (by more than 2°).
3. Applied the same way in `plateframe.py`, `plate.js` and `FRAME_FS`. `frame_check.mjs` covers yaw.

**Accept:**
- [ ] Sleeve view: `neck-l` and `neck-r` within 3 mm of the garment's u (now 29 mm off on the left).
- [ ] No fold, grain within 3°, UV rate ±2 % at the axis. On a turned zone, the squares narrow towards the side that turns away and not towards the other.
- [ ] Before and after crops of the sleeve and hem views, approved by a person.

### Step 5: Swatches as data: sidecar, class, placement (F7)

**Do:**
1. `swatchprep/prep.py fabric` writes `fabric-<name>.json` next to the tile: `repeatCm` with its source (`assumed` for sage, mocha, mustard and reg), `tilePx`, `class`, `oneWay`, `motifCentrePx` (found as for the lace motif; for `allover`, null), `sheen`, `sheenWidth`, `antiTile`, `meanRgb`. The existing three are rebuilt from their sources, and the tiles stay byte-identical.
2. `FABRICS` keeps `src` and `meta`. Everything else is read from the sidecar.
3. **Placement:** the tile coordinate is `(uv − place + motifCentreCm) / repeatCm`, where `place` comes from the design record (`print.offsetCm` per piece). The defaults by class:
   - `allover` and `irregular`: a fixed garment origin, so the views agree (step 1) but no point is chosen;
   - `buta`: the motif centred on the centre front at the bust-line landmark, and on each sleeve's centre line;
   - `border`: v measured up from the piece's hem line, so the border sits on the hem in every view;
   - `oneway`: the print's "up" is v decreasing on every piece (down the body, down the arm).
4. **Test prints** to prove each class, made by a script as `reg` is: a `buta` print and a `border` print. They are test fabrics, not in the picker. They prove the maths until a real border or buta swatch exists.
5. **A scale protocol** for real swatches, in `swatchprep/README.md`: a flat scan with a ruler and a colour card; `repeatCm` measured and marked `measured`. The AI swatches stay `assumed`; the sidecar says so, and the page shows nothing different.

**Accept:**
- [ ] Mocha, mustard and sage render as at step 4 (mean ≤ 0.5), with their sidecars in place of `FABRICS`.
- [ ] `buta` test print: the motif centre lands on the centre front at the bust line within 3 mm in the torso and neck views, and on the sleeve's centre line in the torso and sleeve views.
- [ ] `border` test print: the border's top line is at the same height above the hem (±3 mm) in the torso and hem views, and it follows the curve of the hem.
- [ ] `oneway`: the same print direction on the front and the sleeves, at 2× (person).

### Step 6: Formats for the portal, and the person and device checks

**Do:**
1. **`docs/formats.md`**: `BSP3` field by field (type, unit, range, source); the garment record; the fabric sidecar; the design record; the packing; the versioning rule (a plate names its garment version and hash). It is written from the code, then checked against `platedat.py --dump` of each plate.
2. **Person:** the registration sheet, the buta and border sheets, and mocha and mustard in all 4 views at 2×.
3. **Devices:** the owner opens `testing.html?step=<cloth|neck|sleeve|hem>&perf=1` on the same phone and laptop as StepA step 8. Build ≤ 50 ms (laptop) and ≤ 250 ms (phone); drag ≥ 30 fps.

**Accept:**
- [ ] `formats.md` covers every field that `--dump` prints (a script compares the field lists).
- [ ] The person's approval is written in the results.
- [ ] Device numbers are written in the results, within budget.

### Step 7: Close

**Do:**
1. Remove `?phase=view` and its code path.
2. Delete the reference worktree.
3. Update `breather.md` (§1, §4–§6, glossary: garment record, piece, yaw, placement, sidecar), `render.md` §11, `plate.md` (the plate checks, the scale now fitted), `swatchprep/README.md` and `DedhD.md` §11.7 (B: done).
4. List the open items carried to StepC.

**Accept:**
- [ ] `rebuild_check.sh`, `plate_invariants.py`, `xview_check.py`, `frame_check.mjs` and `maps_check.py` all pass, or every FAIL is listed with its number and an accepted cause.
- [ ] The results file has one section per step.

## 5. Out of scope (StepC and later)

- **Laces** (StepC):
  - the trim band per trim instead of the fixed 56 / 8 mm;
  - the trim field's ±64 cm range and the slits encoded in u;
  - one lace texture (no two borders);
  - corner and end pieces; lace classes.
- **A different fabric per piece in the shader** (one fabric texture now). The data allows it (`print` per piece; see §7 decision 3).
- Normals from the base image; interactions on the design record (option D); new silhouettes and the catalogue factory (option E).

## 6. Risks

| Risk | Effect | Mitigation |
|---|---|---|
| The photos disagree more than 3 mm at several landmarks | Step 3 cannot pass on numbers alone | Step 0 classifies each one. The owner chooses: a new image, an accepted residual or a local correction (decision 1). |
| A fitted scale moves the live neckline's mm | The design record means something different | The neckline response check in step 3. The look's defaults are re-read from the fitted scale. |
| Yaw changes the frame maths in three copies | A parity break | `frame_check.mjs` extended first, then the code. |
| The garment record becomes a second place to edit landmarks | The two drift apart | The build refuses unknown landmarks, and the hash ties plates to the record. |

## 7. Decisions needed before the go-ahead

1. **Cross-view tolerance and the photos' disagreement.** The proposed limit is **3 mm**. For the known 7 mm neck depth (and anything step 0 finds), choose one:
   - **(a)** edit or regenerate one image;
   - **(b)** accept the residual and record it;
   - **(c)** a small local correction of the frame near the landmark, capped (for example ≤ 5 mm), in the plate.
2. **Scale:** fit each view's `mmPerPx` from all of its landmarks (more exact; the residual is reported; every view's scale moves a little), or keep the one agreed distance per view.
3. **Fabric per piece:** data only in StepB (proposed), or also a second fabric texture in the shader now (for contrast yokes and sets).
4. **Branch and push:** work on `stepB` and merge to `main` at the close (proposed), or commit on `main` directly. Push `main` after StepB or after StepC?
