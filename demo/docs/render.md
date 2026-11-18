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

### 6.3 Passes for each plate

A **plate** is one view of one shape variant. Each plate has these files:

| File | Contents | Use in the browser |
|---|---|---|
| `uv.png` | U and V, 16-bit, packed into 8-bit channels (see 6.5) | Where each fabric pixel comes from |
| `shade.webp` | Grey light and ambient occlusion on neutral cloth | Folds and drape |
| `id.png` | One flat colour for each zone | Which fabric or lace goes where; toggles; click targets |
| `spec.webp` (optional) | Highlights only | Sheen on silk, satin, mashru |
| `detail-*.webp` (optional) | Isolated RGBA layers, for example an embroidery motif in grey | Toggled details; the shader tints them with the thread colour |

The dress form itself is a normal photo or render in the background of each plate.

### 6.4 Offline steps (one time for each plate)

1. Make the garment in CLO3D. Keep the real-scale UVs for each pattern piece (do not use unified UVs). Then a 10 cm motif measures 10 cm on the body.
2. Set the four cameras of section 3. Lock them. All looks use the same cameras.
3. Use a neutral mid-grey fabric. Render the passes of 6.3 for each shape variant.
4. Export the UV pass as 16-bit or 32-bit EXR. Treat it as data: do not apply colour management (see Blender issue #83842).
5. Convert the EXR to the packed PNG, then convert shade and spec to WebP. Do this with a script in the worker. Pillow is already in the backend.
6. Record the plate in the registry (section 7).

Fabric and lace swatches also need one step: remove the light (de-light the swatch) and make the brightness even. If you do not, the shade pass darkens the cloth two times. Dark fabrics then lose all their folds.

The base form for the `torso` view must be a **bare** dress form. If the form wears a white kurta, a wide garment (anarkali, lehenga) goes past the kurta onto the wall. The shading is then not correct. Also remove the AI sparkle mark from `assets/torso-base.png`.

### 6.5 In the browser

- One `<canvas>`, one full-screen quad, one fragment shader of approximately 30 lines. No Three.js.
- The shader does: `fabric = texture(swatch[zone], decodeUV(uv) * scale)` → `colour = fabric × shade + sheen × spec` → toggled zones and detail layers on top.
- 4–6 textures. WebGL guarantees a minimum of 8 texture units.
- Draw **only when a choice changes**. Do not use an animation loop.
- Precision: browsers decode PNG to 8 bits for each channel. 8 bits is not sufficient for UVs. Put U into R + G (high byte, low byte) and V into B + A. Set `UNPACK_PREMULTIPLY_ALPHA_WEBGL = false` and `UNPACK_COLORSPACE_CONVERSION_WEBGL = NONE`. You can also use two RGB PNGs.

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
python3 tools/make_plate.py    assets/plates/torso-straight
python3 tools/prep_swatches.py assets assets/swatches /tmp          # add `fabric` as a 4th argument to skip the lace
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
- **Swatches** use `textureGrad`. The gradients come from the plate UV (central difference over ±4 plate px), and only when the neighbours are in the same zone or trim. Otherwise a round footprint from the known scale is used. Thus there are no seams where the UV jumps between zones. A mip bias of −0.5 (`uMipBias`) and anisotropic filtering (max 8, if the browser has it) are on. Test switches: `?bias=<n>`, `?aniso=0`.
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
| The fabric and the lace looked soft and blocky | Plate with one UV per pixel (was 2 × 2 blocks; lace 12 steps across); narrow seam cut instead of a wide blend; `textureGrad` with plate gradients and −0.5 mip bias; interpolation when the canvas is larger than the plate. Numbers: `docs/plan/upscale-results.md`. Bodice sharpness 856 → 1335, block ratio 0.43 → 0.03. |
| White halos around the lace | The key uses warmth (red − blue), not darkness. Paper shadows are neutral. |
| The canvas did not show in headless screenshots | Removed the opacity fade. Kept the drawing buffer. |

#### Known problems (not fixed)

- **Pearls in the lace show only as rings.** Their bright centres keyed out.
- **The fit error can still show** as a thin white strip at some places along the sides.
- **The left-side points are mirrored** from the right side. The left side of the photo is in shadow, so we could not measure it.
- **The scale is an assumption:** shoulder width = 370 mm (size M), and fabric tile = 30 cm. Replace both with real measures.
- **The load time and the draw time were not measured on a real GPU.** The headless harness uses virtual time and reports 0.0 ms for the draw. The ≤ 5 ms budget in `docs/plan/upscale.md` is unverified. The new shader does about 8 more `texelFetch` calls for each fabric pixel and for each lace pixel.
- **The silhouette is stair-stepped when the canvas is larger than the plate.** The garment mask is a 1200 px binary raster.
- **The lace swatch (713 KB) is over the 600 KB swatch budget** of the upscale plan.
- **One petal at the corner of the fabric tile is slightly clipped** where two seam cuts meet. Not visible at garment scale.

#### Next steps

1. Image quality (done, see `docs/plan/upscale-results.md`; step 5, a 1792 px plate and a 2048 px fabric, was not needed). Open: measure draw time on a real GPU and on a phone; shrink the lace swatch; soft alpha for the silhouette.
2. Draw the annotation again on the real `base.jpg`, in a normal editor. Then the fit step is not necessary.
3. Get one real measurement of the kurta, for the scale.
4. Fix the pearl key: add a rule for small bright round shapes.
5. Make the three close views (neckline, sleeve, hem) with the same pipeline.
6. Add more swatches, and measure the load and draw time on a phone.

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
