# Bespoke Studio: garment rendering

Status: proposal, with one working test plate (see section 11, "Progress log").
Scope: Bespoke Studio — 2, "The Salon" edit.

## 1. Purpose

This document gives the method that shows a garment on the dress form in the Salon. The garment shows the client's fabric, lace, and details.

The method must:

- Look like a real photograph of the garment.
- Load fast and use little battery on a phone.
- Use no 3D engine in the browser.

## 2. Non-goals

We do not supply these functions:

- Zoom.
- Pan.
- Rotation, or a free camera.
- A 3D model in the browser.

The client does not control the mannequin. The client controls the **journey**. Each step of the journey shows a fixed view. Each view shows the part of the garment that the client changes at that step.

## 3. The four views

All four views come from the same 3D garment in one CLO3D (or Blender) scene. Thus the cloth, the folds, and the light agree between the views. Each close view has its own render at full resolution. This gives the detail that a zoom function gives, but there is no zoom.

| ID | View | Frame | Focus | Framing reference |
|---|---|---|---|---|
| `torso` | Full torso / silhouette | Plain linen dress form, no head, arms, or legs. Neck knob to hem. | Silhouette, length, flare, overall fabric. | `assets/torso-base.png` (use a bare form, see 6.4) |
| `neckline` | Neckline & placket | Neck knob to bust. Front, centred. | Neck shape, placket, piping, embroidery around the neck. | `reference-neckline` |
| `sleeve` | Shoulder & sleeve cuff | Three-quarter angle. Shoulder to cuff. | Shoulder condition, sleeve length, cuff lace, cuff piping. | `reference-sleeves` |
| `hem` | Hemline & chaak slit | Hip to below the hem. Front, slightly to one side. | Hem stitch, hem border, slit length, motif near the slit. | `reference-hem` |

The reference images are in `media/bespoke/` (`reference-neckline-1280.webp`, `reference-sleeves-1280.webp`, `reference-hem-1280.webp`). Use them as guides for the camera and the light. Do not use them as render inputs.

## 4. The journey controls the view

Each journey step has one view. When the client goes to a step, the stage changes to that view with a short crossfade. There is no camera movement.

| Journey step | View | What the client changes |
|---|---|---|
| Choose the look | `torso` | House look, silhouette |
| Cloth | `torso` | Main fabric |
| Neckline | `neckline` | Neck shape, placket, piping, neck embroidery |
| Shoulder & sleeves | `sleeve` | Shoulder condition, sleeve length, cuff lace |
| Hem & slit | `hem` | Hem stitch, border, slit length, slit motif |
| Review | `torso`, then a strip of the three close views | Nothing. The client examines the result. |

The order of steps can change. The rule does not change: **one step, one view**.

## 5. Options: two types

Each option is one of two types. The type tells us how to show it.

### 5.1 Surface options (applied in the browser)

These options change only the surface of a part. The shape does not change.

- Main fabric.
- Lace on a cuff, a hem, or a neckline.
- Piping and border colour.
- Thread colour of an embroidery.

The browser applies these in real time with a small shader (see section 6). We do not need a new render for each fabric.

### 5.2 Shape options (pre-rendered variants)

These options change the shape of the garment.

- Neck shape: round, V, keyhole & potli, boat, sweetheart, bandhgala collar, angrakha wrap.
- Shoulder condition (examples, the atelier gives the final list): set-in, dropped, gathered, cold-shoulder, sleeveless.
- Sleeve length: cap, elbow, three-quarter, full, bell.
- Slit length, hem shape.

We render each shape variant one time, offline, for the view that shows it. The browser loads the variant. Then it applies the surface options to the variant.

### 5.3 Isolated parts with toggles

Each view has **zones**. A zone is one part that the client can select, such as "cuff lace" or "slit motif". The client sets each zone on or off with a toggle. We render each zone as its own isolated layer, so a toggle only shows or hides a layer. It does not start a new render.

Example: the `sleeve` view

```
sleeve view
├── shoulder condition   (shape variant: set-in | dropped | gathered | …)
│   └── sleeve length    (shape variant: cap | elbow | ¾ | full | bell)
├── body fabric          (surface: any fabric)
├── cuff lace            (zone, toggle on/off; surface: any lace)
└── cuff piping          (zone, toggle on/off; surface: any colour)
```

For one shoulder condition, the view shows all fabrics, all laces, and all toggles. It does not load more data.

## 6. Render method: UV pass and a small shader

### 6.1 Why not SVG only

We tried SVG patterns with `mix-blend-mode: multiply` (`testing.html`). SVG cannot do a texture lookup for each pixel. Thus:

- The weave is flat on the screen. It does not follow the body or the grain of each piece.
- Lace does not bend along the neckline curve.
- The folds come from random noise (`feTurbulence`), not from the real drape.
- `feDisplacementMap` is not hardware-accelerated in Firefox. SVG filters on large regions are slow on Safari iOS.

SVG stays in the design for other tasks (see 6.6).

### 6.2 The method

This is a standard VFX method, the "UV pass" or "STMap". A render stores the UV coordinate of each pixel as a colour: U in red, V in green. After the render, you can put any texture on the garment, and you do not render again.

Our 2D pattern pieces *are* the UV layout. Each piece has its own grain. Trim strips (binding, piping) have their own UV strips. Thus lace bends along the neckline automatically.

### 6.3 What a plate is (since StepA)

A **plate** is one view of one shape variant: a folder of the two files that ship, made from a source image kept in `demo/silhouette/sources/` (`plan/StepA.md` §1; `plan/cleanup.md`):

| File | Contents | Ships |
|---|---|---|
| `silhouette/sources/<plate>.png` | The image as received; it is measured (not in the plate folder) | No |
| `base.jpg` | The 1200 × 1600 photo, made from the source | Yes |
| `plate.dat` | Every number of the view (`silhouette/pipeline/platedat.py`, `BSP2`): typed edges (`free`, `seam`, `frame`, `cut`), each zone's outline as a chain of edges and its **fabric frame**, the trims (from their edges), stitches, landmarks, occluders, scale, and the decisions taken from the image (trim sides, the shade median, the neck block) | Yes |

The source of a plate is `silhouette/sources/<plate>.png` + `silhouette/views/<view>.py` (the measured points); `silhouette/pipeline/make_plate.py <plate>` builds `base.jpg` and `plate.dat` from them, deterministically (`silhouette/checks/rebuild_check.sh`). No map image is stored: the page builds the maps.

**The fabric frame** of a zone (`silhouette/pipeline/plateframe.py`, `Plate.frameUV`): an axis (the centre front, a sleeve's or a panel's centre line), an anchor (v = 0 on the neck-point line, at the shoulder point, or a known distance at the slit top), a half-width profile on each side (a cubic fitted to the outline), `thetaDeg` and a sag (the weft lines curve like the hem or the cuff). v = the position along the axis (mm); u = the arc of a cylinder across it. Defined everywhere around the zone, so the outline alone decides where the fabric shows; the same garment point has the same (u, v) wherever the views agree.

### 6.4 Offline steps (one time for each plate)

`demo/docs/plate.md` (the pipeline) and `demo/docs/annotate.md` (measuring). In short: intake → base crop → measure every edge on gridded crops of `source.png` (typed edges, landmarks, the frame's axis and anchor) → `make_plate.py`: free edges snapped to the photo (`silhouette/pipeline/snap_edges.py`), trims derived from their edges, frames fitted, decisions → `plate.dat` → `plate_invariants.py` and a person's review → record (§11).

A 3D route (CLO3D or Blender) stays possible as an offline source of plates (`DedhD.md` §11.3): its outlines and frames would come from the render instead of a measurement.

Fabric and lace swatches also need one step: remove the light (de-light the swatch) and make the brightness even. If you do not, the shade darkens the cloth two times. Dark fabrics then lose all their folds.

### 6.5 In the browser

- One `<canvas>`, one full-screen quad, one fragment shader. No Three.js. Draw **only when a choice changes**.
- When a view is shown, `maps.js` builds its maps on the GPU from `plate.dat` (`plate.js` parses it): **id** (R zone, G trim, B the neck area, A the coverage of a soft free edge), **uv** (the zone's fabric frame evaluated per pixel), the **trim field** (`uvt` with id G, and `uvts` for the slits: below) and the **shade** (the photo's luminance ÷ its median, a guided filter per zone; it needs float render targets). One exact draw for each zone (its outline, and at a seam the lower zone's strip 6 px under the upper one) and each trim.
- **Precision:** uv and the trim fields are 16-bit, packed into the RGBA8 textures (RG = u, BA = v, over 128 cm: 0.02 mm steps).
- **Laces (StepA extension, `docs/plan/StepA.md` §8):** a lace is a strip of cloth sewn along a garment edge, at its **own** width and repeat (the sidecar's `widthMm` and period: the lace decides, not the trim).
  - The **trim field** gives, for each pixel near a trim's edge: `t` = mm from the edge (+ on the garment) and `s` = the cloth length in cm along the edge, measured in the zone's fabric frame and 0 at the anchor. Because `s` is measured in the fabric frame, the motifs crowd toward a silhouette as the fabric does.
  - The field is built from one element per 2 px segment of the edge, between smooth normals (the chord over ±30 mm). Elements share their normals, so there is no wedge and no overlap at a bend. Where two trims of a zone meet, the nearer edge wins: a mitre. It is built from 8 mm outside the edge to 56 mm inside (the widest lace), so it does not depend on the lace chosen. `silhouette/pipeline/trimfield.py` is the reference; `plate.js` `trimElements` and `maps.js` `TRIM_FS` do the same.
  - Ends: the neck, the cuffs and the hem are loops, so the field goes on past their ends and the garment's outline cuts it. Only the slit top is a square end.
  - The overhang (an edging lace's decorative edge, `edgeDepth` of its width past the edge) exists only along the edge, takes the garment's light 3 px inside the edge (not the stand's or the wall's behind it), and keeps its contact shadow.
  - Phase: a motif is centred at the frame's u = 0 (the centre front, a sleeve's axis). The slits have whole repeats from the hem corner. The slits are a field of their own (`uvts`); the shader mitres them against the hem by the nearer edge.
  - In the views with the live neckline, the neck lace hangs on the live edge (`t` = the distance to it, `s` = its arc length from the centre front).
  - The lace texture's transparent texels carry the lace's mean colour, so its small mipmaps do not grey it.
- **Soft free edges:** where a zone meets the background, its coverage is a 1 px ramp on the photo's 50 % edge, and what shows beside the fabric is the photo 3 px beyond the edge (past the garment's own white).
- The shader does: `fabric = texture(swatch, decode(uv) / repeat)` × shade (+ sheen) → laces from the trim field → the live neckline → the coverage of the edge. `?perf=1` shows the build time, the draw time, the frame rate of a drag and whether float render targets exist.

### 6.6 Where SVG stays

An SVG layer stays on top of the canvas, in the same viewBox as the plate. It holds:

- Focus rings and labels for the zones.
- Pins and atelier notes.
- The line-art drawings of `cDraw()` for the order and fitting stages.

Hit test: read the `id.png` colour under the pointer. You do not need to trace zone paths by hand.

## 7. Preload and registry

### 7.1 Preload

- When the journey starts, load the `torso` plate for the selected look.
- While the client is on one step, load the plates of the next step in idle time.
- In a view, preload **all** shape variants of that view for the selected look. Then each change and each toggle is immediate.
- Load the swatches at 640 px. Fabric is a tiling texture, so a larger file is not necessary.

### 7.2 Registry ("recorded in our system")

The backend keeps a manifest of all plates. The frontend reads it. It does not guess file names.

```json
{
  "look": "salon-06-angrakha",
  "version": 3,
  "views": {
    "sleeve": {
      "camera": "sleeve-v1",
      "size": [1200, 1600],
      "zones": ["body", "cuff-lace", "cuff-piping"],
      "variants": {
        "set-in/three-quarter": {
          "uv": "plates/salon-06/sleeve/set-in-34/uv.png",
          "shade": "plates/salon-06/sleeve/set-in-34/shade.webp",
          "id": "plates/salon-06/sleeve/set-in-34/id.png",
          "spec": null,
          "details": []
        }
      }
    }
  }
}
```

The same manifest tells the order system which plates to use for the share image and the atelier sheet.

### 7.3 Number of plates

Only shape variants make new plates. Fabrics, laces, colours, and toggles do not.

```
plates per look = 1 (torso, for each silhouette and length)
                + neck shapes
                + shoulder conditions × sleeve lengths
                + slit lengths × hem shapes
```

Example: 7 neck shapes, 3 shoulders × 5 sleeves, 3 slits → approximately 1 + 7 + 15 + 3 = 26 plates for each look. The Salon shows a small number of house looks, so this number is acceptable. Limit the variants for each look to the options that the atelier makes for that look.

## 8. Fallback and accessibility

- If WebGL is not available, show a server image. The worker does the same remap with NumPy + Pillow and caches a WebP for each choice. The share image and the order image also use this path.
- The canvas has one `aria-label` that describes the garment (use the text of `cDescribe()`).
- All controls are normal buttons with `aria-pressed`. Toggles are normal switches.
- The view crossfade obeys `prefers-reduced-motion`.

## 9. Problems found in `testing.html`

For reference. These show why we move away from SVG for the cloth.

1. The swatch buttons load `./assets/fabric-*-640.webp`. These files are not in `assets/`. Only `fabric-sage-640.png` and `lace-pearl-640.png` are there.
2. `feTurbulence` + `feDisplacementMap` make random folds, not real folds. They are also slow.
3. `edge-feather` blurs all of the cloth layer, not only the edge.
4. The pattern is in `userSpaceOnUse`, so the grain is the same on the bodice and on the angled sleeves.
5. The swatch photos have their own light, so `multiply` darkens them two times.
6. The silk sheen is a fixed gradient. It does not follow the shape.

## 10. Open questions

- Which shoulder conditions and slit lengths does the atelier make for each house look?
- Do we need a back view (for keyhole and potli backs)? If yes, it is a fifth fixed view with the same method.
- Who makes the CLO3D garments, and in which file format do they come to us?
- What is the maximum load size for one view on a phone? Measure it on the first real plate before we decide.

## 11. Progress log

### 2026-11-18: first working test plate

#### Decisions that change this document

- **We do not use CLO3D.** We make our own tool. CLO3D is too much for a boutique. Some of its ideas stay in our design: pre-rendered views, layer management, and the factory handoff.
- **No toile and no 3D model for now.** We only have a `.zpac` model of a kurta, and Blender cannot open that format. So the plates come from **curves drawn on a photo**, not from a 3D render.
  - **Fabric zone:** 4 edges. A Coons patch fills them.
  - **Trim:** 1 centre line + a width in mm.
- Thus sections 6.3–6.4 ("offline steps with CLO3D") are replaced by the pipeline below. The browser side (section 6.5) did not change.

#### Pipeline (test version)

| Step | Input | Output | Script |
|---|---|---|---|
| 1. Base photo | `assets/torso-base.png` (1792 × 2400) | `base.jpg`, 1200 × 1600, exact 3:4, sparkle mark removed | `make_base.py` |
| 2. Annotation | `base.jpg` | `annotate.png`: colour-coded lines and landmark dots | by hand |
| 3. Extraction | `annotate.png` | `zones.json`: landmarks, 3 fabric zones (grid + outline), 6 trims | `extract_zones.py` |
| 4. Fit | `zones.json` + points measured on `base.jpg` | `zones.json` fitted: one affine for each zone | `fit_zones.py` |
| 5. Plate maker | `base.jpg` + `zones.json` | `id.png`, `uv.png`, `uv_trim.png`, `shade.png`, `plate.json`, `check.png` | `make_plate.py` |
| 6. Swatches | `fabric-sage-640.png`, `lace-pearl-640.png` | de-lit, seamless fabric. Lace with the background keyed to alpha. | `prep_swatches.py` |
| 7. Page | all of the above | `testing.html` (WebGL2, one shader) | — |

All demo files are in `myshoppe/demo/`. Paths in this section are relative to that folder:

```
demo/
├── testing.html
├── docs/render.md            (this file)
├── assets/
│   ├── torso-base.png        source photo
│   ├── fabric-sage-640.png   source fabric swatch
│   ├── lace-pearl-640.png    source lace
│   ├── plates/torso-straight/
│   └── swatches/
└── tools/                    the scripts in the table above (Pillow only)
```

Run the scripts from `demo/`:

```sh
python3 tools/make_base.py     assets/torso-base.png assets/plates/torso-straight/base.jpg /tmp/corner.png
python3 tools/extract_zones.py assets/plates/torso-straight/annotate.png assets/plates/torso-straight/base.jpg \
                               assets/plates/torso-straight/zones.json /tmp/zones-preview.png
python3 tools/fit_zones.py     assets/plates/torso-straight/zones.json assets/plates/torso-straight/base.jpg /tmp/zones-fitted.png
python3 silhouette/pipeline/make_plate.py    assets/plates/torso-straight
python3 swatchprep/prep_swatches.py assets assets/swatches /tmp          # add `fabric` as a 4th argument to skip the lace
```

`fit_zones.py` has the measured `base.jpg` points written in the code (`REAL`). The neck-dip correction after the fit was a one-time step, and it is not in a script.

#### Colour code for annotations (step 2)

| Item | Colour | Line |
|---|---|---|
| Front grid (shoulder line, 2 sides, hem) | Red `#E53935` | Solid |
| Front outline (neck dip, slits) | Red `#E53935` | Dashed |
| Sleeve grids (cap, outer, inner, cuff edge) | Blue `#1E63E9` | Solid |
| Neck trim | Purple `#8E24AA` | Centre line |
| Cuff trims | Orange `#FB8C00` | Centre line |
| Hem trim | Dark gold `#C79100` | Centre line |
| Slit trims | Teal `#00897B` | Centre line |
| Grid corners and landmarks | Black dot, white ring | — |
| Scale | Green `#2E7D32` | On the garment, with a real length in mm |

**Rule:** draw on the real `base.jpg` in a vector or raster editor (Figma, Photopea), on a separate layer. **Do not use an AI image tool.** It redraws the photo, and then the lines do not fit.

#### Files

`assets/plates/torso-straight/`:

| File | Size | Contents |
|---|---|---|
| `base.jpg` | 289 KB | Photo of the dress form with the white straight kurta |
| `annotate.png` | 1.9 MB | Colour-coded annotation (source only, does not ship) |
| `zones.json` | 118 KB | Curves in 1200 × 1600 space |
| `id.png` | 10 KB | R = fabric zone (1 front, 2–3 sleeves). G = trim (1 neck, 2–3 cuffs, 4 hem, 5–6 slits). |
| `uv.png` | 186 KB | Fabric UV in cm. 12 bits for each coordinate: R = U high, G = V high, B = U low · V low. Range 0–128 cm. |
| `uv_trim.png` | 26 KB | Trim UV: U = cm along the trim, V = 0–1 across it |
| `shade.png` | 176 KB | Folds: garment luminance / median. 128 = normal light. |
| `plate.json` | 1 KB | IDs, sizes in cm, scale, UV range |
| `check.png` | 1.2 MB | Checker test image (review only, does not ship) |

`assets/swatches/`:

| File | Size | Contents |
|---|---|---|
| `fabric-sage-1024.jpg` | 427 KB | De-lit and seamless (narrow seam cut, not a wide blend). Assumed tile size: 30 cm. |
| `lace-pearl-2048.webp` | 730 KB | Lace band with alpha. Mirrored along the trim. |

#### `testing.html`

- **Built again from zero.** The old version is not kept in the repo.
- **One WebGL2 fragment shader** on a full-screen triangle. There are no libraries.
- **It draws only when a choice changes.** It keeps the last frame (`preserveDrawingBuffer: true`).
- **Data maps** (`id`, `uv`, `uv_trim`, `shade`) load with `createImageBitmap` (`colorSpaceConversion: "none"`, `premultiplyAlpha: "none"`). The shader reads them with `texelFetch`, with no filtering.
- **Swatches** use `textureGrad`. The gradients come from the plate UV (central difference over ±4 plate px), and only when the neighbours are in the same zone or trim. Otherwise a round footprint from the known scale is used. Thus there are no seams where the UV jumps between zones. A mip bias of −0.5 (`MIP_BIAS` in the shader) and anisotropic filtering (max 8, if the browser has it) are on.
- **Canvas size:** up to 2 × the plate (DPR ≤ 2). When the canvas is larger than the plate, the fabric and trim UV are interpolated between 4 plate texels, only if all four are in the same zone (trim). Shade is read from a second, linearly filtered copy of `shade.png`. Test switch: `?stage=<css px>` makes the stage wider.
- **Edges:** a soft edge from a 3 × 3 sample of the zone map (bilinear mix of the mask when the canvas is larger than the plate).
- **Controls:**
  - Fabric: Original or Sage.
  - Lace on/off: neckline, cuffs, hem, slits.
  - Test: grain checker, photo only.
- **Fallback:** if WebGL2 is not available, or the files do not load, the page shows the photo with a note.
- **It needs an HTTP server.** WebGL cannot read images from `file://`. Run `python3 -m http.server` in `myshoppe/demo/`, then open `/testing.html`.

#### Results

- The fabric follows the body. The weave becomes narrower at the sides of the body and the arms (cylinder correction: 60° for the body, 70° for the sleeves).
- The grain goes straight down on the front and along the arm on the sleeves.
- The real folds of the photo show through all fabrics.
- The lace follows the neckline curve, the cuffs, the hem, and the slits. The fabric shows through the lace holes.
- **Sizes from the plate:** front 44.6 × 105 cm, each sleeve 18.6 × 47 cm.
- The page loads about 370 KB of plate data, plus `base.jpg` and the two swatches.

#### Problems found and fixed

| Problem | Fix |
|---|---|
| The first annotation was drawn by an AI tool. Its photo was not `base.jpg`: 8–60 px off. | Fitted each zone with one affine to points measured on `base.jpg`. Remaining error: 5–11 px. |
| Neck points and shoulder line about 15 px too low | Measured the real points again. Scaled the neck dip to the real opening. |
| Gaps between the sleeves and the front (the two lines were drawn side by side) | The front goes **under** the sleeves: 40 px from the shoulder to the cuffs, 12 px below the cuffs, 10 px at the shoulder tips. |
| Mirrored fabric tiling made diamond patterns | The swatch is made seamless offline (minimum-error seam cut to a half-offset copy, inside 64 px of the tile edge). Normal repeat. |
| The fabric and the lace looked soft and blocky | Plate with one UV per pixel (was 2 × 2 blocks; lace 12 steps across); narrow seam cut instead of a wide blend; `textureGrad` with plate gradients and −0.5 mip bias; interpolation when the canvas is larger than the plate. Numbers: `upscale-results.md` (git history, `da48bfc`). Bodice sharpness 856 → 1335, block ratio 0.43 → 0.03. |
| White halos around the lace | The key uses warmth (red − blue), not darkness. Paper shadows are neutral. |
| The canvas did not show in headless screenshots | Removed the opacity fade. Kept the drawing buffer. |

#### Known problems (not fixed)

- **Pearls in the lace show only as rings.** Their bright centres keyed out.
- **The fit error can still show** as a thin white strip at some places along the sides.
- **The left-side points are mirrored** from the right side. The left side of the photo is in shadow, so we could not measure it.
- **The scale is an assumption:** shoulder width = 370 mm (size M), and fabric tile = 30 cm. Replace both with real measures.
- **The load time and the draw time were not measured on a real GPU.** The headless harness uses virtual time and reports 0.0 ms for the draw. The ≤ 5 ms budget in `upscale.md` (git history, `da48bfc`) is unverified. The new shader does about 8 more `texelFetch` calls for each fabric pixel and for each lace pixel.
- **The silhouette is stair-stepped when the canvas is larger than the plate.** The garment mask is a 1200 px binary raster.
- **The lace swatch (713 KB) is over the 600 KB swatch budget** of the upscale plan.
- **One petal at the corner of the fabric tile is slightly clipped** where two seam cuts meet. Not visible at garment scale.

#### Next steps

1. Image quality (done, see `upscale-results.md` (git history, `da48bfc`); step 5, a 1792 px plate and a 2048 px fabric, was not needed). Open: measure draw time on a real GPU and on a phone; shrink the lace swatch; soft alpha for the silhouette.
2. Draw the annotation again on the real `base.jpg`, in a normal editor. Then the fit step is not necessary.
3. Get one real measurement of the kurta, for the scale.
4. Fix the pearl key: add a rule for small bright round shapes.
5. Make the three close views (neckline, sleeve, hem) with the same pipeline.
6. Add more swatches, and measure the load and draw time on a phone.

### 2026-11-18: `sleeve-straight` plate (shoulder and sleeve view)

- **Source:** `silhouette/sources/sleeve-straight.png` (2048 × 2048). Plate = crop x 512..2048 (the garment runs off the right border), × 0.78125 → 1200 × 1600. A sparkle mark on the garment (bottom right) is covered with a patch of garment from 190 px to the left.
- **Script:** `silhouette/views/sleeve.py` (all points measured on `source.png` on gridded crops, `silhouette/measure/gridcrop.py`; it also runs the checks of `annotate.md` §7.1). Then `silhouette/pipeline/make_plate.py` (11 s).
- **Scale:** shoulder → cuff-out = 470 mm → 0.3382 mm/px. Cross-check: neck-l → neck-r = 140.4 mm; the agreed 158 mm × cos 31° (the form is turned about 31°) = 135 mm.
- **Zones:** `front` 32.4 × 49.9 cm (θ 40°), `sleeve-l` 12.3 × 49.5 cm (θ 70°). Trims: `neck` 12 mm, `cuff-l` 25 mm. Stitches: neck top-stitch (5.3 mm, measured), cuff top-stitch (18.5 mm, measured).
- **Gaps outside every zone:** the wall wedge under the arm (underarm (1042, 977) to (1050, 1399) in source px), and the bare mannequin arm below the cuff, which is in front of the body (a notch in the `front` outline).
- **Tool change:** `make_plate.py` reads an optional `"widthPx"` for a zone. The default (mean of top and bottom edge) gave this sleeve 7.8 cm instead of 12.3 cm, because the sleeve cap is only about 50 px wide, so the fabric was stretched 1.6 × across the sleeve. The sleeve uses area ÷ mean edge length. Torso and neck plates rebuild byte-identical.
- **Checks:** block ratio 0.039, plate data 975 KB (budget 1.0 MB: tight), no crossings, all grid corners meet, outlines closed and simple, trim centres inside their zones.
- **Known problems:**
  - The front uses one symmetric cylinder, but the frame cuts the front near the centre line. The squares also narrow at the right border, where the body does not turn away.
  - The front left edge between y 1399 and 1899 (source px) is hidden by the sleeve and was interpolated.
  - The shoulder → neck check (107 mm) does not apply to a turned view: it measures 72 mm here.
  - A 1–2 px strip of sleeve fabric shows along the lower edge of the cuff trim.
  - The pale diagonal panel under the arm (about (1040–1380, 720–900) in source px) was treated as shading, not a seam.
  - `testing.html` still loads only the torso plate.
- **Review (same day): not accepted yet.** `tools/plate_checks.py` (new) fails two checks:
  - The front grid's left edge bulges **10.7 %** from its chord (limit 5 %; torso 3.9 %, neck 2.6 %).
  - The front grain tilts **18.4°** for 95 % of points (limit 10°; torso 10.0°, neck 8.7°). **Fixed 2026-11-19 (numeric step 5):** the grid edge is now a straight chord under the sleeve; 0.0 % bulge, 4.4° tilt.

  Cause: that grid edge follows the armhole seam, which bulges 161 px in the turned view, so the checker columns make an S-curve across the chest. Correction: make the grid edge a smooth line under the sleeve, and keep the seam only in the outline (`annotate.md` §2, rule 9). The rebuild is byte-identical, and the sparkle patch is clean.

### 2026-11-18: `hem-straight` plate (hemline and chaak)

- **Source:** `silhouette/sources/hem-straight.png` (2048 × 2048). Plate = crop x 214..1750 (the garment is 1583 px wide, so the crop keeps the whole back panel and its hem tip, and cuts 47 px of the shaded left panel at the border), × 0.78125 → 1200 × 1600. The sparkle mark (x 1920–2010) is outside the crop: no patch.
- **Intake:** garment highlights are clipped in the top right (about 120 × 1100 px samples at 252 and above, mostly along the slit and the side seam). Max luminance in the garment is 255, above the limit of 250. I did not reject the image: the clipped area is the lit side seam, about 1 % of the garment, and the folds on the front panel are intact. **Decision needed:** ask for a re-render, or accept.
- **Script:** `silhouette/views/hem.py` (all points measured on `source.png` on gridded crops; silhouettes scanned, then confirmed on crops). Then `silhouette/pipeline/make_plate.py` (11 s).
- **Scale:** slit-top → hem-slit = 240 mm → 0.2221 mm/px. Cross-check: the hem top-stitch is 15 mm above the hem edge (67 px), which matches the 30 mm hem trim with its centre 15 mm up.
- **Zones:** `front` 16.9 × 30.0 cm (θ 45°), `back` (panel right of the slit) 3.0 × 29.5 cm (θ 60°), `back-l` (shaded left panel, seen at a steep angle) 6.3 × 28.0 cm (θ 65°). The shaded left panel is a second front-facing zone, so `ZONE_ID` got `back` = 4 and `back-l` = 5.
- **Trims:** `hem` 30 mm, `slit-l` 8 mm (front slit edge), `slit-r` 8 mm (back slit edge, on the `back` zone), cut at the slit apex. Stitches: slit facing (about 60–90 px inside the front edge), bar tack, hem top-stitch of the front and of the left panel.
- **Outside every zone:** the dress form seen through the slit, the pale inside of the far wall below the form, the stand.
- **Tool changes in `make_plate.py`:** `ZONE_ID` `back` = 4, `back-l` = 5, with checker colours; optional `uvRangeCm` in `zones.json`; `pack()` raises if a value is outside the range. This close view is 0.222 mm/px, so one pixel is 0.022 cm of fabric, but the default 128 cm range resolves only 0.031 cm. Neighbouring pixels shared a UV value (block ratio 0.227), and the quantisation also inflated the grain tilt (11.3°). `uvRangeCm` = 32 fixes both. The torso, neck and sleeve plates rebuild byte-identical.
- **`plate_checks.py`:**
  ```
  PASS  grid bulge front.left              4 px = 0.3 %
  PASS  grid bulge front.right             27 px = 2.0 %
  PASS  UV rate back-l (x face-on)         U 1.06, V 1.00
  PASS  UV rate back (x face-on)           U 1.04, V 1.01
  PASS  grain tilt front (95 %)            9.7 deg (median 4.6)
  PASS  UV rate front (x face-on)          U 1.06, V 1.00
  PASS  block ratio                        0.038
  PASS  plate data                         785 KB
  ALL PASS
  ```
- **Known problems:**
  - `testing.html` still loads only the torso plate, and the zone-id colours of the checker only know ids 1–3 (it shows zones 4 and 5 blue).
  - Hairline gaps (1 px) in the hem trim where the hem polyline bends.
  - The hem trim (30 mm, 135 px) is wider than the real hem band (about 80 px up to the top-stitch): it is the agreed trim width, so the lace would cover part of the garment above the stitch.
  - The slit trims start about 5 mm below the apex, because the trim is clipped to the outline.
  - The two edges of one slit use `slit-l` (front) and `slit-r` (back): `FLIP` in `testing.html` flips `slit-r` already, but the lace direction is not checked in the page.
  - One cylinder for each zone: the `back` strip is only 3 cm wide, and its squares narrow towards the tip as a real turned panel would, but this is an approximation.

### 2026-11-19: polish of the fabric and lace overlay (`polish.md` (git history, `da48bfc`), results in `polish-results.md` (git history, `da48bfc`))

| Step | What changed | Measured |
|---|---|---|
| 1 Lace shadow | soft shadow of the lace on the fabric, offset on the screen (right, down), ≤ 35 % | 0 px changed outside the trims; darkest 17–35 % |
| 2 Linear light | `SRGB8_ALPHA8` textures, shade stored as linear ratio with a sqrt code, sRGB encode at the end | mean luminance +0.15 / +0.87 %; the fold contrast was not lost before (step 0 finding) |
| 3 Shade without the weave | masked guided filter, 1.2 mm, ε 0.006 | weave band −75 to −90 % (neck, sleeve, hem), folds kept 97–99 %; torso unchanged (fallback) |
| 4 Lace repeat | whole-period tiles, `REPEAT`, whole repeats per trim, centred / end-aligned starts | pearl, geometric, fine have periods; leaf keeps the mirror; 35 of 36 trims fitted |
| 5 Edging lace | hem and cuff laces hang past the edge by their decorative depth; strips oriented, no `FLIP` | only pearl and geometric have a clean edge |
| 6 Lace relief | material map (height, metal, pearl); relief ±15 %, zari highlight, pearls filled | metal only on fine; 6 pearls per repeat |
| 7 Fabric | displacement in folds ≤ 1.5 mm, per-fabric sheen (all matte now), hex anti-tiling on mocha and mustard | repeat autocorrelation 1.0 → 0.005 (offline) |

Plate data: torso 437, neck 381, sleeve 726, hem 481 KB. Lace assets: pearl 524, leaf 409, geometric 212, fine 180 KB.

**Known problems after the polish:**
- **Not seen in a real browser.** Screenshot runs were stopped after step 2 (25–30 min per set on this machine). Steps 2–7 were checked offline (plates, assets, simulations, code review, JS syntax). The shader has not been compiled since step 4; the draw time (≤ 5 ms) was never measured. Open the page, check the console, and walk the switches before relying on it.
- **Fine (zari) lace:** the paper inside the loops was never keyed (alpha 1). It cannot hang past an edge and its loops show cream paper. Re-key or photograph again.
- **Leaf lace:** no repeat found (irregular); mirror kept, axis at the centre front.
- **Geometric lace:** the scallop edge (80 px) and the diamonds (177.7 px) have no common repeat in the short band: a soft scallop jog at each wrap.
- **Pearl lace on the hem view:** the hem is 3.4 repeats long; not fitted (a motif is cut at one end).
- The scale values (`repeatCm`, lace `widthMm`) are still assumptions.

### 2026-11-19: live neckline and the showcase (`halfway.md` (git history, `da48bfc`), results in `halfway-results.md` (git history, `da48bfc`))

| Step | What changed | Measured |
|---|---|---|
| 1 Decode | blobs kept for all views, one view decoded at a time, bitmaps closed after upload | 0 MB decoded after 12 switches (was 161 MB) |
| 2 Live curve | neck area in `id.png` B, full-grid UV, `plate.json neck`; design record in mm (`assets/looks/`); 24-point live edge | default mean ≤ 0.009; ±20 mm moves the CF edge by mm ÷ mmPerPx (±0.08 px) |
| 3 Reveal fills | edge band follows the live edge; smooth shade for new fabric; form fill (local light, hex-tiled form patch, CF tape, contact shade) | step across the old edge = the light's own change; no repeat |
| 4 Pivots | 3 SVG handles on rails, snap stops, mouse / touch / keys, ARIA sliders | checked with real input events |
| 5 Live trim | neck lace from the live centre line; fit to the live length | median 0.3 px against the baked trim |
| 6 Torso | one record, per-view mapping; sleeve view keeps its neckline with a note | changes agree within 0.3 mm; the photos' absolute depths differ by 15.7 mm (fallback) |
| 7 Showcase | journey bar, cross-fade, glow, hold for before, lace cards, review with 3 close views, share PNG, phone layout | each step shows its view in < 0.6 s (SwiftShader) after the first visit |

**Verification:** `silhouette/checks/cdp_shot.mjs` (headless Chrome through the DevTools protocol) saves the canvas pixels and the console errors, and sends real mouse, touch and key events. The shader compiles. Open: draw time and the frame rate during a drag on a real phone, the memory panel, and a person's walk through the journey.

### 2026-11-20: numeric plates (`numeric.md` (git history, `da48bfc`), results in `numeric-results.md` (git history, `da48bfc`))

The page builds `id`, `uv`, `uv_trim` and the shade itself, on the GPU, from the curves (`plate.js`, `maps.js`) in `plate.dat`; the four map images are not sent. First visit, 4 views: 1.67 MB (was 3.64 MB); `plate.dat` 21.7 KB for the 4 views. The built maps match the PNG maps: zones to 1 px at the edges, uv with no bias and a median of 0.35 px (the PNG's own jitter), trims likewise, the garment shade to ±1 level. The sleeve view's front grid was fixed (grain tilt 18.4° → 4.4°). **Open:** the build time on a real GPU (1.4–3 s in software rendering, so the budgets are unverified); `?geom=maps` gives back the PNG maps.

### 2026-11-22: StepA, the silhouette closed to the photo's edge (`plan/StepA.md`, results in `plan/StepA-results.md`)

- **One plate file:** `plate.dat` (BSP2) holds typed edges (free, seam, frame, cut), zones as chains of edges, fabric frames, trims, landmarks and decisions. A plate folder holds `base.jpg` + `plate.dat`; the pipeline is `demo/silhouette/` (`plate.py`).
- **Edges:**
  - The torso was measured on its photo.
  - Free edges are snapped to the photo's 50 % crossing.
  - The fabric frame (axis, cylinder, sag) replaces the Coons patch: no fold, grain ≤ 2.94°, page = build to 10⁻¹⁴ cm.
  - Exact 16-bit maps on the page; soft free edges.
  - Rim (mocha) 0.25 / 0.00 / 0.88 / 2.61 %, from 5.7 / 26 / 7.0 / 16.2 % at step 0.
- **Laces** (the extension): each lace lies along its edge at its own width and repeat (the trim field). There are no wedges, streaks or fans, and the slit and hem laces mitre. The ends go out to the silhouette, the overhang takes the garment's light, and the live neck lace hangs on the live edge.
- **Re-read on the photos:** the torso hem over the stand; the right sleeve seam; the slit corner. The neck view's arm "gaps" are now garment.
- **Build time:** 1.05–1.19 s per view in software rendering (`numeric`: 1.4–3.0 s).
- **Open:**
  - closure on the sleeve view (0.06 %);
  - the rim on the sleeve and hem views;
  - the halo's 95th percentile on 3 views;
  - step 8 on a phone and a laptop;
  - the neck-depth agreement of the two front views.

## 12. Sources

- [Nukepedia: Understanding UVMaps, Warping with STMap](https://www.nukepedia.com/written-tutorials/understanding-uvmaps-warping-with-stmap-pt-2)
- [Foundry: STMap reference](https://learn.foundry.com/nuke/content/reference_guide/cara_vr/c_stmap.html)
- [Notch: UV remapping workflow (AOV)](https://manual.notch.one/2026.2/en/docs/learning/working-with-video/uv-remapping/uv-remapping-workflow-aov/)
- [Autodesk Maya: UV multi-render pass workflow](https://help.autodesk.com/cloudhelp/2016/ENU/Maya/files/GUID-D37E1D6E-982E-4938-943E-C67B6110FB13.htm)
- [Blender #83842: colour management applied to AOVs](https://projects.blender.org/blender/blender/issues/83842)
- [Blender #105866: UV AOV mismatch](https://projects.blender.org/blender/blender/issues/105866)
- [CLO3D: Multiple garments, UV issue](https://support.clo3d.com/hc/es/community/posts/360037442274-Multiple-garments-in-one-scene-UV-issue)
- [WebKit bug 200964: large SVG filter region slow](https://bugs.webkit.org/show_bug.cgi?id=200964)
- [WebKit bug 191197: SVG filters slow on iOS](https://bugs.webkit.org/show_bug.cgi?id=191197)
- [Mozilla bug 1883933: feDisplacementMap not accelerated](https://bugzilla.mozilla.org/show_bug.cgi?id=1883933)
- [Learn WebGL: texture mapping using images](http://learnwebgl.brown37.net/10_surface_properties/texture_mapping_images.html)
- [WebGL Fundamentals: image processing](https://webglfundamentals.org/webgl/lessons/webgl-image-processing.html)
- [Chaos: Cylindo and pre-rendered variations](https://www.chaos.com/blog/leveraging-chaos-cloud-for-undecillions-of-product-variations)
- [Kickflip: 2D configurator, when it is better than 3D](https://gokickflip.com/blog/2d-product-configurator)

No public source describes this exact UV-pass fabric swap on a product photo in a browser. Each part has a source. The combination is our design.
