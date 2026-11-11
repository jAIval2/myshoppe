import io
from uuid import UUID
from sqlalchemy import select, func
from PIL import Image, ImageOps, UnidentifiedImageError
from app import db
from app.errors import require, DomainError
from app.identity import require_permission, rate_limit, audit
from .schemas import Design

FABRICS = {
    f"fabric-{x}"
    for x in (
        "mocha",
        "pistachio",
        "ivory",
        "rose",
        "midnight",
        "clay",
        "sage",
        "champagne",
        "charcoal",
        "marigold",
    )
}
SAMPLES = {"sample", "reference-neckline", "reference-sleeves", "reference-hem", "reference-dupatta"}
LACES = {f"lace-{x}" for x in ("scallop", "fine", "floral", "geometric", "pearl", "leaf")}


class BespokeService:
    def __init__(self, engine):
        self.engine = engine

    def _row(self, c, actor, design_id, admin=False, lock=False):
        query = select(db.bespoke_designs).where(db.bespoke_designs.c.id == design_id)
        if admin:
            require_permission(c, actor, "bespoke.manage")
        else:
            query = query.where(db.bespoke_designs.c.owner_id == actor.owner_id)
        row = c.execute(query.with_for_update() if lock else query).mappings().first()
        require(row and (not admin or row["status"] != "draft"), "NOT_FOUND", "Design not found.", 404)
        return dict(row)

    def list(self, actor, admin=False):
        with self.engine.connect() as c:
            if admin:
                require_permission(c, actor, "bespoke.manage")
            q = select(db.bespoke_designs).order_by(db.bespoke_designs.c.updated_at.desc()).limit(100)
            q = (
                q.where(db.bespoke_designs.c.status != "draft")
                if admin
                else q.where(db.bespoke_designs.c.owner_id == actor.owner_id)
            )
            return [dict(r) for r in c.execute(q).mappings()]

    def get(self, actor, design_id, admin=False):
        with self.engine.connect() as c:
            return self._row(c, actor, design_id, admin)

    def create(self, actor):
        with self.engine.begin() as c:
            rate_limit(c, f"bespoke-create:{actor.owner_id}", 10)
            return dict(
                c.execute(
                    db.bespoke_designs.insert()
                    .values(owner_id=actor.owner_id, design=Design().model_dump(mode="json"))
                    .returning(db.bespoke_designs)
                )
                .mappings()
                .one()
            )

    def _write(self, c, actor, row, expected, values, event):
        require(
            row["version"] == expected,
            "STALE_VERSION",
            "This brief changed in another session. Reload it before saving.",
        )
        snapshot = {k: row[k] for k in ("version", "status", "design", "review", "agreement")}
        snapshot.update(event=event, at=db.now().isoformat())
        values.update(version=row["version"] + 1, updated_at=db.now(), history=[*row["history"], snapshot])
        result = (
            c.execute(
                db.bespoke_designs.update()
                .where(db.bespoke_designs.c.id == row["id"])
                .values(**values)
                .returning(db.bespoke_designs)
            )
            .mappings()
            .one()
        )
        audit(c, actor, f"bespoke.{event}", row["id"], {"version": result["version"]})
        return dict(result)

    def save(self, actor, design_id, command):
        d = command.design.model_dump(mode="json")
        require(not d["fabric"] or d["fabric"] in FABRICS, "MATERIAL", "Choose a listed fabric.", 422)
        require(set(d["laces"]) <= LACES, "MATERIAL", "Choose listed lace options.", 422)
        require(len(set(d["laces"])) == len(d["laces"]), "MATERIAL", "Remove duplicate lace options.", 422)
        require(
            (d["lace_choice"] == "selected") == bool(d["laces"]), "MATERIAL", "Confirm your lace choice.", 422
        )
        with self.engine.begin() as c:
            row = self._row(c, actor, design_id, lock=True)
            ids = [r["asset_id"] for r in d["references"] if r["asset_id"] not in SAMPLES] + (
                [d["voice_id"]] if d["voice_id"] else []
            )
            try:
                ids = [str(UUID(x)) for x in ids]
            except ValueError:
                raise DomainError("REFERENCE", "Invalid reference.", 422)
            assets = {
                r["id"]: r["content_type"]
                for r in c.execute(
                    select(db.bespoke_assets.c.id, db.bespoke_assets.c.content_type).where(
                        db.bespoke_assets.c.design_id == design_id, db.bespoke_assets.c.id.in_(ids)
                    )
                ).mappings()
            }
            require(set(ids) <= assets.keys(), "REFERENCE", "Reference does not belong to this design.", 422)
            require(
                all(
                    r["asset_id"] in SAMPLES or assets.get(r["asset_id"], "").startswith("image/")
                    for r in d["references"]
                ),
                "REFERENCE",
                "Choose an image reference.",
                422,
            )
            require(
                not d["voice_id"] or assets.get(d["voice_id"], "").startswith("audio/"),
                "REFERENCE",
                "Choose an audio reference.",
                422,
            )
            if d == row["design"]:
                require(
                    row["version"] == command.expected_version, "STALE_VERSION", "Reload the updated brief."
                )
                return row
            return self._write(
                c,
                actor,
                row,
                command.expected_version,
                {"design": d, "status": "draft", "agreement": None, "review": {}},
                "edited",
            )

    def action(self, actor, design_id, command, admin=False):
        with self.engine.begin() as c:
            row = self._row(c, actor, design_id, admin, True)
            a, d = command.action, row["design"]
            require(
                (a in ("review", "ready")) == admin, "FORBIDDEN", "This action is not available here.", 403
            )
            if a == "submit":
                require(row["status"] == "draft", "STATE", "Only a draft can be submitted.")
                require(
                    d.get("fabric")
                    and d.get("lace_choice")
                    and d.get("name", "").strip()
                    and d.get("vision", "").strip()
                    and d.get("silhouette"),
                    "INCOMPLETE",
                    "Choose materials and add your name, silhouette and design idea.",
                    422,
                )
                values = {"status": "submitted"}
            elif a == "review":
                require(
                    row["status"] in ("submitted", "reviewing", "agreed", "ready"),
                    "STATE",
                    "Wait for the customer to submit this design.",
                )
                require(command.instructions.strip(), "INCOMPLETE", "Add stitching instructions.", 422)
                values = {
                    "status": "reviewing",
                    "agreement": None,
                    "review": {
                        "instructions": command.instructions,
                        "questions": command.questions,
                        "materials": command.material_confirmation,
                        "measurements": command.measurement_confirmation,
                        "owner": actor.user_id,
                        "reviewed_by": c.scalar(
                            select(db.profiles.c.name).where(db.profiles.c.id == actor.user_id)
                        )
                        or "Boutique owner",
                        "at": db.now().isoformat(),
                    },
                }
            elif a == "agree":
                r = row["review"]
                require(
                    row["status"] == "reviewing"
                    and r.get("instructions")
                    and r.get("materials", "").strip()
                    and r.get("measurements", "").strip()
                    and not r.get("questions", "").strip(),
                    "INCOMPLETE",
                    "The boutique must confirm materials and fit and resolve open questions before agreement.",
                )
                values = {
                    "status": "agreed",
                    "agreement": {"version": row["version"], "at": db.now().isoformat(), "name": d["name"]},
                }
            else:
                require(
                    row["status"] == "agreed" and row["agreement"],
                    "AGREEMENT",
                    "Customer agreement is required before handoff.",
                )
                values = {"status": "ready"}
            return self._write(c, actor, row, command.expected_version, values, a)

    def upload(self, actor, design_id, data, kind):
        require(0 < len(data) <= 5_000_000, "FILE_SIZE", "Use a file under 5 MB.", 422)
        if kind.startswith("image/"):
            try:
                with Image.open(io.BytesIO(data)) as im:
                    require(
                        im.format in ("JPEG", "PNG", "WEBP") and im.width * im.height <= 25_000_000,
                        "IMAGE",
                        "Use a JPG, PNG or WebP under 25 megapixels.",
                        422,
                    )
                    im = ImageOps.exif_transpose(im).convert("RGB")
                    im.thumbnail((1600, 1600))
                    out = io.BytesIO()
                    im.save(out, "WEBP", quality=85)
                    data, kind = out.getvalue(), "image/webp"
            except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
                raise DomainError("IMAGE", "The image could not be read.", 422)
        else:
            kind = kind.split(";")[0]
            valid = (
                (kind == "audio/webm" and data.startswith(b"\x1aE\xdf\xa3"))
                or (kind == "audio/ogg" and data.startswith(b"OggS"))
                or (kind == "audio/mp4" and data[4:8] == b"ftyp")
            )
            require(valid, "AUDIO", "Use a browser-recorded WebM, Ogg or MP4 voice note.", 422)
        with self.engine.begin() as c:
            self._row(c, actor, design_id, lock=True)
            rate_limit(c, f"bespoke-upload:{actor.owner_id}", 15)
            count = c.scalar(
                select(func.count())
                .select_from(db.bespoke_assets)
                .where(db.bespoke_assets.c.design_id == design_id)
            )
            require(count < 30, "ASSET_LIMIT", "This design has reached its upload limit (30 files).", 422)
            return dict(
                c.execute(
                    db.bespoke_assets.insert()
                    .values(design_id=design_id, content_type=kind, data=data)
                    .returning(db.bespoke_assets.c.id)
                )
                .mappings()
                .one()
            )

    def asset(self, actor, asset_id):
        with self.engine.connect() as c:
            row = (
                c.execute(select(db.bespoke_assets).where(db.bespoke_assets.c.id == asset_id))
                .mappings()
                .first()
            )
            require(row, "NOT_FOUND", "Reference not found.", 404)
            design = (
                c.execute(select(db.bespoke_designs).where(db.bespoke_designs.c.id == row["design_id"]))
                .mappings()
                .one()
            )
            if design["owner_id"] != actor.owner_id:
                require_permission(c, actor, "bespoke.manage")
                require(design["status"] != "draft", "NOT_FOUND", "Reference not found.", 404)
            return dict(row)
