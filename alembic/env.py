import asyncio, os
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
from core.db import Base

# Import the canonical model registry. Importing legacy duplicate modules here
# can declare the same table twice and break Alembic before migrations run.
import models  # noqa: F401

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

DB_URL = (
    "postgresql+asyncpg://"
    + os.environ.get("POSTGRES_USER","user") + ":"
    + os.environ.get("POSTGRES_PASSWORD","pass") + "@"
    + os.environ.get("POSTGRES_HOST","localhost") + "/"
    + os.environ.get("POSTGRES_DB","workout")
)


def run_migrations_offline():
    context.configure(url=DB_URL, target_metadata=target_metadata,
                      literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    engine = create_async_engine(DB_URL)
    async with engine.connect() as conn:
        await conn.run_sync(do_run_migrations)
    await engine.dispose()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
