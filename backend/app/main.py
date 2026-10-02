import logging
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, DataError
from . import db, controllers
from .features.catalog.controllers import router as catalog
from .features.checkout.controllers import router as checkout
from .features.orders.controllers import router as orders
from .features.content.controllers import router as content
from .errors import DomainError
from .settings import settings
from .features.operations.service import MEDIA_ROOT

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
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
    request.state.request_id = str(uuid.uuid4())
    if request.method not in ("GET", "HEAD", "OPTIONS") and request.url.path != "/api/webhooks/razorpay":
        if request.headers.get("origin") != settings.origin:
            return error(request, "INVALID_ORIGIN", "Request origin is not allowed.", 403)
    try:
        length = int(request.headers.get("content-length", "0"))
    except ValueError:
        return error(request, "INVALID_LENGTH", "Invalid content length.", 400)
    if length > (81_000_000 if request.url.path == "/api/admin/media/video" else 11_000_000):
        return error(request, "BODY_TOO_LARGE", "Request is too large.", 413)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = (
        "public, max-age=31536000, immutable"
        if request.url.path.startswith("/uploads/") and response.status_code < 400
        else "no-store"
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
def health():
    with db.engine.connect() as c:
        c.execute(text("SELECT 1"))
    return {"status": "ready", "environment": settings.environment}
