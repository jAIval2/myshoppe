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
