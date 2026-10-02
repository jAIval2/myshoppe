import os

os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL", "postgresql+psycopg://myshoppe:myshoppe@127.0.0.1:55432/myshoppe_test"
)
os.environ["DEV_LOGIN_ENABLED"] = "true"
os.environ["APP_ENV"] = "development"
os.environ["PAYMENT_MODE"] = "development"

import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient
from app import db
from app.main import app
from app.identity import IdentityService, Actor
from app.features.catalog.service import CatalogService
from app.features.checkout.service import CheckoutService
from app.features.payments.service import PaymentService
from app.features.orders.service import OrderService
from app.schemas import ProductInput, StockAdjustment


@pytest.fixture(scope="session", autouse=True)
def schema():
    assert db.engine.url.database == "myshoppe_test", "Tests may only touch the dedicated test database"
    with db.engine.begin() as c:
        db.metadata.create_all(c)
        c.execute(text("CREATE SEQUENCE IF NOT EXISTS order_number_seq START 10001"))
        c.execute(text("ALTER TABLE orders ALTER COLUMN number SET DEFAULT nextval('order_number_seq')"))
        c.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivered_at timestamptz"))
    yield


@pytest.fixture(autouse=True)
def clean_database(schema):
    with db.engine.begin() as c:
        names = ", ".join('"' + t.name + '"' for t in db.metadata.sorted_tables)
        c.execute(text(f"TRUNCATE {names} CASCADE"))
        c.execute(
            db.settings_table.insert().values(
                key="commerce",
                value={
                    "pin_prefixes": ["4"],
                    "shipping_paise": 15000,
                    "free_shipping_above": 500000,
                    "tax_note": "Test configuration",
                    "live_approved": False,
                    "paused": False,
                },
            )
        )
    yield


@pytest.fixture
def owner():
    with db.engine.begin() as c:
        uid = c.execute(
            db.profiles.insert()
            .values(email="owner@myshoppe.local", name="Owner")
            .returning(db.profiles.c.id)
        ).scalar_one()
        c.execute(db.staff.insert().values(user_id=uid, role="owner", active=True))
    return Actor(uid, uid, "aal2")


@pytest.fixture
def guest():
    return IdentityService(db.engine).session()[1]


@pytest.fixture
def catalog():
    return CatalogService(db.engine)


@pytest.fixture
def checkout():
    return CheckoutService(db.engine)


@pytest.fixture
def payments():
    return PaymentService(db.engine, None)


@pytest.fixture
def orders():
    return OrderService(db.engine)


@pytest.fixture
def client():
    with TestClient(app, headers={"origin": "http://localhost:3000"}) as c:
        yield c


@pytest.fixture
def product(owner, catalog):
    command = ProductInput(
        title="Linen dress",
        slug="linen-dress",
        department="women",
        category="dresses",
        description="A softly tailored linen dress.",
        material="100% linen",
        care="Wash at 30C",
        media=[
            {"src": "/media/woman-1.jpg", "alt": "Linen dress view", "role": r}
            for r in ["lead", "continuation", "continuation", "continuation", "continuation", "cutout"]
        ],
        variants=[
            {
                "sku": "DRESS-BLACK-M",
                "colour": "Black",
                "colour_hex": "#222222",
                "size": "M",
                "price_paise": 295000,
            },
            {
                "sku": "DRESS-ECRU-S",
                "colour": "Ecru",
                "colour_hex": "#dddddd",
                "size": "S",
                "price_paise": 295000,
            },
        ],
    )
    p = catalog.save(owner, command)
    for v in p.variants:
        catalog.stock(
            owner, StockAdjustment(variant_id=v.id, delta=5, reason="Test stock", request_key="stock-" + v.id)
        )
    return catalog.publish(owner, p.id, p.version)
