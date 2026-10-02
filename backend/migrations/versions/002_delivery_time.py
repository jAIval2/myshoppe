"""Track delivery time for return eligibility."""

from alembic import op

revision = "002_delivery_time"
down_revision = "001"


def upgrade():
    op.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivered_at timestamptz")


def downgrade():
    raise RuntimeError("Forward-only: delivery history must be preserved")
