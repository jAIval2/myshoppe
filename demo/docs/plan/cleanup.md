# Cleanup before merging `stepA` into `halfway`: the delete list and two pipeline folders

Status: **for review**. Nothing is deleted or moved yet. StepA is committed (`da48bfc`). Scope: `demo/` and the two skills; the backend and the rest of the repository are not touched.

## 1. What "in use" means

A file is kept when one of these reaches it:
- **The page:** `testing.html` and what it loads.
- **The silhouette pipeline:** source image → measured annotation → plate (`base.jpg` + `plate.dat`), with its checks.
- **The swatch and lace prep:** the tools you keep, with the images they are run on.

Each file was traced by what the page loads (its `src`, `href` and `fetch` paths) and by the imports of every tool. Nothing in this list is used by a kept file, except in comments.

## 2. Delete list

| File | Size | Why it goes | What still refers to it |
|---|---|---|---|
| `tools/polish_metrics.py` | 16 KB | Metrics of the closed polish plan (fold contrast, lace fit and joins on the old trims) | Comments in `make_plate.py` and `cdp_shot.mjs`; `shoot_set.py` (also deleted) |
| `tools/reveal_metrics.py` | 3 KB | The closed halfway plan's step 3 measure | `halfway.md` (closed) |
| `tools/canvas_diff.py` | 2 KB | Compared runs against the PNG maps and numeric (both gone) | — |
| `tools/shoot_set.py`, `tools/shoot_views.sh` | 5 KB | Screenshot sets of the polish plan; `cdp_shot.mjs` does this now | — |
| `docs/plan/upscale.md`, `upscale-results.md` | 17 KB | Closed plan ("Closed. The silhouette method is replaced by StepA.md") | `render.md` §11 log, `DedhD.md` |
| `docs/plan/polish.md`, `polish-results.md` | 58 KB | Closed plan | the same |
| `docs/plan/halfway.md`, `halfway-results.md` | 33 KB | Closed plan (its behaviour lives on in the page; `render.md` §11 records it) | the same |
| `docs/plan/numeric.md`, `numeric-results.md` | 61 KB | Closed plan | the same |
| `docs/plan/img/` (all but `stepA*`) | 12 MB | The figures of the closed plans | the closed plans |

They all stay in git history (`da48bfc`). `render.md` §11 keeps its one-paragraph summary of each plan, with a link to the commit instead of the file.

**Test switches of closed plans in `testing.html`** (their old code paths go with them):
- `?shade=0`, `?shadow=`, `?linear=0` (the old sRGB maths, `uLinear`), `?sheen=0|test` (`uSheenOld`), `?antitile=0`, `?displace=0`;
- `?lacefit=0`, `?edging=0`, `?relief=0`;
- `?revealfill=0` (plain fills), `?bias=`, `?aniso=0`, `?snap=0`, `?test`.

**Kept switches:** `?view`, `?step`, `?fabric`, `?lace`, `?trims`, `?checker`, `?stage`, `?neckDepth` / `?neckWidth`, `?perf`, `?syncbuild`. The review harness and step 8 use them.

## 3. Kept, and where it goes

### The page: stays where it is
`testing.html`, `plate.js`, `maps.js`, `assets/plates/<view>/{base.jpg, plate.dat}`, `assets/swatches/*`, `assets/looks/*`. The page's paths do not change.

### `demo/silhouette/`: annotate and build the silhouette (one folder, one entry point)

```
demo/silhouette/
  README.md              the contract: inputs, outputs, commands, the checks and their limits
  plate.py               the entry point (below)
  views/                 the measured sources: torso.py, neck.py, sleeve.py, hem.py (now silhouette/views/<view>.py)
  sources/               the source images: <view>.png (now assets/plates/<view>/source.png; they do not ship)
  pipeline/              make_plate.py, platedat.py, plateframe.py, snap_edges.py, trimfield.py
  checks/                plate_invariants.py, maps_check.py, frame_check.mjs, fringe.py, edge_crops.py, plate_edges.py,
                         rebuild_check.sh, cdp_shot.mjs
  measure/               gridcrop.py, sample.py, zoom.py, align_check.py (reading points on a source)
```

**Contract:**
- **In:** `sources/<view>.png` + `views/<view>.py`.
- **Out:** `assets/plates/<view>/base.jpg` + `plate.dat`, deterministic.
- Python 3 + Pillow only. Node only for `frame_check.mjs` and `cdp_shot.mjs`, which read the page's `plate.js` / `maps.js`.

**Commands:**

| Command | What it does | Today |
|---|---|---|
| `python3 silhouette/plate.py measure <view>` | The annotation's own checks | `silhouette/views/<view>.py` |
| `build <view> [--review]` | `base.jpg` + `plate.dat`; review images into `demo/review/` | `make_plate.py` |
| `check <view>` | Invariants + frame parity | `plate_invariants.py`, `frame_check.mjs` |
| `page-check <view>` | The page's maps and edges against the plate (needs the page served) | `maps_check.py`, `fringe.py`, `edge_crops.py` |
| `rebuild-check` | Every plate rebuilt byte-identical | `rebuild_check.sh` |

### `demo/swatchprep/`: swatch and lace prep (a separate folder)

```
demo/swatchprep/
  README.md              inputs, outputs, commands, the sidecar format (lace-<name>.json)
  prep.py                the entry point: fabric | lace | lace-repeat | lace-material
  prep_fabric.py, prep_lace.py, prep_swatches.py
  sources/               fabric-sage-640.png, lace-pearl-640.png (the source photos of the sage fabric and the pearl lace: kept),
                         fabric-mocha-src.png, fabric-mustard-src.png (now in assets/; they do not ship)
```

- **Out:** `assets/swatches/` (the page's paths stay).
- `prep_swatches.py` is the first version of the fabric and lace prep. It stays as the record of how sage and pearl were made, unless you want it gone.

### Docs and skills, moved or updated with it
- `tools/README.md` becomes the two READMEs.
- `docs/plate.md`, `docs/annotate.md`, `docs/render.md` §6 and `docs/breather.md` get the new paths.
- `.claude/skills/make-plate` and `annotate-plate` get the new commands.
- Kept docs: `DedhD.md`, `render.md`, `plate.md`, `annotate.md`, `breather.md`, `plan/StepA.md`, `plan/StepA-results.md`, `plan/cleanup.md`.

## 4. Order of work, and what proves it

1. One commit: the moves (`git mv`, so history follows the files), the import paths, the entry points and READMEs, the docs and skills.
2. One commit: the deletions and the test switches.
3. After each: `plate.py rebuild-check` (byte-identical), `plate.py check` on the 4 views, `plate.py page-check` on the 4 views, and the page's queries with no console error.
4. Before the merge, settle the uncommitted work in the other checkouts:
   - the `halfway` worktree has 7 changes: `DedhD.md`, `testing.html`, and copies of the brocade and paisley laces that `stepA` already has;
   - the main checkout (branch `polish`) has the same kind.
5. Merge: `halfway` is an ancestor of `stepA` (stepA is 16 commits ahead, halfway 0), so `halfway` fast-forwards to `stepA`.
