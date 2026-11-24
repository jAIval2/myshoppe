# Image prompts

39 prompts. Order: A1 first (the angrakha's other prompts need it), then the rest of A, then B and C.

**StepD (by parts) supersedes B and C for the three primary looks:** section D below. A look is built from layers (a base without
sleeves, plus sleeve and neckline parts), so an option is ONE edit of a look's own photo that lines up with it to the pixel, and
the same option reaches the other looks by porting (`silhouette/parts/build_layers.py`). D is run as one chat per silhouette.

The prompts for every image still needed (`images.md`): the base views first, then the iterations (the neckline and sleeve options of the bespoke brief, `web/src/features/bespoke/data.ts` `designFields`). One chat per image. Attach the two images named in the prompt; save the result as `silhouette/sources/pending/<file>` and check it against `images.md` (the rules) before it is measured.

| Name in the prompt | Attach |
|---|---|
| `base-straight` | `demo/silhouette/sources/torso-straight.png` |
| `base-anarkali` | the anarkali torso, on the branch `anarkali-wip`: `git show anarkali-wip:demo/silhouette/sources/torso-anarkali.png > torso-anarkali.png` |
| `base-lehenga` | `demo/silhouette/sources/torso-lehenga.png` |
| `base-sharara` | `demo/silhouette/sources/pending/torso-sharara.png` |
| `base-angrakha` | the new `torso-angrakha.png` (prompt A1); until then the failed one, for the garment only |
| `reference-neck` | `web/public/media/bespoke/reference-neckline-1280.webp` |
| `reference-sleeves` | `web/public/media/bespoke/reference-sleeves-1280.webp` |
| `reference-hem` | `web/public/media/bespoke/reference-hem-1280.webp` |

Iterations keep the camera of the look's base view of the same kind (the neck options frame like its round neck, the sleeve options like its full sleeve), so that the plates of one look line up. The angrakha has no neckline options: its neckline is the wrap.

## A. Base views still needed

### A1. Angrakha, torso (first: the other angrakha prompts use it as base-angrakha)

Save as `torso-angrakha.png`.

```
Generate an image with framing like base-lehenga, of the garment in base-angrakha, keeping that garment's cut, fabric and colour, and the mannequin, lighting and background of base-lehenga.

The form faces the camera straight on, with no turn.
Top: just above the finial of the mannequin neck.
Bottom: the floor, with the whole stand showing.
Left and right: both sleeves whole, with wall beyond them.
The form is centred.

What must be clear:
The V-neck's piped edges and the wrap's crossing edge down to the ties.
The ties and their loops at the side, each cord separate.
Both shoulder seams, the armhole seams and both sleeves down to the cuffs, with the wall visible in the gaps under the arms.
The empire waist seam and the gathers of the skirt below it.
The hem across the full width of the skirt, and the stand below.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### A. Lehenga, neck (round)

Save as `neck-lehenga.png`.

```
Generate an image with framing like reference-neck, for the same base image (base-lehenga), keeping the same garment, fabric, colour, mannequin, lighting and background.

The form faces the camera straight on, with no turn.
Top: just above the wooden cap of the mannequin neck, with the top of the finial showing, as in the reference.
Bottom: about 5 cm below the crop top's hem, so the band of bare form and the top of the skirt's waistband show.
Left and right: the outer edge of both shoulders and the top of both sleeves.
The neckline sits in the upper third of the image, centred.

What must be clear:
The round neckline edge, its facing and its top-stitch line.
Both shoulder seams, from the neck point to the armhole.
The crop top's side seams and darts, its hem, and the band of bare form between the top and the skirt's waistband.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### A. Kurta and sharara, neck (round)

Save as `neck-sharara.png`.

```
Generate an image with framing like reference-neck, for the same base image (base-sharara), keeping the same garment, fabric, colour, mannequin, lighting and background.

The form faces the camera straight on, with no turn.
Top: just above the wooden cap of the mannequin neck, with the top of the finial showing, as in the reference.
Bottom: about 5 cm below the underbust line (the kurta has no waist seam), the kurta running on below.
Left and right: the outer edge of both shoulders and the top of both sleeves.
The neckline sits in the upper third of the image, centred.

What must be clear:
The round neckline edge, its facing and its top-stitch line.
Both shoulder seams, from the neck point to the armhole.
The princess seams on the kurta's bodice, curving from the armhole towards the waist.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### A. Angrakha, neck (round, V)

Save as `neck-angrakha.png`.

```
Generate an image with framing like reference-neck, for the same base image (base-angrakha), keeping the same garment, fabric, colour, mannequin, lighting and background.

The form faces the camera straight on, with no turn.
Top: just above the wooden cap of the mannequin neck, with the top of the finial showing, as in the reference.
Bottom: about 5 cm below the empire waist seam, so the first gathers of the skirt are just visible.
Left and right: the outer edge of both shoulders and the top of both sleeves.
The neckline sits in the upper third of the image, centred.

What must be clear:
The V-neck's piped edges, from each neck point down to where the wrap crosses.
Both shoulder seams, from the neck point to the armhole.
The wrap's crossing edge and its piping, the ties at the side, and the empire waist seam with the gathers below it.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### A. Lehenga, sleeve (full)

Save as `sleeve-lehenga.png`.

```
Generate an image with framing like reference-sleeves, for the same base image (base-lehenga), keeping the same garment, fabric, colour, mannequin, lighting and background.

The form is turned about 30° to the right, so the left sleeve is seen from its outer side.
Top: just above the shoulder, with the shoulder line and the side of the neck opening showing.
Bottom: about 5 cm below the cuff, so the mannequin arm shows beneath it.
Left and right: the whole sleeve on the left, with a little wall beyond it; on the right, the turned crop top, with its hem and the skirt's waistband below it, which may run off the edge.
The sleeve runs from the upper left towards the lower centre.

What must be clear:
The shoulder seam, from the neck point to the shoulder point.
The armhole seam, from the shoulder point round the sleeve cap to the underarm.
The sleeve's outer and inner edges down to the cuff, with the wall visible in the gap under the arm.
The cuff edge and its top-stitch line, and where the sleeve ends against the mannequin arm.
The crop top's side seams and darts, its hem, and the band of bare form between the top and the skirt's waistband, as far as they show.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### A. Kurta and sharara, sleeve (full)

Save as `sleeve-sharara.png`.

```
Generate an image with framing like reference-sleeves, for the same base image (base-sharara), keeping the same garment, fabric, colour, mannequin, lighting and background.

The form is turned about 30° to the right, so the left sleeve is seen from its outer side.
Top: just above the shoulder, with the shoulder line and the side of the neck opening showing.
Bottom: about 5 cm below the cuff, so the mannequin arm shows beneath it.
Left and right: the whole sleeve on the left, with a little wall beyond it; on the right, the turned body of the kurta, with its princess seam, which may run off the edge.
The sleeve runs from the upper left towards the lower centre.

What must be clear:
The shoulder seam, from the neck point to the shoulder point.
The armhole seam, from the shoulder point round the sleeve cap to the underarm.
The sleeve's outer and inner edges down to the cuff, with the wall visible in the gap under the arm.
The cuff edge and its top-stitch line, and where the sleeve ends against the mannequin arm.
The princess seams on the kurta's bodice, curving from the armhole towards the waist, as far as they show.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### A. Angrakha, sleeve (full)

Save as `sleeve-angrakha.png`.

```
Generate an image with framing like reference-sleeves, for the same base image (base-angrakha), keeping the same garment, fabric, colour, mannequin, lighting and background.

The form is turned about 30° to the right, so the left sleeve is seen from its outer side.
Top: just above the shoulder, with the shoulder line and the side of the neck opening showing.
Bottom: about 5 cm below the cuff, so the mannequin arm shows beneath it.
Left and right: the whole sleeve on the left, with a little wall beyond it; on the right, the turned bodice, with the wrap's edge and the empire waist seam, which may run off the edge.
The sleeve runs from the upper left towards the lower centre.

What must be clear:
The shoulder seam, from the neck point to the shoulder point.
The armhole seam, from the shoulder point round the sleeve cap to the underarm.
The sleeve's outer and inner edges down to the cuff, with the wall visible in the gap under the arm.
The cuff edge and its top-stitch line, and where the sleeve ends against the mannequin arm.
The wrap's crossing edge and its piping, the ties at the side, and the empire waist seam with the gathers below it, as far as they show.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### A. Lehenga, hem

Save as `hem-lehenga.png`.

```
Generate an image with framing like reference-hem, for the same base image (base-lehenga), keeping the same garment, fabric, colour, mannequin, lighting and background.

The form faces the camera, turned about 10° to the right.
Top: about 35 cm above the hem, well below the waistband, so only the flared panels show.
Bottom: about 8 cm below the hem, with the mannequin stand showing underneath.
Left and right: the hem across the full width of the flare, curving out of sight at both sides.
The hem sits in the lower third of the image.

What must be clear:
The hem edge along its whole length, its turn-up and its top-stitch line.
The panel seams running down through the flare to the hem.
The folds of the flare, with their light and shadow.
Where the hem passes behind at the sides, and the stand below.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### A. Angrakha, hem

Save as `hem-angrakha.png`.

```
Generate an image with framing like reference-hem, for the same base image (base-angrakha), keeping the same garment, fabric, colour, mannequin, lighting and background.

The form faces the camera, turned about 10° to the right.
Top: about 35 cm above the hem, well below the empire waist, so only the gathered skirt shows.
Bottom: about 8 cm below the hem, with the mannequin stand showing underneath.
Left and right: the hem across the full width of the skirt, curving out of sight at both sides.
The hem sits in the lower third of the image.

What must be clear:
The hem edge along its whole length, its turn-up and its top-stitch line.
The gathered folds running down to the hem, with their light and shadow.
The ends of the ties, if they reach into the frame.
Where the hem passes behind at the sides, and the stand below.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### A. Kurta and sharara, hem (the kurta's)

Save as `hem-sharara.png`.

```
Generate an image with framing like reference-hem, for the same base image (base-sharara), keeping the same garment, fabric, colour, mannequin, lighting and background.

The form faces the camera, turned about 10° to the right.
Top: about 35 cm above the kurta's hem.
Bottom: about 8 cm below the hem, with the mannequin stand showing underneath.
Left and right: the kurta across its full width, with the side slit on the right slightly open; the top of both sharara legs below the hem.
The hem sits in the lower third of the image.

What must be clear:
The kurta's hem edge along its whole length, its turn-up and its top-stitch line.
The side slit: both its edges, their facings, and the bar tack at its top.
The sharara's legs below the kurta's hem, and where the kurta lies over them.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### A. Lehenga, waist (its own view)

Save as `waist-lehenga.png`.

```
Generate an image with framing like reference-neck, for the same base image (base-lehenga), keeping the same garment, fabric, colour, mannequin, lighting and background.

The form faces the camera straight on, with no turn.
Top: just below the bust.
Bottom: about 25 cm below the skirt's waistband, where the flare begins.
Left and right: the whole width of the body, with the inner edges of both sleeves.
The band of bare form sits in the upper third of the image, centred.

What must be clear:
The crop top's hem edge and its top-stitch line.
The band of bare form between the top and the skirt.
The waistband: its top and bottom edges and its seam to the skirt.
The panel seams and the first folds where the flare begins.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### A. Kurta and sharara, legs (its own view)

Save as `legs-sharara.png`.

```
Generate an image with framing like reference-hem, for the same base image (base-sharara), keeping the same garment, fabric, colour, mannequin, lighting and background.

The form faces the camera, turned about 10° to the right.
Top: just above the kurta's hem.
Bottom: the floor, with the mannequin stand showing between the legs.
Left and right: both legs across their full width, with wall beyond them.
The tier seams sit in the middle third of the image.

What must be clear:
The kurta's hem at the top, lying over the legs.
Where the two legs meet at the centre.
Both tier seams and the gathers below them.
Both flared hems along their whole length, and their top-stitch lines.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

## B. Neckline options

### B. Straight kurta, V-neck

Save as `neck-straight-vneck.png`.

```
Generate an image with framing like reference-neck, for the same base image (base-straight), keeping the same garment, fabric, colour, mannequin, lighting and background, with one change: the neckline is a V-neck, starting at the same neck points as the round neck and dipping to a point about 12 cm below them at the centre front.

The form faces the camera straight on, with no turn.
Top: just above the wooden cap of the mannequin neck, with the top of the finial showing, as in the reference.
Bottom: about 5 cm below the underbust line (the kurta has no waist seam), the kurta running on below.
Left and right: the outer edge of both shoulders and the top of both sleeves.
The neckline sits in the upper third of the image, centred.

What must be clear:
The V-neck's two edges and the point where they meet, its facing and its top-stitch line.
Both shoulder seams, from the neck point to the armhole.
The side seams on the bodice, as far as they show.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### B. Straight kurta, Boat neck

Save as `neck-straight-boat.png`.

```
Generate an image with framing like reference-neck, for the same base image (base-straight), keeping the same garment, fabric, colour, mannequin, lighting and background, with one change: the neckline is a boat neck, wide and shallow, running almost straight across from close to each shoulder point, about 3 cm deep at the centre front.

The form faces the camera straight on, with no turn.
Top: just above the wooden cap of the mannequin neck, with the top of the finial showing, as in the reference.
Bottom: about 5 cm below the underbust line (the kurta has no waist seam), the kurta running on below.
Left and right: the outer edge of both shoulders and the top of both sleeves.
The neckline sits in the upper third of the image, centred.

What must be clear:
The boat neck's edge from shoulder to shoulder, its facing and its top-stitch line, and the bare form above it.
Both shoulder seams, from the neck point to the armhole.
The side seams on the bodice, as far as they show.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### B. Straight kurta, Mandarin collar

Save as `neck-straight-mandarin.png`.

```
Generate an image with framing like reference-neck, for the same base image (base-straight), keeping the same garment, fabric, colour, mannequin, lighting and background, with one change: the neckline has a mandarin collar, a band about 3 cm high standing up around the round neck, its ends meeting at the centre front.

The form faces the camera straight on, with no turn.
Top: just above the wooden cap of the mannequin neck, with the top of the finial showing, as in the reference.
Bottom: about 5 cm below the underbust line (the kurta has no waist seam), the kurta running on below.
Left and right: the outer edge of both shoulders and the top of both sleeves.
The neckline sits in the upper third of the image, centred.

What must be clear:
The collar's top edge, its seam to the neckline, its ends at the centre front, and its top-stitch line.
Both shoulder seams, from the neck point to the armhole.
The side seams on the bodice, as far as they show.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### B. Anarkali, V-neck

Save as `neck-anarkali-vneck.png`.

```
Generate an image with framing like reference-neck, for the same base image (base-anarkali), keeping the same garment, fabric, colour, mannequin, lighting and background, with one change: the neckline is a V-neck, starting at the same neck points as the round neck and dipping to a point about 12 cm below them at the centre front.

The form faces the camera straight on, with no turn.
Top: just above the wooden cap of the mannequin neck, with the top of the finial showing, as in the reference.
Bottom: about 5 cm below the empire waist seam, so the first folds of the flared panels are just visible.
Left and right: the outer edge of both shoulders and the top of both sleeves.
The neckline sits in the upper third of the image, centred.

What must be clear:
The V-neck's two edges and the point where they meet, its facing and its top-stitch line.
Both shoulder seams, from the neck point to the armhole.
The princess seams on the bodice, curving from the armhole down to the empire waist seam, and the empire waist seam running straight across.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### B. Anarkali, Boat neck

Save as `neck-anarkali-boat.png`.

```
Generate an image with framing like reference-neck, for the same base image (base-anarkali), keeping the same garment, fabric, colour, mannequin, lighting and background, with one change: the neckline is a boat neck, wide and shallow, running almost straight across from close to each shoulder point, about 3 cm deep at the centre front.

The form faces the camera straight on, with no turn.
Top: just above the wooden cap of the mannequin neck, with the top of the finial showing, as in the reference.
Bottom: about 5 cm below the empire waist seam, so the first folds of the flared panels are just visible.
Left and right: the outer edge of both shoulders and the top of both sleeves.
The neckline sits in the upper third of the image, centred.

What must be clear:
The boat neck's edge from shoulder to shoulder, its facing and its top-stitch line, and the bare form above it.
Both shoulder seams, from the neck point to the armhole.
The princess seams on the bodice, curving from the armhole down to the empire waist seam, and the empire waist seam running straight across.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### B. Anarkali, Mandarin collar

Save as `neck-anarkali-mandarin.png`.

```
Generate an image with framing like reference-neck, for the same base image (base-anarkali), keeping the same garment, fabric, colour, mannequin, lighting and background, with one change: the neckline has a mandarin collar, a band about 3 cm high standing up around the round neck, its ends meeting at the centre front.

The form faces the camera straight on, with no turn.
Top: just above the wooden cap of the mannequin neck, with the top of the finial showing, as in the reference.
Bottom: about 5 cm below the empire waist seam, so the first folds of the flared panels are just visible.
Left and right: the outer edge of both shoulders and the top of both sleeves.
The neckline sits in the upper third of the image, centred.

What must be clear:
The collar's top edge, its seam to the neckline, its ends at the centre front, and its top-stitch line.
Both shoulder seams, from the neck point to the armhole.
The princess seams on the bodice, curving from the armhole down to the empire waist seam, and the empire waist seam running straight across.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### B. Lehenga, V-neck

Save as `neck-lehenga-vneck.png`.

```
Generate an image with framing like reference-neck, for the same base image (base-lehenga), keeping the same garment, fabric, colour, mannequin, lighting and background, with one change: the neckline is a V-neck, starting at the same neck points as the round neck and dipping to a point about 12 cm below them at the centre front.

The form faces the camera straight on, with no turn.
Top: just above the wooden cap of the mannequin neck, with the top of the finial showing, as in the reference.
Bottom: about 5 cm below the crop top's hem, so the band of bare form and the top of the skirt's waistband show.
Left and right: the outer edge of both shoulders and the top of both sleeves.
The neckline sits in the upper third of the image, centred.

What must be clear:
The V-neck's two edges and the point where they meet, its facing and its top-stitch line.
Both shoulder seams, from the neck point to the armhole.
The crop top's side seams and darts, its hem, and the band of bare form between the top and the skirt's waistband.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### B. Lehenga, Boat neck

Save as `neck-lehenga-boat.png`.

```
Generate an image with framing like reference-neck, for the same base image (base-lehenga), keeping the same garment, fabric, colour, mannequin, lighting and background, with one change: the neckline is a boat neck, wide and shallow, running almost straight across from close to each shoulder point, about 3 cm deep at the centre front.

The form faces the camera straight on, with no turn.
Top: just above the wooden cap of the mannequin neck, with the top of the finial showing, as in the reference.
Bottom: about 5 cm below the crop top's hem, so the band of bare form and the top of the skirt's waistband show.
Left and right: the outer edge of both shoulders and the top of both sleeves.
The neckline sits in the upper third of the image, centred.

What must be clear:
The boat neck's edge from shoulder to shoulder, its facing and its top-stitch line, and the bare form above it.
Both shoulder seams, from the neck point to the armhole.
The crop top's side seams and darts, its hem, and the band of bare form between the top and the skirt's waistband.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### B. Lehenga, Mandarin collar

Save as `neck-lehenga-mandarin.png`.

```
Generate an image with framing like reference-neck, for the same base image (base-lehenga), keeping the same garment, fabric, colour, mannequin, lighting and background, with one change: the neckline has a mandarin collar, a band about 3 cm high standing up around the round neck, its ends meeting at the centre front.

The form faces the camera straight on, with no turn.
Top: just above the wooden cap of the mannequin neck, with the top of the finial showing, as in the reference.
Bottom: about 5 cm below the crop top's hem, so the band of bare form and the top of the skirt's waistband show.
Left and right: the outer edge of both shoulders and the top of both sleeves.
The neckline sits in the upper third of the image, centred.

What must be clear:
The collar's top edge, its seam to the neckline, its ends at the centre front, and its top-stitch line.
Both shoulder seams, from the neck point to the armhole.
The crop top's side seams and darts, its hem, and the band of bare form between the top and the skirt's waistband.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### B. Kurta and sharara, V-neck

Save as `neck-sharara-vneck.png`.

```
Generate an image with framing like reference-neck, for the same base image (base-sharara), keeping the same garment, fabric, colour, mannequin, lighting and background, with one change: the neckline is a V-neck, starting at the same neck points as the round neck and dipping to a point about 12 cm below them at the centre front.

The form faces the camera straight on, with no turn.
Top: just above the wooden cap of the mannequin neck, with the top of the finial showing, as in the reference.
Bottom: about 5 cm below the underbust line (the kurta has no waist seam), the kurta running on below.
Left and right: the outer edge of both shoulders and the top of both sleeves.
The neckline sits in the upper third of the image, centred.

What must be clear:
The V-neck's two edges and the point where they meet, its facing and its top-stitch line.
Both shoulder seams, from the neck point to the armhole.
The princess seams on the kurta's bodice, curving from the armhole towards the waist.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### B. Kurta and sharara, Boat neck

Save as `neck-sharara-boat.png`.

```
Generate an image with framing like reference-neck, for the same base image (base-sharara), keeping the same garment, fabric, colour, mannequin, lighting and background, with one change: the neckline is a boat neck, wide and shallow, running almost straight across from close to each shoulder point, about 3 cm deep at the centre front.

The form faces the camera straight on, with no turn.
Top: just above the wooden cap of the mannequin neck, with the top of the finial showing, as in the reference.
Bottom: about 5 cm below the underbust line (the kurta has no waist seam), the kurta running on below.
Left and right: the outer edge of both shoulders and the top of both sleeves.
The neckline sits in the upper third of the image, centred.

What must be clear:
The boat neck's edge from shoulder to shoulder, its facing and its top-stitch line, and the bare form above it.
Both shoulder seams, from the neck point to the armhole.
The princess seams on the kurta's bodice, curving from the armhole towards the waist.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### B. Kurta and sharara, Mandarin collar

Save as `neck-sharara-mandarin.png`.

```
Generate an image with framing like reference-neck, for the same base image (base-sharara), keeping the same garment, fabric, colour, mannequin, lighting and background, with one change: the neckline has a mandarin collar, a band about 3 cm high standing up around the round neck, its ends meeting at the centre front.

The form faces the camera straight on, with no turn.
Top: just above the wooden cap of the mannequin neck, with the top of the finial showing, as in the reference.
Bottom: about 5 cm below the underbust line (the kurta has no waist seam), the kurta running on below.
Left and right: the outer edge of both shoulders and the top of both sleeves.
The neckline sits in the upper third of the image, centred.

What must be clear:
The collar's top edge, its seam to the neckline, its ends at the centre front, and its top-stitch line.
Both shoulder seams, from the neck point to the armhole.
The princess seams on the kurta's bodice, curving from the armhole towards the waist.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

## C. Sleeve options

### C. Straight kurta, Sleeveless

Save as `sleeve-straight-sleeveless.png`.

```
Generate an image with framing like reference-sleeves, for the same base image (base-straight), keeping the same garment, fabric, colour, mannequin, lighting and background, with one change: the garment is sleeveless, the armhole finished with a narrow facing.

The form is turned about 30° to the right, so the left sleeve is seen from its outer side.
Top: just above the shoulder, with the shoulder line and the side of the neck opening showing.
Bottom: about 5 cm below where a full sleeve's cuff would be, so the bare mannequin arm shows down the frame.
Left and right: the whole sleeve on the left, with a little wall beyond it; on the right, the turned body of the kurta, which may run off the edge.
The armhole sits in the upper left of the image.

What must be clear:
The shoulder seam, from the neck point to the shoulder point.
The armhole edge, its facing and its top-stitch line, from the shoulder point round to the underarm.
The bare mannequin arm below the armhole, with the wall visible in the gap under the arm.
The side seams on the turned bodice, as far as they show, as far as they show.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### C. Straight kurta, Short

Save as `sleeve-straight-short.png`.

```
Generate an image with framing like reference-sleeves, for the same base image (base-straight), keeping the same garment, fabric, colour, mannequin, lighting and background, with one change: the sleeves are short, ending about 15 cm below the shoulder point with a plain hem.

The form is turned about 30° to the right, so the left sleeve is seen from its outer side.
Top: just above the shoulder, with the shoulder line and the side of the neck opening showing.
Bottom: about 5 cm below where a full sleeve's cuff would be, so the bare mannequin arm shows below the short sleeve.
Left and right: the whole sleeve on the left, with a little wall beyond it; on the right, the turned body of the kurta, which may run off the edge.
The sleeve runs from the upper left towards the lower centre.

What must be clear:
The shoulder seam, from the neck point to the shoulder point.
The armhole seam, from the shoulder point round the sleeve cap to the underarm.
The sleeve's outer and inner edges down to its hem, with the wall visible in the gap under the arm.
The sleeve's hem edge and its top-stitch line, and the bare mannequin arm below it.
The side seams on the turned bodice, as far as they show, as far as they show.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### C. Straight kurta, Three-quarter

Save as `sleeve-straight-threequarter.png`.

```
Generate an image with framing like reference-sleeves, for the same base image (base-straight), keeping the same garment, fabric, colour, mannequin, lighting and background, with one change: the sleeves are three-quarter length, ending about 10 cm below the elbow with a plain cuff.

The form is turned about 30° to the right, so the left sleeve is seen from its outer side.
Top: just above the shoulder, with the shoulder line and the side of the neck opening showing.
Bottom: about 5 cm below where a full sleeve's cuff would be, so the bare mannequin forearm shows below the cuff.
Left and right: the whole sleeve on the left, with a little wall beyond it; on the right, the turned body of the kurta, which may run off the edge.
The sleeve runs from the upper left towards the lower centre.

What must be clear:
The shoulder seam, from the neck point to the shoulder point.
The armhole seam, from the shoulder point round the sleeve cap to the underarm.
The sleeve's outer and inner edges down to the cuff, with the wall visible in the gap under the arm.
The cuff edge and its top-stitch line, and the bare mannequin forearm below it.
The side seams on the turned bodice, as far as they show, as far as they show.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### C. Anarkali, Sleeveless

Save as `sleeve-anarkali-sleeveless.png`.

```
Generate an image with framing like reference-sleeves, for the same base image (base-anarkali), keeping the same garment, fabric, colour, mannequin, lighting and background, with one change: the garment is sleeveless, the armhole finished with a narrow facing.

The form is turned about 30° to the right, so the left sleeve is seen from its outer side.
Top: just above the shoulder, with the shoulder line and the side of the neck opening showing.
Bottom: about 5 cm below where a full sleeve's cuff would be, so the bare mannequin arm shows down the frame.
Left and right: the whole sleeve on the left, with a little wall beyond it; on the right, the turned bodice, with its princess seam and empire waist seam, which may run off the edge.
The armhole sits in the upper left of the image.

What must be clear:
The shoulder seam, from the neck point to the shoulder point.
The armhole edge, its facing and its top-stitch line, from the shoulder point round to the underarm.
The bare mannequin arm below the armhole, with the wall visible in the gap under the arm.
The princess seams on the turned bodice, curving from the armhole down to the empire waist seam, and the empire waist seam running straight across, as far as they show.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### C. Anarkali, Short

Save as `sleeve-anarkali-short.png`.

```
Generate an image with framing like reference-sleeves, for the same base image (base-anarkali), keeping the same garment, fabric, colour, mannequin, lighting and background, with one change: the sleeves are short, ending about 15 cm below the shoulder point with a plain hem.

The form is turned about 30° to the right, so the left sleeve is seen from its outer side.
Top: just above the shoulder, with the shoulder line and the side of the neck opening showing.
Bottom: about 5 cm below where a full sleeve's cuff would be, so the bare mannequin arm shows below the short sleeve.
Left and right: the whole sleeve on the left, with a little wall beyond it; on the right, the turned bodice, with its princess seam and empire waist seam, which may run off the edge.
The sleeve runs from the upper left towards the lower centre.

What must be clear:
The shoulder seam, from the neck point to the shoulder point.
The armhole seam, from the shoulder point round the sleeve cap to the underarm.
The sleeve's outer and inner edges down to its hem, with the wall visible in the gap under the arm.
The sleeve's hem edge and its top-stitch line, and the bare mannequin arm below it.
The princess seams on the turned bodice, curving from the armhole down to the empire waist seam, and the empire waist seam running straight across, as far as they show.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### C. Anarkali, Three-quarter

Save as `sleeve-anarkali-threequarter.png`.

```
Generate an image with framing like reference-sleeves, for the same base image (base-anarkali), keeping the same garment, fabric, colour, mannequin, lighting and background, with one change: the sleeves are three-quarter length, ending about 10 cm below the elbow with a plain cuff.

The form is turned about 30° to the right, so the left sleeve is seen from its outer side.
Top: just above the shoulder, with the shoulder line and the side of the neck opening showing.
Bottom: about 5 cm below where a full sleeve's cuff would be, so the bare mannequin forearm shows below the cuff.
Left and right: the whole sleeve on the left, with a little wall beyond it; on the right, the turned bodice, with its princess seam and empire waist seam, which may run off the edge.
The sleeve runs from the upper left towards the lower centre.

What must be clear:
The shoulder seam, from the neck point to the shoulder point.
The armhole seam, from the shoulder point round the sleeve cap to the underarm.
The sleeve's outer and inner edges down to the cuff, with the wall visible in the gap under the arm.
The cuff edge and its top-stitch line, and the bare mannequin forearm below it.
The princess seams on the turned bodice, curving from the armhole down to the empire waist seam, and the empire waist seam running straight across, as far as they show.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### C. Lehenga, Sleeveless

Save as `sleeve-lehenga-sleeveless.png`.

```
Generate an image with framing like reference-sleeves, for the same base image (base-lehenga), keeping the same garment, fabric, colour, mannequin, lighting and background, with one change: the garment is sleeveless, the armhole finished with a narrow facing.

The form is turned about 30° to the right, so the left sleeve is seen from its outer side.
Top: just above the shoulder, with the shoulder line and the side of the neck opening showing.
Bottom: about 5 cm below where a full sleeve's cuff would be, so the bare mannequin arm shows down the frame.
Left and right: the whole sleeve on the left, with a little wall beyond it; on the right, the turned crop top, with its hem and the skirt's waistband below it, which may run off the edge.
The armhole sits in the upper left of the image.

What must be clear:
The shoulder seam, from the neck point to the shoulder point.
The armhole edge, its facing and its top-stitch line, from the shoulder point round to the underarm.
The bare mannequin arm below the armhole, with the wall visible in the gap under the arm.
The crop top's side seams and darts, its hem, and the band of bare form between the top and the skirt's waistband, as far as they show.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### C. Lehenga, Short

Save as `sleeve-lehenga-short.png`.

```
Generate an image with framing like reference-sleeves, for the same base image (base-lehenga), keeping the same garment, fabric, colour, mannequin, lighting and background, with one change: the sleeves are short, ending about 15 cm below the shoulder point with a plain hem.

The form is turned about 30° to the right, so the left sleeve is seen from its outer side.
Top: just above the shoulder, with the shoulder line and the side of the neck opening showing.
Bottom: about 5 cm below where a full sleeve's cuff would be, so the bare mannequin arm shows below the short sleeve.
Left and right: the whole sleeve on the left, with a little wall beyond it; on the right, the turned crop top, with its hem and the skirt's waistband below it, which may run off the edge.
The sleeve runs from the upper left towards the lower centre.

What must be clear:
The shoulder seam, from the neck point to the shoulder point.
The armhole seam, from the shoulder point round the sleeve cap to the underarm.
The sleeve's outer and inner edges down to its hem, with the wall visible in the gap under the arm.
The sleeve's hem edge and its top-stitch line, and the bare mannequin arm below it.
The crop top's side seams and darts, its hem, and the band of bare form between the top and the skirt's waistband, as far as they show.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### C. Lehenga, Three-quarter

Save as `sleeve-lehenga-threequarter.png`.

```
Generate an image with framing like reference-sleeves, for the same base image (base-lehenga), keeping the same garment, fabric, colour, mannequin, lighting and background, with one change: the sleeves are three-quarter length, ending about 10 cm below the elbow with a plain cuff.

The form is turned about 30° to the right, so the left sleeve is seen from its outer side.
Top: just above the shoulder, with the shoulder line and the side of the neck opening showing.
Bottom: about 5 cm below where a full sleeve's cuff would be, so the bare mannequin forearm shows below the cuff.
Left and right: the whole sleeve on the left, with a little wall beyond it; on the right, the turned crop top, with its hem and the skirt's waistband below it, which may run off the edge.
The sleeve runs from the upper left towards the lower centre.

What must be clear:
The shoulder seam, from the neck point to the shoulder point.
The armhole seam, from the shoulder point round the sleeve cap to the underarm.
The sleeve's outer and inner edges down to the cuff, with the wall visible in the gap under the arm.
The cuff edge and its top-stitch line, and the bare mannequin forearm below it.
The crop top's side seams and darts, its hem, and the band of bare form between the top and the skirt's waistband, as far as they show.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### C. Kurta and sharara, Sleeveless

Save as `sleeve-sharara-sleeveless.png`.

```
Generate an image with framing like reference-sleeves, for the same base image (base-sharara), keeping the same garment, fabric, colour, mannequin, lighting and background, with one change: the garment is sleeveless, the armhole finished with a narrow facing.

The form is turned about 30° to the right, so the left sleeve is seen from its outer side.
Top: just above the shoulder, with the shoulder line and the side of the neck opening showing.
Bottom: about 5 cm below where a full sleeve's cuff would be, so the bare mannequin arm shows down the frame.
Left and right: the whole sleeve on the left, with a little wall beyond it; on the right, the turned body of the kurta, with its princess seam, which may run off the edge.
The armhole sits in the upper left of the image.

What must be clear:
The shoulder seam, from the neck point to the shoulder point.
The armhole edge, its facing and its top-stitch line, from the shoulder point round to the underarm.
The bare mannequin arm below the armhole, with the wall visible in the gap under the arm.
The princess seams on the kurta's bodice, curving from the armhole towards the waist, as far as they show.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### C. Kurta and sharara, Short

Save as `sleeve-sharara-short.png`.

```
Generate an image with framing like reference-sleeves, for the same base image (base-sharara), keeping the same garment, fabric, colour, mannequin, lighting and background, with one change: the sleeves are short, ending about 15 cm below the shoulder point with a plain hem.

The form is turned about 30° to the right, so the left sleeve is seen from its outer side.
Top: just above the shoulder, with the shoulder line and the side of the neck opening showing.
Bottom: about 5 cm below where a full sleeve's cuff would be, so the bare mannequin arm shows below the short sleeve.
Left and right: the whole sleeve on the left, with a little wall beyond it; on the right, the turned body of the kurta, with its princess seam, which may run off the edge.
The sleeve runs from the upper left towards the lower centre.

What must be clear:
The shoulder seam, from the neck point to the shoulder point.
The armhole seam, from the shoulder point round the sleeve cap to the underarm.
The sleeve's outer and inner edges down to its hem, with the wall visible in the gap under the arm.
The sleeve's hem edge and its top-stitch line, and the bare mannequin arm below it.
The princess seams on the kurta's bodice, curving from the armhole towards the waist, as far as they show.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### C. Kurta and sharara, Three-quarter

Save as `sleeve-sharara-threequarter.png`.

```
Generate an image with framing like reference-sleeves, for the same base image (base-sharara), keeping the same garment, fabric, colour, mannequin, lighting and background, with one change: the sleeves are three-quarter length, ending about 10 cm below the elbow with a plain cuff.

The form is turned about 30° to the right, so the left sleeve is seen from its outer side.
Top: just above the shoulder, with the shoulder line and the side of the neck opening showing.
Bottom: about 5 cm below where a full sleeve's cuff would be, so the bare mannequin forearm shows below the cuff.
Left and right: the whole sleeve on the left, with a little wall beyond it; on the right, the turned body of the kurta, with its princess seam, which may run off the edge.
The sleeve runs from the upper left towards the lower centre.

What must be clear:
The shoulder seam, from the neck point to the shoulder point.
The armhole seam, from the shoulder point round the sleeve cap to the underarm.
The sleeve's outer and inner edges down to the cuff, with the wall visible in the gap under the arm.
The cuff edge and its top-stitch line, and the bare mannequin forearm below it.
The princess seams on the kurta's bodice, curving from the armhole towards the waist, as far as they show.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### C. Angrakha, Sleeveless

Save as `sleeve-angrakha-sleeveless.png`.

```
Generate an image with framing like reference-sleeves, for the same base image (base-angrakha), keeping the same garment, fabric, colour, mannequin, lighting and background, with one change: the garment is sleeveless, the armhole finished with a narrow facing.

The form is turned about 30° to the right, so the left sleeve is seen from its outer side.
Top: just above the shoulder, with the shoulder line and the side of the neck opening showing.
Bottom: about 5 cm below where a full sleeve's cuff would be, so the bare mannequin arm shows down the frame.
Left and right: the whole sleeve on the left, with a little wall beyond it; on the right, the turned bodice, with the wrap's edge and the empire waist seam, which may run off the edge.
The armhole sits in the upper left of the image.

What must be clear:
The shoulder seam, from the neck point to the shoulder point.
The armhole edge, its facing and its top-stitch line, from the shoulder point round to the underarm.
The bare mannequin arm below the armhole, with the wall visible in the gap under the arm.
The wrap's crossing edge and its piping, the ties at the side, and the empire waist seam with the gathers below it, as far as they show.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### C. Angrakha, Short

Save as `sleeve-angrakha-short.png`.

```
Generate an image with framing like reference-sleeves, for the same base image (base-angrakha), keeping the same garment, fabric, colour, mannequin, lighting and background, with one change: the sleeves are short, ending about 15 cm below the shoulder point with a plain hem.

The form is turned about 30° to the right, so the left sleeve is seen from its outer side.
Top: just above the shoulder, with the shoulder line and the side of the neck opening showing.
Bottom: about 5 cm below where a full sleeve's cuff would be, so the bare mannequin arm shows below the short sleeve.
Left and right: the whole sleeve on the left, with a little wall beyond it; on the right, the turned bodice, with the wrap's edge and the empire waist seam, which may run off the edge.
The sleeve runs from the upper left towards the lower centre.

What must be clear:
The shoulder seam, from the neck point to the shoulder point.
The armhole seam, from the shoulder point round the sleeve cap to the underarm.
The sleeve's outer and inner edges down to its hem, with the wall visible in the gap under the arm.
The sleeve's hem edge and its top-stitch line, and the bare mannequin arm below it.
The wrap's crossing edge and its piping, the ties at the side, and the empire waist seam with the gathers below it, as far as they show.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

### C. Angrakha, Three-quarter

Save as `sleeve-angrakha-threequarter.png`.

```
Generate an image with framing like reference-sleeves, for the same base image (base-angrakha), keeping the same garment, fabric, colour, mannequin, lighting and background, with one change: the sleeves are three-quarter length, ending about 10 cm below the elbow with a plain cuff.

The form is turned about 30° to the right, so the left sleeve is seen from its outer side.
Top: just above the shoulder, with the shoulder line and the side of the neck opening showing.
Bottom: about 5 cm below where a full sleeve's cuff would be, so the bare mannequin forearm shows below the cuff.
Left and right: the whole sleeve on the left, with a little wall beyond it; on the right, the turned bodice, with the wrap's edge and the empire waist seam, which may run off the edge.
The sleeve runs from the upper left towards the lower centre.

What must be clear:
The shoulder seam, from the neck point to the shoulder point.
The armhole seam, from the shoulder point round the sleeve cap to the underarm.
The sleeve's outer and inner edges down to the cuff, with the wall visible in the gap under the arm.
The cuff edge and its top-stitch line, and the bare mannequin forearm below it.
The wrap's crossing edge and its piping, the ties at the side, and the empire waist seam with the gathers below it, as far as they show.
Every outer edge of the garment against the wall, on the shaded side too.
The weave of the white cloth in its brightest parts (nothing burnt out to pure white).
```

---

## D. StepD: layers and options, one chat per silhouette (2026-11-25)

What the layered builder (`builder.html`, `silhouette/parts/build_layers.py`) needs. Learned on the lehenga (2026-11-25, all seven
edits lined up 0 px with `torso-lehenga.png`, 1.5 - 2.7 / 255 outside the change):

- **An edit that changes one part keeps every other pixel; removing the whole garment at once makes the tool redraw the image**
  (the anarkali's bare form came back 17 px lower on another stand). Remove a garment in steps: sleeves, then the top, then the
  skirt, each an edit of the one before.
- **One change per image.** An image with two changes is usable only if it lines up with an image that has one of them.
- **Say what the form has under a sleeve.** The lehenga / anarkali form has no arms in the front views (rounded shoulder caps), and
  a linen arm in the turned sleeve view; the straight kurta's form has arms. Layers that disagree cannot be combined.
- **Porting:** between looks shot in the same setup (the lehenga and the anarkali: the same form, stand and light) a part ports at
  a light gain of 1.01 (a straight paste); onto the kurta (another setup) a neckline ports well, a sleeve poorly. So: make each
  option once in the lehenga / anarkali setup, port it; the kurta makes its own sleeve edits.
- **Close views by cropping:** the hem view can be cropped from the full-length view (≈ 1.1 × enlargement); the neck view can too,
  at ≈ 2.1 × (softer: 0.8 mm/px against the kurta's real neck view's 0.3). The sleeve view cannot (the form is turned 30°). If the
  neck and hem views are cropped, D3 needs only its sleeve-view prompts (L8 - L16, A3, K4 - K8).

How to run a chat: paste the opening message with the look's full-length photo attached; then each prompt in order, attaching
the image named under it (otherwise the tool edits whatever it made last); download each result at full size under its name into
`silhouette/sources/pending/`; regenerate any result that comes back zoomed, cropped or resized. Every prompt repeats the rules
because a long chat drifts.

### D1. Lehenga choli, full-length view (done 2026-11-25)

Each an edit; attach only the image named. Results: `pending/torso-lehenga-*.png`.

**1. `torso-lehenga-under-sleeveless.png`**, edit of `torso-lehenga.png`:
```
Edit this image. Remove both sleeves of the cropped top: the top becomes sleeveless, with a narrow turned and top-stitched edge along the armhole seam, exactly where the sleeves were sewn in. Do not change the rest of the top: the same high round neckline, the same fit, the same length and hem. Where the sleeves were, show what is behind them: the dress form's rounded linen shoulder caps, the wall, and the sides of the top and of the skirt, continuing their outline, waistband and folds exactly as they are where they are visible.

Change nothing else. Keep every other pixel exactly as it is: the same camera, framing and zoom, the same image size and 3:4 shape; the dress form, its dark wooden knob and its stand in the same place; the wall with its window light, the floor, the light. Do not crop, zoom or reframe. The dress form has no arms, only rounded shoulder caps: do not add arms. The cloth stays plain white matte cotton with no embroidery, lace or print; its brightest parts keep their weave (nothing burnt out to pure white), and every edge of the garment stays visible against the wall, on the shaded side too.
```

**2. `torso-lehenga-under-skirt.png`**, edit of result 1:
```
Edit this image. Remove the sleeveless cropped top completely. Show the bare dress form's upper body underneath it, exactly where it stands now: the same natural-linen cover with its seams and tape lines, continuing seamlessly from the band of bare form already visible above the skirt's waistband, up to the neck and the dark wooden knob, and the rounded shoulder caps. Its shading follows the same light, with no shadows left from the removed top. Do not change the skirt or its waistband at all.

Change nothing else. Keep every other pixel exactly as it is: the same camera, framing and zoom, the same image size and 3:4 shape; the dress form, its knob and its stand in the same place and at the same size; the wall with its window light, the floor, the light. Do not crop, zoom or reframe. The dress form has no arms: do not add arms.
```

**3. `torso-lehenga-under-form.png`**, edit of result 2:
```
Edit this image. Remove the skirt completely. Show the dress form's lower body as it is under the skirt: the same natural-linen cover down to where the form ends at the hips, then the stand's dark wooden pole down to the same tripod feet, which stay exactly where they are. Its shading follows the same light, with no shadows left from the removed skirt. Do not change the upper body of the form at all.

Change nothing else. Keep every other pixel exactly as it is: the same camera, framing and zoom, the same image size and 3:4 shape; the form, its knob and its stand in the same place and at the same size; the wall with its window light, the floor, the light. Do not crop, zoom or reframe.
```

**4. `torso-lehenga-neck-v.png`**, edit of `torso-lehenga.png`:
```
Edit this image. Change only the neckline of the cropped top into a V-neck: from the same two neck points where the round neckline meets the shoulder seams, two straight edges down to a point at the centre front about 12 cm below the neck points, finished with the same narrow turned edge as the round neckline. Where cloth is removed, show the dress form's natural-linen cover with its tape lines. Keep the top's shoulders, sleeves, length, hem and the band of bare form exactly as they are.

Change nothing else. Keep every other pixel exactly as it is: the same camera, framing and zoom, the same image size and 3:4 shape; the dress form, its knob and its stand in the same place; the wall, the floor, the light. Do not crop, zoom or reframe. The cloth stays plain white matte cotton with no embroidery, lace or print, nothing burnt out to pure white.
```

**5. `torso-lehenga-neck-boat.png`**, edit of `torso-lehenga.png`:
```
Edit this image. Change only the neckline of the cropped top into a boat neck: wide and shallow, running almost straight across from about 2 cm inside each shoulder point, dipping only about 3 cm at the centre front, finished with the same narrow turned edge as the round neckline. Where cloth is removed, show the dress form's natural-linen cover. Keep the top's shoulder seams, sleeves, length, hem and the band of bare form exactly as they are.

Change nothing else. Keep every other pixel exactly as it is: the same camera, framing and zoom, the same image size and 3:4 shape; the dress form, its knob and its stand in the same place; the wall, the floor, the light. Do not crop, zoom or reframe. The cloth stays plain white matte cotton with no embroidery, lace or print, nothing burnt out to pure white.
```

**6. `torso-lehenga-neck-mandarin.png`**, edit of `torso-lehenga.png` (the result has a small V notch at the top front):
```
Edit this image. Add a mandarin collar to the cropped top: a band of the same white cloth about 3 cm high, standing up along the existing round neckline, its two ends meeting edge to edge at the centre front, with no slit, placket or opening below it. The neckline itself stays where it is. Keep the rest of the top, the sleeves and the band of bare form exactly as they are.

Change nothing else. Keep every other pixel exactly as it is: the same camera, framing and zoom, the same image size and 3:4 shape; the dress form, its knob and its stand in the same place; the wall, the floor, the light. Do not crop, zoom or reframe. The cloth stays plain white matte cotton with no embroidery, lace or print, nothing burnt out to pure white, and the collar's edge stays visible against the form's linen neck.
```

**7. `torso-lehenga-sleeve-short.png`**, edit of `torso-lehenga.png` (it came back as `torso-lehenga-neck-mandarin-sleeve-short.png`, made on result 6; only its sleeves are used):
```
Edit this image. Change only both sleeves into short sleeves ending 18 cm below the shoulder point. Keep the sleeve's own cut and width down to there, and finish it with the same narrow turned hem as the current cuff. Below the new hem, where the long sleeve was, show what was behind it: the wall, and the sides of the top and of the skirt with its waistband and folds, continuing exactly as they are where they are visible. The sleeve has no arm in it.

Change nothing else. Keep every other pixel exactly as it is: the same camera, framing and zoom, the same image size and 3:4 shape; the dress form, its knob and its stand in the same place; the wall with its window light, the floor, the light. Do not crop, zoom or reframe. The dress form has no arms, only rounded shoulder caps: do not add arms. The cloth stays plain white matte cotton, nothing burnt out to pure white, and every edge stays visible against the wall.
```

**8. `torso-lehenga-sleeve-threequarter.png`** (still needed): prompt 7 with its first sentence *"Edit this image. Change only both
sleeves into three-quarter sleeves ending 45 cm below the shoulder point."*

### D2. Straight kurta, full-length view (still needed)

**`torso-straight-under-sleeveless.png`**, edit of `torso-straight.png`:
```
Edit this photo. Remove both sleeves: the kurta becomes sleeveless, with a narrow turned and top-stitched edge along the armhole seam, exactly where the sleeves were sewn in. Do not change the kurta's body at all: it stays a straight, loose white kurta with straight side seams, no waist seam, no flare, the same round neckline, the same length, side slits and folds. Where the sleeves were, show the dress form's own natural-linen arms as they are under the sleeves, and the wall behind them. Keep a visible edge between the garment and the wall on both sides. Change nothing else: the same camera, framing and image size, the same stand, wall, floor and light.
```

**`torso-straight-under-form.png`**, edit of `torso-straight.png` (if it comes back redrawn, remove the kurta in steps as in D1):
```
Edit this photo. Remove the kurta completely and show the bare dress form underneath it, exactly where it stands now and at exactly the same size: the same natural-linen cover with its seams and tape lines, its neck and dark wooden cap, its arms, and the same stand. Change nothing else: the same camera, framing and image size, the same wall, floor and light. The form's shading follows that light, with no shadows left from the removed kurta.
```

### D3. The close views, one chat per silhouette

Order: the lehenga's chat first (the anarkali's uses two of its images as framing references). The anarkali's neck and hem views
are regenerated, framed like the lehenga's (its current neck view is framed wider than `plate.md` §5, its hem view from the front
to the floor), so that parts port between the two at the same framing.

#### Chat 1: lehenga choli

**Opening message**, attach `torso-lehenga.png`:
```
This is a white cotton lehenga choli on a dress form. In this chat I will ask for several images of exactly this garment, this dress form, this wall, floor and light: first new close-up views, then edits of those views. Every edit changes only what I describe; everything else stays exactly the same, pixel for pixel. The dress form has no arms in the front views, only rounded linen shoulder caps. Reply only "Ready" to this message.
```

**L1. `neck-lehenga.png`**, attach `torso-lehenga.png`:
```
Make a new photo of exactly this garment on exactly this dress form, in the same room and the same light: a close-up of the neck area, as a 3:4 portrait image, 1792 × 2400.

The camera is at the same height and straight in front of the form, with no turn, only closer.
Top edge: just above the top of the wooden knob.
Bottom edge: about 5 cm below the crop top's hem, so the band of bare form and the top edge of the skirt's waistband show.
Width: the two shoulder points sit about 10 % in from the left and right edges; the sleeves run out of the image at the sides.
The centre front runs straight down the middle of the image.

Keep the garment exactly as it is: plain white matte cotton; the high round neckline with its narrow turned edge; the shoulder seams; the darts; the long sleeves; the crop top's hem; the band of bare form; the waistband. The form, its linen cover with its tape lines, and the knob stay the same; the wall and the light stay the same. The dress form has no arms, only rounded linen shoulder caps: do not add arms.

What must be clear: the neckline edge and its top-stitch; both shoulder seams; both armhole seams; the darts and the top's hem; every outer edge of the garment against the wall, on the shaded side too; the weave of the cloth in its brightest parts (nothing burnt out to pure white).
```

**L2. `neck-lehenga-under-sleeveless.png`**, attach L1:
```
Edit the attached image. Remove both sleeves of the crop top: the top becomes sleeveless, with a narrow turned and top-stitched edge along the armhole seam, exactly where the sleeves were sewn in. Do not change the rest of the top. Where the sleeves were, show what is behind them: the dress form's rounded linen shoulder caps, the wall, and the sides of the top, the bare-form band and the waistband, continuing exactly as they are where they show.

Change nothing else. Keep every other pixel exactly as it is: the same camera, framing, zoom and light, the same image size (1792 × 2400). Do not crop, zoom or reframe. The dress form has no arms, only rounded linen shoulder caps: do not add arms. The cloth stays plain white matte cotton; nothing burnt out to pure white; every garment edge stays visible against the wall.
```

**L3. `neck-lehenga-neck-v.png`**, attach L1:
```
Edit the attached image. Change only the neckline of the crop top into a V-neck: from the same two neck points where the round neckline meets the shoulder seams, two straight edges down to a point at the centre front about 12 cm below the neck points, finished with the same narrow turned edge as the round neckline. Where cloth is removed, show the dress form's natural-linen cover with its tape lines. Keep the shoulders, sleeves, darts and hem exactly as they are.

Change nothing else. Keep every other pixel exactly as it is: the same camera, framing, zoom and light, the same image size (1792 × 2400). Do not crop, zoom or reframe. The dress form has no arms: do not add arms. The cloth stays plain white matte cotton; nothing burnt out to pure white.
```

**L4. `neck-lehenga-neck-boat.png`**, attach L1:
```
Edit the attached image. Change only the neckline of the crop top into a boat neck: wide and shallow, running almost straight across from about 2 cm inside each shoulder point, dipping only about 3 cm at the centre front, finished with the same narrow turned edge as the round neckline. Where cloth is removed, show the dress form's natural-linen cover. Keep the shoulder seams, sleeves, darts and hem exactly as they are.

Change nothing else. Keep every other pixel exactly as it is: the same camera, framing, zoom and light, the same image size (1792 × 2400). Do not crop, zoom or reframe. The dress form has no arms: do not add arms. The cloth stays plain white matte cotton; nothing burnt out to pure white.
```

**L5. `neck-lehenga-neck-mandarin.png`**, attach L1:
```
Edit the attached image. Add a mandarin collar to the crop top: a band of the same white cloth about 3 cm high, standing up along the existing round neckline, its two ends meeting at the centre front with a small V-shaped notch at the top edge, and no slit or placket below the collar. The neckline itself stays where it is. Keep the rest of the top and the sleeves exactly as they are.

Change nothing else. Keep every other pixel exactly as it is: the same camera, framing, zoom and light, the same image size (1792 × 2400). Do not crop, zoom or reframe. The dress form has no arms: do not add arms. The cloth stays plain white matte cotton; nothing burnt out to pure white; the collar's edge stays visible against the form's linen neck.
```

**L6. `neck-lehenga-sleeve-short.png`**, attach L1:
```
Edit the attached image. Change only both sleeves into short sleeves ending 18 cm below the shoulder point. Keep the sleeve's own cut and width down to there, and finish it with a narrow turned hem like the crop top's. Below the new hem, where the long sleeve was, show what was behind it: the wall, and the sides of the top, the bare-form band and the waistband, continuing exactly as they are where they show. The sleeve has no arm in it.

Change nothing else. Keep every other pixel exactly as it is: the same camera, framing, zoom and light, the same image size (1792 × 2400). Do not crop, zoom or reframe. The dress form has no arms, only rounded linen shoulder caps: do not add arms. The cloth stays plain white matte cotton; nothing burnt out to pure white; every edge stays visible against the wall.
```

**L7. `neck-lehenga-sleeve-puff.png`**, attach L1:
```
Edit the attached image. Change only both sleeves into short puff sleeves: gathered into the armhole at the top, full and rounded, ending in a narrow straight band 12 cm below the shoulder point. Below the band, where the long sleeve was, show what was behind it: the wall, and the sides of the top, the bare-form band and the waistband, continuing exactly as they are where they show. The sleeve has no arm in it.

Change nothing else. Keep every other pixel exactly as it is: the same camera, framing, zoom and light, the same image size (1792 × 2400). Do not crop, zoom or reframe. The dress form has no arms, only rounded linen shoulder caps: do not add arms. The cloth stays plain white matte cotton; nothing burnt out to pure white; every edge stays visible against the wall.
```

**L8. `sleeve-lehenga.png`**, attach `torso-lehenga.png` and `pending/sleeve-anarkali.png`:
```
Make a new photo of exactly the lehenga choli from the first attached image, on exactly that dress form, in the same room and the same light, framed exactly like the second attached image (a different garment): the same turn of the form, about 30° to the right, so the left sleeve is seen from its outer side; the same camera height and distance; the same crop; the same linen arm of the dress form showing below the cuff. Use the second image only for the framing, the form and its arm; the garment is the lehenga's crop top and skirt. 3:4 portrait, 1792 × 2400.

Keep the garment exactly as it is: plain white matte cotton, the high round neckline, the long fitted sleeves, the crop top's darts and hem, the band of bare form, the waistband.

What must be clear: the shoulder seam from the neck point to the shoulder point; the armhole seam round the sleeve cap to the underarm; the sleeve's outer and inner edges down to the cuff, with the wall in the gap under the arm; the cuff edge, its top-stitch and the linen arm below it; the crop top's side, dart and hem, the bare-form band and the waistband as far as they show; every outer edge of the garment against the wall, on the shaded side too; nothing burnt out to pure white.
```

**L9. `sleeve-lehenga-under-sleeveless.png`**, attach L8:
```
Edit the attached image. Remove the sleeve: the crop top becomes sleeveless, with a narrow turned and top-stitched edge along the armhole seam, exactly where the sleeve was sewn in. Do not change the rest of the top. Where the sleeve was, show the dress form's linen arm, continuing exactly from the part that shows below the cuff up to the shoulder, and the wall and the side of the top behind it.

Change nothing else. Keep every other pixel exactly as it is: the same camera, turn, framing, zoom and light, the same image size (1792 × 2400). Do not crop, zoom or reframe. The cloth stays plain white matte cotton; nothing burnt out to pure white; every garment edge stays visible against the wall.
```

**L10. `sleeve-lehenga-sleeve-short.png`**, attach L8:
```
Edit the attached image. Change only the sleeve into a short sleeve ending 18 cm below the shoulder point. Keep its own cut and width down to there, and finish it with a narrow turned hem. Below the new hem, show the dress form's linen arm, continuing exactly from the part that shows below the old cuff.

Change nothing else. Keep every other pixel exactly as it is: the same camera, turn, framing, zoom and light, the same image size (1792 × 2400). Do not crop, zoom or reframe. The cloth stays plain white matte cotton; nothing burnt out to pure white; every garment edge stays visible against the wall.
```

**L11. `sleeve-lehenga-sleeve-threequarter.png`**, attach L8: L10 with its first sentence *"Edit the attached image. Change only
the sleeve into a three-quarter sleeve ending 45 cm below the shoulder point."*

**L12. `sleeve-lehenga-sleeve-puff.png`**, attach L8:
```
Edit the attached image. Change only the sleeve into a short puff sleeve: gathered into the armhole at the top, full and rounded, ending in a narrow straight band 12 cm below the shoulder point. Below the band, show the dress form's linen arm, continuing exactly from the part that shows below the old cuff.

Change nothing else. Keep every other pixel exactly as it is: the same camera, turn, framing, zoom and light, the same image size (1792 × 2400). Do not crop, zoom or reframe. The cloth stays plain white matte cotton; nothing burnt out to pure white; every garment edge stays visible against the wall.
```

**L13. `sleeve-lehenga-sleeve-bell.png`**, attach L8:
```
Edit the attached image. Change only the sleeve into a bell sleeve: fitted like the current sleeve from the shoulder to the elbow, then flaring out into a wide bell that ends at the same length as the current sleeve, its opening about twice as wide as the upper arm, with soft vertical folds and a narrow turned hem. Inside the bell's mouth, show the dress form's linen arm.

Change nothing else. Keep every other pixel exactly as it is: the same camera, turn, framing, zoom and light, the same image size (1792 × 2400). Do not crop, zoom or reframe. The cloth stays plain white matte cotton; nothing burnt out to pure white; every garment edge stays visible against the wall.
```

**L14. `sleeve-lehenga-neck-v.png`**, attach L8 (optional: the sleeve view shows the neck only in part):
```
Edit the attached image. Change only the neckline of the crop top into a V-neck, seen at this angle: from the same two neck points where the round neckline meets the shoulder seams, two straight edges down to a point at the centre front about 12 cm below the neck points, finished with the same narrow turned edge. Where cloth is removed, show the dress form's natural-linen cover with its tape lines. Keep the shoulder, the sleeve and the rest of the top exactly as they are.

Change nothing else. Keep every other pixel exactly as it is: the same camera, turn, framing, zoom and light, the same image size (1792 × 2400). Do not crop, zoom or reframe. The cloth stays plain white matte cotton; nothing burnt out to pure white.
```

**L15. `sleeve-lehenga-neck-boat.png`**, attach L8 (optional):
```
Edit the attached image. Change only the neckline of the crop top into a boat neck, seen at this angle: wide and shallow, running almost straight across from about 2 cm inside each shoulder point, dipping only about 3 cm at the centre front, finished with the same narrow turned edge. Where cloth is removed, show the dress form's natural-linen cover. Keep the shoulder seam, the sleeve and the rest of the top exactly as they are.

Change nothing else. Keep every other pixel exactly as it is: the same camera, turn, framing, zoom and light, the same image size (1792 × 2400). Do not crop, zoom or reframe. The cloth stays plain white matte cotton; nothing burnt out to pure white.
```

**L16. `sleeve-lehenga-neck-mandarin.png`**, attach L8 (optional):
```
Edit the attached image. Add a mandarin collar to the crop top, seen at this angle: a band of the same white cloth about 3 cm high, standing up along the existing round neckline, its two ends meeting at the centre front with a small V-shaped notch at the top edge, and no slit or placket below the collar. Keep the rest of the top and the sleeve exactly as they are.

Change nothing else. Keep every other pixel exactly as it is: the same camera, turn, framing, zoom and light, the same image size (1792 × 2400). Do not crop, zoom or reframe. The cloth stays plain white matte cotton; nothing burnt out to pure white; the collar's edge stays visible against the form's linen neck.
```

**L17. `hem-lehenga.png`**, attach `torso-lehenga.png` (or crop it from the full-length view instead):
```
Make a new photo of exactly this lehenga skirt on exactly this dress form and stand, in the same room and the same light: a close-up of the hem, as a 3:4 portrait image, 1792 × 2400.

The form is turned about 10° to the right; the camera is lower, level with the hem area.
Top edge: about 35 cm above the hem, well below the waistband, so only the flared panels show.
Bottom edge: about 8 cm below the hem, with the wooden stand and its feet showing underneath and the floor with its window light.
Width: the hem across the full width of the flare, curving out of sight at both sides.
The hem sits in the lower third of the image.

Keep the skirt exactly as it is: plain white matte cotton, the same panels, folds and length.

What must be clear: the hem edge along its whole length, its turn-up and its top-stitch; the panel seams running down to the hem; the folds of the flare with their light and shadow; where the hem passes behind at the sides; the stand below; every outer edge of the garment against the wall, on the shaded side too; nothing burnt out to pure white.
```

#### Chat 2: anarkali

**Opening message**, attach `torso-anarkali.png`: the lehenga's opening message with "lehenga choli" changed to "anarkali".

**A1. `neck-anarkali.png`** (regenerated), attach `torso-anarkali.png` and `neck-lehenga.png`:
```
Make a new photo of exactly the anarkali from the first attached image, on exactly that dress form, in the same room and the same light, framed exactly like the second attached image (a different garment): the same camera height and distance, straight in front with no turn, the same crop from just above the wooden knob, the shoulder points about 10 % in from the left and right edges, the centre front down the middle. Use the second image only for the framing; the garment is the anarkali: the fitted bodice with its princess seams, the empire seam under the bust, the high round neckline, the long sleeves, the start of the pleated skirt. 3:4 portrait, 1792 × 2400.

The dress form has no arms, only rounded linen shoulder caps: do not add arms.

What must be clear: the neckline edge and its top-stitch; both shoulder seams; both armhole seams; the princess seams and the empire seam; every outer edge of the garment against the wall, on the shaded side too; nothing burnt out to pure white.
```

**A2. `neck-anarkali-under-sleeveless.png`**, attach A1: L2 with "crop top" → "bodice" and "the sides of the top, the bare-form
band and the waistband" → "the sides of the bodice and the skirt".

**A3. `sleeve-anarkali-under-sleeveless.png`**, attach `pending/sleeve-anarkali.png`: L9 with "crop top" → "bodice" and "the side
of the top" → "the side of the bodice".

**A4. `hem-anarkali.png`** (regenerated), attach `torso-anarkali.png` and `hem-lehenga.png`:
```
Make a new photo of exactly the anarkali's skirt from the first attached image, on exactly that dress form and stand, in the same room and the same light, framed exactly like the second attached image (a different garment): the form turned about 10° to the right; from about 35 cm above the hem to about 8 cm below it, with the stand, its feet and the floor showing; the hem across the full width, curving out of sight at both sides; the hem in the lower third. Use the second image only for the framing; the garment is the anarkali's pleated, flared skirt, with its side slit at the image right, slightly open. 3:4 portrait, 1792 × 2400.

What must be clear: the hem edge along its whole length, its turn-up and its top-stitch; the pleats and panel seams running down to the hem; the slit's two edges and its top; the folds of the flare with their light and shadow; the stand below; every outer edge of the garment against the wall, on the shaded side too; nothing burnt out to pure white.
```

#### Chat 3: straight kurta

Its views are square (2048 × 2048), and its dress form has arms.

**Opening message**, attach `torso-straight.png`:
```
This is a white cotton straight kurta on a dress form with linen arms. In this chat I will attach close-up views of it and ask for edits. Every edit changes only what I describe; everything else stays exactly the same, pixel for pixel, at the same image size. Reply only "Ready" to this message.
```

**K1. `neck-straight-under-sleeveless.png`**, attach `neck-straight.png`:
```
Edit the attached image. Remove both sleeves: the kurta becomes sleeveless, with a narrow turned and top-stitched edge along the armhole seam, exactly where the sleeves were sewn in. Do not change the kurta's body: the same round neckline, the same fit and folds. Where the sleeves were, show the dress form's own linen arms as they are under the sleeves, and the wall behind them.

Change nothing else. Keep every other pixel exactly as it is: the same camera, framing, zoom and light, the same image size (2048 × 2048). Do not crop, zoom or reframe. The cloth stays plain white matte cotton; nothing burnt out to pure white; every garment edge stays visible against the wall.
```

**K2. `neck-straight-sleeve-short.png`**, attach `neck-straight.png`:
```
Edit the attached image. Change only both sleeves into short sleeves ending 18 cm below the shoulder point. Keep the sleeve's own cut and width down to there, and finish it with a narrow turned hem. Below the new hem, show the dress form's own linen arms as they are under the sleeves.

Change nothing else. Keep every other pixel exactly as it is: the same camera, framing, zoom and light, the same image size (2048 × 2048). Do not crop, zoom or reframe. The cloth stays plain white matte cotton; nothing burnt out to pure white; every garment edge stays visible against the wall.
```

**K3. `neck-straight-sleeve-puff.png`**, attach `neck-straight.png`: K2 with its first two sentences *"Edit the attached image. Change
only both sleeves into short puff sleeves: gathered into the armhole at the top, full and rounded, ending in a narrow straight band
12 cm below the shoulder point."*

**K4. `sleeve-straight-under-sleeveless.png`**, attach `sleeve-straight.png`:
```
Edit the attached image. Remove the sleeve: the kurta becomes sleeveless, with a narrow turned and top-stitched edge along the armhole seam, exactly where the sleeve was sewn in. Do not change the kurta's body. Where the sleeve was, show the dress form's linen arm, continuing exactly from the part that shows below the cuff up to the shoulder, and the wall behind it.

Change nothing else. Keep every other pixel exactly as it is: the same camera, turn, framing, zoom and light, the same image size (2048 × 2048). Do not crop, zoom or reframe. The cloth stays plain white matte cotton; nothing burnt out to pure white; every garment edge stays visible against the wall.
```

**K5. `sleeve-straight-sleeve-short.png`**, attach `sleeve-straight.png`:
```
Edit the attached image. Change only the sleeve into a short sleeve ending 18 cm below the shoulder point. Keep its own cut and width down to there, and finish it with a narrow turned hem. Below the new hem, show the dress form's linen arm, continuing exactly from the part that shows below the old cuff.

Change nothing else. Keep every other pixel exactly as it is: the same camera, turn, framing, zoom and light, the same image size (2048 × 2048). Do not crop, zoom or reframe. The cloth stays plain white matte cotton; nothing burnt out to pure white; every garment edge stays visible against the wall.
```

**K6. `sleeve-straight-sleeve-threequarter.png`**, attach `sleeve-straight.png`: K5 with its first sentence *"Edit the attached image.
Change only the sleeve into a three-quarter sleeve ending 45 cm below the shoulder point."*

**K7. `sleeve-straight-sleeve-puff.png`**, attach `sleeve-straight.png`: K5 with its first two sentences *"Edit the attached image.
Change only the sleeve into a short puff sleeve: gathered into the armhole at the top, full and rounded, ending in a narrow straight
band 12 cm below the shoulder point."*

**K8. `sleeve-straight-sleeve-bell.png`**, attach `sleeve-straight.png`:
```
Edit the attached image. Change only the sleeve into a bell sleeve: fitted like the current sleeve from the shoulder to the elbow, then flaring out into a wide bell that ends at the same length as the current sleeve, its opening about twice as wide as the upper arm, with soft vertical folds and a narrow turned hem. Inside the bell's mouth, show the dress form's linen arm.

Change nothing else. Keep every other pixel exactly as it is: the same camera, turn, framing, zoom and light, the same image size (2048 × 2048). Do not crop, zoom or reframe. The cloth stays plain white matte cotton; nothing burnt out to pure white; every garment edge stays visible against the wall.
```
