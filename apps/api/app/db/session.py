"""
Async SQLAlchemy engine and session factory.

Design decisions:
- `create_async_engine` with asyncpg driver for non-blocking DB I/O
- `expire_on_commit=False` — critical for async: prevents SQLAlchemy from
  expiring attributes after commit (we can't reload synchronously in async context)
- `pool_pre_ping=True` — validates connections before use (handles DB restarts)
- `echo=True` in development logs every SQL query for debugging
- Session is yielded via get_db() in deps.py — never instantiated manually in routes
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.is_development,   # logs SQL queries in dev
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,             # validates connections before use
    pool_recycle=3600,              # recycle connections every hour
)

# async_sessionmaker is the SQLAlchemy 2.0 replacement for sessionmaker
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,         # required for async — see module docstring
    autocommit=False,
    autoflush=False,
)
