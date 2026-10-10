import logging
import json
import time
import uuid
import hmac
import hashlib
import ipaddress
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, DataError
from . import db, controllers
from .features.catalog.controllers import router as catalog
from .features.checkout.controllers import router as checkout
from .features.orders.controllers import router as orders
from .features.content.controllers import router as content
from .errors import DomainError
from .identity import consume_ip_limit
from .settings import settings
from .features.operations.service import MEDIA_ROOT

class JsonFormatter(logging.Formatter):
    def format(self, record):
        item = {"time": self.formatTime(record), "level": record.levelname, "logger": record.name, "message": record.getMessage()}
        for name in ("event", "request_id", "method", "route", "status", "duration_ms"):
            if hasattr(record, name):
                item[name] = getattr(record, name)
        if record.exc_info:
            item["exception"] = self.formatException(record.exc_info)
        return json.dumps(item, separators=(",", ":"))


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger("myshoppe")


@asynccontextmanager
async def lifespan(app):
    settings.validate()
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    yield
    db.engine.dispose()


app = FastAPI(title="MyShoppe commerce API", version="0.1.0", lifespan=lifespan)
for router in [controllers.router, catalog, checkout, orders, content]:
    app.include_router(router)
app.mount("/uploads", StaticFiles(directory=MEDIA_ROOT, check_dir=False), name="uploaded-media")

IP_LIMITS = {
    "/api/auth/development": 8,
    "/api/auth/email": 8,
    "/api/auth/mfa": 8,
    "/api/checkout/quote": 20,
    "/api/checkout/attempts": 10,
    "/api/support": 5,
}


def client_ip(request):
    peer = request.client.host if request.client else "127.0.0.1"
    try:
        peer_address = ipaddress.ip_address(peer)
        trusted = any(
            peer_address in ipaddress.ip_network(value.strip(), strict=False)
            for value in settings.trusted_proxy_cidrs.split(",")
            if value.strip()
        )
        if not trusted:
            return peer_address.compressed
        forwarded = request.headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
        return ipaddress.ip_address(forwarded).compressed
    except ValueError:
        return peer


def error(request, code, message, status, fields=None):
    return JSONResponse(
        status_code=status,
        content={
            "error": {"code": code, "message": message, "fieldErrors": fields, "retryable": status >= 500},
            "requestId": getattr(request.state, "request_id", ""),
        },
    )


@app.middleware("http")
async def safeguards(request: Request, call_next):
    started = time.perf_counter()
    request.state.request_id = str(uuid.uuid4())
    if request.method not in ("GET", "HEAD", "OPTIONS") and request.url.path != "/api/webhooks/razorpay":
        if request.headers.get("origin") != settings.origin:
            return apply_security_headers(
                error(request, "INVALID_ORIGIN", "Request origin is not allowed.", 403), request
            )
    try:
        length = int(request.headers.get("content-length", "0"))
    except ValueError:
        return apply_security_headers(error(request, "INVALID_LENGTH", "Invalid content length.", 400), request)
    if length > (81_000_000 if request.url.path == "/api/admin/media/video" else 11_000_000):
        return apply_security_headers(error(request, "BODY_TOO_LARGE", "Request is too large.", 413), request)
    limit = IP_LIMITS.get(request.url.path)
    if limit and request.method != "OPTIONS":
        secret = settings.rate_limit_hmac_key or "development-local-rate-limit-key"
        digest = hmac.new(
            secret.encode(),
            f"{request.url.path}:{client_ip(request)}".encode(),
            hashlib.sha256,
        ).hexdigest()
        allowed = await run_in_threadpool(consume_ip_limit, db.engine, f"ip:{digest}", limit)
        if not allowed:
            response = error(request, "RATE_LIMIT", "Please wait before trying again.", 429)
            response.headers["Retry-After"] = "60"
            return apply_security_headers(response, request, started)
    response = await call_next(request)
    return apply_security_headers(response, request, started)


def apply_security_headers(response, request, started=None):
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.url.path.startswith(("/api/", "/uploads/")):
        response.headers["Content-Security-Policy"] = "default-src 'none'; base-uri 'none'; frame-ancestors 'none'; object-src 'none'"
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    response.headers["Cache-Control"] = (
        "public, max-age=31536000, immutable"
        if request.url.path.startswith("/uploads/") and response.status_code < 400
        else "no-store"
    )
    if started is not None:
        route = request.scope.get("route")
        logger.info(
            "request complete",
            extra={
                "event": "http_request",
                "request_id": request.state.request_id,
                "method": request.method,
                "route": getattr(route, "path", "unmatched"),
                "status": response.status_code,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            },
        )
    return response


@app.exception_handler(DomainError)
async def domain_error(request, exc):
    return error(request, exc.code, exc.message, exc.status)


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    fields = {".".join(str(v) for v in e["loc"][1:]): e["msg"] for e in exc.errors()}
    return error(request, "VALIDATION", "Please check the highlighted fields.", 422, fields)


@app.exception_handler(IntegrityError)
async def integrity_error(request, exc):
    return error(request, "CONFLICT", "This change conflicts with existing data. Reload and try again.", 409)


@app.exception_handler(DataError)
async def invalid_value(request, exc):
    return error(request, "INVALID_VALUE", "A supplied identifier or value is invalid.", 422)


@app.exception_handler(Exception)
async def unexpected(request, exc):
    logger.exception("request_failed request_id=%s", request.state.request_id)
    return error(request, "INTERNAL", "Something went wrong. Please try again.", 500)


@app.get("/api/health")
@app.get("/api/ready")
def health():
    with db.engine.connect() as c:
        c.execute(text("SELECT 1"))
    return {"status": "ready", "environment": settings.environment}


@app.get("/api/live")
def live():
    return {"status": "alive"}
