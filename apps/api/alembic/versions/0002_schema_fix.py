"""Schema fixes — align DB tables with ORM models

Revision ID: 0002_schema_fix
Revises: 0001_initial_schema
Create Date: 2026-05-19

Covers every mismatch found between the ORM model definitions and the
tables actually created by 0001_initial_schema:

  topics              — add parent_topic_id self-ref FK, unique constraint, index
  question_bank       — add source, usage_count columns + performance indexes
  question_instances  — add unique constraint + corrected index
  response_instances  — rename transcript→transcribed_text, add missing columns,
                        unique constraint, and indexes
  evaluation_reports  — rename evaluated_at→created_at, add cost-tracking + feedback
                        columns, deleted_at, and analytics indexes
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_schema_fix"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # ── topics: parent_topic_id self-referential FK ────────────────────────────
    op.add_column(
        "topics",
        sa.Column("parent_topic_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_topics_parent_topic_id",
        "topics", "topics",
        ["parent_topic_id"], ["id"],
    )
    # Prevent duplicate topic names within the same global/user scope
    op.create_unique_constraint(
        "uq_topic_name_is_global", "topics", ["name", "is_global"]
    )
    # Supports list query: filter by (is_global OR created_by_user_id) + not deleted
    op.create_index(
        "ix_topics_created_by_user_id_deleted_at",
        "topics", ["created_by_user_id", "deleted_at"],
    )

    # ── question_bank: source + usage_count + indexes ──────────────────────────
    op.add_column(
        "question_bank",
        sa.Column(
            "source", sa.String(), nullable=False, server_default="HUMAN"
        ),
    )
    op.add_column(
        "question_bank",
        sa.Column(
            "usage_count", sa.Integer(), nullable=False, server_default="0"
        ),
    )
    # Bank-first selection: pick by topic + difficulty, exclude deleted
    op.create_index(
        "ix_question_banks_topic_difficulty_deleted_at",
        "question_bank", ["topic_id", "difficulty", "deleted_at"],
    )
    # Filter HUMAN vs GENERATED per topic (admin / analytics)
    op.create_index(
        "ix_question_banks_source_topic_id",
        "question_bank", ["source", "topic_id"],
    )
    # Retained for query compatibility
    op.create_index(
        "ix_question_banks_topic_id_difficulty",
        "question_bank", ["topic_id", "difficulty"],
    )

    # ── question_instances: unique constraint + corrected index ────────────────
    # Enforce unique sequence positions per session
    op.create_unique_constraint(
        "uq_question_instance_session_order",
        "question_instances", ["session_id", "sequence_order"],
    )
    # Drop the original index (created with a different name in migration 0001)
    op.drop_index(
        "ix_question_instances_session_id_sequence_order",
        table_name="question_instances",
    )
    # Re-create with the full name the ORM model declares (includes deleted_at)
    op.create_index(
        "ix_question_instances_session_id_sequence_order_deleted_at",
        "question_instances", ["session_id", "sequence_order", "deleted_at"],
    )

    # ── response_instances: rename column + add missing columns ───────────────
    # 0001 named it 'transcript'; ORM model uses 'transcribed_text'
    op.alter_column(
        "response_instances", "transcript",
        new_column_name="transcribed_text",
    )
    # Capture typed-answer character count for behavioral analytics
    op.add_column(
        "response_instances",
        sa.Column("answer_length", sa.Integer(), nullable=False, server_default="0"),
    )
    # Whisper returns audio duration for cost tracking
    op.add_column(
        "response_instances",
        sa.Column("audio_duration_seconds", sa.Float(), nullable=True),
    )
    # Server-computed timing scores (written by evaluation worker)
    op.add_column(
        "response_instances",
        sa.Column("pressure_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "response_instances",
        sa.Column("thinking_depth_score", sa.Float(), nullable=True),
    )
    # Optional LLM explanation (currently empty; reserved for future use)
    op.add_column(
        "response_instances",
        sa.Column("evaluation_explanation", sa.Text(), nullable=True),
    )
    # Soft-delete support — present in ORM model but absent from 0001 migration
    op.add_column(
        "response_instances",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    # One response per question — enforced here and in service layer
    op.create_unique_constraint(
        "uq_response_instance_question_id",
        "response_instances", ["question_id"],
    )
    # Adaptive engine reads overall_score for last N responses
    op.create_index(
        "ix_response_instances_question_id_overall_score",
        "response_instances", ["question_id", "overall_score"],
    )
    # Audio worker: find PENDING transcription jobs quickly
    op.create_index(
        "ix_response_instances_audio_processing_status_created_at",
        "response_instances", ["audio_processing_status", "created_at"],
    )

    # ── evaluation_reports: rename column + add missing columns ───────────────
    # 0001 called this 'evaluated_at'; ORM model uses 'created_at'
    op.alter_column(
        "evaluation_reports", "evaluated_at",
        new_column_name="created_at",
    )
    # Cost & model traceability fields (all nullable — absent for stub evaluations)
    op.add_column(
        "evaluation_reports",
        sa.Column("prompt_version", sa.String(), nullable=True, server_default="stub"),
    )
    op.add_column(
        "evaluation_reports",
        sa.Column("model_used", sa.String(), nullable=True),
    )
    op.add_column(
        "evaluation_reports",
        sa.Column("input_tokens", sa.Integer(), nullable=True),
    )
    op.add_column(
        "evaluation_reports",
        sa.Column("output_tokens", sa.Integer(), nullable=True),
    )
    op.add_column(
        "evaluation_reports",
        sa.Column("estimated_cost_usd", sa.Float(), nullable=True),
    )
    # Human-readable feedback (replaces legacy 'summary' column)
    op.add_column(
        "evaluation_reports",
        sa.Column(
            "feedback_summary",
            sa.Text(),
            nullable=False,
            server_default="",
        ),
    )
    # Structured improvement suggestions keyed by dimension
    op.add_column(
        "evaluation_reports",
        sa.Column(
            "improvement_suggestions",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
        ),
    )
    # Soft-delete support (consistent with other tables)
    op.add_column(
        "evaluation_reports",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Cross-session trend queries sorted by date
    op.create_index(
        "ix_evaluation_reports_created_at",
        "evaluation_reports", ["created_at"],
    )
    # Billing intelligence: cost per model over time
    op.create_index(
        "ix_evaluation_reports_model_used_created_at",
        "evaluation_reports", ["model_used", "created_at"],
    )


def downgrade() -> None:
    # ── evaluation_reports ─────────────────────────────────────────────────────
    op.drop_index("ix_evaluation_reports_model_used_created_at", table_name="evaluation_reports")
    op.drop_index("ix_evaluation_reports_created_at", table_name="evaluation_reports")
    op.drop_column("evaluation_reports", "deleted_at")
    op.drop_column("evaluation_reports", "improvement_suggestions")
    op.drop_column("evaluation_reports", "feedback_summary")
    op.drop_column("evaluation_reports", "estimated_cost_usd")
    op.drop_column("evaluation_reports", "output_tokens")
    op.drop_column("evaluation_reports", "input_tokens")
    op.drop_column("evaluation_reports", "model_used")
    op.drop_column("evaluation_reports", "prompt_version")
    op.alter_column("evaluation_reports", "created_at", new_column_name="evaluated_at")

    # ── response_instances ─────────────────────────────────────────────────────
    op.drop_index(
        "ix_response_instances_audio_processing_status_created_at",
        table_name="response_instances",
    )
    op.drop_index(
        "ix_response_instances_question_id_overall_score",
        table_name="response_instances",
    )
    op.drop_constraint("uq_response_instance_question_id", "response_instances", type_="unique")
    op.drop_column("response_instances", "deleted_at")
    op.drop_column("response_instances", "evaluation_explanation")
    op.drop_column("response_instances", "thinking_depth_score")
    op.drop_column("response_instances", "pressure_score")
    op.drop_column("response_instances", "audio_duration_seconds")
    op.drop_column("response_instances", "answer_length")
    op.alter_column("response_instances", "transcribed_text", new_column_name="transcript")

    # ── question_instances ─────────────────────────────────────────────────────
    op.drop_index(
        "ix_question_instances_session_id_sequence_order_deleted_at",
        table_name="question_instances",
    )
    op.create_index(
        "ix_question_instances_session_id_sequence_order",
        "question_instances", ["session_id", "sequence_order"],
    )
    op.drop_constraint(
        "uq_question_instance_session_order", "question_instances", type_="unique"
    )

    # ── question_bank ──────────────────────────────────────────────────────────
    op.drop_index("ix_question_banks_topic_id_difficulty", table_name="question_bank")
    op.drop_index("ix_question_banks_source_topic_id", table_name="question_bank")
    op.drop_index("ix_question_banks_topic_difficulty_deleted_at", table_name="question_bank")
    op.drop_column("question_bank", "usage_count")
    op.drop_column("question_bank", "source")

    # ── topics ─────────────────────────────────────────────────────────────────
    op.drop_index("ix_topics_created_by_user_id_deleted_at", table_name="topics")
    op.drop_constraint("uq_topic_name_is_global", "topics", type_="unique")
    op.drop_constraint("fk_topics_parent_topic_id", "topics", type_="foreignkey")
    op.drop_column("topics", "parent_topic_id")
