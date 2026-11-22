# demo/tools

Python 3 with Pillow only (Node for the `.mjs` files). Run every tool from `demo/`. Procedures: `docs/plate.md` (pipeline) and `docs/annotate.md` (measuring).

## Plates

A plate folder holds `source.png`, `base.jpg` and `plate.dat` only; the page downloads `base.jpg` + `plate.dat` and builds the maps itself. The source of a plate is `source.png` + `tools/annotate_<view>.py`. Nothing in a plate is edited by hand: change the annotate script (or a tool), then rebuild.
`git diff` shows a `plate.dat` as text once per clone: `git config diff.dat.textconv "python3 demo/tools/platedat.py --dump"` (`.gitattributes`: `demo/assets/plates/*/plate.dat diff=dat`).

| Tool | Job |
|---|---|
| `annotate_torso.py`, `annotate_neck.py`, `annotate_sleeve.py`, `annotate_hem.py` | One per view: `base()` (the crop), `measure()` (typed edges, zones with their outline chains and fabric-frame specifications, trims as specifications, landmarks, occluders). Run alone: the automatic checks. Templates for new views |
| `make_plate.py <plate> [--review] [--no-check]` | The build, deterministic: source → free and cut edges snapped (`snap_edges.py`) → trims derived from their edges → frames fitted → the maps in memory → decisions (trim sides, shade median, neck block, sizes) → `base.jpg` + `plate.dat`. `--review`: `annotate.png`, `check.png` (the checker; a 30 mm lace as stripes on the trim field) and the edge crops into `demo/review/<plate>/`. Runs `plate_invariants.py`. As a module: `build()`, `maps_of(plate)` (the maps of a plate.dat, in memory), `rasterise()`, `review_image()` |
| `platedat.py --dump <plate>` / `--check <plate> ...` | `plate.dat` version 2 (`BSP2`): reader, writer, validator, text dump. Format and the data model in its docstring |
| `trimfield.py` | The trim field (StepA extension): a lace laid on its garment edge, `s` (cloth cm along the edge) and `t` (mm from it) for every pixel near it; the elements and the exact raster of the build (`plate.js` `trimElements` and `maps.js` `TRIM_FS` are the same) |
| `plateframe.py` | The fabric frame of a zone: (u, v) in cm for any point (the axis projection, the cylinder, the sag); the fits of the build. `--samples <plate> <out.json>`: points for `frame_check.mjs` |
| `snap_edges.py <plate> [--json]` | A module of the build: every free and cut edge snapped to the photo (local colour model, sub-pixel 50 % crossing, robust smooth fit); corners and seam ends follow. Alone: the report (accuracy of the fit, weak spans) |
| `rebuild_check.sh [plate ...]` | Rebuild every plate from its source into a scratch copy: `base.jpg` and `plate.dat` must be byte-identical |
| `plate_invariants.py <plate> [--debug png]` | The plate's own invariants, PASS / FAIL: closure against the photo (0.02 %, no piece wider than 1 px), hairline gaps, trim line (on its edge, smooth) and trim field (complete, no seam within 30 mm), landmarks, the frame rules (no fold, grain within 3° of the axis, UV rate at the axis, u = 0 through the centre front). Plate `invariants`: `openings` |
| `node tools/frame_check.mjs <plate> <samples.json>` | `plate.js` `frameUV` against `plateframe.py` at 10,000 points (pass: 10⁻⁴ cm) |
| `maps_check.py <plate> <log.json>` | The maps the page builds (`cdp_shot.mjs --eval 'return window.__studio.readMapsRaw()'`) against the plate: coverage (only a 1 px edge band may differ), uv (0.01 cm), the trim fields (`uvt`, `uvts`: s 0.01 cm, t 0.05 mm) |

## Review set and the render

| Tool | Use |
|---|---|
| `node tools/cdp_shot.mjs <out> <port> [--dpr 2] [--win 900x760] [--page] [--mobile] [--reduced] [--input '<json>'] [--eval '<js>'] [--budget ms] "<query>" ...` or `--polish` / `--numeric` | Headless Chrome through the DevTools protocol: saves the **canvas** (`canvas-<i>.png`) and every console error (`log.json`). `--input` sends real mouse / touch / key events; `--eval` runs JavaScript in the page (`window.__studio`). At DPR 2, `stage=600` gives a 1200 × 1600 canvas: one canvas px = one plate px |
| `fringe.py <canvas> <plate> [--photo <off>] [--debug png] [--json]` | Closure in the render: photo garment the page still shows; the garment-coloured rim along the free edges; the halo outside them |
| `edge_crops.py <canvas> <plate> <out.png> [--photo <off>]` | The review set: a crop at each landmark and every 150 px along each free edge, photo and render side by side, 3× |
| `plate_edges.py` | Module: the outline samples of a plate with their edge types and outward normals |
| `canvas_diff.py <run-a> <run-b> [--diff <out>] [--blur <sigma>]` | Two runs canvas by canvas: mean \|difference\|, share > 8 levels, max |
| `reveal_metrics.py <canvas.png> <plate-dir>` | The step across the old neck edge against the light's own change, and the repeat peak of the form fill (halfway step 3) |
| `shoot_set.py <out> <port> --polish [extra]` or `"<query>" ...`, `shoot_views.sh` | Fixed review query sets; parallel screenshots (`shoot_views.sh` starts its own server: give it a free `PORT`) |
| `polish_metrics.py fd \| crops \| fcr \| shadow \| fit \| joins` | Polish plan: fine detail and fold band of the shade, review crops, fold contrast, lace fit and joins |

## Measuring

| Tool | Use |
|---|---|
| `gridcrop.py <source> <out> x0 y0 x1 y1 [step] [contrast] [scale]` | Gridded crop in source px, for reading points |
| `sample.py <image> label=x,y ... [--blur 1.5]` | RGB / HSV / luminance / chromaticity at points, to set mask thresholds |
| `align_check.py <annotated> <source> [boxes]` | Is an annotation drawn on the exact base, or regenerated? Exit 0 = aligned |
| `zoom.py <out> x0,y0,x1,y1 <img> [img ...] [--scale 2] [--nearest]` | 2× review crop, or the same area of several images side by side |

## Swatches

| Tool | Use |
|---|---|
| `prep_fabric.py <in> <out.jpg> [preview] [--no-delight]` | De-lit, seamless 1024 px fabric tile |
| `prep_lace.py <in> <out.webp> <preview> [--flip] [--cut-bottom 0.12]` | Angled lace on paper → horizontal band with alpha, decorative edge at the bottom |
| `prep_lace.py --repeat <band.webp> <out.webp> <out.json> <preview> [--width-mm 30] [--flip]` | Band → seamless tile of whole periods + sidecar `lace-<name>.json` |
| `prep_lace.py --material <tile.webp> <sidecar.json> <out-mat.webp> <preview> [--pearls]` | Material map (R height, G metal, B pearl) |
| `prep_swatches.py` | Legacy: the first sage and pearl swatches (left for the swatch plan) |

## Notes

- Headless Chrome uses software rendering: its build and draw times are not real (`?perf=1` on a device shows the real ones).
- `testing.html` test switches: `?view=torso|neck|sleeve|hem`, `?fabric=off|sage|mocha|mustard`, `?lace=pearl|geometric|leaf|fine|paisley|brocade`, `?trims=neck,cuffs,hem,slits|none`, `?checker=1`, `?stage=<css px>`, `?bias=`, `?aniso=0`, `?perf=1` (an overlay: build, draw, drag frame rate, float render targets), `?syncbuild=1`.
  Before / after of the polish plan: `?shade=0`, `?shadow=0|<strength>`, `?linear=0`, `?lacefit=0`, `?edging=0`, `?relief=0`, `?displace=0`, `?sheen=0|test`, `?antitile=0`.
  Halfway plan: `?revealfill=0`, `?neckDepth=<mm>&neckWidth=<mm>` (the design record), `?snap=0`, `?step=cloth|neck|sleeve|hem|review`, `?test`.
