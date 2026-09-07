"""Exact cosine retrieval for a small corpus; no ANN index needed."""

from alembic import op

revision = "0008_semantic_memory"
down_revision = "0007_outcomes"
branch_labels = depends_on = None


def upgrade():
    op.execute("""CREATE TABLE semantic_memory (
        id uuid PRIMARY KEY, content text NOT NULL, source_kind text NOT NULL,
        source_id text NOT NULL, model text NOT NULL, embedding vector(768) NOT NULL,
        metadata jsonb NOT NULL, validated boolean NOT NULL DEFAULT true,
        created_at timestamptz NOT NULL DEFAULT now(), valid_until timestamptz
    )""")


def downgrade():
    op.drop_table("semantic_memory")
