# Plan: StepA — the silhouette, closed to the photo's edge

Status: **in progress**: steps 0–7 done (uncommitted from step 3 on; one commit for the rest of StepA); the extension (§8, steps L1–L5) next; then steps 8 and 9. Branch `stepA` (from `numeric`, 430c3fd), worktree `../myshoppe-stepA`.
Compare: **http://localhost:8200/testing.html** (`numeric`, the reference) and **http://localhost:8300/testing.html** (this worktree).
Read first: `docs/breather.md` (what is where). Background: `DedhD.md` §11 (option A, and the facts in §11.1). Product: a visualiser, 4 fixed views, **no 3D, no pan, no zoom**.
Scope: the straight kurta, 4 views (torso, neck, sleeve, hem). Swatches and laces are the next plan; `main` is merged after that one (`DedhD.md` §11, agreed order).

## 1. Final expected behaviour

When StepA is closed, this is true:

**What the customer sees**
1. On every view, the fabric covers the garment **to the photo's own edge**. No white or grey rim of the original garment remains along the shoulders, the sides, the underarms, the sleeves, the cuffs, the hem corners or the slit, with any fabric, at 2× on a phone screen.
2. Where two parts meet (front and sleeve, front and back pieces), the edge between them is the photographed seam: no hairline, no step, no double edge.
3. Free edges (garment against wall, form or mannequin arm) are soft like the photo's own edge: no stair steps, no halo.
4. The print lies on the body as cloth does: warp lines straight down the centre front and along each sleeve, squares of the same real size in all 4 views, no S-curves, no stretch at the sleeve cap. Each print starts from fixed points of the garment (the centre front and the neck-point line; the shoulder point on a sleeve).
5. Every lace lies on its edge at its real width and repeat, with no streak, wedge or fan. Where it goes out of sight (cuffs, hem, neck), the silhouette cuts it; the slit and hem laces meet in a mitre. (Extension, §8.)
6. The live neckline works as now: handles, the area a change reveals, the torso view following.

**What a plate is**

7. **A plate folder holds three files** (since the cleanup, 2026-11-22, `plan/cleanup.md`: the two that ship; `source.png` lives in `demo/silhouette/sources/<plate>.png`):

   | File | What it is | Ships |
   |---|---|---|
   | `source.png` | The image as received (the input; it is measured) | No |
   | `base.jpg` | The 1200 × 1600 photo, made from `source.png` | Yes |
   | `plate.dat` | Every number of the view: edges, frames, trims, stitches, landmarks, occluders, scale, and the decisions taken from the image | Yes |

   - No JSON, no map image, no review image in a plate folder.
   - The **source** of a plate is `source.png` + `silhouette/views/<view>.py` (the measured points). `silhouette/pipeline/make_plate.py <plate>` builds `base.jpg` and `plate.dat` from them, deterministically.
   - `python3 silhouette/pipeline/platedat.py --dump <plate>` prints a `plate.dat` as text. `git diff` shows that text (a `diff=dat` textconv).
   - Review images (`annotate.png`, `check.png`, the edge crops) are made on demand into `demo/review/<plate>/`, which is not committed.
8. A zone's outline is a chain of **typed edges**: `free` (snapped to the photo), `seam` (one list shared by two zones), `frame` (the image border), `cut` (the live neck dip). Trims and stitches are **derived** from the edges (an offset in mm), not traced.
9. A zone's fabric coordinates come from a **fabric frame** (an axis, an anchor, a cylinder), defined everywhere around the zone. The outline alone decides where the fabric shows. **No Coons patch, no grid edges, no `tuck`, no `widthPx`, no `smooth_under`.**
10. The torso plate is measured from its photo by `silhouette/views/torso.py`, both sides, like the other views. No traced annotation image, no affine fit, no mirrored side.
11. Every plate passes `silhouette/checks/plate_invariants.py` (closure, edge accuracy, gaps, frame, trims, landmarks). A new plate must pass it or say why.
12. The shade is built on the GPU. Only if step 8 finds a device without float render targets does a small `shade.webp` ship as a fallback: then it is the one exception to item 7, and step 8 writes why.

**How fast**

13. The page builds a view's maps with one exact pass for each zone and trim: faster than `numeric` in the same software renderer, ≤ 50 ms on a laptop and ≤ 250 ms on a mid-range phone, read from a `?perf=1` overlay on a real device (step 8).

## 2. Why the Coons patch is still here, and why it goes

**Where it came from.** The first test plate (`render.md` §11, 2026-11-18): "Fabric zone: 4 edges. A Coons patch fills them." It turned a hand-traced annotation into fabric coordinates quickly.

**Why it stayed.** No later plan had the job of questioning it:
- `upscale`, `polish` and `halfway` were gated on "pixel-identical to the previous port".
- `numeric` ported it to JavaScript to 3 × 10⁻¹¹ px (`plate.js` `coons`) and then calibrated the GPU to imitate the PNG painter: the zones drawn 5 times, shifted by `grow` 0.5 px; `idOff`; `uvOff` (−0.5, −0.5); the 12-bit packing.
- `rebuild_check.sh` requires the PNG maps to stay byte-identical.

Identity gates protect a refactor. They also keep the first method's defects.

**What it costs.** Coverage today is **grid ∩ outline** (`maps.js`, the id pass). Every free edge is drawn twice: once as the outline and once as a grid edge. Both must reach the real edge, or the photo's white garment shows. Each workaround below exists because of that, or because the fabric scale and grain come from the traced edges:

| Workaround | Why it exists |
|---|---|
| `tuck` (`tip`, `reach`, `yFull`, `yZero`, `below`, `profile`, `exempt`) | Pushes the front's grid and outline under the sleeves, because the grid's side edges stop at the seam |
| `snap_outline.py shoulders` | Had to rewrite the outline's run **and** the grid's top edge |
| `widthPx` (sleeve) | The fabric width is the mean of the grid's top and bottom lengths. A short cap made the sleeve 7.8 cm wide instead of 12.3 cm, so the squares stretched. |
| `smooth_under` and the 5 % bulge rule (`annotate.md` §2, rule 9) | A grid edge on a bulging seam bent the whole bodice: grain tilt 18.4° on the sleeve plate |
| "The grid top never follows the neck dip" | The patch would fold the fabric into the dip |
| Origin at each zone's grid corner | No shared fabric frame (`DedhD.md` §11.1, item 2) |
| `v = j / nt × height` | The fabric's vertical scale follows the traced left and right lengths, not the body |

**Coons is removed, not refactored.** Its defects are its definition: a Coons patch is made from 4 boundary edges, so every free edge must be traced twice, and the grain follows those traced edges. Repairing it inside the patch means more workarounds of the `tuck` kind. Step 4 replaces it; `?frame=coons` exists only as a before and after switch until step 7, which deletes `coons()` from `make_plate.py` and `plate.js` with the grid edges.

**The torso plate was never measured.** It was traced from a drawn annotation (`extract_zones.py`, "throwaway"). Then each zone was fitted with one affine (`fit_zones.py`, "throwaway"), with **the right side measured and the left mirrored about x = 600**. The body-side strip, the slit landmarks 10 px outside the zone, and the shoulder wedges of `numeric` steps 9 and 11 come from this.

**The replacement, and why it was chosen:**

| Method | Needs | Defined outside the outline | Grain | Chosen |
|---|---|---|---|---|
| Coons patch (now) | 4 traced edges per zone | No | Follows the traced edges | No |
| Harmonic or mean-value map | The boundary | No | Follows the boundary | No |
| Thin-plate spline on landmarks | Many landmarks | Unstable | Follows the landmarks | Only as a small correction (step 4, optional) |
| **Anchored cylinder frame** | An axis, an anchor, a half-width profile, `thetaDeg` | **Yes** | Straight along the axis by construction | **Yes** |

The cylinder is already the model of the cross direction (`thetaDeg`, the `asin` correction). StepA makes it the whole map, with the axis and the anchor from the garment instead of from the zone's corners.

## 3. Rules

- One step = one commit on `stepA`. A step that changes the render on purpose says so, and shows before and after crops.
- **No pixel-identity gate against `numeric`.** The gates are the invariants of the plate (edges, coverage, frame), the render-level closure check, and a person at 2×. Port 8200 is for before and after views.
- Each step that changes behaviour has a test switch for the old behaviour **until step 7**. Step 7 removes all of them.
- **A plate folder holds `source.png`, `base.jpg` and `plate.dat` only**, from step 1 on. Every tool reads and writes plates through `silhouette/pipeline/platedat.py`; nothing reads a JSON plate file.
- **Nothing is edited by hand in a plate.** A change is a change to `silhouette/views/<view>.py` (or to a tool), then `make_plate.py <plate>`. The rebuild check (step 1) proves the folder is what the source makes.
- `make_plate.py` (Python, Pillow only) stays the offline reference. It rasterises the maps **in memory**, for the checks and the review images, and writes no map files. `plate.js` is the page's copy of the maths. A parity test keeps the two equal.
- Measure on `source.png`. Edge snapping reads `base.jpg` and the plate frame.
- Review images go to `demo/review/<plate>/` (in `.gitignore`). An image that a results file cites is copied into `docs/plan/img/`, as before.
- Results: `docs/plan/StepA-results.md`, one section for each step. A FAIL is written with its measurement, as an open item.
- Review shots: `node silhouette/checks/cdp_shot.mjs <out> <free port> ...`; the edge crops of step 0 at 2×.

## 4. Steps

### Step 0: Baseline, review set, closure in the render

**Do:**
1. Branch `stepA` from `numeric` (430c3fd), worktree `../myshoppe-stepA`, port 8300. Create `StepA-results.md`.
2. **Review set:** `silhouette/checks/edge_crops.py <canvas> <plate>` cuts fixed 2× crops into one sheet: one crop at each landmark (shoulders, underarms, cuffs, neck corners, hem corners, slit top), and one every 150 px along each free edge. The crops are computed from the plate, so they need no file of their own.
3. **Closure in the render:** `silhouette/checks/fringe.py <canvas.png> <plate>` counts, with a dark fabric (mocha) and lace off:
   - pixels where the photo is garment (the saturation rule of `plate_invariants.py`) and the render still shows the photo (≤ 4 levels from `base.jpg`): the count, the share of the garment, and pieces wider than 1 px;
   - a **rim**: free-edge pixels brighter than both their inner and outer neighbours by more than 8 levels: the share of the free-edge length.
4. Baseline on 8200, all 4 views: `plate_invariants.py`, `fringe.py`, the edge-crop sheets.

**Accept:**
- [ ] Baseline table (invariants, fringe, rim) and 4 crop sheets in the results.
- [ ] `fringe.py` finds the known defects: the torso body-side strip, the hem's 43 px piece, the shoulder slivers.

### Step 1: One plate file (`plate.dat` version 2) with typed edges

**Why:** a plate must be one set of numbers built from its source, not three files edited by different tools. And an outline must say, for each run, what kind of edge it is: only free edges are snapped, a seam is one list, trims hang on edges.

**Do:**
1. `silhouette/pipeline/platedat.py` (a module and a command, Pillow-free): the version 2 format (`BSP2`), a reader, a writer, a validator and `--dump` (text, stable order).
   - **edges:** `{name: {type: free | seam | frame | cut, points, zones: [a, b] for a seam}}`;
   - **zones:** `{order, outline: [[edge, +1 | −1], ...], grid (until step 7), frame (step 4)}`;
   - **trims:** `{edge, from, to (landmark or arc fraction), widthMm, type, join}`; **stitches** the same, with `offsetMm`;
   - **occluders, landmarks, openings, scale, the view's settings, and the decisions** that `make_plate.py` takes from the image (trim sides, the shade median, the neck block's fill colours and form patch).
   - The header lists every curve by index, as `BSP1` does; identical curves are stored once.
2. `silhouette/views/neck.py`, `annotate_sleeve.py` and `annotate_hem.py` become importable: they return the measured data. Run alone, they still run their own checks. The hem's `hem-bl` and `hem-br` (now made by `snap_outline.py edge-trim`) and the trim order (`snap_outline.py trim-order`) become trim data in `annotate_hem.py`.
3. `silhouette/pipeline/make_plate.py <plate> [--review]` = the build: annotation data → (step 3: snap) → decisions → `base.jpg` + `plate.dat`. `--review` writes `annotate.png`, `check.png` and the edge crops into `demo/review/<plate>/`.
4. The torso has no annotate script until step 2: its current data is imported into `plate.dat` once, by a one-off converter that is deleted in the same commit.
5. Every reader moves to `platedat.py`: `plate_invariants.py`, `plate_checks.py`, `snap_outline.py`, `polish_metrics.py`, `reveal_metrics.py`, `map_diff.py`, `mesh_check.mjs`, `trim_match.py` (the last three until step 7 deletes them), and the page (`parseDat` version 2, in `plate.js`, `maps.js`, `testing.html`). `grep -l "zones\.json\|plate\.json"` over `tools/` and the page code then finds nothing. `BSP1`, `make_dat.py`, `dat_check.mjs` and the page's `?dat=0` path are removed.
6. **Removed from the 4 plate folders:** `zones.json`, `plate.json`, `annotate.png`, `check.png`. The map PNGs stay until step 7 (they are the `?frame=coons` reference).
7. `.gitattributes`: `demo/assets/plates/*/plate.dat diff=dat`. `tools/README.md` gives the one-line `git config diff.dat.textconv` setting.
8. `silhouette/checks/rebuild_check.sh`: rebuild every plate from its source into a scratch copy; `base.jpg` and `plate.dat` must be byte-identical to the committed ones.

**Accept:**
- [ ] Each plate folder holds `source.png`, `base.jpg`, `plate.dat` (and the map PNGs until step 7), nothing else.
- [ ] `--dump` of each new `plate.dat` gives back every number of the old `zones.json` + `plate.json` (a test compares them once, then the test is deleted).
- [ ] The render at 8300 = 8200 (mean ≤ 0.5): the outlines are the same points at this step.
- [ ] Each seam is referenced by exactly two zones; each run of each outline has a type; the validator passes on all 4 plates.
- [ ] `rebuild_check.sh`: neck, sleeve and hem byte-identical from their sources. Torso: from its imported data until step 2.
- [ ] `git diff` on a changed `plate.dat` shows text.

### Step 2: The torso, measured

**Why:** the torso is the largest view, and its outlines come from a traced image, an affine fit and a mirrored side (§2).

**Do:**
1. Move `assets/torso-base.png` to `silhouette/sources/torso-straight.png`.
2. `silhouette/views/torso.py` from the nearest template (`annotate_neck.py`), with gridded crops of `source.png` (`annotate.md` §6). **Both sides are measured; nothing is mirrored.** Typed edges, the landmarks of both sides, the trims from the edges. `make_base.py` folds into it (the base crop, as the other views do).
3. Re-check the scale assumption (shoulder width 370 mm) against the neck view's 158 mm neck width. Write both in the results.

**Accept:**
- [ ] The automatic checks of `annotate.md` §9.1 pass. A person approves the review image `annotate.png`.
- [ ] Every landmark of the torso is measured. The left and right landmarks differ from a mirror where the photo differs (written as a table).
- [ ] The plate builds from its source (`rebuild_check.sh`) and renders with the old grid method (step 4 replaces it). Render switch `?torso=v1` gives back the imported plate.

### Step 3: Free edges snapped to the photo

**Do:**
1. `silhouette/pipeline/snap_edges.py` (a module of the build, with `--dry --preview <png>` for a look): for every **free** edge (and the occluders' edges):
   - sample along the edge every 2 px; on each normal, a local colour model (the mean colour inside and outside, 3–8 px from the edge) and the **sub-pixel 50 % crossing** of the projection between the two (±8 px search);
   - a robust smooth fit (data term + curvature term; points more than 1.2 px off the fit are dropped), points every 2 px;
   - **weak spans** (inside and outside colours closer than a threshold: a fold against a similar background) keep their measured points and are listed.
2. Snapping is a step of `make_plate.py`, not an edit of the data: the measured points stay in the annotate script, the snapped points go into `plate.dat`. The same source gives the same snap.
3. Seams are not moved. A seam's ends follow the free edges that meet them.
4. Trims and stitches are rebuilt from their edges (an offset in mm, then a light smoothing over 4 mm, so that a drape stays and the pixel noise goes). The `cuff-l` centre follows the smoothed cuff edge.
5. The neck corners snap too. Re-measure the default neckline (depth from the corner line); update the look's default (`assets/looks/straight-kurta.json`, a look, not a plate file) if it changes, and record the change.

**Accept (outline-only coverage, in memory: the grid still limits the render until step 4):**
- [ ] Edge accuracy for each free edge, against the crossing: median ≤ 0.3 px, 95 % ≤ 0.75 px, max ≤ 1.5 px. Weak spans ≤ 5 % of each edge, listed.
- [ ] Outline closure ≤ 0.02 % of the garment, no piece wider than 1 px, on all 4 plates.
- [ ] Trim offset: mean within 0.5 px of half the strip, std ≤ 1.0 px (`cuff-l` included). Trim smoothness as now.
- [ ] `rebuild_check.sh` passes (the snap is deterministic).

### Step 4: The fabric frame replaces the Coons patch

**Do:**
1. A `frame` for each zone, measured in the annotate script and fitted by the build, stored in `plate.dat`:
   - `axis`: the warp line through the zone (the centre front for a front zone, the sleeve's centre line from the shoulder point to the cuff centre, the centre of a back piece), a smooth polyline;
   - `anchor`: the frame's origin in garment terms: u = 0 on the axis, v = 0 on the neck-point line (front), at the shoulder point (sleeve). In a view without the anchor (the hem view), v0 comes from a landmark with a known distance (the slit top);
   - `half`: the half-width profile, left and right, along the axis: a smooth fit (cubic) to the snapped free edges, or to the seam where the zone goes under another one. The cap of a sleeve continues the sleeve's profile (no stretch);
   - `thetaDeg` (as now) and `sag`: the curvature of the weft lines (fitted to the hem or the cuff, wavelengths over 40 mm only).
2. The map, for a pixel: its position along the axis gives v (arc length in mm, plus the sag term) and its distance from the axis gives u (the cylinder arc: `asin`, continued linearly past the silhouette). It is defined everywhere in the zone's box + 16 px.
3. Coverage = **the outline only**. At a seam, the lower zone runs `underPx` (6 px) under the upper one; the upper zone ends on the seam. This replaces `tuck`.
4. `make_plate.py` evaluates the frame per pixel (in memory) for the checks and the review images. `plate.js` gets `frameUV(zone, x, y)`. `silhouette/checks/frame_check.mjs` compares the two at 10,000 points.
5. The neck area: its uv comes from the frame (it is defined there already); the neck block's corner line is the neck-point line of the anchor, not the grid's top.
6. Optional, only if the person check at the hem asks for it: a thin-plate-spline correction pinned to the hem line with a low weight, so that the print follows the hem's drape.
7. Test switch `?frame=coons` (the old map, from the grid that `plate.dat` still carries) until step 7.

**Accept:**
- [ ] Frame checks in `plate_invariants.py` (replacing `plate_checks.py`'s grain, bulge, UV-rate and block-ratio rules):
  - the map has no fold (positive Jacobian) everywhere in the zone + 16 px;
  - constant-u lines lie within 3° of the axis in 95 % of the zone (now 10°);
  - the UV rate at the axis is within ±2 % of face-on (`mmPerPx` / 10);
  - u = 0 passes through the centre-front landmarks within 1 px.
- [ ] Parity: `frame_check.mjs`, ≤ 10⁻⁴ cm.
- [ ] Closure in the render (`fringe.py`): ≤ 0.02 %, no piece wider than 1 px, on all 4 views (openings excepted). No hairline gaps (0 px); the neck plate's 249 px are gone or explained.
- [ ] Cross-view: the landmarks seen in two views (neck points, shoulder point, slit top, cuff) have their (u, v) in each view written as a table (information; the gate belongs to the swatch plan).
- [ ] The neckline: a depth change of ±20 mm moves the edge by the right px (±1 px); no hole at the corners at the range ends; the reveal fills as before.
- [ ] A person, at 2× on the grain checker and on mocha: straight warp, square 2 cm cells, no S-curve, no stretch at the sleeve cap, in all 4 views.

### Step 5: Exact maps on the page

**Do:**
1. `maps.js`: one draw for each zone (the outline into the stencil, then the frame's uv evaluated per pixel in a fragment pass inside the outline + `underPx` at seams), one for each trim ribbon (built from its edge). **Removed:** the Coons mesh, `grow` (5 shifted draws), `idOff`, `uvOff` (the double uv draw), the `idImage` path, `?cell`, `?mapoff`.
2. **16-bit packing** for uv and uv_trim (RG = u, BA = v; 65,536 steps): no float extension needed, 0.02 mm steps over 128 cm (12-bit: 0.31 mm). The main shader's decode follows.
3. `?perf=1`: an overlay on the page with the build time of the view (with the 1 px readback of `?syncbuild=1`), the draw time and the frame rate of a drag, and whether `EXT_color_buffer_float` is present, so that it can be read on a phone without tools.

**Accept:**
- [ ] The page's maps against `make_plate.py`'s in-memory maps: coverage identical except a 1 px antialiased edge band; uv within 0.01 cm; trims within 0.05 px along and across.
- [ ] Build time in the software renderer ≤ `numeric`'s (1.4–3.0 s): written for each view.
- [ ] `plate.dat` of the 4 views ≤ 40 KB in all.

### Step 6: Soft free edges

**Why:** the photo's edge pixel is a mix of garment and background. A hard switch from fabric to photo leaves a grey rim (`numeric` step 9: "a fine grey rim of 1 px").

**Do:**
1. id A = the coverage of free edges, from the exact sub-pixel distance to the outline (a 1 px ramp centred on the 50 % crossing). Seams and cuts stay hard.
2. The shader: at a free-edge pixel, colour = coverage × fabric + (1 − coverage) × the photo **one and a half pixels outward** along the coverage gradient (the background without the garment's white).
3. Test switch `?softedge=0` (hard, exact edge) until step 7.

**Accept:**
- [ ] Rim (`fringe.py`): ≤ 0.5 % of the free-edge length on all 4 views, with mocha and with sage.
- [ ] No halo: the edge's luminance step in the render is within 10 % of the photo's own step (the same crops).
- [ ] A person, on the edge-crop sheets at 2×: cannot find a white or grey rim in 10 s per crop.

### Step 7: Remove the old artifacts; docs and skills

**Do:** remove everything in §5 marked "step 7", including the grid section of `plate.dat` and the map PNGs. Rewrite the docs and the skills for one plate file, typed edges and frames.

**Accept:**
- [ ] Each plate folder holds exactly `source.png`, `base.jpg`, `plate.dat`.
- [ ] `grep -rniE "coons|tuck|widthPx|smooth_under|zones\.json|plate\.json|uv_trim\.png|uv\.png|id\.png|shade\.png|geom=maps|idOff|uvOff"` over `demo/` (code and the active docs) finds only the closed plans and their results.
- [ ] All 4 plates: `plate_invariants.py` ALL PASS; `fringe.py` within the limits of steps 4 and 6; the review set at 2× looked at and approved by a person.
- [ ] `rebuild_check.sh` passes on all 4 plates. The skills' quick reference runs as written.

### Step 8: Device and person checks (needs you)

**Do (with a real phone, and a laptop browser):**
1. `?perf=1` on each view: build time, draw time, drag frame rate, float render targets.
2. A person goes through the journey on the phone and looks at the edge crops.
3. **Only if a new image is supplied:** an edited torso or neckline image whose neckline depth agrees with the other view (`DedhD.md` §11.1). It becomes that plate's new `source.png`; re-run `make_plate.py`, and the halfway step 6 check (±3 mm).

**Accept:**
- [ ] Build ≤ 50 ms (laptop), ≤ 250 ms (mid-range phone); journey step ≤ 1 s after the first visit; drag ≥ 30 fps. If a phone fails: the fallbacks of `numeric` step 7 (build the next view in idle time) are applied and written.
- [ ] Float render targets on every device tested: no shade fallback ships. Otherwise `make_plate.py` writes a `shade.webp` for each plate (the one exception to §1 item 7), and the devices are written.
- [ ] The neck-depth check of the two front views: passes (new image), or stays open with its reason.

### Step 9: Close

**Accept:**
- [ ] `StepA-results.md` summary table; `render.md` §11 entry; `DedhD.md` §11.7 A marked done, with links.
- [ ] The final behaviour of §1 checked item by item in the results, with the evidence (a number or a crop) for each.

## 5. What is removed

| Artifact | Where | Primitive method it belongs to | Replaced by | Step |
|---|---|---|---|---|
| `zones.json`, `plate.json` | every plate folder | Hand-edited and tool-patched intermediate files | `plate.dat` version 2, built from the source; `platedat.py --dump` | 1 |
| `annotate.png`, `check.png` (committed) | every plate folder | Review images stored with the data | `make_plate.py --review` → `demo/review/<plate>/` | 1 |
| `make_dat.py`, `dat_check.mjs`, `BSP1`, `?dat=0` | `tools/`, `plate.js`, `testing.html` | Two formats for the same numbers | `platedat.py`, `BSP2` | 1 |
| `make_base.py` | `tools/` | A torso-only base step | The base crop in `annotate_torso.py` | 2 |
| `extract_zones.py`, `fit_zones.py` | `tools/` | Traced annotation, affine fit, mirrored side | `annotate_torso.py` | 2 |
| `coons()` | `silhouette/pipeline/make_plate.py`, `plate.js` | Coons patch | The fabric frame | 7 (switch `?frame=coons` until then) |
| Zone `grid` (top, left, right, bottom) | `plate.dat` | Coons patch | `frame` (axis, anchor, half, θ, sag) | 4 (unused), 7 (removed) |
| `tuck` and `prepare()` (`profile`, `exempt`, `tip`, `reach` ...) | `plate.dat`, `plate.js`, `make_plate.py` | Grid edges stopping at the seam | `underPx` at seams | 4 |
| `widthPx` | sleeve data, `plate.js`, `make_plate.py` | Width from grid edge lengths | `half` profile + θ | 4 |
| `smooth_under`, rule 9 (bulge 5 %, grid top and the neck dip), the grid columns of the zone recipes | `annotate_sleeve.py`, `annotate.md` §2 and §7.2, the annotate-plate skill | Grid edges as grain lines | Typed edges + frame | 7 |
| `snap_outline.py` (shoulders, trim-order, edge-trim, hem) and the `snapped` marker | `tools/`, plate data | One-off patches on traced outlines | `snap_edges.py` in the build, trims from edges | 1 (trims), 3 (snap), 7 (file) |
| `id.png`, `uv.png`, `uv_trim.png` (4 plates, ≈ 1.3 MB) | plate folders | PNG maps | Maps built on the page; in memory offline | 7 |
| `shade.png` (4 plates, ≈ 1 MB) | plate folders | PNG maps | The GPU shade; a `shade.webp` only if step 8 needs it | 7, 8 |
| `grow`, `idOff`, `uvOff`, the `idImage` path, 12-bit packing | `maps.js`, the main shader | Imitating the PNG painter | Exact passes, 16-bit packing | 5 |
| `?geom`, `?meshviews`, `?decode=all`, `?neck=baked`, `?gpushade`, `?cell`, `?mapoff`, `?torso=v1`, `?frame=coons`, `?softedge` | `testing.html` | Fallbacks to the old methods | — | 7 |
| `plate_checks.py` (bulge, block ratio, the map-size rule) | `tools/`, the make-plate skill rule 3 | PNG maps, grid edges | Frame rules in `plate_invariants.py` | 7 |
| `map_diff.py`, `trim_match.py`, `mesh_check.mjs`; `rebuild_check.sh` on PNG bytes | `tools/` | Comparison with the PNG maps | Parity on the frame; the rebuild check on `base.jpg` + `plate.dat` (step 1) | 1 (rebuild), 7 |
| `shoot.sh`, `crops.py`, `metrics.py` (the `upscale` harness) | `tools/` | Screenshots of the first page | `cdp_shot.mjs`, `edge_crops.py` | 7 (after a `grep` shows no other use) |
| `after-polish-1/`, `after-polish-3/`, `after-step1/`, `after-step3/`, `baseline/`, `baseline-polish/` | `demo/` | Review runs of closed plans | Git history (430c3fd); one line in each results file | 7 |

**Kept:** in each plate folder, `source.png`, `base.jpg`, `plate.dat`. In `tools/`: the annotate scripts, `make_plate.py`, `platedat.py`, `snap_edges.py`, `plate_invariants.py`, `align_check.py`, `gridcrop.py`, `sample.py`, `zoom.py`, `reveal_metrics.py`, `cdp_shot.mjs`, `canvas_diff.py`, `shoot_set.py`, `shoot_views.sh`. The closed plans and their results stay as history, each with one header line: "Closed. The silhouette method is replaced by `StepA.md`."

**Not plate files, so not in this plan:** `assets/looks/*.json` (a look's options and ranges) and the swatch sidecars `assets/swatches/lace-*.json`. They belong to the catalogue and to the swatch and lace plan.

**Left for the swatch and lace plan, on purpose:** `prep_swatches.py` and the first swatches (`swatchprep/sources/fabric-sage-640.png`, `swatchprep/sources/lace-pearl-640.png`, the `-src.png` fabrics); `?linear=0` and `?lacefit=0` (old light maths, mirrored lace).

**Docs and skills rewritten in step 7:** `docs/plate.md` (output table: three files; pipeline; tool limits; the view table's settings row; the failure cases on S-curves, `widthPx` and `tuck`), `docs/annotate.md` (§1 outputs, §2 rules 5–10, §7 data, §8 the review image), `docs/render.md` §6.3–6.5 and a §11 entry, `tools/README.md`, `.claude/skills/make-plate/SKILL.md` (the description's files, rules 3–4, quick reference) and `.claude/skills/annotate-plate/SKILL.md` (outputs, rule 3, templates).

## 6. Risks and fallbacks

| Risk | Sign | Fallback |
|---|---|---|
| The cylinder frame looks too regular where the cloth drapes (the hem's W) | The person check at the hem | The optional spline correction (step 4.6), pinned to the hem line |
| Snapping follows a fold or a shadow instead of the edge | Weak spans > 5 %, or a crop shows the edge on a fold | Keep the measured points on that span (listed); tighten the colour model |
| AI images have soft or doubled edges in places | Edge accuracy fails on a span | Mark the span weak; review at 2× |
| A sleeve's axis in the turned view is not straight | Warp tilt > 3° on the sleeve | A curved axis (polyline), not a straight line |
| The soft edge shows the background's texture (wall) as a halo | The halo check | `?softedge=0` stays the default for that edge type |
| The default neckline moves when the corners snap | Step 3 | Re-measure, update the look's default, and record it |
| A binary `plate.dat` is not readable in a pull request on GitHub (textconv works only locally) | A review on GitHub | The PR description carries the `--dump` diff of each changed plate |
| Phones without float render targets | Step 8 overlay | `shade.webp`, the one written exception |

## 7. Out of scope

The swatch frame across views (placement, print continuity across seams, swatch classes, real scale), new interactions, new silhouettes, merging to `main`. Those are options B–E of `DedhD.md` §11.7, after StepA. (Lace corners and joins were out of scope here; the extension, §8, takes the slit / hem corner in.)

## 8. Extension (2026-11-22): the lace laid on the garment, and the last silhouette items

**Why.** The review of steps 0–7 (2026-11-22, the user's marked screenshots of the 4 views) found the silhouette nearly done and the lace the weak part. Every marked lace defect comes from how the lace is laid out, not from the lace images (the inventory is good enough for the demo):

| What the user marked | Cause (measured) |
|---|---|
| Vertical streaks through the hem view's lace; a fan of streaks at the slit / hem corner (1126, 1302); the torso hem cut on a diagonal at the right corner | A trim is a centre line cut into 1 px segments, each drawn as its own quad with its own normal. At every bend the quads open a wedge on the outer side and overlap on the inner side: hem view `hem` 106 joints with a wedge over 0.5 px (worst 66 px at a 28° bend), torso `hem` 147 (a 62° bend at the slit corner), cuffs 15–16 (8 px). The wedges show the fabric through the lace (the streaks); the corner folds the strip into a fan. The torso trim mismatch of step 5 (0.37 px) is the same overlap |
| Square-cut lace ends at both torso cuffs, at the inner end of the sleeve-view cuff and at the far end of the sleeve-view neck | Each trim is an open strip with two ends. The neck, the cuffs and the hem are loops: the lace goes on round the arm or the body, out of sight. It should be cut by the silhouette, and its motifs should crowd toward it as the cloth turns away (the fabric frame already does this for the fabric) |
| Specks under the cuffs and the hem; the lace almost black over the stand | The overhang (the part of an edging lace past the edge) takes the shade of whatever is behind it (the dark stand). The lace texture's transparent texels are grey (pearl: RGB 128), so its mipmaps grey the lace when it is small |
| A speckled lace everywhere | One lace image is scaled to every trim's width: the pearl lace (30 mm) shrunk to 12 mm on the neck and 8 mm on the slits. In the torso view (0.88 mm/px) a 25 mm cuff is 28 px tall: the 446 px band is minified 16× |

**Decision (the user, 2026-11-22): the lace decides.** A lace keeps its real width (`widthMm` of its sidecar: fine 15, leaf 25, brocade 28.2, pearl 30, geometric 40, paisley 53.4) and its real repeat on every trim. The plate's trim widths (12 / 25 / 30 / 8 mm) go.

**The model: lace is a strip of cloth sewn along a garment edge.**
1. **A trim is an edge run, not a centre line.** `line` = the snapped garment edge between the trim's anchors, smoothed over 4 mm. The lace's decorative edge lies on it; its body goes inward.
2. **The trim field.** For each pixel near the run: `t` = the distance in mm from the edge (+ inward, on the garment), and `s` = the cloth length in cm along the edge to the foot point. `s` is measured with the zone's fabric frame (the length of the edge in (u, v)), so the motifs crowd toward a silhouette as the fabric does. The field is the exact nearest-point field of the run. It is drawn as one quad per segment and a fan at each vertex, with depth = distance, so the nearest segment wins: no wedge, no overlap, no fan of folded quads.
3. **Band.** The field is written from 8 mm outside the edge to 56 mm inside it (the widest lace, 53.4 mm, and the deepest overhang, 0.123 × 53.4 mm). The page lays the lace in it; the band does not depend on the lace chosen.
4. **Ends.**
   - The loops have no ends. A run's end at a silhouette or a corner is "open": the field goes on past it along the end's tangent, and the garment's outline cuts it.
   - A real end is "cut": a square end. Only the slit top has one.
   - The overhang exists only along the run itself, never past its ends (none hanging beside a side silhouette).
5. **Where the lace can be.**
   - The lace's body: only on its own zone.
   - The overhang: outside the garment, or over a zone behind its own, never over an object in front (an occluder).
   - Between the trims of one zone, the nearest edge wins. Where a slit lace meets the hem lace this gives a **mitre** along the corner's bisector.
   - The slits are a second field, because they can be turned off on their own. The page mitres them against the hem by comparing the two distances.
   - Across zones, the front zone's trims are drawn last.
6. **Phase.** The motif sits centred at the frame's u = 0: the centre front for the neck and the hem; the sleeve's axis for a cuff; a back piece's axis. Each lace keeps its own repeat, with no fitting to the visible length. The slits keep whole repeats from the hem corner up to the slit top (the fit of `polish` step 4, ±5 %), with a whole motif at the corner.
7. **Across.**
   - An edging lace (the sidecar's `edging`) on an edging trim (hem, cuffs): its decorative edge hangs `edgeDepth` × its width past the garment edge.
   - Other laces and trims: the lace lies from the edge inward.
8. **Light.**
   - The overhang takes the shade of the garment 3 px inside the edge, at its foot point, not of the stand or wall behind it.
   - The lace keeps its contact shadow, on the fabric and on the background.
   - The lace texture is uploaded premultiplied, so its mipmaps average only the lace: a small lace softens instead of greying and speckling.
9. **The live neckline.** In the neck area the lace comes from the live edge: `t` = the shader's signed distance to the live edge (`dL`), and `s` = the arc length along it from the centre front. The neck area is made deep and wide enough to hold the widest lace at the deepest setting, so the baked field never shows there.

### Step L1: The trim field in the plate (Python reference)

**Do:**
1. Trim data in the annotate scripts: `{edge, from, to, type, anchor, cut}`. `anchor`: `cf` (the default: the frame's u = 0) or `from` / `to` (a whole motif at that end: the hem end of a slit). `cut`: the ends that are real ends (`from` on the slits: the slit top). `widthMm` and `offsetMm` are removed.
2. `derive_trims` → `line`: the edge, resampled, smoothed over 4 mm, between the anchors (projected on the edge). `plate.dat` stores `line` in place of `centre`; the decisions store each trim's `lengthCm` (the cloth length of the line) and `side` (the inward normal).
3. `make_plate.py` `rasterise`: the trim field, exact (per pixel: the nearest segment or vertex of the line, its foot point, `s` and `t`), with the rules of §8.
   - In memory: `uvt` = the main field (`s` + 64 cm; `t` + 64 mm) and `uvts` = the slit field; id G = the main trim.
   - The neck area grows to the widest lace (`NECK_BAND_MM` 30 → 60; sideways reach + 56 mm).
4. `plate_invariants.py`, the trim rules become:
   - the line lies on its edge (mean ≤ 0.3 px, std ≤ 0.5 px);
   - it is smooth (as before);
   - it ends at its anchors (≤ 1 px);
   - the field is complete: no pixel of the zone within the band and the outline lacks a value;
   - the field is continuous: `s` jumps by at most 2 px of cloth between 4-neighbours, except at a mitre.

**Accept:**
- [ ] `rebuild_check.sh` deterministic; `platedat.py --check` passes.
- [ ] The new trim rules PASS on all 4 plates, and the trim smoothness of step 7 (torso hem 0.82 px) is gone with the centre line.
- [ ] `check.png` shows the bands, the mitres and the overhangs; looked at for the 4 views.

### Step L2: The trim field on the page

**Do:**
1. `plate.js`: `trimField(P, Z)` builds the geometry of each field: the quads and fans of each line, with `s` from `frameUV` at the vertices. The same numbers as the build (a parity check).
2. `maps.js`: one depth-tested pass per zone for the main field, then the slits' field, into `uvt` and `uvts` (16-bit, as `uv`); id G by a second pass with `EQUAL` depth. The fragment shader computes `s` and `t` exactly (a fan's distance from its vertex, not interpolated).
3. `maps_check.py` compares both fields with the build: coverage (only a 1 px band may differ), `s` within 0.01 cm, `t` within 0.05 mm.

**Accept:**
- [ ] `maps_check.py` PASS on all 4 views (coverage, uv, both fields).
- [ ] Build time written for each view; the page loads with no console error on all queries (`cdp_shot.mjs` log).

### Step L3: The lace laid by the page

**Do:**
1. The main shader reads `s`, `t`:
   - lace across = from `t`, the lace's own width and `edgeDepth`;
   - along = `s` / the lace's tile length, phase 0.5 period at u = 0;
   - the slits' fit from the corner;
   - the slit / hem mitre by the nearer edge;
   - no lace outside its width.
2. The live neck from `dL` and the arc length of the live edge. The `uNC` centre line and `uNeckTw` go.
3. The overhang shade from the foot point; the premultiplied lace upload; the glow only on the lace itself.
4. Removed: `trimParams`, `trimTriangles`, `uTrimWcm`, `uTrimVMax`, `uTrimFlip`, `FLIP`, `VIEW_FLIP`, the trims' `widthMm` / `vMax` / `outerV`, the whole-repeat fit of the neck and hem.

**Accept:**
- [ ] Every marked area of the 2026-11-22 review, before / after, in one crop sheet:
  - torso: cuffs (both ends), hem (left, middle over the stand, right corner);
  - sleeve view: cuff (both ends), neck (both ends);
  - hem view: the hem lace, the slit / hem corner.
- [ ] No streak: in each band, fabric shows through only where the lace has a hole. Measured: the lace alpha along `t` = const has no column of 0 between two lace columns over 1 px wide that the lace image does not have.
- [ ] The lace's height on the garment = its `widthMm` ± 2 % (the field's `t` at the lace's edges).
- [ ] The overhang over the stand is within 15 % of the lace's luminance just inside the edge.
- [ ] `fringe.py` and `edge_crops.py` as in step 7 (no new rim).

### Step L4: The last silhouette items

**Do:**
0. (Found in step L3: the "lace almost black over the stand".) Torso, the hem over the stand: the first reading ran straight across at y 2200 (source px), but the garment's hem rises over the stand to y 2161. So the front covered 20–37 px of the stand's top, and the fabric and lace there took the stand's dark shade. Read again column by column (x 760–1060).
1. Torso, the right sleeve's inner edge (the long band beside the sleeve): the photo's dark line along the sleeve lies about 8 px inside the body zone, and the body's pattern runs through it. Read the edge again on `source.png`: is the line the sleeve's turned edge (the seam moves onto it) or its shadow on the body (it stays, and reads as a shadow)?
2. Torso, the right hem corner at the slit: the strip of the photo's white garment beside the slit edge. Read the edge again; close it.
3. Neck view, the two gaps between the arms and the body. They were read as the wall seen through the gap, and their jagged, unshaded edges read as tears. **Decided by the user (2026-11-22): they are the kurta's own white fabric in shadow, not the wall.** They close as garment: the front runs under the sleeve up to the sleeve's inner edge (`sleeve-in-l` / `sleeve-in-r` become seams shared by the front and the sleeve).

**Accept:**
- [ ] Before / after crops of each; `plate_invariants.py` closure and gaps as in step 7 or better; a person approves.

### Step L5: Results

**Accept:**
- [ ] `StepA-results.md`: one section for the extension, with the numbers above and the crop sheets (into `docs/plan/img/`).
- [ ] `docs/render.md` (the lace), `docs/plate.md` (trims), `docs/annotate.md` (trim data), `tools/README.md` and the two skills follow the new trim data.

Then steps 8 and 9 as written (step 9 also checks §1 item 5 against the extension).
