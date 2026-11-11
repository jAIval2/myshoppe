import io
import pytest
from PIL import Image
from app import db
from app.errors import DomainError
from app.identity import IdentityService, Actor
from app.features.bespoke.service import BespokeService
from app.features.bespoke.schemas import Design, Save, Action


@pytest.fixture
def studio():
    return BespokeService(db.engine)


def complete(studio, guest):
    b = studio.create(guest)
    return studio.save(
        guest,
        b["id"],
        Save(
            expected_version=1,
            design=Design(
                name="Asha",
                fabric="fabric-mocha",
                lace_choice="none",
                silhouette="Straight kurta",
                vision="Relaxed fit with full sleeves",
            ),
        ),
    )


def act(studio, actor, b, action, admin=False, **kwargs):
    return studio.action(
        actor, b["id"], Action(expected_version=b["version"], action=action, **kwargs), admin
    )


def reviewed(studio, guest, owner):
    b = act(studio, guest, complete(studio, guest), "submit")
    return act(
        studio,
        owner,
        b,
        "review",
        True,
        instructions="Full sleeves, round neckline, enclosed seams.",
        material_confirmation="Mocha sample confirmed, 3 metres",
        measurement_confirmation="Measure in cm at boutique before cutting",
    )


def test_handoff_requires_agreement_and_edits_invalidate_it(studio, guest, owner):
    b = reviewed(studio, guest, owner)
    with pytest.raises(DomainError, match="agreement"):
        act(studio, owner, b, "ready", True)
    b = act(studio, guest, b, "agree")
    agreed_version = b["agreement"]["version"]
    b = act(studio, owner, b, "ready", True)
    assert b["status"] == "ready"
    old_design = b["design"].copy()
    changed = Design(**{**b["design"], "neckline": "V-neck"})
    updated = studio.save(guest, b["id"], Save(expected_version=b["version"], design=changed))
    assert updated["status"] == "draft" and updated["agreement"] is None
    assert updated["history"][-1]["design"] == old_design
    assert updated["history"][-1]["agreement"]["version"] == agreed_version
    with pytest.raises(DomainError):
        act(studio, owner, updated, "ready", True)


def test_open_questions_and_incomplete_confirmation_block_agreement(studio, guest, owner):
    b = reviewed(studio, guest, owner)
    b = act(studio, owner, b, "review", True, instructions="Full sleeves", questions="Confirm sleeve length")
    with pytest.raises(DomainError, match="resolve open questions"):
        act(studio, guest, b, "agree")
    b = act(
        studio,
        owner,
        b,
        "review",
        True,
        instructions="Full sleeves",
        material_confirmation="   ",
        measurement_confirmation="   ",
    )
    with pytest.raises(DomainError):
        act(studio, guest, b, "agree")


def test_stale_writes_and_wrong_actor_cannot_change_brief(studio, guest, owner):
    b = complete(studio, guest)
    other = IdentityService(db.engine).session()[1]
    with pytest.raises(DomainError):
        studio.get(other, b["id"])
    with pytest.raises(DomainError):
        studio.list(guest, True)
    with pytest.raises(DomainError):
        act(studio, guest, b, "review")
    with pytest.raises(DomainError):
        studio.save(
            guest, b["id"], Save(expected_version=1, design=Design(**{**b["design"], "vision": "stale"}))
        )
    b = act(studio, guest, b, "submit")
    with pytest.raises(DomainError):
        act(
            studio,
            Actor(owner.owner_id, owner.user_id, "aal1"),
            b,
            "review",
            True,
            instructions="unauthenticated",
        )


def test_private_uploads_cannot_be_reused_across_designs(studio, guest, owner):
    b = complete(studio, guest)
    out = io.BytesIO()
    Image.new("RGB", (20, 20), "white").save(out, "PNG")
    image = studio.upload(guest, b["id"], out.getvalue(), "image/png")
    other = IdentityService(db.engine).session()[1]
    with pytest.raises(DomainError):
        studio.asset(other, image["id"])
    with pytest.raises(DomainError):
        studio.asset(owner, image["id"])
    second = complete(studio, guest)
    with pytest.raises(DomainError, match="does not belong"):
        studio.save(
            guest,
            second["id"],
            Save(
                expected_version=second["version"],
                design=Design(
                    **{
                        **second["design"],
                        "references": [{"asset_id": image["id"], "name": "private", "pins": []}],
                    }
                ),
            ),
        )
    assert studio.asset(guest, image["id"])["content_type"] == "image/webp"
    act(studio, guest, b, "submit")
    assert studio.asset(owner, image["id"])["data"]
    with pytest.raises(DomainError):
        studio.upload(guest, b["id"], b"<script>bad</script>", "audio/webm")


def test_guest_designs_follow_account_login(studio, guest):
    b = complete(studio, guest)
    _, customer = IdentityService(db.engine).login(guest, "designer@example.test", "Designer")
    assert studio.get(customer, b["id"])["owner_id"] == customer.user_id
    with pytest.raises(DomainError):
        studio.get(guest, b["id"])


def test_http_routes_validate_and_keep_guest_cookie(client):
    response = client.post("/api/bespoke")
    assert response.status_code == 200
    b = response.json()
    assert client.get(f"/api/bespoke/{b['id']}").status_code == 200
    assert (
        client.post(
            f"/api/bespoke/{b['id']}/actions", json={"action": "submit", "expected_version": 1}
        ).status_code
        == 422
    )
    assert client.get("/api/admin/bespoke").status_code == 403
    assert client.get("/api/bespoke/not-a-uuid").status_code == 422
