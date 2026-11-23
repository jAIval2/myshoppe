# demo/swatchprep: fabric swatches and laces for the page

Turns a photo of a fabric or a lace into the tiles the page uses (`../assets/swatches/`). Python 3 with Pillow only. It is
separate from the silhouette pipeline (`../silhouette/`): a swatch does not depend on any plate, and a plate does not depend on
any swatch.

## The contract

| | |
|---|---|
| **In** | A photo in `sources/`: the fabric flat and lit evenly, or the lace on plain paper. Sources do not ship |
| **Out** | `../assets/swatches/fabric-<name>-1024.jpg`; `lace-<name>-2048.webp` + its sidecar `lace-<name>.json` + its material map `lace-<name>-mat.webp`. `fabric-<name>.json`, the fabric's sidecar (`fabric-sidecar`, StepB step 5: name, real width and its source, class, placement data, sheen, anti-tiling; `docs/formats.md` §3). The page's registries (`FABRICS`, `LACES` in `testing.html`) point at the files |

## One entry point

```
python3 demo/swatchprep/prep.py fabric <in> <out.jpg> [preview_3x3.png] [--no-delight]
python3 demo/swatchprep/prep.py lace <in> <out.webp> <preview.png> [--flip] [--cut-bottom 0.12] [--paper R,G,B] [--key 8]
python3 demo/swatchprep/prep.py lace-repeat <band.webp> <out.webp> <out.json> <preview.png> [--width-mm 30] [--flip]
python3 demo/swatchprep/prep.py lace-material <tile.webp> <sidecar.json> <out-mat.webp> <preview.png> [--pearls]
python3 demo/swatchprep/prep.py first-swatches <src-dir> <out-dir> <debug-dir>
```

| Command | Tool | What it does |
|---|---|---|
| `fabric` | `prep_fabric.py` | De-lights the photo (divides by a large blur), resizes to 1024 px and makes it seamless (a minimum-error seam to the half-offset copy). The tile's real width (`repeatCm`) goes in its sidecar (`fabric-sidecar`) |
| `lace` | `prep_lace.py` | A lace on paper: keys out the paper by chromaticity, turns the band horizontal and crops it. The decorative edge goes at the bottom (`--flip` turns it), 446 px tall |
| `lace-repeat` | `prep_lace.py --repeat` | The band becomes a seamless tile of whole periods (the period found by autocorrelation), plus the sidecar: `periodPx`, `periods`, `periodRatio`, `edgeDepth` (the decorative edge's share of the height), `widthMm` (the lace's real width: the page lays the lace at this width) |
| `lace-material` | `prep_lace.py --material` | The material map: R height, G metal (zari), B pearl. **It writes into the sidecar it is given** (its `material` block, and `pearls` with `--pearls`): give it the real sidecar only when you mean to update it |
| `first-swatches` | `prep_swatches.py` | How the first sage fabric and pearl lace were made, from `sources/fabric-sage-640.png` and `sources/lace-pearl-640.png` (kept as the record) |

| `fabric-sidecar` | `fabric_sidecar.py` | The fabric's sidecar `fabric-<name>.json` (StepB step 5). The AI swatches' `repeatCm` is `assumed` |
| `test-print` | `test_prints.py` | Test fabrics made by a script: `reg` (the registration grid), `buta` (one placed motif), `border` (a hem border). With their sidecars (`--test`), they are `?fabric=<name>` only |

## Lace sidecars, version 2 (StepC step 1)

`lace_sidecar.py upgrade <lace.json> --name "<name>" --class <class> [--width-mm <mm> --src measured]` adds to what `prep_lace.py` writes: `version` 2, `name`, `class` (insertion, edging, border, gota, zari, pearl, mirror, latkan), `widthSrc`, `repeatSrc`, `materialFile`, `endRule`. `lace_sidecar.py check` validates. The page reads the lace's facts from it (`LACES` holds only the band and the sidecar). The six AI laces are `widthSrc: assumed`.

**Measuring a real lace:** photograph it flat on plain paper with a ruler across the band (perpendicular to it). `prep.py lace`, then `lace-repeat --width-mm <the band's measured width>`, then `lace_sidecar.py upgrade … --width-mm <mm> --src measured`. The repeat in cm follows (period ÷ band height × width), so it becomes `measured` too.

## Measuring a real swatch (the scale)

The AI swatches have no physical scale: their `repeatCm` is an assumption and their sidecar says `"repeatSrc": "assumed"`. For a real fabric:
1. Scan it flat (or photograph it square-on, evenly lit) with a **ruler** along one edge and a **colour card** (a grey and a white patch) in the frame.
2. `prep.py fabric` makes the seamless tile; note which part of the scan the tile covers.
3. Measure the tile's real width on the ruler (mm), and write the sidecar with `--repeat-cm <cm> --src measured`. A print's motif (`--motif`) or a border's edge (`--border-bottom`) is read on the tile in px.
4. The colour card: the tile's white patch should read as the card's white after the de-light; if it does not, the scan's colour is off (re-scan).

## Sources

| File | Made |
|---|---|
| `sources/fabric-sage-640.png` (2048²) | `fabric-sage-1024.jpg` (by `first-swatches`) |
| `sources/lace-pearl-640.png` (3168 × 1344) | `lace-pearl-2048.webp` (by `first-swatches`, then `lace-repeat`, `lace-material`) |
| `sources/fabric-mocha-src.png`, `fabric-mustard-src.png` (1254²) | `fabric-mocha-1024.jpg`, `fabric-mustard-1024.jpg` (by `fabric`) |

What a good source looks like, and what a lace sidecar must give the page (its real `widthMm` above all), is in `docs/render.md` and `docs/plan/StepA.md` §8.
