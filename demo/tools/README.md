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
| `prep_swatches.py` | Legacy: the first sage and pearl swatches |

## Quality plan (`docs/plan/upscale.md`)

| Tool | Use |
|---|---|
| `shoot.sh <out> [port]` | Torso screenshots at 1× and 2× |
| `crops.py <shot-2x> <out>` | The 4 fixed review crops |
| `metrics.py <run-dir>` | Block ratio, sharpness, sizes |

## Notes

- Headless Chrome uses software rendering. The close views need a virtual-time budget of about 45 s, and the load and draw times it reports are not real.
- `testing.html` test switches: `?view=torso|neck|sleeve|hem`, `?fabric=off|sage|mocha|mustard`, `?lace=pearl|geometric|leaf|fine`, `?bias=`, `?aniso=0`, `?stage=<css px>`.
