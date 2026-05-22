"""add is_voice to sessions

Revision ID: 0007_add_is_voice_to_sessions
Revises: 0006_fix_skill_tables
Create Date: 2026-05-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_add_is_voice_to_sessions"
down_revision: Union[str, None] = "0006_fix_skill_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "interview_sessions",
        sa.Column(
            "is_voice",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )


def downgrade() -> None:
    op.drop_column("interview_sessions", "is_voice")
