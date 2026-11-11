"""Versioned bespoke briefs and access-controlled references."""

from alembic import op

revision = "004_bespoke"
down_revision = "003_worker_indexes"


def upgrade():
    op.execute("""CREATE TABLE bespoke_designs (
      id uuid PRIMARY KEY, owner_id varchar(64) NOT NULL, version integer NOT NULL DEFAULT 1,
      status varchar(20) NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','submitted','reviewing','agreed','ready')),
      design jsonb NOT NULL DEFAULT '{}', review jsonb NOT NULL DEFAULT '{}', agreement jsonb,
      history jsonb NOT NULL DEFAULT '[]', updated_at timestamptz NOT NULL DEFAULT now(),
      created_at timestamptz NOT NULL DEFAULT now())""")
    op.execute("CREATE INDEX ix_bespoke_designs_owner_id ON bespoke_designs(owner_id)")
    op.execute("""CREATE TABLE bespoke_assets (
      id uuid PRIMARY KEY, design_id uuid NOT NULL REFERENCES bespoke_designs(id),
      content_type varchar(50) NOT NULL, data bytea NOT NULL, created_at timestamptz NOT NULL DEFAULT now())""")
    op.execute("CREATE INDEX ix_bespoke_assets_design_id ON bespoke_assets(design_id)")


def downgrade():
    raise RuntimeError("Forward-only: preserve customer briefs and references")
