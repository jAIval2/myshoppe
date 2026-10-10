import hashlib
import json
from datetime import timedelta
from sqlalchemy import func, select, update
from app import db
from app.errors import require
from app.settings import settings
from app.features.checkout.service import enqueue


class PaymentService:
    def __init__(self, engine, gateway):
        self.engine, self.gateway = engine, gateway

    def session(self, actor, order_id):
        with self.engine.begin() as c:
            order = (
                c.execute(
                    select(db.orders)
                    .where(db.orders.c.id == order_id, db.orders.c.owner_id == actor.owner_id)
                    .with_for_update()
                )
                .mappings()
                .first()
            )
            require(order, "NOT_FOUND", "Order not found", 404)
            unexpired = c.execute(select(func.now() < order["expires_at"])).scalar_one()
            require(
                order["status"] == "pending" and unexpired,
                "CHECKOUT_EXPIRED",
                "This checkout is no longer active.",
            )
            if settings.payment_mode == "development":
                return {"mode": "development", "order_id": order_id, "amount": order["total"]}
            if order["provider_order_id"]:
                return {
                    "mode": "razorpay",
                    "key": settings.razorpay_id,
                    "provider_order_id": order["provider_order_id"],
                    "amount": order["total"],
                }
            key = f"provider-order:{order_id}"
            job = c.execute(select(db.jobs).where(db.jobs.c.operation_key == key)).mappings().first()
            require(
                not job, "PAYMENT_PENDING", "Payment session is being reconciled. Check your order shortly."
            )
            enqueue(c, key, "provider.create", {"order_id": order_id})
            c.execute(update(db.jobs).where(db.jobs.c.operation_key == key).values(status="unknown"))
            enqueue(c, f"reconcile:{order_id}", "payment.reconcile", {"order_id": order_id})
            c.execute(
                update(db.jobs)
                .where(db.jobs.c.operation_key == f"reconcile:{order_id}")
                .values(due_at=func.now() + timedelta(seconds=45))
            )
        # Durable marker precedes network. Never blindly retry a timed-out creation.
        result = self.gateway.create_order(order)
        with self.engine.begin() as c:
            c.execute(
                update(db.orders).where(db.orders.c.id == order_id).values(provider_order_id=result["id"])
            )
            c.execute(update(db.jobs).where(db.jobs.c.operation_key == key).values(status="done"))
        return {
            "mode": "razorpay",
            "key": settings.razorpay_id,
            "provider_order_id": result["id"],
            "amount": order["total"],
        }

    def reconcile(self, order_id):
        with self.engine.connect() as c:
            order = dict(c.execute(select(db.orders).where(db.orders.c.id == order_id)).mappings().one())
        if not order["provider_order_id"]:
            found = self.gateway.find_order(order)
            if not found:
                require(
                    order["created_at"] > db.now() - timedelta(minutes=20),
                    "ORDER_UNRESOLVED",
                    "Provider order creation remains uncertain. Review the provider receipt before any new attempt.",
                )
                return False
            require(
                found["amount"] == order["total"] and found["currency"] == "INR",
                "PAYMENT_MISMATCH",
                "Provider order totals differ.",
            )
            order["provider_order_id"] = found["id"]
            with self.engine.begin() as c:
                c.execute(
                    update(db.orders)
                    .where(db.orders.c.id == order_id, db.orders.c.provider_order_id.is_(None))
                    .values(provider_order_id=found["id"])
                )
                c.execute(
                    update(db.jobs)
                    .where(db.jobs.c.operation_key == f"provider-order:{order_id}")
                    .values(status="done")
                )
        rows = self.gateway.fetch_order_payments(order["provider_order_id"])["items"]
        for payment in rows:
            if payment["status"] == "captured":
                verified = self.gateway.fetch_payment(payment["id"])
                require(verified["status"] == "captured", "PAYMENT_PENDING", "Payment capture pending")
                self.capture(
                    order_id, verified["id"], verified["amount"], verified["currency"], verified["order_id"]
                )
        return bool(
            order["payment_id"]
            or any(r["status"] == "captured" for r in rows)
            or order["created_at"] < db.now() - timedelta(days=3)
        )

    def development_capture(self, actor, order_id):
        require(
            settings.environment == "development" and settings.payment_mode == "development",
            "NOT_FOUND",
            "Not available",
            404,
        )
        with self.engine.connect() as c:
            order = (
                c.execute(
                    select(db.orders).where(
                        db.orders.c.id == order_id, db.orders.c.owner_id == actor.owner_id
                    )
                )
                .mappings()
                .first()
            )
        require(order, "NOT_FOUND", "Order not found", 404)
        self.capture(order_id, f"dev_{order_id}", order["total"])
        return {"ok": True, "development": True}

    @db.retry_transient_write
    def ingest(self, raw, signature, event_id):
        self.gateway.verify(raw, signature)
        require(event_id and len(event_id) <= 150, "INVALID_EVENT", "Event ID is required", 400)
        payload = json.loads(raw)
        digest = hashlib.sha256(raw).hexdigest()
        with self.engine.begin() as c:
            from sqlalchemy.dialects.postgresql import insert

            row = c.execute(
                insert(db.events)
                .values(event_id=event_id, body_hash=digest, payload=payload)
                .on_conflict_do_nothing()
                .returning(db.events.c.event_id)
            ).first()
            if not row:
                old = c.execute(
                    select(db.events.c.body_hash).where(db.events.c.event_id == event_id)
                ).scalar_one()
                require(old == digest, "EVENT_CONFLICT", "Event payload changed")
            enqueue(c, f"webhook:{event_id}", "payment.event", {"event_id": event_id})

    @db.retry_transient_write
    def capture(self, order_id, payment_id, amount, currency="INR", provider_order_id=None):
        with self.engine.begin() as c:
            order = (
                c.execute(select(db.orders).where(db.orders.c.id == order_id).with_for_update())
                .mappings()
                .first()
            )
            require(order, "NOT_FOUND", "Order not found", 404)
            require(
                order["total"] == amount and currency == "INR",
                "PAYMENT_MISMATCH",
                "Payment does not match the order.",
            )
            if provider_order_id:
                require(
                    provider_order_id == order["provider_order_id"],
                    "PAYMENT_MISMATCH",
                    "Provider order does not match.",
                )
            if order["payment_id"] == payment_id:
                return
            require(
                not order["payment_id"],
                "DUPLICATE_CAPTURE",
                "Additional capture requires operator reconciliation.",
            )
            unexpired = c.execute(select(func.now() < order["expires_at"])).scalar_one()
            active = order["status"] == "pending" and unexpired
            items = (
                c.execute(
                    select(db.order_items)
                    .where(db.order_items.c.order_id == order_id)
                    .order_by(db.order_items.c.variant_id)
                )
                .mappings()
                .all()
            )
            for item in items:
                if item["reservation"] != "active":
                    continue
                c.execute(
                    update(db.inventory)
                    .where(db.inventory.c.variant_id == item["variant_id"])
                    .values(
                        reserved=db.inventory.c.reserved - item["quantity"],
                        **({"on_hand": db.inventory.c.on_hand - item["quantity"]} if active else {}),
                    )
                )
                c.execute(
                    update(db.order_items)
                    .where(db.order_items.c.id == item["id"])
                    .values(reservation="consumed" if active else "released")
                )
                c.execute(
                    db.movements.insert().values(
                        variant_id=item["variant_id"],
                        operation_key=f"capture:{order_id}:{item['id']}",
                        on_hand_delta=-item["quantity"] if active else 0,
                        reserved_delta=-item["quantity"],
                        reason="Payment capture",
                    )
                )
            c.execute(
                update(db.orders)
                .where(db.orders.c.id == order_id)
                .values(status="paid" if active else "paid_needs_resolution", payment_id=payment_id)
            )
            if active:
                enqueue(
                    c,
                    f"clear-cart:{order_id}",
                    "cart.clear",
                    {"owner_id": order["owner_id"], "version": order["cart_version"]},
                )
                enqueue(c, f"confirmation:{order_id}", "email.order", {"order_id": order_id})
            else:
                rid = c.execute(
                    db.refunds.insert()
                    .values(
                        order_id=order_id,
                        request_key=f"late:{payment_id}",
                        amount=amount,
                        reason="Payment arrived after reservation expiry",
                    )
                    .returning(db.refunds.c.id)
                ).scalar_one()
                enqueue(c, f"refund:{rid}", "payment.refund", {"refund_id": rid})

    @db.retry_transient_write
    def expire(self, at=None, limit=100):
        with self.engine.begin() as c:
            expiry = at if at is not None else func.now()
            orders = (
                c.execute(
                    select(db.orders)
                    .where(db.orders.c.status == "pending", db.orders.c.expires_at <= expiry)
                    .order_by(db.orders.c.expires_at)
                    .with_for_update(skip_locked=True)
                    .limit(limit)
                )
                .mappings()
                .all()
            )
            for order in orders:
                items = (
                    c.execute(
                        select(db.order_items)
                        .where(
                            db.order_items.c.order_id == order["id"], db.order_items.c.reservation == "active"
                        )
                        .order_by(db.order_items.c.variant_id)
                    )
                    .mappings()
                    .all()
                )
                for item in items:
                    c.execute(
                        update(db.inventory)
                        .where(db.inventory.c.variant_id == item["variant_id"])
                        .values(reserved=db.inventory.c.reserved - item["quantity"])
                    )
                    c.execute(
                        update(db.order_items)
                        .where(db.order_items.c.id == item["id"])
                        .values(reservation="released")
                    )
                    c.execute(
                        db.movements.insert().values(
                            variant_id=item["variant_id"],
                            operation_key=f"expire:{item['id']}",
                            on_hand_delta=0,
                            reserved_delta=-item["quantity"],
                            reason="Reservation expired",
                        )
                    )
                c.execute(update(db.orders).where(db.orders.c.id == order["id"]).values(status="expired"))
        return len(orders)
