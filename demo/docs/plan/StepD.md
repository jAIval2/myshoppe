# Plan: StepD — necklines and sleeves as layers that move between looks

Status: **draft** (2026-11-24, rewritten after the prototype of §2), waiting for the owner's go-ahead and the decisions in §8.
Read first: `docs/breather.md`, `docs/formats.md`, `DedhD.md` §5 (the anchored model), `docs/images.md`, and §2 of this plan (what the prototype showed).
Base: branch `stepB-stepC` (`7109edb`). Scope: the **torso view** of two looks, the straight kurta (plates in all 4 views) and the anarkali (photo and its edits in `silhouette/sources/pending/`); the neckline templates also in the kurta's neck and sleeve views. Parts in the close views (neck, sleeve) are the next plan. **No 3D, no pan, no zoom.**

**Why this plan matters for the portal.** A view today is one photo of one finished garment, and the torso view shows the neck and both sleeves at once: a photo per option multiplies (look × neckline × sleeve, about 350 photos for 5 looks). StepD builds a view from layers instead, and makes each neckline and sleeve style **once**, then places it on any look:

```
  sleeve part      (bell, puff, …)      made once, from one edit, on any look
  neckline part    (mandarin collar)    made once, from one edit, on any look
  neckline cut     (V, square, boat …)  numbers in cm: no image
  garment without sleeves               one edit per look
  bare dress form                       one edit per look
```

A neckline template is also what the atelier needs: a curve in cm from the centre front and the neck point.

## 1. Final expected behaviour

**What the customer sees**
1. **Any look, any neckline, any sleeve style, any length**, in the torso view, with any fabric and lace. No combination is photographed.
2. **Necklines that remove fabric** (round / scoop, V, square, boat, sweetheart, keyhole) as cuts with their handles (depth, width, a shape value). Where a cut uncovers the form, the form shows as photographed in the same light. The same shape in the kurta's torso, neck and sleeve views.
3. **Necklines that add fabric** (the mandarin collar) as parts, sitting on the look's own neck.
4. **Sleeve styles** as parts: straight (the photo), bell, puff (decision 4); sleeveless (the garment without sleeves); each with its shadow on the bodice.
5. **Sleeve length** on the styles with an open end (straight, bell), with stops; below a shorter sleeve the form's arm or cap and the garment's side show.
6. **Lace** on every new edge (corners at V and square points; whole motifs while dragging).
7. Everything StepA–C delivered still holds; the look's own neck and sleeves render exactly as today.

**What the data is**

8. **The neckline library** (`assets/necklines/<shape>.json`) in the front piece's cm (origin: the centre front on the neck-point line), with parameters, ranges, stops, corners and their sources. One generator in `necklines.js`, a Python twin for the checks.
9. **Parts** (`assets/parts/<name>/`): the source look and view, the cut-out (RGBA), its shade split into folds and broad light, its anchors in the source plate's px and in piece cm, its trims, its sidecar (kind `sleeve` | `collar` | `decal`, length range or `null`, the source edit and its intake numbers).
10. **Each host plate** gains its **under layers** (`under.jpg`: crops of the bare-form and sleeveless edits, one atlas) and, per part it can take, the part **placed for that host** (the warped cut-out, its relit shade, its shadow on the host, its zones and trims), built offline (decision 8). `plate.dat` version 5 (`BSP5`).
11. **Each look record** lists the necklines and parts it allows, with ranges clipped to its blank (a cut cannot add fabric), source `computed`.
12. **The design record** gains `neck.shape` (+ values), `neck.part` (mandarin or none), `sleeve = {style, lengthCm}`; the URL `?neck=v&neckDepth=…`, `?collar=mandarin`, `?sleeve=bell&sleeveLen=45`.
13. `docs/formats.md` covers all of it.

**How exact**

14. A neckline template agrees in cm between the kurta's views within the photographed neck's spread (step 0) + 2 mm.
15. A placed part keeps its shape: its width-to-height ratio within ± 5 % of the source's (the prototype's stretch bug, §2.3).
16. A placed part's join: the anchors fit within 8 px (sleeve: the host's own sleeve outline; collar: the host's neckline).
17. An edit passes the **edit intake** (§2.1): used as it is when it lines up (≤ 1 px), corrected (similarity + tone) when it was redrawn and the join still fits, else regenerated.

## 2. What the prototype showed (2026-11-24)

Offline, in Python, on the owner's edits; the scripts are in `silhouette/parts/prototype/`, the figures in `plan/img/StepD-proto-*.jpg`.

### 2.1 The owner's edits (the image tool)

| Edit | Of | Lines up | Outside the edit |
|---|---|---|---|
| anarkali without sleeves | `torso-anarkali.png` | 0 px at 7 landmarks (correlation 0.97–1.00) | garment 2.2 / 255; wall and stand 4–8 % brighter |
| anarkali bare form | `torso-anarkali.png` | **redrawn**: 17 px lower, another stand | after the 17 px shift the form's neck fits (6.5 / 255, 2 % brighter) |
| anarkali puff | `torso-anarkali.png` | 0 px | garment 2.0–2.4; wall 3–8 % brighter |
| anarkali V-neck | `torso-anarkali.png` | **zoomed** × 1.84 on the upper body (cap 1.82, empire seam 1.86; correlation 0.98–0.99) | a clean close-up: usable for comparison |
| kurta bell, boat, mandarin | `torso-straight.png` | 0 px | 1.7–2.8 / 255 |

**Rule:** a partial edit (sleeves, neckline, collar) keeps every other pixel; removing the whole garment makes the tool redraw the image, which a similarity and a tone match correct. The mandarin edit also opened a front slit (placket); it comes with the part.

### 2.2 Placing a sleeve from another look (the kurta's bell on the anarkali)

The two looks were photographed in **different setups**: another dress form (the kurta's has arms, the anarkali's only shoulder caps), hard warm side light against soft window light, another stand. It works once the part is fitted to the host, not to two points:

1. **The cut-out.** Where the edit lines up with its base, the part is the difference between them. Where it does not (the bell's base had other sleeves), the sleeve is traced from the plate's own edges (the armhole and the body side, `views/torso.py`) outwards to the wall, row by row (the wall is smooth; brightness alone fails where the lit sleeve and the wall match, so colour is used too: the linen and the wall are warmer than the cloth).
2. **The host's anchors from its own pair.** The host's photo with sleeves against its sleeveless edit gives the host's own sleeve outline: where a sleeve sits on that form, and how the light falls on it.
3. **Placement:** one uniform scale and rotation per sleeve (least squares over the shoulder point, the underarm, the outer edge to the elbow and the wrist), plus a small bend near the shoulder so it wraps the form's cap, held at zero below the elbow.
4. **Normalisation (relight):** keep the part's folds (its luminance over its own broad light, a 45 px normalised blur), soften the source's hard light (folds ^ 0.7, highlights capped to 0.75–1.06), and multiply by the **host sleeve's** broad light, in the host's colour.
5. **Shadow:** the host's own sleeve shadow on the bodice (its photo ÷ its sleeveless edit), above the elbow.

| | First try (2 anchor points) | Free warp | Final |
|---|---|---|---|
| Light | kurta's (flat, too bright on the right) | host's | host's, folds softened |
| Form's cap | a sliver of bare form shows | covered | covered |
| Shape (width ÷ height vs the source) | kept | **left 0.81, right 1.43** (sheared) | left 0.90, right 1.08 (measured outside the armhole line) |
| Scale, rotation | 0.80, 0° | anisotropic | 0.918 / 0.910, −0.2° / −2.2° |

### 2.3 Placing a collar from another look (the kurta's mandarin on the anarkali)

- **Anchors:** the kurta's neckline (from its plate) onto the anarkali's, which was **measured**, column by column, where the form's warm linen turns into the cooler cloth (linen R−B 35–41, cloth 17–22). Reading it by eye put it 10 px too high and left a crescent of bare form at each side of the collar.
- **Placement:** scale 0.878, rotation 1.6°, the neckline fits within 6.3 px, plus a bend along the neckline only.
- **Cover strip:** the edit replaced the kurta's neck band with the collar, so the part carries 55 px of the kurta's cloth below the collar, fading over 32 px, to cover the host's own neck band.
- **Light:** as the sleeves, with the host's light around the neck; the source's colour cast halved; the slit keeps the form's colour.

### 2.4 Open after the prototype

- The right bell's outer edge is ragged near the shoulder and elbow (its cut-out was traced at half size).
- The parts were placed on a white garment; with a fabric on, the page uses the shade, which hides most remaining light differences, but this was not tried.
- The puff (anarkali) on the kurta needs the kurta without sleeves (§9).

## 3. What is wrong now (read in the code, 2026-11-24)

| # | Finding | Where | Effect |
|---|---|---|---|
| N1 | **The live neck only scales the one photographed curve** | `testing.html` `neckCurves` (line 1499) | No V, square, keyhole |
| N2 | **The neck is placed in px per view**, in the torso and neck views only; the sleeve view has no `decisions.neck` | `neckCurves`; `sleeve-straight` plate | A V in the torso view, a round neck in the sleeve view |
| N3 | **Reach:** 70 mm deeper and 25 mm wider per side than the photo | `torso-` and `neck-straight` plates | No boat neck, no deep V |
| N4 | **The reveal is a flat toile colour × the old fabric's shade** | `testing.html` lines 940–942 | A deep cut shows a flat patch |
| N5 | **Lace corner pieces are data, not drawn** | StepC open item | A V's point cuts the lace |
| N6 | **A plate is one photo**: the sleeves and the neck are baked into it; nothing shows what is under them | `plate.dat` | No other sleeve, no other collar |
| N7 | **15 samplers are bound**; WebGL2 guarantees 16 | `testing.html` lines 563–566, 1724 | Layers need an atlas |
| N8 | **The option images** of `images.md` assume a photo per option per look | `images.md` | 27 images, no combinations |
| N9 | **The brief mixes sleeve style and length** (Sleeveless, Short, Three-quarter, Full) | `web/src/features/bespoke/data.ts` | The storefront's field should split (after this plan) |
| N10 | **The anarkali has no torso plate** (its view module is a template; the photo arrived 2026-11-24) | `silhouette/views/` | No host plate for the anarkali |

## 4. Rules

- **Branch `stepD` from `stepB-stepC`.** One commit per step, results in `plan/StepD-results.md`; a FAIL is written with its number.
- **Lighter verification** (the owner, 2026-11-23): offline gates each step; one render run per step that changes the render, with a short-lived server stopped in the same command.
- **Nothing is edited by hand** in a plate, a part, a sidecar or a library file: change a view, a record, a tool or a source, then rebuild.
- **Every number has a source** (agreed, measured, fitted, computed, assumed).
- **A person approves** what a render shows. The agent's look is not the approval.
- **The owner's images are edits of a base image** (§9), each through the edit intake.
- **A part is placed by a uniform scale and rotation plus a local bend at its join**, never a free warp (§2.2); the shape check (item 15) gates it.

## 5. Steps

### Step 0: Baseline, the tools from the prototype, the edit intake

**Do:**
1. Branch `stepD`; `StepD-results.md` with §2 as its first section. The prompts of §9 into `image-prompts.md` (section D) and their rows into `images.md`; the 27 option images marked **held**.
2. **`silhouette/checks/edit_intake.py <base> <edit>`** (from `prototype/drift.py`): the offset by phase correlation on a grid of blocks; the global scale and shift when the edit was redrawn or zoomed; the difference outside the edit; the tone change; the highlight rule; a difference image. It writes the fitted correction (source `fitted`) into the view file.
3. The intake of every edit in `pending/` (§2.1), written to the results.
4. **The neck in cm:** each kurta view's photographed neck edge through its front frame into front-piece cm; the spread between views (the floor for item 14). The sleeve view's centre-front point (StepB open item 1), so its frame can carry a neckline.
5. **Baseline sheet:** the kurta's neck at its 3 stops and its sleeves, in the torso, neck and sleeve views.

**Accept:**
- [ ] `edit_intake.py` passes a base against itself, fails a shifted copy, and reproduces the §2.1 numbers.
- [ ] The neck spread table; the sleeve view's front-frame residuals before and after its centre-front point.

### Step 1: The anarkali's torso plate (N10)

**Do:**
1. Measure `torso-anarkali.png` (`annotate.md`, with `_kit.py`): zones, frames, trims, landmarks (neck points and centre front, shoulder points, underarms, cuffs, hem, slit), scale from the neck width (158 mm, assumed as for the other looks). Move it from `pending/` to `sources/`; `images.md` row 10 to **have**.
2. **Its neckline by colour** (§2.3): the measuring tool that found the neckline column by column becomes part of `annotate.md`'s helpers, so the neck edge is measured, not read.
3. The plate builds and passes its checks (`plate.py check`, `page-check`).

**Accept:**
- [ ] The anarkali torso plate passes the invariants, or each FAIL is listed with its number; a person approves its annotate sheet.

### Step 2: The under layers (N4, N6, N7)

**Do:**
1. **Bare form** (`*-under-form`) and **garment without sleeves** (`*-under-sleeveless`) for each host: corrected by their intake (the anarkali's bare form by its 17 px shift and tone), cropped to the neck area and the sleeve areas, packed into `under.jpg`; their rectangles and corrections in `plate.dat` (`BSP5`).
2. **The host's own sleeve outline and light** (§2.2 step 2): from its photo against its sleeveless edit; written into the plate as the sleeve anchors (shoulder point, underarm, the outer edge to the elbow, the wrist) and a broad-light map of each sleeve.
3. **Annotate the sleeveless layer** where the sleeves hide it: the front zone's side and armhole edges (with frames fitted to the garment record), the form's arm or cap as an occluder, the armhole as a trim (`layer: under`).
4. **The page:** the atlas appended to the photo texture (N7); the layers drawn in order: form, garment (cut by the neckline), parts.

**Accept:**
- [ ] With no option chosen, both plates render pixel-identical to step 0 (the kurta) or to the step 1 plate (the anarkali).
- [ ] Sleeveless on both looks, with a fabric: a sheet for a person.

### Step 3: Neckline cuts (N1–N3)

**Do:**
1. **The library** (`assets/necklines/`): `round`, `v`, `square`, `boat`, `sweetheart`, `keyhole` (decision 1); the look's own neck stays `photo` on today's code path.
2. `necklines.js` and `silhouette/pipeline/necklines.py`, with a parity check.
3. **The blank clip:** each template's range on each look where it stays below the photographed neck and inside the shoulders (source `computed`).
4. **The neck area grows** to the library's widest and deepest curve; the plates rebuild.
5. **The page:** `state.neck = {shape, …}`; a pixel is cut when its fabric (u, v) lies inside the template; the edge in px by inverting `frameUV`; the edge band follows the new curve by arc-length share; what is cut shows the bare-form layer, with the edge's shadow (1–2 mm).
6. The kurta's torso, neck and sleeve views and the anarkali's torso view.
7. **The comparison:** the anarkali V edit (scaled by its intake's 1.84) beside the `v` template set to its measured depth and width; the kurta boat edit beside the `boat` template.

**Accept:**
- [ ] `photo` at its 3 stops: pixel-identical to step 2.
- [ ] Each template agrees between the kurta's views within the step 0 spread + 2 mm; the parity check passes.
- [ ] A person judges the V and boat comparisons and a sheet of the 6 shapes on both looks.

### Step 4: Lace on the new necklines (N5)

**Do:** corner pieces drawn at each listed corner (V tip, square corners, sweetheart notch); the keyhole's own trim with `piece` ends; `xview_lace.py` on the new trims.

**Accept:**
- [ ] With the registration lace: a whole "C" motif at each corner, whole motifs between, no jump while dragging the V (the scripted drag of StepC step 5).

### Step 5: Parts (N6)

**Do:**
1. **`silhouette/parts/make_part.py <edit> --kind sleeve|collar`** (from the prototype): the cut-out (§2.2 step 1, at full size: the difference to its base where it lines up, else the plate's edges and the wall trace), its folds and broad light, its anchors, its trims, its sidecar.
2. **`silhouette/parts/place_part.py <part> <host plate>`**: the placement (§2.2 steps 3–5, §2.3), the shape check (item 15), the join check (item 16); the placed part written into the host's plate (decision 8).
3. **The parts of this plan:** the bell (from the kurta), the puff (from the anarkali), the mandarin collar (from the kurta); each placed on both looks.
4. **Sleeve length:** a cut across the placed sleeve's frame at `lengthCm` from the shoulder point, on straight and bell (decision 5); the cuff trim moves to the cut; below it, the sleeveless layer.
5. **The page:** the style and length pickers, the collar switch; `state.sleeve`, `state.neck.part`.

**Accept:**
- [ ] Every placed part passes the shape check (± 5 %) and the join check (≤ 8 px).
- [ ] A sheet for a person: each part on each look, alone and combined (bell + mandarin, puff + V), with the white garment and with 2 fabrics. The person's verdict per part is written down.

### Step 6: Formats, person and device checks, close

**Do:**
1. `docs/formats.md`: `BSP5` (layers, placed parts), the neckline library, parts and their sidecars, the design record.
2. `images.md`: the option images replaced by the edit list per look (§9); what still needs a photo.
3. **Person:** the sheets of steps 1–5. **Devices:** `?perf=1` on the phone and the laptop with a V, a bell at elbow length, the mandarin and two laces.
4. Docs: `breather.md`, `render.md`, `plate.md`, `annotate.md` (the layers, the neckline by colour), `DedhD.md` §5 and §11.7. The prototype folder is removed once its tools are in. Results closed with the open items.

**Accept:**
- [ ] All offline gates pass or every FAIL is listed; the results have one section per step.

## 6. Out of scope (later)

- **Parts in the close views** (neck, sleeve): the same tools; each part needs its view's edit or a placement across views.
- **More sleeve styles** (flutter, bishop, cap) and **collars** (band, shirt, Peter Pan): the same pipeline, one edit each.
- **The potli button and loop** (a decal at a template's anchor): after a keyhole edit.
- **Sleeves that move the armhole** (dropped shoulder, raglan, kimono): they need their own sleeveless base.
- **A banded style's length** (puff, bishop): moving the band, as StepC moves a lace's end piece.
- The back view; asymmetric necks (the angrakha's wrap); hem and slit lengths as cuts.
- The lehenga and sharara as hosts: each needs its sleeveless and bare-form edits (§9, batch 3).

## 7. Risks

| Risk | Effect | Mitigation |
|---|---|---|
| A part from another setup keeps its source's light | Glossy or flat patches | The relight of §2.2; the person's verdict per part; a part that fails is made again as an edit of that host |
| The tool redraws an edit | It does not line up | The intake: similarity + tone, and only the crop at the join matters (§2.1) |
| A free warp distorts a part | A stretched sleeve (§2.2: 1.43) | Uniform scale and rotation only; the shape check |
| A host's anchors read by eye | A gap at the join (§2.3: a crescent of bare form) | Measured anchors only (plate edges, the colour scan, the photo ÷ sleeveless outline) |
| The cut-out is rough | A ragged edge | Full-size cut-outs from the plate's edges; a person looks at the edges at 2× |
| Texture units (15 of 16) | No unit for layers | The atlas in the photo texture |
| Placed parts per host grow the download | Load time | Only the crops; placed parts built offline as JPEG + alpha; the device check |

## 8. Decisions needed before the go-ahead

1. **The neckline list:** round / scoop, V, square, boat, sweetheart, keyhole as cuts; mandarin as a part (proposed).
2. **The blank:** keep each look's photographed neck as the blank (proposed); no template higher than it.
3. **The second look:** the anarkali (proposed: its edits are in hand), in place of the lehenga.
4. **The sleeve styles of this plan:** straight, bell, puff, sleeveless (proposed); flutter, bishop and cap later.
5. **Sleeve lengths:** stops short 18, elbow 33, three-quarter 45, full, in cm from the shoulder point, on straight and bell (proposed, assumed until the atelier gives them).
6. **The 27 option images of `images.md`:** held (proposed).
7. **The mandarin's front slit:** keep it (the edit has it), or a fresh edit of a closed mandarin.
8. **Where a part is placed:** offline, built into each host plate (proposed: the maths stays in Python and checkable, the page only draws layers), or live in the page (fewer files, more page code).

## 9. Images

**In hand** (`silhouette/sources/pending/`, 2026-11-24, intake in §2.1): `torso-anarkali.png`, `torso-anarkali-under-sleeveless.png`, `torso-anarkali-under-form.png`, `torso-anarkali-sleeve-puff.png`, `torso-anarkali-truth-vneck.png`, `torso-straight-sleeve-bell.png`, `torso-straight-part-mandarin.png`, `torso-straight-truth-boat.png`.

**Still needed for this plan** (each an edit; attach only the named image; same size as it; the rules of `images.md`):

| # | File | Edit of | For |
|---|---|---|---|
| 1 | `torso-straight-under-sleeveless.png` | `torso-straight.png` | step 2: the kurta without sleeves (the puff goes on it) |
| 2 | `torso-straight-under-form.png` | `torso-straight.png` | steps 2–3: the form under the kurta's neckline cuts |
| 3 | `neck-straight-under-form.png` | `neck-straight.png` | step 3: the same, neck view |
| 4 | `sleeve-straight-under-form.png` | `sleeve-straight.png` | step 3: the neck in the sleeve view |

**Batch 3 (later hosts):** for the lehenga and the sharara, the same two edits of their torso photo (sleeveless, bare form).

**Prompts:**

Rows 2–4 (`under-form`):
```
Edit this photo. Remove the garment completely and show the bare dress form underneath it, exactly where it stands now: the same natural-linen cover, its seams and tape lines, its neck and wooden cap, and its arms or shoulder caps as they are under the garment. Change nothing else: the same camera, framing, stand, wall, floor and light. The form's shading follows that light, with no new shadows from the removed garment.
```

Row 1 (`under-sleeveless`):
```
Edit this photo. Remove both sleeves: the garment becomes sleeveless, with a narrow turned and top-stitched edge along the armhole seam. Do not change the garment's body at all: it stays a straight, loose kurta with straight side seams, no waist seam, no flare, the same length and side slits. Where the sleeves were, show the dress form's arms or shoulder caps as they are, and the wall. Change nothing else: the same camera, framing, stand, wall, floor and light.
```

A new sleeve style or collar later: one edit of any look's torso photo that changes only that part (*"Change only both sleeves into …"*, *"Add a … collar to the existing neckline …"*), then `make_part.py`.
