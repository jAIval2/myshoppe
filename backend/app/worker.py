import argparse
import logging
import secrets
import signal
import time
from uuid import UUID
from datetime import timedelta

from sqlalchemy import func, or_, select, update, delete, text

from . import db
from .dependencies import payments
from .settings import settings

logger = logging.getLogger("myshoppe.worker")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
LANE_KINDS = {
    "commerce": ("payment.reconcile", "payment.event", "payment.refund", "cart.clear", "email.order"),
    "media": ("media.video",),
}
stopping = False


def handle(kind, payload):
    if kind == "payment.reconcile":
        return payments.reconcile(payload["order_id"])
    elif kind == "payment.event":
        with db.engine.connect() as c:
            event = c.execute(
                select(db.events.c.payload).where(db.events.c.event_id == payload["event_id"])
            ).scalar_one()
        event_type = event.get("event")
        if event_type not in ("payment.captured", "order.paid"):
            return
        body = event.get("payload") or {}
        payment_entity = (body.get("payment") or {}).get("entity") or {}
        order_entity = (body.get("order") or {}).get("entity") or {}
        if not payment_entity.get("id"):
            # order.paid officially contains both entities. Keep order-only
            # recovery for older/provider-specific payloads via verified lookup.
            provider_order_id = order_entity.get("id")
            if event_type != "order.paid" or not provider_order_id:
                raise ValueError("Captured-payment webhook has no payment identifier")
            with db.engine.connect() as c:
                order_id = None
                receipt = order_entity.get("receipt")
                if receipt:
                    try:
                        receipt_id = str(UUID(receipt))
                    except (ValueError, TypeError, AttributeError):
                        receipt_id = None
                    if receipt_id:
                        order_id = c.execute(
                            select(db.orders.c.id).where(db.orders.c.id == receipt_id)
                        ).scalar_one_or_none()
                if not order_id:
                    order_id = c.execute(
                        select(db.orders.c.id).where(db.orders.c.provider_order_id == provider_order_id)
                    ).scalar_one_or_none()
            if not order_id:
                raise RuntimeError("Paid webhook order is not mapped yet; retry after order reconciliation")
            return payments.reconcile(order_id)

        verified = payments.gateway.fetch_payment(payment_entity["id"])
        if verified.get("status") != "captured" or not verified.get("order_id"):
            raise RuntimeError("Provider payment is not a captured order payment")
        with db.engine.connect() as c:
            order_id = c.execute(
                select(db.orders.c.id).where(db.orders.c.provider_order_id == verified["order_id"])
            ).scalar_one_or_none()
        if not order_id:
            raise RuntimeError("Captured payment order is not mapped yet; retry reconciliation")
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
            ).scalar_one_or_none()
            if version is not None and version == payload["version"]:
                c.execute(delete(db.cart_items).where(db.cart_items.c.owner_id == payload["owner_id"]))
                c.execute(
                    update(db.carts)
                    .where(db.carts.c.owner_id == payload["owner_id"])
                    .values(version=version + 1, updated_at=func.now())
                )
    elif kind == "email.order":
        from .adapters.email import send_order

        with db.engine.connect() as c:
            order = c.execute(select(db.orders).where(db.orders.c.id == payload["order_id"])).mappings().one()
        send_order(order)
    elif kind == "media.video":
        from .adapters.media import process_video
        if "source_key" in payload:
            import tempfile
            from pathlib import Path

            from .adapters.storage import storage

            object_store = storage()
            with tempfile.TemporaryDirectory(prefix="myshoppe-video-") as scratch:
                source = Path(scratch) / "source.video"
                destination = Path(scratch) / "processed.mp4"
                with source.open("wb") as stream:
                    object_store.download(payload["source_key"], stream)
                process_video(str(source), str(destination))
                poster = destination.with_suffix(".jpg")
                with destination.open("rb") as stream:
                    object_store.put(payload["destination_key"], stream, destination.stat().st_size, "video/mp4")
                with poster.open("rb") as stream:
                    object_store.put(payload["poster_key"], stream, poster.stat().st_size, "image/jpeg")
                object_store.delete(payload["source_key"])
        else:
            process_video(payload["source"], payload["destination"])
    else:
        raise RuntimeError(f"Unsupported job {kind}")


def claim(lane):
    token = secrets.token_urlsafe(24)
    with db.engine.begin() as c:
        row = (
            c.execute(
                select(db.jobs)
                .where(
                    db.jobs.c.kind.in_(LANE_KINDS[lane]),
                    or_(
                        db.jobs.c.status == "pending",
                        (db.jobs.c.status == "processing") & (db.jobs.c.lease_until < func.now()),
                    ),
                    db.jobs.c.due_at <= func.now(),
                )
                .order_by(db.jobs.c.created_at)
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            .mappings()
            .first()
        )
        if not row:
            return None
        c.execute(
            update(db.jobs)
            .where(db.jobs.c.id == row["id"])
            .values(
                status="processing",
                attempts=row["attempts"] + 1,
                claim_token=token,
                lease_until=func.now() + timedelta(minutes=5),
            )
        )
    return row, token


def tick(lane="commerce"):
    claimed = claim(lane)
    if not claimed:
        return False
    row, token = claimed
    try:
        complete = handle(row["kind"], row["payload"])
        values = {
            "status": "pending" if complete is False else "done",
            "last_error": None,
            "attempts": 0,
            "due_at": func.now() + timedelta(seconds=45),
            "completed_at": None if complete is False else func.now(),
        }
    except Exception as exc:
        values = {
            "status": "failed" if row["attempts"] >= 4 else "pending",
            "last_error": str(exc)[:500],
            "due_at": func.now() + timedelta(seconds=min(300, 2 ** (row["attempts"] + 2))),
            "completed_at": None,
        }
        logger.warning("job_failed id=%s kind=%s", row["id"], row["kind"])
    with db.engine.begin() as c:
        result = c.execute(
            update(db.jobs)
            .where(
                db.jobs.c.id == row["id"],
                db.jobs.c.claim_token == token,
                db.jobs.c.status == "processing",
            )
            .values(**values, lease_until=None, claim_token=None)
        )
    if not result.rowcount:
        logger.warning("stale_job_claim id=%s kind=%s", row["id"], row["kind"])
    return True


def cleanup_retention(batch_size=500):
    """Bounded, repeatable cleanup. Audit and stock ledgers remain untouched."""
    counts = {}
    with db.engine.begin() as c:
        counts["sessions"] = c.execute(text("""
            DELETE FROM sessions WHERE token_hash IN (
              SELECT token_hash FROM sessions
              WHERE expires_at < now() - interval '24 hours'
              ORDER BY expires_at LIMIT :batch FOR UPDATE SKIP LOCKED
            )
        """), {"batch": batch_size}).rowcount
        counts["rate_limits"] = c.execute(text("""
            DELETE FROM rate_limits WHERE key IN (
              SELECT key FROM rate_limits
              WHERE window < floor(extract(epoch from now() - interval '24 hours') / 60)
              ORDER BY window LIMIT :batch FOR UPDATE SKIP LOCKED
            )
        """), {"batch": batch_size}).rowcount
        counts["jobs"] = c.execute(text("""
            UPDATE outbox_jobs SET payload = '{}'::jsonb
            WHERE id IN (
              SELECT id FROM outbox_jobs
              WHERE status = 'done' AND completed_at < now() - interval '30 days'
                AND payload <> '{}'::jsonb
              ORDER BY completed_at LIMIT :batch FOR UPDATE SKIP LOCKED
            )
        """), {"batch": batch_size}).rowcount
        counts["webhooks"] = c.execute(text("""
            UPDATE webhook_events SET payload = '{}'::jsonb
            WHERE event_id IN (
              SELECT e.event_id FROM webhook_events e
              JOIN outbox_jobs j ON j.operation_key = 'webhook:' || e.event_id
              WHERE e.created_at < now() - interval '90 days'
                AND j.status = 'done' AND j.completed_at < now() - interval '30 days'
                AND e.payload <> '{}'::jsonb
              ORDER BY e.created_at LIMIT :batch FOR UPDATE OF e SKIP LOCKED
            )
        """), {"batch": batch_size}).rowcount
        owners = c.execute(text("""
            SELECT c.owner_id FROM carts c
            WHERE c.updated_at < now() - interval '30 days'
              AND NOT EXISTS (SELECT 1 FROM sessions s WHERE s.owner_id=c.owner_id AND s.expires_at > now())
              AND NOT EXISTS (SELECT 1 FROM profiles p WHERE p.id::text=c.owner_id)
              AND NOT EXISTS (SELECT 1 FROM orders o WHERE o.owner_id=c.owner_id
                              AND o.status='pending' AND o.expires_at > now())
            ORDER BY c.updated_at LIMIT :batch FOR UPDATE OF c SKIP LOCKED
        """), {"batch": batch_size}).scalars().all()
        counts["guest_carts"] = 0
        if owners:
            c.execute(delete(db.cart_items).where(db.cart_items.c.owner_id.in_(owners)))
            c.execute(delete(db.saved).where(db.saved.c.owner_id.in_(owners)))
            counts["guest_carts"] = c.execute(
                delete(db.carts).where(db.carts.c.owner_id.in_(owners))
            ).rowcount
    return counts


def run(lane):
    global stopping
    settings.validate()
    signal.signal(signal.SIGTERM, lambda *_: setattr_signal())
    if settings.db_role != lane:
        raise RuntimeError(f"Set DB_ROLE={lane} for the {lane} worker connection budget")
    next_expiry = 0.0
    next_retention = 0.0
    idle = 0.1
    while not stopping:
        if lane == "commerce" and time.monotonic() >= next_expiry:
            try:
                for _ in range(10):
                    if payments.expire() < 100:
                        break
            except Exception:
                logger.exception("reservation_expiry_failed")
            next_expiry = time.monotonic() + 30
        if lane == "commerce" and time.monotonic() >= next_retention:
            try:
                counts = cleanup_retention()
                logger.info("retention_completed rows=%s", counts)
            except Exception:
                logger.exception("retention_failed")
            next_retention = time.monotonic() + 3600
        try:
            worked = tick(lane)
        except Exception:
            logger.exception("worker_tick_failed lane=%s", lane)
            worked = False
        if worked:
            idle = 0.1
        else:
            time.sleep(idle)
            idle = min(2.0, idle * 2)


def setattr_signal():
    global stopping
    stopping = True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lane", choices=tuple(LANE_KINDS), default="commerce")
    run(parser.parse_args().lane)
