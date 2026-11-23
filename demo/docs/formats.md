# Data formats: plate, garment record, fabric, design record

Date: 2026-11-23 (StepB step 6; StepC: plate version 4, lace sidecar version 2, a lace per line). Status: the contract between the demo (the test bed) and the portal.
The code is the reference: `silhouette/pipeline/platedat.py` (plate), `silhouette/pipeline/garment.py` (garment record), `swatchprep/fabric_sidecar.py` (fabric). This file says what each field means, its unit, its range and where its value comes from.

**Units.** Plate coordinates are plate px (1200 × 1600, an integer is a pixel's centre). Fabric coordinates (u, v) are **cm of cloth**. Lengths in garment terms are mm when the name ends in `Mm`, cm when it ends in `Cm`.

**Sources.** Every number that is a fact about the garment or a swatch says where it comes from (`src`):

| src | Meaning |
|---|---|
| `agreed` | A value the atelier gave (a measure on the real garment) |
| `measured` | Read in one view's photo |
| `fitted` | The mean of several views, with the spread |
| `assumed` | Not measured; a stated assumption |
| `definition` | True by the definition of a frame (an origin) |

## 1. The plate: `assets/plates/<view>-<variant>/plate.dat` (`BSP4`)

One fixed view of one garment variant. It ships with `base.jpg` (the photo, 1200 × 1600). Nothing in a plate is edited by hand: `silhouette/plate.py build <view>` makes it from `silhouette/sources/<plate>.png`, `silhouette/views/<view>.py` and the garment record.

**Binary layout** (little endian): `"BSP4"`, u16 version (4), u16 unit (1/1000 px; 100 = 0.1 px), u32 header length, the header (UTF-8 JSON), then every polyline as int16 (dx, dy) steps from (0, 0). In the header a polyline is `{"@c": index}`. `platedat.py --dump` prints the whole file as text, one value per line.

### Header fields

| Field | Type | Meaning |
|---|---|---|
| `view`, `variant` | string | `torso` \| `neck` \| `sleeve` \| `hem`; the look (`straight-kurta`) |
| `source`, `scaleNote` | string | The source image and its crop; how `mmPerPx` was set (the agreed distance) |
| `viewBox` | [w, h] px | 1200 × 1600 |
| `mmPerPx` | number | The view's scale. From one agreed distance (`scaleNote`); `fit.scale` reports the scale the landmarks would fit |
| `garment` | {look, version, hash} | The garment record the plate was built against. A plate whose hash is not the record's is stale (`rebuild-check` fails) |
| `trimPack` | {`rangeCm`: 256, `mainSOffCm`: 128, `openSOffCm`: [64, 192], `tOffMm`: 64} | The page's 16-bit packing of the trim fields (StepC): the main field u = s + 128 (s within ±128 cm); the open field (the slits) two slots at s + 64 and s + 192 (±64 cm each); v = (t mm + 64) / 10. The same for every plate |
| `uvPack` | {rangeCm: 256, offsetCm: [128, 32]} | The page's 16-bit packing of (u, v): stored = (u, v) + offset, over the range. The same for every plate. u from −128 to 128, v from −32 to 224 cm |
| `edges` | {name: {type, points, zones?, under?}} | Typed edges: `free` (the photo's own contour, snapped), `seam` (one list shared by two zones), `frame` (the image border), `cut` (the live neck dip) |
| `zones` | {name: {id, order, piece, outline, frame}} | A fabric piece as seen in this view. `id` 1..15 (by `order`, then name); `order` = draw order (higher in front); `piece` = the garment record's piece; `outline` = a closed chain `[[edge, ±1], …]` |
| `zones.<z>.frame` | see below | The zone's fabric frame: (u, v) in cm for any plate point |
| `trims` | {name: {…}} | A lace's place: see below |
| `stitches` | {name: points} | Stitch lines (review only) |
| `landmarks` | {name: [x, y]} | The view's measured points. Every one is named in the garment record (`views.<view>.landmarks`) |
| `occluders` | [chains] | Objects in front of the garment (the mannequin arm) |
| `settings` | {…} | The view's settings: `thetaDeg` per zone, `shadeSmoothMm`, `shadeSmoothEps`, `shadeSpace`, optional `laceBandMm` |
| `decisions` | {…} | Taken from the photo by the build: `shadeMedian`, `shadeSmoothPx`, `shadeEncoding`, `shadeSpace`, `neck` (the live neckline's block), zone sizes, trim lengths |
| `fit` | {zones, scale} | How the frames were fitted to the garment record (below) |
| `invariants` | {openings} | Openings the closure check accepts (the slit) |

### The fabric frame (`zones.<z>.frame`)

| Field | Meaning |
|---|---|
| `axis` | The zone's warp line, a polyline top → bottom (the centre front, a sleeve's or a panel's midline) |
| `L`, `s0` | The axis length (px); the anchor's position along it (px) |
| `half` | {left, right}: the half width (px) on each side as a cubic in t = s / L |
| `thetaDeg` | The half angle of the visible arc of the cylinder the zone is unrolled from |
| `yawDeg` | The body's turn about the axis in this view (0 = not turned) |
| `sag` | {c, s1}: the weft lines curve like the hem (s corrected by c r², fully at s1) |
| `uMm`, `vMm` | The u shift and the v at the anchor, mm: fitted to the garment record where the view does not fix them |
| `axisFrom`, `anchor`, `sagEdge`, `skipTop`, `axisDegree` | The specification the frame was measured from |

**The arithmetic** (the same in `plateframe.py`, `plate.js` `frameUV`, `maps.js` `FRAME_FS`; `frame_check.mjs` keeps them equal to 10⁻⁴ cm):
- (s, r) = the point's position along the axis and its signed distance from it (+ to the image right);
- h = the half width on r's side at s;
- with φ = yawDeg and θ = thetaDeg:
  - not turned: u_px = (h / sin θ) asin(|r| sin θ / h), with r's sign;
  - turned: R = h / |sin(±θ + φ) − sin φ|, u_px = R (asin(sin φ + r / R) − φ);
  - past the silhouette: continued with the slope 1 / cos(±θ + φ);
- u = (u_px · mmPerPx + uMm) / 10;
- v = ((s − c r² w(s) − s0) · mmPerPx + vMm) / 10.

### Trims (`trims.<t>`)

| Field | Meaning |
|---|---|
| `id` | 1..15 (by `order`, then name); the page's arrays are indexed by it |
| `type` | `edging` (the lace's decorative edge may hang past the garment edge) \| `insertion` |
| `group` | The page's button: `neck` \| `cuffs` \| `hem` \| `slits` |
| `field`, `slot` | `main` \| `open` (the slits: a field of their own, toggled apart and mitred against the hem); an open trim's `slot` 0 or 1 (at most 2 per plate) |
| `ends` | {from, to}: `runout` (carries on; the outline cuts it) \| `cut` (stops square) \| `piece` (stops square; the lace ends on its last whole motif) |
| `corners` | [{at: [x, y], deg, side}]: where the line turns more than 35° within 5 mm (data: no corner piece is drawn yet) |
| `live` | true: the page lays this trim on the live (customer-moved) neckline; its edge is the `cut` edge |
| `bandInMm`, `bandOutMm` | The depth the trim's field covers inward and (an edging) outward. Default 56 / 8 mm; a wider lace needs a wider band. The hem and cuff trims have 100 mm: a border fabric follows their edge (StepC) |
| `join` | {kind: `mitre` \| `butt` \| `overlap` \| `open`, with: [trims]}: how it meets other trims. The page draws `mitre` (the trim in front, then the nearer edge) and `butt` (the declaring trim runs through its lace width, the other stops at it) between a main and an open trim; `overlap` is drawn as `butt`; two trims of one field meet in the build's nearest-edge mitre |
| `edge`, `from`, `to` | The garment edge it hangs on, between two landmarks |
| `anchor` | Where the motif sits: `cf` (the frame's u = 0: the centre front) \| `from` \| `to` (an end) |
| `cut` | The ends that are square cuts (`from`, `to`) |
| `line`, `side`, `zone` | Derived by the build: the edge between the anchors; the sign toward the garment; the zone |

### The fit (`fit`)

| Field | Meaning |
|---|---|
| `fit.zones.<z>.free` | Which offsets were fitted (`u`, `v`). u is fixed when the axis starts at a point whose garment u is 0; v is fixed when the anchor is the piece's own v origin |
| `.by`, `.n` | `landmarks` (with the count), or a seam tie to another zone |
| `.residualsMm` | {view landmark = garment name: [du, dv]}: the frame minus the record, mm. Over 3 mm is a FAIL unless the record accepts it |
| `.yaw` | {deg, best, rmsAt0Mm, rmsAtBestMm, notApplied?}: the turn that fits best, and whether it was applied (only when over-determined: at least 4 u landmarks on both sides) |
| `fit.scale` | {agreed, fitted, factor, pairs}: information only; the agreed scale is used |

## 2. The garment record: `assets/looks/<look>.json`, block `garment`

One record for all views of one garment. The portal's master copy of where the cloth is.

| Field | Meaning |
|---|---|
| `version` | An integer; raise it when a value changes meaning |
| `pieces.<p>` | {grain, origin, u, v}: what the piece's frame is. `front` and `back`: u from the centre front / back, v from the neck-point line; sleeves: u from the sleeve's centre line, v from the shoulder point down the arm |
| `landmarks.<n>` | {compare: `uv` \| `v` \| `none`, at: {piece: {u, v, src, views?, spreadMm?, note?}}}: a garment point in piece cm. `none`: not compared (a silhouette point) |
| `lines.<n>` | {piece, v, src}: a weft line (a cuff): only v is a property of the cloth |
| `placement` | `buta.<piece>` = {u, v, src}: where a placed motif sits; `border.<piece>` = {hemV, src}: the hem line a border sits on |
| `views.<view>.zones` | {zone: piece} |
| `views.<view>.landmarks` | {view name: garment name \| {line: name} \| null (not a garment point)} |
| `views.<view>.acceptedResiduals` | {view name: reason}: a residual over 3 mm that the **owner** accepts (the photos disagree). Only the owner adds to it |
| `views.<view>.note` | Free text (the hem view's fold) |

The hash (`garment.py ghash`, sha256 of the sorted block, 16 hex) goes into every plate. `garment.py --dump` lists every value with its source.

## 3. The fabric: `assets/swatches/fabric-<name>-<px>.<ext>` + `fabric-<name>.json`

| Field | Meaning |
|---|---|
| `name` | The customer-facing name |
| `tile`, `tilePx` | The tile file and its size. The tile is de-lit and seamless (`swatchprep/prep.py fabric`) |
| `repeatCm`, `repeatSrc` | The tile's real width, and its source: `assumed` for the AI swatches; `measured` from a flat scan with a ruler (`swatchprep/README.md`) |
| `class` | `allover` \| `oneway` \| `buta` \| `border` \| `irregular` |
| `oneWay` | The print has an up: it runs down the grain (v increasing) on every piece, the sleeves included |
| `motifCentrePx` | buta: the motif's centre in the tile |
| `borderBottomPx`, `borderTopPx` | border: the band's lower edge in the tile (the line that sits on the hem) and its upper edge. Above the band only the ground (rows 0 .. `borderTopPx`) repeats: one band per piece |
| `sheen`, `sheenWidth` | The directional highlight along the warp (0 = matte) |
| `antiTile` | Hex tiling to hide the repeat (offsets only, the grain stays) |
| `meanRgb` | The tile's mean colour (sRGB) |
| `test` | A test print, not offered to the customer |

**Placement** (the page, `placeOf`): tile coordinate = (u, v − place) / repeatCm + anchor.
- `allover`, `irregular`, `oneway`: place = 0, anchor = 0; the print's phase is the garment's, the same in every view.
- `buta`: place = `garment.placement.buta[piece]`, anchor = `motifCentrePx / tilePx`.
- `border`: place = (0, `garment.placement.border[piece].hemV`), anchor = (0, `borderBottomPx / tileH`); above the band (tile v < `borderTopPx / tileH`) the tile v wraps inside the ground. Near a hem or cuff trim the tile v comes from the trim's field instead: anchor − t / 10 / repeatCm, so the band lies on the photographed edge, a curved one too (StepC). It fades to the record's line over the field's last 20 mm.

## 3b. The lace: `assets/swatches/lace-<name>-2048.webp` + `lace-<name>.json` (version 2, StepC)

| Field | Meaning |
|---|---|
| `version`, `name` | 2; the customer-facing name |
| `class` | `insertion` \| `edging` \| `border` \| `gota` \| `zari` \| `pearl` \| `mirror` \| `latkan` |
| `widthMm`, `widthSrc` | The band's real width, and its source: `assumed` for the AI laces, `measured` with a ruler (`swatchprep/README.md`) |
| `periodPx`, `periods`, `periodRatio`, `repeatSrc` | The repeat: measured on the image in px; in cm it is `periodRatio` × `widthMm`, so its source is the width's |
| `motifCentrePx` | The motif's centre in the tile (a motif centred at the centre front: the page's phase) |
| `edge`, `edgeDepth`, `bottomOpen`, `edging` | The decorative edge (the band's bottom); the share of the band that hangs past the garment edge on an edging trim; whether the key is clean enough for that |
| `mirror` | No repeat found: the page mirrors the band along the trim |
| `material`, `materialFile` | The material map (R height, G metal, B pearl) and its numbers |
| `endRule` | How the lace ends at a `piece` end: `boundary` (its last whole motif) |
| `bandPx`, `source`, `cutFromPx`, `blendPx`, `flipped`, `pearls`, `corr`, `periodMm`, `test`, `note`, `edgingNote`, `reason` | How the tile was made and why (`prep_lace.py`): the autocorrelation of the period, notes |

**The fit on a trim** (the page, `laceFit`): the repeat r = `periodRatio` × `widthMm`.
- The neck: whole repeats, both corners on motif boundaries; an odd count (a motif at the centre front) when it fits within 6 %, else the nearest.
- The slits (anchored at the hem corner): whole repeats within ±5 % (±10 % on short trims), else the scale is kept.
- The hem and cuffs: a motif centred at the centre front.
- A count is kept while it fits within ±6 % (hysteresis) and is part of the design record.

## 4. The design record (the page's `state`, in the URL)

| Field | Unit | Meaning |
|---|---|---|
| `fabric` | key | A fabric of §3 (`off` = the photo) |
| `laceBy` | {neck, cuffs, hem, slits}: key | The lace of each line (StepC). URL: `?lace=<key>` (every line), `?lace.neck=<key>` … (one line). Up to 4 different laces at once |
| `laceN` | {"<trim>.<lace>": n} | The count of whole repeats of each fitted trim (StepC). URL: `?laceN=neck.pearl:5` |
| `trims` | groups | Which trim groups carry the lace |
| `neckDepthMm`, `neckWidthMm` | mm | The live neckline (`look.neck`: default, range, stops) |
| `print.offsetCm` (per piece) | cm | **Reserved** (StepB): a customer's own shift of the print's place. Not in the page yet; the place comes from the class and the record |
| fabric per piece | key | **Reserved**: the data allows a fabric per piece (`piece` on every zone); the page has one fabric texture |

## 5. Versioning

- A plate names its format (`BSP4`), its garment record (version and hash) and its packings (`uvPack`, `trimPack`). The page refuses another format.
- Changing the garment record changes its hash: rebuild every plate of that look (`silhouette/plate.py rebuild-check` shows which differ).
- A lace sidecar is version 2 (`lace_sidecar.py check`). A fabric sidecar has no version yet; its fields are only added to.
