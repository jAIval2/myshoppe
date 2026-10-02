from sqlalchemy import select
from app import db


def hydrate(conn, rows, private=False):
    if not rows:
        return []
    ids = [r["id"] for r in rows]
    variants = (
        conn.execute(
            select(db.variants, db.inventory.c.on_hand, db.inventory.c.reserved)
            .join(db.inventory)
            .where(db.variants.c.product_id.in_(ids), db.variants.c.active)
        )
        .mappings()
        .all()
    )
    grouped = {key: [] for key in ids}
    for v in variants:
        item = dict(v)
        item["available"] = item["on_hand"] - item["reserved"]
        if not private:
            item["on_hand"], item["reserved"] = 0, 0
        grouped[item["product_id"]].append(item)
    return [
        {
            **dict(r),
            "variants": grouped[r["id"]],
            "price_paise": min((v["price_paise"] for v in grouped[r["id"]]), default=0),
        }
        for r in rows
    ]
