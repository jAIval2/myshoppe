"""Add worker claim fencing, activity clocks and commerce hot-path indexes."""

from alembic import op

revision = "003_worker_indexes"
down_revision = "002_delivery_time"


def upgrade():
    op.execute("ALTER TABLE carts ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now()")
    op.execute("ALTER TABLE outbox_jobs ADD COLUMN IF NOT EXISTS claim_token varchar(36)")
    op.execute("ALTER TABLE outbox_jobs ADD COLUMN IF NOT EXISTS completed_at timestamptz")
    # Run online on populated tables. If interrupted, inspect/drop any invalid
    # index concurrently before retrying this migration.
    with op.get_context().autocommit_block():
        for statement in (
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS orders_pending_expiry_idx ON orders (expires_at) WHERE status = 'pending'",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS order_items_order_idx ON order_items (order_id)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS shipments_order_idx ON shipments (order_id)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS sessions_owner_idx ON sessions (owner_id)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS sessions_expiry_idx ON sessions (expires_at)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS saved_items_product_idx ON saved_items (product_id)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS cart_items_variant_idx ON cart_items (variant_id)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS carts_activity_idx ON carts (updated_at)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS outbox_completed_idx ON outbox_jobs (completed_at) WHERE status = 'done'",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS limits_window_idx ON rate_limits (window)",
        ):
            op.execute(statement)


def downgrade():
    raise RuntimeError("Forward-only: worker claims and commerce history must be preserved")
