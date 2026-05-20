"""
SQLAlchemy declarative base.

All models import Base from here. Alembic's env.py also imports Base.metadata
for autogenerate to detect schema changes.

Single import point — prevents circular dependency issues.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Shared base class for all ORM models.

    Using DeclarativeBase (SQLAlchemy 2.0 style) gives us:
    - Full type inference with Mapped[] annotations
    - Registry-based relationship resolution
    - Native support for async sessions
    """
    pass
