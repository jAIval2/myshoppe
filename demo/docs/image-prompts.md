# Image prompts

39 prompts. Order: A1 first (the angrakha's other prompts need it), then the rest of A, then B and C.

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
