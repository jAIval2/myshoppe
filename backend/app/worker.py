import logging
import time
from datetime import timedelta
from sqlalchemy import select, update, or_, delete
from . import db
from .dependencies import payments
from .settings import settings

logger = logging.getLogger("myshoppe.worker")


def handle(kind, payload):
    if kind == "payment.reconcile":
        return payments.reconcile(payload["order_id"])
    elif kind == "payment.event":
        with db.engine.connect() as c:
            event = c.execute(
                select(db.events.c.payload).where(db.events.c.event_id == payload["event_id"])
            ).scalar_one()
        if event.get("event") not in ("payment.captured", "order.paid"):
            return
        entity = event["payload"]["payment"]["entity"]
        verified = payments.gateway.fetch_payment(entity["id"])
        if verified["status"] != "captured":
            raise RuntimeError("Payment is not captured")
        with db.engine.connect() as c:
            order_id = c.execute(
                select(db.orders.c.id).where(db.orders.c.provider_order_id == verified["order_id"])
            ).scalar_one()
        payments.capture(
            order_id, verified["id"], verified["amount"], verified["currency"], verified["order_id"]
        )
    elif kind == "payment.refund":
        with db.engine.begin() as c:
            refund = (
                c.execute(select(db.refunds).where(db.refunds.c.id == payload["refund_id"]).with_for_update())
                .mappings()
                .one()
            )
            if refund["status"] == "succeeded":
                return
            order = c.execute(select(db.orders).where(db.orders.c.id == refund["order_id"])).mappings().one()
            c.execute(update(db.refunds).where(db.refunds.c.id == refund["id"]).values(status="unknown"))
        if order["payment_mode"] == "development" and settings.environment == "development":
            result = {"id": f"dev_{refund['id']}", "status": "processed"}
        elif refund["status"] in ("unknown", "processing"):
            result = payments.gateway.find_refund(order["payment_id"], refund["id"])
            if not result:
                raise RuntimeError("Refund remains unknown; reconcile with provider, never blindly retry")
        else:
            result = payments.gateway.refund(order["payment_id"], refund["amount"], refund["id"])
        if order["payment_mode"] != "development":
            if result["payment_id"] != order["payment_id"] or result["amount"] != refund["amount"]:
                raise RuntimeError("Refund identity or amount mismatch")
        with db.engine.begin() as c:
            c.execute(
                update(db.refunds)
                .where(db.refunds.c.id == refund["id"])
                .values(
                    status="succeeded"
                    if result["status"] == "processed"
                    else "failed"
                    if result["status"] == "failed"
                    else "processing",
                    provider_id=result["id"],
                )
            )
        return result["status"] in ("processed", "failed")
    elif kind == "cart.clear":
        with db.engine.begin() as c:
            version = c.execute(
                select(db.carts.c.version).where(db.carts.c.owner_id == payload["owner_id"]).with_for_update()
            ).scalar_one()
            if version == payload["version"]:
                c.execute(delete(db.cart_items).where(db.cart_items.c.owner_id == payload["owner_id"]))
                c.execute(
                    update(db.carts)
                    .where(db.carts.c.owner_id == payload["owner_id"])
                    .values(version=version + 1)
                )
    elif kind == "email.order":
        from .adapters.email import send_order

        with db.engine.connect() as c:
            order = c.execute(select(db.orders).where(db.orders.c.id == payload["order_id"])).mappings().one()
        send_order(order)
    elif kind == "media.video":
        from .adapters.media import process_video

        process_video(payload["source"], payload["destination"])
    else:
        raise RuntimeError(f"Unsupported job {kind}")


def tick():
    payments.expire()
    with db.engine.begin() as c:
        row = (
            c.execute(
                select(db.jobs)
                .where(
                    or_(
                        db.jobs.c.status == "pending",
                        (db.jobs.c.status == "processing") & (db.jobs.c.lease_until < db.now()),
                    ),
                    db.jobs.c.due_at <= db.now(),
                )
                .order_by(db.jobs.c.created_at)
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            .mappings()
            .first()
        )
        if not row:
            return False
        c.execute(
            update(db.jobs)
            .where(db.jobs.c.id == row["id"])
            .values(
                status="processing", attempts=row["attempts"] + 1, lease_until=db.now() + timedelta(minutes=5)
            )
        )
    try:
        complete = handle(row["kind"], row["payload"])
        values = {
            "status": "pending" if complete is False else "done",
            "last_error": None,
            "attempts": 0,
            "due_at": db.now() + timedelta(seconds=45),
        }
    except Exception as exc:
        values = {
            "status": "failed" if row["attempts"] >= 4 else "pending",
            "last_error": str(exc)[:500],
            "due_at": db.now() + timedelta(seconds=min(300, 2 ** (row["attempts"] + 2))),
        }
        logger.warning("job_failed id=%s kind=%s", row["id"], row["kind"])
    with db.engine.begin() as c:
        c.execute(update(db.jobs).where(db.jobs.c.id == row["id"]).values(**values, lease_until=None))
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    settings.validate()
    while True:
        try:
            tick()
        except Exception:
            logger.exception("worker_tick_failed")
        time.sleep(2)
