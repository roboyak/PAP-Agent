"""Enable pgvector; domain tables arrive in PR02."""

from alembic import op

revision = "0001_enable_pgvector"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    # Keep the shared extension: removing it could destroy later vector data.
    pass
