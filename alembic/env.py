import asyncio, os
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
from core.database import Base

# Import all models
from models import user, workout_session, personal_record
from models import body_measurement, reminder, referral
try:
    from models import gamification
except ImportError:
    pass

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

DB_URL = (
    "postgresql+asyncpg://"
    + os.environ.get("DB_USER","user") + ":"
    + os.environ.get("DB_PASS","pass") + "@"
    + os.environ.get("DB_HOST","localhost") + "/"
    + os.environ.get("DB_NAME","workout")
)


def run_migrations_offline():
    context.configure(url=DB_URL, target_metadata=target_metadata,
                      literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    engine = create_async_engine(DB_URL)
    async with engine.connect() as conn:
        await conn.run_sync(lambda c: context.configure(
            connection=c, target_metadata=target_metadata
        ))
        await conn.run_sync(lambda c: context.run_migrations())
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
