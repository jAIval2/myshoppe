# Images to generate

The source images the plates still need: one per look and view. Updated 2026-11-24.

- Every image goes through `plate.md` step 1 (intake) before it is measured.
- An image that has arrived but whose view is not yet measured waits in `silhouette/sources/pending/`. The rebuild loop
  (`plate.py`, `rebuild_check.sh`) builds every `.png` directly in `silhouette/sources/`, so an unmeasured source there would
  break it.
- Once the view is measured, move the image to `silhouette/sources/<view>-<look>.png`.

## The table

Status:
- **have**: a source to standard is in `silhouette/sources/`.
- **pending**: the image is in `silhouette/sources/pending/` and passed intake; its view must be measured.
- **redo**: the image is good; its plate must be rebuilt on the current tools.
- **regenerate**: an image arrived but failed intake.
- **need**: generate it.

Priority:
1. The look's torso. With only a torso, the page shows the torso for every view.
2. The neckline: the view in which the customer drags the neckline.
3. Sleeve, hem, and the look's own view.

| # | Look | View | Source file | Status | Priority | Scale on the plate |
|---|---|---|---|---|---|---|
| 1 | straight-kurta | torso | `torso-straight.png` | have | — | neck-l → neck-r 158 mm |
| 2 | straight-kurta | neck | `neck-straight.png` | have | — | neck-l → neck-r 158 mm |
| 3 | straight-kurta | sleeve | `sleeve-straight.png` | have | — | shoulder → cuff-out 470 mm |
| 4 | straight-kurta | hem | `hem-straight.png` | have | — | slit-top → hem-slit 240 mm |
| 5 | lehenga | torso | `torso-lehenga.png` | have (plate built, not yet approved) | — | neck-l → neck-r 158 mm (assumed) |
| 6 | lehenga | neck | `neck-lehenga.png` | **need** | 2 | neck-l → neck-r 158 mm (assumed) |
| 7 | lehenga | sleeve | `sleeve-lehenga.png` | **need** | 3 | shoulder → cuff-out (open: the straight's 470 mm?) |
| 8 | lehenga | hem | `hem-lehenga.png` | **need** | 3 | open: no slit; the atelier to give a length |
| 9 | lehenga | **waist** (its own view) | `waist-lehenga.png` | **need**; the page has no slot yet | 3 | open: the waistband's height, from the atelier |
| 10 | anarkali | torso | `torso-anarkali.png` | have (2026-11-24; plate `torso-anarkali` built, not yet approved; its puff-sleeve edit is plate `torso-anarkali-puff`) | — | neck-l → neck-r 158 mm (assumed) |
| 11 | anarkali | neck | `pending/neck-anarkali.png` | pending (2026-11-24) | 2 | neck-l → neck-r 158 mm (assumed) |
| 12 | anarkali | sleeve | `pending/sleeve-anarkali.png` | pending (2026-11-24) | 3 | shoulder → cuff-out (open) |
| 13 | anarkali | hem | `pending/hem-anarkali.png` | pending (2026-11-24); framed wider than §5, see below | 3 | open: no slit shows in this image |
| 14 | angrakha | torso | `pending/torso-angrakha.png` | **regenerate**: failed intake (2026-11-24), see below | 1 | neck-l → neck-r 158 mm (assumed) |
| 15 | angrakha | neck | `neck-angrakha.png` | **need** (after row 14) | 2 | neck-l → neck-r 158 mm (assumed) |
| 16 | angrakha | sleeve | `sleeve-angrakha.png` | **need** (after row 14) | 3 | shoulder → cuff-out (open) |
| 17 | angrakha | hem | `hem-angrakha.png` | **need** (after row 14) | 3 | open |
| 18 | sharara | torso | `pending/torso-sharara.png` | pending (2026-11-24) | 1 | neck-l → neck-r 158 mm (assumed) |
| 19 | sharara | neck | `neck-sharara.png` | **need** | 2 | neck-l → neck-r 158 mm (assumed) |
| 20 | sharara | sleeve | `sleeve-sharara.png` | **need** | 3 | shoulder → cuff-out (open) |
| 21 | sharara | hem | `hem-sharara.png` | **need**: the kurta's hem and its side slits | 3 | open: the kurta's slit length, from the atelier |
| 22 | sharara | **legs** (its own view) | `legs-sharara.png` | **need**; the page has no slot yet | 3 | open: a tier's height, from the atelier |

**Still to generate: 11 base views, and 27 option images (below).** The prompts, and what to attach to each: `image-prompts.md`.
1. Row 14 (the angrakha torso, again).
2. Rows 6, 15 and 19 (the necklines).
3. Rows 7, 8, 16, 17, 20 and 21 (sleeves and hems).
4. Rows 9 and 22 (the looks' own views).

**View modules.** They exist only for rows 5, 14, 18 (`silhouette/views/torso_<look>.py`) and 11 (`neck_anarkali.py`). Rows
14, 18 and 11 were written against the removed 765 × 1024 images: they are templates and must be re-measured on the new image.

### Notes on the images of 2026-11-24

All five are 1792 × 2400, with the sparkle mark on the floor or the wall.

| Row | Image | Intake |
|---|---|---|
| 11 | anarkali, neck | Highlights PASS (max 239). Same scene. Framed as the prompt asks (finial to below the empire seam), wider than the straight's neck view: the neckline spans about 250 plate px (≈ 0.6 mm/px, against the straight's 0.305) |
| 12 | anarkali, sleeve | Highlights PASS (max 243). Form turned, the sleeve at the left seen from outside, the mannequin arm below the cuff: as §5 |
| 13 | anarkali, hem | Highlights PASS (max 239). From the front, not turned 10–15°; from under the empire seam to the floor, not ≈ 35 cm above the hem. No side slit shows, so the anarkali has no slit to frame. Accepting the wider framing is open |
| 14 | angrakha, torso | **FAIL.** Clipped highlights: ≈ 3,000 garment px > 250, on the ties and the wrap's edge (limit: max ≤ 250). **Not the same scene:** the knob and the stand are darker and differently shaped, and the backdrop curves, with a light gradient. Regenerate in the shared scene, with the ties' highlights held down. Its garment (V-neck wrap, ties at the image right, gathered skirt) is right |
| 18 | sharara, torso | Highlights PASS (max 244). Same scene (the window light on the wall and the floor, as on the lehenga) |

## The options (iterations)

The bespoke brief offers necklines Round, V-neck, Boat neck and Mandarin collar, and sleeves Sleeveless, Short,
Three-quarter and Full length (`web/src/features/bespoke/data.ts`, `designFields`). The base images are round and full. So each
look needs the other three of each, framed like its base view of the same kind, so that the plates line up:

| Look | Neck options (`neck-<look>-<option>.png`) | Sleeve options (`sleeve-<look>-<option>.png`) |
|---|---|---|
| straight-kurta | vneck, boat, mandarin | sleeveless, short, threequarter |
| anarkali | vneck, boat, mandarin | sleeveless, short, threequarter |
| lehenga | vneck, boat, mandarin | sleeveless, short, threequarter |
| sharara | vneck, boat, mandarin | sleeveless, short, threequarter |
| angrakha | none: its neckline is the wrap | sleeveless, short, threequarter |

27 images, all **need**. Open: a neckline or sleeve option changes the torso view too; these prompts cover only the close views.

## The looks' own views

The four views are the straight kurta's. Two looks have their main feature where none of the four views can show it.

- **Lehenga: `waist`.** From the front; from just below the bust to ≈ 25 cm below the waistband. It shows the crop top's hem, the
  band of bare form, the waistband and the start of the flare. This is where a lehenga is designed: the top's length and the
  waistband. In the torso view they are a few pixels high.
- **Sharara: `legs`.** From the front, turned 10–15°; from just above the kurta's hem to the floor. It shows the tier seams, the
  gathers and the flared hems. In the torso view, the gathered hems failed the trim checks (33 field seams on the old image).
  This frees the sharara's `hem` view (row 21) for the kurta's hem and its side slits, as on the straight kurta.

Both need:
- page work: `testing.html` knows four views (`VIEWS`, line 414);
- a column in `plate.md` §5 (framing, zones, frames, trims, scale);
- a view module.

Generate them last.

## The garment of each look

The same garment in all views of a look: plain white matte cotton, no embroidery, lace or print, full-length sleeves.

| Look | Garment |
|---|---|
| lehenga | A high round neck. A fitted crop top ending above the waist (a band of the bare form shows), and a high-waisted, long flared skirt (waistband, soft folds) |
| anarkali | A high round neck. One dress: a fitted bodice with princess seams and an empire seam under the bust, then a long pleated, flared skirt |
| angrakha | A V-neck wrap dress: the over panel crosses the front to ties at the image right, the under panel shows beside it, an empire waist, and a gathered skirt to mid-calf |
| sharara | A high round neck. A straight kurta to mid-thigh with side slits, over a sharara: two wide legs that meet at the centre, each gathered into a lower tier, to the floor |

## The framing of each view

As the prompts give it (`image-prompts.md`); the neck view runs lower than the straight kurta's (`plate.md` §5).

| View | Framing |
|---|---|
| torso | The whole form, from the front, knob to stand |
| neck | Straight on; from just above the finial to ≈ 5 cm below the empire seam (or the underbust line); both shoulders and the tops of both sleeves |
| sleeve | Turned ≈ 30° to the right; the left sleeve from its outer side; from just above the shoulder to ≈ 5 cm below the cuff (the options: below where a full cuff would be) |
| hem | Turned ≈ 10° to the right; ≈ 35 cm above to ≈ 8 cm below the hem, the stand below (a slit at the right, slightly open, where the look has one) |
| waist (lehenga) | From the front; just below the bust to ≈ 25 cm below the waistband (proposed) |
| legs (sharara) | From the front, turned 10–15°; just above the kurta's hem to the floor (proposed) |

## The rules for every image

From `plate.md` step 1 and from the images rejected on 2026-11-23 (`render.md` §11).

- **Size:** 1792 × 2400 (3:4). Never smaller than 1200 × 1600 after the 3:4 crop. The 765 × 1024 images failed: the base was
  upscaled 1.57 ×.
- **Scene:** the same in every image: the natural-linen dress form, the dark wood knob and stand, the warm beige wall, the pale floor,
  soft light from the upper left.
- **Highlights:** the brightest cloth ≤ 250 (not clipped). Ties, piping and edges clip first.
- **The edges must show against the wall.** On the shaded right side, the lehenga's cloth took the wall's own colour, so its edge
  had to be measured by hand. The old anarkali neckline view had the same problem. Ask for a visible edge or a thin shadow line
  all around the garment.
- **The sparkle mark** must be on the wall or the floor, not on the garment. It is patched in `base()`.
- **Make every view of a look from its torso image**, given as the reference. Two images made separately do not agree: the
  straight kurta's neck depth is 32.6 mm in the torso view and 39.7 mm in the neckline view.

## When an image arrives

1. Check it against the rules above (`plate.md` step 1); reject it if it fails one.
2. Save it as `silhouette/sources/pending/<view>-<look>.png` and set its row here to **pending**.
3. Measure the view (`annotate.md`), then move the image to `silhouette/sources/` and make the plate (`plate.md`).
4. Set the row's status to **have**.
