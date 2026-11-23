# Plan: StepC — lace as parts: data, joins, ends, two laces, the curved hem

Status: **closed** (2026-11-23). The decisions taken, the deviations and the open items are in `StepC-results.md`.
Read first: `docs/breather.md`, `docs/formats.md` (the data contract), `DedhD.md` §11.7 option C, and the open items at the end of `plan/StepB-results.md`.
Base: `main` (StepB merged, `9f5755d`, not pushed). Scope: the straight kurta, 4 views, its laces and trims. No new silhouette. **No 3D, no pan, no zoom.**

**Why this plan matters for the portal.** StepB made the fabric exact data. The lace is still partly page code:
- one lace for every trim;
- its width assumed and unmarked;
- the slits keyed by their names;
- the joins written as data, but the page ignores them;
- no corner or end pieces;
- a border print that cannot follow a curved hem.

StepC makes a lace and a trim as self-describing as a fabric. The portal can then offer laces per placement and hand the atelier a trim sheet in mm.

## 1. Final expected behaviour

**What the customer sees**
1. **A lace per placement.** The neckline, cuffs, hem and slits can each take their own lace, with up to two different laces on the garment at once (decision 1). A slit and its hem may differ.
2. **Clean ends and corners.**
   - A slit's top ends in a finished end piece (a whole motif or the lace's own end), not a square cut through a motif.
   - Where a slit meets the hem, the two laces meet as the record says: a mitre (today), a butt or an overlap.
   - A lace that has a corner piece uses it at a sharp corner.
3. **Motifs do not jump while dragging.** When the customer changes the neckline, the number of whole repeats changes only past a threshold (hysteresis). Between thresholds the lace stretches or shrinks a little (within ±6 %, decision 2).
4. **A border fabric follows the hem**, the curved one included: its lower edge sits on the hem in every view, including the hem view's slit corner (StepB open item 3: 4 cm off today).
5. Everything StepA and StepB delivered still holds: fabric to the edge, soft edges, the live neckline, the print's place in every view, the build budgets.

**What the data is**

6. **Lace sidecar version 2** (`lace-<name>.json`):
   - `widthMm` with `widthSrc` (assumed | measured), the repeat and its source;
   - `class`: `insertion` | `edging` | `border` | `gota` | `zari` | `pearl` | `mirror` | `latkan`;
   - `parts`: where the side tile, the end piece and the corner pieces are in the lace's files (made from the band by a script, or from a photo later);
   - the existing keys (period, edge depth, material map).

   `LACES` in `testing.html` keeps `src` and `meta` only, as `FABRICS` does.
7. **Trims in `plate.dat`** (version 4, `BSP4`):
   - each trim's **field slot** comes from the plate (no `SLIT_OFF_CM` keyed by name);
   - the cloth length along an edge (`s`) packs over ±128 cm (today ±64 cm, the slits ±32 cm);
   - each trim **end** has a kind: `runout` (the silhouette cuts it), `cut` (square), `piece` (an end piece);
   - sharp **corners** along a trim's line are listed, with their angle and inner or outer side.
8. **The design record** gains `lace` per trim group (`neck`, `cuffs`, `hem`, `slits`). The URL keeps `?lace=` as "all groups".
9. `docs/formats.md` covers all of it.

**How exact**

10. **Cross-view lace check** (`xview_lace.py`): at the points two views share, the lace's phase (s modulo the repeat) agrees within 3 mm, or the difference is one the owner accepted. The centre front of the neck is the torso and neck views; the hem corner at the slit is the torso and hem views. The slit lengths differ by the photos (accepted in StepB), so the slits' counts of whole repeats may differ; their start at the hem corner must not.
11. The trim-field checks of StepA hold:
    - complete: no pixel without a value, 1 px to 30 mm in;
    - no seam within 30 mm;
    - the page against the build: s within 0.01 cm, t within 0.05 mm.

## 2. What is wrong now (read in the code, 2026-11-23)

| # | Finding | Where | Effect |
|---|---|---|---|
| L1 | **One lace texture** (unit 6, its material on unit 7) for every trim | `testing.html` `setLace` | No lace per placement; no two borders (the Salon's code allows more than one) |
| L2 | **Lace widths and repeats are assumed**: pearl 30, geometric 40, leaf 25, fine 15, paisley 53.4, brocade 28.2 mm. The sidecar has a free-text note, no source field | `lace-*.json` | The portal cannot tell a measured lace from a guessed one |
| L3 | **The slits are keyed by name**: `slit-l` → s + 32, `slit-r` → s + 96 in their own field. **s range ±32 cm per slit, ±64 cm on the main field** | `plate.js` / `trimfield.py` `SLIT_OFF_CM`, `S_OFF_CM` | A third opening (an angrakha wrap edge, a choli back) or a long hem (a flared silhouette) does not fit |
| L4 | **Joins are data, but unused.** The page mitres a slit against its hem by "the nearer edge wins"; `join.kind` is never read | `testing.html` (`uTrimOrder`, `fieldAt`) | Butt and overlap joins are impossible; the data says one thing, the page does another |
| L5 | **Ends:** a slit's top is a square cut through the lace (`cut`); cuffs and neck run out to the silhouette. No end piece, no corner piece | `trimfield.py` `extended`, `cut` | A cut motif at every slit top; a V or square neckline (later) would need corner pieces |
| L6 | **Lace fit:** the neck and hem centre a motif at u = 0 with no whole-repeat fit; the slits and cuffs fit whole repeats within ±5 % (±10 % on short trims). No hysteresis | `laceFit` | While dragging, a whole-repeat fit would make motifs jump |
| L7 | **A border fabric uses the frame's weft line**, not the hem | `testing.html` `placeOf` (StepB) | On a curved hem the band is cut (4 cm at the hem view's slit corner) |
| L8 | **Edging only on laces with a clean key** (pearl, geometric, paisley); fine and leaf stay insertion (their keys are not clean) | sidecar `edging` | Asset quality, not code: listed, not fixed here |

## 3. Rules

- **Branch `stepC` from `main`.** One commit per step, results in `plan/StepC-results.md`; a FAIL is written with its number.
- **Lighter verification** (the owner, 2026-11-23: StepB's checks took too long):
  - each step runs the offline gates (`rebuild-check`, `check`, the parity checks);
  - one render run per step that changes the render, with a short-lived server stopped in the same command;
  - no standing reference worktree. A before / after is rendered only when a step changes the render on purpose, from a scratch `git archive` export of the previous commit.
- **Nothing is edited by hand** in a plate or a sidecar: change a view, the record, a tool or a source, then rebuild.
- **Every number has a source** (the StepB rule), the laces' too.
- **A person approves** what a render shows. The agent's look is not the approval.

## 4. Steps

### Step 0: Baseline, a registration lace, the lace cross-view check

**Do:**
1. Branch `stepC`. Create `StepC-results.md`.
2. **The registration lace** (`swatchprep/test_prints.py lace-reg`, with its sidecar): a 30 mm band.
   - Motifs numbered 1, 2, 3 …, each with an arrow pointing to the decorative edge.
   - A thin line at every motif boundary, and a distinct end motif ("E") and corner motif ("C") in its parts (used from step 3).
   - It shows at a glance the direction, the phase, the whole repeats, the ends and the joins. `?lace=reg`, not in the picker.
3. **`silhouette/checks/xview_lace.py`:**
   - For each trim and lace: its length in cm, the repeat, the count of whole repeats, the phase at its anchor.
   - At the shared points: the phase in each view (cf-neck: torso and neck; the hem corner at the slit: torso and hem).
   - Numbers from the plates and the sidecars, no render.
4. **Baseline:**
   - `xview_lace.py` on the 6 laces;
   - one sheet of the 4 views with `?lace=reg&trims=neck,cuffs,hem,slits`;
   - an inventory of the 6 laces: width, repeat, edging, mirror, and what is assumed.

**Accept:**
- [ ] The baseline table and the sheet; each cross-view difference over 3 mm is classed (photos / model / data).

### Step 1: Lace sidecar version 2 (L2)

**Do:**
1. `swatchprep/prep_lace.py` writes and reads version 2:
   - `widthMm` + `widthSrc` (all 6 `assumed`);
   - `repeatSrc`;
   - `class` (pearl → `pearl`, fine → `zari`, geometric, leaf, paisley, brocade → `insertion` or `edging` by their edge);
   - `parts` (step 3 fills it);
   - `version: 2`.

   The existing 6 sidecars are converted by the tool, not by hand; the band and material images stay byte-identical.
2. `LACES` keeps `src` and `meta`. The name, width and class come from the sidecar.
3. A scale protocol for a real lace (a ruler across the band, `--width-mm --src measured`) in `swatchprep/README.md`.

**Accept:**
- [ ] The render is pixel-identical to step 0 (6 laces × 4 views, one run).
- [ ] Every lace number in the sidecars has a source.

### Step 2: The trim field without names (L3) and `BSP4`

**Do:**
1. **The slits' field:** the trim's id goes into the id map's B channel (bits 4–7; bit 0 stays the neck area), not into the packed s. Both fields pack s + 128 over 256 cm (±128 cm along an edge).
2. **The trim's field slot** (`field`: main | open) and its packing come from `plate.dat`. `SLIT_OFF_CM`, `S_OFF_CM` and `TRIM_RANGE_CM` (128) go; the page reads `trimPack` from the plate.
3. **`BSP4`:**
   - `trimPack`;
   - each trim's `ends` {from, to}: `runout` | `cut` | `piece`, from today's `cut` list (today's cut ends become `cut`, the rest `runout`);
   - each trim's `corners` (the build finds bends sharper than a threshold along the line: angle, side). None are expected on these plates; the slit / hem meeting is a join, not a corner.
4. `maps.js` `TRIM_FS`, `trimfield.py`, `plate.js`, `maps_check.py` follow. `rebuild-check` and the parity checks gate it.

**Accept:**
- [ ] The render is pixel-identical to step 1 (it moves data, not maths); the trim-field checks pass (s 0.01 cm, t 0.05 mm, complete, no seam within 30 mm).
- [ ] `grep` finds no trim name in the field code.

### Step 3: Joins and ends from the data, end and corner pieces (L4, L5)

**Do:**
1. **The join kinds in the shader**, read from `join`:
   - `mitre`: today's nearer-edge rule;
   - `butt`: the `with` trim stops at this trim's inner edge (this one runs through);
   - `overlap`: both run, the trim in front (by order) on top, with its shadow;
   - `open`: no meeting.

   The torso's and hem view's hem / slit joins stay `mitre` (the render must not change for them).
2. **End and corner pieces from the band** (`prep_lace.py --parts`):
   - **the end piece:** the whole motif nearest the band's start, finished by the band's own edge (a soft fade over a quarter period where the lace has no natural end);
   - **the corner piece:** a mitred square of the band with a motif centred on the diagonal.

   They are written beside the band as `lace-<name>-parts.webp` and listed in `parts`. A real lace's photographed end or corner can replace them later.
3. **`piece` ends:** the page lays the end piece over the last part of the trim (its length = one period), so the trim ends on a whole motif. The **slit tops become `piece`**: the record's change, written in the view file.
4. **Corners:** at each listed corner the page lays the corner piece. None on these plates; tested on a synthetic trim in `xview_lace.py`'s self-test (an L-shaped line on a test plate built in memory).

**Accept:**
- [ ] The slit tops end on a whole motif in the torso and hem views, with the registration lace (motif numbers whole, "E" at the top).
- [ ] The hem / slit mitre is pixel-identical to step 2. A `butt` and an `overlap`, set on a scratch copy of the hem plate, render as described (sheet, for a person).
- [ ] The trim-field checks hold.

### Step 4: A lace per placement, two laces at once (L1)

**Do:**
1. **The design record:** `state.lace = {neck, cuffs, hem, slits}` (a lace key or `none`); the URL takes `?lace=<key>` (all groups) or `?lace.hem=<key>` (one group).
2. **Two lace slots** in the shader, each with its band, material map and parts:
   - slot A on units 6 and 7 (as now);
   - slot B on units 10 and 11 (WebGL2 guarantees 16 units; the build uses 14 and 15 as scratch).

   Each trim id maps to a slot (`uTrimSlot[16]`). A third different lace is refused in the UI with a message (decision 1).
3. **The lace fit per trim** uses its own lace (width, repeat). The two edges of one slit share the slit group's lace.
4. **The UI:** the lace picker gets a placement selector (all, or one group); the review strip names the lace of each group.

**Accept:**
- [ ] With one lace in all groups, the render is pixel-identical to step 3.
- [ ] Pearl on the neck and geometric on the hem and slits, in all 4 views: each trim shows its own lace at its own width and repeat; no console error.
- [ ] The build budget: no device number moves (the owner's device check, step 6).

### Step 5: The repeat rule while dragging (L6)

**Do:**
1. Every trim with whole repeats keeps a count n. A change of length keeps n while L / (n · r) stays within 1 ± 6 % (decision 2), then moves n by one.
   - The neck: whole repeats between the corners, a motif centred at the centre front. Today the neck is not fitted; this changes the neck's look, so a before / after sheet goes to a person.
   - The slits and cuffs keep the StepA fit, now with hysteresis.
2. The count is part of the design record (`state.laceN`), so a shared link shows the same motifs.
3. `xview_lace.py` reports n per trim per view.

**Accept:**
- [ ] Dragging the neckline from 132 to 194 mm wide and back: n changes at most once per threshold crossing, never back and forth (a scripted drag through `window.__studio.setNeck`, the count logged per frame).
- [ ] The torso and neck views show the same n on the neck.

### Step 6: The border fabric on the hem (L7, StepB open item 3)

**Do:**
1. A border fabric's v near a hem trim comes from that trim's field: v = hemV − t / 10, with t the distance from the hem edge in mm. Away from the field it falls back to the frame (StepB). The two meet with a 10 mm blend.
2. The hem trims' band covers the border: `settings.laceBandMm` (or a per-trim `bandInMm`) of the hem trims raised to the border height (about 100 mm; decision 3), in the torso and hem view files. The plates rebuild (the band is in the plate since StepB).
3. The fabric's sidecar says how deep its border is (`borderTopPx`), so the page knows when the field is deep enough.

**Accept:**
- [ ] With the border test print, the band's lower edge sits on the hem within ±3 mm along the whole hem in the torso and hem views, the slit corners included (today 4 cm).
- [ ] The trim-field checks hold with the deeper band (complete; no seam within 30 mm; the deeper seams reported).

### Step 7: Formats, person and device checks, close

**Do:**
1. `docs/formats.md`: lace sidecar version 2, `BSP4` (trim pack, ends, corners), the design record's lace per group and its counts.
2. **Person:** the sheets of steps 0, 3, 4, 5 and 6. **Devices:** `?perf=1` on the phone and the laptop, with two laces (step 4).
3. Docs: `breather.md`, `render.md` §11, `plate.md`, `swatchprep/README.md`, `DedhD.md` §11.7 (C done). Results closed with the open items. Merge `stepC` into `main` (no push unless asked).

**Accept:**
- [ ] All offline gates pass or every FAIL is listed; the results have one section per step.

## 5. Out of scope (later)

- **New lace photography** (gota patti, mirror work, latkan, real zari) and the re-keying of fine and leaf (L8): assets from the owner. The classes and the parts are ready for them.
- **Mirror work's specular discs** and **latkan tassels that hang**: new material channels and an overhang geometry (a later plan).
- **The sleeve view's centre-front point** (StepB open item 1): a measurement, not lace work. It can be done any time, and the fit then applies the turn.
- New silhouettes, a V or square neckline (the corner pieces are ready for them), the catalogue factory.

## 6. Risks

| Risk | Effect | Mitigation |
|---|---|---|
| End and corner pieces cut from an AI band look wrong (a half motif, a seam) | A visible defect at every slit top | The registration lace first; a person checks each real lace's parts; a lace without good parts keeps `cut` |
| Two lace slots cost draw time on phones | The budget | Slot B only bound when a second lace is chosen; the device check in step 7 |
| Hysteresis makes the shared link differ from a fresh load | Two customers see different motifs for the same mm | The count is in the design record (step 5) |
| A 100 mm hem band overlaps the slit band near the corner | Seams in the field deep in the band | The trim-field checks report deep seams; the mitre is the nearer edge |

## 7. Decisions needed before the go-ahead

1. **Laces at once:** at most **two different laces** on the garment (proposed), or one per group (four slots: more texture units and draw time).
2. **The repeat rule:** hysteresis band **±6 %** (proposed; StepA fits within ±5 %, ±10 % on short trims). And should the neck get whole repeats at all? Today a motif is centred at the centre front and the corners cut motifs.
3. **The border band depth:** about **100 mm** on the hem trims (proposed), enough for the test border's 80 mm band; real border fabrics can be deeper (daaman borders reach 300 mm).
4. **End pieces:** made from the band by script for now (proposed), or wait for photographed ends.
5. **Lace classes:** the list `insertion, edging, border, gota, zari, pearl, mirror, latkan` (proposed). Which of the 6 current laces is which, if not as step 1 proposes?
