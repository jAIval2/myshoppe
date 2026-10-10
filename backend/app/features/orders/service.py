from datetime import timedelta
from sqlalchemy import select, update, func
from app import db
from app.identity import require_permission, audit
from app.errors import require
from app.features.checkout.service import enqueue


class OrderService:
    def __init__(self, engine):
        self.engine = engine

    def list(self, actor, admin=False):
        with self.engine.connect() as c:
            if admin:
                require_permission(c, actor, "orders.read")
            query = select(db.orders).order_by(db.orders.c.created_at.desc()).limit(100)
            if not admin:
                query = query.where(db.orders.c.owner_id == actor.owner_id)
            return [dict(row) for row in c.execute(query).mappings()]

    def get(self, actor, order_id, admin=False):
        with self.engine.connect() as c:
            if admin:
                require_permission(c, actor, "orders.read")
            query = select(db.orders).where(db.orders.c.id == order_id)
            if not admin:
                query = query.where(db.orders.c.owner_id == actor.owner_id)
            row = c.execute(query).mappings().first()
            require(row, "NOT_FOUND", "Order not found", 404)
            return {
                **dict(row),
                **{
                    name: [
                        dict(r)
                        for r in c.execute(select(table).where(table.c.order_id == order_id)).mappings()
                    ]
                    for name, table in [
                        ("items", db.order_items),
                        ("shipments", db.shipments),
                        ("refunds", db.refunds),
                        ("returns", db.returns),
                    ]
                },
            }

    @db.retry_transient_write
    def refund(self, actor, order_id, command):
        with self.engine.begin() as c:
            require_permission(c, actor, "refunds.write")
            order = (
                c.execute(select(db.orders).where(db.orders.c.id == order_id).with_for_update())
                .mappings()
                .first()
            )
            require(order and order["payment_id"], "NOT_PAID", "Only a captured payment can be refunded.")
            prior = (
                c.execute(
                    select(db.refunds).where(
                        db.refunds.c.order_id == order_id, db.refunds.c.request_key == command.request_key
                    )
                )
                .mappings()
                .first()
            )
            if prior:
                require(
                    prior["amount"] == command.amount and prior["reason"] == command.reason,
                    "KEY_CONFLICT",
                    "Refund key already used",
                )
                return dict(prior)
            allocated = c.execute(
                select(func.coalesce(func.sum(db.refunds.c.amount), 0)).where(
                    db.refunds.c.order_id == order_id, db.refunds.c.status != "failed"
                )
            ).scalar_one()
            require(
                command.amount <= order["total"] - allocated,
                "REFUND_EXCEEDS_BALANCE",
                "Amount exceeds the remaining refundable balance.",
            )
            refund = (
                c.execute(
                    db.refunds.insert()
                    .values(
                        order_id=order_id,
                        request_key=command.request_key,
                        amount=command.amount,
                        reason=command.reason,
                    )
                    .returning(db.refunds)
                )
                .mappings()
                .one()
            )
            enqueue(c, f"refund:{refund['id']}", "payment.refund", {"refund_id": refund["id"]})
            audit(c, actor, "refund.requested", refund["id"], {"amount": command.amount})
            return dict(refund)

    @db.retry_transient_write
    def ship(self, actor, order_id, command):
        with self.engine.begin() as c:
            require_permission(c, actor, "orders.fulfil")
            order = (
                c.execute(select(db.orders).where(db.orders.c.id == order_id).with_for_update())
                .mappings()
                .first()
            )
            require(order and order["status"] == "paid", "ORDER_HELD", "Only paid, unheld orders can ship.")
            refund = c.execute(
                select(db.refunds.c.id).where(
                    db.refunds.c.order_id == order_id, db.refunds.c.status != "failed"
                )
            ).first()
            require(not refund, "ORDER_HELD", "Resolve refunds before creating another shipment.")
            for item_id, qty in command.items.items():
                row = c.execute(
                    update(db.order_items)
                    .where(
                        db.order_items.c.id == item_id,
                        db.order_items.c.order_id == order_id,
                        db.order_items.c.shipped + qty <= db.order_items.c.quantity,
                    )
                    .values(shipped=db.order_items.c.shipped + qty)
                    .returning(db.order_items.c.id)
                ).first()
                require(row, "SHIPMENT_QUANTITY", "Shipment exceeds an order item's remaining quantity.")
            c.execute(
                db.shipments.insert().values(
                    order_id=order_id, tracking=command.tracking, items=command.items
                )
            )
            remaining = c.execute(
                select(func.sum(db.order_items.c.quantity - db.order_items.c.shipped)).where(
                    db.order_items.c.order_id == order_id
                )
            ).scalar_one()
            c.execute(
                update(db.orders)
                .where(db.orders.c.id == order_id)
                .values(fulfilment="shipped" if remaining == 0 else "partially_shipped")
            )
            audit(c, actor, "order.shipped", order_id)
        return self.get(actor, order_id, True)

    @db.retry_transient_write
    def deliver(self, actor, order_id):
        with self.engine.begin() as c:
            require_permission(c, actor, "orders.fulfil")
            row = c.execute(
                update(db.orders)
                .where(db.orders.c.id == order_id, db.orders.c.fulfilment == "shipped")
                .values(fulfilment="delivered", delivered_at=db.now())
                .returning(db.orders.c.id)
            ).first()
            require(row, "INVALID_TRANSITION", "Ship every item before marking the order delivered.")
            c.execute(
                update(db.shipments).where(db.shipments.c.order_id == order_id).values(status="delivered")
            )
            audit(c, actor, "order.delivered", order_id)
        return self.get(actor, order_id, True)

    @db.retry_transient_write
    def request_return(self, actor, order_id, command):
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
            prior = (
                c.execute(
                    select(db.returns).where(
                        db.returns.c.order_id == order_id, db.returns.c.request_key == command.request_key
                    )
                )
                .mappings()
                .first()
            )
            if prior:
                require(
                    prior["items"] == command.items and prior["reason"] == command.reason,
                    "KEY_CONFLICT",
                    "Return key already used",
                )
                return dict(prior)
            require(
                order["fulfilment"] == "delivered"
                and order["delivered_at"]
                and order["delivered_at"] > db.now() - timedelta(days=30),
                "RETURN_INELIGIBLE",
                "This order requires support review for a return.",
            )
            pending = (
                c.execute(
                    select(db.returns.c["items"]).where(
                        db.returns.c.order_id == order_id, db.returns.c.status != "rejected"
                    )
                )
                .scalars()
                .all()
            )
            for iid, qty in command.items.items():
                item = (
                    c.execute(
                        select(db.order_items).where(
                            db.order_items.c.id == iid, db.order_items.c.order_id == order_id
                        )
                    )
                    .mappings()
                    .first()
                )
                used = sum(p.get(iid, 0) for p in pending)
                require(
                    item and used + qty <= item["shipped"],
                    "RETURN_QUANTITY",
                    "These quantities are already in a return or were not delivered.",
                )
            return dict(
                c.execute(
                    db.returns.insert()
                    .values(
                        order_id=order_id,
                        request_key=command.request_key,
                        items=command.items,
                        reason=command.reason,
                    )
                    .returning(db.returns)
                )
                .mappings()
                .one()
            )

    @db.retry_transient_write
    def receive_return(self, actor, return_id, sellable):
        with self.engine.begin() as c:
            require_permission(c, actor, "returns.manage")
            if sellable:
                require_permission(c, actor, "orders.fulfil")
            row = (
                c.execute(select(db.returns).where(db.returns.c.id == return_id).with_for_update())
                .mappings()
                .first()
            )
            require(row, "NOT_FOUND", "Return not found", 404)
            require(row["status"] == "requested", "ALREADY_RECEIVED", "Return was already inspected.")
            for iid, qty in sorted(row["items"].items()):
                item = (
                    c.execute(
                        update(db.order_items)
                        .where(
                            db.order_items.c.id == iid,
                            db.order_items.c.returned + qty <= db.order_items.c.shipped,
                        )
                        .values(returned=db.order_items.c.returned + qty)
                        .returning(db.order_items)
                    )
                    .mappings()
                    .first()
                )
                require(item, "RETURN_QUANTITY", "Return exceeds delivered quantity.")
                if sellable:
                    c.execute(
                        update(db.inventory)
                        .where(db.inventory.c.variant_id == item["variant_id"])
                        .values(on_hand=db.inventory.c.on_hand + qty)
                    )
                    c.execute(
                        db.movements.insert().values(
                            variant_id=item["variant_id"],
                            operation_key=f"return:{return_id}:{iid}",
                            on_hand_delta=qty,
                            reserved_delta=0,
                            reason="Inspected sellable return",
                            actor=actor.owner_id,
                        )
                    )
            c.execute(
                update(db.returns)
                .where(db.returns.c.id == return_id)
                .values(status="received", sellable=sellable)
            )
            audit(c, actor, "return.received", return_id, {"sellable": sellable})
        return {"ok": True}

    def dashboard(self, actor):
        with self.engine.connect() as c:
            require_permission(c, actor, "orders.read")
            paid = c.execute(
                select(func.coalesce(func.sum(db.orders.c.total), 0)).where(
                    db.orders.c.payment_id.is_not(None)
                )
            ).scalar_one()
            refunded = c.execute(
                select(func.coalesce(func.sum(db.refunds.c.amount), 0)).where(
                    db.refunds.c.status == "succeeded"
                )
            ).scalar_one()
            return {
                "paused": c.execute(
                    select(db.settings_table.c.value).where(db.settings_table.c.key == "commerce")
                )
                .scalar_one()
                .get("paused", False),
                "captured": paid,
                "refunded": refunded,
                "net": paid - refunded,
                "orders": c.execute(select(func.count()).select_from(db.orders)).scalar_one(),
                "low_stock": c.execute(
                    select(func.count())
                    .select_from(db.inventory)
                    .where(db.inventory.c.on_hand - db.inventory.c.reserved < 3)
                ).scalar_one(),
                "exceptions": [
                    dict(r)
                    for r in c.execute(
                        select(db.jobs)
                        .where(db.jobs.c.status.in_(["failed", "unknown"]))
                        .order_by(db.jobs.c.created_at.desc())
                        .limit(30)
                    ).mappings()
                ],
                "audit": [
                    dict(r)
                    for r in c.execute(
                        select(db.audit).order_by(db.audit.c.created_at.desc()).limit(30)
                    ).mappings()
                ],
            }
