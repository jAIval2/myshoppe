from typing import Annotated
from fastapi import APIRouter, Depends, Request, Response, UploadFile
from starlette.concurrency import run_in_threadpool
from pydantic import Field
from .dependencies import current_actor, identity, payments, set_session, get_operations
from .identity import Actor
from .errors import require
from .schemas import Command, SupportInput
from .features.operations.interfaces import Operations

router = APIRouter()
User = Annotated[Actor, Depends(current_actor)]
Ops = Annotated[Operations, Depends(get_operations)]


class Login(Command):
    email: str = Field(pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    code: str | None = None


@router.get("/api/session")
def me(actor: User):
    return identity.me(actor)


@router.post("/api/auth/development")
def dev_login(command: Login, actor: User, response: Response):
    token, new_actor = identity.development_login(actor, command.email)
    set_session(response, token)
    return identity.me(new_actor)


@router.post("/api/auth/email")
def email_login(command: Login, actor: User, response: Response):
    result = identity.email_login(actor, command.email, command.code)
    if not result:
        return {"sent": True}
    if isinstance(result, dict):
        return result
    token, new_actor = result
    set_session(response, token)
    return identity.me(new_actor)


class MFA(Command):
    access_token: str = Field(min_length=20, max_length=12000)
    factor_id: str | None = None
    code: str | None = Field(default=None, pattern=r"^\d{6}$")


@router.post("/api/auth/mfa")
def mfa(command: MFA, actor: User, response: Response):
    result = identity.mfa(actor, command.access_token, command.factor_id, command.code)
    if isinstance(result, dict):
        return result
    token, new_actor = result
    set_session(response, token)
    return identity.me(new_actor)


@router.post("/api/auth/logout")
def logout(request: Request, response: Response):
    identity.logout(request.cookies.get("shop_session"))
    response.delete_cookie("shop_session")
    return {"ok": True}


class PaymentSession(Command):
    order_id: str


@router.post("/api/payments/session")
def payment_session(command: PaymentSession, actor: User):
    return payments.session(actor, command.order_id)


@router.post("/api/payments/development/{order_id}/capture")
def dev_capture(order_id: str, actor: User):
    return payments.development_capture(actor, order_id)


@router.post("/api/webhooks/razorpay")
async def webhook(request: Request):
    raw = bytearray()
    async for chunk in request.stream():
        require(len(raw) + len(chunk) <= 256000, "BODY_TOO_LARGE", "Webhook body too large", 413)
        raw.extend(chunk)
    await run_in_threadpool(
        payments.ingest,
        bytes(raw),
        request.headers.get("x-razorpay-signature", ""),
        request.headers.get("x-razorpay-event-id", ""),
    )
    return {"ok": True}


@router.post("/api/support")
def support(command: SupportInput, actor: User, service: Ops):
    return service.submit_support(actor, command)


@router.get("/api/admin/support")
def support_list(actor: User, service: Ops):
    return service.support_list(actor)


@router.post("/api/admin/media")
def upload(file: UploadFile, actor: User, service: Ops):
    return service.image(actor, file.file.read(10_000_001))


class Pause(Command):
    paused: bool


@router.post("/api/admin/checkout-pause")
def pause(command: Pause, actor: User, service: Ops):
    return service.pause(actor, command.paused)


@router.post("/api/admin/media/video")
def upload_video(file: UploadFile, actor: User, service: Ops):
    return service.video(actor, file.file.read(80_000_001))


@router.get("/api/admin/media/jobs/{key}")
def media_job(key: str, actor: User, service: Ops):
    return service.job(actor, key)


@router.post("/api/admin/jobs/{job_id}/retry")
def retry_job(job_id: str, actor: User, service: Ops):
    return service.retry(actor, job_id)
