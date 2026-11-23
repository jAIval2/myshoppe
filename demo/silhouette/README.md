# demo/silhouette: annotate a view and build its plate

Everything that makes and checks a plate (the silhouette of one fixed view: zones, fabric frames, trims) lives in this folder.
Python 3 with Pillow only; Node for the two `.mjs` checks, which read the page's own `plate.js` / `maps.js`.
Procedures: `docs/plate.md` (the pipeline) and `docs/annotate.md` (measuring).

## The contract

| | |
|---|---|
| **In** | `sources/<plate>.png` (the image as received; it does not ship) and `views/<view>.py` (the points measured on it) |
| **Out** | `../assets/plates/<plate>/base.jpg` + `plate.dat`: the only two files the page downloads for a view. Deterministic: the same source gives the same bytes |
| **Never** | Edit a plate by hand. Change `views/<view>.py` (or a tool), then build again |

`<plate>` is `<view>-<variant>` (`torso-straight`); `<view>` is `torso`, `neck`, `sleeve` or `hem`.

## From an image: `make` (in demo/)

`make intake VIEW=<view> IMAGE=<path>` checks that the image lines up with the one the view was measured on, installs it, builds the plate and runs its checks; a different photo is stopped (the view must be measured again: `make replace`, then `docs/annotate.md`). `make plate VIEW=`, `make plates`, `make check`, `make serve`; `make help` lists all.

## One entry point

```
python3 demo/silhouette/plate.py views                      the plates that have a source
python3 demo/silhouette/plate.py measure <view>             the measured view's own checks (writes nothing)
python3 demo/silhouette/plate.py build <view> [--review]    source -> base.jpg + plate.dat; --review: demo/review/<plate>/
python3 demo/silhouette/plate.py check <view>               the plate's invariants + the page's frame maths against the build's
python3 demo/silhouette/plate.py page-check <view>          the page (served from demo/ on 8300, --port) against the plate
python3 demo/silhouette/plate.py rebuild-check [view ...]   every plate rebuilt from its source: byte-identical
```

It runs from anywhere (it works in `demo/`). Exit code 0 = pass.
`git diff` shows a `plate.dat` as text once you run `git config diff.dat.textconv "python3 demo/silhouette/pipeline/platedat.py --dump"` (`.gitattributes`: `demo/assets/plates/*/plate.dat diff=dat`).

## What is inside

| Folder | File | Job |
|---|---|---|
| `views/` | `torso.py`, `neck.py`, `sleeve.py`, `hem.py` | One per view. `base(source)` is the crop. `measure()` gives typed edges, zones with their outline chains and fabric-frame specifications, trims as specifications, landmarks and occluders. Run alone: the automatic checks. Templates for new views |
| `sources/` | `<plate>.png` | The images as received |
| `pipeline/` | `make_plate.py <plate-dir> [--review] [--no-check]` | The build: source → free and cut edges snapped → trim lines from their edges → frames fitted → the maps in memory → decisions → `base.jpg` + `plate.dat`. As a module: `build()`, `maps_of(plate)`, `rasterise()`, `review_image()` |
| | `platedat.py --dump / --check` | `plate.dat` version 3 (`BSP3`, StepB step 2): reader, writer, validator, text dump. The format and the data model are in its docstring |
| | `garment.py --check / --dump [look]` | The garment record (`assets/looks/<look>.json`, block `garment`): pieces, landmarks in piece cm with their sources, lines, each view's zones and landmark names. The build reads it; a plate carries its version and hash |
| | `snap_edges.py` | Every free and cut edge snapped to the photo (local colour model, sub-pixel 50 % crossing, robust smooth fit). Alone: the report |
| | `plateframe.py` | The fabric frame of a zone: (u, v) in cm for any point. `--samples <plate> <out.json>`: points for `frame_check.mjs` |
| | `trimfield.py` | The trim field: a lace laid on its garment edge, `s` (cloth cm along the edge) and `t` (mm from it). The page's `plate.js` `trimElements` and `maps.js` `TRIM_FS` are the same |
| `checks/` | `plate_invariants.py <plate> [--debug png]` | PASS / FAIL on the plate's own rules: closure (0.02 %, no piece over 1 px), hairline gaps, trim line and trim field, landmarks, the frame rules |
| | `frame_check.mjs <plate> <samples.json>` | `plate.js` `frameUV` against `plateframe.py` (10⁻⁴ cm) |
| | `maps_check.py <plate> <log.json>` | The maps the page builds against the plate: coverage, uv (0.01 cm), trim fields (0.01 cm, 0.05 mm) |
| | `cdp_shot.mjs <out> <port> [--dpr 2] [--page] [--eval '<js>'] [--input '<json>'] "<query>" ...` | Headless Chrome: the canvas, console errors, real input events, JavaScript in the page (`window.__studio`). At DPR 2, `stage=600` gives one canvas px per plate px |
| | `fringe.py <canvas> <plate> [--photo <off>]` | Closure in the render: leftover photo garment, the rim along free edges, the halo |
| | `edge_crops.py <canvas> <plate> <out.png> [--photo <off>]` | The review set: a crop at each landmark and every 150 px of each free edge, 3× |
| | `plate_edges.py` | Module: the outline samples with edge types and outward normals |
| | `xview_check.py [--json out] [plate ...]` | One cloth point = one fabric (u, v) in every view (StepB): each shared landmark's spread in mm, and its residual against the garment record |
| | `xview_sheet.py <out.png> <shots-dir>` | The same as an image: 10 cm crops of each shared landmark in each view, rendered with `?fabric=reg` |
| | `ba_sheet.py <out.png> <before> <after>` | Before / after of two `cdp_shot.mjs` runs, with the mean difference per query |
| | `rebuild_check.sh [plate ...]` | Every plate rebuilt into a scratch copy, compared byte for byte |
| `measure/` | `gridcrop.py <source> <out> x0 y0 x1 y1 [step] [contrast] [scale]` | Gridded crop in source px, for reading points |
| | `sample.py <image> label=x,y ...` | Colour, luminance, chromaticity at points |
| | `zoom.py <out> x0,y0,x1,y1 <img> ...` | Review crops, side by side |
| | `align_check.py <annotated> <source>` | Is an annotation drawn on the exact base, or regenerated? |

## Notes

- Headless Chrome renders in software, so its build and draw times are not real. `?perf=1` on a device shows the real ones.
- The page's switches for checks: `?view=torso|neck|sleeve|hem`, `?step=cloth|neck|sleeve|hem|review`, `?fabric=off|sage|mocha|mustard`, `?lace=<name>`, `?trims=neck,cuffs,hem,slits|none`, `?checker=1` (the grain checker), `?stage=<css px>`, `?neckDepth=<mm>&neckWidth=<mm>`, `?perf=1`, `?syncbuild=1`.
- Swatch and lace prep is a separate folder: `demo/swatchprep/`.
