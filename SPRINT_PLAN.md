# Boutique commerce platform — three-sprint implementation plan

Prepared 1 October 2026. Companion specification: [STYLING_GUIDE.md](./STYLING_GUIDE.md).

**Screenshot-led revision:** the user's fourteen Zara captures and described homepage behavior replace the earlier generic storefront assumptions. Requirements ZR-01–ZR-12 below are committed across the existing nine stories. This remains a planning deliverable; these behaviors are specified for implementation, not reported as already built.

**Recording refinement:** the supplied 101.59-second recording adds requirements V01–V06 in [style §1.3](./STYLING_GUIDE.md#13-recording-evidence-and-decisions), verified in [style §13.2](./STYLING_GUIDE.md#132-recording-refinement-acceptance-supplement). Build heavy-sans campaign typography, one pinned campaign wordmark, a real collection-route transition at the entrance, sale navigation and the centered View 1 frame. Retain the deliberate readable text sizes. These refine existing stories; the plan remains three sprints × three stories.

**Implementation constraint — compact FastAPI application:** FastAPI/Python is the sole commerce backend, PostgreSQL the data store, with explicit controller → service interface → service implementation → SQL/provider adapter boundaries. Keep one modular application, a shared Python worker and reusable frontend components. Dependency growth, duplicated business logic and repetitive generated tests are release-review concerns. ZR-01–12 and V01–V06 remain mandatory; reducing code must not reduce animation, layout or interaction fidelity. §§4.1, 4.5 and 4.6 govern this refinement.

## 1. Outcome, boundaries, and working assumptions

Build a working boutique storefront with Zara-inspired editorial presentation, a PostgreSQL commerce backend, and an authenticated admin console. Customers must be able to discover products, select the exact variant, pay, receive confirmation, track an order, and request a return. Staff must be able to create, publish, update, remove, stock, fulfil, and refund products/orders without a developer.

- **Confirmed:** launch market India; currency INR; women's clothing and home textiles only.
- **Planning assumption:** one boutique owns and fulfils all inventory. “Marketplace” means a complete commerce platform in this release. Independent seller onboarding, commissions, settlements, seller-specific shipping, and seller tenancy are not included. If multiple sellers are required, re-estimate before Sprint 1; adding a `seller_id` alone does not deliver that capability.
- **Working brand:** MyShoppe, to be replaced by the boutique's name. Use original identity, photographs, and copy; reference sites provide design direction.
- **Catalogue:** Women → dresses, tops/shirts, trousers, skirts, knitwear, outerwear, co-ords. Home → duvet covers, duvet inserts, bedsheets, pillowcases, quilts/bedspreads, throws, cushion covers. No men's/kids' merchandise, beauty, furniture, or unrelated seed inventory.
- **Commercial baseline:** one fulfilment location, English, guest checkout plus optional account, domestic delivery, Razorpay hosted checkout with merchant-enabled UPI/cards, explicit shipping/serviceability rules. No COD, subscriptions, gift cards, reviews, loyalty, coupons, or automatic carrier procurement in this release.
- **Removal semantics:** archive published or previously ordered products; permanently delete only never-published drafts with no references. Historical order lines remain intact.
- **Repository state:** the workspace was empty during research. This document specifies future implementation; no application or database has been built by this planning task.

## 2. Research and design decisions

Primary visual evidence is now the supplied recording and fourteen Zara screenshots (Z01–Z14 in the styling guide). The user also explicitly described default Women, horizontal department swiping, the below-hero video/poster sequence and scroll entry into the new collection. These behaviors must be built. Earlier readable Zara/Zara Home pages and the live TOTEME walkthrough remain supplemental; direct Chrome access to Zara was blocked. Screenshot composition is observed, user-described interactions are requirements, and exact fonts/CSS measurements/timings/mobile adaptations remain specified choices. Use the [screenshot ledger](./STYLING_GUIDE.md#12-supplied-screenshot-ledger) for source-file links and evidence boundaries.

| Reference finding | Implementation consequence | Owning story |
| --- | --- | --- |
| Zara groups clothing into clear categories and editorial collections. [Zara India](https://www.zara.com/in/en/) | Only Women and Home departments; New In and curated collections are catalogue queries, not separate inventory copies. | S1.3, S2.1 |
| Zara Home exposes grid density, filters, sort, colour alternatives, and size-dependent price ranges. [Bedding](https://www.zarahome.com/us/bedroom-bedding-n945) | Responsive product grid with URL filters; exact variant price replaces the range after selection. | S2.1 |
| Its duvet detail includes gallery, material description, colours, size guide, and delivery/returns information. [Duvet detail](https://www.zarahome.com/us/cotton-percale-duvet-cover-300-thread-count-l40030088) | Home products need dimensions, pack contents, material, care, and insert/cover distinction. | S1.2, S2.1 |
| TOTEME's inspected listing pairs large product imagery with compact captions and grid controls. [Dresses and skirts](https://toteme.com/en-ap/collections/dresses-and-skirts) | Borderless cards, disciplined image ratios, restrained utility controls, and stronger mobile readability. | S1.3, S2.1 |

### 2.1 Required reference-to-build coverage

| Requirement | Concrete scope | Style section / evidence | Implementation owner |
| --- | --- | --- | --- |
| **ZR-01** | Women-first full-bleed hero; horizontal Women/Home swipe, arrows and labels; one pinned campaign masthead; heavy-sans headlines | §§4.1, 4.4 / user description, Z07–Z08, V01–V02 | S1.3; authored in S3.2 |
| **ZR-02** | Image → actual video → at least two posters → centered scroll cue → real collection URL/live products → footer | §§4.2–4.3 / user description, Z08–Z09, V03 | S1.3; media S1.2; editor S3.2 |
| **ZR-03** | Corner Menu/Search, right vertical Bag/Account/Help, left numbered category/Filters/Sort, lower-left View controls; responsive collision rules | §§3.1, 3.3 / Z03–Z14 | S1.3, S2.1; bag S2.2 |
| **ZR-04** | Full-screen, multi-column menu with large inset masthead, Women/Home, numbered groups, eligible pink Special prices link and preview imagery | §3.2 / Z02, V04 | S1.3; editor S3.2 |
| **ZR-05** | Functional View 1 Editorial / 2 Gallery / 3 Compact; preserve query, product order, anchor and Back state | §5.1 / Z04–Z06, Z10 | S2.1 |
| **ZR-06** | Centered editorial frame, four-panel category opener, shoppable look, mixed-scale/mosaic templates, regular model grid and six-column cutout presentation | §§4–5 / Z03–Z06, Z10, Z13 | Contracts S1.2; rendering S2.1; editor S3.2 |
| **ZR-07** | Card/recommendation plus triggers variant selector; actual add mutation, no implicit size | §5.2 / Z04, Z06, Z10, Z14 | S2.1 UI; S2.2 persistence |
| **ZR-08** | PDP left lead/right information; title/bookmark, price/tax, rule, colour/SKU/squares, outlined Add, description and detail links in reference order | §6.1 / Z11 | S2.1; bookmarks S2.2 |
| **ZR-09** | Separate continuing two-column/multi-row large-image PDP gallery with authored order and mobile adaptation | §§6.2–6.3 / Z12 | Media S1.2; rendering S2.1 |
| **ZR-10** | Complementary miniatures in purchase panel, collection-product navigator, separate below-gallery suggested products and bag suggestions | §6.4 / Z11, Z14; Z01 bag | Data S1.2; UI S2.1–S2.2; editor S3.2 |
| **ZR-11** | Spacious bag item cards, quantity/delete/bookmark, real Favourites, suggestions, fixed total + bottom-right black Continue | §7.1 / Z01 | S2.2; account integration S3.2 |
| **ZR-12** | Versioned admin control of campaigns/video/posters/menu/templates/media roles/relationships, with previews and rollback | §8 / content needed to operate ZR-01–11 | Schema S1.1; media S1.2; editor S3.2 |

S3.3 verifies all twelve requirements and the V01–V06 refinements against screenshot/recording evidence and behavioral tests. Keep women's clothing/home textiles only even where reference screenshots contain men's products or fragrance. Gift-service, newsletter and physical-store availability controls visible in references are explicitly acknowledged in the styling guide; omit them until real services exist. Favourites/bookmarks are now included because they are recurring product/bag controls in the supplied layouts.

## 3. Delivery shape and capacity

**Exactly three sprints, three stories per sprint.** Plan for three weeks per sprint: nine weeks total. These are large implementation stories containing work packages, not extra hidden stories.

Revised estimate: **184 engineering person-days**, up from 152 to cover the required presentation modes, media journey, related-product surfaces, Favourites and authoring/verification. To retain three three-week sprints, assume **six engineers** (two storefront, two commerce/backend, two full-stack/platform), one designer at roughly half time, one QA engineer and a boutique operator. Capacity is 270 person-days gross; reserve 54 for integration/review/defects, leaving 216 planned and 32 unallocated. Per-sprint demand is 54 / 68 / 62 days against 72 planned capacity each. This is a staffing assumption, not an instruction to hire or a delivery guarantee; with the original five engineers, extend sprint length/re-estimate instead of dropping the requested visuals. Photography/video production and merchant activation remain external dependencies. Retain this estimate for the FastAPI revision: simpler ownership reduces duplication, but Python/API contract integration still takes time. Confirm Python expertise and recalibrate using Sprint 1 throughput; do not promise fewer days by deleting required frontend behavior.

| Sprint | Story | Deliverable | Eng. days | Lead / dependencies |
| --- | --- | --- | ---: | --- |
| 1 — Real catalogue and visual foundation | S1.1 | PostgreSQL, auth, application skeleton, environments | 14 | Platform / none |
| 1 | S1.2 | Admin product/stock, image roles, campaign video pipeline, presentation data | 18 | Backend + full-stack / S1.1 contracts |
| 1 | S1.3 | Women-first campaign journey, edge controls, full-screen menu, design system | 22 | Frontend / S1.1; integrates S1.2 |
| 2 — Browse to paid order | S2.1 | Search, three views, editorial templates, PDP gallery and recommendations | 24 | Frontend + backend / S1.2–S1.3 |
| 2 | S2.2 | Reference bag, Favourites, quick-add persistence, checkout and reservations | 24 | Backend + frontend / S1.1–S1.2; integrates S2.1 |
| 2 | S2.3 | Payments, durable order lifecycle, confirmations | 20 | Backend + full-stack / S2.2 |
| 3 — Operate and launch | S3.1 | Admin overview, fulfilment, returns, refunds | 18 | Full-stack + backend / S2.3 |
| 3 | S3.2 | Customer self-service, campaign/template/recommendation authoring | 22 | Frontend + full-stack / S2.3; integrates S3.1 |
| 3 | S3.3 | Reference parity, gestures/media/state recovery, security and launch | 22 | Platform + frontend + QA / all stories |
| | **Total** | | **184** | |

Each sprint: days 1–2 confirm contracts and fixtures; days 3–10 implement vertical slices; days 11–13 integrate and exercise failure paths; days 14–15 demo, fix blockers, and release to staging. Start CI, accessibility, and security checks in Sprint 1; S3.3 verifies the integrated system. Payment merchant onboarding and real content preparation start on day 1.

Critical path: S1.1 → S1.2 → S2.2 → S2.3 → S3.1 → S3.3. Frontend work can use agreed fixtures while the corresponding service is implemented; every sprint demo must use persisted PostgreSQL data.

## 4. Architecture and implementation contracts

### 4.1 Compact stack and ownership

Use a **modular monolith**: one Python application package owns catalogue, cart, checkout, payment, orders and content. The worker imports the same services. Next.js remains the planned React storefront/admin renderer for server-rendered product pages and the recorded experience; it contains no second commerce backend. Both deployments live in one repository, without workspace orchestration tooling or independent domain microservices.

| Layer | Committed choice / reason |
| --- | --- |
| Frontend | Next.js + React + TypeScript, CSS Modules and custom properties. Public page rendering calls FastAPI; interactive components use one typed fetch helper. Keep the existing route continuity, pinned overlay, video, three views, PDP and admin scope. |
| HTTP backend | FastAPI `APIRouter` controllers; Pydantic v2 request/response models; generated OpenAPI. Built-in dependency injection composes services; no DI container library. |
| Service interfaces | Python `Protocol` contracts per feature's public use cases in `interfaces.py`. Plain service classes implement them structurally. External payment/identity/storage/email boundaries have small protocols where substitution is useful. No interface per function, data table or trivial helper. |
| Persistence | PostgreSQL, SQLAlchemy 2 **Core** table/query definitions, psycopg 3 driver, Alembic migrations. One metadata model, parameterized queries and explicit transactions. Do not add SQLModel, a second ORM or a generic repository framework. |
| Identity | Retain managed Supabase Auth for customer identity and staff MFA; FastAPI owns auth callback/login/refresh/logout controllers and cookie policy. One identity adapter verifies provider tokens and handles provider calls. No custom password/MFA implementation or frontend auth SDK stack. |
| Storage/media | Retain managed object storage/CDN; direct signed uploads through the backend's storage adapter. Pillow handles image validation/derivatives; FFmpeg is an isolated worker binary for real campaign video. No separate media service. |
| Payment/email | Razorpay hosted browser checkout; Python gateway adapter over the shared HTTPX client. One transactional email provider adapter. Never introduce parallel SDK and REST implementations for the same provider. |
| Durable work | Same Python image, separate `python -m app.worker` process; PostgreSQL inbox/outbox with bounded leases/retries. Payment/expiry/refund/email handlers call existing services. No Redis, Celery, Kafka or extra scheduler for this release. |
| Deployment | One Node rendering process, one FastAPI/Uvicorn API process, one Python worker process; API and worker share code/image. A same-origin edge routes `/api/*` directly to FastAPI and other paths to Next.js. PostgreSQL/storage are managed; staging and production are isolated. |
| Tooling/tests | Python: pytest + HTTPX/TestClient, Ruff and mypy. Frontend: TypeScript check, framework lint, Playwright + axe. Native Node test runner for the few pure frontend reducers if needed; no parallel Jest/Vitest/browser-unit stack. |

Framework references support these mechanics, not the project's exact architecture: [FastAPI routers](https://fastapi.tiangolo.com/tutorial/bigger-applications/), [FastAPI dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/), [Python Protocol](https://docs.python.org/3/library/typing.html#typing.Protocol), and [SQLAlchemy connection/transaction contexts](https://docs.sqlalchemy.org/en/20/core/connections.html). Pin compatible maintained versions at kickoff in one Python lockfile and one frontend lockfile; do not use this plan to assert unverified version numbers.

**Boundary rules:**

| Layer | Owns | Must not contain |
| --- | --- | --- |
| `controllers.py` | HTTP parsing, verified actor dependency, invoking the service interface, response serialization | SQL, totals, stock rules, provider workflows or commits |
| `interfaces.py` | Typed public use-case signatures and necessary provider ports | FastAPI, SQLAlchemy or concrete provider imports; implementation and pass-through wrapper classes |
| `service.py` | Authorization/ownership, use-case rules, state transitions, transaction scope, durable command creation | Request/Response objects, HTTP status codes, UI behavior or provider network calls while holding locks |
| `queries.py` | Explicit feature SQL accepting a supplied connection; typed query results | Opening/committing transactions, HTTP decisions or duplicated business rules |
| Provider adapters | HTTP transport, provider authentication/signatures, timeouts and response translation | Order/stock policy or access to browser state |
| Composition root | Engine/client lifecycle and binding protocols to implementations using `Depends` | Business policy or runtime service discovery |

Pydantic input/output types may also serve as service commands/results where shapes match; do not create equivalent DTO/entity/domain classes solely to satisfy a layer diagram. Separate public/admin projections when privacy or shape actually differs. Services raise a small domain-error vocabulary; one FastAPI exception mapping produces the §4.3 envelope. Internal jobs receive explicit trusted system context and the same business checks; they never forge a browser staff identity.

**Concurrency choice:** use synchronous SQLAlchemy/psycopg and normal `def` endpoints for database work. FastAPI dispatches synchronous path operations through its thread pool; plain helper calls inside `async def` are not automatically offloaded. For raw webhook streaming, use an async controller to read a bounded body, then `run_in_threadpool` for its synchronous service. Size API concurrency, worker concurrency and DB pools together; do not add an async database stack pre-emptively. See [FastAPI concurrency guidance](https://fastapi.tiangolo.com/async/). Long transcodes run as bounded worker subprocesses outside API request threads and DB transactions.

**Auth and API contract:** browser and SSR call the same FastAPI API; Next.js forwards only required cookies/request IDs for private SSR and never holds a database credential. FastAPI exchanges and refreshes provider credentials, sets Secure/HttpOnly/SameSite cookies, validates JWT signature/issuer/audience/expiry/assurance using a maintained library and cached provider keys, and reads staff membership per request. Provider auth still owns passwordless/MFA challenges. Serialize refresh-token rotation per session, enforce origin/CSRF protections, revoke/clear on logout and test expired/revoked identities. Preserve the existing opaque guest-token ownership model. Avoid a custom second token issuer or Next.js auth middleware that reimplements backend permissions.

Pydantic/OpenAPI is the canonical transport schema. Generate **TypeScript types only** with one dev-only generator (`openapi-typescript`); use a small handwritten `apiFetch` for requests, aborts and the shared error envelope. Do not generate a large client SDK or maintain matching Zod schemas. UI-required-field feedback is convenience; FastAPI validation remains authoritative. Use strict integer constraints for quantities/paise and forbid unknown command fields where silently accepting them would mask mistakes. A CI schema/type diff catches accidental drift. No endpoint-by-endpoint Next.js proxy handlers; the edge's same-origin routing avoids a duplicated backend-for-frontend layer.

```text
Browser ── same-origin edge ─┬─ Next.js: pages / React / CSS / motion
                            └─ /api/* → FastAPI controllers
Next.js SSR ── typed HTTP ────────────────────┘
                                    ↓ service interfaces
                              Python services
                               ↙            ↘
                     SQLAlchemy queries     Provider adapters
                            ↓               identity / storage / payment / email
                       PostgreSQL
                            ↑
               Python worker → same services (inbox/outbox)
```

```text
web/
  src/app/                         route composition, SSR, metadata; no commerce handlers
  src/features/{campaign,catalog,cart,checkout,account,admin}/
  src/components/ui/               button, field, dialog; shared visual primitives
  src/lib/{api.ts,api-types.d.ts}/  one fetch helper and generated contract types
  src/styles/                      tokens, globals, motion
  tests/                           focused pure-state tests and Playwright scenarios
backend/
  app/{main.py,dependencies.py,errors.py,settings.py}
  app/features/{catalog,checkout,payments,orders,content,identity}/
    controllers.py                 APIRouter transport entry points
    interfaces.py                  small public service/provider contracts
    schemas.py                     Pydantic commands/responses
    service.py                     actual use cases; split only as responsibilities grow
    queries.py                     concrete SQL; no BaseRepository hierarchy
  app/db/{engine.py,tables.py}      connection lifecycle and table metadata
  app/adapters/                    one adapter per external provider
  app/worker.py                    lease/dispatch loop; feature handlers call services
  migrations/                     Alembic; reviewed generated SQL
  tests/{unit,integration}/         shared builders, risk-focused suites
compose.yaml                       local web/API/worker/PostgreSQL
```

This is a naming convention, not a command to scaffold every empty file. Group cart/saved-list use cases with checkout until a meaningful split is needed; group support/returns with orders. Add a feature file only when it contains behavior. One Python project and one frontend package are enough.

### 4.2 Data model and invariants

Use UUID internal keys, UTC `timestamptz`, integer paise for monetary values, ISO currency codes, and explicit status enums/checks. Format displayed prices using `Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' })`. Do not use floating-point rupee arithmetic.

| Entity | Required fields / constraints |
| --- | --- |
| `profiles`, `staff_memberships` | Verified auth user reference; staff role/permissions, active flag; customers cannot write membership rows. |
| `categories`, `collections`, `collection_products` | Department enum `women/home`; category hierarchy; unique slugs; curated ordering and publication dates. |
| `products` | Department/category, unique slug, title, description, `draft/published/archived`, material/care, product type, version, published timestamp. |
| `product_variants` | Product FK; globally unique SKU; unique `(product_id, option_key)`; colour, size label, price paise, optional compare-at price, active flag, weight, version. |
| `apparel_details`, `home_details` | Typed product-specific fields. Apparel: fit, size chart. Home: textile type, composition, sold-as/pack contents, care. |
| `variant_dimensions` | Variant FK; length/width/depth in cm as applicable; fill weight/TOG only for applicable inserts; never infer dimensions from “Queen”. |
| `media_assets`, `product_media` | Storage key, MIME, dimensions, alt, focal point, rights/source, processing status, ordering, optional colour association. |
| Presentation/media extensions | Asset kind `image/video`, derivative/poster/caption references, duration, mobile source, focal point and explicit `lead/continuation/cutout/swatch/editorial` usage. Required publishable product: lead + four continuation views and a compact cutout. |
| `campaign_revisions`, `campaign_blocks`, `navigation_revisions` | Department-bound ordered hero/video/poster/collection-entry blocks; ready assets, target collection, control tone, publish/rollback revision; numbered menu groups, preview links, semantic normal/sale link kind, heavy-sans title/quote roles and per-media-block overlay tone/destination. |
| `collection_presentations`, `presentation_items` | View default, allowlisted template, ordered media/product references, span/aspect/focal point; never a duplicate SKU or arbitrary HTML layout. |
| `product_relations` | Product FK + related product FK, kind `complements/suggested`, display order; unique source/kind/target, no self-reference; published/in-scope eligibility checked at render. |
| `inventory`, `stock_movements` | One row per SKU/location: `on_hand >= reserved >= 0`; append-only movements with reason, actor, and unique operation key. |
| `carts`, `cart_items` | Opaque guest owner or user FK; unique cart/variant; positive bounded quantity; version for concurrent updates. |
| `saved_lists`, `saved_items` | Verified guest/user owner; unique list/product bookmark, optional selected colour, timestamp; never reserves stock; idempotent guest-to-account merge. |
| `checkout_attempts`, `reservations` | Owner, cart/quote fingerprint, scoped idempotency key, fixed totals, expiry, state; unique attempt/variant reservation line. |
| `orders`, `order_items` | Unique display number; immutable address, SKU, title, options, price/tax/shipping snapshots; quantities; payment and fulfilment states separated. |
| `payment_attempts`, `refunds` | Provider references unique when present; amount/currency; `pending/unknown/succeeded/failed` lifecycle; request keys and reconciliation timestamps. |
| `shipments`, `shipment_items` | Carrier label, validated tracking URL, dispatched/delivered timestamps, exact order-item quantities; cannot over-ship. |
| `return_requests`, `return_items` | Eligibility result, reason, requested/received/approved quantities, disposition, refund link; cannot over-return/refund. |
| `webhook_events`, `outbox_jobs` | Unique provider event IDs; durable payload, retries, lease, next attempt, last error, processed marker; restricted payload retention. |
| `audit_events`, `site_content`, `shipping_rules`, `tax_rules` | Actor and safe before/after values; content revisions; explicit configured serviceability, shipping and tax policies. |
| `support_requests`, `support_notes` | Unique submission key, customer contact/order scope, subject/body, status, staff notes, notification job reference; private access only. |

Selling price, stock, permissions, tax, and order totals are never authoritative in browser storage. Public catalogue DTOs omit cost price, supplier information, private media, and customer data. Protect application tables in a non-exposed schema; revoke direct `anon/authenticated` access. If an exposed table is introduced, enable and test deny-by-default RLS. Server database credentials remain server-only and use a least-privilege application role, separate from migrations.

Stock meaning: `on_hand` includes unsold physical units and reserved units; available = `on_hand - reserved`. Reserve increases `reserved`. Capture consumes a reservation by subtracting its quantity from both counters. Release subtracts only `reserved`. Returns increase `on_hand` only after staff accepts the physical item as sellable. Every counter change and corresponding movement commit together.

### 4.3 API and error contract

| Endpoint family | Required behavior |
| --- | --- |
| `GET /api/products`, `/api/search`, `/api/products/:slug` | Published only, department/category/attribute filters, deterministic pagination, explicit price range and availability DTO. |
| `GET /api/campaigns/:department`, `/api/collections/:slug/presentation` | Published versioned manifests/allowlisted templates; department-consistent media and live product references. |
| `GET /api/products/:id/related` | Complementary/suggested results with explicit slots; deterministic eligible fallbacks, no current/archived/out-of-scope products. Collection strip uses public result context, not personalization by default. |
| `POST/PATCH /api/admin/content/:id`, `/publish`, `/rollback`; `/api/admin/presentations/:id`, `/api/admin/products/:id/relations` | Content/catalogue permissions, validated asset/department/target references, expected revision conflict, audited publication and cache invalidation. |
| `POST/PATCH/DELETE /api/admin/products/:id?` | Staff permission check, server schema validation, optimistic version conflict, audit, archive policy. |
| `POST /api/admin/inventory/adjustments` | Signed quantity delta/reason; row lock; cannot reduce on-hand below reserved. |
| `GET /api/cart`, `POST/PATCH/DELETE /api/cart/items/:id?` | Owner verification, positive bounded quantity, exact variant, version conflict, server recalculation. |
| `GET /api/favourites`, `PUT/DELETE /api/favourites/:productId` | Owner-scoped saved products; idempotent set/unset state, safe guest merge, no inventory effects. |
| `POST /api/checkout/quote`, `/api/checkout/attempts` | Shipping/tax quotation; quote fingerprint; idempotent attempt and transactional reservation. |
| `POST /api/payments/session`, `/api/webhooks/razorpay` | Provider session for owned attempt; raw-body signature check; inbox deduplication. |
| `GET /api/orders/:id`, `POST /api/orders/:id/returns` | Authenticated ownership or short-lived verified guest access; never order-number-only access. |
| `POST /api/admin/orders/:id/shipments`, `/refunds` | Permission and state transition checks, quantity/amount limits, durable external commands. |

Errors: `{ error: { code, message, fieldErrors?, retryable }, requestId }`. Use 422 schema validation or unserviceable-address errors (distinct error codes), 400 malformed protocol requests, 401 unauthenticated, 403 insufficient permission, 404 missing/inaccessible resource, 409 stock/version/quote conflict, and 503 temporary dependency failure. Never return stack traces or payment secrets. Require CSRF/origin protections for cookie-authenticated mutations; bound body sizes, query lengths, page sizes, and rates.

### 4.4 Permissions, caching, and worker contracts

| Role | Allowed operations |
| --- | --- |
| Customer/guest | Public catalogue; owned cart/Favourites/checkout/order/address and return request only |
| Merchandiser | Catalogue, inventory and content edits; no customer exports, refunds or staff management |
| Fulfilment | Order/address access needed for packing, shipments, return inspection and audited restock; no pricing, refund execution or staff grants |
| Support | Order/support access, return triage and staff notes; no direct stock changes or refund execution |
| Owner | All operational permissions, refund authorization/execution, commercial settings and staff management |

Use named permissions including `orders.read`, `returns.manage`, `support.manage` alongside write permissions in code. Membership is read server-side on each request; revoking a staff membership blocks subsequent operations even when an identity token is still valid. Staff fulfilment can restock only through a validated return-inspection transition, not arbitrary stock adjustment.

Public catalogue caches have a maximum 60-second lifetime and explicit invalidation jobs after publish/archive/price changes. Cache keys include the public query/department; never cache an authenticated response or Set-Cookie response in shared storage. Cart, Favourites, checkout, order, admin and preview use private/no-store responses. Checkout reads authoritative database rows regardless of cached availability. Public product DTOs do not embed a visitor's saved state; fetch that through the private saved-list endpoint and compose it in the client.

Workers claim due jobs with `FOR UPDATE SKIP LOCKED`, commit a timed lease, then perform external work outside the transaction. Expired leases are reclaimed; retry transient errors with bounded exponential backoff and jitter; surface exhausted jobs for operator action. Duplicate execution is expected, so each business effect has a unique operation key. Payment/refund commands with an unknown external outcome enter reconciliation instead of blind retry. Limit provider concurrency; use edge limits plus a small atomic PostgreSQL rate-limit bucket for sensitive identity/checkout endpoints, not an additional cache service. Keep this table bounded with expiry cleanup. Database-generated sequences supply order display numbers; never use `count + 1`.

### 4.5 Keep code, dependencies and debugging small

The fidelity target is the supplied recording and approved styling contract, including animations and transitional states. Optimize implementation reuse, payloads and ownership. Do not replace video with a poster-only feature, remove a view/template, flatten the PDP, skip the pinned overlay or drop the route transition to hit a code-size goal. Existing explicitly documented mobile/readability adaptations remain; new visible deviations require a design decision, not an undocumented performance shortcut.

**Dependency baseline and review rule:**

- Frontend runtime starts with `next`, `react`, `react-dom` and at most one proven accessible dialog primitive if native dialog behavior is insufficient. Use native details for simple accordions, native input validation hooks, browser scroll snap, CSS transitions, IntersectionObserver and requestAnimationFrame. Do not add a carousel library, page-builder, state manager, general animation framework, form framework, utility-CSS framework or data-query framework by default.
- Backend runtime starts with FastAPI, Uvicorn, Pydantic, SQLAlchemy, psycopg, HTTPX, a maintained JWT verifier with cryptographic support, and Pillow. Alembic runs migrations from the same locked environment; FFmpeg runs only in the worker process, using the shared backend image. Reuse transitive platform facilities instead of installing duplicate HTTP, validation, logging or scheduling libraries. Use Python stdlib settings/logging/time helpers unless requirements exceed them.
- Dev tools are explicit: Python pytest/Ruff/mypy; frontend TypeScript/lint/Playwright/axe/type generation. Add pytest-cov only for diagnostic coverage measurement when useful. No Storybook, testing-library/JSDOM stack, snapshot framework or load-test dependency unless its distinct benefit is demonstrated; component states can use a small development fixture route excluded from production.
- Each new **direct** dependency needs a short decision in the eventual repository README: required capability, existing/native alternatives, maintained/security status, added client bytes or runtime cost, and owner. A library can be justified when it materially reduces accessible-interaction code or achieves a demonstrated animation requirement. This is a review rule, not a ban that forces unsafe hand-written security or focus management.
- No microservices, generic event bus, CQRS layer, plugin registry, universal repository, internal design-system package or speculative “future vendor” framework. No wrapper whose only job is forwarding identical arguments to another wrapper. Dependencies point inward without circular feature imports; background effects cross features through a real use case or the existing outbox.

**Reuse by behavior, not by page count:**

| Shared component/module | Reused by | One owner for state/rules |
| --- | --- | --- |
| `ShopShell`, `CornerControls`, `UtilityRail`, `FullScreenMenu` | Home, categories, PDP, bag | Shell owns responsive mode, modal stack and focus restoration |
| `CampaignJourney`, `CampaignOverlay`, `CampaignVideo`, entrance coordinator | Women and Home, public page and editor preview | One department/route state machine and one media lifecycle; manifests supply content |
| `ProductCard`, `ProductMedia`, `ProductPrice`, `VariantPicker`, `QuickAdd` | Three views, suggestions, complements, Favourites | One selected-SKU interaction and cart mutation; thin `Editorial/Gallery/Compact` layout renderers |
| `ProductGallery`, `ProductDetails`, relation slots | Clothing and bedding PDP | Typed apparel/textile data; same gallery/zoom controls, no copied department pages |
| `Dialog`, `Button`, `Field`, `FormErrors`, scoped table controls | Storefront, checkout, admin | Shared focus/pending/error semantics; no giant all-purpose form/page renderer |
| Catalogue/checkout/payment/order/content services | Controllers and worker jobs | One authoritative calculation/state transition; UI formats server facts |

Use URL state for shareable department/filter/view/page data; local component state or a small feature reducer for transient UI. A narrow cart/saved summary context is enough; do not copy the whole catalogue into global state. Public/admin preview uses the same campaign/product renderers with draft DTOs. Use discriminated props for real variants; split responsibilities before a component becomes a collection of unrelated boolean switches. Extract a helper when repeated behavior has settled; do not create dozens of single-use abstractions to reduce line count.

**Performance/debugging budget:** server-render catalogue, lazy-load admin/zoom/provider checkout, load only the active campaign video, cancel stale requests and share decoded media. No React state update on every scroll pixel; sample geometry in one requestAnimationFrame coordinator or IntersectionObserver. Measure before memoizing. One API error mapper and one fetch error translator expose the same `requestId`; propagate request/checkout/job IDs through structured Python logs and browser error reports. Log state transitions and SQL timings without tokens/PII. Emit worker heartbeat/old-job metrics from the same worker; use hosting logs/alerts first, add a tracing SDK only for a diagnosed visibility gap.

The PR template reports: capability changed; reused component/service; new dependencies; handwritten source/test growth; request/client-bundle impact; owning risk checks. Generated types/migrations are reported separately. Investigate files above roughly 400 lines, repeated state logic, and unusually large diffs; these are review triggers, not instructions to split cohesive code into fragments. Track client JS gzip per route against the Sprint 1 baseline; >10% or >20 KB growth on a main shopping route needs explanation and measurement. No invented total-line cap and no minification as an architectural shortcut.

### 4.6 Testing that earns its maintenance cost

**Rule: test distinct failure modes at the lowest layer that can prove them.** Acceptance criteria describe behaviors, not a command to create a test file/function for every bullet. Give each risk below one primary automated suite; add another layer only for a different failure mode, such as HTTP ownership wiring versus a transaction race. Do not assert the same price arithmetic through unit, mocked service, controller and five browser flows.

| Risk ID / owner | Primary verification | Representative cases; avoid the full cross-product |
| --- | --- | --- |
| T01 — S1.1 | FastAPI + real DB permission/ownership matrix | Anonymous/customer/staff/MFA/revoked identity and object ownership; generated route inventory ensures no protected mutation is omitted. Cases identify a distinct permission boundary, not arbitrary user names. |
| T02 — S1.2 | Real DB catalogue integration + one operator browser journey | Clothing and bedding publication, missing media/pack, stale edit, archive/history; invalid scalar input boundaries parameterized once. |
| T03 — S1.3 | Browser state/motion suite, a few pure coordinator tests | Women/Home, video pause/re-entry, pinned overlay exit, route handoff/Back/cancel/failure; keyboard/reduced motion. Test transitions, not React internals. |
| T04 — S2.1 | PostgreSQL query integration + discovery browser journey | Same-SKU filter, stable paging/order, private-product exclusion; one multi-variant apparel and one dimension/pack textile fixture. View/template composition and anchor restoration stay in browser. |
| T05 — S2.2 | Real DB bag/saved-list integration | Owned persistence, version conflict, merge/retry once, invalid/archived SKU, no reservation on save/add; reuse one identity fixture family. |
| T06 — S2.2 | Unit money/quote boundaries; independent-connection DB race tests | Paise rounding/quote changes; last-unit contention, all-or-none reservation, key/payload conflict, expiry/capture race and worker recovery. No SQLite or mocked locks. |
| T07 — S2.3 | HTTP ingress + real DB transitions + provider adapter contract | Raw signature/mapping failure; duplicate/out-of-order capture, unknown result, late capture/refund hold. One hosted-checkout staging smoke; browser never re-proves every payment state. |
| T08 — S3.1 | Real DB operational transitions + one operator lifecycle browser journey | Partial shipment/return, concurrent refund limit, unknown refunds count against balance, once-only inspected restock, permission limits. |
| T09 — S3.2 | Content/auth integration + authoring browser journey | Manifest order/media/target rejection, revision rollback, signed guest-order access, return ownership, sale eligibility. Shared renderer visual checks are reused. |
| T10 — S1.3/S2.1/S3.3 | Playwright layouts + manual recorded-motion comparison | ZR/V coverage matrix, all six template families, three views, PDP and bag. One representative per distinct layout/state, not every product or category at every viewport. |
| T11 — S1.1/S3.3 | Contract/build checks + adapter staging checks | OpenAPI/types drift, empty-DB Alembic upgrade, controller/service import direction; exercise real auth/storage/payment/email adapters in staging before release. |
| T12 — S3.3 | Load/restore/operator drills | Existing latency/invariant goals, backup restore/payment reconciliation, payment outage, alerts and pause/rollback. Keep expensive drills outside every local edit. |

**Small, explicit test set:** initial planning envelope is roughly 25–40 pytest functions grouping 60–100 distinct backend cases, 8–12 short browser journeys, and 20–30 named visual checkpoints. These are review estimates, not quotas or coverage ceilings. Security-route enumeration may legitimately add cases; every additional case must name its uncovered boundary, defect or risk. Never delete a unique money/security/concurrency test to fit a count. Avoid multiplying all products × colours × sizes × departments × viewports × browsers; use equivalence partitions and pairwise combinations for presentation, while covering all critical state transitions.

Parameterize real boundaries with meaningful IDs, as supported by [pytest parametrization](https://docs.pytest.org/en/stable/how-to/parametrize.html). One table for invalid quantities `0, -1, fractional, over-limit` is enough; do not add tests for twenty negative integers. Do not write tests that restate constants, schema field lists, trivial getters/setters, mocks calling mocks, framework behavior or private implementation methods. Do not snapshot entire DTOs/DOM trees when a few observable invariants suffice. Use unit tests for pure branching logic, not every service method.

**Harness and fixtures:** reuse small named builders (`apparel`, `bedding`, `last_unit`, `paid_order`, `campaign`) with explicit inputs; keep the 40-product visual seed and 10k-product performance dataset out of ordinary backend tests. Each integration test gets isolated committed data and cleanup; race tests use real separate PostgreSQL connections and a barrier, not a single connection wrapped in a rollback fixture. Replace only external provider transports/clock using dependency injection, not internal repositories. Reuse HTTPX's mock transport for provider errors; staging contract checks catch assumptions doubles cannot prove. Inject `now` into expiry services so tests advance time without sleeps. Browser fixtures seed through a local setup command or test harness, never a production test endpoint.

**Browser/visual fidelity:** keep separate short journeys for campaign, discovery/PDP, bag/saved merge, purchase/status, operator fulfil/refund and content publication; build shared setup helpers, not one 100-step test whose first failure hides the rest. Use role/label locators and stable product IDs, retrying assertions and recorded traces on failure. Follow [Playwright's observable-behavior/isolation guidance](https://playwright.dev/docs/best-practices). Layout screenshots may freeze animation and use seeded media. **Motion checks must run actual transitions:** sample pinned coordinates across real scroll, verify video time advances/pauses, compare transition start/middle/settled frames and check route/URL timing, reduced motion, focus and cancellation. A static screenshot cannot approve an animation. Retain desktop/mobile recordings alongside the supplied reference for manual side-by-side review; exact source font/timing uncertainties remain labelled in the style guide.

**CI lanes and failure policy:**

| Lane | Runs | Provisional wall-time budget on a documented fixed runner |
| --- | --- | --- |
| Local focused | Changed pure/service tests, lint/type checks as relevant | Feedback <60 seconds for focused tests |
| Every PR | Lint/types/build/OpenAPI diff, full compact Python suite on PostgreSQL, primary Chromium desktop+mobile journeys, affected visual states, axe on those same states | ≤10 minutes, parallel jobs; measure cold install/build separately |
| Main/nightly | Firefox/WebKit critical smoke, broader visual/viewport matrix, provider staging contracts when credentials available | ≤20 minutes excluding external outage investigation |
| Release | Physical iOS/Android and screen reader pass, full reference/motion review, load/restore/merchant purchase-refund and operator drill | Explicit scheduled run; reuse collected evidence from the same candidate |

No browser/viewport Cartesian product in every PR. Route/layout changes expand the affected visual set; shared shell changes run all shell checkpoints. Re-run a passed suite only after relevant code/config/fixture changes or new evidence. CI may capture a single diagnostic retry/trace, but a retry-only pass is flaky and does not silently satisfy a release gate. Fix it; any temporary quarantine needs an owner, short expiry and alternate evidence, and never covers a stock/payment/authorization gate. Keep benchmarks separate from ordinary tests to avoid noisy timing failures.

**AI-builder test review:** before adding a test, search existing scenarios and list the risk ID, distinct boundary and why the existing suite cannot catch it. Extend the closest parameter table when appropriate. Review test diffs for copied assertions/fixtures and unnecessary permutations; consolidate duplicates in the same PR. Measure unique risks covered, runtime, flake rate and fault detection, not raw test count or a universal 100% coverage target. A regression gets one minimal reproducer at the owning layer. Once per critical invariant, deliberately remove the stock guard/signature/ownership check in an isolated test branch and verify its owning test fails; avoid a permanent mutation-testing platform unless evidence justifies it.

Code excerpts below define implementation direction. They omit imports and repository adapters where indicated; they are not a drop-in finished application. Their invariants and acceptance criteria are mandatory.

## 5. Sprint 1 — Real catalogue and visual foundation

### S1.1 — Establish PostgreSQL, identity, and deployable application

**Story:** As the boutique owner, I need a reliable, access-controlled foundation so product and order data survive deployments and only authorized staff can administer the shop.

**Scope / implementation:**

1. Scaffold only needed frontend and Python feature files; configure strict TypeScript, Ruff/mypy, lint/build checks, local PostgreSQL and reproducible web/API/worker setup. Add OpenAPI type generation and the controller/interface/service boundary from §4.1. Define environment validation; commit an example env file with placeholders only.
2. Implement Alembic migrations for identity, catalogue, inventory, audit, job foundations and the ZR-12 campaign/presentation/media-role/product-relation/saved-list contracts. Add FK/check/unique constraints; seed roles and Women/Home departments idempotently. Version content separately from stock/price records.
3. Implement the FastAPI identity adapter/controllers for managed Supabase Auth, verified cookies, serialized refresh, CSRF/origin protections, invite-only staff, current role lookup on every protected operation, MFA on admin sessions, logout and expiry. Next.js forwards required cookies for SSR; it does not duplicate auth/permission rules. Bootstrap the first owner through an audited operator command, never a public signup flag.
4. Deploy staging web, FastAPI API and shared Python worker; readiness verifies DB connectivity, liveness does not depend on third parties. Add structured request IDs, secret redaction, migration job, and initial backup configuration.

**Code direction — authorization inside the service boundary:**

```python
# features/catalog/interfaces.py — no HTTP or persistence imports
from typing import Protocol

class CatalogCommands(Protocol):
    def publish(self, actor: Actor, product_id: UUID,
                command: PublishInput) -> ProductView: ...

# features/catalog/controllers.py — transport only; imports abbreviated
router = APIRouter(prefix="/api/admin/products")

@router.post("/{product_id}/publish", response_model=ProductView)
def publish_product(
    product_id: UUID,
    command: PublishInput,
    actor: Annotated[Actor, Depends(current_actor)],
    service: Annotated[CatalogCommands, Depends(get_catalog)],
) -> ProductView:
    return service.publish(actor, product_id, command)

# dependencies.py — composition root; process-lifetime dependencies from lifespan
def get_catalog(request: Request) -> CatalogCommands:
    return request.app.state.catalog_service  # CatalogService(engine, ...)

# schemas.py defines PublishInput.expected_version and ProductView once.
# current_actor verifies identity; service checks current permission/ownership.
# main.py maps domain exceptions to one HTTP error envelope.
```

**Verification ownership (T01/T11):** One parameterized direct-API permission matrix owns anonymous/customer/inactive/wrong-role/MFA failures; enumerate protected routes to catch omissions. Verify a denied direct service call too. PostgreSQL migration/seed checks and OpenAPI/type drift run in CI. Add no duplicate browser permission matrix.

**Acceptance criteria:**

- [ ] Controllers contain no SQL or commerce rules; services authorize use cases independently of HTTP; generated frontend types match OpenAPI. Web contains no DB credentials, business-rule backend or per-endpoint proxy layer.

- [ ] A clean clone can provision the local DB, migrate, seed, and start the app using documented commands; re-running seed does not duplicate records.
- [ ] CI builds and applies migrations against an empty PostgreSQL instance; a second migration run makes no changes.
- [ ] Anonymous, customer, inactive staff, and staff without the required permission cannot call an admin API directly. Staff MFA is enforced on server mutations.
- [ ] Draft catalogue data, admin data, and private assets are inaccessible using public Supabase credentials.
- [ ] Staging restarts preserve seeded records; web/API/worker health and failed-job diagnostics are visible without leaking secrets.

**Exit strategy:** Demo an invited staff login, a rejected customer mutation, and a persisted record after redeploy. Attach passing migration/auth integration results and staging URL. S1.1 exits only when those gates pass. If deployment fails, roll back the web and API/worker images while retaining compatible additive schema; keep admin behind its flag. No public release depends on an unverified migration.

### S1.2 — Admin catalogue, variants, media, and stock

**Story:** As a merchandiser, I can add, edit, publish, remove, and stock women's clothing and home textiles so the storefront reflects actual sellable inventory.

**Scope / implementation:**

1. Build `/admin/products` with search, department/status filters, pagination, New product top right, row actions, and explicit archive confirmation. Build create/edit pages with identity, description, taxonomy, variants/prices, media, stock, SEO, and preview sections.
2. Model apparel sizes separately from bedding dimensions. Generate variant combinations deliberately, allow removing invalid combinations, and prevent duplicate SKUs/options. Bedding must distinguish cover versus insert, pack count, dimensions, composition, and care.
3. Implement authenticated signed image uploads (10 MB source limit), MIME/signature checks, pixel limits, re-encoding/metadata stripping, alt, focal points, reorder controls, failures and unused-upload cleanup. Add explicit lead/continuation/cutout/swatch/editorial roles for ZR-06/ZR-09. Add separate video ingestion (≤80 MB, ≤60 seconds), MIME/duration/dimension validation, async transcode/derivatives/poster/captions and ready/failed status; budgets are in the styling guide. Publish only ready media.
4. Implement draft/publish/archive and allowed draft deletion; archival hides public catalogue and blocks new cart/checkout use. Existing reserved checkout attempts may finish until expiry unless staff performs an explicit audited withdrawal/refund workflow.
5. Add stock adjustment ledger, reason, reorder threshold, optimistic product versions, and audit trail. Do not expose a freely editable stock total that overwrites concurrent reservations.
6. Seed 24 women's products and 16 home products with original demo copy, realistic INR prices, varied sizes/colours, one lead plus four continuation images and a separate compact cutout per published product, one sold-out SKU and one low-stock SKU. Record image/video rights; reference-store screenshots are design evidence, not sale inventory assets.
7. Seed both departments' complete hero → video → two posters → collection-entry manifests, full-screen menu groups, a centered editorial frame, four-panel category opener, shoppable look and mosaic presentation fixtures, plus complementary/suggested product relations. Templates reference canonical product IDs. Add one valid markdown-price fixture and its sale collection plus an empty-sale fixture; reject compare-at prices that are nonpositive or not above the selling price when claiming a reduction. S3.2 adds full authoring; S1.3 must already render real database-backed manifests.

**Code direction — publish gate and inventory constraints:**

```python
# features/catalog/service.py — called by HTTP and authorized internal callers.
# Queries receive this connection; none opens or commits another transaction.
class CatalogService:
    def __init__(self, engine):
        self.engine = engine

    def publish(self, actor, product_id, command):
        with self.engine.begin() as conn:
            require_permission(conn, actor, "catalog.write")  # active staff + MFA
            product = queries.lock_product(conn, product_id)
            if product.version != command.expected_version:
                raise Conflict("STALE_VERSION")
            variants = queries.variants(conn, product_id)
            media = queries.ready_media(conn, product_id)
            assert_publishable(product, variants, media)
            # Valid attributes/prices/rights, lead + four views + cutout required.
            result = queries.publish(conn, product_id, product.version + 1)
            audit.append(conn, actor, "product.published", product_id)
            outbox.enqueue_unique(
                conn, f"catalog:{product_id}:{result.version}",
                "catalog.invalidate", {"product_id": str(product_id)},
            )
            return ProductView.model_validate(result)
# Exceptions roll back; successful context exit commits update/audit/job together.
```

```sql
ALTER TABLE inventory
  ADD CONSTRAINT inventory_valid CHECK (
    on_hand >= 0 AND reserved >= 0 AND reserved <= on_hand
  );
CREATE UNIQUE INDEX variant_sku_unique ON product_variants (sku);
CREATE UNIQUE INDEX variant_options_unique
  ON product_variants (product_id, option_key);
```

**Verification ownership (T02/T09):** PostgreSQL integration owns catalogue constraints, archive/version/stock races and publish validation; parameter tables cover distinct apparel/bedding/media boundaries. One operator browser journey proves create → publish → edit → archive and field errors, reusing the same controls for both departments.

**Acceptance criteria:**

- [ ] Admin forms and previews reuse shared field/media/product components; product/audit/outbox writes commit atomically through the Python service. No generic CRUD framework or duplicate form-schema library is introduced.

- [ ] Staff create a dress and duvet cover, upload/reorder images, create sizes/colours, publish, edit, and archive entirely through the UI; changes survive reload.
- [ ] API rejects unsupported departments, duplicate SKU/options, negative price/stock, missing dimensions/pack information for bedding, and invalid media.
- [ ] Publishing requires valid title/slug/category/variants/attributes and ready lead + four continuation views + a cutout, with alt/rights/role metadata. A product may remain published while sold out.
- [ ] Archive disappears from list/search/collections within 60 seconds and blocks new checkout immediately; old order snapshots remain readable. Unsafe hard deletion is rejected.
- [ ] Two simultaneous staff edits produce one success and one 409; inventory adjustments never erase reservations and always record actor/reason.
- [ ] All 40 seed products belong to Women/Home; no placeholder links or broken images in the staging catalogue.
- [ ] **ZR-02/06/09/10/12:** each department has a ready real video/poster sequence; fixtures exercise every required template/gallery/related-product surface. Invalid media, self-recommendations and cross-department campaign links fail validation; processing retries survive worker restart.

**Exit strategy:** A merchandiser completes the dress/duvet workflow with lead, four continuation images and cutout unassisted; demonstrate ready video derivatives and persisted campaign/template/relation fixtures. Export the audit trail and show corresponding PostgreSQL rows. Roll back a bad content change using its prior revision; archive problematic merchandise while preserving orders. Failed media processing keeps a draft unpublished and presents a retry. CSV import is the first optional enhancement to defer, not basic admin CRUD.

### S1.3 — Campaign homepage, edge controls, and full-screen navigation

**Story:** As a shopper, I enter on Women, switch horizontally to Home, follow each campaign through video and posters into its new collection, and navigate using the supplied Zara layout patterns.

**Scope / implementation:**

1. Implement tokens and shared accessible controls from the revised styling guide, including Inter 800/900 campaign headlines/quotes, serif wordmark/departments/entrance, `--sale` and retained 12–13 px utility/price sizing. Build `CornerControls`, `UtilityRail`, `CategoryRail`, `FullScreenMenu`, `DepartmentHero`, `CampaignVideo`, `CampaignPoster`, `CollectionEntrance` and `CampaignSequence`. Use the compact responsive shell below the rail breakpoint.
2. **ZR-01:** fresh `/` defaults Women; explicit department deep links/Back are honoured. Support horizontal swipe/trackpad, labelled arrows and Women/Home controls using one state model. Keep vertical scrolling native, pause outgoing media, preserve bag/session, and update safe URL state after a settled switch. No timed auto-rotation or blank logo interstitial. Add one pinned `CampaignOverlay` spanning hero/video/posters; stable desktop coordinates, dynamic tone/destination, pointer-safe arrow, no per-poster duplicate, hidden before the entrance and during menu/search. Implement the narrow/short-screen adaptation in style §4.4.
3. **ZR-02 / V03:** render database-authored image hero → actual video → at least two posters → centered scroll cue → real collection route/live products → footer for both departments. Implement the style §4.3 single-flight handoff: prefetch, deliberate downward entrance threshold, ready destination, one history entry, retained entrance geometry, title/canonical update and no blank frame. The explicit cue is a real collection anchor link. Back restores the homepage checkpoint without immediately redirecting; Forward/reload/deep links work. Preserve the entrance and original URL on failure; reject stale completions after department/navigation changes. Video supports muted inline playback, explicit Play/Pause, viewport/tab lifecycle, autoplay rejection, reduced motion/data-saving posters and failed-media fallback.
4. **ZR-03/04:** fixed desktop corner Menu/Search, right vertical utilities, left numbered category area and full-screen multi-column menu with an inset wordmark/preview imagery. Implement collision-safe rails, legible overlays, focus trapping/restore, keyboard/touch and mobile reflow. Menu is full screen now, not a later expansion of a narrow drawer. Guest rail label is Log in. Special prices uses the sale token on its link and group number only when real eligible markdown inventory exists; ordinary prices and CTAs retain their specified colours.
5. Build `/women`, `/home`, `/collections/[slug]`, category shell, basic title search and read-only product detail from real PostgreSQL data. The initial collection destination uses a shared simple renderer and the retained entrance transition; S2.1 supplies all three views/templates. Cart/Favourites mutation controls stay behind their feature flags until S2.2, with real auth routes from S1.1. Expose only available help content.

**Code direction — one department state drives the complete campaign sequence:**

```tsx
// Client component receives published manifests from its server page.
type Department = 'women' | 'home';
function CampaignExperience({ initialDepartment, manifests }: CampaignProps) {
  const [department, setDepartment] = useState<Department>(initialDepartment);
  function selectDepartment(next: Department) {
    if (next === department) return;
    const url = new URL(window.location.href);
    url.searchParams.set('department', next);
    window.history.replaceState(window.history.state, '', url);
    setDepartment(next);
  }
  return (
    <>
      <CampaignMediaTrack>
        <CampaignOverlay department={department} />
        <DepartmentHero value={department} onSettled={selectDepartment}
          heroes={{ women: manifests.women.hero, home: manifests.home.hero }} />
        <CampaignSequence key={department} manifest={manifests[department]} />
      </CampaignMediaTrack>
      <CollectionEntrance department={department} />
    </>
  );
}
// Server page: absent/invalid department => women; explicit home => home.
// Sequence renders only active video/posters; entrance is outside the media track.
// Loader projects published blocks into hero/media/entrance props.
// Overlay is shared and cleared before the entrance; it does not remount per poster.
// Video cleanup pauses playback; popstate/deep links restore department/section.
// Keep explicit pause preferences keyed by asset above the remounted sequence.
// Hero gestures and arrow/label clicks all call the same settled-state handler.
```

Additional controller direction for the shared-layout route adapter (implement these adapters; they are not framework APIs):

```ts
async function enterCollection(source: 'scroll' | 'explicit') {
  // canStart checks active department, trigger eligibility, restoration suppression
  // and a single in-flight request. Explicit activation can retry or override suppression.
  if (!handoff.canStart(source)) return;
  const attempt = handoff.begin(); // generation ID + AbortSignal
  const checkpoint = journey.capture(); // department, URL, scroll, pause preferences
  try {
    const destination = await collections.prepare(checkpoint.collectionHref, {
      signal: attempt.signal,
    });
    if (!handoff.isCurrent(attempt)) return;
    await navigation.commitCollection({
      destination, checkpoint, signal: attempt.signal,
      history: 'push-once', preserveEntrancePosition: true,
      focusCollectionHeading: source === 'explicit',
    });
    handoff.complete(attempt);
  } catch (error) {
    if (handoff.isCurrent(attempt) && !attempt.signal.aborted) {
      handoff.fail(attempt, error); // retain entrance/URL, expose Retry + real link
    }
  }
}
// commitCollection owns route/data/title/history consistency and commits atomically
// from the user's perspective after readiness; cancel on department/navigation change.
// Popstate restoration suppresses scroll entry until exit/re-entry or explicit action.
// Keep modified-click/new-tab behavior of the actual <a href> unchanged.
```

**Verification ownership (T03/T10):** Build campaign state/history tests and real-motion browser checkpoints now. Test the transition coordinator in isolation only for branches awkward to drive through the browser; do not duplicate every state transition at both layers. Record measured positions/playback/URL alongside screenshots.

**Acceptance criteria:**

- [ ] One CampaignJourney renderer and overlay/media lifecycle serve Women, Home and later admin previews. Native CSS/browser APIs reproduce the pinned mark, media sequence, gestures and route continuity without a default animation/carousel library.

- [ ] **ZR-01:** fresh `/` opens Women; swipe/arrow/label moves to Home and back, with correct lower content and collection target. Explicit Home URL and browser Back restore Home; vertical gestures still scroll and no offscreen video plays.
- [ ] **ZR-02 / V03:** both sequences contain a real playable video and two posters. Passive entry and cue Enter/click transition to the correct real collection URL once while retaining the entrance, then expose published products. Back/Forward, refresh/direct load, slow/failed request, cancellation, reduced motion and no-JavaScript link paths pass. No repeated history entries, focus theft, blank transition or automatic re-entry after Back.
- [ ] **ZR-03:** screenshots at 1440/1920 px match the corner/side-control arrangement; 390/768 px use the compact adaptation; 320 px/zoom has no overlap or inaccessible action. Long categories scroll independently above View's reserved area.
- [ ] **V01/V02/V06:** headline/quote use heavy sans while mark/departments/entrance use serif; pinned wordmark drifts ≤2 CSS px across media boundaries at a fixed viewport, clears at entrance and hides for dialogs. Chosen readable utility/price sizes and narrow-screen adaptation pass.
- [ ] **V04:** Special prices link/group use `--sale` only against qualifying published merchandise; empty/invalid markdown collections never show a misleading sale link.
- [ ] **ZR-04:** full-screen menu has Women/Home, numbered groups, real links and campaign preview; Escape/Close restores trigger focus, hidden background is inert, and no men's/fragrance departments leak into the boutique.
- [ ] Reduced motion shows content immediately; blocked autoplay exposes Play; video/image/network failures keep the rest of the campaign and collection accessible. User pause is respected across re-entry.
- [ ] Initial HTML includes the active campaign and collection links; axe has no serious/critical failures in hero, menu, video-controls and scroll-entry states.

**Exit strategy:** Demo both complete department journeys, pinned overlay, collection URL/Back handoff, conditional sale link, keyboard menu and blocked-video fallback; attach viewport screenshots and video/gesture tests. Runtime poster fallback is valid for playback restrictions, but an unimplemented video or department switch does not pass. An incident may roll back a campaign revision while preserving navigation/catalogue; ZR-01–04 remain open if their required behavior is missing.

**Sprint 1 exit:** Staff maintain a real catalogue and media pipeline; both departments render the complete swipeable hero/video/posters/collection-route journey and full-screen navigation from persisted fixtures. Checkout remains disabled until Sprint 2 gates pass.

## 6. Sprint 2 — Browse to paid order

### S2.1 — Three product views, search, and complete product pages

**Story:** As a shopper, I can find suitable clothing or bedding and understand exactly which size, colour, material, and pack I am buying.

**Scope / implementation:**

1. Implement `/search`, `/women/[category]`, `/home/[category]`, `/collections/[slug]`, and `/products/[slug]`. Search title/category/material with PostgreSQL full-text search, a GIN index and a small synonym dictionary. Bound page sizes and use stable sort plus ID tie-breakers. Women filters include size/colour/material; Home filters include textile type/dimensions/bed label/pack. Size AND colour AND availability must match the same variant.
2. **ZR-05:** implement all three presentation modes: **1 Editorial, 2 Gallery, 3 Compact**. These numbers are modes, not column counts. Persist `view`, query, filters, sort and page in the URL. All modes consume the same eligible ordered product IDs. Preserve the first visible product anchor, loaded-page context and Back position when switching modes or returning from PDP; a view switch never resets to page 1. Provide readable 44 px controls in the lower-left desktop rail and compact mobile toolbar.
3. **ZR-06:** build and seed each required presentation: centered single-frame editorial story; four-panel category opener; large look with two linked cutouts; mixed-scale/mosaic editorial rows; regular model grid; dense product cutouts. Templates use allowlisted spans and product/media references. In editorial mode, decorate the eligible result sequence without silently reordering, hiding or duplicating products; a shoppable-look group is eligible only when its products occur in the current ordered set. Filtered/sorted results fall back to editorial tiles when a group no longer fits. Never reintroduce excluded products through a campaign block. View 2 uses 4/3/2 columns wide desktop/tablet/phone; View 3 uses 6/4/3 (2 below 360 px); View 1 uses authored compositions with a readable mobile stack.
4. **ZR-07:** card plus opens a labelled quick-add sheet with colour, actual size/dimensions/pack, price and unavailable states. Confirming calls the same S2.2 cart mutation as PDP. Prevent implicit first-size selection, optimistic false success and stale selection after colour changes. Search suggestions debounce 250 ms and cancel stale responses. Filter sheets have Apply/Clear/count; empty/error states keep inputs editable.
5. **ZR-08/09:** PDP opening follows Z11: large left lead, right title/bookmark, price/tax, rule, colour/SKU/square swatches, outlined Add, description, complementary miniatures, detail links. Add opens selection when needed. Critical bedding dimensions, pack and insert distinction are visible before commitment. Then render a separate two-column, multi-row continuation gallery from at least four additional images (Z12), not thumbnails confined beside the lead. Implement zoom, mobile gallery and safe sticky Add as specified in style §6.
6. **ZR-10:** implement three distinct surfaces: staff-curated complementary miniatures inside the purchase panel; small collection-product navigator with current-product marker and origin context; separate suggested-products grid below the continuing gallery. Suggestions use deterministic eligible fallback and quick-add. The navigator links to other products, not images of this product. Exclude archived/draft/out-of-scope merchandise and self-recommendation. Required seeded fixtures populate all surfaces; genuinely empty live relations hide cleanly.
7. Integrate corner/side navigation without text or controls colliding with photographs, captions, filters or Add. Match style §13 placement matrix; use the compact shell before rails overlap. Implement loading, unavailable image, sold-out, no-results and request-failure states.

**Code direction — explicit variant selection, with no implicit size:**

```ts
type Variant = {
  id: string; colour: string; sizeKey: string;
  pricePaise: number; available: number; active: boolean;
};
export function resolveSelection(
  variants: Variant[], colour?: string, sizeKey?: string,
) {
  const selected = colour && sizeKey
    ? variants.find(v => v.colour === colour && v.sizeKey === sizeKey && v.active)
    : undefined;
  return {
    selected,
    canAdd: Boolean(selected && selected.available > 0),
    message: !sizeKey ? 'Choose a size' : !selected
      ? 'This combination is unavailable' : selected.available < 1
      ? 'Sold out' : null,
  };
}
// This is a UI projection of generated API types, not a parallel transport schema.
// Python cart/checkout services authoritatively recheck availability and ownership.
// For bedding, sizeKey identifies actual stored dimensions and pack configuration.
```

**Verification ownership (T04/T10):** PostgreSQL cases own search eligibility/filter semantics; one focused browser discovery journey owns view/anchor/URL/variant interaction. Reuse ProductCard/Media/VariantPicker/QuickAdd in all views and recommendations; verify distinct layout states through selected checkpoints, not repeated purchase journeys.

**Acceptance criteria:**

- [ ] All three modes consume the same API results and shared product primitives. Layout templates remain explicit; no copied card implementations, independent quick-add rules or redundant frontend validation schema.

- [ ] Same-variant filtering passes a black-medium dress fixture; search finds “linen dress”, “duvet cover”, and “pillowcase” with no draft, archived or out-of-scope results. Sale collections include only published variants with valid current/compare-at reduction; choosing a nonsale variant never inherits a misleading sale price.
- [ ] **ZR-05:** View 1→2→3→1 preserves ordered product IDs, filters/sort/page, bag state and first visible product anchor. Copy/reload/Back restore the selected mode and position. Each control has an accessible name and selected state; invalid query values normalize predictably.
- [ ] **ZR-06:** approved fixtures demonstrate all six compositions at desktop and mobile sizes. Filter/sort changes never let editorial blocks add excluded products or change the result order. All products remain reachable in every mode; no duplicate product cards or invented cutout imagery.
- [ ] **ZR-07/08:** plus and outlined Add open the correct variant selector; colour changes invalidate incompatible size. Exact SKU price, stock and imagery update; selection/failed-add errors are announced and never increment the bag count falsely. Product bookmark integrates with S2.2.
- [ ] **ZR-08/09:** Women and Home PDPs follow the specified purchase order and show one lead plus four distinct continuation images in a separate paired gallery. Home clearly shows cm dimensions, contents, cover/insert distinction and care; Women shows measurements/fit. Zoom, gallery, detail links and mobile sticky Add work by keyboard/touch.
- [ ] **ZR-10:** the three separate PDP discovery surfaces are visible with populated fixtures, link to the right products, preserve origin context and use eligible Women/Home merchandise only. Removing a related product never creates a dead Add action; empty states remain usable.
- [ ] At 1440 px, 768 px, 390 px, 320 px and zoomed layouts, rails, view controls, product captions and purchase actions remain reachable without overlap. Loading, failed image/search, no-results and sold-out states pass review.

**Exit strategy:** Demo a complete Women and bedding journey through all three views, every editorial template, quick-add, PDP lead/continuation gallery and all related-product surfaces. Attach query/state tests plus the ZR-05–10 comparison screenshots. All required modes and surfaces must be implemented before this story exits. A regression may trigger runtime rollback to the last working revision; disabling a required mode or replacing the gallery with a standard grid leaves its acceptance gate open. Misleading price, pack or variant always blocks release.

### S2.2 — Reference bag, Favourites, checkout, and atomic reservations

**Story:** As a shopper, I can keep a bag across visits, see the full delivered price, and check out without losing stock to a simultaneous purchase.

**Scope / implementation:**

1. Implement the Z01 full `/cart` layout: spacious vertical item cards, contained imagery, title/bookmark, exact options, price, quantity/Delete, below-item suggestions and fixed white checkout bar with total then black bottom-right Continue (total units). Reserve bar space/safe area and adapt to a full-width mobile action. A bag drawer is supplemental; it cannot replace this page. Back all bag operations with PostgreSQL. Guest identity uses a random opaque token whose hash is stored server-side; Secure/HttpOnly/SameSite cookie. Adding to bag does not reserve stock. On login, transactionally merge owned carts by SKU, report quantity/availability conflicts, and rotate guest ownership.
2. Build guest-first checkout: contact, Indian address/PIN, delivery option, review, payment hand-off. Persist draft state; validate serviceability using boutique-owned rules. Recompute prices, shipping, tax breakdown, and order total on the server. Merchant supplies actual tax and shipping configuration before live launch; this plan does not prescribe tax rates.
3. Build quote fingerprint/version and explicit re-acceptance when prices, address, delivery, or tax change. Default quote lifetime 10 minutes and reservation lifetime 15 minutes, configurable separately; no silent extensions on page refresh.
4. Create one active checkout attempt per cart version/owner. Unique scoped idempotency key plus canonical request hash means a repeated request returns the same attempt; reuse with different input returns 409.
5. In a short database transaction, lock the cart/attempt and affected catalogue/stock rows in a consistent order, revalidate publication/price, reserve all lines or none, and create immutable pending order snapshots. Use a conditional stock update per sorted SKU. Implement bounded retries for serialization/deadlock errors only.
6. Build reservation expiry worker now. Payment completion and expiry lock the same attempt/order then stock rows in the same order. Transitions are conditional and ledger keys unique. Enforce per-cart quantity limits and per-owner active reservation caps to reduce stock hoarding.
7. **ZR-11:** build `/favourites` plus product/bookmark actions. PostgreSQL saves belong to the verified guest/user; use unique list/product keys and idempotent set-union login merge. A repeated merge never duplicates saves or re-adds removed entries from an already-consumed guest list. Guest saves persist 30 days; authenticated saves persist until removal. Rotate/consume guest ownership in the merge transaction. Show current price and available options; retain an unavailable label for saved archived products without exposing private draft data. Saving never reserves stock. All quick-add surfaces reuse the same authorized cart service; recommendation eligibility is checked again at mutation.

**Code direction — reservation kernel, inside the attempt transaction:**

```python
from sqlalchemy import text

def reserve_lines(conn, attempt_id, lines):
    # Called INSIDE CheckoutService's engine.begin() after ownership, quote,
    # attempt idempotency and sellability checks. No standalone commit here.
    merged = aggregate_by_variant(lines)  # integer quantities, total per SKU 1..10
    for line in sorted(merged, key=lambda item: str(item.variant_id)):
        variant_id = conn.execute(text("""
            UPDATE inventory
               SET reserved = reserved + :qty, version = version + 1
             WHERE variant_id = :sku AND on_hand - reserved >= :qty
             RETURNING variant_id
        """), {"sku": line.variant_id, "qty": line.quantity}).scalar_one_or_none()
        if variant_id is None:
            raise InsufficientStock(line.variant_id)
        queries.insert_reservation(conn, attempt_id, variant_id, line.quantity)
        ledger.append(
            conn, operation_key=f"reserve:{attempt_id}:{variant_id}",
            variant_id=variant_id, reserved_delta=line.quantity, on_hand_delta=0,
        )
    # Exception escapes the service transaction: all lines roll back together.
```

PostgreSQL row locking provides the concurrency primitive; use consistent lock ordering and short transactions. See [PostgreSQL explicit locking](https://www.postgresql.org/docs/current/explicit-locking.html) and [SQLAlchemy transaction contexts](https://docs.sqlalchemy.org/en/20/core/connections.html). The surrounding checkout protocol is an application design, not a database feature.

**Verification ownership (T05/T06):** Pure Python table tests own totals; PostgreSQL tests own ownership, idempotency, merge and independent-connection stock/expiry races. One short bag-to-reservation browser journey covers UI integration. The twenty contenders are one concurrency scenario, not twenty near-identical tests.

**Acceptance criteria:**

- [ ] Every cart/checkout entry point calls the same Python use cases. Worker expiry reuses the state-transition/ledger code; no Node implementation or in-memory stock lock exists.

- [ ] Guest bag persists for 30 days; login merge does not lose items or duplicate quantities; separate users cannot read or mutate each other's cart.
- [ ] **ZR-11:** desktop/mobile snapshots match the central item-card layout, right-side Favourites link, suggestions and bottom-right Continue. Count means total units everywhere. Footer, recommendations and focused controls remain clear of the bar, including on short screens and with the keyboard open.
- [ ] Favourites/bookmarks work on cards/PDP/bag, persist guest visits, merge exactly once into account saves and cannot be read/mutated by another owner. Repeated save/delete is idempotent; unavailable products cannot be added. Saves never change stock or reservation counters.
- [ ] Plus on listings/PDP recommendations/bag suggestions and PDP Add all persist the exact selected SKU once; pending/failure preserves input and recoverable state.
- [ ] UI and server reject zero, negative, fractional, excessive, archived, and invalid SKU inputs. Bag shows changed prices/stock clearly before payment.
- [ ] Quote totals equal the sum of immutable line totals plus configured charges, using integer paise; changing address or shipping invalidates the old quote.
- [ ] With stock = 1, 20 concurrent attempts for the same SKU produce exactly one active reservation and no negative stock. Multi-line failure leaves every line unreserved.
- [ ] Ten concurrent retries using the same idempotency key create one attempt, one order, and one reservation set. A different payload with that key yields 409.
- [ ] Expiry releases each reservation once within two minutes of its deadline; restart/retry does not double-release. Capture-versus-expiry race has one valid terminal transition.
- [ ] Browser refresh, worker restart, and a stale cart tab do not corrupt totals or extend reservations. Tests use real PostgreSQL transactions.

**Exit strategy:** Demonstrate the screenshot-led bag and Continue placement, guest/account Favourites merge, every quick-add entry point, and competing checkouts for the last unit with a mixed clothing/bedding bag. Attach visual, ownership, concurrency and expiry results. Missing Favourites or bag composition keeps ZR-11 open. If reservation correctness fails, keep payment initiation off and allow browsing/bag only; do not replace the inventory guard with a client stock check. Abandoned attempts expire via the worker even during a web rollback.

### S2.3 — Payment integration and durable order confirmation

**Story:** As a shopper, I can pay securely and receive a trustworthy order result, even when I close the tab or a notification is retried.

**Scope / implementation:**

1. Define `PaymentGateway` protocol with `create_order`, `fetch_payment`, `fetch_order_payments`, and `refund`; implement one HTTPX adapter. Create provider orders from stored attempt totals in INR; bind returned provider order ID to the local attempt before presenting checkout. Never trust browser amounts or provider IDs without ownership/mapping checks.
2. Provider creation happens outside inventory transactions. Persist a command before sending it. A timeout after an external request is `unknown`, not automatically failed: reconcile by recorded reference/provider evidence before retrying. Do not assume Razorpay order creation supports an idempotency key unless its selected API explicitly documents it.
3. Integrate hosted checkout. Verify callback signatures server-side, then show Pending until capture is confirmed by a verified webhook or server API fetch. Closing the payment UI, a failed individual attempt, or a client redirect must not mark the whole order paid/failed incorrectly.
4. Verify webhooks against the raw body and secret; durably insert an inbox event before acknowledging. Worker cross-checks provider order, payment, amount, currency, and capture status against snapshots. Deduplicate both events and business effects using unique payment/order transitions.
5. Capture under an active reservation consumes stock once, marks payment paid, and queues order email. Late capture after reservation release never blindly takes stock: mark `paid_needs_resolution`, block fulfilment, and enqueue an idempotent full refund plus an admin alert. A second capture against an already-paid order is reconciled/refunded, never fulfilled twice.
6. Reconcile pending/unknown payments every minute with bounded retries and backoff; alert on unresolved items over five minutes. Send transactional confirmation through an outbox with a stable deduplication key; email failure does not roll back a paid order. Add receipt/order detail and pending/failed/retry pages.

**Code direction — verified, durable webhook ingress:**

```python
# payments/controllers.py — bound streaming avoids reading an unbounded body.
@router.post("/api/webhooks/razorpay", status_code=200)
async def razorpay_webhook(
    request: Request,
    service: Annotated[PaymentIngress, Depends(get_payment_ingress)],
):
    raw = bytearray()
    async for chunk in request.stream():
        if len(raw) + len(chunk) > 256_000:
            raise HTTPException(status_code=413, detail="BODY_TOO_LARGE")
        raw.extend(chunk)
    await run_in_threadpool(
        service.ingest, bytes(raw),
        request.headers.get("x-razorpay-signature", ""),
        request.headers.get("x-razorpay-event-id", ""),
    )
    return Response(status_code=200)

# adapters/razorpay.py — stdlib HMAC; secret injected, never browser supplied.
def verify_webhook(raw: bytes, signature: str, secret: bytes) -> None:
    expected = hmac.new(secret, raw, hashlib.sha256).hexdigest()
    if not re.fullmatch(r"[a-fA-F0-9]{64}", signature):
        raise InvalidSignature()
    if not hmac.compare_digest(expected, signature.lower()):
        raise InvalidSignature()

# payments/service.py — method on service, represented as a function excerpt.
def ingest(self, raw: bytes, signature: str, event_id: str) -> None:
    self.gateway.verify_webhook(raw, signature)
    if not event_id:
        raise InvalidEvent("MISSING_EVENT_ID")
    payload = parse_supported_webhook(raw)
    with self.engine.begin() as conn:
        queries.insert_or_confirm_duplicate(
            conn, provider="razorpay", event_id=event_id,
            body_hash=hashlib.sha256(raw).hexdigest(), payload=payload,
        )  # unique provider/event ID; changed body under same ID is a conflict
# Commit BEFORE 200; DB failure produces retryable error. Worker applies effects.
# Configure edge body/time limits too; invalid signature maps centrally to 401.
```

Razorpay documents raw-body signature validation, duplicate event identification, and potentially out-of-order delivery in [webhook validation guidance](https://razorpay.com/docs/webhooks/validate-test/). Follow its [Standard Checkout integration](https://razorpay.com/docs/payments/payment-gateway/web-integration/standard/integration-steps/) for provider order creation and verification. The inbox, reservation, and reconciliation logic here must be implemented separately.

Durable work uses the shared PostgreSQL worker, not request-lifetime tasks; see [FastAPI background-task guidance](https://fastapi.tiangolo.com/tutorial/background-tasks/).

**Required state transitions:**

| Domain | Transitions / guard |
| --- | --- |
| Checkout | `reserved → completed / expired / cancelled`; only one terminal transition |
| Payment | `pending → paid / failed / paid_needs_resolution`; a confirmed capture is not overwritten by an older failed event |
| Refund | `requested → processing / unknown → succeeded / failed`; reconcile unknown before another external request |
| Fulfilment | `unfulfilled → partially_shipped → shipped → delivered`; paid, non-held quantities only |

**Verification ownership (T07/T11):** HTTP-plus-PostgreSQL tests own raw signature/inbox behavior and state transitions; HTTPX transport doubles model timeout/unknown/duplicate/out-of-order provider outcomes. One hosted test-mode purchase validates the real adapter. Do not replay every provider event in a browser test.

**Acceptance criteria:**

- [ ] Only the gateway adapter speaks provider HTTP; checkout and worker share the payment services. Inbox acknowledgement follows commit; delayed processing never relies on FastAPI in-process BackgroundTasks.

- [ ] Test-mode clothing and bedding purchases complete via supported hosted payment methods; browser receives no secret or raw card/UPI credential storage.
- [ ] Forged webhook, mismatched amount/currency/provider order, unauthenticated session creation, and foreign checkout access are rejected.
- [ ] Replaying the same event 20 times and delivering distinct capture/order-paid events out of order produces one paid order, one stock consumption, and one logical confirmation job.
- [ ] Browser closes before the callback: webhook/reconciliation still completes the order; reopening shows its server status. Client “success” alone cannot do so.
- [ ] Provider timeout, worker crash after inbox insertion, and duplicate refund requests are recoverable without duplicate fulfilment or uncontrolled external retries.
- [ ] Late capture after expiry follows the refund/hold path; automated tests prove it cannot oversell. Failed/abandoned checkout retains a useful retry route with a fresh quote when required.
- [ ] Confirmation shows order number, exact items/options, charge breakdown, delivery address/estimate, and support link; email sends from an authenticated test domain.

**Exit strategy:** Demo a successful test payment, abandoned browser recovery, replayed notification, and late-capture refund/hold. Keep `checkout_enabled=false` for production until merchant activation and launch gates pass. During a payment incident disable new sessions while leaving webhooks, reconciliation, refunds, and order access running. Never roll back by deleting paid orders.

**Sprint 2 exit:** A customer can use all three product views and editorial templates, the full PDP gallery/discovery surfaces, Favourites and reference bag, then select → checkout → pay in staging and see a durable order. All stock/idempotency/security gates must pass before Sprint 3 operational validation.

## 7. Sprint 3 — Operate and launch

### S3.1 — Admin overview, fulfilment, returns, and refunds

**Story:** As a boutique operator, I can see what needs attention and complete the daily order cycle with traceable actions.

**Scope / implementation:**

1. `/admin` shows paid sales, successful refunds, net collected, order count, unfulfilled orders, low-stock SKUs, pending returns, payment exceptions, and failed jobs. Use Asia/Kolkata date boundaries for reports while storing UTC timestamps. Define each metric in a tooltip; pending/failed payments never count as sales.
2. Implement searchable/filterable order tables and detail timelines, safe customer/address display, downloadable packing slips and configured invoice/receipt output. Invoice fields/numbering and tax breakdown require merchant-provided settings; do not label incomplete documents tax invoices.
3. Staff can allocate shipment quantities, enter carrier/tracking, mark dispatched/delivered, and notify customers. Manual tracking entry is the implemented v1 workflow; automatic labels and carrier callbacks are a future adapter. Validate HTTPS tracking hosts and escape customer-provided data.
4. Handle pre-dispatch cancellation and per-line returns: approve/reject with reason, record receipt, inspect, choose restock/quarantine, and request full/partial refunds up to remaining captured amount. Define merchandise/tax/shipping refund allocation from original snapshots using integer rounding; never recompute using current prices.
5. Guard every transition under locks. Shipment/refund/cancellation races cannot allocate the same units inconsistently. A refund's pending/unknown amount counts against the refundable balance. External request uncertainty is reconciled before another refund command is sent.
6. Provide audit history, staff role management for owner only, and actionable low-stock/payment/job exception lists. CSV export escapes formula-leading values and records export actor/date.

**Code direction — request a refund through a durable command:**

```python
# OrdersService method; dependencies/query result types omitted for brevity.
def request_refund(self, actor, command):
    with self.engine.begin() as conn:
        require_permission(conn, actor, "refunds.write")
        order = queries.lock_order(conn, command.order_id)
        prior = queries.refund_by_key(conn, order.id, command.request_key)
        if prior:
            return assert_same_refund_request(prior, command)
        allocation = validate_refund_allocation(conn, order, command)
        # Per-line quantities; successful AND pending/unknown amounts reserved.
        if allocation.amount_paise > queries.refundable_balance(conn, order.id):
            raise Conflict("REFUND_EXCEEDS_BALANCE")
        refund = queries.create_refund(conn, order, allocation, command.request_key)
        outbox.enqueue_unique(
            conn, f"refund:{refund.id}", "payment.refund",
            {"refund_id": str(refund.id)},
        )
        audit.append(conn, actor, "refund.requested", refund.id)
        return refund  # requested, not falsely labelled refunded
# Worker calls provider outside DB locks; unknown response is reconciled first.
```

**Verification ownership (T08/T01):** PostgreSQL integration owns quantity/balance/race guards; extend the existing permission table for operation roles. One operator lifecycle journey owns shipment → return → refund UI. Test unknown external results via the existing adapter harness, not a second mock framework.

**Acceptance criteria:**

- [ ] Dashboard/order actions use shared fields/dialogs/tables and the existing Python services; refund, restock and shipment state rules have one owner and one audit path.

- [ ] Dashboard fixture totals equal underlying captured/refunded amounts for an explicit date range; cancelled unpaid orders do not inflate sales.
- [ ] Staff find a paid order, create a shipment, enter tracking, and deliver it through UI; customer timeline and transactional notification reflect each transition.
- [ ] Unpaid/held orders cannot ship; over-shipment, over-return, duplicate restock, and over-refund are rejected transactionally.
- [ ] Full cancellation and partial return/refund scenarios work, including refund failure/unknown state; a second click/retry does not create an extra external refund.
- [ ] Stock returns only after a sellable receipt decision. Non-sellable returns remain quarantined and do not change available stock.
- [ ] Merchandiser cannot refund, fulfilment staff cannot manage roles, and only owner can grant privileges. Audit history records actor/reason/state changes.
- [ ] Operator resolves one payment exception and one failed notification from a documented queue without changing rows manually.

**Exit strategy:** Run a daily-operations rehearsal: new order → partial shipment → delivery → partial return → refund → stock reconciliation. Attach reconciliation totals and audit evidence. Disable the affected admin action if a transition is unsafe; preserve read access and queue pending work. Manual provider intervention must be recorded and reconciled, not used to bypass amount/stock guards.

### S3.2 — Customer self-service and boutique content publishing

**Story:** As a customer, I can retrieve my order and request help; as the boutique editor, I can keep the storefront current without code changes.

**Scope / implementation:**

1. Complete account sign-in/out, verified email flow, saved addresses, order list/detail, S2.2 Favourites integration, and links to tracking, downloadable receipts, and return requests. Support already-built guest checkout without forcing account creation.
2. Guest order lookup takes order reference + email, returns a generic response, and sends a short-lived single-use link to the stored email. Store only its token hash; exchange it for a scoped session, strip it from the URL, and disable referrer leakage/third-party analytics on that exchange page. Never disclose an address using order reference/email alone.
3. Build return request UI against S3.1 eligibility and remaining quantities; show policy, reason, outcome, status, and support contact. Do not promise automatic approval or a refund until the server confirms it.
4. **ZR-12:** build `/admin/content` for separate Women/Home manifests requiring image hero → video → at least two posters → collection entrance. Edit ready video/poster/mobile derivatives, playback fallback, captions when relevant, focal points, control tone and live collection targets. Allow full/split/inset poster treatment. Preview the horizontal department switch and whole vertical journey at desktop/mobile widths; draft/publish/rollback complete revisions atomically. Sanitize rich text and allow only internal storefront CTA paths; use server-resolved collection/product IDs where possible.
5. Add editors for numbered menu groups, semantic sale links/eligibility preview and small previews; headline/quote roles, mobile line breaks, overlay tone/destination; View 1 template/placements (centered single frame, four-panel category opener, shoppable look, mixed-scale/mosaic), default view, cutout/media roles and complementary/suggested relationship order. Preview all three views plus PDP opening/continuation/related surfaces against real catalogue data. Validate department scope, published targets and required asset roles before publish; invalid edits keep the live revision intact. Publication/archive emits durable cache invalidation; request-time eligibility still filters archives before cached relations render.
6. Publish About, Contact, Delivery, Returns, Size guide, Bedding guide, Privacy, and Terms pages using boutique-supplied text and service details. Provide a persisted, rate-limited support request form and transactional acknowledgement; route staff responses through the boutique's support process.
7. Add unique title/meta/OG, canonical URLs, sitemap of public published pages, Product/Breadcrumb structured data from current facts, and noindex on account/admin/checkout/search/filter combinations. Keep base category URLs indexable. Enable only necessary analytics; optional measurement follows the configured consent choice. Newsletter subscription and gift services remain outside scope; omit those inactive controls. Favourites/bookmarks are committed features with real persistence.

**Code direction — safe, versioned editorial block contract:**

```python
from typing import Annotated, Literal, Self, Union
from uuid import UUID
from pydantic import BaseModel, Field, model_validator

class Overlay(BaseModel):
    tone: Literal["light", "dark"]
    collection_id: UUID

class Hero(BaseModel):
    type: Literal["hero"]
    image_id: UUID
    mobile_image_id: UUID
    overlay: Overlay

class Video(BaseModel):
    type: Literal["video"]
    video_id: UUID
    poster_id: UUID
    mobile_video_id: UUID
    caption_asset_id: UUID | None = None
    overlay: Overlay

class Poster(BaseModel):
    type: Literal["poster"]
    image_id: UUID
    mobile_image_id: UUID
    collection_id: UUID
    layout: Literal["full", "split", "inset"]
    overlay: Overlay
    title: str | None = Field(default=None, max_length=240)
    type_role: Literal["campaign-headline", "campaign-quote"]

class CollectionEntry(BaseModel):
    type: Literal["collection-entry"]
    collection_id: UUID
    heading: str = Field(min_length=1, max_length=60)

CampaignBlock = Annotated[
    Union[Hero, Video, Poster, CollectionEntry], Field(discriminator="type")
]

class CampaignRevision(BaseModel):
    department: Literal["women", "home"]
    version: int = Field(gt=0)
    blocks: list[CampaignBlock] = Field(min_length=5)

    @model_validator(mode="after")
    def validate_sequence(self) -> Self:
        kinds = [block.type for block in self.blocks]
        if (kinds[:2] != ["hero", "video"]
                or kinds[-1] != "collection-entry"
                or any(kind != "poster" for kind in kinds[2:-1])):
            raise ValueError("Required: hero, video, two or more posters, entrance")
        return self

# Pydantic -> OpenAPI -> generated TS types; no second frontend schema.
# Publish service checks ready/rights/alt/crops/captions and live department targets.
# Menu kind normal/sale requires real sale eligibility; type roles map to tokens.
# One revision swap + invalidation job commit; rollback selects a prior revision.
# Shared public/preview renderer owns the pinned overlay, route entrance and footer.
```

The schema uses [Pydantic model validators](https://docs.pydantic.dev/latest/concepts/validators/) for structural checks; database-backed publish eligibility belongs to the content service.

**Verification ownership (T09/T05/T11):** Extend existing ownership/merge cases and content validation parameter tables; add one editor publish/rollback journey with the public renderer. Contract/type generation verifies editorial schema changes. Preview comparisons reuse public visual checkpoints, rather than duplicating their entire suite.

**Acceptance criteria:**

- [ ] Pydantic is the authoritative content schema and generates frontend types. Public pages and admin preview render the same components; no page-builder dependency, arbitrary CSS editor or parallel rendering stack is added.

- [ ] A customer sees only their own orders and addresses. Changing IDs in requests does not reveal another person's data.
- [ ] Guest lookup responses resist enumeration; expired/reused links fail; rate limits apply. A successful exchange grants access only to the intended order.
- [ ] Return request quantities and eligibility come from the server; the customer can follow approval, receipt, and refund progress without contacting a developer.
- [ ] **ZR-12:** editor replaces each department hero/video/posters, changes crops/control tone/collection target, previews both journeys, publishes and rolls back through UI. Missing video, fewer than two posters, wrong order, unready media or cross-department target blocks publication without changing live content. Public revision change appears within 60 seconds.
- [ ] Editor configures menu groups/previews, eligible sale links, headline/quote roles, overlay tone/destination, every required editorial template, model/cutout roles and both relation types without code. View 1/2/3 and PDP previews reproduce the public renderer. Archived targets disappear safely from live navigation/recommendations; no stale price/stock is committed through a preview or cached block.
- [ ] Guest/account Favourites remain accessible through authentication changes; one-time merge preserves owned products and removal semantics. Order and saved-list ownership checks pass independently.
- [ ] Every public footer/help link resolves to real content; support submission is stored once and visible to staff, with recoverable email delivery.
- [ ] Structured data price/stock matches rendered product facts; private routes and preview drafts are absent from sitemap and public caches. Required policy/business details are supplied before launch.

**Exit strategy:** Customer retrieves a guest order, requests a return and uses merged Favourites; editor authors both full campaign journeys, all template families and product relations, then publishes and rolls back. Archive screenshots, publication validation and authorization tests. A hard-coded campaign or missing template/video editor does not satisfy ZR-12. If publishing breaks a layout, restore the prior content revision. If account enhancements regress, keep the secure guest access flow and support workflow operating; do not remove required order access or return handling.

### S3.3 — Prove resilience and prepare production release

**Story:** As the owner, I can launch a store whose shopping, stock, payment, and operational behavior has been tested under realistic failures.

**Scope / implementation:**

1. Execute the existing risk-owned suites from §4.6, browser journeys, permission matrix, inventory/payment races and a11y review; consolidate gaps into their owning tests rather than writing a second release regression suite. Complete the style §§12–13 screenshot/traceability matrix. Compare all ZR-01–12 plus V01–V06 to Z01–Z14 and the recording; distinguish observed composition from proposed CSS sizes/timings. Capture both department heroes, video, two posters, scroll entrance, full-screen menu, all product views/templates, PDP opening/continuation/three discovery surfaces, bag/Favourites/Continue and content preview. Fix failures within this story; a report alone is not completion.
2. Test catalogue/search against 10,000 representative products and 100,000 variants in a performance-only DB. Run 50 requests/sec mixed public reads for 15 minutes and 20 concurrent checkout attempts. Record dataset, hosting tier, latency percentiles, error rates, and bottlenecks.
3. Target p95 public read API <400 ms and checkout application transaction <800 ms, excluding provider interaction, with <1% unexpected HTTP failures and zero invariant violations. Tune indexes/queries and set pool limits before scaling services.
4. Target field p75 LCP ≤2.5 s, INP ≤200 ms, CLS ≤0.1 once adequate real traffic exists. Before launch use repeated lab runs on representative mobile devices/network throttling as a proxy; lab results cannot establish field p75. Apply [Web Vitals guidance](https://web.dev/articles/vitals).
5. Verify backup/PITR coverage and restore into an isolated DB; restore media/configuration too. Provisional operating targets: RPO ≤15 minutes, RTO ≤4 hours, measured in the drill; choose a managed plan that supports them. An older backup requires provider/payment reconciliation before accepting new checkouts, not blind resumption.
6. Add alerts for payment mismatch, reservation invariant violation, old inbox/outbox work, DB exhaustion, worker heartbeat loss, and sustained 5xx. Document pause-checkout, replay/reconcile, restore, credential rotation, customer communication, and forward-fix procedures.
7. Rehearse additive migration → web/API/worker rollout → smoke purchase → refund → rollback. Keep webhook/refund processing active when checkout is paused. Launch production only after merchant credentials, actual inventory/media, shipping/tax configuration, verified support/email domain, and policies are ready.

8. Exercise horizontal touch gestures without blocking vertical scroll, arrow/keyboard alternatives, Women default and Home deep-link/Back restoration, inactive-department media teardown, explicit pause/autoplay rejection/reduced-motion/data-saving behavior, and the actual collection-route handoff/anchor: deduplicated history, retained entrance, no auto-loop on Back, reload/deep links, failed load and stale-request cancellation. Verify heavy-sans/serif roles, pinned-overlay coordinates and retirement, sale accent/eligibility and intentional text-size adaptation. Verify View 1/2/3 keeps result IDs/order/anchor after filters/Back; inspect sticky controls over each actual image and in short/zoomed layouts. Test publishing/archiving while a shopper has an older page open.

**Code direction — one release-blocking invariant test:**

```python
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

def test_final_unit_reserved_once(committed_fixtures, checkout_service):
    sku = committed_fixtures.stocked_variant(on_hand=1)
    owners = [committed_fixtures.guest_cart(sku, quantity=1) for _ in range(20)]
    start = Barrier(20)

    def attempt(index):
        start.wait(timeout=10)  # before acquiring a connection; synchronize contenders
        try:
            checkout_service.reserve(owners[index], key=f"race-{index}")
            return "reserved"
        except InsufficientStock:
            return "sold_out"
        # Any unexpected exception fails the test, not counted as a valid loser.

    with ThreadPoolExecutor(max_workers=20) as pool:
        outcomes = list(pool.map(attempt, range(20)))
    assert outcomes.count("reserved") == 1
    assert outcomes.count("sold_out") == 19
    assert committed_fixtures.inventory(sku).reserved == 1
    assert committed_fixtures.inventory(sku).on_hand == 1
    assert committed_fixtures.active_reservation_quantity(sku) == 1
# Real PostgreSQL + committed isolated fixtures; each service call owns a transaction.
# This is the S2.2/T06 test reused at release, not a duplicate Sprint 3 test file.
```


Additional browser-test direction (fixtures expose stable semantic names):

```ts
test('home department journey enters its real collection route', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'Women department', exact: true }))
    .toHaveAttribute('aria-pressed', 'true');
  await page.getByRole('button', { name: 'Home department', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Home department', exact: true }))
    .toHaveAttribute('aria-pressed', 'true');
  await expect(page.getByTestId('campaign-sequence'))
    .toHaveAttribute('data-department', 'home');
  await expect(page.getByTestId('campaign-sequence').locator('video')).toHaveCount(1);
  await expect(page.getByTestId('campaign-poster')).toHaveCount(2); // seeded fixture
  await page.getByRole('link', { name: 'Scroll to the new collection' }).click();
  await expect(page).toHaveURL(/\/collections\/home-new-in(?:[?#].*)?$/);
  await expect(page.locator('#new-collection')).toBeInViewport();
  await expect(page.locator('#new-collection [data-product-id]').first()).toBeVisible();
});
// Also test passive scroll URL entry, one history push, Back suppression and stale requests.
// Add physical-touch and media-event tests; element counts do not prove playback.
```

**Verification ownership (T01–T12):** Reuse prior suites on the release candidate; add only a genuinely missing risk case at its owning layer. Release work focuses on reference/motion comparison, physical devices, performance, provider rehearsal and restore. Attach runtime/flake/dependency reports as well as failures fixed.

**Acceptance criteria:**

- [ ] The §4.6 risk register has a primary test owner and evidence for each risk, with no unexplained duplicate suites. CI timings meet the stated runner budgets or have a measured remediation decision; dependency/source growth is reviewed under §4.5 without removing any required fidelity or integrity gate.

- [ ] **ZR-01–12:** every row has linked implementation, automated/manual result and approved desktop/mobile comparison capture. All required journeys/templates/modes/gallery/recommendation/bag/authoring surfaces are present; screenshots alone cannot pass behavior gates.
- [ ] V01–V06 checks from style §13.2 pass: type roles, ≤2 px pinned-position drift, overlay exit, URL handoff/history/failure, sale eligibility and readable small text.
- [ ] Gesture, media lifecycle, scroll entrance, URL/view restoration, product eligibility and fixed-control collision tests pass for both departments. No out-of-scope merchandise appears in authored or fallback surfaces.
- [ ] All story gates pass against the release candidate; zero unresolved P0/P1 defects and no known stock/payment/authorization defect at any severity.
- [ ] Desktop Chrome/Firefox/Safari and physical iOS Safari/Android Chrome complete browse-to-order and admin-critical flows. At 200% text zoom and 320 px width, primary actions remain reachable.
- [ ] Automated axe shows no serious/critical findings on critical states; manual keyboard, VoiceOver or NVDA, dialog, error, and focus checks pass. Target WCAG 2.2 AA, not just a scanner score.
- [ ] Defined load run meets latency/error/invariant goals, with logs retained; application handles provider outage and worker restart without losing paid orders.
- [ ] Restore drill meets measured RPO/RTO and reconciles a payment captured after the restored snapshot. No double fulfilment, refund, or stock consumption results.
- [ ] A controlled authorized live purchase and refund validates production merchant mode before opening checkout broadly; staging success is never reported as live readiness.
- [ ] Operator can add/remove products, fulfil, refund, pause checkout, and use exception queues with the release runbook; alerts reach the configured operator channel.

**Exit strategy:** Go live only when the acceptance checklist, reconciliation report, visual review, and operator rehearsal pass. Otherwise retain the staging/catalogue-only release and record the exact blocker/owner; never call it a functioning launched store. Roll back application containers with compatible schema, disable new checkouts if necessary, and keep reconciliation running. Database restore is a disaster-recovery action, not ordinary deployment rollback.

**Sprint 3 exit:** Boutique staff can operate the shop and the complete purchase/fulfilment/refund lifecycle has been verified. If external merchant activation or required business inputs remain unavailable, label the result “staging complete, production blocked” with those explicit dependencies.

## 8. Cross-story release checklist and decisions

| Gate | Evidence | Owner |
| --- | --- | --- |
| Catalogue/media | 40 staging products; real launch stock; lead + four continuation images + cutout per product; both department videos/posters ready; rights, dimensions and pack contents complete | Boutique operator + S1.2 |
| Commerce integrity | Stock contention, expiry/capture race, duplicate/late events, unknown external results and refund limits | Backend + QA |
| Privacy/permissions | Direct API denial, object ownership, staff revocation/MFA, public DB isolation, no private caching | Platform + QA |
| Visual/usability | ZR-01–12 and V01–V06 signed coverage; all reference compositions and interactions; style §§12–13 snapshots, mobile keyboard/dialog checks, clear error states and implemented tokens | Designer + frontend |
| Operations | Shipment/return demo, failed-job recovery, alert drill, backup/media restore and reconciliation | Operator + platform |
| Maintainability/testing | One commerce implementation; reviewed dependency and source growth; T01–T12 evidence, CI runtime/flake report, no redundant generated suites | Tech lead + QA |
| Business inputs | Merchant activation, boutique identity, serviceable PINs, shipping fees, tax/invoice rules, returns policy, support contacts, real imagery | Boutique owner |

Confirm business inputs during Sprint 1; proceed with explicit staging fixtures until provided. Do not invent live rates, delivery promises, garment measurements, product availability, or return eligibility. Live credentials and sending/hosting resources are provisioned during implementation through the project's normal access process.

If capacity tightens, defer CSV conveniences, additional editorial templates beyond the specified families, extra decorative effects absent from the supplied references and automatic carrier integrations. Do not defer ZR-01–12: Women/Home switching, real video/poster/scroll journey, all three product views, specified templates, PDP continuation gallery and separate discovery surfaces, Favourites, reference bag, and admin authoring are required. Preserve commerce integrity, product CRUD, exact variants, PostgreSQL persistence, operations, accessibility and recovery. Extend duration or adjust staffing if the committed gates do not fit; never label a removed requirement complete. Incident rollback is an operational safeguard, not an acceptance waiver.

The nine story exit strategies define completion evidence and containment/rollback. A failed gate means the story remains open, even if the happy-path demo looks finished.
