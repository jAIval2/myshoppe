import math
from sqlalchemy import select, func, update, or_, exists, literal_column
from app import db
from app.errors import require
from app.identity import require_permission, audit
from app.schemas import Product, ProductPage
from .queries import hydrate


def validate_publish(product):
    roles = [m["role"] for m in product["media"]]
    require(
        "lead" in roles and "cutout" in roles and roles.count("continuation") >= 4,
        "MISSING_MEDIA",
        "Add a lead, four continuation images and a cutout before publishing.",
        422,
    )
    if product["department"] == "home":
        require(
            all(product["details"].get(k) for k in ("dimensions", "contents", "type")),
            "MISSING_DETAILS",
            "Home textiles need dimensions, pack contents and cover/insert type.",
            422,
        )


class CatalogService:
    def __init__(self, engine):
        self.engine = engine

    def list(
        self,
        department=None,
        category=None,
        q=None,
        colour=None,
        size=None,
        material=None,
        available=False,
        sale=False,
        sort="new",
        page=1,
        limit=24,
        actor=None,
    ):
        with self.engine.connect() as c:
            conditions = []
            if actor:
                require_permission(c, actor, "catalog.write")
            else:
                conditions.append(db.products.c.status == "published")
            if department:
                conditions.append(db.products.c.department == department)
            if category:
                conditions.append(db.products.c.category == category)
            if material:
                conditions.append(db.products.c.material.ilike(f"%{material}%"))
            if q:
                document = literal_column(
                    "to_tsvector('english', products.title || ' ' || products.material || ' ' || products.category)"
                )
                conditions.append(
                    or_(
                        document.op("@@")(func.websearch_to_tsquery("english", q)),
                        db.products.c.title.ilike(f"%{q}%"),
                    )
                )
            vconditions = [db.variants.c.product_id == db.products.c.id, db.variants.c.active]
            if colour:
                vconditions.append(db.variants.c.colour == colour)
            if size:
                vconditions.append(db.variants.c.size == size)
            if sale:
                vconditions.append(db.variants.c.compare_at_paise > db.variants.c.price_paise)
            if available:
                vconditions.append(db.inventory.c.on_hand > db.inventory.c.reserved)
            conditions.append(
                exists(select(1).select_from(db.variants.join(db.inventory)).where(*vconditions))
            )
            total = c.execute(select(func.count()).select_from(db.products).where(*conditions)).scalar_one()
            price = (
                select(func.min(db.variants.c.price_paise))
                .where(db.variants.c.product_id == db.products.c.id, db.variants.c.active)
                .scalar_subquery()
            )
            ordering = {
                "price-asc": price.asc(),
                "price-desc": price.desc(),
                "name": db.products.c.title.asc(),
            }.get(sort, db.products.c.created_at.desc())
            rows = (
                c.execute(
                    select(db.products)
                    .where(*conditions)
                    .order_by(ordering, db.products.c.id)
                    .offset((page - 1) * limit)
                    .limit(limit)
                )
                .mappings()
                .all()
            )
            return ProductPage(
                items=[Product.model_validate(p) for p in hydrate(c, rows, bool(actor))],
                total=total,
                page=page,
                pages=max(1, math.ceil(total / limit)),
            )

    def get(self, slug, actor=None):
        with self.engine.connect() as c:
            if actor:
                require_permission(c, actor, "catalog.write")
            conditions = [or_(db.products.c.slug == slug, db.products.c.id.cast(db.Text) == slug)]
            if not actor:
                conditions.append(db.products.c.status == "published")
            row = c.execute(select(db.products).where(*conditions)).mappings().first()
            require(row, "NOT_FOUND", "This product is unavailable.", 404)
            return Product.model_validate(hydrate(c, [row], bool(actor))[0])

    def save(self, actor, command, product_id=None):
        data = command.model_dump(exclude={"variants", "expected_version"})
        with self.engine.begin() as c:
            require_permission(c, actor, "catalog.write")
            if product_id:
                old = (
                    c.execute(select(db.products).where(db.products.c.id == product_id).with_for_update())
                    .mappings()
                    .first()
                )
                require(old, "NOT_FOUND", "Product not found", 404)
                if old["status"] == "published":
                    validate_publish(data)
                require(
                    old["version"] == command.expected_version,
                    "STALE_VERSION",
                    "Another editor changed this product. Reload before saving.",
                )
                c.execute(
                    update(db.products)
                    .where(db.products.c.id == product_id)
                    .values(**data, version=old["version"] + 1)
                )
            else:
                product_id = c.execute(
                    db.products.insert().values(**data).returning(db.products.c.id)
                ).scalar_one()
            current = set(
                c.execute(select(db.variants.c.id).where(db.variants.c.product_id == product_id)).scalars()
            )
            retained = set()
            for variant in command.variants:
                fields = variant.model_dump(exclude={"id"})
                if variant.id:
                    require(
                        variant.id in current,
                        "INVALID_VARIANT",
                        "Variant does not belong to this product",
                        422,
                    )
                    c.execute(
                        update(db.variants)
                        .where(db.variants.c.id == variant.id)
                        .values(**fields, active=True)
                    )
                    retained.add(variant.id)
                else:
                    vid = c.execute(
                        db.variants.insert()
                        .values(**fields, product_id=product_id)
                        .returning(db.variants.c.id)
                    ).scalar_one()
                    c.execute(db.inventory.insert().values(variant_id=vid, on_hand=0, reserved=0))
            if current - retained:
                c.execute(
                    update(db.variants).where(db.variants.c.id.in_(current - retained)).values(active=False)
                )
            audit(c, actor, "product.saved", product_id)
        return self.get(product_id, actor)

    def publish(self, actor, product_id, version, status="published"):
        with self.engine.begin() as c:
            require_permission(c, actor, "catalog.write")
            row = (
                c.execute(select(db.products).where(db.products.c.id == product_id).with_for_update())
                .mappings()
                .first()
            )
            require(row, "NOT_FOUND", "Product not found", 404)
            require(
                row["version"] == version, "STALE_VERSION", "Reload the latest version before publishing."
            )
            if status == "published":
                validate_publish(row)
            c.execute(
                update(db.products)
                .where(db.products.c.id == product_id)
                .values(status=status, version=version + 1)
            )
            audit(c, actor, f"product.{status}", product_id)
        return self.get(product_id, actor)

    def stock(self, actor, command):
        with self.engine.begin() as c:
            require_permission(c, actor, "inventory.write")
            key = f"adjust:{command.request_key}"
            c.execute(
                select(db.inventory).where(db.inventory.c.variant_id == command.variant_id).with_for_update()
            )
            old = (
                c.execute(select(db.movements).where(db.movements.c.operation_key == key)).mappings().first()
            )
            if old:
                require(
                    old["variant_id"] == command.variant_id and old["on_hand_delta"] == command.delta,
                    "KEY_CONFLICT",
                    "Adjustment key already used",
                )
                return {"ok": True}
            row = c.execute(
                update(db.inventory)
                .where(
                    db.inventory.c.variant_id == command.variant_id,
                    db.inventory.c.on_hand + command.delta >= db.inventory.c.reserved,
                )
                .values(on_hand=db.inventory.c.on_hand + command.delta)
                .returning(db.inventory.c.variant_id)
            ).first()
            require(row, "STOCK_CONFLICT", "Adjustment would remove reserved stock or SKU is unavailable.")
            c.execute(
                db.movements.insert().values(
                    variant_id=command.variant_id,
                    operation_key=key,
                    on_hand_delta=command.delta,
                    reserved_delta=0,
                    reason=command.reason,
                    actor=actor.owner_id,
                )
            )
            audit(c, actor, "inventory.adjusted", command.variant_id, {"delta": command.delta})
        return {"ok": True}
