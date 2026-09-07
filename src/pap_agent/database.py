from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from pap_agent.config import Settings


class Database:
    """One connection pool; each session commits on success or rolls back on error."""

    def __init__(self, settings: Settings):
        self.engine = create_engine(
            settings.database_url.get_secret_value(),
            pool_pre_ping=True,
            pool_timeout=3,
            connect_args={"connect_timeout": 3, "options": "-c statement_timeout=3000"},
        )
        self.sessions = sessionmaker(bind=self.engine)

    @contextmanager
    def session(self) -> Iterator[Session]:
        with self.sessions.begin() as session:
            yield session

    def has_pgvector(self) -> bool:
        """A real round trip checks PostgreSQL and its installed vector extension."""
        with self.session() as session:
            session.execute(text("SELECT 1")).scalar_one()
            return bool(
                session.execute(
                    text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')")
                ).scalar_one()
            )

    def close(self) -> None:
        self.engine.dispose()
