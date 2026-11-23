# StepC results

Plan: `StepC.md`. Branch `stepC` from `main` (`9f5755d`), worked in the worktree `../myshoppe-stepC` so that the owner's demo server (port 8300, the main checkout) is not disturbed. Checks run on short-lived servers on port 8301, each stopped in the same command.

## Decisions at the go-ahead (2026-11-23)

| §7 | Taken | By |
|---|---|---|
| 1. Laces at once | **A lace per line:** neck, cuffs, hem, slits may each differ, so up to 4 different laces. The placements do not change | the owner ("lace placement doesn't change, but lace can be different along different lines") |
| 2. Repeat rule | hysteresis ±6 %; the neck gets whole repeats (a motif centred at the centre front) | the plan's proposal |
| 3. Border band | 100 mm on the hem trims | the plan's proposal |
| 4. End pieces | made from the lace by rule, not from photographed ends | the plan's proposal (see step 3: a rule, not an image) |
| 5. Classes | insertion, edging, border, gota, zari, pearl, mirror, latkan | the plan's proposal |

**Design change from the plan (step 4).** The plan proposed two lace slots; four are needed. A texture array would resample every lace to one size and change its look. Instead there are four separate slots:
- each slot is a lace texture and its material map;
- the shader picks the trim's slot with a constant-index branch, which is valid in divergent control flow because every lace read uses explicit gradients (`textureGrad`);
- 15 of the 16 guaranteed fragment texture units are used.

One lace on every line therefore stays pixel-identical.

## Step 0: baseline, the registration lace, the lace cross-view check

**Done:**
- **The registration lace** (`test_prints.py lace-reg`; `?lace=reg`, not in the picker): 4 motifs of 300 px numbered 1–4, arrows to the decorative edge, a dark line at every motif boundary, a scalloped edge. Its sidecar is the first of version 2 (with `widthSrc`, `repeatSrc`, `class`, `test`).
- **`silhouette/checks/xview_lace.py`:** per lace, view and trim, the cloth length, the repeat, the anchor and what the page's fit does with it; across views, the trims with the same group and anchor.

**Baseline** (`xview_lace.py`, pearl, 4.25 cm repeat):
- the slits fit whole repeats except `slit-l` (torso 2.28 repeats, hem view 5.65): the scale is kept and **a motif is cut at the slit top**;
- the neck, cuffs and hem are centred on u = 0 with no whole repeats;
- across views the slits' counts differ (torso 4 / hem view 6, pearl), because the photos' slit lengths differ (accepted in StepB).

The phases at the shared anchors (the centre front, the hem corner) are equal by construction.

**Render** (4 views × reg on sage and pearl on mocha, all trims with the slits): no console error. [`img/stepC-step0-reg.jpg`](img/stepC-step0-reg.jpg).

**Accept:**
- [x] The baseline table and the sheet. No cross-view phase difference: the anchors are garment points. The counts differ only by the photos' lengths.

## Step 1: lace sidecar version 2 (L2)

**Done:**
- **`swatchprep/lace_sidecar.py`** (`upgrade`, `check`): version 2 adds `name`, `class`, `widthSrc`, `repeatSrc`, `materialFile`, `endRule`, and drops `widthMmNote`. `prep_lace.py` writes `widthSrc: "assumed"` for a new band.
- **The 6 AI laces upgraded:** their bands and material maps untouched; all `widthSrc: assumed`.

  | Lace | Class |
  |---|---|
  | pearl | pearl |
  | geometric | edging |
  | leaf | insertion |
  | fine | zari |
  | paisley | edging |
  | brocade | border |
- **`LACES` holds only `src` and `meta`.** The page preloads the sidecars (`laceMeta`); the name and the material map come from them.
- A lace's scale protocol in `swatchprep/README.md`.

**Measured:**
- `lace_sidecar.py check`: 7 PASS.
- The render against step 0: 8 queries (reg on sage, pearl on mocha, 4 views) **pixel-identical**.
- Fine (with its material map), leaf (mirrored) and brocade (no map) render with no console error.

**Accept:**
- [x] The render is pixel-identical.
- [x] Every lace number in the sidecars has a source.

## Step 2: the trim field without names (L3), `plate.dat` version 4

**Done:**
- **`trimPack`** in every plate (`trimfield.TRIM_PACK`): 256 cm range.
  - The main field: u = s + 128, so s within ±128 cm (was ±64).
  - The **open** field (the slits; was "slit"): two slots at s + 64 and s + 192, so ±64 cm each (was ±32), assigned by the build (`slot`, by id) from the trim's group (`slits`), not its name.
  - t: (t mm + 64) / 10.
  - `SLIT_OFF_CM`, `S_OFF_CM`, `T_OFF_MM` and `TRIM_RANGE_CM` are gone from `plate.js`, `trimfield.py` and `maps.js`; the page and `maps_check.py` read the plate's `trimPack`.
- **`BSP4`:**
  - each trim's `ends` {from, to}: `runout` | `cut` | `piece` (from today's `cut` list, or the view's own `ends`);
  - its `corners`: the line turns more than 35° within 5 mm, with the place, the angle and the side;
  - `slot` for the open field.

  At most 2 trims per open field (the build refuses more).
- **`maps_check.py`:** its slit decode had a stale hard-coded id (`sid == 6`, from before StepB's renumbering); it now takes the slot's trim from the plate.

**Corners found** (data only; nothing draws a corner piece yet):
- the torso's hem turning up into the right slit corner, at (800, 1453), −42°;
- the sleeve view's neck at its right corner, at (971, 157), −40°.

**Measured:**
- `rebuild-check` ALL IDENTICAL; `platedat --check` 4 PASS.
- `page-check` (torso, sleeve, hem), page against build:
  - uv as before;
  - main and open fields complete, no stray pixels;
  - s ≤ 0.0020 cm (limit 0.01), t ≤ 0.0196 mm (limit 0.05): one 16-bit step of the wider range.
- Render against step 1 (8 queries): mean 0.000–0.193 levels, ≤ 0.22 % of pixels over 8 levels. This is the coarser 16-bit step of the 256 cm range, not pixel-identical as the plan wrote. No console error.

**Accept:**
- [~] The render: near-identical (above), not pixel-identical.
- [x] The trim-field checks pass.
- [x] `grep` finds no trim name in the field code.

## Step 3: joins and ends from the data (L4, L5)

**Done:**
- **End kinds drawn.**
  - A `piece` end stops the field square, as a `cut` does (`trimfield.square_ends`, the same rule in `plate.js`); the page clips the lace to the last whole-motif boundary inside the end (`uPieceLo`, `uPieceHi`, from each trim's s at its ends: `Plate.trimElements` now returns `sFrom`, `sTo`). The lace's shadow is clipped with it.
  - **The slit tops are `piece`** in the torso and hem views (the view files).
  - A mirrored lace (leaf) has no motif boundary, so a piece end acts as a cut.
- **Joins drawn from the data** (`uJoinK`, `uJoinW`): where a slit (the open field) and a main trim (the hem) both reach a pixel, a `butt` lets the trim that declares it run through its own lace width, and the other stops at its inner edge. `mitre` keeps StepA's rule (the trim in front, then the nearer edge). The plates keep their `mitre`s.
  - Test switch `?joinkind=<trim>:<butt|overlap|mitre>`.
- **The end piece is a rule, not an image** (`endRule: "boundary"` in the sidecars): the lace ends on its own last whole motif. The plan's cut-out end and corner images are not made: a lace with a photographed end can add one later. This keeps the 4 lace slots of step 4 within the 16 texture units.

**Not done (deviations):**
- **`overlap` is drawn as a `butt`.** A true overlap needs the lace drawn twice per pixel, the trim behind showing through the one in front's holes; the lace block is one pass.
- **Corner pieces are not drawn.** The two corners of step 2 stay as data. The torso's hem fans its motifs where it turns up into the right slit corner (visible with the registration lace).
- **Joins between two trims of the same field** (the main field's hem and side hems) stay the build's nearest-edge mitre.

**Measured:**
- `rebuild-check` ALL IDENTICAL.
- `page-check` torso and hem: the main and open fields as step 2 (s 0.0020 cm, t 0.0196 mm).
- Pearl against step 2: the neck and sleeve views pixel-identical; torso 0.016, hem view 0.84 levels mean (the slit tops: the cut motif is gone).
- No console error.
- Sheet: [`img/stepC-step3-ends.jpg`](img/stepC-step3-ends.jpg): the hem view's two slit tops and the torso's right slit end on a whole motif ("1"); the hem / slit mitre; the same corner as a butt (test), with the hem lace's motifs 2, 3, 4 whole and the slit stopping at it.

**Accept:**
- [x] The slit tops end on a whole motif in the torso and hem views.
- [x] The mitre is unchanged; a butt renders as described.
- [ ] An overlap: drawn as a butt (above).
- [x] The trim-field checks hold.

## Step 4: a lace per line (L1)

**Done:**
- **The design record:**
  - `state.laceBy = {neck, cuffs, hem, slits}`;
  - the URL takes `?lace=<key>` (every line) and `?lace.neck=`, `?lace.cuffs=`, `?lace.hem=`, `?lace.slits=` (one line);
  - the placements (which lines carry lace) are unchanged (the owner).
- **Four lace slots,** one per distinct lace:
  - slot 0 on units 6 and 7 (as before), slots 1–3 on 9 and 10, 11 and 12, 13 and 14; 15 of 16 fragment texture units in use;
  - each trim reads its slot (`uTrimSlot`) and the slot's width, aspect, edge depth and material map;
  - the reads go through `laceTex` / `matTex`, a constant-index branch, valid with `textureGrad`;
  - a loaded lace keeps its slot;
  - the map build uses unit 14 as scratch, so the lace units are re-bound after it (`rebindLaceUnits`).
- **The lace fit, the ends and the joins** take each trim's own lace (`laceFit`; `laceMmOf`).
- **The UI:**
  - a line selector above the lace picker (All lines, Neckline, Cuffs, Hem, Slits): the picker sets the lace of the chosen line;
  - the caption, the description and the review list name each line's lace when they differ.

**Measured:**
- **One lace on every line** (pearl, 4 views): **pixel-identical** to step 3.
- **Four laces at once** (fine on the neck, leaf on the cuffs, geometric on the hem, the registration lace on the slits; 4 views): each line shows its own lace at its own width and repeat, the mirrored leaf included; no console error. [`img/stepC-step4-laces.jpg`](img/stepC-step4-laces.jpg).
- **The UI path** (a scripted click on "Hem", then on "brocade"): only the hem changed (`laceBy.hem = brocade`, the others pearl), the hem fitted with brocade's repeat (1.41 cm), and the caption lists each visible line.

**Accept:**
- [x] One lace everywhere: pixel-identical.
- [x] Each line its own lace in all 4 views; no console error.
- [ ] The device budget with 4 laces: the owner's check (step 7).

## Step 5: the repeat rule while dragging (L6)

**Done:**
- **The neckline in whole repeats** (the live neck in the torso and neck views, and the sleeve view's neck), with both corners on motif boundaries.
  - An odd count (a motif centred at the centre front) when one fits within 6 %; otherwise the nearest count (a gap between two motifs at the centre front).
  - The live neck's length is the live edge's, corner to corner. The fit runs again on every neckline change (`neckUpload` → `laceFit`).
- **Hysteresis** (`chooseN`): a count is kept while the lace stretches or shrinks by at most 6 %; past that, the nearest. This applies to the neck and to the slits' whole repeats.
- **The count is in the design record:** `state.laceN` per trim and lace; the URL carries the neck's (`?laceN=neck.pearl:5`).

**Deviation from the plan:** "an odd count always" was tried first. With pearl's 4.25 cm repeat on an 18–20 cm neckline it stretched the lace from 0.80 to 1.33. The rule above keeps it within 0.91–1.12.

**Measured** (a scripted drag, `window.__studio.setNeck`: neck width 132 → 194 → 132 mm in 2 mm steps; the count logged at each):

| View, lace | Counts | Stretch (fit) | Changes |
|---|---|---|---|
| neck, pearl | 4, 5 | 0.908–1.124 | 4 → 5 at 158 mm going up, 5 → 4 at 156 mm going down: once per crossing |
| torso, pearl | 4, 5 | 0.907–1.123 | at 172 / 170 mm, once per crossing |
| neck, geometric | 11–14 | 0.940–1.056 | up at 150, 170, 188; down at 176, 158, 142: a 6–12 mm band between the up and down thresholds, no flicker |

**Render:** the registration lace round the neck: whole motifs, motif "1" centred at the centre front; pearl on mocha. No console error. [`img/stepC-step5-neck.jpg`](img/stepC-step5-neck.jpg).

**Accept:**
- [x] The count changes at most once per threshold crossing, never back and forth.
- [ ] The torso and neck views show the same count on the neck. **Not met at the default width:** torso 4, neck view 5 (pearl). The photos' neck lengths differ by 7 % (18.4 / 19.7 cm), more than the band: the photo disagreement accepted in StepB.

## Step 6: the border fabric on the hem (L7, StepB open item 3)

**Done:**
- **The edge itself:** near a hem or a cuff (`uEdgeTrim`: the trims of the groups hem and cuffs), a border fabric's v comes from that trim's field: tile v = the band's lower edge − t / repeat, with t the distance from the edge in mm. It fades to the frame's weft line (StepB) over the last 20 mm of the field.
- **Cuffs included:** a border lies on the garment's own edge, so on the torso's sleeves it now sits on the photographed cuff, not on the record's 47 cm line (7 cm above it before).
- **The hem and cuff trims' band** is 100 mm (`bandInMm` in the torso, sleeve and hem view files), enough for the test border's 80 mm band plus the fade. The plates are rebuilt (the band is in the plate since StepB step 2).

**Measured:**
- `rebuild-check` ALL IDENTICAL; the invariants as before (StepA's closure only); the trim fields complete with the deeper band.
- `page-check` (torso, sleeve, hem): the main and open fields PASS. On the torso, under 0.1 % of the main field's pixels differ, deep in the new band at the hem's sharp bend into the right slit corner (s up to 1.47 cm, t 0.13 mm). Two parts of the edge are equally near there, and the GPU and the build break the tie differently. The check's 99.9 % rule passes.
- Border, 4 views: [`img/stepC-step6-border.jpg`](img/stepC-step6-border.jpg). The band's lower edge lies on the edge along the whole hem in the torso and hem views, **the hem view's slit corner included** (StepB: 4 cm off), and on the cuffs in the torso and sleeve views. No console error.

**Accept:**
- [x] The band's lower edge on the hem along the whole hem in the torso and hem views, the slit corners included: by construction from the field (t = 0 is the edge), and seen on the sheet.
- [x] The trim-field checks hold with the deeper band.

## Step 7: formats, docs, close

**Done:**
- **`docs/formats.md`:** `BSP4` (`trimPack`, `field` / `slot`, `ends`, `corners`, the bands, the joins as drawn); the lace sidecar version 2 (§3b) and the fit on a trim; the design record's `laceBy` and `laceN`; the border fabric on the edge; versioning. The coverage check (every key of the 4 plates and the 7 lace sidecars against the document): none undocumented.
- **Docs:**
  - `breather.md`: the branch, the test switches, §8, §9 (the open items), glossary (open field, piece end, lace slot, hysteresis);
  - `render.md` §11: the StepC entry;
  - `plate.md`: the tool limits;
  - `swatchprep/README.md`: lace sidecar v2 and the lace's scale protocol;
  - `DedhD.md` §11.7: C done.
- **Merged** into `main` (a fast-forward), not pushed. The worktree `../myshoppe-stepC` removed.

**Final gates:**

| Gate | Result |
|---|---|
| `rebuild-check` | ALL IDENTICAL |
| `platedat.py --check`, `garment.py --check`, `lace_sidecar.py check` | 4, 1, 7 PASS |
| Frame parity | ≤ 2.8 × 10⁻¹⁴ cm on all 4 |
| `plate_invariants.py` | neck ALL PASS; torso, sleeve, hem: only StepA's closure items |
| `xview_check.py` | 2 PASS, 8 ACCEPTED, 1 FAIL (shoulder-r: the photo split of StepB, each view within 3 mm of the record) |
| `xview_lace.py` | the phases at the shared anchors equal; the slits' counts differ by the photos' slit lengths (accepted) |

**Not done here (the owner's):** the person checks of the sheets (steps 0, 3, 4, 5, 6); the device check with 4 laces at once (`?perf=1`, phone and laptop).

**Open items:**
1. **Corner pieces:**
   - the corners are data (`corners`), not drawn;
   - the torso's hem fans its motifs at its bend into the right slit corner;
   - a V or square neckline will need them.
2. **An `overlap` join** is drawn as a `butt` (one lace pass per pixel); joins between two trims of one field stay the build's mitre.
3. **The lace widths are assumed** (all 6 AI laces, `widthSrc: assumed`); the protocol is in `swatchprep/README.md`.
4. **The neck's count differs** between the torso and neck views at the default width (pearl: 4 / 5): the photos' neck lengths differ by 7 %.
5. **Edging laces with an unclean key** (fine, leaf) stay insertion (L8: assets).
6. **From StepB:** the sleeve view's centre-front point; the hem view's fold to confirm; StepA's closure items.
