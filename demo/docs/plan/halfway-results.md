# Results: halfway plan

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
