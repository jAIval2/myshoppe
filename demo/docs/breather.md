# Breather: what is where, and why

Date: 2026-11-21. Status: orientation for an agent (or a person) that picks up a task such as `plan/StepA.md`. **Read this first, then the plan you work on.**
Keep it current: when a plan closes, a file moves, or a rule changes, update the section concerned (§12).

## 1. Start here

- **Product:** the Bespoke Studio garment visualiser of the MyShoppe boutique (Indian women's wear). A customer picks cloth, lace and shape options, and sees the garment on a dress form in **4 fixed views** (torso, neckline, sleeve, hem). **No 3D, no pan, no zoom.** Photo realism is the product.
- **Method:** each view is a **plate**: a photo of the garment + numbers that say where each part is (zones, trims, fabric coordinates). A WebGL shader paints the chosen fabric and lace onto the photo and keeps the photo's light and folds.
- **All images are AI-generated** (base photos, swatches, laces). The swatches' physical scale is assumed, not measured.
- **Code of the visualiser:** `demo/` only. The rest of the repository is the storefront app (§3).
- **Current branch of work:** `numeric` (worktree `../myshoppe-numeric`). **Next task:** `demo/docs/plan/StepA.md` (the silhouette closed to the photo's edge; replaces the Coons patch; one `plate.dat` per view).
- **Agreed order** (`DedhD.md` §11): StepA → perfect the swatches and laces on the 4 views → merge to `main` → more silhouettes.

**Read in this order for StepA:** this file → `DedhD.md` §11 → `plan/StepA.md` → `plate.md` and `annotate.md` (the current pipeline that StepA changes) → `plan/numeric-results.md` steps 9–11 (the defects StepA fixes).

## 2. Branches, worktrees, ports

| Branch | Worktree | Port (convention) | State |
|---|---|---|---|
| `main` | — (not checked out) | — | = `polish` step 8 (ba978fe). Merged last after the swatch and lace plan. |
| `polish` | `/Users/kayan/Developer/myshoppe` | 8000 | Closed. Has an uncommitted `demo/docs/DedhD.md` (an old copy of §10) and `demo/testing.html` (+4 lines), and an untracked `demo.zip` (a snapshot of `demo/`). |
| `halfway` | `/Users/kayan/Developer/myshoppe-halfway` | 8100 | Closed. |
| `numeric` | `/Users/kayan/Developer/myshoppe-numeric` | 8200 | Current. 20 commits ahead of `main`; `main` is its ancestor (fast-forward). Last: 430c3fd. |
| `stepA` | `../myshoppe-stepA` (to create) | 8300 | StepA step 0 creates it from `numeric`. |

- Serve a worktree: `python3 -m http.server <port> --bind 127.0.0.1 --directory demo`, then open `http://localhost:<port>/testing.html`.
- Two review runs on the same port kill each other's server: always pass a free port to the tools.
- Outside the repository: the Salon page whose option counts `DedhD.md` uses (`C_GROUPS`, `C_FIELDS_BY_SILHOUETTE`) is `/Users/kayan/Downloads/demo 22.26.03/index.html`.

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
| `testing.html` | ≈ 1,800 | The visualiser: one canvas, one fragment shader, the journey UI. |
| `plate.js` | ≈ 250 | The plate maths of `tools/make_plate.py` in JavaScript: `resample`, `coons`, `tuck`, `prepare`, `zoneParams`, `zoneVertices`, `trimParams`, `trimStrip`, `trimTriangles`, `neck_edge`, `offset_poly`, `parseDat`. A classic script (`window.Plate`), also `require`d in Node by the tests. |
| `maps.js` | ≈ 530 | Builds a view's maps on the GPU from the curves: `id`, `uv`, `uv_trim` (stencil + meshes) and the shade (from `base.jpg`: luminance ÷ median, a guided filter per zone, the neck-dip fill). Holds the PNG-imitation calibrations (`grow`, `idOff`, `uvOff`) that StepA removes. |

**Inside `testing.html`** (search for the `// ----` markers):
- Registries: `VIEWS` (view → plate folder), `FABRICS` (src, `repeatCm`, sheen, anti-tiling), `LACES` (band, sidecar json, material map), `TRIMS` (trim name → id 1–8), `FLIP`, `GROUP` (button groups: neck, cuffs, hem, slits).
- Shader samplers: `uPhoto, uId, uUV, uUVT, uShade, uFabric, uLace, uLaceMat`. Sections: live neckline (in the neck area the garment is below the live edge; reveal fills), hex anti-tiling, form detail, lace shadow, relief / metal / pearl, fold displacement, sheen, linear light.
- Loading: `fetchView` keeps the downloaded blobs of all views, `decodeView` decodes only the shown one; `?geom=mesh` (default) builds the maps with `maps.js` from `plate.dat`.
- Neckline (halfway): `neckSetup`, `neckCurves`, the three pivots on rails, snap stops, `applyNeck`, the design record `state.neck` in the URL (`?neckDepth=&neckWidth=`).
- Journey (halfway step 7): steps Cloth → Neckline → Sleeves → Hem → Review, cross-fade, highlight glow, before / after (hold button or Space), review strip, share image (1080 × 1500 PNG), phone layout ≤ 760 px.
- Test hook: `window.__studio` (for example `readMaps()`, used by `tools/map_diff.py`).

**Test switches** (URL query): `?view=torso|neck|sleeve|hem`, `?fabric=off|sage|mocha|mustard`, `?lace=pearl|geometric|leaf|fine|paisley|brocade`, `?trims=neck,cuffs,hem,slits|none`, `?checker=1`, `?step=`, `?test`.
Before / after of closed plans: `?shade=0`, `?shadow=`, `?linear=0`, `?lacefit=0`, `?edging=0`, `?relief=0`, `?displace=0`, `?sheen=0|test`, `?antitile=0`, `?bias=`, `?aniso=0`, `?stage=`, `?decode=all`, `?neck=baked`, `?revealfill=0`, `?snap=0`, `?geom=maps`, `?meshviews=`, `?gpushade=0`, `?dat=0`, `?cell=`, `?mapoff=`, `?syncbuild=1`. StepA removes the ones tied to the old methods (`plan/StepA.md` §5).

## 5. `demo/assets/`

### 5.1 Plates (`assets/plates/<view>-straight/`), one look: the straight kurta

Files now (StepA reduces them to `source.png`, `base.jpg`, `plate.dat`):

| File | Made by | Ships | What |
|---|---|---|---|
| `source.png` | received | no | The AI image as received; measured. **The torso has none**: its source is `assets/torso-base.png`. |
| `base.jpg` | `annotate_<view>.py` (torso: `make_base.py`) | yes | 1200 × 1600 photo, 3:4 |
| `zones.json` | `annotate_<view>.py` (torso: legacy, §9), patched by `snap_outline.py` | no | Zones (order, Coons `grid` edges, `outline`), trims (centre lines, width), landmarks, stitches, occluders, scale, settings |
| `plate.json` | `make_plate.py` | no | Decisions from the image: trim sides, shade median, neck block, zone sizes, ids |
| `plate.dat` | `make_dat.py` | yes | `BSP1`: the curves (int16 deltas, 0.1 px) + a JSON header of the numbers |
| `id.png`, `uv.png`, `uv_trim.png`, `shade.png` | `make_plate.py` | no (since numeric step 7) | Reference maps (§7); `?geom=maps` still uses them |
| `annotate.png`, `check.png` | annotate script, `make_plate.py` | no | Review images for a person |

| View | Plate | mm/px | Zones | Trims (mm) | Scale from | Settings |
|---|---|---|---|---|---|---|
| Torso | `torso-straight` | 0.8978 | front, sleeve-l, sleeve-r | neck 12, cuff-l/r 25, slit-l/r 8, hem 30 | shoulder width 370 mm (**assumption**) | `tuck` (with `profile`, `exempt`), `snapped` |
| Neckline | `neck-straight` | 0.3046 | front, sleeve-l, sleeve-r | neck 12 | neck-l → neck-r 158 mm | neck block, stitches |
| Sleeve | `sleeve-straight` | 0.3382 | front, sleeve-l | neck 12, cuff-l 25 | shoulder → cuff-out 470 mm | `thetaDeg` 40 / 70, `widthPx` 278.8, occluder (mannequin arm) |
| Hem | `hem-straight` | 0.2221 | back-l, back, front | slit-l/r 8, hem 30, hem-bl 30, hem-br 30 | slit-top → hem-slit 240 mm | `thetaDeg` 45 / 60 / 65, `uvRangeCm` 32, `invariants` |

### 5.2 Swatches, looks, legacy

| Path | What |
|---|---|
| `assets/swatches/fabric-{sage,mocha,mustard}-1024.jpg` | De-lit seamless fabric tiles. `repeatCm` in `FABRICS`: 30, 30, 20 (assumptions). |
| `assets/swatches/lace-<name>-2048.webp` + `lace-<name>.json` + `lace-<name>-mat.webp` | 6 laces: pearl, geometric, leaf, fine, paisley, brocade (brocade has no material map). Band with alpha, decorative edge at the bottom. Sidecar: `periodPx`, `periods`, `motifCentrePx`, `cutFromPx`, `blendPx`, `edge`, `widthMm` (assumption), `edgeDepth`, `bottomOpen`, `edging`, `flipped`, `material`. Material map: R height, G metal, B pearl. |
| `assets/looks/straight-kurta.json` | The look's design parameters: `neck.depthMm` (default 40.9, 20–100, stops), `neck.widthMm` (158, 132–194), rules |
| `assets/torso-base.png` | The torso's source image (StepA step 2 moves it into the plate) |
| `assets/fabric-{mocha,mustard}-src.png` | Fabric sources for `prep_fabric.py` |
| `assets/fabric-sage-640.png`, `assets/lace-pearl-640.png` | Legacy first swatches (`prep_swatches.py`); left for the swatch plan |

### 5.3 Old review runs

`demo/after-polish-1/`, `after-polish-3/`, `after-step1/`, `after-step3/`, `baseline/`, `baseline-polish/`: screenshots of the `upscale` and `polish` plans, cited by their results. StepA step 7 removes them (git history keeps them).

## 6. `demo/tools/`

Python 3 with **Pillow only**; Node for the `.mjs` files. Run from `demo/`. Full usage: `tools/README.md`.

| Tool | Job | Status (after StepA) |
|---|---|---|
| `annotate_neck.py`, `annotate_sleeve.py`, `annotate_hem.py` | One per view: base crop, measured points, `zones.json`, `annotate.png`, automatic checks; the templates for new views | Kept; write `plate.dat` v2 |
| `make_base.py` | Torso base (sparkle patch, 3:4 cut) | Folded into `annotate_torso.py` |
| `extract_zones.py`, `fit_zones.py` | "Throwaway": the torso from a drawn annotation + one affine per zone, left side mirrored | Removed (step 2) |
| `make_plate.py` | The reference maths: rasterises `id`, `uv`, `uv_trim`, `shade`, writes `plate.json`, `check.png`, runs the invariants; `--dump-mesh` for the parity test | Becomes the build: source → `base.jpg` + `plate.dat` |
| `make_dat.py`, `dat_check.mjs` | `plate.dat` (`BSP1`) from the JSON files; round-trip check | Replaced by `platedat.py` (step 1) |
| `plate_checks.py` | Grid bulge, grain tilt, UV rate, block ratio, map size | Replaced by frame rules in `plate_invariants.py` |
| `plate_invariants.py` | Closure, gaps, symmetry, trim offset / smoothness, landmarks | Kept; extended |
| `snap_outline.py` | One-off patches: `shoulders`, `trim-order`, `edge-trim`, `hem` | Replaced by `snap_edges.py` |
| `prep_fabric.py`, `prep_lace.py` | Fabric tile (de-lit, seamless); lace band → tile + sidecar + material map | Kept (swatch plan) |
| `prep_swatches.py` | Legacy first swatches | Swatch plan |
| `gridcrop.py`, `sample.py`, `zoom.py`, `align_check.py` | Measuring: gridded crops, colour at points, 2× crops, "is an annotation on the exact base" | Kept |
| `cdp_shot.mjs` | Headless Chrome via DevTools: exact canvas, console log, real input events, `--eval` | Kept: the main review harness |
| `shoot_set.py`, `shoot_views.sh` | Fixed review query sets; parallel screenshots | Kept |
| `canvas_diff.py` | Two runs canvas by canvas (`--blur`) | Kept |
| `polish_metrics.py`, `reveal_metrics.py` | Fold contrast, fine detail, lace fit and joins; the neck reveal step | Kept |
| `map_diff.py`, `mesh_check.mjs`, `trim_match.py`, `rebuild_check.sh` | Comparisons with the PNG maps; byte-identical PNG rebuild | Removed or rewritten (StepA steps 1, 7) |
| `shoot.sh`, `crops.py`, `metrics.py` | The `upscale` harness | Removed (step 7) |

## 7. Data formats (now)

- **Frame:** 1200 × 1600 plate px, origin top left, x right, y down. Every curve is in this frame. Edge directions: `top` / `bottom` left → right, `left` / `right` top → bottom.
- **`id`** (RGBA8): R = zone id (front 1, sleeve-l 2, sleeve-r 3, back 4, back-l 5), G = trim id (`TRIMS`), B = 1 in the neck area.
- **`uv`**: fabric (u, v) in cm, **12-bit packing**: u = ((R << 4) | (B >> 4)) / 4095 × `uvRangeCm`, v = ((G << 4) | (B & 15)) / 4095 × `uvRangeCm`. Each zone's origin is its own grid corner (no shared frame: `DedhD.md` §11.1).
- **`uv_trim`**: u = cm along the trim's centre line, v = 0–1 across (to `vMax` 1.5 for an edging trim, the overhang past the edge).
- **`shade`**: photo luminance ÷ the median light, linear light, sqrt encoding (`shadeSpace`, `shadeEncoding`, `shadeMedian` in `plate.json`).
- **Coverage:** a zone shows where its **Coons grid ∩ its outline** cover the pixel. The root of the closure defects (`plan/StepA.md` §2).
- **Trim types:** `insertion` (inside the garment, v 0–1) and `edging` (hangs past the edge to `vMax` 1.5). A trim's `side` (±1) says which normal points to the garment edge.
- **`plate.dat` `BSP1`:** "BSP1", u16 version, u16 unit (1/1000 px), u32 header length, JSON header, int16 curve deltas. Format in `tools/make_dat.py`.
- **StepA changes all of this:** `BSP2` with typed edges and fabric frames, 16-bit packing, coverage from the outline only, the plate folder = `source.png` + `base.jpg` + `plate.dat`.

## 8. The docs

| Doc | What it holds | Read when |
|---|---|---|
| `demo/docs/breather.md` | This orientation | First |
| `demo/docs/render.md` | The method: purpose, non-goals, the 4 views, the journey, surface vs shape options, the UV-pass render method, preload and registry, fallback; §11 the **progress log** of every plate and plan; §12 sources | To understand why the method is what it is; to record a plate or a closed plan (§11) |
| `demo/docs/DedhD.md` | Plate counts and combinations (§1–9: ≈ 77–89 plates, the anchored model, decisions for the atelier); §10 numeric plates; **§11 the review of 2026-11-21**: off-the-shelf tools, the 3D route and its cost (₹70k–2.1 L), the 2.5D proposal against the repo, the Amber model read again, the process review, **options A–E** | Before choosing work; for the facts in §11.1 |
| `demo/docs/plate.md` | **Skill "make a plate"**: output files, the pipeline (intake → alignment test → base → annotate → make plate → accept → record), tool limits, view specifications (§5), failure cases | Building or rebuilding a plate |
| `demo/docs/annotate.md` | **Skill "annotate a base image"**: data rules (§2), colour code, measuring with gridded crops (§6), zone recipes and trims (§7), checks and review (§9), common errors | Measuring a photo |
| `demo/tools/README.md` | Every tool's usage, grouped by plan; the test switches | Running a tool |
| `demo/docs/plan/upscale.md` + `-results.md` | Done 2026-11-18: one UV per pixel, swatch tiling, mip bias, device-resolution canvas | History |
| `demo/docs/plan/polish.md` + `-results.md` | Done 2026-11-19: lace shadow, shade without the weave, linear light, real lace repeat and whole repeats, edging past the edge, lace relief / metal / pearl, fold displacement, sheen, hex anti-tiling | Lace or fabric work |
| `demo/docs/plan/halfway.md` + `-results.md` | Done: the live neckline (pivots, reveal fills, the lace follows, the torso follows), the showcase journey. §1 defines **the Amber model** | Interaction or neckline work |
| `demo/docs/plan/numeric.md` + `-results.md` | Steps 0–7, 9–11 done: maps built on the GPU from curves, `plate.dat`, the maps not shipped (first visit 1.67 MB, was 3.64 MB); shoulder closure, hem layout, `plate_invariants.py` | Before StepA (its defects and open items) |
| `demo/docs/plan/StepA.md` | **Next**: final expected behaviour, why Coons goes, steps 0–9, the removal table | The task |
| `demo/docs/plan/img/` | Review images cited by the results (≈ 12 MB) | When a result cites one |
| `.claude/skills/*/SKILL.md` | Short skill entries: the rules never broken and a quick reference; they point to `plate.md` / `annotate.md` | When the skill is invoked |

**Results files:** every plan `X.md` has `X-results.md`, one section per step, with the measurements, what was revised and why, and the open items. A FAIL is always written with its number.

## 9. Work so far, and what is open

| Date | Plan | Outcome |
|---|---|---|
| 2026-11-18 | First plates (`render.md` §11) | Torso (traced, legacy tools), then neck, sleeve, hem with measuring scripts |
| 2026-11-18 | `upscale` | Image quality of the overlay |
| 2026-11-19 | `polish` | Fabric and lace realism (8 steps) |
| 2026-11-19/20 | `halfway` | Live neckline + the journey showcase |
| 2026-11-20 | `numeric` | Curves and a `.dat` in place of map images; shoulders; hem lace; invariants |
| 2026-11-21 | `DedhD.md` §11 | Review, options A–E; StepA chosen first |

**Open items carried into StepA (or after it):**
1. **Closure fails on all 4 plates:** outlines 1–3 px inside the real edge (torso 0.138 %, neck 0.239 %, sleeve 0.097 %, hem one 43 px piece). Neck plate: 249 px of thin gaps. Torso: slit landmarks 10 px outside the front, a body-side strip; the right neck-corner speck. Sleeve: `cuff-l` offset.
2. **The torso plate was never measured** (legacy tools, mirrored left side).
3. **No shared fabric frame:** a motif is not at the same garment point in two views.
4. **Neck depth differs between the torso and neckline photos** (25.2 against 40.9 mm): two AI images that disagree. Fix by editing one image.
5. **Unverified on a device or by a person:** draw time ≤ 5 ms; build time (1.4–3.0 s in software rendering); drag ≥ 30 fps; the 10-second tests; lace relief and anti-tiling at 2×; a person on a phone.
6. **Assumed scales:** torso shoulder 370 mm; fabric `repeatCm`; lace `widthMm`.

## 10. Rules of work

- **One step = one commit**, on the plan's branch, in its own worktree. Each step has a test switch for the old behaviour until the plan removes it.
- **Results are written**, with numbers, including FAILs and revised criteria (and why).
- **Measure on `source.png`**, at full resolution, with gridded crops; never take lines from a regenerated annotation (`plate.md` step 2: every tool-made annotation was a new picture, 8–60 px off).
- **A shared seam is one list.** Gaps and objects in front stay outside every zone.
- **A person approves** the review images before a plate is done; your own look is not the approval.
- **Decide offline, ship numbers:** the page evaluates; it does not search the image.
- **Headless Chrome uses software rendering:** its draw and build times are not real; close views need a virtual-time budget of about 45 s.
- **Writing style of the docs:** short declarative sentences, tables, numbered steps with **Do** / **Accept** checkboxes, units on every number (px, mm, cm, %), file names in backticks.
- **No 3D in the product.** A 3D garment (CLO3D or Blender) is only ever an offline source of plates (`DedhD.md` §11.3).

## 11. How to run

```sh
cd demo
python3 -m http.server 8200 --bind 127.0.0.1 --directory .        # then http://localhost:8200/testing.html?view=torso&fabric=mocha&lace=pearl
python3 tools/make_plate.py assets/plates/neck-straight             # rebuild a plate (runs the invariants)
python3 tools/plate_invariants.py assets/plates/torso-straight      # the plate's own checks
node tools/cdp_shot.mjs <out> 8200 "view=hem&fabric=mocha"        # exact canvas + console log, from the server already on that port
PORT=8793 DPR=2 python3 tools/shoot_set.py <out> 8793 --polish     # screenshot sets: shoot_views.sh starts its OWN server on a free port
python3 tools/canvas_diff.py <run-a> <run-b> --blur 2              # compare two runs
```

`cdp_shot.mjs` does not start a server: serve the worktree first. `shoot_views.sh` (used by `shoot_set.py`) does start one, so give it a port that nothing else uses.

## 12. Glossary

| Term | Meaning |
|---|---|
| **Plate** | One fixed view of one garment variant: photo + numbers |
| **Zone** | A fabric piece in a view (front, sleeve-l, back ...), with a draw `order` |
| **Outline** | A zone's visible edge, closed; cuts the neck dip, slits, gaps, notches |
| **Grid** | The 4 edges (top, left, right, bottom) of a zone's Coons patch: the fabric coordinates now. Removed by StepA. |
| **Coons patch** | The surface between 4 boundary curves; today's fabric map |
| **Fabric frame** | StepA's replacement: an axis, an anchor, a half-width profile, `thetaDeg`, `sag` |
| **Typed edge** | StepA: `free` (snapped to the photo), `seam` (shared), `frame` (image border), `cut` (live neck dip) |
| **Trim** | A lace strip along a centre line: `insertion` or `edging` |
| **`thetaDeg`** | The half-angle of the cylinder a zone is unrolled from (the cross-direction foreshortening) |
| **`tuck`** | A push of the front's grid and outline under the sleeves. Removed by StepA. |
| **`widthPx`** | A fabric-width override for a sleeve cap. Removed by StepA. |
| **Neck area / reveal fill** | Where the live neckline can move; the fabric or the dress-form linen that a change reveals |
| **Design record** | The customer's choices in mm (`state.neck`), one record shown in all views |
| **The Amber model** | The data split borrowed from the Amber molecular-dynamics package: parameters, topology, coordinates, internal coordinates (mm), restraints (`halfway.md` §1, `DedhD.md` §11.5) |
| **Closure** | Photo garment that no zone covers: the white rim |
| **`mmPerPx`** | The plate's scale, from an agreed value (`plate.md` §5) |
| **Lace fit** | Whole repeats on each trim, a defined start, a scale of 1.00–1.03 |
| **Review set** | Fixed 2× crops of the edges (StepA step 0) |

## 13. Keeping this file current

Update it in the commit that changes the fact: a plan opens or closes (§1, §2, §8, §9), a file or tool is added, moved or removed (§4–§7), a rule changes (§10). StepA step 7 rewrites §5.1, §6 and §7 for the three-file plate.
