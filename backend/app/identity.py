import hashlib
import secrets
import time
from dataclasses import dataclass
from datetime import timedelta
import httpx
from sqlalchemy import select, update, delete
from sqlalchemy.dialects.postgresql import insert
from . import db
from .errors import DomainError, require
from .settings import settings


@dataclass(frozen=True)
class Actor:
    owner_id: str
    user_id: str | None = None
    assurance: str = "aal1"


PERMISSIONS = {
    "owner": {
        "catalog.write",
        "inventory.write",
        "content.write",
        "orders.read",
        "orders.fulfil",
        "returns.manage",
        "refunds.write",
        "support.manage",
        "staff.manage",
    },
    "merchandiser": {"catalog.write", "inventory.write", "content.write"},
    "fulfilment": {"orders.read", "orders.fulfil", "returns.manage"},
    "support": {"orders.read", "returns.manage", "support.manage"},
}


def require_permission(conn, actor, permission):
    member = conn.execute(select(db.staff).where(db.staff.c.user_id == actor.user_id)).mappings().first()
    require(
        member and member["active"] and permission in PERMISSIONS.get(member["role"], set()),
        "FORBIDDEN",
        "You do not have permission for this action.",
        403,
    )
    require(actor.assurance == "aal2", "MFA_REQUIRED", "Verify your second factor to continue.", 403)


def audit(conn, actor, action, target, detail=None):
    conn.execute(
        db.audit.insert().values(actor=actor.owner_id, action=action, target=str(target), detail=detail or {})
    )


def rate_limit(conn, key, maximum=20):
    window = int(time.time()) // 60
    stmt = insert(db.limits).values(key=key, window=window, count=1)
    from sqlalchemy import case

    count = conn.execute(
        stmt.on_conflict_do_update(
            index_elements=[db.limits.c.key],
            set_={
                "window": window,
                "count": case((db.limits.c.window == window, db.limits.c.count + 1), else_=1),
            },
        ).returning(db.limits.c.count)
    ).scalar_one()
    require(count <= maximum, "RATE_LIMIT", "Please wait a minute before trying again.", 429)


class IdentityService:
    def __init__(self, engine):
        self.engine = engine

    def resolve(self, token):
        if not token:
            return None
        with self.engine.connect() as c:
            row = (
                c.execute(
                    select(db.sessions).where(
                        db.sessions.c.token_hash == hashlib.sha256(token.encode()).hexdigest(),
                        db.sessions.c.expires_at > db.now(),
                    )
                )
                .mappings()
                .first()
            )
            return Actor(row["owner_id"], row["user_id"], row["assurance"]) if row else None

    def session(self, actor=None):
        token = secrets.token_urlsafe(32)
        actor = actor or Actor(secrets.token_hex(24))
        with self.engine.begin() as c:
            c.execute(
                db.sessions.insert().values(
                    token_hash=hashlib.sha256(token.encode()).hexdigest(),
                    owner_id=actor.owner_id,
                    user_id=actor.user_id,
                    assurance=actor.assurance,
                    expires_at=db.now()
                    + (
                        timedelta(minutes=30)
                        if actor.assurance == "aal2" and settings.environment == "production"
                        else timedelta(days=30)
                    ),
                )
            )
            c.execute(insert(db.carts).values(owner_id=actor.owner_id).on_conflict_do_nothing())
        return token, actor

    def me(self, actor):
        with self.engine.connect() as c:
            row = c.execute(select(db.profiles).where(db.profiles.c.id == actor.user_id)).mappings().first()
            role = c.execute(
                select(db.staff.c.role).where(db.staff.c.user_id == actor.user_id, db.staff.c.active)
            ).scalar_one_or_none()
        return {
            "name": row["name"] if row else None,
            "email": row["email"] if row else None,
            "role": role,
            "permissions": sorted(PERMISSIONS.get(role, set())),
            "development": settings.dev_login,
            "payment_mode": settings.payment_mode,
        }

    def login(self, old_actor, email, name, assurance="aal1", provider_id=None):
        with self.engine.begin() as c:
            # Merge is serialized by guest cart; consuming guest sessions prevents replay.
            c.execute(select(db.carts).where(db.carts.c.owner_id == old_actor.owner_id).with_for_update())
            row = c.execute(select(db.profiles).where(db.profiles.c.email == email)).mappings().first()
            uid = (
                row["id"]
                if row
                else c.execute(
                    db.profiles.insert()
                    .values(**({"id": provider_id} if provider_id else {}), email=email, name=name)
                    .returning(db.profiles.c.id)
                ).scalar_one()
            )
            c.execute(insert(db.carts).values(owner_id=uid).on_conflict_do_nothing())
            require(
                not old_actor.user_id or old_actor.user_id == uid,
                "SIGN_OUT_FIRST",
                "Sign out before switching accounts.",
                409,
            )
            c.execute(select(db.carts).where(db.carts.c.owner_id == uid).with_for_update())
            if old_actor.owner_id != uid:
                for item in c.execute(
                    select(db.cart_items).where(db.cart_items.c.owner_id == old_actor.owner_id)
                ).mappings():
                    stmt = insert(db.cart_items).values(
                        owner_id=uid, variant_id=item["variant_id"], quantity=item["quantity"]
                    )
                    from sqlalchemy import func

                    c.execute(
                        stmt.on_conflict_do_update(
                            index_elements=[db.cart_items.c.owner_id, db.cart_items.c.variant_id],
                            set_={"quantity": func.least(10, db.cart_items.c.quantity + item["quantity"])},
                        )
                    )
                for item in c.execute(
                    select(db.saved).where(db.saved.c.owner_id == old_actor.owner_id)
                ).mappings():
                    c.execute(
                        insert(db.saved)
                        .values(owner_id=uid, product_id=item["product_id"])
                        .on_conflict_do_nothing()
                    )
                c.execute(delete(db.cart_items).where(db.cart_items.c.owner_id == old_actor.owner_id))
                c.execute(delete(db.saved).where(db.saved.c.owner_id == old_actor.owner_id))
                c.execute(
                    update(db.orders).where(db.orders.c.owner_id == old_actor.owner_id).values(owner_id=uid)
                )
                c.execute(delete(db.sessions).where(db.sessions.c.owner_id == old_actor.owner_id))
            c.execute(
                update(db.carts).where(db.carts.c.owner_id == uid).values(version=db.carts.c.version + 1)
            )
        return self.session(Actor(uid, uid, assurance))

    def logout(self, token):
        with self.engine.begin() as c:
            c.execute(
                delete(db.sessions).where(
                    db.sessions.c.token_hash == hashlib.sha256((token or "").encode()).hexdigest()
                )
            )

    def development_login(self, actor, email):
        require(
            settings.environment == "development" and settings.dev_login, "NOT_FOUND", "Not available", 404
        )
        with self.engine.connect() as c:
            allowed = c.execute(select(db.profiles.c.id).where(db.profiles.c.email == email)).first()
        require(allowed, "INVALID_DEMO_ACCOUNT", "Use a seeded development account.", 401)
        return self.login(actor, email, email.split("@")[0], "aal2")

    def email_login(self, actor, email, code):
        with self.engine.begin() as c:
            rate_limit(c, f"login:{actor.owner_id}", 5)
        result = self.otp(email, code)
        if not code:
            return None
        user = result["user"]
        with self.engine.connect() as c:
            staff = c.execute(
                select(db.staff.c.user_id)
                .join(db.profiles)
                .where(db.profiles.c.email == user["email"], db.staff.c.active)
            ).first()
        if staff:
            return {"mfa_required": True, "access_token": result["access_token"]}
        return self.login(
            actor,
            user["email"],
            user.get("user_metadata", {}).get("name", "Customer"),
            provider_id=user["id"],
        )

    def mfa(self, actor, access_token, factor_id=None, code=None):
        from .adapters import supabase
        from uuid import UUID

        with self.engine.begin() as c:
            rate_limit(c, f"mfa:{actor.owner_id}", 6)
        claims = supabase.verified_claims(access_token)
        user = supabase.request("GET", "user", access_token)
        require(
            user["id"] == claims["sub"] and user.get("email_confirmed_at"),
            "INVALID_IDENTITY",
            "Verify your email first.",
            401,
        )
        with self.engine.connect() as c:
            member = (
                c.execute(
                    select(db.staff)
                    .join(db.profiles)
                    .where(db.profiles.c.id == user["id"], db.staff.c.active)
                )
                .mappings()
                .first()
            )
        require(member, "FORBIDDEN", "This account has no staff membership.", 403)
        if code:
            try:
                factor_id = str(UUID(factor_id))
            except (ValueError, TypeError):
                raise DomainError("INVALID_FACTOR", "Invalid second factor", 422)
            challenge = supabase.request("POST", f"factors/{factor_id}/challenge", access_token, {})
            result = supabase.request(
                "POST",
                f"factors/{factor_id}/verify",
                access_token,
                {"challenge_id": challenge["id"], "code": code},
            )
            elevated = supabase.verified_claims(result["access_token"])
            require(
                elevated["sub"] == user["id"] and elevated.get("aal") == "aal2",
                "MFA_REQUIRED",
                "Second factor was not verified.",
                401,
            )
            return self.login(
                actor,
                user["email"],
                user.get("user_metadata", {}).get("name", "Boutique staff"),
                "aal2",
                user["id"],
            )
        factors = [
            f
            for f in user.get("factors", [])
            if f.get("factor_type") == "totp" and f.get("status") == "verified"
        ]
        if factors:
            return {"factor_id": factors[0]["id"]}
        result = supabase.request(
            "POST",
            "factors",
            access_token,
            {"factor_type": "totp", "friendly_name": f"MyShoppe {secrets.token_hex(3)}"},
        )
        return {
            "factor_id": result["id"],
            "secret": result["totp"]["secret"],
            "qr_code": result["totp"]["qr_code"],
        }

    def otp(self, email, code=None):
        require(
            bool(settings.supabase_url and settings.supabase_key),
            "IDENTITY_UNCONFIGURED",
            "Email sign-in is not configured yet.",
            503,
        )
        path, body = (
            ("verify", {"email": email, "token": code, "type": "email"})
            if code
            else ("otp", {"email": email, "create_user": True})
        )
        with httpx.Client(timeout=15) as client:
            response = client.post(
                f"{settings.supabase_url}/auth/v1/{path}",
                headers={"apikey": settings.supabase_key},
                json=body,
            )
        if response.is_error:
            raise DomainError("SIGN_IN_FAILED", "Unable to sign in. Check the code and try again.", 401)
        return response.json()
