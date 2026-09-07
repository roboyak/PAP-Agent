"""Persist the evidence used by the first PAP slice."""

import sqlalchemy as sa
from alembic import op

revision = "0002_domain_evidence"
down_revision = "0001_enable_pgvector"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "telemetry_snapshots",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("battery_voltage_v", sa.Float(), nullable=False),
        sa.Column("solar_power_kw", sa.Float(), nullable=False),
        sa.Column("load_power_kw", sa.Float(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("data_mode", sa.String(32), nullable=False),
        sa.Column("measurement_time_verified", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_telemetry_observed_at", "telemetry_snapshots", ["observed_at"])
    op.create_table(
        "reserve_policies",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("min_battery_voltage_v", sa.Float(), nullable=False),
        sa.Column("max_extra_power_kw", sa.Float(), nullable=False),
    )
    op.create_table(
        "scenarios",
        sa.Column("name", sa.String(64), primary_key=True),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column(
            "telemetry_id", sa.Uuid(), sa.ForeignKey("telemetry_snapshots.id"), nullable=False
        ),
        sa.Column("policy_id", sa.String(64), sa.ForeignKey("reserve_policies.id"), nullable=False),
    )
    op.create_table(
        "weather_intervals",
        sa.Column(
            "scenario_name", sa.String(64), sa.ForeignKey("scenarios.name"), primary_key=True
        ),
        sa.Column("starts_at", sa.DateTime(timezone=True), primary_key=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("solar_factor", sa.Float(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("weather_intervals")
    op.drop_table("scenarios")
    op.drop_table("reserve_policies")
    op.drop_table("telemetry_snapshots")
