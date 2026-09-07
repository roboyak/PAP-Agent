"""Persist sanitized MCP acquisition and T3 decisions."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0003_evidence_records"
down_revision = "0002_domain_evidence"
branch_labels = depends_on = None


def upgrade():
    op.create_table(
        "evidence_records",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("payload", JSONB, nullable=False),
    )


def downgrade():
    op.drop_table("evidence_records")
