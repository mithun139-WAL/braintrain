"""Fix skill_tags and user_skill_preferences schema

Revision ID: 0006_fix_skill_tables
Revises: 0005_add_evaluation_job_columns
Create Date: 2026-05-21

Aligns skill_tags and user_skill_preferences with their ORM models:

  skill_tags
    - add is_global (Boolean, NOT NULL, default false)
    - add created_by_user_id (UUID, nullable, FK → users.id)

  user_skill_preferences
    - rename proficiency_level → level
    - make level NOT NULL (backfill existing NULLs with 'BEGINNER')
    - add updated_at (DateTime, NOT NULL, server_default now())
    - drop old FK constraints (no CASCADE) and recreate with ondelete=CASCADE
    - add unique constraint uq_user_skill_preference (user_id, skill_tag_id)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_fix_skill_tables"
down_revision: Union[str, None] = "0005_add_evaluation_job_columns"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── skill_tags: add is_global + created_by_user_id ────────────────────────
    op.add_column(
        "skill_tags",
        sa.Column(
            "is_global",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "skill_tags",
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_skill_tags_created_by_user_id",
        "skill_tags",
        "users",
        ["created_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ── user_skill_preferences: rename proficiency_level → level ─────────────
    op.alter_column(
        "user_skill_preferences",
        "proficiency_level",
        new_column_name="level",
    )
    # Backfill any NULLs before enforcing NOT NULL
    op.execute(
        "UPDATE user_skill_preferences SET level = 'BEGINNER' WHERE level IS NULL"
    )
    op.alter_column(
        "user_skill_preferences",
        "level",
        nullable=False,
    )

    # ── user_skill_preferences: add updated_at ────────────────────────────────
    op.add_column(
        "user_skill_preferences",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # ── user_skill_preferences: drop old FKs (no CASCADE) and recreate ────────
    # The FK constraint names depend on PostgreSQL auto-naming from migration 0001.
    # PostgreSQL names them as <table>_<col>_fkey by default.
    op.drop_constraint(
        "user_skill_preferences_user_id_fkey",
        "user_skill_preferences",
        type_="foreignkey",
    )
    op.drop_constraint(
        "user_skill_preferences_skill_tag_id_fkey",
        "user_skill_preferences",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_user_skill_preferences_user_id",
        "user_skill_preferences",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_user_skill_preferences_skill_tag_id",
        "user_skill_preferences",
        "skill_tags",
        ["skill_tag_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # ── user_skill_preferences: unique constraint ─────────────────────────────
    op.create_unique_constraint(
        "uq_user_skill_preference",
        "user_skill_preferences",
        ["user_id", "skill_tag_id"],
    )


def downgrade() -> None:
    # ── user_skill_preferences ────────────────────────────────────────────────
    op.drop_constraint(
        "uq_user_skill_preference", "user_skill_preferences", type_="unique"
    )
    op.drop_constraint(
        "fk_user_skill_preferences_skill_tag_id",
        "user_skill_preferences",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_user_skill_preferences_user_id",
        "user_skill_preferences",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "user_skill_preferences_skill_tag_id_fkey",
        "user_skill_preferences",
        "skill_tags",
        ["skill_tag_id"],
        ["id"],
    )
    op.create_foreign_key(
        "user_skill_preferences_user_id_fkey",
        "user_skill_preferences",
        "users",
        ["user_id"],
        ["id"],
    )
    op.drop_column("user_skill_preferences", "updated_at")
    op.alter_column(
        "user_skill_preferences",
        "level",
        nullable=True,
    )
    op.alter_column(
        "user_skill_preferences",
        "level",
        new_column_name="proficiency_level",
    )

    # ── skill_tags ────────────────────────────────────────────────────────────
    op.drop_constraint(
        "fk_skill_tags_created_by_user_id", "skill_tags", type_="foreignkey"
    )
    op.drop_column("skill_tags", "created_by_user_id")
    op.drop_column("skill_tags", "is_global")
