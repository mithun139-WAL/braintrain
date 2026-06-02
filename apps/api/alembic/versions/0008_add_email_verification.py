"""add email verification fields to users

Revision ID: 0008_add_email_verification
Revises: 0007_add_is_voice_to_sessions
Create Date: 2026-05-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008_add_email_verification"
down_revision: Union[str, None] = "0007_add_is_voice_to_sessions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "email_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "users",
        sa.Column("email_confirmation_token", sa.String(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "email_confirmation_expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.create_unique_constraint(
        "uq_users_email_confirmation_token",
        "users",
        ["email_confirmation_token"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_users_email_confirmation_token", "users", type_="unique")
    op.drop_column("users", "email_confirmation_expires_at")
    op.drop_column("users", "email_confirmation_token")
    op.drop_column("users", "email_verified")
