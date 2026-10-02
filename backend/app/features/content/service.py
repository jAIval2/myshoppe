from sqlalchemy import select, update, func
from app import db
from app.identity import require_permission, audit
from app.errors import require
from pathlib import Path


class ContentService:
    def __init__(self, engine):
        self.engine = engine

    def campaign(self, department):
        with self.engine.connect() as c:
            row = (
                c.execute(
                    select(db.campaigns).where(
                        db.campaigns.c.department == department, db.campaigns.c.published
                    )
                )
                .mappings()
                .first()
            )
            require(row, "NOT_FOUND", "Campaign not found", 404)
            return dict(row)

    def history(self, actor, department):
        with self.engine.connect() as c:
            require_permission(c, actor, "content.write")
            return [
                dict(row)
                for row in c.execute(
                    select(db.campaigns)
                    .where(db.campaigns.c.department == department)
                    .order_by(db.campaigns.c.revision.desc())
                ).mappings()
            ]

    def save(self, actor, department, command):
        require(department in ("women", "home"), "INVALID_DEPARTMENT", "Choose Women or Home", 422)
        require(
            all(b.target.startswith(f"/collections/{department}-") for b in command.blocks),
            "INVALID_TARGET",
            "Campaign targets must belong to this department",
            422,
        )
        with self.engine.begin() as c:
            require_permission(c, actor, "content.write")
            c.execute(
                select(db.settings_table).where(db.settings_table.c.key == "commerce").with_for_update()
            ).one()
            latest = (
                c.execute(
                    select(func.max(db.campaigns.c.revision)).where(db.campaigns.c.department == department)
                ).scalar_one()
                or 0
            )
            require(
                latest == command.expected_revision,
                "STALE_VERSION",
                "A newer revision exists. Reload before saving.",
            )
            row = (
                c.execute(
                    db.campaigns.insert()
                    .values(
                        department=department,
                        revision=latest + 1,
                        content={"blocks": [b.model_dump() for b in command.blocks]},
                        published=False,
                    )
                    .returning(db.campaigns)
                )
                .mappings()
                .one()
            )
            audit(c, actor, "campaign.saved", row["id"])
            return dict(row)

    def publish(self, actor, revision_id):
        with self.engine.begin() as c:
            require_permission(c, actor, "content.write")
            c.execute(
                select(db.settings_table).where(db.settings_table.c.key == "commerce").with_for_update()
            ).one()
            row = c.execute(select(db.campaigns).where(db.campaigns.c.id == revision_id)).mappings().first()
            require(row, "NOT_FOUND", "Revision not found", 404)
            public = Path(__file__).resolve().parents[4] / "web/public"
            for block in row["content"]["blocks"]:
                for field in ("src", "poster", "mobile_src"):
                    if not block.get(field):
                        continue
                    path = (public / block[field].lstrip("/")).resolve()
                    require(
                        path.is_relative_to(public.resolve()) and path.is_file(),
                        "MEDIA_NOT_READY",
                        "Upload and process every campaign asset before publishing.",
                        422,
                    )
            c.execute(
                update(db.campaigns)
                .where(db.campaigns.c.department == row["department"])
                .values(published=False)
            )
            c.execute(update(db.campaigns).where(db.campaigns.c.id == revision_id).values(published=True))
            audit(c, actor, "campaign.published", revision_id)
        return self.campaign(row["department"])
