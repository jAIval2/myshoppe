# demo/tools

Python 3 with Pillow only. Run every tool from `demo/`. Procedures: `docs/plate.md` (pipeline) and `docs/annotate.md` (measuring).

## Plates

| Tool | Step | Job |
|---|---|---|
| `make_base.py` | 3 | Torso only: sparkle patch, 3:4 cut, 1200 × 1600 |
| `annotate_neck.py`, `annotate_sleeve.py`, `annotate_hem.py` | 3–4 | One per view: base crop, measured points, `zones.json`, `annotate.png`, automatic checks. Templates for new views. |
| `extract_zones.py` | 4 | Read an **aligned** colour annotation (Path B) |
| `fit_zones.py` | — | Legacy, torso only |
| `make_plate.py` | 5 | `id`, `uv`, `uv_trim`, `shade` maps, `plate.json`, `check.png` |
| `plate_checks.py` | 6 | Acceptance numbers, PASS / FAIL |

## Measuring and review (the middleware we keep reusing)

| Tool | Use |
|---|---|
| `gridcrop.py <source> <out> x0 y0 x1 y1 [step] [contrast] [scale]` | Gridded crop in source px, for reading points |
| `sample.py <image> label=x,y ... [--blur 1.5]` | RGB / HSV / luminance / chromaticity at points, to set mask thresholds |
| `align_check.py <annotated> <source> [boxes]` | Is an annotation drawn on the exact base, or regenerated? Exit 0 = aligned |
| `zoom.py <out> x0,y0,x1,y1 <img> [img ...] [--scale 2] [--nearest]` | 2× review crop, or the same area of several images side by side |
| `rebuild_check.sh [plate ...]` | After a `make_plate.py` change: rebuild every plate in a scratch copy, compare byte for byte |
| `shoot_views.sh <out> ["view=hem&fabric=mocha&lace=leaf" ...]` | Headless screenshots of `testing.html`, in parallel, plus `sheet.png` |

## Swatches

| Tool | Use |
|---|---|
| `prep_fabric.py <in> <out.jpg> [preview] [--no-delight]` | De-lit, seamless 1024 px fabric tile |
| `prep_lace.py <in> <out.webp> <preview> [--flip] [--cut-bottom 0.12]` | Angled lace on paper → horizontal band with alpha, decorative edge at the bottom |
| `prep_lace.py --repeat <band.webp> <out.webp> <out.json> <preview> [--width-mm 30] [--flip]` | Band → seamless tile of whole periods (autocorrelation) + sidecar `lace-<name>.json` (period, edgeDepth, edging). No period: band kept, `"mirror": true` |
| `prep_lace.py --material <tile.webp> <sidecar.json> <out-mat.webp> <preview> [--pearls]` | Material map (R height, G metal, B pearl), lossless, half size; results in the sidecar `"material"` |
| `prep_swatches.py` | Legacy: the first sage and pearl swatches |

## Polish plan (`docs/plan/polish.md`)

| Tool | Use |
|---|---|
| `shoot_set.py <out> <port> --polish [extra]` or `"<query>" ...` | The 8 fixed review queries (or any list), 2 at a time; rejects a shot that is only the fallback photo and retries it. Use a free `<port>`. |
| `polish_metrics.py fd [plate]` | Fine detail (< 1.5 mm) and fold band (2–30 mm) of `shade.png` |
| `polish_metrics.py crops <shots> <out>` / `fcr <shots> [flat]` | Fixed review crops; fold contrast retention (exact with a `?shade=0` run) |
| `polish_metrics.py shadow <old> <new>` | What changed between two runs, and the darkest ratio |
| `polish_metrics.py fit [swatch-dir]` / `joins` | Whole lace repeats on every trim (same rules as the page); wrap joins of the lace tiles |

`shoot_views.sh` takes `DPR`, `WIN`, `JOBS`, `TMO` and `PORT`. Two runs on the same port kill each other's server.

## Halfway plan (`docs/plan/halfway.md`)

| Tool | Use |
|---|---|
| `node tools/cdp_shot.mjs <out> <port> [--dpr 2] [--win 900x760] [--page] [--mobile] [--reduced] [--input '<json>'] [--eval '<js>'] "<query>" ...` or `--polish [extra]` | Headless Chrome through the DevTools protocol: saves the **canvas** (`canvas-<i>.png`, exact pixels once the frame is drawn) and every console error, including the shader compile log (`log.json`). `--input` sends real mouse / touch / key events (`{"m":"down","sel":"#h-cf"}`, `{"t":"move","dx":10}`, `{"k":"ArrowDown","shift":true}`, `{"kd":" "}` / `{"ku":" "}`, `{"js":"..."}`, `{"wait":ms}`); `--page` adds a full-page screenshot; `--mobile` a phone; `--reduced` prefers-reduced-motion. 5–10 s per query. |
| `canvas_diff.py <run-a> <run-b> [--diff <out>]` | Two runs canvas by canvas: mean \|difference\|, share > 8 levels, max. PASS at mean ≤ 0.5 ("pixel-identical" in the plan). |
| `reveal_metrics.py <canvas.png> <plate-dir>` | Step 3: the step across the old neck edge against the light's own change, and the repeat peak of the form fill |
| `trim_match.py <plate-dir> <sent.json>` | Step 5: the live neck trim (the shader's 24 points) against `uv_trim.png`, in px along and across |

`make_plate.py` now writes, on the neck and torso plates, the neck area (`id.png` B = 1), the full-grid UV in it, the shade carried 8 px into the dip, and the `neck` block of `plate.json` (edge, trim centre, grid top, CF, reach, fill colours, form patch).

## Quality plan (`docs/plan/upscale.md`)

| Tool | Use |
|---|---|
| `shoot.sh <out> [port]` | Torso screenshots at 1× and 2× |
| `crops.py <shot-2x> <out>` | The 4 fixed review crops |
| `metrics.py <run-dir>` | Block ratio, sharpness, sizes |

## Notes

- Headless Chrome uses software rendering. The close views need a virtual-time budget of about 45 s, and the load and draw times it reports are not real.
- `testing.html` test switches: `?view=torso|neck|sleeve|hem`, `?fabric=off|sage|mocha|mustard`, `?lace=pearl|geometric|leaf|fine`, `?bias=`, `?aniso=0`, `?stage=<css px>`.
  Polish plan, kept for before / after comparisons (each one gives back the old behaviour of its step):
  `?shade=0` (flat light, for the fold contrast), `?shadow=0|<strength>` (lace shadow), `?linear=0` (sRGB maths), `?lacefit=0` (mirrored lace, no fit),
  `?edging=0` (no lace past the edge), `?relief=0` (no lace relief, metal, pearl), `?displace=0`, `?sheen=0|test` (old 0.15 highlight | a test sheen), `?antitile=0`.
  Halfway plan: `?decode=all` (keep the decoded images: the old memory use), `?neck=baked` (the baked neckline and trim, no handles), `?revealfill=0` (plain colours where a change reveals fabric or form),
  `?neckDepth=<mm>&neckWidth=<mm>` (the design record), `?snap=0` (no snap stops), `?step=cloth|neck|sleeve|hem|review` (the journey step; `?view=` still picks the step of that view), `?test` (shows the test panel).
