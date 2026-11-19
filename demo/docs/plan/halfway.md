# Plan: halfway — live neckline with pivot points, then the showcase

Status: **in progress**. Branch `halfway`, worktree `../myshoppe-halfway`.
Compare: **http://localhost:8000/testing.html** (branch `polish`, the reference) and **http://localhost:8100/testing.html** (this worktree).
Product: a **visualiser** for customers, and an easier life for the owner. Not a factory tool. **4 fixed views, no 3D.**

## 1. Goal

1. The customer **drags pivot points** on the neckline, in the fixed neckline view, to set its depth and width. The lace and the stitch line follow. The torso view shows the same neckline.
2. The page **presents the journey** well: steps, transitions, a review screen.

Out of scope here: new swatch and lace photos, deep-neckline photos, hem and sleeve length controls, 3D. They come later.

### The Amber model, as the data structure

| Amber | Here |
|---|---|
| Topology | Zones, seams, trims, draw order (`zones.json`) |
| Coordinates | The curves of each view, in plate px |
| Internal coordinates (Z-matrix) | **Design parameters in mm, measured from landmarks**: `neck.depthMm` (from the neck-point line, along the centre front), `neck.widthMm` |
| Restraints | Ranges and rules (depth and width inside the look's range; lace narrower than the neck depth) |
| One input deck → many outputs | One **design record** → all views |

## 2. Rules

- One step = one commit on `halfway`. Each step has a test switch for the old behaviour.
- **No new image file for each view.** The controls are numbers (uniforms and curves).
- With the controls at their default values, the render must be **pixel-identical** to port 8000 (mean difference ≤ 0.5 on the 8 polish review queries). Check with `tools/shoot_set.py` on both ports.
- Budgets: plate data ≤ 1.0 MB for each view; draw time ≤ 5 ms (normal browser); a drag must redraw at ≥ 30 frames per second on a mid-range phone.
- Review shots on port 8100: `PORT=<free port>` for the harness, because 8000 and 8100 are in use.

## 3. Steps

### Step 1: Decode only the current view (housekeeping)

**Why:** the page keeps the decoded images of all 4 views (≈ 150 MB). A drag adds redraws, and phones need the memory.

**Do:** keep the downloaded files (compressed blobs) for all views; decode only the current view; free the previous view's images after a switch.

**Accept:**
- [x] Render unchanged (8 queries, pixel-identical).
- [x] Decoded image memory ≤ 1 view (about 40 MB) after any number of switches. Measure in the browser's memory panel.

### Step 2: The neckline becomes a live curve

**Idea:** today the neckline is baked into `id.png` (the outline cuts the front zone). The front zone's **grid** already spans the neck dip (its top runs straight across the neck points), so fabric coordinates for the dip exist; they are only masked away.

**Do:**
1. `make_plate.py`: in the front zone, write `uv.png` for the **whole grid**, also inside the neck dip. Mark the neck area in `id.png` **B channel** (= 1 inside the grid but above the photographed neckline, and in a band below it for deeper settings). No new file.
2. Neckline curve in the shader: a polyline of 24 points (plate px), as a uniform array. A pixel in the neck area is fabric if it is **below** the live curve, and photo if it is above it.
3. The default curve = the annotated neckline, so the default render does not change.
4. The curve comes from **3 pivots** (§ step 4) through a fixed recipe: neck corners fixed on the shoulder line; centre-front point at `depthMm`; width scales the curve sideways around the centre front. Smooth curve through them (Catmull-Rom or a cubic Bézier, sampled to 24 points in JavaScript).
5. Test switch `?neck=baked` (the old mask).

**Accept:**
- [x] Default: pixel-identical to port 8000 on the neck and torso views.
- [x] A depth change of ± 20 mm moves the edge by the right amount in px (`mm ÷ mmPerPx`, ± 1 px).
- [x] No hole, no hairline gap at the shoulder corners for any setting in the range.

### Step 3: Area that a change reveals

| Change | What fills it |
|---|---|
| **Shallower** than the photo (more fabric) | Fabric, with the UV of the full grid. Shade: the photo's form is not a fold map, so use a smooth shade, extended from the fabric just below the photographed neckline. |
| **Deeper** than the photo (more form) | The dress form: copy the form's linen from just **above** the photographed neckline (mirror about it), with a soft shade gradient. On a plain white production background this area is the form, not the background. |

**Do:** both fills in the shader, in the neck band only. Test switch `?revealfill=0` (plain colour, to see the areas).

**Accept:**
- [ ] At the range limits, a person cannot point to the old neckline in 10 seconds (neck view, 2×).
- [x] No visible repeat or smear in the form fill.
- [x] Range limits written in the look's data, for example depth 60–140 mm. Outside the range the pivots stop.

### Step 4: Pivot points and drag

**Do:**
1. **Three handles** in the neckline view, drawn in an SVG layer above the canvas, in plate px (the same 1200 × 1600 frame):
   - **Centre front:** moves only up and down, along the centre-front line → `depthMm`.
   - **Left and right:** move only sideways, together and mirrored → `widthMm`.
   - Each handle moves on a **rail** (a short line), with ends at the range limits.
2. **Snap stops** (optional, on by default): for example 3 depths and 3 widths. The atelier sets them. A free drag is a setting.
3. **Input:** mouse, touch, keyboard (Tab to a handle, arrow keys step it, Shift + arrow for a large step). ARIA: each handle is a slider with its value in mm.
4. **The design record** in the page state: `{ neck: { depthMm, widthMm } }`. Also in the URL for testing (`?neckDepth=110`).
5. The neckline pill panel shows the values: "Depth 110 mm · Width 165 mm", and a "Reset" button.
6. Redraw only while dragging (one `requestAnimationFrame` per pointer move).

**Accept:**
- [x] Drag works with mouse, touch and keyboard; the handles never leave their rails.
- [ ] The neckline, the lace and the stitch line follow during the drag (needs step 5 for the lace).
- [ ] ≥ 30 frames per second on a mid-range phone during a drag.

### Step 5: The lace and the stitch line follow the live neckline

**Idea:** the neck trim is baked into `uv_trim.png`. With a live neckline, compute the trim in the shader instead, **in the neck area only**.

**Do:**
1. For each pixel in the neck band: the nearest point on the live curve (24 segments) → `u` = distance along the curve (cm), `v` = distance from the edge ÷ trim width. This is the same coordinate the plate maker writes.
2. Lace repeat, fit and start (polish step 4) work from the live curve's length, so the motif stays centred at the centre front at every depth.
3. The top-stitch line: a dashed line at its measured distance from the live edge (5.5 mm on the neck plate).
4. Default curve: the result must match the baked trim (≤ 0.5 px).

**Accept:**
- [ ] Default: pixel-identical to the baked trim (mean difference ≤ 0.5).
- [ ] At every setting: the lace hugs the edge, whole motifs, centred at the centre front, no seam at the neck corners.

### Step 6: The torso view shows the same neckline

**Do:**
1. Both front views read the same design record. Each view converts mm to its own px with its scale (`mmPerPx`) and its landmarks (neck points, centre-front line).
2. The torso view's neck area gets the same live curve, cut and trim (steps 2, 3, 5 on the torso plate).
3. The sleeve view (turned): the neckline is at the edge of the frame. Phase 1: keep its baked neckline and show a small note when the neckline was changed. Phase 2 (later): the same curve, foreshortened by the turn.

**Accept:**
- [ ] For 3 settings, the neck depth measured in the torso view and in the neckline view agrees within ± 3 mm.
- [ ] Switching views keeps the setting.

### Step 7: Showcase

**Do:**
1. **Journey bar** across the top: Cloth → Neckline → Sleeves → Hem → Review. Each step opens its view (one step, one view). Crossfade 250 ms; none with `prefers-reduced-motion`.
2. **Highlight:** when a lace placement or a pivot is selected, its part glows softly for about 1 second.
3. **Before / after:** hold a button (or the space key) to see the plain white garment.
4. **Swatch cards** with the real tile and the name; lace cards with a strip of the lace.
5. **Review screen:** the torso view large; a strip of the 3 close views below (rendered from the same record); the list of choices (cloth, lace, placements, neckline depth and width).
6. **Share image:** one PNG of the review screen, made from the canvases (`toBlob`), for WhatsApp or download.
7. Phone layout: the stage on top, the controls below, as one column (at ≤ 760 px wide).

**Accept:**
- [ ] A person goes through the whole journey on a phone without help.
- [ ] The review image shows the same choices as the page.
- [ ] No step takes more than 1 s to show its view after the first visit (views are preloaded as blobs, step 1).

## 4. Exit strategy

**Stop a step** and revert its commit if it fails after 2 attempts, breaks a budget, or changes the default render (port 8000 comparison). Write the reason in `halfway-results.md`.

**Fallbacks:**

| Situation | Fallback |
|---|---|
| Step 3 fill looks false at the deep end | Smaller range: the deepest stop = the photographed neckline; only shallower settings |
| Step 5 analytic trim is too slow on phones | Compute the trim on a small offscreen texture once per drag end, and show the old trim while dragging |
| Drag below 30 fps on phones | Snap stops only (no free drag); redraw on release |
| Step 6 views disagree by more than 3 mm | Use only the neckline view for the control; the torso view updates on the step change |

**Stop the plan** after 5 working days for steps 1–6. Then ship the showcase (step 7) on the current renderer.

**Always safe:** port 8000 keeps the `polish` version. Merge `halfway` into `polish` only after each step passes.

## 5. Tracking

| Step | Status | Commit | Result (`halfway-results.md`) |
|---|---|---|---|
| 1 Decode only the current view | done | (step 1) | 0 MB decoded after switches (was 161 MB); render identical |
| 2 Live neckline curve | done | (step 2) | default mean ≤ 0.009; edge move exact (±0.08 px) |
| 3 Area that a change reveals | done | (step 3) | old-edge step = the light's own change; no repeat; 10 s person test open |
| 4 Pivot points and drag | done | (step 4) | mouse, touch, keys checked with real input events; phone fps open |
| 5 Lace and stitch follow the curve | not started | | |
| 6 Torso view shows the same neckline | not started | | |
| 7 Showcase | not started | | |
