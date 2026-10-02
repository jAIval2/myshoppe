"""Idempotent DEVELOPMENT catalogue. Never seed demo stock into production."""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from . import db
from .settings import settings

WOMEN = [
    ("Fluid linen shirt", "tops", 295000),
    ("Sculpted cotton dress", "dresses", 595000),
    ("Relaxed wool blazer", "outerwear", 795000),
    ("Wide-leg tailored trousers", "trousers", 435000),
    ("Fine knit cardigan", "knitwear", 395000),
    ("Satin midi skirt", "skirts", 355000),
    ("Structured poplin shirt", "tops", 295000),
    ("Longline linen waistcoat", "co-ords", 495000),
]
HOME = [
    ("Washed linen duvet cover", "duvet-covers", 895000),
    ("Cotton percale sheet", "bedsheets", 435000),
    ("Linen pillowcase pair", "pillowcases", 295000),
    ("Textured cotton throw", "throws", 595000),
    ("Quilted cotton bedspread", "quilts", 795000),
    ("Cotton cushion cover", "cushion-covers", 195000),
    ("Lightweight duvet insert", "duvet-inserts", 695000),
    ("Striped linen duvet cover", "duvet-covers", 945000),
]


def seed():
    if settings.environment != "development":
        raise RuntimeError("Demo seed is development-only")
    with db.engine.begin() as c:
        c.execute(
            insert(db.settings_table)
            .values(
                key="commerce",
                value={
                    "pin_prefixes": [str(n) for n in range(1, 10)],
                    "shipping_paise": 15000,
                    "free_shipping_above": 500000,
                    "tax_note": "Development prices; merchant tax configuration required before launch",
                    "live_approved": False,
                    "paused": False,
                },
            )
            .on_conflict_do_nothing()
        )
        for role in ("owner", "merchandiser", "fulfilment", "support", "customer"):
            email = f"{role}@myshoppe.local"
            uid = c.execute(select(db.profiles.c.id).where(db.profiles.c.email == email)).scalar_one_or_none()
            if not uid:
                uid = c.execute(
                    db.profiles.insert().values(email=email, name=role.title()).returning(db.profiles.c.id)
                ).scalar_one()
            if role != "customer":
                c.execute(
                    insert(db.staff).values(user_id=uid, role=role, active=True).on_conflict_do_nothing()
                )
        for department, source, count in [("women", WOMEN, 24), ("home", HOME, 16)]:
            for i in range(count):
                title, category, price = source[i % len(source)]
                edition = ["", " — Natural", " — Studio"][i // len(source)]
                slug = title.lower().replace(" ", "-") + (f"-{i}" if i >= len(source) else "")
                if c.execute(select(db.products.c.id).where(db.products.c.slug == slug)).first():
                    continue
                prefix, n = ("woman", 6) if department == "women" else ("home", 4)
                media = [
                    {
                        "src": f"/media/{prefix}-{(i + j) % n + 1}.jpg",
                        "alt": f"Editorial reference for {title}, view {j + 1}",
                        "role": role,
                    }
                    for j, role in enumerate(
                        ["lead", "continuation", "continuation", "continuation", "continuation", "cutout"]
                    )
                ]
                details = (
                    {
                        "fit": "Relaxed silhouette",
                        "measurements": "Model imagery is editorial reference. Replace with verified garment measurements.",
                        "origin": "Merchant confirmation required",
                    }
                    if department == "women"
                    else {
                        "dimensions": "Queen 230 × 250 cm; King 260 × 280 cm",
                        "contents": "1 cover; insert and pillowcases sold separately",
                        "type": "Duvet cover" if "cover" in category else title,
                        "origin": "Merchant confirmation required",
                    }
                )
                pid = c.execute(
                    db.products.insert()
                    .values(
                        slug=slug,
                        title=title + edition,
                        department=department,
                        category=category,
                        description="A considered everyday piece with a soft, natural texture and a quietly distinctive silhouette. Designed to be layered, lived in, and returned to season after season.",
                        material="100% linen" if "linen" in title else "100% cotton",
                        care="Gentle wash at 30°C. Wash with similar colours. Line dry. Cool iron.",
                        details=details,
                        media=media,
                        relations={},
                        status="published",
                    )
                    .returning(db.products.c.id)
                ).scalar_one()
                for j, (colour, hex_value) in enumerate([("Ecru", "#d9d0bd"), ("Black", "#262522")]):
                    for k, size in enumerate(
                        ["XS", "S", "M", "L"] if department == "women" else ["Queen", "King"]
                    ):
                        vid = c.execute(
                            db.variants.insert()
                            .values(
                                product_id=pid,
                                sku=f"{department[:1].upper()}-{i + 1:03}-{j}{k}",
                                colour=colour,
                                colour_hex=hex_value,
                                size=size,
                                dimensions=None
                                if department == "women"
                                else ("230 × 250 cm" if k == 0 else "260 × 280 cm"),
                                price_paise=price + (k * 50000 if department == "home" else 0),
                                compare_at_paise=price + 100000 if i in (1, 4) else None,
                            )
                            .returning(db.variants.c.id)
                        ).scalar_one()
                        c.execute(
                            db.inventory.insert().values(
                                variant_id=vid,
                                on_hand=0 if i == 3 and k == 0 else 2 if i == 2 else 12,
                                reserved=0,
                            )
                        )
            if not c.execute(
                select(db.campaigns.c.id).where(db.campaigns.c.department == department)
            ).first():
                target = f"/collections/{department}-new-in"
                lead = f"/media/campaign-{department}.jpg"
                prefix = "woman" if department == "women" else "home"
                blocks = [
                    {
                        "type": "hero",
                        "src": lead,
                        "title": "THE NEW\nPERSPECTIVE"
                        if department == "women"
                        else "A QUIETER\nKIND OF LUXURY",
                        "subtitle": "THE OCTOBER EDIT / 2026",
                        "tone": "light",
                        "layout": "full",
                        "target": target,
                    },
                    {
                        "type": "video",
                        "src": "/media/campaign.mp4",
                        "poster": lead,
                        "title": "In your own rhythm.",
                        "tone": "light",
                        "layout": "full",
                        "target": target,
                    },
                    {
                        "type": "poster",
                        "src": f"/media/{prefix}-2.jpg",
                        "mobile_src": f"/media/{prefix}-3.jpg",
                        "title": "THE ART\nOF EVERYDAY",
                        "subtitle": "A STUDY IN TEXTURE AND FORM",
                        "tone": "dark",
                        "layout": "split",
                        "target": target,
                    },
                    {
                        "type": "poster",
                        "src": f"/media/{prefix}-4.jpg",
                        "title": "Less, but\nwith feeling.",
                        "subtitle": "CONSIDERED PIECES. PERSONAL EXPRESSION.",
                        "tone": "dark",
                        "layout": "inset",
                        "target": target,
                    },
                    {
                        "type": "collection-entry",
                        "src": "",
                        "title": "THE NEW",
                        "tone": "dark",
                        "layout": "full",
                        "target": target,
                    },
                ]
                c.execute(
                    db.campaigns.insert().values(
                        department=department, revision=1, content={"blocks": blocks}, published=True
                    )
                )
    print("Seeded 40 development products, two campaigns and five development accounts")


if __name__ == "__main__":
    seed()
