import hashlib
import hmac
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
import pytest
from pydantic import ValidationError
from sqlalchemy import select, update, func
from app import db
from app.errors import DomainError
from app.identity import Actor, IdentityService, require_permission
from app.schemas import (
    CartMutation,
    Address,
    Checkout,
    RefundInput,
    ShipmentInput,
    ReturnInput,
    CampaignInput,
    ProductInput,
    StockAdjustment,
)
from app.features.payments.service import PaymentService
from app.features.content.service import ContentService

ADDRESS = Address(
    name="Test Shopper",
    email="test@example.test",
    phone="9876543210",
    line1="12 Test Road",
    city="Mumbai",
    state="Maharashtra",
    pin="400001",
)


def prepare(service, actor, variant):
    cart = service.cart(actor)
    service.mutate(actor, CartMutation(variant_id=variant, quantity=1, expected_version=cart["version"]))
    quote = service.quote(actor, ADDRESS)
    return Checkout(address=ADDRESS, quote_hash=quote["quote_hash"], request_key=str(uuid.uuid4()))


@pytest.mark.parametrize(
    "quantity", [-1, 1.5, 11, True], ids=["negative", "fractional", "over-limit", "boolean"]
)
def test_quantity_boundaries(quantity):
    with pytest.raises(ValidationError):
        CartMutation(variant_id="sku", quantity=quantity, expected_version=1)


@pytest.mark.parametrize(
    "role,assurance,allowed",
    [
        ("owner", "aal2", True),
        ("owner", "aal1", False),
        ("merchandiser", "aal2", False),
        ("support", "aal2", False),
    ],
)
def test_refund_permission_boundary(owner, role, assurance, allowed):
    with db.engine.begin() as c:
        c.execute(update(db.staff).where(db.staff.c.user_id == owner.user_id).values(role=role))
        actor = Actor(owner.owner_id, owner.user_id, assurance)
        if allowed:
            require_permission(c, actor, "refunds.write")
        else:
            with pytest.raises(DomainError):
                require_permission(c, actor, "refunds.write")


def test_direct_admin_and_origin_denial(client, product):
    assert client.get("/api/admin/products").status_code == 403
    assert (
        client.post(
            "/api/admin/products/" + product.id + "/archive", json={"expected_version": product.version}
        ).status_code
        == 403
    )
    assert client.post("/api/auth/logout", headers={"origin": "https://attacker.example"}).status_code == 403


def test_filter_matches_same_variant_and_archive(catalog, owner, product):
    assert catalog.list(colour="Black", size="S").total == 0
    assert catalog.list(colour="Black", size="M").total == 1
    catalog.publish(owner, product.id, product.version, "archived")
    assert catalog.list().total == 0
    with pytest.raises(DomainError):
        catalog.get(product.slug)


def test_bag_ownership_and_stale_version(checkout, guest, product):
    command = CartMutation(variant_id=product.variants[0].id, quantity=1, expected_version=1)
    checkout.mutate(guest, command)
    other = IdentityService(db.engine).session()[1]
    assert checkout.cart(other)["items"] == []
    with pytest.raises(DomainError, match="another tab"):
        checkout.mutate(guest, command)
    checkout.save(guest, product.id)
    checkout.save(guest, product.id)
    assert len(checkout.saved(guest)) == 1 and len(checkout.saved(other)) == 0
    with db.engine.connect() as c:
        assert c.execute(select(func.sum(db.inventory.c.reserved))).scalar_one() == 0


def test_reservation_idempotency_and_immutable_totals(checkout, guest, product):
    command = prepare(checkout, guest, product.variants[0].id)
    first = checkout.reserve(guest, command)
    assert first["total"] == 310000
    assert checkout.reserve(guest, command)["id"] == first["id"]
    changed = command.model_copy(update={"quote_hash": "different"})
    with pytest.raises(DomainError, match="different details"):
        checkout.reserve(guest, changed)


def test_last_unit_contention(checkout, product):
    sku = product.variants[0].id
    actors = [IdentityService(db.engine).session()[1] for _ in range(20)]
    commands = [prepare(checkout, a, sku) for a in actors]
    with db.engine.begin() as c:
        c.execute(update(db.inventory).where(db.inventory.c.variant_id == sku).values(on_hand=1))
    barrier = Barrier(20)

    def contend(i):
        barrier.wait(timeout=10)
        try:
            checkout.reserve(actors[i], commands[i])
            return "won"
        except DomainError as e:
            assert e.code == "INSUFFICIENT_STOCK"
            return "lost"

    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(contend, range(20)))
    assert results.count("won") == 1 and results.count("lost") == 19
    with db.engine.connect() as c:
        stock = c.execute(select(db.inventory).where(db.inventory.c.variant_id == sku)).mappings().one()
        assert (stock["on_hand"], stock["reserved"]) == (1, 1)
        assert c.execute(select(func.count()).select_from(db.orders)).scalar_one() == 1


def test_capture_expiry_and_late_refund_hold(checkout, payments, guest, product):
    command = prepare(checkout, guest, product.variants[0].id)
    order = checkout.reserve(guest, command)
    assert payments.expire(order["expires_at"] + timedelta(seconds=1)) == 1
    assert payments.expire(order["expires_at"] + timedelta(seconds=2)) == 0
    payments.capture(order["id"], "pay_late", order["total"])
    payments.capture(order["id"], "pay_late", order["total"])
    with db.engine.connect() as c:
        row = c.execute(select(db.orders).where(db.orders.c.id == order["id"])).mappings().one()
        assert row["status"] == "paid_needs_resolution"
        assert c.execute(select(func.count()).select_from(db.refunds)).scalar_one() == 1
        assert (
            c.execute(
                select(db.inventory.c.on_hand).where(db.inventory.c.variant_id == product.variants[0].id)
            ).scalar_one()
            == 5
        )


def test_paid_order_fulfilment_return_refund(checkout, payments, orders, guest, owner, product):
    order = checkout.reserve(guest, prepare(checkout, guest, product.variants[0].id))
    payments.capture(order["id"], "pay_good", order["total"])
    payments.capture(order["id"], "pay_good", order["total"])
    result = orders.get(guest, order["id"])
    item = result["items"][0]
    with pytest.raises(DomainError):
        orders.get(Actor("other"), order["id"])
    orders.ship(owner, order["id"], ShipmentInput(tracking="TEST-TRACKING", items={item["id"]: 1}))
    with pytest.raises(DomainError):
        orders.ship(owner, order["id"], ShipmentInput(tracking="DUPLICATE", items={item["id"]: 1}))
    orders.deliver(owner, order["id"])
    ret = orders.request_return(
        guest,
        order["id"],
        ReturnInput(items={item["id"]: 1}, reason="Wrong size", request_key="return-test-key"),
    )
    orders.receive_return(owner, ret["id"], True)
    with pytest.raises(DomainError):
        orders.receive_return(owner, ret["id"], True)
    refund = orders.refund(
        owner,
        order["id"],
        RefundInput(amount=order["total"], reason="Returned item", request_key="refund-test-key"),
    )
    assert refund["status"] == "requested"
    with pytest.raises(DomainError):
        orders.refund(
            owner, order["id"], RefundInput(amount=1, reason="Extra refund", request_key="refund-extra-key")
        )


def test_webhook_signature_and_durable_deduplication(monkeypatch):
    from app.adapters import razorpay
    from dataclasses import replace

    monkeypatch.setattr(razorpay, "settings", replace(razorpay.settings, webhook_secret="test"))
    service = PaymentService(db.engine, razorpay.RazorpayGateway())
    raw = json.dumps({"event": "payment.captured"}).encode()
    with pytest.raises(DomainError):
        service.ingest(raw, "bad", "evt-1")
    signature = hmac.new(b"test", raw, hashlib.sha256).hexdigest()
    service.ingest(raw, signature, "evt-1")
    service.ingest(raw, signature, "evt-1")
    with db.engine.connect() as c:
        assert c.execute(select(func.count()).select_from(db.events)).scalar_one() == 1
        assert c.execute(select(func.count()).select_from(db.jobs)).scalar_one() == 1


def test_campaign_revision_and_cross_department_target(owner):
    blocks = [
        {"type": kind, "src": "/media/test.jpg", "title": "Test", "target": "/collections/women-new-in"}
        for kind in ["hero", "video", "poster", "poster", "collection-entry"]
    ]
    service = ContentService(db.engine)
    draft = service.save(owner, "women", CampaignInput(expected_revision=0, blocks=blocks))
    assert not draft["published"]
    with pytest.raises(DomainError, match="process every"):
        service.publish(owner, draft["id"])
    for block in blocks:
        block["src"] = "/media/woman-1.jpg"
    draft = service.save(owner, "women", CampaignInput(expected_revision=1, blocks=blocks))
    assert service.publish(owner, draft["id"])["revision"] == 2
    with pytest.raises(DomainError):
        service.save(owner, "home", CampaignInput(expected_revision=0, blocks=blocks))


def test_account_switch_does_not_transfer_owned_order(checkout, guest, owner, product):
    identity = IdentityService(db.engine)
    token, customer = identity.login(guest, "customer@example.test", "Customer")
    order = checkout.reserve(customer, prepare(checkout, customer, product.variants[0].id))
    with pytest.raises(DomainError, match="Sign out"):
        identity.login(customer, "owner@myshoppe.local", "Owner")
    with db.engine.connect() as c:
        assert (
            c.execute(select(db.orders.c.owner_id).where(db.orders.c.id == order["id"])).scalar_one()
            == customer.owner_id
        )
    assert identity.resolve(token).user_id == customer.user_id


def test_published_edit_and_stock_retry_preserve_invariants(catalog, owner, product):
    raw = product.model_dump(include=set(ProductInput.model_fields), exclude={"variants"})
    raw["variants"] = [
        v.model_dump(
            include={
                "id",
                "sku",
                "colour",
                "colour_hex",
                "size",
                "dimensions",
                "price_paise",
                "compare_at_paise",
            }
        )
        for v in product.variants
    ]
    raw["expected_version"] = product.version
    raw["media"] = raw["media"][:1]
    with pytest.raises(DomainError, match="four continuation"):
        catalog.save(owner, ProductInput(**raw), product.id)
    command = StockAdjustment(
        variant_id=product.variants[0].id, delta=3, reason="Receipt", request_key="same-stock-receipt"
    )
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert all(pool.map(lambda _: catalog.stock(owner, command)["ok"], range(4)))
    assert catalog.get(product.id, owner).variants[0].on_hand == 8


def test_reconciliation_recovers_unknown_order_without_second_charge(checkout, guest, product):
    order = checkout.reserve(guest, prepare(checkout, guest, product.variants[0].id))

    class Gateway:
        def find_order(self, local):
            return {"id": "order_recovered", "amount": local["total"], "currency": "INR"}

        def fetch_order_payments(self, provider_id):
            return {"items": [{"id": "pay_recovered", "status": "captured"}]}

        def fetch_payment(self, payment_id):
            return {
                "id": payment_id,
                "status": "captured",
                "amount": order["total"],
                "currency": "INR",
                "order_id": "order_recovered",
            }

    service = PaymentService(db.engine, Gateway())
    assert service.reconcile(order["id"])
    assert service.reconcile(order["id"])
    with db.engine.connect() as c:
        assert (
            c.execute(select(db.orders.c.status).where(db.orders.c.id == order["id"])).scalar_one() == "paid"
        )
        assert (
            c.execute(
                select(db.inventory.c.on_hand).where(db.inventory.c.variant_id == product.variants[0].id)
            ).scalar_one()
            == 4
        )


def test_staff_mfa_requires_verified_provider_assurance(monkeypatch, guest, owner):
    from app.adapters import supabase

    factor = str(uuid.uuid4())
    elevated = {"sub": owner.user_id, "aal": "aal1"}
    monkeypatch.setattr(
        supabase,
        "verified_claims",
        lambda token: {"sub": owner.user_id, "aal": "aal1"} if token == "first" else elevated,
    )

    def provider(method, path, token, body=None):
        if path == "user":
            return {
                "id": owner.user_id,
                "email": "owner@myshoppe.local",
                "email_confirmed_at": "2026-10-01",
                "factors": [{"id": factor, "factor_type": "totp", "status": "verified"}],
            }
        if path.endswith("/challenge"):
            return {"id": "challenge"}
        if path.endswith("/verify"):
            return {"access_token": "second"}
        raise AssertionError("Unexpected provider request")

    monkeypatch.setattr(supabase, "request", provider)
    identity = IdentityService(db.engine)
    assert identity.mfa(guest, "first")["factor_id"] == factor
    with pytest.raises(DomainError, match="not verified"):
        identity.mfa(guest, "first", factor, "123456")
    elevated["aal"] = "aal2"
    token, actor = identity.mfa(guest, "first", factor, "123456")
    assert identity.resolve(token).assurance == "aal2" and actor.user_id == owner.user_id
