"""Separate observations, derived metrics, and confidence feedback."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0007_outcomes"
down_revision = "0006_publications"
branch_labels = depends_on = None


def upgrade():
    op.create_table(
        "outcome_records",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("publication_id", sa.Uuid(), sa.ForeignKey("pap_publications.id")),
        sa.Column("payload", JSONB, nullable=False),
    )
    op.create_table(
        "outcome_metrics",
        sa.Column("id", sa.Uuid(), sa.ForeignKey("outcome_records.id"), primary_key=True),
        sa.Column("source_kind", sa.Text(), nullable=False),
        sa.Column("forecast_version", sa.Text(), nullable=False),
        sa.Column("solar_bias_kw", sa.Float(), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
    )
    op.create_table(
        "calibration_records",
        sa.Column("source_kind", sa.Text(), primary_key=True),
        sa.Column("forecast_version", sa.Text(), primary_key=True),
        sa.Column("payload", JSONB, nullable=False),
    )


def downgrade():
    op.drop_table("calibration_records")
    op.drop_table("outcome_metrics")
    op.drop_table("outcome_records")
