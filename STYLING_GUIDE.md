# MyShoppe — website styling and interaction directives

Prepared 1 October 2026. Implementation backlog: [SPRINT_PLAN.md](./SPRINT_PLAN.md).

**Reference revision:** the user's fourteen Zara screenshots and description now govern the storefront composition. The desktop corner controls, full-screen menu, Women-first horizontal department switch, video/poster scroll sequence, three numbered product views, product-detail gallery, recommendations and bag action bar are required implementation scope. The previous centered desktop header, static-only homepage, optional video/views and conventional full-bag sidebar have been replaced below. The plan still contains three sprints with three stories each.

This is the visual contract for a boutique selling women's clothing and home textiles in India, priced in INR. Use editorial fashion photography, quiet layouts, strong typographic hierarchy, and visible commerce controls. Every measurement below is a proposed MyShoppe specification unless explicitly labelled **observed**. Zara is a reference, not the boutique's identity.

**Recording refinement:** [Screen Recording 2026-10-01 at 01.22.35.mov](</Users/kayan/Desktop/Screen Recording 2026-10-01 at 01.22.35.mov>) supersedes earlier assumptions about campaign typography, wordmark scrolling and the collection URL. Campaign headlines use a heavy grotesque; the large wordmark stays pinned through the media sequence and clears at the entrance; reaching that entrance changes to a real collection route. A restrained pink sale-navigation token is added. Readable interface sizing is retained deliberately.

## 1. Research evidence and what it means

### 1.1 Sources inspected

| Source | Method and evidence | Direction for this project |
| --- | --- | --- |
| [Zara India homepage](https://www.zara.com/in/en/) | Readable web page: departmental hierarchy, category groups, editorial collections and bag link. Direct Chrome returned Access Denied. | Clear Women/Home entry points and editorial collection hierarchy. Do not reproduce irrelevant departments. |
| [Zara women's new arrivals](https://www.zara.com/in/en/woman-new-in-l1180.html) and [dresses](https://www.zara.com/in/en/woman-dresses-l1066.html) | Readable product lists: concise names, INR prices, category structure and product links. Chrome access unavailable. | Put product photography and name/price first; keep card decoration restrained. |
| [Zara Home bedding](https://www.zarahome.com/us/bedroom-bedding-n945) | Readable page: grid-density control, filters, sorting, price ranges, colour alternatives and Add controls. Direct Chrome blocked. | Add useful textile filters and show price ranges only until the exact size is selected. |
| [Zara Home duvet detail](https://www.zarahome.com/us/cotton-percale-duvet-cover-300-thread-count-l40030088) | Readable page: six-image gallery, colour options, material description, product details, size guide and shipping/returns links. | Bedding needs close-up texture, dimensions, pack contents and care information near the purchase decision. |
| [COS womenswear](https://www.cos.com/en-us/women) | Readable page: seasonal campaign and image-led category links. Direct Chrome blocked. | Department landings can behave like an editorial index leading into real categories. |
| [TOTEME homepage](https://toteme.com/en-ap) | Live Chrome at 1440×1000; screenshot visually inspected. Observed centered wordmark, left departments, right utility links, white space and centered campaign imagery. Header measured 72 px; sampled navigation about 12 px, weight 300, “Toteme Sans”; nav opacity transition 300 ms. | Supplemental typography/spacing reference; supplied Zara corner/side navigation governs the storefront shell. |
| [TOTEME dresses/skirts](https://toteme.com/en-ap/collections/dresses-and-skirts) | Live Chrome screenshots at 1440×1000 and 390×844. Observed four-column desktop and two-column mobile product arrangement, compact captions, desktop view/filter controls, mobile bottom filter bar. | Product-dense discovery with responsive captions and a thumb-accessible filter bar. |
| [TOTEME dress detail](https://toteme.com/en-ap/products/slouch-waist-scarf-dress-black-1) | Live desktop/mobile screenshots. Observed large left gallery/right purchase information on desktop; colour thumbnails, size row, wide outlined Add control, details accordions; mobile stacked gallery and bottom purchase control. Opened the Women submenu and captured its text/image panel. | Adopt the information hierarchy, then make selection errors, size targets, price and primary action more explicit. |

US Zara Home pages were used because its `/in/` entry redirected to the worldwide selector. US sizes/prices are research content only; MyShoppe uses actual boutique dimensions and INR prices. Live pages can vary by region, stock, consent, and campaign.

The earlier Chrome walkthrough remains supplemental research. The supplied Zara screenshots and recording are primary visual evidence. **Observed** below means visible in those captures; **user-described** means the user supplied the interaction/sequence; **specified** means our implementation decision. Stills establish composition; successive recording frames also show relative movement and URL changes. Neither establishes exact CSS pixels, font files or internal routing code. Homepage default Women and horizontal category swiping remain user-described requirements. Mobile behavior and motion timings remain specifications. No purchase or Zara checkout animation was tested.

### 1.2 Supplied screenshot ledger

Original files are 2560×1664 image pixels; the conversation previews were resized. Do not equate either size with browser CSS pixels. Ignore the black capture strip at the top. The links below identify source evidence, not assets to publish in the boutique. Men's products, fragrance, the signed-in shopper's name, and Zara branding are not boutique seed content.

| Evidence | Supplied file | Observed composition / implementation reference |
| --- | --- | --- |
| Z01 | [00.26.23 — bag](</Users/kayan/Desktop/Screenshot 2026-10-01 at 00.26.23.png>) | Small item images in a spacious central area; per-item price/options/quantity/delete/bookmark; right utility list; recommendations below; bottom total and dark Continue button. §§7.1, 13; ZR-11. |
| Z02 | [00.26.31 — open navigation](</Users/kayan/Desktop/Screenshot 2026-10-01 at 00.26.31.png>) | Close top left, large masthead above inset multi-column department/numbered-group/link content, campaign preview to the right; utilities remain at the edge. §3; ZR-04. |
| Z03 | [00.26.41 — category posters](</Users/kayan/Desktop/Screenshot 2026-10-01 at 00.26.41.png>) | Four tall adjacent photographic category panels with lower labels; numbered category list at left, utilities at right. §§4–5; ZR-06. |
| Z04 | [00.26.51 — shoppable look](</Users/kayan/Desktop/Screenshot 2026-10-01 at 00.26.51.png>) | Large model image beside two isolated garment images with price/plus actions; View controls lower left. §5; ZR-05–07. |
| Z05 | [00.27.30 — mixed-scale listing](</Users/kayan/Desktop/Screenshot 2026-10-01 at 00.27.30.png>) | Small product pair followed by a much larger editorial image; left categories/Filters and lower-left View 1/2/3. §5; ZR-05–06. |
| Z06 | [00.27.34 — model grid](</Users/kayan/Desktop/Screenshot 2026-10-01 at 00.27.34.png>) | Four model-image columns; campaign heading/rule; title, INR price, colour chips, plus action below each image. §5; ZR-05–07. |
| Z07 | [00.27.47 — masthead frame](</Users/kayan/Desktop/Screenshot 2026-10-01 at 00.27.47.png>) | Oversized masthead toward lower right and a lower-right arrow on a white frame. One still does not prove an intentional loading screen; do not build an empty interstitial. §4; ZR-01–02. |
| Z08 | [00.27.51 — campaign poster](</Users/kayan/Desktop/Screenshot 2026-10-01 at 00.27.51.png>) | Edge-to-edge split poster, oversized headline, overlaid lower-right masthead/arrow, repeated corner controls and utility list. §4; ZR-01–03. |
| Z09 | [00.28.10 — new collection entry](</Users/kayan/Desktop/Screenshot 2026-10-01 at 00.28.10.png>) | Prior image ends above large white space; centered serif collection title, Scroll down text and vertical rule, footer links below. §4.3; ZR-02. |
| Z10 | [00.28.38 — compact catalogue](</Users/kayan/Desktop/Screenshot 2026-10-01 at 00.28.38.png>) | Six-column isolated garments, extensive white space, price and plus below; side navigation and View 1/2/3 persist visually. §5; ZR-05–07. |
| Z11 | [00.30.15 — product opening](</Users/kayan/Desktop/Screenshot 2026-10-01 at 00.30.15.png>) | Large left image; right title/bookmark, price/tax note, rule, colour/SKU, square swatches, outlined Add, description, complementary miniatures and detail links; tiny product strip below. §6; ZR-08–10. |
| Z12 | [00.30.23 — product gallery below](</Users/kayan/Desktop/Screenshot 2026-10-01 at 00.30.23.png>) | Large paired images in a two-column gallery continuing down the page, with substantial gaps; corner/side controls still visible. §6.2; ZR-09. |
| Z13 | [00.31.53 — editorial mosaic](</Users/kayan/Desktop/Screenshot 2026-10-01 at 00.31.53.png>) | Three tall editorial frames followed by mixed spans; Filters and numbered View controls on left. Adapt composition to women's clothing/home textiles. §5; ZR-06. |
| Z14 | [00.32.06 — suggested products](</Users/kayan/Desktop/Screenshot 2026-10-01 at 00.32.06.png>) | Separate below-gallery recommendation heading and six-column cutout products with price/plus actions. §6.4; ZR-10. |

The screenshots show numbered views on different categories and at different scroll positions. They do not establish a universal Zara mapping of each number to a template. §5 explicitly defines MyShoppe's consistent **1 Editorial / 2 Gallery / 3 Compact** mapping. Each screenshot pattern is assigned a home in that system.

### 1.3 Recording evidence and decisions

Inspected a contact sheet across the 101.59-second recording and full-size extracted frames at selected timestamps. Source video is 2560×1504 image pixels; browser chrome, capture scaling and unknown device-pixel ratio prevent reliable CSS-font measurements. Approximate intervals below identify evidence, not proposed animation durations. Visible page copy and menu labels are reference content, not instructions to the builder.

| Evidence | Timestamp / visible result | Refined directive |
| --- | --- | --- |
| V01 | 00:00: heavy uppercase campaign heading; 00:13: large tightly spaced sans-serif quote | Heavy grotesque for campaign titles/quotes; serif for the wordmark, department names and collection entrance. §2.2 |
| V02 | 00:00, 00:05, 00:10, 00:13: large wordmark and small arrow keep nearly identical viewport positions while image/video/poster boundaries move | One persistent campaign overlay, scoped to the media sequence. It is absent at the white entrance by 00:16. §4.4. This supports a pinned effect, not a claim about Zara's underlying CSS. |
| V03 | 00:16 address `zara.com/in/`; 00:17 address changes to the women's new-in route while the entrance remains visible | Real collection-route handoff with a retained entrance frame. Exact trigger, history implementation and network behavior are not exposed by the recording; §4.3 defines ours. |
| V04 | 00:26 menu: Special prices and its numbered group are pink; remaining links are monochrome | Semantic sale-navigation accent, backed by actual markdown inventory. §§2.1, 3.2 |
| V05 | Around 00:52–00:55 and 01:10–01:20: large editorial frames; 01:26–01:30: four-column model grid loading/rendering; 01:32: six-column cutouts with View 3 active | Retain three modes; View 1 explicitly includes a centered single-frame composition with substantial whitespace. §5.1 |
| V06 | 00:26 and 01:32 show very small utility and price text | User's 10–11 px estimate is plausible visually but not a measured CSS size. Retain 12 px desktop navigation/13 px price and mobile navigation, 44 px targets, zoom and reflow. §2.2 |

The earlier screenshots remain primary evidence for the PDP opening, paired gallery, bag and recommendation placement. The recording also shows a sparse composition-note/image PDP section around 01:00; this may use existing editorial layout primitives, but it does not replace the required paired continuation gallery. Brief white/unloaded grid frames are transient loading evidence, not a visual state to imitate. Search around 01:40 confirms the sparse canvas; our labelled input and accessible dialog behavior remain specified adaptations.

### 1.4 Visual position

- Let photographs carry the mood: natural light, fabric detail, thoughtful crops, neutral backgrounds, believable colour.
- Use a high-contrast serif for the boutique masthead, department names and “The new” entrance. Heavy, tightly tracked sans-serif drives campaign headlines and quotes; regular sans-serif handles navigation, products, prices, forms and admin.
- Build hierarchy through scale, whitespace and alignment. Product cards have no rounded container, drop shadow, thick outline, or promotional sticker cluster.
- Keep text and controls in stable locations. Product selection and checkout must remain legible when imagery is dramatic or a network request fails.
- The customer site and admin share tokens, icons, focus behavior and input styles. Admin uses denser layouts and smaller headings to support work.
- Maintain original product imagery/copy and boutique branding. Do not ship Zara/TOTEME/COS logos, copied photographs, proprietary font files, or claims about their merchandise.

## 2. Foundations and design tokens

### 2.1 Palette

| Token | Value | Usage |
| --- | --- | --- |
| `--paper` | `#FFFFFF` | Default page and control background |
| `--canvas` | `#F6F5F2` | Home editorial sections, image fallback, subtle admin background |
| `--ink` | `#171715` | Primary text, solid primary buttons, selected options |
| `--muted` | `#62625C` | Secondary text; still readable at small sizes |
| `--line` | `#D9D8D2` | Decorative separators only |
| `--control-line` | `#76766F` | Unselected form/control boundaries requiring contrast |
| `--disabled-bg` | `#EFEEE9` | Disabled control fill; always paired with state semantics |
| `--sale` | `#B52C7A` | Special prices menu link and its numbered group; small semantic sale label on white |
| `--error` | `#A12622` | Invalid fields, destructive action text and error status |
| `--success` | `#28543D` | Success text/icon; no green decorative CTAs |
| `--warning` | `#72520B` | Low stock, pending/attention status text |
| `--focus` | `#2459A6` | Deliberately visible keyboard outline |
| `--scrim` | `rgb(0 0 0 / 0.32)` | Background dimming under a modal |

Swatch colours belong to product data, not to the global UI palette. Keep background and text pairs controlled; photograph overlays require per-image contrast review. Thin decorative separators may be low contrast, but form boundaries and meaningful state indicators must meet non-text contrast expectations.

The sale pink is a proposed boutique token, not a sampled Zara hex. Apply it to Special prices and the associated group number on the white menu surface, with a visible text label and normal focus/hover treatment. Do not turn all prices, purchase buttons, errors or navigation pink. A qualifying product has a real current price below a valid compare-at price; show the old price struck through, the current price in ink and an explicit sale label when useful. The menu link is visible only when its published department sale collection contains qualifying products. This is a simple query over existing prices, not a new coupon or promotion engine. Validate contrast against every actual background; never use pink alone to communicate a discount.

### 2.2 Typography

Use **Bodoni Moda 400/500** for the masthead, department names and collection-entrance serif. Use **Inter 800/900** as the campaign grotesque and **Inter 400/500/600** for interface/body. These are proposed accessible-to-source alternatives, not identified Zara fonts. Obtain font assets from [Bodoni Moda on Google Fonts](https://fonts.google.com/specimen/Bodoni+Moda) and the [Inter project](https://rsms.me/inter/), retain applicable licenses, self-host WOFF2, and preload only the font needed above the fold. Verify the selected subset contains ₹ and all product-name characters.

| Role | Font / weight | Desktop size / line height | Mobile size / line height | Tracking / case |
| --- | --- | --- | --- | --- |
| Campaign wordmark | Bodoni Moda 500 | `clamp(96px, 18vw, 300px)` / .9 | 64–96 px / .95 | `-0.04em`; lower-right campaign placement; protect controls |
| Menu wordmark | Bodoni Moda 500 | 72–120 px / 1 | 32 / 36 px | Inset over menu columns; own boutique identity |
| Compact wordmark | Bodoni Moda 500 | 32 / 36 px when needed | 28 / 32 px | Mobile/checkout, not a centered desktop storefront bar |
| Campaign H1 / poster headline | Inter 800/900 | `clamp(64px, 9vw, 180px)` / .92–1.0 | `clamp(36px, 11vw, 64px)` / .98–1.04 | `-0.045em`; short uppercase or authored case |
| Campaign quote | Inter 800 | fluid 56–112 / 1.0 | fluid 32–48 / 1.06 | `-0.035em`; sentence case; deliberate editorial line breaks |
| Menu department / collection entrance | Bodoni Moda 400 | 28–36 / 1.12 and 36–48 / 1.08 | 26–32 / 1.12 | `-0.02em`; short labels |
| Editorial H2 | Inter 700 | 40 / 44 px | 30 / 34 px | `-0.025em`; serif only for the explicit entrance role |
| Category H1 | Inter 400 | 24 / 32 px | 20 / 28 px | `0.03em`; short uppercase allowed |
| Product title | Inter 400 | 20 / 28 px | 18 / 26 px | `0.02em`; short uppercase display, preserve source copy |
| Body/description | Inter 400 | 16 / 25 px | 16 / 25 px | normal |
| Card title / price | Inter 400 | 13 / 19 px | 13 / 19 px | short uppercase title allowed; price tabular |
| Navigation / button | Inter 500 | 12 / 16 px | 13 / 18 px | `0.08em`; short uppercase |
| Input value | Inter 400 | 16 / 24 px | 16 / 24 px | normal |
| Input label / helper | Inter 400/500 | 14 / 20 px | 14 / 20 px | sentence case |
| Caption / metadata | Inter 400 | 12 / 18 px | 12 / 18 px | `0.02em`; never essential body copy |
| Admin H1 | Inter 500 | 28 / 36 px | 24 / 32 px | normal |
| Admin table | Inter 400/500 | 14 / 20 px | 14 / 20 px | numbers tabular |

Campaign type is deliberately much heavier and tighter than the interface. Use a real supplied weight, not synthetic bold or horizontally stretched text; author line breaks separately for mobile and desktop, and permit wrapping at zoom. Keep headings as HTML, not text baked into imagery. Where the reference quote crosses photograph and white margin, use an authored solid text treatment or controlled backing with tested contrast; no blanket blend-mode effect over essential text. Use one semantic H1 per page; visual headline size is independent of heading level.

**Intentional readability adaptation (V06):** keep desktop utilities at 12/16 px, prices/card text at 13/19 px, mobile utilities at 13/18 px, body at 16/25 px and inputs at 16/24 px. Do not add a 10 px “faithful” mode or shrink text to fit the rails. Preserve the reference's quiet density through whitespace, regular weight and restrained tracking. These are chosen sizes, not asserted Zara measurements.

Do not shrink an action's hit area to its text size. Avoid light font weights for prices/forms, long uppercase paragraphs, italic functional labels, and display serif in data tables. Gallery card titles wrap to two lines with a reserved region; compact-view titles use the accessible reveal behavior in §5.2. At increased text size allow regions to grow rather than clip. Prices never truncate.

```css
/* src/styles/tokens.css — proposed starter tokens */
:root {
  --paper: #fff;
  --canvas: #f6f5f2;
  --ink: #171715;
  --muted: #62625c;
  --line: #d9d8d2;
  --control-line: #76766f;
  --disabled-bg: #efeee9;
  --sale: #b52c7a;
  --error: #a12622;
  --success: #28543d;
  --warning: #72520b;
  --focus: #2459a6;
  --scrim: rgb(0 0 0 / 0.32);
  --font-ui: 'Inter', Arial, sans-serif;
  --font-display: 'Bodoni Moda', 'Times New Roman', serif;
  --font-campaign: 'Inter', Arial, sans-serif;
  --space-1: 4px; --space-2: 8px; --space-3: 12px;
  --space-4: 16px; --space-6: 24px; --space-8: 32px;
  --space-12: 48px; --space-16: 64px; --space-24: 96px;
  --page-gutter: 16px;
  --header-height: 64px;
  --chrome-edge: 16px;
  --rail-left: 0px; --rail-right: 0px;
  --section-gap: 56px;
  --duration-fast: 140ms; --duration-base: 220ms; --duration-panel: 280ms;
  --ease-out: cubic-bezier(.2, .7, .2, 1);
  --z-header: 30; --z-sticky: 20; --z-scrim: 80; --z-dialog: 90; --z-toast: 100;
}
@media (min-width: 768px) {
  :root { --page-gutter: 32px; --section-gap: 80px; }
}
@media (min-width: 1024px) {
  :root { --page-gutter: 48px; --header-height: 88px; --section-gap: 112px; }
}
@media (min-width: 1280px) {
  .shop-shell {
    --header-height: 0px; /* corner controls overlay the storefront canvas */
    --chrome-edge: 32px;
    --rail-left: clamp(208px, 17vw, 300px);
    --rail-right: clamp(144px, 12vw, 208px);
  }
}
.checkout-shell, .admin-shell { --header-height: 64px; --rail-left: 0px; --rail-right: 0px; }
* { box-sizing: border-box; }
body { margin: 0; color: var(--ink); background: var(--paper); font: 400 16px/1.55 var(--font-ui); }
button, input, select, textarea { font: inherit; }
:focus-visible { outline: 2px solid var(--focus); outline-offset: 3px; }
.money { font-variant-numeric: tabular-nums; white-space: nowrap; }
.campaign-title { font: 900 clamp(2.25rem, 9vw, 11.25rem)/.98 var(--font-campaign); letter-spacing: -.045em; }
.campaign-quote { font: 800 clamp(2rem, 6vw, 7rem)/1.04 var(--font-campaign); letter-spacing: -.035em; }
.entrance-title { font: 400 clamp(1.75rem, 3vw, 3rem)/1.08 var(--font-display); letter-spacing: -.02em; }
.menu-link[data-kind='sale'], .menu-group-number[data-kind='sale'] { color: var(--sale); }
```

### 2.3 Geometry, breakpoints and layers

| Width | Layout specification |
| --- | --- |
| 320–767 px | 16 px gutter; 64 px compact header; View 1/2/3 all available; stacked PDP/checkout; full-width menu/sheets |
| 768–1023 px | 32 px gutter; 64 px compact header; numbered view layouts adapt to available width; stacked PDP if its panel would be <320 px |
| 1024–1279 px | 48 px gutter; 88 px compact header; expanded menu uses columns; side controls collapse into category strip/toolbar |
| ≥1280 px | Corner menu/search and fixed side utility/category areas; canvas may be full bleed; interactive catalogue captions use rail-safe stage; PDP opening uses wide split layout |
| Wide desktop | No generic 1600 px cap on hero/posters or paired PDP gallery; catalogue stage may cap at 1920 px between rails; max 1120 px checkout and 720 px prose |

Use a 4 px spacing unit; section gaps 56/80/112 px by size, with intentionally larger editorial pauses in §§4–6. Controls, swatches and image containers have 0 px radius; badges can have 2 px radius. Use 1 px rules. Shadows are limited to overlays and elevated sticky bars where a border alone is unclear.

Header z=30; sticky filter/purchase bars z=20; scrim z=80; modal z=90; toast z=100. Only one modal at a time. Dialogs created in the native top layer still obey the same intended interaction ordering. Suppress nonessential toasts while a modal has focus. Add bottom safe-area padding and reserve document space for fixed bars.

Scope the zero-height desktop storefront header to the shop shell. Checkout and admin retain their own 64 px task headers and layout offsets; do not inherit an overlay rail or zero header height merely because their viewport is wide. When a screen is too short for the category list plus View controls, move the category controls into flow. Fixed-position controls must be collision-safe in height as well as width.

## 3. Navigation and global shell — ZR-03 / ZR-04

### 3.1 Desktop corner and side controls

At ≥1280 px, follow Z02–Z14: a sparse canvas with **Menu top left**, **Search top right**, and a **right-aligned vertical utility list** beginning around the upper quarter of the viewport. This replaces the conventional horizontal department header. The two-line menu glyph becomes an X while open; its visible strokes are 48–64 px wide inside a generously sized button. Search is uppercase above a 144–192 px underline. Both use `--chrome-edge` offsets; every target remains at least 44×44 px.

Proposed utility position: right `--chrome-edge`, top `clamp(176px, 23vh, 300px)`, 44–48 px link rows: **Bag [n] / Log in (guest) or Account/verified first name / Help**. On the bag route place **Favourites** under Bag. Do not reproduce the screenshot's shopper name. Active Bag uses heavier weight; keep count visible and announced. The wordmark is a large campaign/menu element, not a permanent centered desktop navigation bar. Home is always reachable through the menu masthead and an accessible Home link.

On category pages, a left list starts at the same upper-quarter baseline: numbered **01 View all / 02 …**, then Filters and Sort. `aria-current` and weight identify the active category. **VIEW / 1 / 2 / 3** anchors near bottom left, 24–32 px above the viewport bottom. Category lists have their own max-height/scroll region ending above View, so long taxonomy does not collide with it. Footer intersection releases these controls into document flow or hides the redundant floating set, keeping footer links reachable.

Images/posters may extend behind edge controls, matching the photographic canvas. Text, form inputs, plus actions and other actionable captions stay outside rail exclusion zones. On photography, choose an explicit light/dark theme from content metadata and add a small opaque backing where needed; do not use automatic blend modes as a contrast guarantee. Reserve the right rail in purchase layouts. At zoom or widths <1280 px, switch to the compact shell before anything overlaps.

### 3.2 Full-screen navigation

Menu opens an opaque paper dialog filling the viewport, as in Z02. Close replaces Menu at top left; the boutique masthead sits over the inset content area. Desktop content begins below the masthead, roughly 18% from the left edge. Use columns: department selector (Women/Home, serif 28–36 px), numbered group titles (New In / Collections / Clothing or Textiles), category links (14–16 px sans), then a small campaign preview. Keep the right utility links inside the dialog's focus boundary. Lists scroll below the fixed Close control; no content may be cut off at the bottom.

Only **Women / Home** are departments. Women's groups contain New In, All clothing, Dresses, Tops & shirts, Trousers, Skirts, Knitwear, Outerwear and Co-ords. Home contains New In, All home textiles, Duvet covers, Duvet inserts, Bedsheets, Pillowcases, Quilts & bedspreads, Throws and Cushion covers. Use real configured collections for editorial links. A department may include a numbered Special prices group using `--sale` for both number and link; render it only against a nonempty eligible sale collection. Its label, target and semantic `kind: sale` are authored, while the application controls the colour token and eligibility. Lower utilities include Orders, Favourites, Delivery & returns, Contact, About and Bedding guide. An active department gets a dot plus programmatic selected state. Department selection updates the adjacent groups; a category link navigates and closes the dialog.

Open by click/Enter/Space; Escape/Close returns focus to Menu. Focus is trapped and the background inert. Preserve the prior page position. A preview image can change with the focused collection but must not move focus or create a hover-only destination. The full-screen menu is required in S1.3, not a future enhancement.

### 3.3 Compact/mobile shell

Below 1280 px use a stable top row: Menu left, compact boutique wordmark center, Search and Bag right; 64 px height below 1024 px and 88 px at 1024–1279 px. Account/Help/Favourites move into the menu. Full-screen menu becomes a vertical department selector followed by numbered accordion groups; Close stays top left to preserve the trigger location. Maintain 44 px targets, safe-area insets, and internal vertical scrolling.

On listings the category links become a horizontally scrollable labelled strip below the top row. Filters, Sort and View 1/2/3 use the mobile toolbar defined in §5. View controls remain real buttons with visible active state. No page-level horizontal overflow outside intentional hero/gallery/strip scrollers.

### 3.4 Search, footer and checkout shell

Search opens a full-screen paper search dialog; input at the upper portion of a centered 720 px content area, visible label, clear action, Close top right. Retain Women/Home scope and query after a recoverable error. Before typing show department shortcuts; after two characters fetch at 250 ms debounce and cancel stale requests. Show up to six linked thumbnail/title/price suggestions and View all results. A combobox is used only if its keyboard/listbox semantics are implemented; otherwise use a normal search form plus linked suggestions. Enter opens `/search`.

Footer follows the collection journey, rather than replacing the new-collection entrance. Use a centered compact first row for real boutique contact/social links when configured, then help/business/policy links and India/INR. Newsletter and external social links seen in Z09 are acknowledged reference content; a newsletter workflow is outside these sprints, so omit its control. Help links must resolve to merchant-approved content.

Checkout/admin use their task-focused shells specified in §§7–8. Checkout header contains boutique identity, Back to bag, and Help; it does not carry the floating category list or the campaign wordmark. Keep all shopping state across shell transitions.

## 4. Homepage and editorial journey — ZR-01 / ZR-02

### 4.1 Women-first horizontal department hero

**Required behavior from the user's description:** a fresh `/` opens **Women** on a photographic hero; horizontal swipe switches to **Home** and back. The switch changes the department's entire campaign sequence and new-collection destination. An explicit `?department=home`, `/home` deep link, or browser Back restoration may open Home; a stored preference must not silently replace Women on a fresh `/`.

The first section is approximately one viewport high (`100svh` for a stable initial frame), with responsive full-bleed imagery and separately chosen mobile crops. The content may be one image or a split poster like Z08. Place one large original boutique masthead in the persistent lower-right campaign overlay (§4.4), retained while the hero, video and posters scroll. It is not an element duplicated inside every poster. Constrain it to avoid faces, arrows and utility links; mobile uses the scoped adaptation in §4.4. Essential headings/links remain HTML and have readable contrast. Z07's blank still is not a required empty/loading screen: reserve the poster and draw it before decorative transitions.

Place a visible Women/Home selector along the lower-left safe region and previous/next arrow buttons at the horizontal edges around mid-height. Label arrows by destination, e.g. “Next department: Home”. With two departments, use finite navigation; disable Previous on Women and Next on Home. The persistent lower-right campaign arrow is a separate link into the active campaign, not the category switch; §4.4 defines its target changes. Keep their accessible names distinct.

Use native buttons named “Women department” and “Home department”, with `aria-pressed` reflecting the active choice; Enter/Space activates them. Give the controlled hero region a descriptive label and announce a settled swipe politely. The visible labels remain Women/Home. Arrow alternatives ensure the gesture is never the only way to switch.

Touch/trackpad horizontal swipe, arrows, and department labels all operate the same selected department. Use native horizontal scrolling with snap or a tested gesture primitive; do not intercept ordinary vertical wheel/touch scrolling or browser-edge Back gestures. Switch only on a deliberate horizontal gesture. During transition, inactive slides are removed from the tab order; announce the settled department once. Do not auto-rotate categories. Switching at the hero keeps the hero in view, updates the query state, pauses outgoing media, and preserves bag/account state. Only the active department's lower sequence is mounted for interaction; no hidden video keeps playing.

### 4.2 Vertical order: image → video → posters → collection entrance

Each department's published sequence must contain these ordered blocks:

| Block | Layout and action placement | Behavior |
| --- | --- | --- |
| 1. Image hero | Full-bleed/split campaign image, Women/Home controls; shared pinned masthead/campaign arrow | Women default; explicit horizontal department switch |
| 2. Campaign video | Large frame immediately below the hero, full-width or 70–80% centered width; Play/Pause lower left, optional mute control beside it | Actual video block required, with poster fallback; never a static-only substitute for the implemented feature |
| 3. Poster A | Full-bleed or split poster, heavy-sans campaign title and shared lower-right overlay arrow | Links to an actual department collection |
| 4. Poster B (and optional further posters) | Centered inset photograph or distinct split composition with deliberate whitespace | Own desktop/mobile crop, heading and real destination |
| 5. New-collection entrance | Large white pause; centered serif “The new” / “New collection”, Scroll down label and thin vertical line; large masthead clears | Scroll-triggered handoff to the collection URL while retaining the entrance frame; explicit cue also works |
| 6. New collection | Visually continuous live collection under its real route, with category context, products and View 1/2/3 | Same collection renderer/data as direct loads; retain scroll continuity during the handoff |
| 7. Footer | Compact contact/help/business links after the collection | Remains reachable without endless scroll |

Video is a scoped campaign element, not the first LCP resource: render a poster initially, load media only near the viewport, play muted/inline only when sufficiently visible and browser policy allows, pause offscreen/on tab hiding/on department change, and honour an explicit user pause across re-entry. Always provide a visible Play/Pause target. When autoplay is denied, show a normal Play control; do not show a broken empty frame. Reduced motion or data saving keeps the poster with an explicit Play option. Meaningful speech needs captions/transcript; the initial campaign films should be visual and muted by default. Story S1.3 implements playback; S3.2 implements editorial control of it.

Use intentional 96–160 px desktop / 48–80 px mobile pauses between selected inset posters. Full-bleed pairs can meet directly. Do not turn every block into the same padded marketing section. The user-described order governs both departments; photography changes to home textiles for Home. Each sequence has at least one real video and two posters in the launch content.

### 4.3 Scroll into a real collection route — V03

Replace the former inline-only/no-URL-change requirement. At the collection entrance, the browser address must become the active department's actual published collection URL, for example `/collections/women-new-in` or `/collections/home-new-in`. The recording changes address between 00:16 and 00:17 without replacing the visible entrance with a blank screen. Reproduce that continuity; the precise trigger/history policy below is our specification.

1. Prefetch the target collection as the final poster approaches. After genuine downward scroll brings at least 50% of the entrance into view for about 200 ms, request one soft route transition. These thresholds are proposed, not measured. Do not trigger merely because hydration, restored scroll, resizing or closing a modal makes the entrance visible. Pause automatic handoff while a dialog or field has focus.
2. A shared journey/collection layout retains the entrance at the same viewport position while committing the destination route. Mount the ready collection, update the title/canonical route and release the outgoing media/large wordmark. Preserve bag, saved state and selected department. Continue scrolling to the live `#new-collection` product region. Do not simply paint a new URL over unrelated page data or show an empty logo/loading screen.
3. Push **one** history entry per accepted handoff. Repeated intersection callbacks, wheel events and loading retries do not add entries. Before leaving, save the homepage department, entrance offset and media pause state. Browser Back restores that checkpoint and suppresses automatic re-entry until the shopper leaves the trigger region and deliberately approaches again, or activates the cue. Forward restores the collection view; direct/reloaded collection URLs render the collection normally without requiring a homepage visit. No artificial campaign prefix is required on a direct load.
4. The visible Scroll down cue is a real link to the target collection's `#new-collection` anchor, accessible name “Scroll to the new collection”. It works without JavaScript. With enhancement it uses the same single-flight handoff and then reveals/focuses the collection heading for explicit keyboard activation. Passive scrolling must not steal keyboard focus. A separate View full collection link is also valid.
5. Pending or failed route/data loads retain the entrance, ordinary scrolling and usable footer links; show inline Retry and the real collection link. Commit only the active department's latest request. Changing department or navigating elsewhere cancels stale completion. Keep the current URL until the destination can render; a genuinely empty collection displays its empty state under the correct route. Reduced motion removes fades/smooth scrolling, not the URL change.

The entrance remains roughly 55–75 `svh` of white space on desktop and 40–55 `svh` mobile, serif title 36–48 / 28–36 px, helper 12–14 px and a 120–180 px hairline beneath. A dark segment can progress along the pale line with actual entrance scroll progress; it is not a timer or fake network progress. Reduced motion uses a static line. Keep PageDown/Space, wheel and touch native; no mandatory extra wheel gesture, forced scroll lock or inaccessible footer. The reference shows footer content beneath the entrance; retain that sense of white space and usable help links during the handoff, with the complete footer reachable after the resulting collection.

### 4.4 Persistent campaign wordmark and arrow — V02

Use **one campaign overlay spanning hero + video + posters**, with a viewport-pinned appearance. Its bounding box remains stable across those sections; do not animate or remount the wordmark for each poster, and do not bake it into images. A sticky viewport layer inside the campaign-media track can provide the effect without a page-global fixed logo. The recording supports the appearance; it does not reveal Zara's CSS implementation.

Desktop proposed geometry: original wordmark in a lower-right zone, right 0–32 px and bottom around 22 `svh`, width constrained to approximately 30–36 vw (maximum 680 px). Fit the boutique's actual name without clipping; a longer name needs an authored wordmark lockup. The separate 44 px campaign-link arrow is right `--chrome-edge`, bottom 5–7 `svh`. Keep the wordmark decorative/noninteractive with `aria-hidden`; brand/Home navigation remains available through the menu. Pointer events pass through the overlay except on the arrow. Media layer z=0, decorative campaign overlay z=10, functional controls z=30, dialogs above both.

Keep the same overlay during Women/Home switching, updating content tone and campaign destination once the new department settles. A dominant-block observer may update the arrow destination to the currently displayed poster's real collection; freeze that destination while the arrow is focused/pressed, and announce a useful link name. Every block has an explicit destination and light/dark overlay tone in the manifest. A poster may use the department's default collection. Never have two overlapping arrow links.

End the large overlay at the media-track boundary, **before “THE NEW”**. Hide it while the full-screen menu/search is open; the menu has its own smaller inset masthead. It stays absent on listing/PDP/bag/checkout/admin routes. On mobile ≥390 px with adequate height, use a smaller pinned mark (64–96 px type, width ≤55vw); on narrow/short screens put it in a reserved hero caption area and omit the persistent oversized layer. Keep the campaign link reachable in flow in that adaptation. Re-evaluate fit on resize/zoom; typography and purchase controls take precedence over decorative overlap.

```css
/* The track contains only hero, video and posters; entrance follows outside it. */
.campaign-media-track { position: relative; isolation: isolate; }
.campaign-overlay {
  position: sticky; top: 0; height: 100svh; margin-bottom: -100svh;
  z-index: 10; pointer-events: none;
}
.campaign-overlay__mark {
  position: absolute; right: var(--chrome-edge); bottom: 22svh;
  width: min(36vw, 680px); max-height: 30svh;
}
.campaign-overlay__link {
  position: absolute; right: var(--chrome-edge); bottom: 6svh;
  min-width: 44px; min-height: 44px; pointer-events: auto;
}
/* Controller clears the overlay at the entrance and while a dialog is open. */
.campaign-overlay[hidden] { display: none; }
```

The snippet is structural direction; keep overlay layout space stable when hiding it, and avoid transformed/overflow-clipped ancestors that defeat the chosen sticky strategy. Test real scrolling over image/video/poster boundaries, not just individual page screenshots.

```text
CAMPAIGN MEDIA TRACK                      ONE PINNED OVERLAY
  image hero, Women ↔ Home                 large serif wordmark
  ↓ video                                 at constant screen position
  ↓ split poster                          small campaign arrow
  ↓ quote/inset poster                    heavy sans-serif headline moves with media
END TRACK → large overlay clears
                    THE NEW  (serif)
                   SCROLL DOWN
                        │
  ↓ soft handoff: URL → /collections/{department}-new-in
  ↓ live collection / View 1 2 3 / reachable footer
```

## 5. Listings and the three views — ZR-05 / ZR-06 / ZR-07

### 5.1 One catalogue, three presentation modes

**All three numbered modes are committed scope.** Numbers describe presentation modes, not “one/two/three columns”. MyShoppe's defined mapping below interprets the supplied patterns consistently; it is not a claim that every Zara category uses the same mapping.

| View | Desktop specification | Mobile/tablet adaptation | Evidence |
| --- | --- | --- | --- |
| **1 — Editorial** | Large centered single-frame stories with generous surrounding whitespace, plus deterministic shoppable look (large model/room image + two related items), paired small images followed by a large frame, or a three-frame mosaic with mixed spans. A four-panel category-poster opener is supported on curated landing/collection routes. | Centered frames become full-width in the safe stage; one large frame then its labelled product pair; mosaic reflows in reading order; category posters become 1-up horizontal cards with buttons/swipe. | Z03–Z05, Z13 |
| **2 — Gallery** | Regular large model/lifestyle product cards: four columns on a wide stage, three or two when rails reduce space. Title/price/colour chips/plus visible below. | Two columns on phones, three on tablets; price never truncates. | Z06 |
| **3 — Compact** | Six-column cutout/product-only grid on a wide stage; five/four if needed. Product sits inside a white 1:1 cell using contain; price and centered plus below. No campaign posters in this mode. | Two columns at 320–359 px, three at ≥360 px, four on tablets; minimum 96 px card width, with controls in separate rows. | Z10, Z14 |

Default curated collections to View 1, plain categories/search to View 2; honour a valid `view=1|2|3` URL parameter over the default. A stored preference is only a fallback when no explicit view exists. Changing view preserves department, filters, sort, fetched pages, product IDs and cart state. Retain the leading visible product as the viewport anchor after reflow; do not reset to page one or rearrange sales ranking. A filtered editorial mode uses deterministic product compositions without unrelated campaign inserts. Custom authored placements apply only to their compatible unfiltered/curated ordering; otherwise use the fallback editorial template over the current result order. No product is duplicated as a new SKU to create an editorial photograph.

Desktop category/filter controls and View placement follow §3.1. Product count/sort context can sit in a discreet stage heading; do not replace the side controls with the former right-aligned density toolbar. On mobile place Filters and Sort in a 48 px toolbar under the category strip, and **View 1 2 3** in a 48 px sticky bottom strip. Reserve its height plus safe area and hide it while a modal is open. Active view uses weight/underline and `aria-pressed`; tooltips/accessibility names say Editorial, Gallery, Compact.

Use bounded Load more with crawlable next-page links; after the final page show the footer. Keep enough state to restore the exact mode and product anchor on Back from a PDP. No animation should block repeated view changes, keyboard navigation, or product actions.

### 5.2 Cards, captions, plus actions and filters

Gallery clothing photos use a 2:3 portrait ratio; Home uses 4:5. Mixed-department results normalize frames to 3:4 with intentional art direction. Editorial templates have explicit role/aspect/span/focal-point fields instead of arbitrary masonry. Standard horizontal gaps are 24–40 px desktop and 8–16 px mobile; vertical gaps 56–96 px desktop and 32–48 px mobile. Compact mode uses more empty area around the cutout with a reserved cell, not a tiny cropped model photograph.

Gallery captions: short uppercase title and optional New label aligned left; price immediately below; **+** aligned to the caption's upper-right corner; square colour chips below price. Title can wrap to two lines; avoid relying on the reference's truncated text for identification. Compact cards prioritize cutout → INR price → plus; provide a descriptive accessible product link and reveal the visible title on hover/focus. Touch users can use an explicit Details action to open a preview showing title/options before purchase. At text zoom/assistive layout, show the title in flow rather than forcing an inaccessible image-only grid.

The plus is a **required quick-add trigger**, 18–20 px glyph in a 44×44 px target, sibling to the product link. It opens an anchored selector beside the card on desktop, a bottom/full-height sheet on mobile, containing product name, price, colour, size/dimensions, availability and Add. The first tap never assumes a size or buys an arbitrary variant. Confirming a valid SKU uses the same server cart mutation as the PDP. Loading, success and 409 stock/price conflicts are visible beside that selection; preserve choices on retry. Escape/Close restores focus to the original plus.

Saving from a card remains secondary to plus: provide a bookmark at the image's upper-right on hover or keyboard focus, with a 44 px target and safe backing; touch users get an explicit Save to Favourites action in the Details/quick-add sheet. On PDP and bag the bookmark is always visible beside the title. Each action exposes its current saved state and uses the same private saved-list service.

Filter drawer is a 400 px right panel on desktop/full-height mobile sheet. Apply/Clear/Close, labelled colour/size/material/price/stock inputs and zero-result recovery retain the existing catalogue semantics. Women uses apparel attributes; Home uses actual textile dimensions and pack data. Sort supports Newest, Price ascending/descending and Curated/Relevance where applicable. Filters match the same variant; presentation mode does not change the query's meaning.

### 5.3 Layout implementation direction

Use one result model and separate renderers. `EditorialResults`, `GalleryResults` and `CompactResults` receive the same product IDs and card actions; a view change changes composition only. Preserve the visible product ID before reflow and restore its position after layout without animating the whole grid. Product links and quick-add buttons are siblings, never nested interactive elements. The four-panel category opener links to categories and is distinct from the product-result set.

```css
/* Starter geometry; editorial spans and PDP have separate templates. */
.catalogue-stage {
  margin-inline: max(var(--page-gutter), var(--rail-left))
                 max(var(--page-gutter), var(--rail-right));
  padding-block: calc(var(--header-height) + 32px) 96px;
}
.product-grid { display: grid; gap: 48px 12px; }
.product-grid[data-view='2'] { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.product-grid[data-view='3'] { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.cutout-frame { aspect-ratio: 1; }
.cutout-frame img { width: 100%; height: 100%; object-fit: contain; }
.card-caption { position: relative; padding-inline-end: 44px; }
.card-quick-add { position: absolute; inset-block-start: 0; inset-inline-end: 0; }
@media (min-width: 360px) {
  .product-grid[data-view='3'] { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (min-width: 768px) {
  .product-grid { gap: 64px 24px; }
  .product-grid[data-view='2'] { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .product-grid[data-view='3'] { grid-template-columns: repeat(4, minmax(0, 1fr)); }
}
@media (min-width: 1440px) {
  .product-grid[data-view='2'] { grid-template-columns: repeat(4, minmax(0, 1fr)); }
  .product-grid[data-view='3'] { grid-template-columns: repeat(6, minmax(0, 1fr)); }
}
/* Compact price/+ are stacked; do not inherit the caption-corner placement. */
[data-view='3'] .card-caption { padding-inline-end: 0; text-align: center; }
[data-view='3'] .card-quick-add { position: static; }
```

Use container checks to reduce column count when the available stage would make Compact cards narrower than 96 px or Gallery text unusable. The sample is a starting point, not permission to squeeze controls to match a column count. Editorial templates should use CSS Grid with authored spans and DOM reading order; Home can substitute room/bed imagery for the model photographs while retaining the same interaction structure.

## 6. Product detail: purchase opening, image sequence and discovery — ZR-08–10

### 6.1 Opening composition and exact information order

Z11 governs desktop hierarchy: top whitespace/corner controls, **one large left image** and **right purchase column**, followed later by a separate broad gallery. Start the opening roughly 160–220 px below the document top on large desktop (a proposed value); reduce to 112–144 px on shorter screens. Within the safe stage use approximately 60% image / 40% information with 40–64 px gap; purchase column width 360–480 px. Leave space for right-side Bag/Account/Help. The opening uses at least 70 `svh` where practical, but content determines height. A short purchase column can stick within this opening only; it stops before the full-width gallery rather than occupying the entire page height.

Information order and actions:

1. Short uppercase title left and **bookmark/Favourite** at the far right of the same title row; price below with factual tax note if applicable.
2. Thin horizontal rule after a 24–32 px pause.
3. **Colour name | SKU**, then square swatches (20–24 px marks inside 44 px radio targets). Selected swatch has a double boundary/check state.
4. Full-width **outlined ADD** control, 48–52 px high, beneath swatches. It opens the size/dimension selector when no exact variant is selected. Desktop selector expands in place directly above Add; mobile uses a sheet. Selection summary and Change size link appear once selected; the button then adds that SKU. Publish readable “Choose size” help before selection. For a single valid one-size variant, display its exact size/pack explicitly before allowing Add.
5. Actual description **below Add**, 16/25 px, with 24–32 px top gap. For bedding, critical dimensions/pack inclusion must also be visible beside selection before commit.
6. **Complete your look / Complete your bedding set**: two to four small linked product cutouts below description, title above, generous whitespace. These are complementary items, explicitly sold separately, not other photographs of the current product.
7. Product measurements; Composition & care; Delivery & returns, as accessible expandable links/rows. A PIN delivery check sits with delivery information. Do not copy Check in-store availability unless the boutique supplies a real location-stock integration (outside this release).

Bookmark is functional: it toggles the product in Favourites with an announced saved/removed state; it does not reserve stock. Failed saves retain prior state and show recovery. Solid black buttons remain reserved for Checkout/Continue/Pay and admin commitment actions; the pictured PDP Add is deliberately outlined.

### 6.2 Continuing gallery

After the opening, render a distinct **two-column, multi-row gallery** with large front/detail/back/alternate photographs, as in Z12. Use equal column widths, 32–64 px desktop gaps, and 24–48 px outer gutters; allow the image-only canvas to extend behind safe utility backings. Row order is editorially defined and matches DOM order. Do not confine this gallery to the opening's left column or replace it with thumbnails only. Minimum launch product set: one lead image plus four continuation images; never duplicate an image merely to fill a cell. A missing/failed image preserves geometry and leaves purchase/details accessible.

On tablet retain two columns when useful; mobile uses a swipeable lead gallery with accessible arrows/counter, followed by the continuation images in a vertical sequence or paired detail crops when legible. Large desktop photos use object-fit appropriate to the authored focal point; cutouts use contain. Clicking an image opens labelled zoom with Close, previous/next, keyboard arrows and Escape. Browser/pinch zoom stays enabled.

### 6.3 Mobile purchase and selection

Mobile order: compact breadcrumb → lead image/counter → title/bookmark → price/tax → rule → colour/SKU/swatches → selection/Add → description → complementary miniatures → detail rows → continuing gallery → recommendations. Gallery initial height caps at 65 `svh` on short screens. A sticky bottom purchase bar shows price plus outlined Add while the inline action is out of view; before selection it opens Choose size. Hide it while a modal/keyboard is active and reserve its document space. Keep text accessible when the sticky bar is suppressed.

Size tiles are min 48×44 px with 8 px gaps; unavailable states are textually identified, not colour-only. Home tiles include real dimensions and pack, e.g. “Queen · 230 × 250 cm · 1 cover”. Colour changes invalidate incompatible size selections rather than silently selecting another SKU. Description/care, garment measurements, textile composition, closure and fill/TOG data are shown only when provided.

### 6.4 Three distinct related-product surfaces

| Surface | Placement / style | Data and behavior |
| --- | --- | --- |
| Complementary products | In purchase column below description (Z11), two to four miniature cutouts | Staff-curated `complements` relation; named links show title/price on focus/preview. “Complete the bedding set” lists each separately sold item. |
| Collection product navigator | Small horizontal cutout strip at the lower-right of desktop PDP, with selected-product dot (Z11); bounded to safe width | Current ordered category/collection result, not current-product image thumbnails. Real product links preserve origin filters/view/anchor; distinct accessible labels. Mobile places it in flow after detail rows so it cannot collide with Add. |
| Suggested products | Separate full-width section **after the continuing gallery**, heading top left, six-column cutout/price/plus layout on wide desktop (Z14) | `suggested` curation then deterministic same-department/category fallback; exclude current/archived items and invalid variants; use View 3 responsive sizing and quick-add. |

The first two are different from the below-gallery recommendation grid and must not be collapsed into one generic carousel. Show actual Women's/Home merchandise only. Hide an empty section instead of repeating the current product or importing fragrances/men's goods from the reference. A recommendation can be added only after variant selection. Use stable product IDs and back-link context when navigating the strip; never expose internal customer/session IDs in those URLs.

```text
Menu                                            Search ___
       LARGE LEAD IMAGE      TITLE          bookmark   Bag
                             ₹ price / tax            Account
                             ------------------       Help
                             Colour | SKU  [squares]
                             [      ADD      ]  outline
                             Description
                             Complete your look [miniatures]
                             Measurements / Care / Delivery
                                      [collection-product strip]

       LARGE PHOTO 2                 LARGE PHOTO 3
       LARGE PHOTO 4                 LARGE PHOTO 5

YOU MAY BE INTERESTED IN
  cutout    cutout    cutout    cutout    cutout    cutout
  ₹  +      ₹  +      ₹  +      ₹  +      ₹  +      ₹  +
```

## 7. Bag, checkout and order status — ZR-11

### 7.1 Full bag, Favourites and checkout bar

Z01 governs `/cart`: keep a spacious central area with vertical item cards (two to three columns desktop, one/two mobile according to usable width) instead of the old item-list/summary-sidebar split. Each card shows a contained product image, optional low-stock text, title/bookmark, exact size/colour/pack, price, quantity controls and Delete. The quantity buttons and Delete have 44 px targets and pending/conflict feedback. Sale styling is used only when actual compare-at data exists. Add a separate suggested-products section below items using the same published catalogue and quick-add behavior.

Desktop right rail shows Bag count (active), Favourites, Account and Help. Favourites opens a real saved-products route/tab with product-level bookmarks, current price/availability and Choose options; guests persist saves and login merges them once without duplication. An out-of-stock saved product stays identifiable. An archived product is labelled unavailable and cannot be added. A saved list never counts as a reservation.

The bottom **fixed white checkout bar** spans the page with a thin top boundary: total and tax/shipping qualification right aligned, then a solid black **Continue (n)** button at bottom right (280–340 px desktop, 48–52 px tall). `n` means total units consistently with bag count and its accessible label. No promotional copy competes with that action. Reserve full bar height plus safe area so recommendations/footer are reachable. Mobile stacks total above a full-width Continue action; use one checkout bar only.

Z01's “Is your order a gift?” control is acknowledged as an ancillary reference element. Gift wrapping/note fulfilment is not part of the agreed inventory/operations scope; omit that action until a real service is implemented. Do not add a dead Add gift link just to match the photograph. The required bag composition, bookmarks, recommendations, totals and Continue placement are implemented.

After a successful Add, a 440 px desktop/full-width mobile bag drawer may provide immediate confirmation, with item summary, total, View bag and Checkout. It is a supplementary interaction, not a substitute for the full bag layout. Update count only after server success; preserve selection on failure. Empty bag/Favourites show useful Women/Home links. Changed price or insufficient stock stays visible beside the affected item and blocks unsafe progression rather than silently deleting it.

### 7.2 Checkout

Max width 1120 px, 40 px top spacing on desktop/24 px mobile. Two columns: 640 px form area + 360 px summary when space allows; at <1024 px use one column. Header progress uses Contact → Delivery → Review → Payment; completed sections can be edited without clearing the rest.

Guest checkout is the default; a modest “Already have an account? Sign in” link appears above contact fields. Inputs have permanent visible labels, 48 px minimum height, 16 px text, 12 px horizontal padding. Mark optional fields explicitly. Indian address supports name, email, phone, address lines, optional landmark, city, state, and PIN. Use appropriate input modes/autocomplete and avoid guessing an address from a PIN without user review.

Primary step action sits below the active form, full width on mobile and right aligned on desktop. Back is a text link on the left. At final review label the action **Pay ₹X,XXX**; show item totals, configured tax/shipping breakdown, address, delivery option, and policy links before it. Payment methods are shown through the actual enabled provider checkout, not hard-coded promises of unavailable methods.

Desktop summary may stick at header+24 px; mobile has a collapsible summary above fields with total always visible. No extra floating Pay button while typing. Preserve input on validation/provider failure. Focus an error summary, link it to invalid fields, and show field-specific text. Pending payment locks only payment submission, not Help or order status access.

### 7.3 Status pages and customer area

| Page/state | Required visual and action behavior |
| --- | --- |
| Payment pending | Calm heading “Confirming your payment”, order reference, short explanation, status refresh, Help. Never show a green completed check or invite another payment while status is unknown. |
| Payment failed | Explain known failure without exposing provider internals; **Try again** creates/reuses a server-approved attempt; **Return to bag** secondary. Retain address and selections. |
| Confirmation | Restrained success icon, order number, item/amount/address summary, delivery estimate, **View order** primary, **Continue shopping** secondary. No confetti or false delivery promise. |
| Order detail | Timeline of confirmed states, products/options, charges, shipment links, receipt, eligible **Request return** action; plain status language and last-updated time. |
| Guest access | Order reference + email form, generic submission confirmation, clear expired-link recovery. Never render another customer's details after lookup alone. |
| Account/sign-in | Centered 440 px form; visible labels, focused recovery message, safe return destination. Orders and Addresses navigation becomes tabs on mobile. |
| Favourites | Saved-product grid with current availability, bookmark/remove and Choose options; guest and account states use the same layout; no implicit stock reservation. |
| Return request | Select eligible items/quantities, reason, review; primary **Submit request**. Submitted, approved, received, refund processing and refunded are distinct. |
| Support/help | 720 px prose width; 16/26 body; visible contact methods and accessible support form. Confirmation displays the persisted request reference. |

Customer status badges use text plus a small icon. Green denotes a confirmed completion; amber denotes pending/attention; red denotes error/action required. Do not equate an approved return with a completed refund.

## 8. Admin console

### 8.1 Shell and overview

Use the same Inter, ink/paper palette, buttons, and focus treatment with a compact, practical layout. Desktop sidebar 232 px, top bar 64 px, main padding 32 px; canvas background with white content surfaces and subtle 1 px borders. At <1024 px the sidebar becomes a labelled menu drawer; main padding 16 px. Admin is optimized for desktop work but product/stock/order actions remain usable on mobile.

Sidebar: Overview, Products, Inventory, Orders, Returns, Content, Support, Settings. Settings includes owner-only staff roles and commercial configuration. Display current location, signed-in staff identity, and sign-out. Restricted actions are omitted or explained according to permissions, but server permissions remain authoritative.

Overview: heading/date range top; four metric blocks (paid sales, refunds, net collected, order count), then two task lists for fulfilment and stock, then payment/return/job exceptions. Numbers 28/36 px with a period label and tooltip definition; avoid decorative charts without actionable meaning. Clicking a metric/task opens the corresponding filtered list. Loading uses same-sized placeholders; failed metrics show Retry, never a fabricated zero.

### 8.2 Catalogue and inventory screens

Products list: title and count left; **New product** top right. Toolbar below: search, department, status; clear filters adjacent. Table columns: thumbnail, name/SKU, department, price range, available units, status, updated time, actions. Rows 64 px minimum; image 40×48 px; name links to editor. Archive lives in row overflow and in the editor's secondary action area, separated from Save.

Editor: page title/back link left; **Save draft** secondary and **Publish / Save changes** primary top right. A sticky action bar is allowed after the original controls leave view; it must show an unsaved-changes indicator and never cover validation messages. Desktop main form 70% plus 30% publication/preview summary; mobile all sections stack. Section headings are explicit: Basic details, Description, Category, Images, Variants & price, Inventory, Product details, Search preview.

Media grid: 4 columns desktop/2 mobile, numbered order, progress/errors per asset, Edit alt and crop controls. Explicit media roles: lead/model, continuation/detail/back, cutout, swatch and editorial; select the compact-view cutout separately from the model image. Drag reordering must also expose Move earlier/Move later buttons. A failed upload remains visibly failed and retryable; Publish explains which required assets/fields are missing. Product editor also sets complementary/suggested relationships and previews the lead-plus-paired-gallery layout.

Variant table: colour, size/dimensions, SKU, price, stock, active state; horizontal scroll inside a labelled region on narrow screens, with name/SKU pinned or repeated in a card alternative. Stock editor opens an adjustment form with current on-hand/reserved/available, signed adjustment, reason, and resulting available count. Never present reserved inventory as an editable number.

Archive confirmation: product name, effect on storefront, consequence for existing orders, **Cancel** and **Archive product**. Default focus Cancel. Hard deletion is shown only for eligible drafts, with clear permanent-delete language. On stale version conflict, preserve unsaved form values and offer review/reload; do not discard staff work.

### 8.3 Orders, returns, support and content

Order table: order number, customer, created date, total, payment, fulfilment, action; status filters always distinguish payment from fulfilment. Detail: title/status top left, valid next action top right; item table, customer/shipping panel, amount breakdown, then chronological timeline. Fulfil/refund buttons show only when eligible. Tracking entry and refund amount/line selection use focused forms with clear review steps.

Refund confirmation explicitly names order, items/quantity, amount, payment method, and restock decision. **Request refund** starts processing; the button/row must not instantly claim completion. Error/unknown status includes a safe resolution action and avoids encouraging duplicate requests. Restock is a distinct physical-inspection decision.

Support list shows request reference, customer, subject, order if linked, age, and status; detail retains the customer's submitted context and staff notes. Content editor shows a block list left, selected block fields center, responsive preview right (tabs on smaller screens). Publish and revision history remain in the top action area. Preview is visibly labelled and cannot be mistaken for the public site.

**ZR-12 — required presentation controls:** edit separate Women/Home campaign manifests: image hero, video with poster/mobile source, at least two posters, collection entrance and linked collection. Validate the required sequence and ready media before publish; show upload/transcode progress, captions/alt, desktop/mobile focal points, utility-control tone and target links. Preview horizontal department switching and the entire vertical journey. Configure menu groups/preview imagery, semantic Special prices links with eligibility preview, heavy-sans headline/quote roles, per-block overlay tone/destination, View 1 template/placements, cutout assignments and product relationship ordering. Preview View 1/2/3 and PDP opening/gallery/recommendations against actual products. Publish/rollback a whole version atomically; moving a poster must not sever a live product relationship.

## 9. Component states and control placement

### 9.1 Buttons and links

| Type | Appearance | Typical placement |
| --- | --- | --- |
| Primary commitment | Ink fill, paper text, 1 px ink border, 0 radius, 48–52 px high, 24 px inline padding | Bag Continue/Checkout, checkout Pay, admin Publish |
| Outlined purchase | Paper fill, ink text, 1 px control border, full purchase-column width, 48–52 px high, 24 px inline padding | PDP ADD / Choose size and quick-add confirmation |
| Secondary | Paper fill, ink text, 1 px control border; same dimensions as primary | Save draft, View order alternative, preview |
| Text action | Underlined on hover/focus; always recognisable in body copy; 44 px hit area outside prose | Back, Remove, Clear all, size guide |
| Destructive | Error-colour text/border; filled error only inside final confirmation if needed | Archive/delete/refund confirmation, separated from ordinary save |
| Icon action | 20 px stroke glyph in 44×44 px target; accessible name; tooltip on desktop when helpful | Search, menu, Close, gallery arrows |

Hover changes colour/border subtly over 140 ms. Active darkens without moving layout. Focus uses the independent visible blue outline; never replace it with a tiny colour difference. Loading keeps width stable, includes spinner + meaningful verb (“Adding…”, “Saving…”, “Processing…”), and prevents duplicate submission. Disabled has native semantics and a nearby explanation when the reason is not obvious. A missing required selection uses a useful Choose action, not a permanently unexplained disabled control.

```css
.button {
  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  min-height: 48px; min-width: 44px; padding: 12px 24px;
  border: 1px solid var(--ink); border-radius: 0;
  color: var(--paper); background: var(--ink);
  font: 500 .8125rem/1.4 var(--font-ui); letter-spacing: .08em;
  text-transform: uppercase; cursor: pointer;
  transition: background-color var(--duration-fast), color var(--duration-fast);
}
.button:hover:not(:disabled) { background: #33332f; }
.button--secondary { color: var(--ink); background: var(--paper); border-color: var(--control-line); }
.button--secondary:hover:not(:disabled) { color: var(--ink); background: var(--canvas); }
.button:disabled { color: var(--muted); background: var(--disabled-bg); border-color: var(--line); cursor: not-allowed; }
.icon-button { min-width: 44px; min-height: 44px; padding: 10px; }
.field[aria-invalid='true'] { border-color: var(--error); }
.field-error { margin-top: 8px; color: var(--error); font-size: .875rem; }
```

### 9.2 Forms, dialogs and feedback

Fields always have visible associated labels. Help precedes error text where both exist; `aria-describedby` references the right messages. Validation occurs on blur or submission, then updates responsively after correction. Avoid showing red errors before the user interacts. Password/OTP entry supports paste and password managers. Checkboxes/radios use full-row labels with ≥44 px interactive area.

Dialog title is visible; Close stays top right and keyboard-reachable. Enter may submit a focused form but cannot silently confirm a destructive dialog. Trap focus, mark background inert, handle Escape, restore trigger focus, and preserve scrollbar geometry when locking scroll. Use the [WAI modal dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/) as behavior guidance; native semantics or tested primitives are preferred to ad hoc focus management.

Toast: desktop bottom right 24 px inset; mobile above fixed controls with 16 px inset. Maximum 360 px width, clear icon/text, dismiss control. Noncritical success can disappear after six seconds; errors requiring action stay inline until resolved. Use polite announcements for bag updates and assertive announcement only for immediate blocking errors. Never rely on a toast alone to explain checkout failure.

### 9.3 State matrix

| State | Required treatment |
| --- | --- |
| Loading | Preserve image/row/form geometry; static or gentle-opacity skeleton, label loading region; no indefinite whole-page spinner |
| Empty category/search | Plain title, useful explanation, Clear filters/category routes; keep navigation and query accessible |
| Empty admin list | Explain selected filters or first-use state; offer New product only where permitted |
| Network failure | Keep previous content/input where valid, show inline retry; distinguish unknown payment status from failure |
| Sold out | Product still viewable; exact unavailable options labelled; Add disabled for that SKU; no invented restock date |
| Partial availability | Mark affected bag line and explain permitted quantity; ask shopper to confirm changes |
| Unauthorized/expired session | Explain sign-in/permission issue, retain safe return path; do not expose private page behind a translucent overlay |
| 404/archived product | Useful unavailable-page message plus department link; never render stale Add control |
| 500/service interruption | Branded fallback, Retry/Home/Help; preserve order reference where safe; never render raw exception data |
| Offline during form use | State inability to save/submit, preserve entered values for retry; do not claim offline purchases are queued |

## 10. Motion specification

Motion explains state changes. All values here are **proposed**, except the research ledger's measured navigation transition. Use CSS transitions and the Web Animations API only where necessary. Avoid `transition: all`; animate opacity/transform rather than large layout changes.

| Interaction | Trigger and effect | Duration / easing | Reduced-motion equivalent |
| --- | --- | --- | --- |
| Navigation underline | Hover/focus, underline opacity or scale-X; no text movement | 140 ms ease-out | Instant underline |
| Department hero switch | Deliberate horizontal swipe, arrow or Women/Home label; settle selected panel, pause outgoing video | Native gesture tracking; button-driven settle 320–420 ms ease-out | Immediate panel/department change |
| Full-screen menu | Menu click/keyboard; paper surface and columns fade in with ≤8 px displacement | 220–280 ms ease-out | Immediate open with focus trap |
| View 1/2/3 | Explicit mode click; recompose around the same visible product anchor | ≤180 ms opacity; no long masonry shuffle | Immediate layout change with anchor retained |
| Collection handoff/cue | Downward entrance threshold or explicit link; one real route change retaining the entrance; no focus steal on passive scroll | Optional ≤160 ms opacity after destination readiness; explicit anchor scroll ≤400 ms | Same route change, immediate anchor placement |
| Pinned campaign wordmark | Image/video/posters scroll beneath a single stable layer; clears before entrance | No position animation; optional ≤140 ms exit fade | Same pinned position, immediate hide |
| Product secondary image | Fine-pointer hover/focus, crossfade after image decode | 180 ms ease-out | Instant swap or retain primary |
| Drawer/sheet open | Explicit action, translate from edge + scrim fade | Panel 280 ms `cubic-bezier(.2,.7,.2,1)`; scrim 180 ms | Immediate placement; no slide |
| Drawer/sheet close | Close/Escape/route transition; retain focus management until closed | 200 ms ease-out | Immediate close/focus restore |
| Accordion | Click/keyboard, small content fade; intrinsic height handled by primitive | 180–220 ms | Immediate expansion |
| Hero/editorial reveal | First intersection only, opacity 0→1 and ≤12 px translate | 400 ms, optional ≤60 ms stagger, total ≤600 ms | Visible immediately |
| Add to bag | Pending spinner, confirmed count crossfade, then bag drawer | Count 140 ms; no flying-product effect | Text status + immediate drawer |
| Form error | Validation completion, reveal text within reserved/flow space | 140 ms opacity | Immediate message; no shake |
| Image gallery | User action, native scroll/snap or crossfade | 220 ms if scripted | Native immediate navigation |
| Page navigation | Framework navigation with stable shell; optional brief content fade | ≤160 ms, never delay data interaction | Immediate content replacement |
| Admin save | Stable-width pending button followed by inline saved state | 140 ms | Immediate state text |

Content is visible before JavaScript; progressive reveal may only activate after the observer is ready. Never set essential content permanently `opacity: 0` awaiting an event. No automatic PDP carousel, parallax on product images, bouncing CTAs, fake progress bars, or looping background motion in checkout/admin.

```css
.drawer[data-state='open'] { animation: drawer-in var(--duration-panel) var(--ease-out); }
@keyframes drawer-in { from { transform: translateX(100%); opacity: .6; } to { transform: none; opacity: 1; } }
.editorial-reveal { opacity: 1; transform: none; } /* safe non-JS baseline */
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  .drawer, .editorial-reveal, .gallery, .product-card, .toast,
  .department-hero, .menu-dialog, .product-grid, .collection-entrance {
    animation: none !important; transition: none !important;
  }
  .editorial-reveal { opacity: 1 !important; transform: none !important; }
}
```

Application close/focus logic must not depend exclusively on `animationend`; reduced motion and interrupted transitions still close reliably. Preserve structural transforms used to position the selected slide; only their transition is removed. Honour reduced motion in any JavaScript animation as well as CSS. The required below-hero video stays on its poster until explicit Play for reduced motion/data saving. Pausing video never removes the posters or collection entrance.

## 11. Photography and content art direction

| Asset | Direction | Required production data |
| --- | --- | --- |
| Women hero | Confident natural pose; complete garment silhouette; uncluttered interior/exterior; no text baked into image | Desktop/mobile crop, focal point, source/rights, alt |
| Women card/PDP | Front/full look, alternate/back, detail/texture; consistent lighting per colour | Lead + ≥4 continuation images; additional cutout asset for Compact, accurate colour/fit and supplied measurements |
| Department video | Short real campaign film immediately below the image hero, Women and Home variants | Ready MP4/WebM derivative, desktop/mobile framing, poster, duration, rights, captions when meaningful audio exists |
| Home hero | Realistic made bed, warm daylight, restrained props; photograph relates to sold textiles | Mobile crop retains textile; caption distinguishes styling props |
| Bedding PDP | Lead bed/flat product + ≥4 continuation views of weave/edge/closure/contents, plus a compact product-only view | Dimensions/pack data, cover-versus-insert distinction; no implied included accessories |
| Swatch | True fabric colour or close-up texture | Text colour name; link to corresponding SKU/media |
| Editorial tiles | Coherent story within one shoot/edit | All items link to published products/collections; no out-of-scope inventory |

Avoid aggressive saturation, artificial fabric changes, inconsistent white balance, generic unrelated stock imagery, and watermarks. Use licensed assets for staging and boutique-approved photography for sale; do not imply reference-store products are this boutique's inventory. Product media must represent what arrives, particularly duvet inserts, pillowcases and multi-piece sets.

Provide widths around 360/640/960/1440/1920 px as needed, modern AVIF/WebP with fallback, explicit width/height, and correct `sizes`. Aim for roughly ≤200 KB mobile card, ≤450 KB mobile hero, and ≤700 KB desktop hero after visual quality review. Only the actual LCP image has highest priority; reserve aspect ratios to prevent shifts. Lazy-load secondary gallery/zoom assets and embed no third-party trackers in product media.

Video upload target: ≤80 MB source and ≤60 seconds; launch campaign edits ideally 12–30 seconds with a mobile derivative around ≤6 MB and desktop derivative ≤15 MB, subject to quality review. Validate type/duration/dimensions, transcode and mark ready asynchronously. Deliver poster first with `preload="none"` until near viewport; range-capable media delivery, playback rejection and failed-derivative states must be tested. These are project budgets, not measurements of Zara media.

Copy is concrete and brief: “Linen midi dress”, “Cotton percale duvet cover”, “230 × 250 cm · 1 piece”. Store names in normal case; short product titles, navigation and actions may render uppercase following Z06/Z11. Body descriptions stay sentence case. Format dates for India, and prices using `en-IN`/INR with consistent decimals (omit `.00` only when the value is a whole rupee). Do not invent composition percentages, thread counts, discounts, stock urgency, certification or dispatch promises.

## 12. Accessibility, performance and verification

Target WCAG 2.2 AA across customer and admin flows, using [WCAG 2.2](https://www.w3.org/TR/WCAG22/) as the standard. Project touch targets are **44×44 px minimum** even though WCAG 2.2's AA [target-size criterion](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html) generally specifies 24×24 CSS px with defined exceptions. This is an intentional project usability standard, not a claim that AA requires 44 px universally.

- Contrast: normal text ≥4.5:1; qualifying large text ≥3:1; meaningful control boundaries/states ≥3:1. Verify every real photograph overlay, not just the token colours.
- Use one descriptive page H1, semantic landmarks, a visible-on-focus Skip link, logical heading order, descriptive link names, and DOM order matching the screen. Decorative icons/images are hidden from assistive technology where appropriate.
- Radio groups announce colour/size, option availability and selected state. Selection does not rely only on colour. Buttons with identical visual text get enough contextual accessible naming to distinguish them.
- Sticky controls must not obscure focused elements; use scroll padding/margins matching header/bottom bars. Test 200% text zoom, 400% browser zoom/reflow where applicable, 320 px width, landscape phones, long translations/product names, and keyboard-only navigation.
- Reserve image/placeholder dimensions; self-host fonts with swap/fallback metrics; limit font families/weights. Avoid layout-changing masthead shrink, oversized JS animation bundles and eager loading of every gallery image.
- Performance targets match S3.3: field p75 LCP ≤2.5 s, INP ≤200 ms, CLS ≤0.1; prelaunch lab runs are a proxy until field data exists. See [Web Vitals](https://web.dev/articles/vitals).

### 12.1 Review and screenshot matrix

Capture deterministic screenshots using seeded products, fixed content, stable fonts, no random sale banners, and frozen animation time. Compare layout/content visibility rather than treating harmless subpixel font differences as a defect.

| Viewport/state | Required review |
| --- | --- |
| 1440×1000 desktop | Both complete homepage sequences, pinned overlay across media, collection URL handoff, corner/side controls, full-screen menu, all three product modes and six template families; PDP opening, paired continuation, complementary items, product navigator, separate suggestions; bag/Favourites/Continue; checkout, admin and content preview |
| 1920×1080 wide desktop | Image/poster canvas, four-panel opener, large campaign masthead, six-column cutouts, multi-column navigation, side-rail collisions and paired gallery composition; compare proportions with supplied 2560×1664 image files without treating image pixels as CSS pixels |
| 1279×800 and 1280×800 boundary | Compact-to-rail transition, long taxonomy, captions/plus and PDP purchase width; no clipped header or overlapping fixed controls |
| 768×1024 tablet | Compact menu, View 1 reflow, three-column Gallery/four-column Compact, PDP stacking, forms and admin drawer |
| 390×844 mobile | Women-first hero and touch switch, video/playback fallback, poster crops, scoped wordmark and collection-route handoff; menu/search; all three views; filter sheet; PDP size error, continuing gallery and sticky Add; bag/Favourites/Continue, checkout keyboard and order/return |
| 320×568 and short landscape | Header fit, View toolbar, readable two-column Compact, long title, dimension tiles, dialogs, right-sized media and no page overflow; rails move into flow when height is insufficient |
| 200% text / 400% zoom, reduced motion | No truncation or hidden content, visible focus, immediate dialog/view changes, poster until explicit Play, native vertical scrolling and reachable footer |
| Slow/broken network and stale page | Font fallback, reserved image/video poster space, autoplay rejection, failed derivative, stale price/stock, failed add/save, pending payment, failed admin save and archived recommendation target |

Validate with Playwright/axe plus manual Safari/iOS/Android and screen-reader passes; automated screenshots do not prove keyboard correctness or accessibility. New images/content get overlay-contrast and crop review before publishing.

Use capture names such as `ZR02-home-video-paused-390`, `ZR05-women-view3-1440`, `ZR09-home-gallery-1440` and `ZR11-bag-bar-390` in implementation review evidence. Compare source and implementation side by side using boutique assets. Record observed composition, intentional accessibility/responsive adaptations and pass/fail separately. Every ZR row below requires both screenshot coverage and its behavioral check; a placeholder video, inert plus or nonpersistent View toggle cannot pass on appearance alone.

### 12.2 Styling definition of done and story mapping

| Deliverable | Must satisfy | Sprint story |
| --- | --- | --- |
| Tokens/components/campaign shell | Sections 2–4 and 9–10; Women/Home switch, video/posters/scroll journey, corner controls/full-screen menu, keyboard/reduced motion | S1.3 |
| Product editor/stock/media | Validation, lead + four continuation images + cutout, video processing, template/relation fixtures, dimensions, save/archive | S1.2 |
| Listing/search/PDP | Sections 5–6; all three views/templates, exact variants, functional plus, opening/paired gallery/three discovery surfaces and failure states | S2.1 |
| Bag/Favourites/checkout/payment | Section 7; reference cards/Continue bar, persistent bookmarks/merge, explicit totals, selection errors and pending/payment states | S2.2–S2.3 |
| Admin operations | Section 8; readable metrics/tables, valid actions, distinct refund/restock status | S3.1 |
| Customer/content/help | Order access/returns/support, versioned campaign/menu/template/relationship authoring and responsive preview | S3.2 |
| Release | Sections 12–13 matrix, all ZR gates, contrast checks, gesture/media/state tests, performance evidence, actual merchant content | S3.3 |

No component is visually complete with only its ideal populated state. Its loading, empty, validation, disabled, unavailable, error, pending and success states must be implemented wherever applicable. Review the same components with long names, real INR prices, sold-out sizes, large bedding dimensions and multiple shipment/refund states before accepting the release.

## 13. Explicit reference coverage and placement register

These IDs are repeated in the sprint plan so implementation cannot treat a reference pattern as decorative inspiration only. All are required; the final gate is S3.3. Screenshot evidence establishes appearance, while user-described behavior and the specifications above establish interaction requirements.

| ID | Required visual/interaction result | Evidence / style | Build owner and acceptance evidence |
| --- | --- | --- | --- |
| ZR-01 | Women first, Home via deliberate horizontal swipe/arrows/labels, single pinned campaign masthead | User description; Z07–Z08, V01–V02; §§4.1, 4.4 | S1.3; default/deep-link/gesture/keyboard tests and both heroes |
| ZR-02 | Image → actual video → two or more posters → scroll entrance → real collection URL/live products → footer | User description; Z08–Z09, V03; §§4.2–4.3 | S1.2 media + S1.3 journey; playback lifecycle, route handoff/Back/reload/failure and real-link tests |
| ZR-03 | Menu/Search corners, right utilities, left numbered categories/filter/sort and lower-left View | Z03–Z14; §§3.1, 3.3 | S1.3 shell + S2.1 controls; viewport/height/zoom collision checks |
| ZR-04 | Opaque full-screen multi-column menu, inset masthead, serif Women/Home, numbered groups, previews | Z02; §3.2 | S1.3; keyboard focus, close/restore, real category links |
| ZR-05 | All three View modes with same results/order and persistent query/anchor/Back | Z04–Z06, Z10; §5.1 | S2.1; view-cycle screenshots plus URL/state assertions |
| ZR-06 | Four-panel opener, shoppable look, mixed-scale/mosaic, model grid and cutout grid | Z03–Z06, Z10, Z13; §§5.1–5.3 | S1.2 fixtures + S2.1 rendering; all templates populated with boutique merchandise |
| ZR-07 | Plus in correct caption position or centered under compact price; working variant selector/add | Z04, Z06, Z10, Z14; §5.2 | S2.1 + S2.2; exact-SKU add, pending/error and focus restoration |
| ZR-08 | Lead left/purchase right, exact title/price/rule/colour/outlined Add/description order, bookmark | Z11; §6.1 | S2.1 + S2.2 saved state; Women/Home selection and screenshot review |
| ZR-09 | Separate large paired continuing gallery, four distinct additional images, zoom/mobile adaptation | Z12; §§6.2–6.3 | S1.2 media + S2.1 gallery; ordered image fixtures and responsive/zoom tests |
| ZR-10 | In-panel complements, separate collection-product navigator, below-gallery suggestions; bag suggestions | Z01, Z11, Z14; §§6.4, 7.1 | S2.1–S2.2; separate populated surfaces and eligibility/quick-add checks |
| ZR-11 | Spacious bag cards, real Favourites/bookmarks, quantity/delete, fixed totals and black bottom-right Continue | Z01; §7.1 | S2.2; persistence/merge/ownership, correct totals and reachable bottom content |
| ZR-12 | Staff can author/publish/preview/roll back all above content and presentation choices | Operational requirement; §8 | S1.1–S1.2 contracts + S3.2 editor; operator authoring demo, invalid-publication tests |

### 13.1 Page and control placement matrix

| Page/state | Top-left / top-right | Side or in-flow controls | Primary action / bottom area |
| --- | --- | --- | --- |
| Desktop homepage/campaign | Menu / underlined Search | Right Bag, Log in/Account, Help; Women/Home labels and directional department arrows on hero | Pinned lower-right wordmark/campaign link across media, cleared at entrance; video Play/Pause lower-left; serif cue hands off to collection URL |
| Full-screen menu | Close replaces Menu / Search inside dialog | Inset masthead and four menu columns; right utilities inside focus boundary | Category links close/navigate; scrollable lists cannot cover Close |
| Desktop collection/category | Menu / Search | Left numbered taxonomy, Filters, Sort; right Bag/Account/Help | View 1/2/3 bottom-left; Gallery plus top-right of caption; Compact plus centered under price; bounded Load more in flow |
| Search results | Menu / Search (expanded search surface on demand) | Query/count/sort in stage; same applicable filter/view controls | Same card actions and pagination as listing |
| Desktop PDP opening | Menu / Search | Right utility rail; bookmark at title-right; colour/size selection in purchase panel | Outlined Add spans panel above description; in-panel complements; small collection-product strip bottom-right in reserved safe area |
| PDP continuation/suggestions | Menu / Search | Large two-column images; utility backing where needed | Zoom Close top-right; suggestion price/+ below cutout; collection strip hides/docks before it can cover gallery links or footer |
| Desktop bag/Favourites | Menu / Search | Right Bag/Favourites/Account/Help; bookmark, quantity and Delete within each item card | Fixed white bar: totals then black Continue bottom-right on bag; Favourites has Choose options and no checkout bar unless viewing bag |
| Mobile shop/listing | Menu left, compact identity center, Search/Bag right | Department/category strips in flow; filter/sort toolbar | View strip at bottom on listing only; no overlap with modal or keyboard |
| Mobile PDP | Same compact header | Gallery then complete information stack; collection navigator in flow | One sticky outlined Add when inline Add is outside view; suppress while selector/keyboard active |
| Mobile bag | Same compact header | Single/two-column cards as space permits, Favourites accessible through real tab/link | Total above full-width Continue, safe-area padding; final item/footer not obscured |
| Checkout | Compact brand/Home and Help in task header | Progress then active contact/delivery/review fields; summary right or above on mobile | Back below form on left; Continue/Pay below active form on right/full-width mobile; no storefront View bar |
| Account/orders/help | Compact header and contextual page title | Account links and forms in bounded readable layout | Sign in, View order, Request return or Send request below relevant content; no unrelated sticky purchase controls |
| Admin | Navigation/sidebar left; staff identity top-right | Page title and filters above table; form/preview sections in main area | Save/Publish/New product top-right action area; destructive actions separate; confirmation Cancel then explicit action |

Mobile rows specify adaptations; the supplied images only show desktop. Do not reproduce reference capture artifacts, clipped labels, inaccessible tiny targets or overlapping text. Gift wrapping, newsletter and in-store availability are acknowledged but omitted until backed by real services; all twelve rows above remain committed.

### 13.2 Recording refinement acceptance supplement

| Refinement | Required check | Story |
| --- | --- | --- |
| V01 — typography | Heavy-sans headline and quote fixtures render real 800/900 weights with authored wrapping; wordmark/departments/entrance remain serif; no clipped essential text at zoom | S1.3; content S3.2; release S3.3 |
| V02 — pinned identity | Compare overlay coordinates during hero, video and two posters at one viewport: ≤2 CSS px positional drift while active; no duplicate masthead; clears before entrance and hides for dialogs; mobile narrow/short adaptation passes | S1.3, S3.3 |
| V03 — URL transition | Passive downward entry and explicit cue each commit the correct real collection route once; retained entrance, no blank frame, correct title/data, Back/Forward, reload/deep link, reduced motion and failed-load recovery pass | S1.3; collection S2.1; S3.3 |
| V04 — sale navigation | Pink number/link only for published eligible sale collection; empty sale hides link; current/compare-at price reflects actual SKU; keyboard focus/contrast pass | S1.2 data, S1.3 menu, S2.1 results, S3.2 editor |
| V05/V06 — composition/readability | View 1 centered-frame fixture joins existing templates; View 2/3 remain four/six on wide desktop; retain chosen 12–13 px utility/price text and 44 px targets | S2.1, S3.3 |

These refine ZR-01/02/04/06/12 rather than adding another sprint or removing any of the twelve required features. Record the deliberate font-size adaptation separately from visual mismatches. No DOM inspection or browser-scale calibration was available for the supplied recording, so font family, exact pixels and internal route implementation remain project specifications.
