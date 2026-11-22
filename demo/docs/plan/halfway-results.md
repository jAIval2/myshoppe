# Results: halfway plan

Closed. The silhouette method is replaced by `StepA.md` (one `plate.dat` per view, typed edges, fabric frames, maps built on the page).

Plan: `halfway.md`. Branch `halfway`. Reference: port 8000 (`polish`).

## How it was checked

`tools/cdp_shot.mjs` drives headless Chrome (SwiftShader) through the DevTools protocol. It saves the **WebGL canvas itself** (`toDataURL`, exact pixels) once the page says the frame is drawn, and records every console error. This includes the shader compile log, so a shader that does not compile shows up as an error. `tools/canvas_diff.py` compares two runs canvas by canvas: the mean |difference| over RGB, the share of px that differ by more than 8 levels, and the max. The plan's rule is a mean ≤ 0.5.

Before any change, port 8000 and port 8100 gave 0.000 on all 8 polish queries, so the harness is deterministic. The shader compiles in Chrome (SwiftShader): the polish plan's open check "the shader has not been compiled since step 4" is closed.

Times reported by SwiftShader are not real. The draw-time and phone-frame-rate budgets still need a real browser (see "Open checks").

## Step 1: Decode only the current view

The page now keeps the **downloaded files** (blobs) of every view and of every swatch. It decodes only the view it shows, and closes each decoded image as soon as it is on the GPU. The test switch `?decode=all` keeps the decoded images (the old way).

| | Decoded images held after 12 view switches |
|---|---|
| `?decode=all` (old) | 160.6 MB (23 images: 4 views, swatches) |
| new | **0 MB** (peak during a switch: one view, about 38 MB, for the time of the upload) |

The numbers come from the page's own count of open `ImageBitmap`s (`__studio.decodedBytes()`), not from a memory panel. The GPU keeps one view's textures, as before.

- Render: 8 of 8 queries identical to port 8000 (mean 0.000, max 0).
- Open: the same check in a real browser's memory panel.

## Step 2: The neckline becomes a live curve

**Plate** (`make_plate.py`, neck and torso plates only):
- In the neck area, the front zone's UV is written for the whole grid, the dip included.
- `id.png` B = 1 marks the neck area: the cut garment plus the dip under the corner line, inside a rectangle that reaches 70 mm deeper, 25 mm wider on each side and 30 mm of band. The 1 px rim that the grid quads add beyond the outline is left out; it put a row of fabric on the shoulder line.
- In the dip, the shade carries the garment's shade 8 px outward.
- `plate.json` has a new `neck` block: the photographed edge, the trim centre, the grid top, the centre front, the reach, and the plain fill colours.

Only these channels changed: id B, uv in the dip, and shade outside the garment. No garment pixel of R, G, uv or shade changed. Plate data with base.jpg: neck 840 KB, torso 723 KB.

**Look data:** `assets/looks/straight-kurta.json`:
- depth 20–100 mm, default 40.9 mm (the neckline-view photo);
- width 132–194 mm, default 158 mm;
- snap stops.

**Recipe** (in the page, per view):
- Width scales the photographed edge sideways around the centre front.
- The corners then sit on the grid top (the shoulder line).
- Depth scales the dip below the corner line.
- Each view turns a change in mm into its own px.
- Away from the default, the shape blends (over the first 8 % of change) into a centripetal Catmull-Rom curve through the photographed points. Scaling the polyline itself turned its small kink at the centre front into a point at 2.4× depth.
- 24 points are picked from a dense curve (Douglas–Peucker order) for each shape. At the default they are the photographed vertices, so the default is exact (torso: 0.16 px, 46 vertices → 24).

**Shader:** in the neck area, the garment is the part below the live edge (signed distance, analytic edge coverage). Where the photo shows garment and the setting shows form, the plain form colour shows; where the photo shows form and the setting shows fabric, fabric shows at flat light (step 3 replaces both). `?neck=baked` gives the old mask.

| Check | Result |
|---|---|
| Default, 8 queries vs port 8000 | PASS: mean 0.002–0.009 on neck and torso, 0.000 on sleeve and hem. The only px that differ are the neckline edge itself (analytic edge instead of the 3×3 count). |
| Depth +20 mm / −20 mm, CF edge move | neck: +65.66 / −65.66 px (expected ±65.66); torso: +22.20 / −22.20 px (expected ±22.28). Within ±1 px. |
| Corners at the 4 range ends (both views) | no hole, no hairline (`img/halfway-step2.png`: shallow-narrow, deep-wide, shallow-wide, deep-narrow, torso shallow-narrow and deep-wide; plain fills) |

The depth minimum is 20 mm, not 30 mm, so that −20 mm can be tested. In the torso view that gives a 4 mm dip, because the torso photo's neckline is 25 mm deep against 41 mm in the neckline photo (step 6).

## Step 3: Area that a change reveals

All in the shader, in the neck area only. `?revealfill=0` gives the plain colours of step 2. Where the edge has not moved (under 0.5–3 px), the photo shows as it is, so the default does not change (8 queries: same numbers as step 2).

| Area | Fill |
|---|---|
| **Edge band**: 9 mm along the live edge | Shade (and, with fabric off, the photo) from the **photographed edge band at the same distance from the edge**, at the matching place along it. The edge roll and the top-stitch at 5.5 mm move with the edge. |
| **More fabric** (shallower): in or above the photographed band | The shade just inside the photographed band, averaged over 12 mm along the edge. Smooth, so no fold of the old edge stays. A 5 mm crossfade to the photo's own shade further in. |
| **More form** (deeper) | **Colour:** the photo's form just above the old edge at that place, blurred. When it strays more than 15 % from the patch mean, an added share of the patch colour pulls it back; scaling a dark warm colour up turned it orange. **Detail:** a clean square of the form (`plate.json neck.formPatch`, chosen beside the centre-front tape) hex-tiled, as for the fabric in polish step 7. **Centre-front tape:** the photo's column just above the old edge, averaged over 4 heights (the line stays, the weave goes), carried straight down. **Contact shade:** 0.84 at the new edge, gone after 5 mm. The photo's own collar shadow (4 mm above the old edge) is replaced, with a 4 mm fade. |

What did not work, kept for the record:
1. Mirroring the photo about the old edge, folded into an 8 mm band, gave visible bands and dashes in the tape.
2. Using the patch mean colour made the fill 6–13 levels too light, because the patch is on the lit side.
3. Scaling the local colour up made the shaded side orange.

`tools/reveal_metrics.py` measures a render of a deeper setting with the lace off:

| Render | Step across the old edge (6 mm below − 6 mm above) | Same 12 mm step in real form (6–18 mm above) | Detail repeat peak (fill / real form) |
|---|---|---|---|
| neck, depth 100, toile | +7.9 levels (mean \|·\| 10.6) | +6.4 (mean \|·\| 15.2) | 0.18 / 0.25 |
| torso, depth 100, width 194, toile | +9.2 (9.4) | +11.7 (16.7) | (square too small at 0.9 mm/px) |

The step across the old edge is the size of the light's own change, and the fill's detail has no stronger repeat than the real form. Review images: `img/halfway-step3.png` (neck deep, neck shallow, neck deep-wide in mocha, neck at 65 mm narrow in sage, torso deep-wide, torso shallow-narrow) and `img/halfway-step3-2x.png` (neck deep-wide at plate scale).

- [x] Range limits written in the look's data (`assets/looks/straight-kurta.json`): depth 20–100 mm, width 132–194 mm. The page clamps to them, and the pivots (step 4) stop there.
- [x] No visible repeat or smear: no repeat peak (0.18); smear checked at plate scale.
- **Open (a person):** "cannot point to the old neckline in 10 s". By my own look at plate scale, I could not point to it. The number above is the stand-in.
- **Known:** on the torso plate the photo's white garment shows in a 2–4 px sliver along the shoulder line, above the grid top. It is in the default render too: the plate fit at the shoulder, not this step. With a wide setting it now sits next to the form fill near the corner.

## Step 4: Pivot points and drag

The neckline view has three handles in an SVG layer over the canvas (viewBox = the 1200 × 1600 plate frame), each on a rail drawn between the range limits, with the snap stops marked (`img/halfway-step4.png`).

| Handle | Moves | Sets |
|---|---|---|
| Centre front | down and up along the centre-front line only | `depthMm` |
| Left and right | sideways only, mirrored, along the grid top (the shoulder line) | `widthMm` |

- **Design record:** `state.neck = { depthMm, widthMm }`, clamped to the look's range. The record goes into the URL when a drag ends (`?neckDepth=65&neckWidth=194`), and the page reads it from there.
- **Snap:** on by default ("Snap to stops"). Within 2.5 mm of a stop the value goes to the stop. With snap off, every value in the range can be set.
- **Keys:** Tab to a handle. The arrow keys move it 1 mm in the direction it moves (down = deeper, outward = wider); Shift + arrow moves 10 mm; Page Up / Down jumps to the next stop; Home / End go to the range ends. Each handle is a `role="slider"` with `aria-valuetext` "Depth 65 mm".
- **Panel:** "Depth 65 mm · Width 194 mm", Reset, and Snap to stops. In the other views it says to open the Neckline view.
- **Redraw:** at most one redraw per animation frame during a drag (pointer events are merged); nothing is drawn when no drag is running.

Checked with real input events through the DevTools protocol (`tools/cdp_shot.mjs --input`):

| Input | Result |
|---|---|
| Mouse: centre handle 20, 40, then 400 css px down | depth 57.9 → 74.9 → **100** (stops at the max) |
| Mouse: left handle 15 px out, then 80 px up | width 183.8; the move up does nothing (the handle stays on its rail) |
| Keys: Tab to the right handle; ←, Shift+←, Page Up, Home | 182.8 → 172.8 → 158 (stop) → 132 (min) |
| Touch: right handle 10, 20, 30 px out | 174.8 → 191.6 → **194** (max), no `pointercancel` |
| Touch: centre handle 15, then 30 px down | 53.7 → 65 (snapped to the 65 stop) |

Fixed on the way: the first touch drag was cancelled by the browser after one move, because Chrome reads `touch-action` only on the outer `<svg>`, not on its children. The outer SVG now has `touch-action: none`. It takes no pointer events itself, so the page still scrolls when the photo is touched.

- [x] Drag works with mouse, touch and keyboard; the handles never leave their rails, because their positions come from the clamped record.
- [ ] The lace follows during the drag: step 5.
- **Open (phone):** ≥ 30 frames per second on a mid-range phone. SwiftShader's timings are not real. The drag cost is one draw per frame, and the neck area adds three 24-segment curve searches per pixel.

## Step 5: The lace and the stitch line follow the live neckline

In the neck area the baked neck trim is not used. The shader finds the nearest point on the **live trim centre line** (24 points), and writes the same coordinates the plate maker writes:
- u = cm along the centre line;
- v = 0.5 + offset toward the edge ÷ trim width.

Past the two ends of the strip there is no trim, as on the plate. The lace's texture gradients come from the curve's tangent and normal, not from the plate.

Default match, measured by `tools/trim_match.py` at every baked neck-trim px, with the 24 points the shader gets:

| Plate | Along (u): median / 95 % / max | Across (v): median / 95 % / max | Signed mean (u, v) |
|---|---|---|---|
| neck (26 921 px) | 0.36 / 1.09 / 6.9 px | 0.29 / 0.86 / 1.9 px | +0.05, −0.06 px |
| torso (2 795 px) | 0.28 / 0.77 / 2.5 px | 0.26 / 0.74 / 1.4 px | −0.03, 0.00 px |

Two fixes made the default match:
- **Recipe at the strip ends.** The recipe was not the identity for the trim centre's end points, which lie past the neck corners. Depth is now measured from the grid top, not the corner line. Before the fix the whole strip was shifted 7 px.
- **The plate's u convention.** The plate maker draws the strip quad after quad, each with a 1 px outline, so a px on the border of two quads takes the later quad's u. The baked u runs 0.9–1.0 px ahead of the exact arc, and the page adds the same 0.95 px.

The few px with a larger error are at the bends, on the outer side, where neighbouring baked quads overlap.

The 8 queries against port 8000: PASS, mean 0.013–0.189. The neck views are the highest, because the high-contrast lace changes a lot for a sub-pixel move. Sleeve and hem: 0.000.

**Lace fit:** repeat, fit and start (polish step 4) now use the live trim length: the plate's `lengthCm` × live length ÷ default length (both from the 24-point line), so the default fit is exactly the plate's.

| Setting | Live length | Pearl repeats / fit | Middle motif to the CF line |
|---|---|---|---|
| neck, default | 20.71 cm | 12 / 1.014 | −1.45 mm (the photo's own) |
| neck, depth 100 | 29.93 cm | 17 / 1.035 | −0.82 mm |
| torso, depth 100, width 194 | 27.32 cm | 16 / 1.003 | −0.19 mm |
| neck 20 / 132 (geometric) | 15.70 cm | 33 / 0.995 | −2.07 mm |

The motif is centred at the middle of the strip's length, as before. That is within 2.1 mm of the centre-front line at every setting tried, 12 % of a pearl motif. Centring on the CF line exactly would move the default lace by 1.45 mm, so it was not done.

**Top-stitch:** the photographed top-stitch at 5.5 mm moves with the edge, because the edge band (step 3) is taken from the photographed band at the same distance from the edge (seen in `img/halfway-step3.png`). With a lace on, the stitch is under the 12 mm lace, as in the photo; no extra dashed line is drawn.

- [x] Default: matches the baked trim (median 0.3 px; 8 queries: mean ≤ 0.19).
- [x] At every setting tried: the lace hugs the edge, the motifs are whole, the middle motif is within 2.1 mm of the CF, and there is no seam at the neck corners (`img/halfway-step5.png`: neck pearl at depth 100, geometric at 20/132, fine at 65/194, leaf (mirror) at 90/140 on toile; torso pearl at 100/194 and geometric at 20/132).

## Step 6: The torso view shows the same neckline

Both front views read the same record (`state.neck`). Each one converts a **change in mm** into its own px with its own `mmPerPx` and landmarks (corner line, centre front, grid top). The torso plate has the same neck area, live edge, fills and live trim (steps 2, 3, 5), as the step 2–5 images show.

**Sleeve view (phase 1):** it keeps its photographed neckline. When the record differs from the photo, a note shows on the stage: "Neckline here as photographed. Your neckline (80 mm deep, 170 mm wide) shows in the front views." (`img/halfway-step6-sleeve.png`).

**Switching views keeps the setting:** with real clicks on the view pills, the record went from neck (80 / 170) to torso and then to sleeve unchanged.

**Neck depth in the two views:** the depth is measured on the live edge at the centre front, from the corner line.

| Record | Neckline view | Torso view | Change from the photo, neckline / torso |
|---|---|---|---|
| 65 / 158 | 65.0 mm | 49.2 mm | +24.10 / +23.92 mm |
| 90 / 180 | 90.0 mm | 74.1 mm | +49.10 / +48.83 mm |
| 25 / 140 | 25.0 mm | 9.3 mm | −15.90 / −15.93 mm |

- **Changes:** the two views agree within 0.3 mm (the torso's smooth shape moves the CF point by up to 0.27 mm).
- **Absolute depth:** the views differ by 15.7–15.9 mm, which is more than the ±3 mm the plan allows. The cause is in the photos, not in the method. The photographed necklines already differ: 40.9 mm deep in the neckline photo and 25.2 mm in the torso photo, with the same 158 mm width (from the corners: 29.6 mm from the torso's neck-point landmarks). The close-up is most likely shot from lower down: the neck points sit about 6 cm behind the centre front, so seen from below they appear higher, and the dip looks deeper. To match the absolute depth, the torso view would have to move its photographed neckline at the default, and then the default would no longer be the photo.
- **Width:** the torso corners (grid top) are 2.6 px outside the `neck-l` / `neck-r` landmarks that set the scale, so the torso measures 160.35 mm for the same width (158 mm in the neckline view). A change in width agrees exactly.

**Applied: the plan's fallback for "views disagree by more than 3 mm".** The neckline view is the control (the handles are only there), and its mm values are the record. The torso view shows the same change from its own photographed neckline, and updates when it is shown (one view is on screen at a time).

To close the 3 mm check, measure the real garment's neck depth (atelier), then re-annotate the torso neckline, or re-shoot one of the two views from the same height.

- [ ] For 3 settings, the neck depth in the torso and neckline views agrees within ±3 mm: **no**, the photos differ by 15.7 mm. Changes agree within 0.3 mm. Fallback applied.
- [x] Switching views keeps the setting.

## Step 7: Showcase

| Part | What it does |
|---|---|
| **Journey bar** | Cloth → Neckline → Sleeves → Hem → Review. Each step opens its view (torso, neck, sleeve, hem, torso) and shows only its controls: cloth; lace with its placements; the neckline shape on the Neckline step; the review. There are Back and Next buttons, and `?step=` is kept in the URL. The test panel shows only with `?test`. |
| **Cross-fade** | A still of the old view, faded out over 250 ms once the new view is drawn. With `prefers-reduced-motion` the transition is 0 s, checked with emulated media. A token stops a late fade-out from clearing a newer still. |
| **Highlight** | When a placement is turned on, its trims glow softly: a warm lift that rises and falls over 1 s (a test shows the glow frame differs from the settled one). When a pivot is selected (focus, including by pointer), the band along the live neck edge glows. With reduced motion the glow is on for 1 s, with no pulse. |
| **Before / after** | Hold the "Hold: before" button (pointer, touch, Space / Enter on it) or the Space key anywhere outside a control to see the plain garment (the photo). The handles hide meanwhile. Holding Space was checked with a held key. |
| **Cards** | Swatch cards with the real tile and its name (as before). Lace cards with a strip of the lace. |
| **Review** | The torso view large; below it a strip of the 3 close views (neck, sleeve, hem), drawn from the same record on the stage canvas behind a still of the torso and copied to the strip; the list of choices (cloth, lace, placements, neckline depth and width). The strip is rebuilt only when a choice changes. |
| **Share image** | One 1080 × 1500 PNG (`toBlob`): the torso, the choices, and the 3 close views. **Share** uses the system share sheet (WhatsApp) where the browser can share files; otherwise it downloads, and says so. **Download** always saves `my-kurta.png`. |
| **Phone** | One column at ≤ 760 px (stage on top). The 5 steps share one row; the numbers are hidden at ≤ 440 px. The sleeve note keeps clear of the before button. |

Fixed on the way:
1. The first phone run lost a fabric download ("Failed to fetch") on the busy local server, and the swatch cache then kept the failed promise. Downloads now retry once, and a failed swatch or material is not cached.
2. The journey bar first scrolled sideways on a phone, and the Review step was off screen.

Checked with real input events (`tools/cdp_shot.mjs --input`):

| Check | Result |
|---|---|
| Desktop journey: mocha → Next → drag depth and width → lace geometric → Sleeves (note shows) → Next → slits → Review | review list = "Mocha Chikan / Woven Diamond Border / neckline, sleeve cuffs, hem border, chaak slits / 79 mm deep, 175 mm wide"; no console error |
| The review image shows the same choices as the page | yes: the same list, and the 79 mm neckline in the torso and neck images (`img/halfway-step7-share.png`) |
| Step times after the first visit (SwiftShader, so slower than a real GPU) | cloth 1–481 ms, neck 158–370, sleeve 448, hem 463, review 530 ms (strip cached). The first review shows the torso at 358 ms; the strip fills in by 2.1 s. |
| Phone (390 × 844, touch taps): each of the 5 steps | every step opens; page width = window width (no sideways scroll); no error (`img/halfway-step7-phone.png`) |
| Default render, 8 queries vs port 8000 | PASS, unchanged from step 5 (mean ≤ 0.19) |

- [x] The review image shows the same choices as the page.
- [x] No step takes more than 1 s to show its view after the first visit (SwiftShader: ≤ 0.53 s).
- **Open (a person on a phone):** goes through the whole journey without help. The layout and every step work with touch on a phone-sized viewport; a real person on a real phone is still to do.
- **Known:** in the share image and on the sleeve step the turned sleeve view shows the photographed neckline (step 6, phase 1). The stage note says so; the image does not.

## Open checks (all need a real browser, phone or person)

1. Draw time ≤ 5 ms in a normal browser, and ≥ 30 frames per second while dragging on a mid-range phone (SwiftShader timings are not real).
2. Decoded image memory in the browser's memory panel (step 1: the page's own count says 0 MB after switches).
3. A person cannot point to the old neckline within 10 s at the range ends (step 3: by my own look, and the edge-step number).
4. A person goes through the journey on a phone without help (step 7).
5. Step 6: measure the real neck depth (atelier), then re-annotate the torso neckline or re-shoot one view, so that the views agree in absolute depth.
