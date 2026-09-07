"""Persist calculation evidence and allow an explicitly unconfigured equipment cap."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0004_calculations"
down_revision = "0003_evidence_records"
branch_labels = depends_on = None


def upgrade():
    op.alter_column("reserve_policies", "max_extra_power_kw", nullable=True)
    op.create_table(
        "calculation_records",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("evidence_id", sa.Uuid(), sa.ForeignKey("evidence_records.id"), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
    )


def downgrade():
    op.drop_table("calculation_records")
    # Keep nullable caps: reverting must not invent a real equipment rating.
