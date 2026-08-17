"""
Evaluation service — business logic for session analysis.

Key responsibilities:
  1. analyze_session()          — user-facing; verifies ownership before delegating
  2. analyze_session_internal() — worker-facing; called by EvaluationWorker directly
  3. _run_analysis()            — core pipeline: transcribe → evaluate → persist → report
  4. get_evaluation()           — read existing report for a session

Score flow:
  LLM → 6 content dimensions (clarity, structure, depth, confidence, communication, technical)
  LLM → technical_accuracy_issues (list of factual contradictions against RAG context)
  Server → pressure_score (from response_time_ms)
  Server → thinking_depth_score (from thinking_time_ms)
  Server → overall_score (weighted formula, BEHAVIORAL vs TECHNICAL rubrics)

RAG grounding:
  For TECHNICAL sessions, InterviewKnowledgeRetriever retrieves up to 3 authoritative
  chunks from the KB for each question. These are injected into EvaluationInput as
  reference_facts and passed to the LLM provider, which is required to enumerate any
  factual contradictions in the candidate's answer before scoring technicalScore.

Aggregation: simple average across all questions in the session.

Credit check:
  PRO users with monthly_evaluation_credits > 0 → real AI provider.
  All others → stub provider (no cost incurred).

Matches NestJS: apps/backend/src/modules/evaluation/evaluation.service.ts
"""
import logging
import time
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import get_evaluation_provider, get_transcription_provider
from app.ai.protocols import EvaluationInput, PerformanceSignal
from app.ai.rag.retriever import InterviewKnowledgeRetriever
from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.modules.evaluation import repository as repo
from app.modules.evaluation.schemas import (
    DifficultyProgressionSchema,
    EvaluationDimensionsSchema,
    SessionEvaluationResponseSchema,
)
from app.usage import service as usage_svc

logger = logging.getLogger(__name__)

# Module-level retriever — stateless, safe to share across requests
_retriever = InterviewKnowledgeRetriever()

# ── Strength threshold ────────────────────────────────────────────────────────
STRENGTH_THRESHOLD = 70.0

DIMENSION_LABELS: dict[str, str] = {
    "clarity":        "Clear and coherent communication",
    "structure":      "Well-structured answers (STAR format)",
    "depth":          "Strong depth and detail in responses",
    "confidence":     "Confident and assertive delivery",
    "communication":  "Fluent communication with minimal fillers",
    "technical":      "Solid technical knowledge",
    "pressure":       "Calm and composed under time pressure",
    "thinking_depth": "Deliberate and thoughtful before answering",
}


# ── Public entry points ────────────────────────────────────────────────────────


async def analyze_session(
    db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID
) -> SessionEvaluationResponseSchema:
    """
    POST /sessions/:id/evaluation/analyze — user-facing manual trigger.
    Verifies session ownership before running analysis.
    """
    session = await repo.get_session_for_user(db, session_id, user_id)
    if not session:
        raise NotFoundException("Session not found or forbidden.")
    result = await _run_analysis(db, session_id)
    await db.commit()
    return result


async def analyze_session_internal(
    db: AsyncSession, session_id: uuid.UUID
) -> SessionEvaluationResponseSchema:
    """Worker-facing — called by EvaluationWorker; no ownership guard."""
    return await _run_analysis(db, session_id)


async def get_evaluation(
    db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID
) -> SessionEvaluationResponseSchema:
    """
    GET /sessions/:id/evaluation — read existing report.
    """
    session = await repo.get_session_for_user(db, session_id, user_id)
    if not session:
        raise NotFoundException("Session not found or forbidden.")

    report = await repo.get_report_with_session(db, session_id)
    if not report:
        raise NotFoundException("No evaluation found for this session.")

    return _to_response_schema(report)


# ── Core analysis pipeline ────────────────────────────────────────────────────

# Evaluate at most this many responses per session. Long interviews with many
# follow-ups can produce dozens of responses — beyond this the LLM context cost
# and latency balloon while marginal scoring value drops.
MAX_EVALUATION_RESPONSES = 10


async def _run_analysis(
    db: AsyncSession, session_id: uuid.UUID
) -> SessionEvaluationResponseSchema:
    # 1. Load session + check state
    session = await repo.get_session_for_evaluation(db, session_id)
    if not session:
        raise NotFoundException("Session not found.")
    if session.status != "COMPLETED":
        raise BadRequestException("Session must be COMPLETED before analysis.")
    if session.evaluation:
        raise ConflictException("Evaluation already exists for this session.")

    # 2. Load questions + responses
    questions = await repo.get_questions_with_responses(db, session_id)
    if not questions:
        raise BadRequestException("Cannot analyze a session without questions.")
    # Filter to answered questions only — the last question may have been auto-generated
    # after the user's final answer but before they clicked "End Session".
    questions = [q for q in questions if q.responses]
    if not questions:
        raise BadRequestException("Cannot analyze a session without any answered questions.")

    # 3. Credit check — never call LLM for users without credits
    user_row = await repo.get_user_plan(db, session.user_id)
    plan_type = user_row.plan_type if user_row else "FREE"
    credits = user_row.monthly_evaluation_credits if user_row else 0

    has_credits = plan_type == "PRO" and (credits or 0) > 0
    if not has_credits:
        logger.warning(
            "Session %s: no evaluation credits (plan=%s) — running stub evaluation",
            session_id,
            plan_type,
        )

    # Select provider based on credits
    ai_provider = get_evaluation_provider() if has_credits else _get_stub_evaluation()
    transcription_provider = get_transcription_provider() if has_credits else _get_stub_transcription()

    # Resolve topic name for RAG queries (safe: selectinload loaded it above)
    is_technical = (
        session.interview_type and session.interview_type.upper() == "TECHNICAL"
    )
    topic_name: Optional[str] = session.topic.name if session.topic else None

    # 4. Per-response transcription + evaluation
    signals: list[PerformanceSignal] = []
    total_input_tokens = 0
    total_output_tokens = 0
    total_cost_usd = 0.0

    eval_start = time.monotonic()

    # Cap responses evaluated to limit LLM cost/latency on long sessions.
    # Take only the last MAX_EVALUATION_RESPONSES.
    total_responses = sum(len(q.responses) for q in questions)
    skip_count = max(0, total_responses - MAX_EVALUATION_RESPONSES)
    if skip_count:
        logger.warning(
            "Session %s has %d responses — evaluating only the last %d",
            session_id, total_responses, MAX_EVALUATION_RESPONSES,
        )

    response_idx = 0
    for q in questions:
        for response in q.responses:
            response_idx += 1
            if response_idx <= skip_count:
                continue  # skip early responses, keep only the last N

            # ── 4a: Audio transcription ──────────────────────────────────────────
            transcribed_text: Optional[str] = None
            audio_duration_seconds: Optional[float] = None
            audio_processing_status: str = response.audio_processing_status

            if response.audio_url:
                logger.debug(
                    "Transcribing audio for response %s | url: %s",
                    response.id,
                    response.audio_url,
                )
                # Mark PROCESSING before API call
                await repo.set_response_audio_processing(db, response.id, "PROCESSING")
                await db.flush()

                transcription = await transcription_provider.transcribe(response.audio_url)
                transcribed_text = transcription.text or None
                audio_duration_seconds = transcription.duration_seconds
                audio_processing_status = "COMPLETED"

                if transcription.estimated_cost_usd is not None:
                    total_cost_usd += transcription.estimated_cost_usd

                logger.info(
                    "Audio transcribed for response %s | model=%s | words=%d | duration=%ss",
                    response.id,
                    transcription.model_used,
                    len((transcription.text or "").split()),
                    f"{audio_duration_seconds:.1f}" if audio_duration_seconds else "?",
                )

            # ── 4b: Merge text sources ───────────────────────────────────────────
            # Transcribed text takes precedence (richer signal)
            effective_text = (
                transcribed_text.strip()
                if transcribed_text and transcribed_text.strip()
                else (response.answer_text or "")
            )

            # ── 4c: RAG grounding context ────────────────────────────────────────
            # Only retrieved for TECHNICAL sessions; behavioral sessions don't need
            # factual cross-checking against the KB.
            reference_facts: Optional[str] = None
            if is_technical and has_credits:
                # Skip retrieval for stub mode — not worth the DB round-trip for
                # heuristic scoring that has no factual checking logic.
                reference_facts = await _retriever.retrieve_context(
                    db,
                    query_text=q.content,
                    topic=topic_name,
                    difficulty=q.difficulty,
                    top_k=3,
                )
                if reference_facts:
                    logger.debug(
                        "RAG: retrieved grounding context for question %s (%d chars)",
                        q.id,
                        len(reference_facts),
                    )

            eval_input = EvaluationInput(
                question_text=q.content,
                answer_text=effective_text,
                topic_name=topic_name or "",
                interview_type=(
                    session.interview_type.lower()
                    if session.interview_type
                    else "behavioral"
                ),
                difficulty=q.difficulty,
                response_time_ms=response.response_time_ms,
                thinking_time_ms=response.thinking_time_ms,
                reference_facts=reference_facts,
            )

            # ── 4d: LLM evaluation ───────────────────────────────────────────────
            signal = await ai_provider.evaluate(eval_input)
            signal.is_followup = response.is_followup
            signals.append(signal)

            # Accumulate cost
            if signal.cost_meta:
                total_input_tokens += signal.cost_meta.input_tokens
                total_output_tokens += signal.cost_meta.output_tokens
                total_cost_usd += signal.cost_meta.estimated_cost_usd

            # ── 4e: Build evaluation_explanation ────────────────────────────────
            # Stores factual accuracy issues (from RAG) and low-score evidence
            # (from conditional second call). Used for per-question audit trail.
            explanation_parts: list[str] = []
            if signal.evaluation_explanation:
                explanation_parts.append(signal.evaluation_explanation)
            if signal.technical_accuracy_issues:
                issues_str = "; ".join(signal.technical_accuracy_issues)
                explanation_parts.append(f"FACTUAL ISSUES: {issues_str}")
            if signal.technical_accuracy_evidence:
                explanation_parts.append(f"RAG: {signal.technical_accuracy_evidence}")
            evaluation_explanation = " | ".join(explanation_parts)

            # ── 4f: Persist scores for this response ─────────────────────────────
            await repo.update_response_scores(
                db,
                response.id,
                transcribed_text=transcribed_text,
                audio_duration_seconds=audio_duration_seconds,
                audio_processing_status=audio_processing_status,
                clarity_score=signal.clarity_score,
                clarity_evidence=signal.clarity_evidence,
                structure_score=signal.structure_score,
                structure_evidence=signal.structure_evidence,
                depth_score=signal.depth_score,
                depth_evidence=signal.depth_evidence,
                confidence_score=signal.confidence_score,
                confidence_evidence=signal.confidence_evidence,
                communication_score=signal.communication_score,
                communication_evidence=signal.communication_evidence,
                technical_score=signal.technical_score,
                technical_evidence=signal.technical_evidence,
                pressure_score=signal.pressure_score or 50.0,
                thinking_depth_score=signal.thinking_depth_score or 50.0,
                overall_score=signal.overall_score or 0.0,
                evaluation_explanation=evaluation_explanation,
            )

    eval_duration_ms = int((time.monotonic() - eval_start) * 1000)

    # 5. Aggregate signals → session-level averages
    aggregated = _aggregate_signals(signals)

    # Extract prompt version + model from last signal's cost_meta
    last_meta = next(
        (s.cost_meta for s in reversed(signals) if s.cost_meta), None
    )
    prompt_version = last_meta.prompt_version if last_meta else "stub"
    model_used = last_meta.model_used if last_meta else "stub"

    # 6. Atomic: create EvaluationReport + set session ANALYZED
    # Note: no db.commit() here — the caller (run_evaluation_tick) commits
    # alongside mark_job_completed. This ensures the job's PROCESSING status
    # is rolled back together with the report if anything fails after this
    # point (see evaluation_worker.py). A separate commit here would
    # prematurely persist the PROCESSING status before mark_job_completed,
    # creating a zombie PROCESSING job that zombie recovery can't reliably
    # recover.
    report = await repo.create_evaluation_report(
        db,
        session_id=session_id,
        overall_score=aggregated["overall_score"],
        clarity_score=aggregated["clarity_score"],
        structure_score=aggregated["structure_score"],
        depth_score=aggregated["depth_score"],
        confidence_score=aggregated["confidence_score"],
        communication_score=aggregated["communication_score"],
        technical_score=aggregated["technical_score"],
        pressure_score=aggregated["pressure_score"],
        thinking_depth_score=aggregated["thinking_depth_score"],
        first_answer_score=aggregated["first_answer_score"],
        post_followup_score=aggregated["post_followup_score"],
        feedback_summary=aggregated["feedback_summary"],
        improvement_suggestions=aggregated["improvement_suggestions"],
        prompt_version=prompt_version,
        model_used=model_used,
        input_tokens=total_input_tokens or None,
        output_tokens=total_output_tokens or None,
        estimated_cost_usd=total_cost_usd or None,
    )

    if has_credits:
        await usage_svc.consume_evaluation_credit(db, session.user_id)

    await repo.set_session_analyzed(db, session_id)

    logger.info(
        "Session %s ANALYZED in %dms | Provider: %s | Overall: %.1f | Cost: $%.6f",
        session_id,
        eval_duration_ms,
        prompt_version,
        aggregated["overall_score"],
        total_cost_usd,
    )

    # 7. Reload report with nested session + questions for mapper
    full_report = await repo.get_report_with_session(db, session_id)
    return _to_response_schema(full_report)


# ── Aggregation ───────────────────────────────────────────────────────────────


def _aggregate_signals(signals: list[PerformanceSignal]) -> dict:
    """Average all numeric PerformanceSignal fields across the session's responses."""
    n = len(signals)

    def avg(attr: str) -> float:
        return sum(getattr(s, attr) or 0.0 for s in signals) / n

    technical_scores = [s.technical_score for s in signals if s.technical_score is not None]
    technical_avg = (
        sum(technical_scores) / len(technical_scores) if technical_scores else None
    )

    agg = {
        "overall_score":        avg("overall_score"),
        "clarity_score":        avg("clarity_score"),
        "structure_score":      avg("structure_score"),
        "depth_score":          avg("depth_score"),
        "confidence_score":     avg("confidence_score"),
        "communication_score":  avg("communication_score"),
        "technical_score":      technical_avg,
        "pressure_score":       avg("pressure_score"),
        "thinking_depth_score": avg("thinking_depth_score"),
    }

    first_answers = [s.overall_score for s in signals if not s.is_followup and s.overall_score is not None]
    followups = [s.overall_score for s in signals if s.is_followup and s.overall_score is not None]

    agg["first_answer_score"] = sum(first_answers) / len(first_answers) if first_answers else None
    agg["post_followup_score"] = sum(followups) / len(followups) if followups else None

    agg["feedback_summary"] = _build_feedback_summary(agg)
    agg["improvement_suggestions"] = _build_improvement_suggestions(agg)
    return agg


def _build_feedback_summary(scores: dict) -> str:
    overall = scores["overall_score"]
    label = f"{overall:.1f}"
    if overall >= 75:
        return (
            f"Strong performance with an overall score of {label}/100. "
            "Clarity and structure were highlights."
        )
    if overall >= 50:
        return (
            f"Solid foundation with an overall score of {label}/100. "
            "Key areas for growth: structure and confidence."
        )
    return (
        f"Developing performance with an overall score of {label}/100. "
        "Focus on answer depth and reducing hesitation."
    )


def _build_improvement_suggestions(scores: dict) -> dict[str, list[str]]:
    suggestions: dict[str, list[str]] = {}

    if scores["structure_score"] < 60:
        suggestions["structure"] = [
            "Use the STAR format (Situation, Task, Action, Result)",
            "Outline your answer mentally before speaking",
        ]
    if scores["confidence_score"] < 60:
        suggestions["confidence"] = [
            'Eliminate hedging phrases like "I think" and "maybe"',
            "State your position assertively, then support it with evidence",
        ]
    if scores["depth_score"] < 60:
        suggestions["depth"] = [
            "Provide specific, quantified examples for every claim",
            'Explain the "why" behind your decisions, not just the "what"',
        ]
    if scores["communication_score"] < 60:
        suggestions["communication"] = [
            "Practice concise delivery — aim for 60–120 seconds per answer",
            "Record yourself answering and review for filler words",
        ]
    if (scores.get("pressure_score") or 50) < 50:
        suggestions["pace"] = [
            "You answered too quickly — take a breath before responding",
            'It is fine to say "let me think about that for a moment"',
        ]
    if (scores.get("thinking_depth_score") or 50) < 50:
        suggestions["composure"] = [
            "Practice pausing 4–8 seconds before answering to organize your thoughts",
            "Deliberate pauses signal confidence, not uncertainty",
        ]

    return suggestions


# ── Response mapper ───────────────────────────────────────────────────────────


def _to_response_schema(report) -> SessionEvaluationResponseSchema:
    """Map EvaluationReport ORM object → clean response schema."""
    questions = report.session.questions if report.session else []
    sorted_qs = sorted(
        [q for q in questions if q.deleted_at is None],
        key=lambda q: q.sequence_order,
    )

    difficulty_progression = DifficultyProgressionSchema(
        started_at=report.session.difficulty,
        ended_at=sorted_qs[-1].difficulty if sorted_qs else report.session.difficulty,
    )

    dimensions = EvaluationDimensionsSchema(
        clarity=report.clarity_score,
        structure=report.structure_score,
        depth=report.depth_score,
        confidence=report.confidence_score,
        communication=report.communication_score,
        technical=report.technical_score,
        pressure=report.pressure_score or 50.0,
        thinking_depth=report.thinking_depth_score or 50.0,
    )

    strengths = _derive_strengths(dimensions)

    raw_suggestions: dict = report.improvement_suggestions or {}
    improvements = [item for sublist in raw_suggestions.values() for item in sublist]

    return SessionEvaluationResponseSchema(
        session_id=report.session_id,
        overall_score=report.overall_score,
        first_answer_score=report.first_answer_score,
        post_followup_score=report.post_followup_score,
        summary=report.feedback_summary,
        dimensions=dimensions,
        strengths=strengths,
        improvements=improvements,
        difficulty_progression=difficulty_progression,
        evaluated_at=report.created_at.isoformat(),
    )


def _derive_strengths(dimensions: EvaluationDimensionsSchema) -> list[str]:
    """Return labels for dimensions that scored ≥ STRENGTH_THRESHOLD."""
    scores: dict[str, Optional[float]] = {
        "clarity":        dimensions.clarity,
        "structure":      dimensions.structure,
        "depth":          dimensions.depth,
        "confidence":     dimensions.confidence,
        "communication":  dimensions.communication,
        "technical":      dimensions.technical,
        "pressure":       dimensions.pressure,
        "thinking_depth": dimensions.thinking_depth,
    }
    return [
        DIMENSION_LABELS[key]
        for key, score in scores.items()
        if score is not None and score >= STRENGTH_THRESHOLD
    ]


# ── Lazy stub accessors (avoids circular imports) ─────────────────────────────


def _get_stub_evaluation():
    from app.ai.providers.stub_evaluation import StubEvaluationProvider
    return StubEvaluationProvider()


def _get_stub_transcription():
    from app.ai.providers.stub_transcription import StubTranscriptionProvider
    return StubTranscriptionProvider()
