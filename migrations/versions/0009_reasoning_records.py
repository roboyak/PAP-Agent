"""Domain-owned retrieval and agent audit records, separate from checkpoints."""

from alembic import op

revision = "0009_reasoning_records"
down_revision = "0008_semantic_memory"
branch_labels = depends_on = None


def upgrade():
    op.execute("""CREATE TABLE reasoning_records (
        id uuid PRIMARY KEY, episode_id uuid NOT NULL, kind text NOT NULL,
        payload jsonb NOT NULL
    )""")
    op.execute("CREATE INDEX reasoning_episode ON reasoning_records (episode_id)")


def downgrade():
    op.drop_table("reasoning_records")
