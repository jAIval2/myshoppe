# MyShoppe

A local, working boutique storefront for **Women and Home**, India / INR. Next.js + React on the front, FastAPI + PostgreSQL behind it. Products, inventory, bags, favourites, orders, campaign revisions and staff permissions persist in PostgreSQL.

## Open the store

- Store: <http://localhost:3000>
- Account: <http://localhost:3000/account>
- Admin: <http://localhost:3000/admin>
- API documentation: <http://127.0.0.1:8000/docs>

For the local admin, open **Account → Development accounts → Continue as owner → Open boutique admin**. Customer, merchandiser, fulfilment and support accounts are also available. These buttons only exist when development login is explicitly enabled. Checkout has a clearly labelled **development order** action; it does not charge a card or send external email.

## Operating the shop

Customers can browse **Women** and **Home**, use **VIEW 1** (editorial frames), **VIEW 2** (model gallery) or **VIEW 3** (compact product grid), then open a product, choose its exact colour and size, add it to the bag or save it to Favourites. Checkout validates the delivery address and stock. In this local build choose **development order**; that records a demo order and never charges a payment method. Customers can open Account → Orders to track or request an eligible return.

To add merchandise, open Admin → Products → Add product. Enter a clear title, URL slug, department and category, description, material and care. For Home, provide dimensions, contents and whether the item is a cover or insert. Add one row per sellable SKU/colour/size; enter prices in rupees, although the API stores paise. Upload photographs, choose their roles, add useful alternative text, save the draft, adjust stock with a reason, preview the product, then publish it. Publishing checks the required product data and media. Archive removes a product from the storefront while keeping existing order records. A published or previously ordered item must be archived rather than erased.

The **Revision 1 / Revision 2 / Revision 3** label on an edited product is its saved revision number. It protects newer edits from being overwritten by a stale browser tab; it is not a product tier and does not select a storefront layout. The separate storefront **VIEW 1 / VIEW 2 / VIEW 3** controls change listing density. Campaign **VERSION** labels identify saved campaign drafts; **LIVE** marks the currently published version. Restore changes campaign content only, not stock or orders.

Staff permissions are checked by the API on every operation. **Owner** can manage products, inventory, content, staff, fulfilment, returns, refunds and support. **Merchandiser** can manage products, stock and campaign content, but has no order/refund access. **Fulfilment** can read orders, ship/deliver them, inspect returns and restock sellable returns. **Support** can read orders and manage support/returns; support can receive an unsellable return but cannot restock it or issue a refund. **Customer** and **Guest** accounts can access only their own account/guest shopping state and order actions. Real staff accounts require the configured provider login and MFA; the local persona buttons are development-only. Staff provisioning may require the setup command described in the integration section below.

For campaign changes, create or edit a department draft, preview it, publish it, and use campaign history to restore a previous revision if needed. Video processing runs in the background; wait for its status before publishing. In Orders, fulfil the paid order, add tracking, mark delivery, inspect a return and issue any approved refund. Keep provider and customer support actions tied to the order history.

The seeded photographs and prices are demonstration content, not actual merchandise. Replace them with your product photography, real cutouts, consistent colour/size photographs, Home film, prices and policies before launch. The source manifest is in `web/public/media/sources.json`. Fonts are locally served Inter and Bodoni Moda, with their OFL licences beside the assets.

## Run locally

Requires Node 24, Python 3.13+, PostgreSQL 18, and FFmpeg/FFprobe for uploaded campaign films. The current development database is isolated in `.local/postgres`, listening only on `127.0.0.1:55432`.

Install from the repository root:

```sh
python3.13 -m venv .venv
.venv/bin/pip install -r backend/requirements.lock
npm --prefix web ci
cp .env.example .env
python3 scripts/database.py
```

Alternatively, start PostgreSQL with `docker compose up -d postgres` instead of `scripts/database.py`. Do not run both on the same port. To run the full containerized local shop, use `docker compose -f compose.yaml -f compose.app.yaml up --build`; open <http://localhost:8080>. Seed its demo catalogue once with `docker compose -f compose.yaml -f compose.app.yaml --profile tools run --rm seed`. With Docker, create the test database once using `docker compose exec postgres createdb -U myshoppe myshoppe_test`.

Initialize the schema and development inventory:

```sh
cd backend
../.venv/bin/alembic upgrade head
../.venv/bin/python -m app.seed
cd ..
python3 scripts/dev.py
```

The runner loads `.env` and starts the API, commerce worker, media worker and web app. Ctrl-C stops those four child processes; PostgreSQL remains running. Stop the native database explicitly with `pg_ctl -D .local/postgres stop`, or use `docker compose stop postgres` for Docker. Do not start a second runner while the review servers occupy ports 3000 and 8000. The full local Compose profile uses local disk for processed uploads on one host; it is for review and development, not horizontal deployment.

To review the optimized frontend, build with `npm --prefix web run build` while the API is available. Stop the existing web process first, then run `python3 scripts/dev.py --production-build` after stopping any existing API/worker. This serves the production **frontend build** while retaining development identity and payments.

Media and fonts are included locally. Recovery scripts `scripts/fetch-media.py` and `scripts/fetch-fonts.py` require internet access. Uploaded originals are private under `.local/media-sources`; processed outputs live in `web/public/uploads`. Back up both PostgreSQL and these media directories.

## What is implemented

- Women-default campaign, horizontal department transition, pinned lower-right wordmark, video playback/pause, split and inset posters, scroll entrance with collection URL handoff, fullscreen navigation and mobile controls.
- Numbered categories, search and SKU-consistent filters, three listing densities, editorial category panels, shared quick-add, colour/size selection, large product opening, four-image continuation gallery, product strip, curated complements and suggestions.
- Persistent guest/account bags and favourites, address validation, shipping quote, transactional stock reservation, immutable order snapshots, order history and return requests.
- Admin product/variant creation and editing, upload/reorder/remove images, publication validation, archive, stock adjustments with reasons, campaign drafts/preview/publish/restore, overview, fulfilment, delivery, return inspection and refunds.
- Opaque HttpOnly sessions, permission checks in services, managed email OTP/TOTP adapter, current staff membership checks, origin checks, optimistic version checks and audit records.
- Durable webhook inbox and leased PostgreSQL outbox; payment reconciliation, reservation expiry, refund reconciliation, cart clearing, confirmation delivery and video processing. Unknown money operations are reconciled before retrying.

See [implementation status](IMPLEMENTATION_STATUS.md) for the remaining launch gates. This is a reviewable development build, not a claim that every acceptance criterion in the much larger sprint plan has passed.

## Code organization

```text
web/src/app/                 Routes and global visual rules
web/src/components/          Shell, dialogs, product cards, SKU picker, owned shop state
web/src/features/            Campaign, catalogue, PDP, bag, checkout, account
web/src/features/admin/      Product, content, order and operations screens
web/src/lib/                 Fetch transport and generated OpenAPI types
backend/app/features/*/      HTTP controllers → Protocol interfaces → services
backend/app/adapters/        Razorpay, Supabase, email and video processing
backend/app/db.py            PostgreSQL tables and constraints
backend/app/worker.py        Leased outbox dispatcher
backend/migrations/         Forward migrations
backend/tests/              Risk-focused PostgreSQL tests
web/tests/                  Four cross-layer browser journeys
```

Transactions belong to services. Controllers validate transport and call interfaces; they do not decide money, inventory, publication or authorization rules. SQLAlchemy Core keeps query/transaction behavior explicit. One API and one worker share the same code and database; no Redis, Celery, broker, generic repository layer, frontend state library, animation library or component kit.

Only Next.js, React and React DOM are frontend runtime dependencies. Native CSS, Web Animations, IntersectionObserver and `<dialog>` provide interactions. The backend lock records exact installed versions; npm has a lockfile. Generated API types are updated with `npm --prefix web run types:api` while the API is running. Some read DTOs are still explicit TypeScript types; consolidating those is listed in the status file. The commerce and media workers run as separate processes so video encoding cannot block payment recovery.

## Tests and debugging

```sh
.venv/bin/ruff check backend scripts
cd backend
../.venv/bin/pytest -q
cd ../web
npm run typecheck
npm run build
npm test
```

The browser tests use installed Google Chrome. On CI or a machine without it, run `npx playwright install --with-deps chrome` first. Browser tests expect API, worker and the optimized web build on their default ports. They place development orders, consuming a small amount of seeded development stock. The backend suite uses **only `myshoppe_test`**, which is truncated between tests; it rejects any other database name. Never point it at merchant data.

The suite assigns each invariant an owner: database/service tests for concurrency, money, permissions and retries; browser journeys for routing, interaction and accessibility. Quantity and role partitions are parameterized. Add a test for a distinct risk or regression, not for every similar button. Current automated scope: **21 backend cases and 4 browser journeys**; browser scope includes a serious/critical axe check on the mobile listing. This is not a full accessibility audit or proof of pixel parity.

Browser screenshots and failure traces appear in `web/test-results`; request failures carry `X-Request-ID`. Admin Overview exposes failed/unknown jobs and allows retry of safe recovery handlers. Development confirmations are JSON files in `.local/mail`. Run the worker whenever testing order completion: cart clearing and confirmation delivery are asynchronous.

There is one dependency deprecation warning from Starlette's HTTPX TestClient. The suite passes with the locked versions; avoid adding a second HTTP library just to silence it. A dependency update should resolve that compatibility path deliberately.

## Configure real integrations

Keep secret values in environment configuration, never the repository or browser bundle. `.env.example` lists names.

- **Supabase Auth:** configure email OTP, TOTP and asymmetric JWT signing keys. Set `SUPABASE_URL` and `SUPABASE_ANON_KEY`. The server verifies JWT issuer/audience/signature for MFA and retrieves the provider user; only verified AAL2 staff sessions can operate admin services. Initial staff membership is an explicit operator action after that person first verifies their email: from `backend`, run `../.venv/bin/python -m app.staff person@example.com owner`. Granting/revoking a role revokes existing local sessions. Production staff sessions expire after 30 minutes and require sign-in again. [Provider MFA documentation](https://supabase.com/docs/guides/auth/auth-mfa/totp).
- **Razorpay:** set key ID, key secret and webhook secret, set `PAYMENT_MODE=razorpay`, configure automatic capture and the `/api/webhooks/razorpay` endpoint. Checkout callbacks only navigate to a pending order; a verified provider capture decides payment state. Interrupted creation is matched to a local order receipt using a bounded provider query; uncertain results stay visible for operator review. [Order query API](https://razorpay.com/docs/api/orders/fetch-all/).
- **Email:** configure `RESEND_API_KEY` and a verified `EMAIL_FROM`. Development payments spool locally; real orders use an idempotency key for the email request. Provider delivery and domain verification must be exercised before launch.
- **Product and campaign media:** set `MEDIA_STORAGE_MODE=object`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` and `MEDIA_BUCKET`. Create that Supabase Storage bucket as public so storefront images/video can load, and set its upload limit to at least 80 MB with WebP, JPEG and MP4 allowed. The app performs bounded resumable uploads and stores object keys in video jobs, so API and media worker can run on separate hosts. Keep the service key server-side. Local development defaults to disk storage.
- **Network limits:** set `TRUSTED_PROXY_CIDRS` to the exact private CIDRs of the only reverse proxies allowed to reach FastAPI, and `RATE_LIMIT_HMAC_KEY` to a random secret of at least 32 characters. Configure matching Nginx `set_real_ip_from` entries and have that proxy replace, not append to, the client address header. The app ignores forwarding headers from untrusted peers and stores only a keyed hash for its secondary auth/checkout/support budgets.
- **Commerce:** configure real serviceable PINs, shipping, tax/invoice data, returns and merchant disclosures. The development `commerce` settings row has `live_approved=false`; real-payment checkout remains blocked until launch configuration is deliberately completed.

`APP_ENV=production` rejects development login/payment settings and requires HTTPS, object media storage, and identity/payment credentials. The full local Compose stack includes PostgreSQL, API, web, separate commerce/media workers and a loopback-only Nginx entry point; it is a development setup, not a hosted production deployment. For a real deployment, terminate TLS at a managed edge, allow Nginx traffic only from that trusted edge, configure the edge's forwarded-protocol header, and keep the Nginx listener private. Configure Nginx `set_real_ip_from` with only the edge's published CIDRs before relying on per-client limits; its default limit key sees the direct peer. Set database pool limits to the provider's connection budget. Before accepting live orders, configure and review the merchant's tax/invoice, shipping, PIN-code, returns and disclosure rules; complete Razorpay/Supabase/email sandbox checks; and establish backups, restore drills, alerting and a rollback runbook. Those merchant and hosting values are intentionally not guessed in this repository.
