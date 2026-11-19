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
