from fastapi import Request, Response
from . import db
from .identity import IdentityService
from .settings import settings
from .features.catalog.service import CatalogService
from .features.checkout.service import CheckoutService
from .features.orders.service import OrderService
from .features.content.service import ContentService
from .features.payments.service import PaymentService
from .features.operations.service import OperationsService
from .adapters.razorpay import RazorpayGateway

identity = IdentityService(db.engine)
catalog = CatalogService(db.engine)
checkout = CheckoutService(db.engine)
orders = OrderService(db.engine)
content = ContentService(db.engine)
payments = PaymentService(db.engine, RazorpayGateway())


def set_session(response, token):
    response.set_cookie(
        "shop_session",
        token,
        max_age=30 * 86400,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        path="/",
    )


def current_actor(request: Request, response: Response):
    actor = identity.resolve(request.cookies.get("shop_session"))
    if not actor:
        token, actor = identity.session()
        set_session(response, token)
    return actor


def get_catalog():
    return catalog


def get_checkout():
    return checkout


def get_content():
    return content


def get_orders():
    return orders


operations = OperationsService(db.engine)


def get_operations():
    return operations
