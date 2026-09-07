"""Canonical PAP publications and evidence links."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0006_publications"
down_revision = "0005_episodes"
branch_labels = depends_on = None


def upgrade():
    op.create_table(
        "pap_publications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("evidence_id", sa.Uuid(), sa.ForeignKey("evidence_records.id"), nullable=False),
        sa.Column("calculation_id", sa.Uuid(), sa.ForeignKey("calculation_records.id")),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
    )
    op.create_index("ix_publication_generated", "pap_publications", ["generated_at"])


def downgrade():
    op.drop_table("pap_publications")
