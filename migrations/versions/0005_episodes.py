"""Canonical episode summaries; checkpoint tables are owned by the official saver."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0005_episodes"
down_revision = "0004_calculations"
branch_labels = depends_on = None


def upgrade():
    op.create_table(
        "episode_records",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("payload", JSONB, nullable=False),
    )


def downgrade():
    op.drop_table("episode_records")
