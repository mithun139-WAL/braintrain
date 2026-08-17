"""add_interview_plan_to_sessions

Revision ID: c1a9f2e7b3d4
Revises: 9404b39c9ad8
Create Date: 2026-07-20 09:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c1a9f2e7b3d4'
down_revision: Union[str, None] = '9404b39c9ad8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'interview_sessions',
        sa.Column('interview_plan', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('interview_sessions', 'interview_plan')
