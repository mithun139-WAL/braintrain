"""
Evaluation repository — all DB read/write operations for the evaluation module.

Rules:
  - No business logic, no HTTP objects, no imports from other feature modules
  - selectinload used for all nested relationships
  - Claim query uses SELECT ... FOR UPDATE SKIP LOCKED to prevent double-processing
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.evaluation_job import EvaluationJob
from app.db.models.evaluation_report import EvaluationReport
from app.db.models.enums import EvaluationJobStatus
from app.db.models.interview_session import InterviewSession
from app.db.models.question_instance import QuestionInstance
from app.db.models.response_instance import ResponseInstance
from app.db.models.topic import Topic  # noqa: F401 — needed for selectinload of InterviewSession.topic

# ── Retry backoff delays per attempt (spec §4) ────────────────────────────────
# attempt 1 → 30s, attempt 2 → 2 min, attempt 3 → 10 min
RETRY_DELAYS_SECONDS: dict[int, int] = {
    1: 30,
    2: 2 * 60,
    3: 10 * 60,
}

MAX_ATTEMPTS = 3

# Jobs stuck in PROCESSING longer than this are considered zombies (spec §6)
ZOMBIE_THRESHOLD_SECONDS = 10 * 60  # 10 minutes


# ── Session + questions ───────────────────────────────────────────────────────


async def get_session_for_evaluation(
    db: AsyncSession, session_id: uuid.UUID
) -> Optional[InterviewSession]:
    """Load session with evaluation + topic relationships for evaluation pipeline."""
    result = await db.execute(
        select(InterviewSession)
        .where(
            InterviewSession.id == session_id,
            InterviewSession.deleted_at.is_(None),
        )
        .options(
            selectinload(InterviewSession.evaluation),
            selectinload(InterviewSession.topic),
        )
    )
    return result.scalar_one_or_none()


async def get_session_for_user(
    db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID
) -> Optional[InterviewSession]:
    """Verify session belongs to user (ownership check before user-facing analyze)."""
    result = await db.execute(
        select(InterviewSession)
        .where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user_id,
            InterviewSession.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def get_questions_with_responses(
    db: AsyncSession, session_id: uuid.UUID
) -> list[QuestionInstance]:
    """Load all non-deleted questions + their responses for a session, ordered by sequence."""
    result = await db.execute(
        select(QuestionInstance)
        .where(
            QuestionInstance.session_id == session_id,
            QuestionInstance.deleted_at.is_(None),
        )
        .options(selectinload(QuestionInstance.responses))
        .order_by(QuestionInstance.sequence_order.asc())
    )
    return list(result.scalars().all())


async def get_user_plan(db: AsyncSession, user_id: uuid.UUID):
    """Load user plan info for credit check."""
    from app.db.models.user import User
    result = await db.execute(
        select(User.plan_type, User.monthly_evaluation_credits)
        .where(User.id == user_id)
    )
    return result.one_or_none()


# ── Response updates ──────────────────────────────────────────────────────────


async def set_response_audio_processing(
    db: AsyncSession, response_id: uuid.UUID, status: str
) -> None:
    """Update audio_processing_status on a response (e.g. PENDING → PROCESSING)."""
    await db.execute(
        update(ResponseInstance)
        .where(ResponseInstance.id == response_id)
        .values(audio_processing_status=status)
        .execution_options(synchronize_session=False)
    )


async def update_response_scores(
    db: AsyncSession,
    response_id: uuid.UUID,
    *,
    transcribed_text: Optional[str],
    audio_duration_seconds: Optional[float],
    audio_processing_status: str,
    clarity_score: float,
    clarity_evidence: Optional[str],
    structure_score: float,
    structure_evidence: Optional[str],
    depth_score: float,
    depth_evidence: Optional[str],
    confidence_score: float,
    confidence_evidence: Optional[str],
    communication_score: float,
    communication_evidence: Optional[str],
    technical_score: Optional[float],
    technical_evidence: Optional[str],
    pressure_score: float,
    thinking_depth_score: float,
    overall_score: float,
    evaluation_explanation: str,
) -> None:
    """Persist all evaluation scores + audio fields for a single response.
    hesitation_score column intentionally excluded — see PerformanceSignal comment.
    """
    await db.execute(
        update(ResponseInstance)
        .where(ResponseInstance.id == response_id)
        .values(
            transcribed_text=transcribed_text,
            audio_duration_seconds=audio_duration_seconds,
            audio_processing_status=audio_processing_status,
            clarity_score=clarity_score,
            clarity_evidence=clarity_evidence,
            structure_score=structure_score,
            structure_evidence=structure_evidence,
            depth_score=depth_score,
            depth_evidence=depth_evidence,
            confidence_score=confidence_score,
            confidence_evidence=confidence_evidence,
            communication_score=communication_score,
            communication_evidence=communication_evidence,
            technical_score=technical_score,
            technical_evidence=technical_evidence,
            pressure_score=pressure_score,
            thinking_depth_score=thinking_depth_score,
            overall_score=overall_score,
            evaluation_explanation=evaluation_explanation,
        )
        .execution_options(synchronize_session=False)
    )


# ── EvaluationReport ──────────────────────────────────────────────────────────


async def create_evaluation_report(
    db: AsyncSession,
    *,
    session_id: uuid.UUID,
    overall_score: float,
    clarity_score: float,
    structure_score: float,
    depth_score: float,
    confidence_score: float,
    communication_score: float,
    technical_score: Optional[float],
    pressure_score: Optional[float],
    thinking_depth_score: Optional[float],
    first_answer_score: Optional[float],
    post_followup_score: Optional[float],
    feedback_summary: str,
    improvement_suggestions: dict,
    prompt_version: str,
    model_used: str,
    input_tokens: Optional[int],
    estimated_cost_usd: Optional[float],
    output_tokens: Optional[int],
) -> EvaluationReport:
    # hesitation_score column intentionally left NULL — see PerformanceSignal comment.
    report = EvaluationReport(
        session_id=session_id,
        overall_score=overall_score,
        clarity_score=clarity_score,
        structure_score=structure_score,
        depth_score=depth_score,
        confidence_score=confidence_score,
        communication_score=communication_score,
        technical_score=technical_score,
        pressure_score=pressure_score,
        thinking_depth_score=thinking_depth_score,
        first_answer_score=first_answer_score,
        post_followup_score=post_followup_score,
        feedback_summary=feedback_summary,
        improvement_suggestions=improvement_suggestions,
        prompt_version=prompt_version,
        model_used=model_used,
        input_tokens=input_tokens or None,
        output_tokens=output_tokens or None,
        estimated_cost_usd=estimated_cost_usd or None,
    )
    db.add(report)
    await db.flush()
    return report


async def get_report_with_session(
    db: AsyncSession, session_id: uuid.UUID
) -> Optional[EvaluationReport]:
    """Load report with nested session + questions (for response mapper)."""
    result = await db.execute(
        select(EvaluationReport)
        .where(EvaluationReport.session_id == session_id)
        .options(
            selectinload(EvaluationReport.session).selectinload(InterviewSession.questions)
        )
    )
    return result.scalar_one_or_none()


# ── Session status update ─────────────────────────────────────────────────────


async def set_session_analyzed(db: AsyncSession, session_id: uuid.UUID) -> None:
    """Transition session to ANALYZED status."""
    await db.execute(
        update(InterviewSession)
        .where(InterviewSession.id == session_id)
        .values(status="ANALYZED")
        .execution_options(synchronize_session=False)
    )


# ── EvaluationJob — worker operations ─────────────────────────────────────────


async def claim_next_pending_job(db: AsyncSession) -> Optional[EvaluationJob]:
    """
    Claim the next PENDING job ready to run.

    Uses SELECT ... FOR UPDATE SKIP LOCKED so concurrent workers never
    claim the same job (spec §2).
    Respects next_retry_at — jobs with a future timestamp are skipped.
    """
    now = datetime.now(timezone.utc)

    # Raw FOR UPDATE SKIP LOCKED via SQLAlchemy
    result = await db.execute(
        select(EvaluationJob)
        .where(
            EvaluationJob.status == EvaluationJobStatus.PENDING,
            or_(
                EvaluationJob.next_retry_at.is_(None),
                EvaluationJob.next_retry_at <= now,
            ),
        )
        .order_by(EvaluationJob.created_at.asc())
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    job = result.scalar_one_or_none()
    if job is None:
        return None

    job.status = EvaluationJobStatus.PROCESSING
    job.evaluation_started_at = now
    job.next_retry_at = None
    await db.flush()
    return job


async def mark_job_completed(db: AsyncSession, job_id: uuid.UUID) -> None:
    await db.execute(
        update(EvaluationJob)
        .where(EvaluationJob.id == job_id)
        .values(
            status=EvaluationJobStatus.COMPLETED,
            evaluation_completed_at=datetime.now(timezone.utc),
        )
        .execution_options(synchronize_session=False)
    )


async def mark_job_failed(db: AsyncSession, job_id: uuid.UUID, error: str) -> None:
    """
    Mark job failed or reset to PENDING with exponential backoff.
    Increments attempts; permanently FAILED after MAX_ATTEMPTS.
    """
    result = await db.execute(
        select(EvaluationJob).where(EvaluationJob.id == job_id)
    )
    job = result.scalar_one()

    new_attempts = job.attempts + 1
    is_final = new_attempts >= MAX_ATTEMPTS
    delay_seconds = RETRY_DELAYS_SECONDS.get(new_attempts, RETRY_DELAYS_SECONDS[MAX_ATTEMPTS])
    next_retry_at = (
        None
        if is_final
        else datetime.fromtimestamp(
            datetime.now(timezone.utc).timestamp() + delay_seconds,
            tz=timezone.utc,
        )
    )

    import logging as _logging
    _log = _logging.getLogger(__name__)
    _log.warning(
        "EvaluationJob %s failed (attempt %d/%d): %s%s",
        job_id,
        new_attempts,
        MAX_ATTEMPTS,
        error[:200],
        " — PERMANENTLY FAILED" if is_final else f" — retry in {delay_seconds}s",
    )

    job.status = EvaluationJobStatus.FAILED if is_final else EvaluationJobStatus.PENDING
    job.attempts = new_attempts
    job.last_error = error[:1000]
    job.evaluation_started_at = None
    job.next_retry_at = next_retry_at
    await db.flush()


async def recover_zombie_jobs(db: AsyncSession) -> int:
    """
    Reset PROCESSING jobs stuck longer than ZOMBIE_THRESHOLD_SECONDS to PENDING.
    Called periodically by the scheduler to prevent jobs stuck mid-execution.
    """
    stuck_before = datetime.fromtimestamp(
        datetime.now(timezone.utc).timestamp() - ZOMBIE_THRESHOLD_SECONDS,
        tz=timezone.utc,
    )
    retry_at = datetime.fromtimestamp(
        datetime.now(timezone.utc).timestamp() + RETRY_DELAYS_SECONDS[1],
        tz=timezone.utc,
    )

    result = await db.execute(
        update(EvaluationJob)
        .where(
            EvaluationJob.status == EvaluationJobStatus.PROCESSING,
            EvaluationJob.evaluation_started_at <= stuck_before,
        )
        .values(
            status=EvaluationJobStatus.PENDING,
            evaluation_started_at=None,
            last_error="Recovered from zombie state (worker crashed mid-execution)",
            next_retry_at=retry_at,
        )
        .execution_options(synchronize_session=False)
    )
    count = result.rowcount
    if count > 0:
        import logging as _logging
        _logging.getLogger(__name__).warning(
            "Zombie recovery: reset %d stuck PROCESSING job(s) to PENDING", count
        )
    return count


async def get_job_by_session_id(
    db: AsyncSession, session_id: uuid.UUID
) -> Optional[EvaluationJob]:
    result = await db.execute(
        select(EvaluationJob).where(EvaluationJob.session_id == session_id)
    )
    return result.scalar_one_or_none()
