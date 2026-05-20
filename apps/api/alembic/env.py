"""
Alembic async migration environment.

Reads DATABASE_URL from app/core/config.py — never from alembic.ini.
Uses asyncpg driver via run_async_migrations() for async SQLAlchemy compatibility.

All models are imported via app.db.models to register them with Base.metadata
so that `alembic revision --autogenerate` can detect schema changes.
"""
import asyncio
import logging
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ── Import Base and ALL models ─────────────────────────────────────────────────
# Base.metadata must know about every table for autogenerate to work.
# This import triggers all model registrations via app/db/models/__init__.py
from app.db.base import Base
import app.db.models  # noqa: F401 — registers all models with Base.metadata

# ── Alembic config object ──────────────────────────────────────────────────────
config = context.config

# Set up logging from alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")

# ── Target metadata for autogenerate ──────────────────────────────────────────
target_metadata = Base.metadata


def get_database_url() -> str:
    """Read DATABASE_URL from app settings (never from alembic.ini)."""
    from app.core.config import get_settings
    url = get_settings().database_url
    # Alembic autogenerate works with asyncpg, but sync migration runner needs
    # the sync driver for offline mode. asyncpg is fine for online migrations.
    return url


# ── Offline migrations (generates SQL without connecting to DB) ─────────────
def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    Generates migration SQL without a live DB connection.
    Useful for reviewing what changes will be applied before running them.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,         # detect column type changes
        compare_server_default=True,  # detect server_default changes
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online migrations (connects to DB and applies changes) ──────────────────
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create async engine and run migrations via a sync connection wrapper."""
    url = get_database_url()

    connectable = async_engine_from_config(
        {"sqlalchemy.url": url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # no connection pooling during migrations
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migration mode."""
    asyncio.run(run_async_migrations())


# ── Entry point ────────────────────────────────────────────────────────────────
if context.is_offline_mode():
    logger.info("Running migrations in offline mode")
    run_migrations_offline()
else:
    logger.info("Running migrations in online mode")
    run_migrations_online()
