"""Persist replay progress; PAP facts remain in their existing domain tables."""

from alembic import op

revision = "0010_simulations"
down_revision = "0009_reasoning_records"
branch_labels = depends_on = None


def upgrade():
    op.execute("""CREATE TABLE simulations (
        id uuid PRIMARY KEY, created_at timestamptz NOT NULL, payload jsonb NOT NULL
    )""")


def downgrade():
    op.drop_table("simulations")
