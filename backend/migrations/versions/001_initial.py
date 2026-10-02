"""Initial commerce schema, reviewed constraints and PostgreSQL search index."""

from alembic import op
from pathlib import Path

revision = "001"
down_revision = None


def upgrade():
    for statement in Path(__file__).with_name("001_schema.sql").read_text().split(";"):
        if statement.strip():
            op.execute(statement)
    op.execute("CREATE SEQUENCE order_number_seq START 10001")
    op.execute("ALTER TABLE orders ALTER COLUMN number SET DEFAULT nextval('order_number_seq')")
    op.execute(
        "CREATE INDEX product_search ON products USING gin(to_tsvector('english', title || ' ' || material || ' ' || category))"
    )
    op.execute("CREATE INDEX due_jobs ON outbox_jobs(status, due_at)")
    op.execute("CREATE INDEX owner_orders ON orders(owner_id, created_at DESC)")


def downgrade():
    raise RuntimeError("Use forward migrations; restore is an explicit operational action")
