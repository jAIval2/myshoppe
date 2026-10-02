from sqlalchemy import select
from app import db


def lines(conn, owner):
    query = (
        select(
            db.cart_items.c.quantity,
            db.variants,
            db.products.c.title,
            db.products.c.slug,
            db.products.c.status,
            db.products.c.media,
            db.inventory.c.on_hand,
            db.inventory.c.reserved,
        )
        .select_from(db.cart_items.join(db.variants).join(db.products).join(db.inventory))
        .where(db.cart_items.c.owner_id == owner)
        .order_by(db.variants.c.id)
    )
    return [dict(row) for row in conn.execute(query).mappings()]
