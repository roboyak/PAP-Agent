from alembic import context

from pap_agent.config import Settings
from pap_agent.database import Database

if context.is_offline_mode():
    context.configure(url=Settings().database_url.get_secret_value(), literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    database = Database(Settings())
    try:
        with database.engine.connect() as connection:
            context.configure(connection=connection)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        database.close()
