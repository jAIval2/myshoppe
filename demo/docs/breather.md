# Breather: what is where, and why

Date: 2026-11-21, updated 2026-11-23 (StepB step 0). Status: orientation for an agent (or a person) that picks up a task such as `plan/StepA.md`. **Read this first, then the plan you work on.**
Keep it current: when a plan closes, a file moves, or a rule changes, update the section concerned (§13).

## 1. Start here

- **Product:** the Bespoke Studio garment visualiser of the MyShoppe boutique (Indian women's wear). A customer picks cloth, lace and shape options, and sees the garment on a dress form in **4 fixed views** (torso, neckline, sleeve, hem). **No 3D, no pan, no zoom.** Photo realism is the product.
- **Method:** each view is a **plate**: a photo of the garment + numbers that say where each part is (zones, trims, fabric coordinates). A WebGL shader paints the chosen fabric and lace onto the photo and keeps the photo's light and folds.
- **All images are AI-generated** (base photos, swatches, laces). The swatches' physical scale is assumed, not measured.
- **Code of the visualiser:** `demo/` only. The rest of the repository is the storefront app (§3).
- **Current branch:** `main`, with StepB and StepC merged (2026-11-23; not pushed: `origin/main` is `fbd2446`). StepA's step 8 passed (the owner, 2026-11-23). StepB and StepC are closed (`plan/StepB.md`, `plan/StepC.md`, results beside them). **Next:** the owner's choice: the person and device checks, the image route (`DedhD.md` §11.3), then more silhouettes.
- **To make a plate from an image:** `make -C demo help` (the Makefile, after StepC).
- **The data contract for the portal:** `docs/formats.md` (the plate, the garment record, the fabric sidecar, the design record).
- **Agreed order** (`DedhD.md` §11): StepA (done) → StepB (fabric) → StepC (laces) → more silhouettes. The demo is the **test bed for the portal**: what the portal takes from it is the data (`plate.dat`, the garment record, the swatch sidecars), so those must be exact and self-describing.

**Read in this order:** this file → `DedhD.md` §11 → `plan/StepB.md` (the plan in work) → `plan/StepA-results.md` (step 9: what is done and open) → `plate.md` and `annotate.md` (the pipeline) → `silhouette/README.md`, `swatchprep/README.md`.

## 2. Branch and server

| Branch | Checkout | Port | State |
|---|---|---|---|
| `main` | the repository root | 8300 (start it when needed) | StepA, the cleanup, StepB. `stepB` was merged into it and deleted; `polish`, `halfway`, `numeric` and `stepA` were its ancestors and are deleted (2026-11-22) |

- Serve: `python3 -m http.server 8300 --bind 127.0.0.1 --directory demo`, then open `http://localhost:8300/testing.html`.
- Two review runs on the same port kill each other's server: always pass a free port to the tools.
- Outside the repository: the Salon page whose option counts `DedhD.md` uses (`C_GROUPS`, `C_FIELDS_BY_SILHOUETTE`) was `/Users/kayan/Downloads/demo 22.26.03/index.html` on the first machine; it is not in the repository.
- The tools need Python 3 with Pillow, Node ≥ 22 (`cdp_shot.mjs` uses the built-in `WebSocket`) and a Chrome: `cdp_shot.mjs` reads its path from `CHROME` (default: the macOS app). On Linux, a Chrome for Testing works; it may need `--no-sandbox` (a two-line wrapper script as `CHROME`).

## 3. The repository

| Path | What | For the visualiser |
|---|---|---|
| `demo/` | **The visualiser**: page, plates, swatches, tools, docs | Everything |
| `.claude/skills/make-plate`, `.claude/skills/annotate-plate` | Claude Code skills; each points to `demo/docs/plate.md` or `annotate.md` | Yes (rewritten by StepA step 7) |
| `backend/`, `web/`, `scripts/`, `compose*.yaml`, `Dockerfile.*`, `nginx.conf`, `Makefile` | The storefront app: Next.js + FastAPI + PostgreSQL | No |
| `README.md`, `IMPLEMENTATION_STATUS.md`, `SPRINT_PLAN.md`, `STYLING_GUIDE.md` | The storefront's docs, plan and visual contract | No |
| `MyShoppe-Bespoke-Studio.html` | A standalone "Your design story" page (900 KB) | Background only |
| `demo.html` | An unrelated page ("Kaanch Brewer Plan") | No |
| `generated/` | One generated look SVG | No |

## 4. `demo/`: the page

| File | Lines | Job |
|---|---|---|
| `testing.html` | ≈ 1,850 | The visualiser: one canvas, one fragment shader, the journey UI. |
| `plate.js` | ≈ 330 | The plate maths of the build in JavaScript: `parseDat` (plate.dat version 3), `outlineOf`, `underStrips`, `frameProject` / `frameUV` (the fabric frame), `trimElements` / `trimTriangles` (the trim field, StepA extension), `offset_poly`. A classic script (`window.Plate`), also `require`d in Node by `silhouette/checks/frame_check.mjs`. |
| `maps.js` | ≈ 670 | Builds a view's maps on the GPU from `plate.dat`: `id` (R zone, G trim, B neck area, A the soft-edge coverage), `uv` (each zone's frame evaluated per pixel in `FRAME_FS`), the trim field (`TRIM_FS`: `uvt` + id G, `uvts` for the slits; one element per segment of each trim's edge, the nearest edge wins), 16-bit packing; soft free edges (`SOFT_FS`); the shade (from `base.jpg`: luminance ÷ median, a guided filter per zone, the neck-dip fill). |

**Inside `testing.html`** (search for the `// ----` markers):
- Registries: `VIEWS` (view → plate folder), `FABRICS` (tile + sidecar per fabric; the sidecar holds the facts, StepB step 5), `LACES` (band, sidecar json, material map). `TRIMS` and `GROUP` are filled per view from the plate (`setTables`, StepB step 2); `placeOf` / `setPlacement` place the print by its class (StepB step 5).
- Shader samplers: `uPhoto, uId, uUV, uUVT, uShade, uFabric, uLace, uLaceMat`. Sections: live neckline (in the neck area the garment is below the live edge; reveal fills), the soft free edge (StepA step 6), hex anti-tiling, form detail, lace shadow, relief / metal / pearl, fold displacement, sheen, linear light.
- Loading: `fetchView` keeps the downloaded blobs of all views (`base.jpg` + `plate.dat`), `decodeView` decodes only the shown one; `Maps.build` makes the maps. Without float render targets the shade is flat (a console warning; StepA step 8).
- Neckline (halfway): `neckSetup`, `neckCurves`, the three pivots on rails, snap stops, `applyNeck`, the design record `state.neck` in the URL (`?neckDepth=&neckWidth=`).
- Journey (halfway step 7): steps Cloth → Neckline → Sleeves → Hem → Review, cross-fade, highlight glow, before / after (hold button or Space), review strip, share image (1080 × 1500 PNG), phone layout ≤ 760 px.
- Test hook: `window.__studio` (for example `readMapsRaw()`, used by `silhouette/checks/maps_check.py`; `neckCurves()`, `setNeck()`).
- `?perf=1`: an overlay with the build time (with a 1 px readback), the draw time, the frame rate of a drag, and whether float render targets exist.

**Test switches** (URL query): `?view=torso|neck|sleeve|hem`, `?fabric=off|sage|mocha|mustard|reg|buta|border`, `?lace=pearl|geometric|leaf|fine|paisley|brocade|reg` (every line) and `?lace.neck=`, `?lace.cuffs=`, `?lace.hem=`, `?lace.slits=` (one line), `?laceN=neck.pearl:5`, `?joinkind=<trim>:<butt|overlap|mitre>`, `?trims=neck,cuffs,hem,slits|none`, `?checker=1`, `?step=`, `?test`, `?perf=1`, `?syncbuild=1`, `?stage=`.
`?neckDepth=<mm>&neckWidth=<mm>` (the design record). The before / after switches of the closed plans (`?shade=0`, `?linear=0`, `?lacefit=0`, `?sheen=`, `?revealfill=0`, `?bias=`, `?aniso=0`, `?snap=0` and the rest) were removed in the cleanup, with their code paths; StepA step 7 had removed the switches of the old methods.

## 5. `demo/assets/`

### 5.1 Plates (`assets/plates/<view>-straight/`), one look: the straight kurta

**A plate folder holds the two files that ship**; its source image is `silhouette/sources/<plate>.png` (the cleanup, `plan/cleanup.md`):

| File | Made by | Ships | What |
|---|---|---|---|
| `silhouette/sources/<plate>.png` | received | no | The AI image as received; measured (not in the plate folder) |
| `base.jpg` | `make_plate.py` (from `silhouette/views/<view>.py` `base()`) | yes | 1200 × 1600 photo, 3:4 |
| `plate.dat` | `make_plate.py` | yes | `BSP3` (`silhouette/pipeline/platedat.py`; StepB step 2): the garment header, typed edges, zone outlines as chains of edges and their **fabric frames**, trims (from their edges), stitches, landmarks, occluders, settings, and the decisions taken from the image. `platedat.py --dump` prints it; `git diff` shows that text |

Review images (`annotate.png`, `check.png`, crops) are made on demand into `demo/review/<plate>/` (not committed): `make_plate.py <plate> --review`.

| View | Plate | mm/px | Zones | Trims (mm) | Scale from | Settings |
|---|---|---|---|---|---|---|
| Torso | `torso-straight` | 0.8773 | front, sleeve-l, sleeve-r | neck 12, cuff-l/r 25, slit-l/r 8, hem 30 | neck-l → neck-r 158 mm (the neck view's value; shoulders then 341 mm, the old 370 mm assumption disagreed) | measured both sides (StepA step 2) |
| Neckline | `neck-straight` | 0.3046 | front, sleeve-l, sleeve-r | neck 12 | neck-l → neck-r 158 mm | neck block, stitches |
| Sleeve | `sleeve-straight` | 0.3382 | front, sleeve-l | neck 12, cuff-l 25 | shoulder → cuff-out 470 mm | `thetaDeg` 40 / 70, occluder (mannequin arm) |
| Hem | `hem-straight` | 0.2221 | back-l, back, front | slit-l/r 8, hem 30, hem-bl 30, hem-br 30 | slit-top → hem-slit 240 mm | `thetaDeg` 45 / 60 / 65, `invariants` (the slit opening) |

### 5.2 Swatches, looks, legacy

| Path | What |
|---|---|
| `assets/swatches/fabric-{sage,mocha,mustard}-1024.jpg` | De-lit seamless fabric tiles. `repeatCm` in `FABRICS`: 30, 30, 20 (assumptions). |
| `assets/swatches/lace-<name>-2048.webp` + `lace-<name>.json` + `lace-<name>-mat.webp` | 6 laces: pearl, geometric, leaf, fine, paisley, brocade (brocade has no material map). Band with alpha, decorative edge at the bottom. Sidecar: `periodPx`, `periods`, `motifCentrePx`, `cutFromPx`, `blendPx`, `edge`, `widthMm` (assumption), `edgeDepth`, `bottomOpen`, `edging`, `flipped`, `material`. Material map: R height, G metal, B pearl. |
| `assets/looks/straight-kurta.json` | The **garment record** (block `garment`, StepB step 2: pieces, landmarks in piece cm with their sources, each view's zones and landmark names; `silhouette/pipeline/garment.py`) and the look's design parameters: `neck.depthMm` (default 39.7 since StepA step 3, 20–100, stops), `neck.widthMm` (158, 132–194), rules |
| `assets/fabric-{mocha,mustard}-src.png` | Fabric sources for `prep_fabric.py` |
| `swatchprep/sources/fabric-sage-640.png`, `swatchprep/sources/lace-pearl-640.png` | Legacy first swatches (`prep_swatches.py`); left for the swatch plan |

The old review runs of the `upscale` and `polish` plans (`demo/after-*`, `demo/baseline*`) were removed in StepA step 7; git history keeps them (430c3fd).

**Closed plans** (`upscale`, `polish`, `halfway`, `numeric`, with their results and figures) were removed in the cleanup (`plan/cleanup.md`); code comments still cite their steps. Read one with `git show da48bfc:demo/docs/plan/<name>.md`.

## 6. `demo/silhouette/` and `demo/swatchprep/`

Two self-contained folders, each with one entry point and a README that states what goes in and what comes out (the cleanup, `plan/cleanup.md`). Python 3 with **Pillow only**; Node for the `.mjs` checks.

| Folder | Entry point | Inside |
|---|---|---|
| `demo/silhouette/` | `python3 silhouette/plate.py views \| measure \| build \| check \| page-check \| rebuild-check` | `views/` (one measured view each: `base()`, `measure()`), `sources/` (the images as received), `pipeline/` (`make_plate.py`, `platedat.py`, `plateframe.py`, `snap_edges.py`, `trimfield.py`), `checks/` (`plate_invariants.py`, `frame_check.mjs`, `maps_check.py`, `cdp_shot.mjs`, `fringe.py`, `edge_crops.py`, `plate_edges.py`, `rebuild_check.sh`), `measure/` (`gridcrop.py`, `sample.py`, `zoom.py`, `align_check.py`). Usage: `silhouette/README.md` |
| `demo/swatchprep/` | `python3 swatchprep/prep.py fabric \| lace \| lace-repeat \| lace-material \| first-swatches` | `prep_fabric.py`, `prep_lace.py`, `prep_swatches.py`, `sources/` (the source photos of the fabrics and the pearl lace). Usage: `swatchprep/README.md` |

```sh
cd demo
python3 -m http.server 8200 --bind 127.0.0.1 --directory .        # then http://localhost:8200/testing.html?view=torso&fabric=mocha&lace=pearl
python3 silhouette/plate.py build neck --review                   # rebuild a plate from its source (runs the invariants)
python3 silhouette/plate.py rebuild-check                          # every plate = what its source makes
python3 silhouette/plate.py check torso                            # the plate's own checks + the frame parity
python3 silhouette/plate.py page-check hem --port 8200             # the page's maps and edges against the plate (server on that port)
python3 silhouette/pipeline/platedat.py --dump assets/plates/neck-straight   # a plate as text
node silhouette/checks/cdp_shot.mjs <out> 8200 "view=hem&fabric=mocha"      # exact canvas + console log, from the server already on that port
```

`cdp_shot.mjs` does not start a server: serve the worktree first, on a port nothing else uses.

## 7. Checks: what proves what

| Check | Proves | Run |
|---|---|---|
| `silhouette/plate.py rebuild-check` | every plate = what its source makes (byte-identical) | after any change to a view, a tool or the garment record |
| `silhouette/plate.py check <view>` | the plate's invariants (closure, gaps, frame rules, trims) and the frame parity (`frame_check.mjs`) | after a rebuild |
| `silhouette/plate.py page-check <view> --port <p>` | the page's maps = the build's (`maps_check.py`); closure in the render (`fringe.py`); the edge crops | with the page served on `<p>` |
| `silhouette/checks/xview_check.py` | one cloth point = one fabric (u, v) in every view (StepB): each shared landmark's spread in mm | numbers only, no render |
| `silhouette/checks/xview_sheet.py` | the same, as an image: 10 cm crops of each shared landmark in each view, rendered with `?fabric=reg` | for a person |

## 8. Plans

| Plan | State | Results |
|---|---|---|
| `plan/StepC.md` | closed 2026-11-23 | `plan/StepC-results.md` |
| `plan/StepB.md` | closed 2026-11-23 | `plan/StepB-results.md` |
| `plan/StepA.md` | closed 2026-11-22; step 8 passed 2026-11-23 | `plan/StepA-results.md` |
| `plan/cleanup.md` | closed | — |
| `upscale`, `polish`, `halfway`, `numeric` | closed; removed in the cleanup | `git show da48bfc:demo/docs/plan/<name>.md` |

## 9. Open items (carried between plans)

- From StepB (`plan/StepB-results.md`, the close): a centre-front point to measure in the sleeve view (so the fit can apply its turn); the hem view's shaded panel read as the front past a fold (the owner to confirm); the person checks of StepB's sheets.
- From StepC (`plan/StepC-results.md`, the close): corner pieces are data, not drawn (the torso's hem fans its motifs at the bend into the right slit corner); an `overlap` join is drawn as a `butt`; the lace widths are assumed; the person and device checks (4 laces at once).
- The photos disagree on the neck depth (7 mm), the slit length (8 cm) and the sleeve length (7 cm): **accepted by the owner** (2026-11-23), listed in the garment record (`acceptedResiduals`).

- From StepA: closure FAILs (sleeve 0.0596 %, torso 6 px, hem 10 px); the rim on the sleeve and hem views; the halo's 95th percentile on 3 views; 1 px of map coverage on the torso; the neck-depth agreement of the two front views (7 mm).
- The swatches' and laces' physical scales are assumptions (`repeatCm`, `widthMm`).

## 10. Rules

- **Nothing is edited by hand in a plate** (or a sidecar): change the source (a view, a tool, the garment record), then rebuild.
- **One step = one commit**, its numbers in the plan's results file; a FAIL is written with its number.
- **A person approves** what a render shows; an agent's own look is not the approval.
- **Every number has a source** (agreed, measured, fitted, assumed) once it is in the garment record, a plate or a sidecar (StepB).

## 11. Where the numbers come from

- Each view's scale (`mmPerPx`) comes from one agreed distance (`plate.md` §5). The torso borrows the neck view's 158 mm neck width.
- Each zone's fabric frame is measured in its view (StepA step 4). StepB ties the views together through the garment record.
- The swatch tile sizes and the lace widths are assumptions (AI images).

## 12. Glossary

| Term | Meaning |
|---|---|
| **Plate** | One fixed view of one garment variant: photo + numbers |
| **Zone** | A fabric piece in a view (front, sleeve-l, back ...), with a draw `order` |
| **Outline** | A zone's visible edge, closed; cuts the neck dip, slits, gaps, notches |
| **Grid** | The 4 edges (top, left, right, bottom) of a zone's Coons patch, before StepA. Removed by StepA. |
| **Coons patch** | The surface between 4 boundary curves; the fabric map before StepA (replaced by the fabric frame) |
| **Fabric frame** | StepA's replacement: an axis, an anchor, a half-width profile, `thetaDeg`, `sag` |
| **Typed edge** | StepA: `free` (snapped to the photo), `seam` (shared), `frame` (image border), `cut` (live neck dip) |
| **Trim** | A lace sewn along a garment edge at its own width: `insertion` or `edging` (StepA extension) |
| **`thetaDeg`** | The half-angle of the cylinder a zone is unrolled from (the cross-direction foreshortening) |
| **`tuck`** | A push of the front's grid and outline under the sleeves. Removed by StepA. |
| **`widthPx`** | A fabric-width override for a sleeve cap. Removed by StepA. |
| **Neck area / reveal fill** | Where the live neckline can move; the fabric or the dress-form linen that a change reveals |
| **Design record** | The customer's choices in mm (`state.neck`), one record shown in all views |
| **The Amber model** | The data split borrowed from the Amber molecular-dynamics package: parameters, topology, coordinates, internal coordinates (mm), restraints (`halfway.md` (git history, `da48bfc`) §1, `DedhD.md` §11.5) |
| **Closure** | Photo garment that no zone covers: the white rim |
| **`mmPerPx`** | The plate's scale, from an agreed value (`plate.md` §5) |
| **Lace fit** | Whole repeats on each trim, a defined start, a scale of 1.00–1.03 |
| **Review set** | Fixed 2× crops of the edges (StepA step 0) |
| **Garment record** | `assets/looks/<look>.json` block `garment` (StepB): the pieces, the landmarks in piece cm with their sources, each view's zones and landmark names, the placement points, the accepted residuals |
| **Piece** | A pattern piece of the garment (front, back, sleeve-l, sleeve-r); each zone of a view shows one |
| **Fit** | StepB step 3: a zone's free frame offsets (`uMm`, `vMm`) fitted to the garment record; `fit` in `plate.dat` holds the residuals |
| **Yaw** | StepB step 4: the body's turn about a zone's axis in a view (`yawDeg`); applied only when the landmarks over-determine it |
| **Placement** | StepB step 5: where a print sits by its class (all-over, buta on a point, border on the hem line) |
| **Sidecar** | The JSON next to a swatch tile (`fabric-<name>.json`, `lace-<name>.json`): its scale with the source, class and placement data |
| **Open field** | StepC: the slits' own trim field (two slots), toggled apart from the main field and mitred against the hem |
| **Piece end** | StepC: a trim end where the lace stops on its last whole motif (the slit tops) |
| **Lace slot** | StepC: one of 4 texture slots; each line's lace occupies one, so the neck, cuffs, hem and slits can differ |
| **Hysteresis** | StepC: a trim keeps its count of whole repeats while the lace stretches by at most 6 %, so motifs do not jump while dragging |

## 13. Keeping this file current

Update it in the commit that changes the fact: a plan opens or closes (§1, §2, §8, §9), a file or tool is added, moved or removed (§4–§7), a rule changes (§10). StepA step 7 rewrites §5.1, §6 and §7 for the three-file plate.
