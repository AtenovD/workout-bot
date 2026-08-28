# Alembic migrations

## Init (first time)
alembic revision --autogenerate -m "initial"
alembic upgrade head

## New migration
alembic revision --autogenerate -m "your message"
alembic upgrade head

## Rollback
alembic downgrade -1
