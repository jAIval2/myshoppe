"""Small REST adapter. Provider tokens stay in memory during MFA, never localStorage."""

import httpx
import jwt
from app.settings import settings
from app.errors import require, DomainError


def request(method, path, token, body=None):
    require(
        settings.supabase_url and settings.supabase_key,
        "IDENTITY_UNCONFIGURED",
        "Sign-in is not configured",
        503,
    )
    with httpx.Client(timeout=15) as client:
        response = client.request(
            method,
            f"{settings.supabase_url}/auth/v1/{path}",
            headers={"apikey": settings.supabase_key, "Authorization": f"Bearer {token}"},
            json=body,
        )
    require(not response.is_error, "MFA_FAILED", "Unable to verify. Check your code or sign in again.", 401)
    return response.json()


def verified_claims(token):
    try:
        key = jwt.PyJWKClient(
            f"{settings.supabase_url}/auth/v1/.well-known/jwks.json", timeout=10
        ).get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            key.key,
            algorithms=["ES256", "RS256"],
            audience="authenticated",
            issuer=f"{settings.supabase_url}/auth/v1",
            options={"require": ["exp", "sub", "iss", "aud"]},
        )
    except jwt.PyJWTError as exc:
        raise DomainError("INVALID_IDENTITY", "Identity verification failed. Sign in again.", 401) from exc
