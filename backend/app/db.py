import uuid
import random
import time
from functools import wraps
from datetime import datetime, timezone
from sqlalchemy import (
    MetaData,
    Table,
    Column,
    String,
    Integer,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Text,
    create_engine,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.exc import DBAPIError
from .settings import settings

metadata = MetaData()


def retry_transient_write(function):
    """Retry a whole idempotent service write after PostgreSQL aborted its transaction."""

    @wraps(function)
    def wrapped(*args, **kwargs):
        for attempt in range(3):
            try:
                return function(*args, **kwargs)
            except DBAPIError as exc:
                state = getattr(exc.orig, "sqlstate", None) or getattr(exc.orig, "pgcode", None)
                if state not in {"40001", "40P01"} or attempt == 2:
                    raise
                time.sleep(random.uniform(0.01, min(0.2, 0.025 * 2**attempt)))

    return wrapped


def now():
    return datetime.now(timezone.utc)


def key():
    return Column("id", UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))


def created():
    return Column("created_at", DateTime(timezone=True), default=now, nullable=False)


profiles = Table(
    "profiles",
    metadata,
    key(),
    Column("email", String(254), unique=True, nullable=False),
    Column("name", String(100)),
    created(),
)
staff = Table(
    "staff_memberships",
    metadata,
    Column("user_id", ForeignKey("profiles.id"), primary_key=True),
    Column("role", String(30), nullable=False),
    Column("active", Boolean, default=True, nullable=False),
)
sessions = Table(
    "sessions",
    metadata,
    Column("token_hash", String(64), primary_key=True),
    Column("owner_id", String(64), nullable=False),
    Column("user_id", ForeignKey("profiles.id")),
    Column("assurance", String(10), default="aal1"),
    Column("expires_at", DateTime(timezone=True), nullable=False),
)
products = Table(
    "products",
    metadata,
    key(),
    Column("slug", String(150), unique=True, nullable=False),
    Column("title", String(200), nullable=False),
    Column("department", String(10), nullable=False),
    Column("category", String(60), nullable=False),
    Column("description", Text, nullable=False),
    Column("material", String(200), nullable=False),
    Column("care", Text, nullable=False),
    Column("details", JSONB, default=dict, nullable=False),
    Column("media", JSONB, default=list, nullable=False),
    Column("relations", JSONB, default=dict, nullable=False),
    Column("status", String(20), default="draft", nullable=False),
    Column("version", Integer, default=1, nullable=False),
    created(),
    CheckConstraint("department in ('women','home')"),
    CheckConstraint("status in ('draft','published','archived')"),
)
variants = Table(
    "product_variants",
    metadata,
    key(),
    Column("product_id", ForeignKey("products.id"), nullable=False),
    Column("sku", String(80), unique=True, nullable=False),
    Column("colour", String(60), nullable=False),
    Column("colour_hex", String(7), nullable=False),
    Column("size", String(80), nullable=False),
    Column("dimensions", String(100)),
    Column("price_paise", Integer, nullable=False),
    Column("compare_at_paise", Integer),
    Column("active", Boolean, default=True, nullable=False),
    UniqueConstraint("product_id", "colour", "size"),
    CheckConstraint("price_paise > 0"),
    CheckConstraint("compare_at_paise is null or compare_at_paise > price_paise"),
)
inventory = Table(
    "inventory",
    metadata,
    Column("variant_id", ForeignKey("product_variants.id"), primary_key=True),
    Column("on_hand", Integer, nullable=False, default=0),
    Column("reserved", Integer, nullable=False, default=0),
    CheckConstraint("on_hand >= reserved and reserved >= 0"),
)
movements = Table(
    "stock_movements",
    metadata,
    key(),
    Column("variant_id", ForeignKey("product_variants.id"), nullable=False),
    Column("operation_key", String(200), unique=True, nullable=False),
    Column("on_hand_delta", Integer, nullable=False),
    Column("reserved_delta", Integer, nullable=False),
    Column("reason", String(300), nullable=False),
    Column("actor", String(64)),
    created(),
)
carts = Table(
    "carts",
    metadata,
    Column("owner_id", String(64), primary_key=True),
    Column("version", Integer, default=1, nullable=False),
    Column("updated_at", DateTime(timezone=True), default=now, nullable=False),
)
cart_items = Table(
    "cart_items",
    metadata,
    Column("owner_id", ForeignKey("carts.owner_id"), primary_key=True),
    Column("variant_id", ForeignKey("product_variants.id"), primary_key=True),
    Column("quantity", Integer, nullable=False),
    CheckConstraint("quantity between 1 and 10"),
)
saved = Table(
    "saved_items",
    metadata,
    Column("owner_id", String(64), primary_key=True),
    Column("product_id", ForeignKey("products.id"), primary_key=True),
    created(),
)
orders = Table(
    "orders",
    metadata,
    key(),
    Column("number", BigInteger, autoincrement=True, unique=True, nullable=False),
    Column("owner_id", String(64), nullable=False),
    Column("request_key", String(100), nullable=False),
    Column("request_hash", String(64), nullable=False),
    Column("cart_version", Integer, nullable=False),
    Column("address", JSONB, nullable=False),
    Column("subtotal", Integer, nullable=False),
    Column("shipping", Integer, nullable=False),
    Column("total", Integer, nullable=False),
    Column("status", String(40), default="pending", nullable=False),
    Column("fulfilment", String(30), default="unfulfilled", nullable=False),
    Column("delivered_at", DateTime(timezone=True)),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("provider_order_id", String(100), unique=True),
    Column("payment_id", String(100), unique=True),
    Column("payment_mode", String(20), nullable=False),
    created(),
    UniqueConstraint("owner_id", "request_key"),
)
order_items = Table(
    "order_items",
    metadata,
    key(),
    Column("order_id", ForeignKey("orders.id"), nullable=False),
    Column("variant_id", ForeignKey("product_variants.id"), nullable=False),
    Column("snapshot", JSONB, nullable=False),
    Column("quantity", Integer, nullable=False),
    Column("price_paise", Integer, nullable=False),
    Column("reservation", String(20), default="active", nullable=False),
    Column("shipped", Integer, default=0, nullable=False),
    Column("returned", Integer, default=0, nullable=False),
    CheckConstraint(
        "quantity > 0 and shipped >= 0 and shipped <= quantity and returned >= 0 and returned <= shipped"
    ),
)
refunds = Table(
    "refunds",
    metadata,
    key(),
    Column("order_id", ForeignKey("orders.id"), nullable=False),
    Column("request_key", String(100), nullable=False),
    Column("amount", Integer, nullable=False),
    Column("status", String(30), default="requested", nullable=False),
    Column("provider_id", String(100), unique=True),
    Column("reason", String(300), nullable=False),
    created(),
    UniqueConstraint("order_id", "request_key"),
    CheckConstraint("amount > 0"),
)
shipments = Table(
    "shipments",
    metadata,
    key(),
    Column("order_id", ForeignKey("orders.id"), nullable=False),
    Column("tracking", String(300), nullable=False),
    Column("items", JSONB, nullable=False),
    Column("status", String(20), default="shipped", nullable=False),
    created(),
)
returns = Table(
    "return_requests",
    metadata,
    key(),
    Column("order_id", ForeignKey("orders.id"), nullable=False),
    Column("request_key", String(100), nullable=False),
    Column("items", JSONB, nullable=False),
    Column("reason", String(500), nullable=False),
    Column("status", String(30), default="requested", nullable=False),
    Column("sellable", Boolean),
    created(),
    UniqueConstraint("order_id", "request_key"),
)
campaigns = Table(
    "campaign_revisions",
    metadata,
    key(),
    Column("department", String(10), nullable=False),
    Column("revision", Integer, nullable=False),
    Column("content", JSONB, nullable=False),
    Column("published", Boolean, nullable=False, default=False),
    created(),
    UniqueConstraint("department", "revision"),
)
Index(
    "one_live_campaign", campaigns.c.department, unique=True, postgresql_where=campaigns.c.published.is_(True)
)
jobs = Table(
    "outbox_jobs",
    metadata,
    key(),
    Column("operation_key", String(200), nullable=False, unique=True),
    Column("kind", String(40), nullable=False),
    Column("payload", JSONB, nullable=False),
    Column("status", String(20), default="pending", nullable=False),
    Column("attempts", Integer, default=0, nullable=False),
    Column("due_at", DateTime(timezone=True), default=now, nullable=False),
    Column("lease_until", DateTime(timezone=True)),
    Column("claim_token", String(36)),
    Column("completed_at", DateTime(timezone=True)),
    Column("last_error", String(500)),
    created(),
)
events = Table(
    "webhook_events",
    metadata,
    Column("event_id", String(150), primary_key=True),
    Column("body_hash", String(64), nullable=False),
    Column("payload", JSONB, nullable=False),
    created(),
)
audit = Table(
    "audit_events",
    metadata,
    key(),
    Column("actor", String(64)),
    Column("action", String(100), nullable=False),
    Column("target", String(100)),
    Column("detail", JSONB, default=dict, nullable=False),
    created(),
)
support = Table(
    "support_requests",
    metadata,
    key(),
    Column("owner_id", String(64), nullable=False),
    Column("request_key", String(100), nullable=False),
    Column("email", String(254), nullable=False),
    Column("subject", String(200), nullable=False),
    Column("message", Text, nullable=False),
    Column("status", String(20), default="open", nullable=False),
    created(),
    UniqueConstraint("owner_id", "request_key"),
)
settings_table = Table(
    "shop_settings",
    metadata,
    Column("key", String(50), primary_key=True),
    Column("value", JSONB, nullable=False),
)
limits = Table(
    "rate_limits",
    metadata,
    Column("key", String(160), primary_key=True),
    Column("window", BigInteger, nullable=False),
    Column("count", Integer, nullable=False),
)

def create_database_engine(role: str = "api"):
    pools = {"api": (5, 2), "commerce": (2, 0), "media": (1, 0)}
    if role not in pools:
        raise ValueError(f"Unsupported database pool role: {role}")
    pool_size, max_overflow = pools[role]
    options = "-c statement_timeout=10000 -c lock_timeout=2000 -c idle_in_transaction_session_timeout=30000"
    return create_engine(
        settings.database_url,
        pool_size=int(settings.db_pool_size or pool_size),
        max_overflow=int(settings.db_pool_overflow or max_overflow),
        pool_timeout=5,
        pool_recycle=1800,
        pool_pre_ping=True,
        connect_args={"options": options},
    )


engine = create_database_engine(settings.db_role)
