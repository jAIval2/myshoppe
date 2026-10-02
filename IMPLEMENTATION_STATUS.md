# Implementation status — 2 October 2026

The original [sprint plan](SPRINT_PLAN.md) and [styling guide](STYLING_GUIDE.md) remain the target. The application is implemented and running for local review. The following separates working code from acceptance gates that require further implementation, real assets, provider configuration or operational evidence.

| Story | Working implementation | Remaining acceptance / launch work |
|---|---|---|
| S1.1 Foundation and identity | FastAPI controllers/interfaces/services, PostgreSQL schema with frozen baseline and forward migrations, local runner, email OTP/TOTP adapter, staff permissions, opaque sessions, staff CLI and revocation | Real provider integration exercise, provider-wide session revocation/refresh policy, hosted environments and restore drill |
| S1.2 Catalogue/admin/inventory | Product + variant CRUD, archive, media uploads and roles, stock ledger, optimistic edits, publication checks | Rights/crop/caption metadata workflow, complete media lifecycle cleanup/object storage; true product-specific photos and cutouts |
| S1.3 Campaign and navigation | Department switching, pinned wordmark, real video, split/inset posters, scroll entrance URL transition, menu, reduced motion, local typefaces | Reference-aligned timing and frame-by-frame review at all target sizes; Home-specific film; fully authored navigation and merchandising templates |
| S2.1 Listings/PDP | Views 1/2/3, numbered filters, search, category panels, explicit SKU choice, lead + paired continuation images, collection strip, curated complements/suggestions | Exact per-collection editorial composition, sticky strip behavior matching every reference frame, colour-specific photography, larger-catalog query/load profiling |
| S2.2 Bag/checkout/reservations | Bag/favourites persistence, quote validation, atomic reservation, last-unit contention test, stale-cart handling, immutable order data | Gift options, explicit quote TTL, final PIN/courier rules, full merchant tax/invoice engine, cookie-free guest order access |
| S2.3 Payments/confirmation | Development capture, Razorpay adapter, signed durable inbox, deduplication, expiry, late-capture hold/refund, reconciliation, confirmation outbox | Real Razorpay sandbox callback/webhook/reconciliation matrix, second distinct capture resolution, email delivery verification and monitoring |
| S3.1 Admin operations | Overview, job recovery, checkout pause, shipments, delivery timestamp, returns/inspection, bounded refunds, audit | Cancellation/exchange workflow, line-level refund allocation, pagination/date filters across large order sets, carrier integration; overview metrics currently aggregate development and real orders |
| S3.2 Customer/content | Account/order pages, favourites, support inbox, campaigns with saved draft preview, video processing, revision restore, staff TOTP flow | Newsletter integration, rich policy/settings/navigation editor, staff management UI, verified-email guest order lookup; some read DTOs still manually typed |
| S3.3 Hardening/launch | Focused PostgreSQL/browser checks, same-origin controls, upload processing, production build, local media/fonts, CI workflow | Live CI execution, full accessibility/visual regression audit, measured performance budgets, load/soak tests, deployment rollback/backup restore, merchant content and production incident runbook |

## Visual evidence and limitations

The supplied screenshots and 101-second screen recording were used as reference. Implemented the major page order, fixed controls, type contrast, large image placement, listing density controls and separate product continuation/suggestion sections. Chrome screenshots are captured by `web/tests/storefront.spec.ts` into `web/test-results`.

This build is **not yet certified as an exact visual or motion match**. Seed assets are reusable editorial placeholders, including model photography currently assigned to cutout roles and a shared temporary campaign film. Merchant photos, true cutouts and individual colour variants are necessary before final visual acceptance. Homepage department switching uses a lightweight native slide animation; precise reference timing still needs side-by-side recording review.

## Test ownership

Verified locally on 2 October: production build, TypeScript, Ruff, **21 backend cases**, **4 Chrome journeys**, migrations against an empty scratch database, authenticated video upload through FFmpeg to MP4/poster, immediate new-image serving without restart, and video byte-range playback. Screenshots were inspected after correcting a font-variable scope regression; the campaign journey now asserts the headline and wordmark remain large.

- PostgreSQL suite: valid quantity partitions; staff permission/AAL boundary; direct route and origin denial; same-variant filters; archive visibility; ownership and stale cart; checkout retry hash; 20 shoppers competing for one unit; expiry/late capture; capture/ship/deliver/return/refund lifecycle; actual HMAC verification and durable deduplication; campaign revision/asset readiness; account-switch isolation; concurrent stock adjustment retry; unknown provider-order recovery; staff MFA assurance.
- Browser suite: campaign/menu/department/collection handoff; three product views to development paid order; mobile navigation/overflow/axe; owner catalogue editor and campaign preview.
- Provider adapters are exercised through controlled fakes for deterministic failure semantics. No live charge, real email delivery or real Supabase project was claimed as tested.

## Review sequence

1. Browse Women → view 1/2/3 → product → choose colour/size → bag → development order.
2. Account → development owner → admin → change stock or product → publish/archive and verify storefront.
3. Campaigns → edit/save draft → saved preview → publish/restore.
4. Orders → ship quantities → mark delivered → customer return → inspect/restock → refund; observe worker recovery and audit.
5. Replace development assets and configure provider sandboxes before converting the remaining launch gates into release acceptance evidence.
