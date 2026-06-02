"""Add missing columns to evaluation_jobs

Revision ID: 0005_add_evaluation_job_columns
Revises: 0004_add_billing_fields
Create Date: 2026-05-21

The ORM model (app/db/models/evaluation_job.py) was extended with three
timing/retry columns and two supporting indexes that were never reflected in a
migration.  As a result, any INSERT into evaluation_jobs would fail because
SQLAlchemy includes those columns in the statement but the DB table does not
have them, causing a 500 on PUT /sessions/{id}/complete.

Columns added:
  - next_retry_at       — when the worker should next attempt the job (NULL = ready now)
  - evaluation_started_at — timestamp the worker began processing (used by zombie recovery)
  - evaluation_completed_at — timestamp the job finished successfully

Indexes added:
  - ix_evaluation_jobs_status_next_retry_at_created_at  (used by claim_next_pending_job query)
  - ix_evaluation_jobs_status_evaluation_started_at     (used by recover_zombie_jobs query)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_add_evaluation_job_columns"
down_revision: Union[str, None] = "0004_add_billing_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── New columns ────────────────────────────────────────────────────────────
    op.add_column(
        "evaluation_jobs",
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "evaluation_jobs",
        sa.Column("evaluation_started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "evaluation_jobs",
        sa.Column("evaluation_completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── New indexes (mirror the ORM __table_args__) ────────────────────────────
    op.create_index(
        "ix_evaluation_jobs_status_next_retry_at_created_at",
        "evaluation_jobs",
        ["status", "next_retry_at", "created_at"],
    )
    op.create_index(
        "ix_evaluation_jobs_status_evaluation_started_at",
        "evaluation_jobs",
        ["status", "evaluation_started_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_evaluation_jobs_status_evaluation_started_at",
        table_name="evaluation_jobs",
    )
    op.drop_index(
        "ix_evaluation_jobs_status_next_retry_at_created_at",
        table_name="evaluation_jobs",
    )
    op.drop_column("evaluation_jobs", "evaluation_completed_at")
    op.drop_column("evaluation_jobs", "evaluation_started_at")
    op.drop_column("evaluation_jobs", "next_retry_at")
