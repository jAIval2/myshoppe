import io
import secrets
import shutil
from pathlib import Path
from PIL import Image, ImageOps
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from app import db
from app.errors import require
from app.identity import audit, rate_limit, require_permission
from app.settings import settings
from app.adapters.storage import storage

MEDIA_ROOT = Path(__file__).resolve().parents[4] / "web/public/uploads"


class OperationsService:
    def __init__(self, engine):
        self.engine = engine

    @db.retry_transient_write
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
        stream = io.BytesIO(raw) if isinstance(raw, bytes) else raw
        stream.seek(0, 2)
        size = stream.tell()
        stream.seek(0)
        require(size <= 10_000_000, "MEDIA_TOO_LARGE", "Images must be smaller than 10 MB.", 413)
        Image.MAX_IMAGE_PIXELS = 25_000_000
        try:
            with Image.open(stream) as uploaded:
                require(
                    uploaded.width * uploaded.height <= 25_000_000,
                    "IMAGE_DIMENSIONS",
                    "Image has too many pixels",
                    422,
                )
                image = ImageOps.exif_transpose(uploaded).convert("RGB")
            image.thumbnail((2200, 2200))
        except (OSError, Image.DecompressionBombError):
            require(False, "INVALID_IMAGE", "Use a valid JPEG, PNG or WebP image.", 422)
        name = secrets.token_hex(16) + ".webp"
        if settings.media_storage_mode == "object":
            output = io.BytesIO()
            image.save(output, "WEBP", quality=85)
            output.seek(0, 2)
            size = output.tell()
            output.seek(0)
            src = storage().put(f"products/{name}", output, size, "image/webp")
        else:
            MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
            image.save(MEDIA_ROOT / name, "WEBP", quality=85)
            src = f"/uploads/{name}"
        return {"src": src, "width": image.width, "height": image.height}

    @db.retry_transient_write
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
        stream = io.BytesIO(raw) if isinstance(raw, bytes) else raw
        stream.seek(0, 2)
        size = stream.tell()
        stream.seek(0)
        require(size <= 80_000_000, "MEDIA_TOO_LARGE", "Video must be smaller than 80 MB", 413)
        require(size > 16, "INVALID_VIDEO", "Video is empty", 422)
        from app.features.checkout.service import enqueue

        name = secrets.token_hex(16)
        if settings.media_storage_mode == "object":
            source_key = f"video-sources/{name}.source"
            storage().put(source_key, stream, size, "application/octet-stream")
            payload = {
                "source_key": source_key,
                "destination_key": f"campaign/{name}.mp4",
                "poster_key": f"campaign/{name}.jpg",
            }
            src = storage().public_url(payload["destination_key"])
            poster = storage().public_url(payload["poster_key"])
        else:
            MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
            private = MEDIA_ROOT.parents[2] / ".local/media-sources"
            private.mkdir(parents=True, exist_ok=True)
            source = private / (name + ".source")
            with source.open("xb") as destination:
                shutil.copyfileobj(stream, destination, 1024 * 1024)
            payload = {"source": str(source), "destination": str(MEDIA_ROOT / (name + ".mp4"))}
            src, poster = f"/uploads/{name}.mp4", f"/uploads/{name}.jpg"
        with self.engine.begin() as c:
            enqueue(
                c,
                f"video:{name}",
                "media.video",
                payload,
            )
        return {"job_key": f"video:{name}", "src": src, "poster": poster}

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

    @db.retry_transient_write
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
                .values(status="pending", attempts=0, due_at=func.now(), lease_until=None, claim_token=None)
            )
            audit(c, actor, "job.retry", job_id)
        return {"ok": True}
