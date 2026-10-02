import io
import secrets
from pathlib import Path
from PIL import Image, ImageOps
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from app import db
from app.errors import require
from app.identity import audit, rate_limit, require_permission

MEDIA_ROOT = Path(__file__).resolve().parents[4] / "web/public/uploads"


class OperationsService:
    def __init__(self, engine):
        self.engine = engine

    def submit_support(self, actor, command):
        with self.engine.begin() as c:
            rate_limit(c, f"support:{actor.owner_id}", 5)
            c.execute(
                insert(db.support)
                .values(owner_id=actor.owner_id, **command.model_dump())
                .on_conflict_do_nothing()
            )
        return {"ok": True}

    def support_list(self, actor):
        with self.engine.connect() as c:
            require_permission(c, actor, "support.manage")
            return [
                dict(r)
                for r in c.execute(
                    select(db.support).order_by(db.support.c.created_at.desc()).limit(100)
                ).mappings()
            ]

    def image(self, actor, raw):
        with self.engine.connect() as c:
            require_permission(c, actor, "catalog.write")
        require(len(raw) <= 10_000_000, "MEDIA_TOO_LARGE", "Images must be smaller than 10 MB.", 413)
        Image.MAX_IMAGE_PIXELS = 25_000_000
        try:
            image = Image.open(io.BytesIO(raw))
            require(
                image.width * image.height <= 25_000_000, "IMAGE_DIMENSIONS", "Image has too many pixels", 422
            )
            image = ImageOps.exif_transpose(image).convert("RGB")
            image.thumbnail((2200, 2200))
        except (OSError, Image.DecompressionBombError):
            require(False, "INVALID_IMAGE", "Use a valid JPEG, PNG or WebP image.", 422)
        MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
        name = secrets.token_hex(16) + ".webp"
        image.save(MEDIA_ROOT / name, "WEBP", quality=85)
        return {"src": f"/uploads/{name}", "width": image.width, "height": image.height}

    def pause(self, actor, paused):
        with self.engine.begin() as c:
            require_permission(c, actor, "staff.manage")
            value = c.execute(
                select(db.settings_table.c.value)
                .where(db.settings_table.c.key == "commerce")
                .with_for_update()
            ).scalar_one()
            c.execute(
                update(db.settings_table)
                .where(db.settings_table.c.key == "commerce")
                .values(value={**value, "paused": paused})
            )
            audit(c, actor, "checkout.paused", "commerce", {"paused": paused})
        return {"ok": True}

    def video(self, actor, raw):
        with self.engine.connect() as c:
            require_permission(c, actor, "content.write")
        require(len(raw) <= 80_000_000, "MEDIA_TOO_LARGE", "Video must be smaller than 80 MB", 413)
        require(len(raw) > 16, "INVALID_VIDEO", "Video is empty", 422)
        from app.features.checkout.service import enqueue

        name = secrets.token_hex(16)
        MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
        private = MEDIA_ROOT.parents[2] / ".local/media-sources"
        private.mkdir(parents=True, exist_ok=True)
        source = private / (name + ".source")
        source.write_bytes(raw)
        with self.engine.begin() as c:
            enqueue(
                c,
                f"video:{name}",
                "media.video",
                {"source": str(source), "destination": str(MEDIA_ROOT / (name + ".mp4"))},
            )
        return {"job_key": f"video:{name}", "src": f"/uploads/{name}.mp4", "poster": f"/uploads/{name}.jpg"}

    def job(self, actor, key):
        with self.engine.connect() as c:
            require_permission(c, actor, "content.write")
            row = (
                c.execute(
                    select(db.jobs.c.status, db.jobs.c.last_error).where(db.jobs.c.operation_key == key)
                )
                .mappings()
                .first()
            )
            require(row, "NOT_FOUND", "Job not found", 404)
            return dict(row)

    def retry(self, actor, job_id):
        with self.engine.begin() as c:
            require_permission(c, actor, "staff.manage")
            job = (
                c.execute(select(db.jobs).where(db.jobs.c.id == job_id).with_for_update()).mappings().first()
            )
            require(job and job["status"] == "failed", "NOT_RETRYABLE", "Only failed jobs can be retried.")
            require(
                job["kind"]
                in {
                    "payment.reconcile",
                    "payment.event",
                    "payment.refund",
                    "cart.clear",
                    "email.order",
                    "media.video",
                },
                "NOT_RETRYABLE",
                "This operation needs manual reconciliation.",
            )
            c.execute(
                update(db.jobs)
                .where(db.jobs.c.id == job_id)
                .values(status="pending", attempts=0, due_at=db.now(), lease_until=None)
            )
            audit(c, actor, "job.retry", job_id)
        return {"ok": True}
