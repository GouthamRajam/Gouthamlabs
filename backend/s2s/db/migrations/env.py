"""Alembic environment: the database URL comes from S2S_DATABASE_URL (s2s.config)."""
from alembic import context
from sqlalchemy import create_engine, pool

from s2s.config import settings
from s2s.db.models import Base

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=settings().database_url, target_metadata=target_metadata,
                      literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = context.config.attributes.get("database_url") or settings().database_url
    connectable = create_engine(url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
