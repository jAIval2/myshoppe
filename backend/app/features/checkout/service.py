import hashlib
import json
from datetime import timedelta
from sqlalchemy import func, select, update, delete
from sqlalchemy.dialects.postgresql import insert
from app import db
from app.errors import require
from app.settings import settings
from app.identity import rate_limit
from .queries import lines


def fingerprint(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def enqueue(conn, key, kind, payload):
    conn.execute(
        insert(db.jobs)
        .values(operation_key=key, kind=kind, payload=payload, due_at=func.now())
        .on_conflict_do_nothing(index_elements=[db.jobs.c.operation_key])
    )


class CheckoutService:
    def __init__(self, engine):
        self.engine = engine

    def cart(self, actor):
        with self.engine.connect() as c:
            version = c.execute(
                select(db.carts.c.version).where(db.carts.c.owner_id == actor.owner_id)
            ).scalar_one_or_none()
            if version is None:
                return {"version": 1, "items": [], "subtotal": 0, "count": 0}
            items = lines(c, actor.owner_id)
        return {
            "version": version,
            "items": [
                {
                    **v,
                    "variant_id": v["id"],
                    "available": v["on_hand"] - v["reserved"],
                    "image": v["media"][0]["src"],
                }
                for v in items
            ],
            "subtotal": sum(i["quantity"] * i["price_paise"] for i in items),
            "count": sum(i["quantity"] for i in items),
        }

    @db.retry_transient_write
    def mutate(self, actor, command):
        with self.engine.begin() as c:
            cart = (
                c.execute(select(db.carts).where(db.carts.c.owner_id == actor.owner_id).with_for_update())
                .mappings()
                .one()
            )
            require(
                cart["version"] == command.expected_version,
                "STALE_CART",
                "Your bag changed in another tab. Review it and try again.",
            )
            if command.quantity:
                v = (
                    c.execute(
                        select(
                            db.variants, db.products.c.status, db.inventory.c.on_hand, db.inventory.c.reserved
                        )
                        .join(db.products)
                        .join(db.inventory)
                        .where(db.variants.c.id == command.variant_id)
                    )
                    .mappings()
                    .first()
                )
                require(
                    v and v["active"] and v["status"] == "published",
                    "UNAVAILABLE",
                    "This item is no longer available.",
                )
                require(
                    v["on_hand"] - v["reserved"] >= command.quantity,
                    "INSUFFICIENT_STOCK",
                    "There are not enough items available.",
                )
                stmt = insert(db.cart_items).values(
                    owner_id=actor.owner_id, variant_id=command.variant_id, quantity=command.quantity
                )
                c.execute(
                    stmt.on_conflict_do_update(
                        index_elements=[db.cart_items.c.owner_id, db.cart_items.c.variant_id],
                        set_={"quantity": command.quantity},
                    )
                )
            else:
                c.execute(
                    delete(db.cart_items).where(
                        db.cart_items.c.owner_id == actor.owner_id,
                        db.cart_items.c.variant_id == command.variant_id,
                    )
                )
            c.execute(
                update(db.carts)
                .where(db.carts.c.owner_id == actor.owner_id)
                .values(version=cart["version"] + 1, updated_at=db.now())
            )
        return self.cart(actor)

    def saved(self, actor):
        from app.features.catalog.queries import hydrate

        with self.engine.connect() as c:
            rows = (
                c.execute(
                    select(db.products)
                    .join(db.saved)
                    .where(db.saved.c.owner_id == actor.owner_id, db.products.c.status != "draft")
                )
                .mappings()
                .all()
            )
            return hydrate(c, rows)

    @db.retry_transient_write
    def save(self, actor, product_id, remove=False):
        with self.engine.begin() as c:
            if remove:
                c.execute(
                    delete(db.saved).where(
                        db.saved.c.owner_id == actor.owner_id, db.saved.c.product_id == product_id
                    )
                )
            else:
                require(
                    c.execute(
                        select(db.products.c.id).where(
                            db.products.c.id == product_id, db.products.c.status == "published"
                        )
                    ).first(),
                    "NOT_FOUND",
                    "Product unavailable",
                    404,
                )
                c.execute(
                    insert(db.saved)
                    .values(owner_id=actor.owner_id, product_id=product_id)
                    .on_conflict_do_nothing()
                )
        return {"ok": True}

    def _quote(self, c, actor, address):
        config = c.execute(
            select(db.settings_table.c.value).where(db.settings_table.c.key == "commerce")
        ).scalar_one()
        require(not config.get("paused"), "CHECKOUT_PAUSED", "Checkout is temporarily paused.", 503)
        require(
            settings.environment != "production" or config.get("live_approved"),
            "CONFIGURATION_REQUIRED",
            "Shipping and tax settings need merchant approval.",
            503,
        )
        require(
            any(address.pin.startswith(p) for p in config["pin_prefixes"]),
            "UNSERVICEABLE",
            "We do not currently deliver to this PIN code.",
            422,
        )
        items = lines(c, actor.owner_id)
        require(items, "EMPTY_CART", "Add an item to your bag first.")
        for item in items:
            require(
                item["active"] and item["status"] == "published",
                "UNAVAILABLE",
                f"{item['title']} is no longer available.",
            )
            require(
                item["quantity"] <= item["on_hand"] - item["reserved"],
                "INSUFFICIENT_STOCK",
                f"Not enough stock for {item['title']}.",
            )
        subtotal = sum(i["quantity"] * i["price_paise"] for i in items)
        shipping = 0 if subtotal >= config["free_shipping_above"] else config["shipping_paise"]
        quote = {
            "subtotal": subtotal,
            "shipping": shipping,
            "total": subtotal + shipping,
            "currency": "INR",
            "tax_note": config["tax_note"],
            "development": settings.payment_mode == "development",
        }
        version = c.execute(
            select(db.carts.c.version).where(db.carts.c.owner_id == actor.owner_id)
        ).scalar_one()
        quote["quote_hash"] = fingerprint([actor.owner_id, version, address.model_dump(), quote])
        return quote, items, version

    def quote(self, actor, address):
        with self.engine.connect() as c:
            return self._quote(c, actor, address)[0]

    @db.retry_transient_write
    def reserve(self, actor, command):
        request_hash = fingerprint(command.model_dump(exclude={"request_key"}))
        with self.engine.begin() as c:
            c.execute(select(db.carts).where(db.carts.c.owner_id == actor.owner_id).with_for_update()).one()
            prior = (
                c.execute(
                    select(db.orders).where(
                        db.orders.c.owner_id == actor.owner_id, db.orders.c.request_key == command.request_key
                    )
                )
                .mappings()
                .first()
            )
            if prior:
                require(
                    prior["request_hash"] == request_hash,
                    "KEY_CONFLICT",
                    "Checkout key has already been used for different details.",
                )
                return dict(prior)
            rate_limit(c, f"checkout:{actor.owner_id}", 10)
            active = c.execute(
                select(db.orders.c.id).where(
                    db.orders.c.owner_id == actor.owner_id,
                    db.orders.c.status == "pending",
                    db.orders.c.expires_at > func.now(),
                )
            ).first()
            require(
                not active,
                "CHECKOUT_EXISTS",
                "A checkout is already active. Complete it from your orders or wait for it to expire.",
            )
            quote, items, version = self._quote(c, actor, command.address)
            require(
                quote["quote_hash"] == command.quote_hash,
                "QUOTE_CHANGED",
                "Your price or bag changed. Review the new total.",
            )
            # Lock product rows against archive/edit before checking snapshots again.
            ids = sorted(set(i["product_id"] for i in items))
            c.execute(
                select(db.products.c.id)
                .where(db.products.c.id.in_(ids))
                .order_by(db.products.c.id)
                .with_for_update()
            ).all()
            quote2, items, version = self._quote(c, actor, command.address)
            require(quote2["quote_hash"] == command.quote_hash, "QUOTE_CHANGED", "Review the updated total.")
            order = (
                c.execute(
                    db.orders.insert()
                    .values(
                        owner_id=actor.owner_id,
                        request_key=command.request_key,
                        request_hash=request_hash,
                        cart_version=version,
                        address=command.address.model_dump(),
                        subtotal=quote["subtotal"],
                        shipping=quote["shipping"],
                        total=quote["total"],
                        expires_at=func.now() + timedelta(minutes=15),
                        payment_mode=settings.payment_mode,
                    )
                    .returning(db.orders)
                )
                .mappings()
                .one()
            )
            for item in items:
                result = c.execute(
                    update(db.inventory)
                    .where(
                        db.inventory.c.variant_id == item["id"],
                        db.inventory.c.on_hand - db.inventory.c.reserved >= item["quantity"],
                    )
                    .values(reserved=db.inventory.c.reserved + item["quantity"])
                    .returning(db.inventory.c.variant_id)
                ).first()
                require(
                    result,
                    "INSUFFICIENT_STOCK",
                    "Another shopper purchased the last item. Your bag is unchanged.",
                )
                snapshot = {k: item[k] for k in ("title", "slug", "sku", "colour", "size", "dimensions")}
                snapshot["image"] = item["media"][0]["src"]
                c.execute(
                    db.order_items.insert().values(
                        order_id=order["id"],
                        variant_id=item["id"],
                        snapshot=snapshot,
                        quantity=item["quantity"],
                        price_paise=item["price_paise"],
                    )
                )
                c.execute(
                    db.movements.insert().values(
                        variant_id=item["id"],
                        operation_key=f"reserve:{order['id']}:{item['id']}",
                        on_hand_delta=0,
                        reserved_delta=item["quantity"],
                        reason="Checkout reservation",
                        actor=actor.owner_id,
                    )
                )
            return dict(order)
