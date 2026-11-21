# demo/tools

Python 3 with Pillow only. Run every tool from `demo/`. Procedures: `docs/plate.md` (pipeline) and `docs/annotate.md` (measuring).

## Plates (StepA step 1: one file per view)

A plate folder ships `base.jpg` + `plate.dat`; its source is `source.png` + `tools/annotate_<view>.py` (the torso: its imported
`plate.dat` until StepA step 2). Nothing in a plate is edited by hand: change the annotate script (or a tool), then rebuild.
`git diff` shows a `plate.dat` as text once per clone: `git config diff.dat.textconv "python3 demo/tools/platedat.py --dump"`
(`.gitattributes`: `demo/assets/plates/*/plate.dat diff=dat`).

| Tool | Job |
|---|---|
| `make_plate.py <plate> [--review] [--no-check] [--dump-mesh <prefix>]` | The build: source → decisions (trim sides, shade median, neck block, sizes) → `base.jpg` + `plate.dat`, deterministic. The maps only in memory. `--review`: `annotate.png`, `check.png` and the edge crops into `demo/review/<plate>/`. Runs `plate_invariants.py`. As a module: `build()`, `maps_of(plate)` (the maps of a plate.dat, in memory), `rasterise()` |
| `platedat.py --dump <plate>` / `--check <plate> ...` | `plate.dat` version 2 (`BSP2`): reader, writer, validator, text dump. Format and the data model in its docstring: typed edges (`free`, `seam`, `frame`, `cut`), zone outlines as chains of edges, trims, settings, decisions |
| `annotate_neck.py`, `annotate_sleeve.py`, `annotate_hem.py` | One per view: `base()`, `measure()` (typed edges, zones, trims, landmarks), `review()`. Run alone: the automatic checks. Templates for new views |
| `make_base.py` | Torso only, until StepA step 2: sparkle patch, 3:4 cut, 1200 × 1600 |
| `rebuild_check.sh [plate ...]` | Rebuild every plate from its source into a scratch copy: `base.jpg` and `plate.dat` must be byte-identical |
| `plate_invariants.py <plate> [--debug png]` | The plate's own invariants, PASS / FAIL (closure against the photo, hairline gaps, symmetry, trim offset and smoothness, landmarks, `plate_checks.py`). Plate `invariants`: `openings`, `skipTrimOffset` |
| `plate_checks.py <plate>` | Grid bulge, grain tilt, UV rate, block ratio, shipped size (replaced by frame rules in StepA step 4, removed in step 7) |
| `snap_outline.py` | Helpers only (garment mask, robust cubic); its one-off commands went with the JSON files. Removed in StepA step 7 |

## StepA review set (`docs/plan/StepA.md`)

| Tool | Use |
|---|---|
| `node tools/cdp_shot.mjs <out> <port> "view=<v>&fabric=mocha&trims=none&stage=600"` | At DPR 2, `stage=600` gives a 1200 × 1600 canvas: one canvas px = one plate px. Shoot `fabric=off` too (the photo as the page draws it) |
| `fringe.py <canvas> <plate> [--photo <off>] [--debug png] [--json]` | Closure in the render: photo garment the page still shows (count, share, pieces wider than 1 px) and the bright rim along the free edges (share of their length) |
| `edge_crops.py <canvas> <plate> <out.png> [--photo <off>]` | The review set: a crop at each landmark and every 150 px along each free edge, photo and render side by side, 3× |
| `plate_edges.py` | Module: the outline samples of a plate with their edge types and outward normals (used by the two above) |

## Measuring and review (the middleware we keep reusing)

| Tool | Use |
|---|---|
| `gridcrop.py <source> <out> x0 y0 x1 y1 [step] [contrast] [scale]` | Gridded crop in source px, for reading points |
| `sample.py <image> label=x,y ... [--blur 1.5]` | RGB / HSV / luminance / chromaticity at points, to set mask thresholds |
| `align_check.py <annotated> <source> [boxes]` | Is an annotation drawn on the exact base, or regenerated? Exit 0 = aligned |
| `zoom.py <out> x0,y0,x1,y1 <img> [img ...] [--scale 2] [--nearest]` | 2× review crop, or the same area of several images side by side |
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
| `trim_match.py <plate-dir> <sent.json>` | Step 5: the live neck trim (the shader's 24 points) against the plate's uv_trim (in memory), in px along and across |

`make_plate.py` makes, on the neck and torso plates, the neck area (id B = 1), the full-grid UV in it, the shade carried 8 px into the dip, and the `neck` block of the decisions (edge, trim centre, grid top, CF, reach, fill colours, form patch).

## Numeric plan (`docs/plan/numeric.md`)

The page builds the plate maps itself from the curves: `plate.js` (the maths of `make_plate.py`), `maps.js` (the GPU passes: `id`, `uv`, `uv_trim`, the shade) and `plate.dat` (the curves and decisions of one view, a few KB). `?geom=mesh` turns it on; the PNG maps stay the offline reference.

| Tool | Use |
|---|---|
| `make_plate.py <plate> --dump-mesh <prefix>` + `node tools/mesh_check.mjs <plate> <prefix>` (reads `plate.dat` through `Plate.parseDat`) | Step 1: every vertex of every zone grid, trim strip and ribbon, and the neck edge, `plate.js` against Python (pass: 0.01 px, 0.001 cm; found 3e-11) |
| `node tools/cdp_shot.mjs <out> <port> --eval 'return window.__studio.readMaps()' "view=torso&geom=mesh"` then `python3 tools/map_diff.py <plate> <out>/log.json [--only id,uv,uvt,shade] [--debug <png>]` | Steps 2-5: the textures that the page built, against `id.png`, `uv.png`, `uv_trim.png`, `shade.png`: edge band, holes, area, uv / uv_trim bias, median and 99 %, shade levels. Criteria in the docstring |
| `python3 tools/canvas_diff.py <a> <b> [--blur <sigma>]` | Render comparison. A real fabric differs by the PNG maps' own 12-bit uv noise (about a texel); the gate is the grain checker (`?checker=1`, mean <= 1.0) with `?trims=none`; `--blur` shows the structure |

Test switches of the page: `?geom=mesh`, `?meshviews=torso,neck,sleeve,hem`, `?gpushade=0` (shade from `shade.png`), `?cell=<px>` and `?mapoff=idx,idy,uvx,uvy,grow` (mesh calibration), `?checker=1`, `?trims=neck,cuffs,hem,slits|none`.

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
