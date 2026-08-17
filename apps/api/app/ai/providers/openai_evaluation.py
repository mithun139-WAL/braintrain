"""
OpenAIEvaluationProvider — GPT-4o-mini based answer evaluation.

Design:
  - LLM scores 6 content dimensions + enumerates factual contradictions (JSON mode, temp=0.1)
  - RAG reference_facts injected when available; LLM must enumerate contradictions or
    explicitly confirm "no contradictions found" — not a soft instruction to deduct points.
  - Conditional second call: if any dimension scores < EVIDENCE_SCORE_THRESHOLD (70),
    a single follow-up call fetches per-dimension evidence quotes. Pays extra cost only
    on the subset of responses that need explaining (not every evaluation).
  - pressure_score + thinking_depth_score computed SERVER-SIDE from timing
  - overall_score computed SERVER-SIDE with weighted formula (BEHAVIORAL vs TECHNICAL)
  - Difficulty boost +4 for HARD applied to content scores (not timing)
  - One retry on malformed JSON; falls back to stub on second failure
  - Cost tracked per-call; attached as cost_meta on PerformanceSignal

Matches NestJS: apps/backend/src/modules/ai/providers/openai-evaluation.provider.ts
"""
import asyncio
import json
import logging
import math
from typing import Optional

from app.ai.prompts.evaluation import (
    EVALUATION_SYSTEM_PROMPT,
    EVIDENCE_SCORE_THRESHOLD,
    EVIDENCE_SYSTEM_PROMPT,
    MODEL_USED,
    PROMPT_VERSION,
    build_evaluation_user_prompt,
    build_evidence_user_prompt,
    find_low_score_dimensions,
)
from app.ai.protocols import EvaluationCostMeta, EvaluationInput, PerformanceSignal

logger = logging.getLogger(__name__)

# ── Pricing (gpt-4o-mini, as of 2024) ─────────────────────────────────────────
COST_PER_INPUT_TOKEN = 0.00000015   # $0.15 / 1M input tokens
COST_PER_OUTPUT_TOKEN = 0.0000006   # $0.60 / 1M output tokens

# Primary scoring call — increased from 150 to accommodate RAG accuracy fields
# (technicalAccuracyIssues list + technicalAccuracyEvidence string ≈ +100 tokens)
MAX_OUTPUT_TOKENS = 400

# Conditional evidence call — batches all low-scoring dimensions into one request
MAX_EVIDENCE_OUTPUT_TOKENS = 300

# Difficulty boost applied to content scores before clamping (spec §7)
DIFFICULTY_BOOST: dict[str, int] = {
    "EASY": 0,
    "MEDIUM": 0,
    "HARD": 4,   # +4 for HARD — fairness adjustment
}

# Fields the LLM is responsible for scoring (5 required + 1 optional)
LLM_REQUIRED_SCORE_FIELDS = [
    "clarityScore",
    "structureScore",
    "depthScore",
    "confidenceScore",
    "communicationScore",
]

# Evidence fields — required alongside their score partners
LLM_REQUIRED_EVIDENCE_FIELDS = [
    "clarityEvidence",
    "structureEvidence",
    "depthEvidence",
    "confidenceEvidence",
    "communicationEvidence",
]


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, round(value)))


class OpenAIEvaluationProvider:
    """
    GPT-4o-mini evaluation provider with server-side score computation.
    Implements the AnswerEvaluationProvider protocol.
    """

    def __init__(self, api_key: str) -> None:
        import openai
        self._client = openai.OpenAI(api_key=api_key)
        # Lazy import to avoid circular dependency before ai_enabled check
        from app.ai.providers.stub_evaluation import StubEvaluationProvider
        self._fallback = StubEvaluationProvider()

    async def evaluate(self, input: EvaluationInput) -> PerformanceSignal:
        user_prompt = build_evaluation_user_prompt(
            question=input.question_text,
            answer=input.answer_text,
            interview_type=input.interview_type,
            difficulty=input.difficulty,
            reference_facts=input.reference_facts,
        )

        result = await self._call_with_retry(user_prompt, input.difficulty)

        if result is None:
            # Malformed JSON after retry — degrade to stub
            logger.warning("LLM returned malformed JSON after retry — degraded mode (stub)")
            signal = await self._fallback.evaluate(input)
            signal.cost_meta = EvaluationCostMeta(
                input_tokens=0,
                output_tokens=0,
                estimated_cost_usd=0.0,
                model_used="stub-degraded",
                prompt_version=PROMPT_VERSION,
                degraded=True,
            )
            return signal

        scores, meta = result

        # ── Server-side timing signals ─────────────────────────────────────────
        pressure_score = self._compute_pressure_score(input.response_time_ms)
        thinking_depth_score = self._compute_thinking_depth_score(input.thinking_time_ms)

        # ── Server-side weighted overall score ────────────────────────────────
        overall_score = self._compute_overall_score(
            clarity_score=scores["clarityScore"],
            structure_score=scores["structureScore"],
            depth_score=scores["depthScore"],
            confidence_score=scores["confidenceScore"],
            communication_score=scores["communicationScore"],
            technical_score=scores.get("technicalScore"),
            pressure_score=pressure_score,
            thinking_depth_score=thinking_depth_score,
            interview_type=input.interview_type,
        )

        # ── Conditional evidence call for low-scoring dimensions ──────────────
        low_score_dims = find_low_score_dimensions(scores)
        evidence_map: dict[str, str] = {}
        if low_score_dims:
            evidence_map = await self._fetch_evidence(
                question=input.question_text,
                answer=input.answer_text,
                low_score_dimensions=low_score_dims,
            )
            # Accumulate tokens from evidence call into existing meta
            # (evidence call tokens are tracked via its own usage; we add to meta below)

        # Merge evidence into score fields (overrides placeholder strings when available)
        def _evidence(key: str, fallback: str) -> str:
            return evidence_map.get(key) or scores.get(f"{key}Evidence") or fallback

        # Build evaluation_explanation from evidence map + accuracy issues
        explanation_parts: list[str] = []
        if evidence_map:
            explanation_parts.append(
                " | ".join(f"{k}: {v}" for k, v in evidence_map.items())
            )

        logger.debug(
            "Evaluated | Overall: %.1f | Tokens: %din/%dout | Cost: $%.6f | Model: %s | Prompt: %s",
            overall_score,
            meta.input_tokens,
            meta.output_tokens,
            meta.estimated_cost_usd,
            meta.model_used,
            meta.prompt_version,
        )

        return PerformanceSignal(
            clarity_score=scores["clarityScore"],
            clarity_evidence=_evidence("clarity", scores.get("clarityEvidence", "")),
            structure_score=scores["structureScore"],
            structure_evidence=_evidence("structure", scores.get("structureEvidence", "")),
            depth_score=scores["depthScore"],
            depth_evidence=_evidence("depth", scores.get("depthEvidence", "")),
            confidence_score=scores["confidenceScore"],
            confidence_evidence=_evidence("confidence", scores.get("confidenceEvidence", "")),
            communication_score=scores["communicationScore"],
            communication_evidence=_evidence("communication", scores.get("communicationEvidence", "")),
            technical_score=scores.get("technicalScore"),
            technical_evidence=scores.get("technicalEvidence"),
            evaluation_explanation=" | ".join(explanation_parts),
            technical_accuracy_issues=scores.get("technicalAccuracyIssues") or [],
            technical_accuracy_evidence=scores.get("technicalAccuracyEvidence"),
            pressure_score=pressure_score,
            thinking_depth_score=thinking_depth_score,
            overall_score=overall_score,
            cost_meta=meta,
        )

    # ── LLM call with one retry ────────────────────────────────────────────────

    async def _call_with_retry(
        self, user_prompt: str, difficulty: str
    ) -> Optional[tuple[dict, EvaluationCostMeta]]:
        for attempt in range(1, 3):
            try:
                completion = await asyncio.to_thread(
                    self._client.chat.completions.create,
                    model=MODEL_USED,
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    max_tokens=MAX_OUTPUT_TOKENS,
                    messages=[
                        {"role": "system", "content": EVALUATION_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                raw = completion.choices[0].message.content or ""
                input_tokens = completion.usage.prompt_tokens if completion.usage else 0
                output_tokens = completion.usage.completion_tokens if completion.usage else 0
                estimated_cost = (
                    input_tokens * COST_PER_INPUT_TOKEN
                    + output_tokens * COST_PER_OUTPUT_TOKEN
                )

                scores = self._parse_and_validate(raw, difficulty)
                if scores is not None:
                    meta = EvaluationCostMeta(
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        estimated_cost_usd=round(estimated_cost, 8),
                        model_used=MODEL_USED,
                        prompt_version=PROMPT_VERSION,
                        degraded=False,
                    )
                    return scores, meta

                logger.warning(
                    "Attempt %d: malformed JSON from LLM. Raw: %.200s", attempt, raw
                )
            except Exception as exc:
                logger.error("Attempt %d: OpenAI API call failed — %s", attempt, exc)

        return None

    # ── Conditional evidence call ──────────────────────────────────────────────

    async def _fetch_evidence(
        self,
        *,
        question: str,
        answer: str,
        low_score_dimensions: dict[str, float],
    ) -> dict[str, str]:
        """
        Single follow-up call for dimensions that scored below EVIDENCE_SCORE_THRESHOLD.
        Returns a dict mapping dimension name → direct quote from the answer.
        Non-fatal: returns empty dict on any failure.
        """
        prompt = build_evidence_user_prompt(
            question=question,
            answer=answer,
            low_score_dimensions=low_score_dimensions,
        )
        try:
            completion = await asyncio.to_thread(
                self._client.chat.completions.create,
                model=MODEL_USED,
                response_format={"type": "json_object"},
                temperature=0.0,
                max_tokens=MAX_EVIDENCE_OUTPUT_TOKENS,
                messages=[
                    {"role": "system", "content": EVIDENCE_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )
            raw = completion.choices[0].message.content or ""
            parsed = json.loads(raw)
            # Only accept string values to guard against unexpected shapes
            return {k: v for k, v in parsed.items() if isinstance(v, str)}
        except Exception as exc:
            logger.warning("Evidence call failed (non-fatal, skipping): %s", exc)
            return {}

    # ── Parse + validate LLM response ─────────────────────────────────────────

    def _parse_and_validate(self, raw: str, difficulty: str) -> Optional[dict]:
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return None

        # Validate 5 required numeric content fields
        for f in LLM_REQUIRED_SCORE_FIELDS:
            value = parsed.get(f)
            if not isinstance(value, (int, float)) or math.isnan(value):
                logger.warning("Validation failed: %s = %s", f, value)
                return None

        # technicalScore may be null for behavioral
        tech = parsed.get("technicalScore")
        if tech is not None and not isinstance(tech, (int, float)):
            logger.warning("Invalid technicalScore: %s", tech)
            return None

        # technicalAccuracyIssues must be a list (empty list is valid and expected)
        accuracy_issues = parsed.get("technicalAccuracyIssues")
        if accuracy_issues is not None and not isinstance(accuracy_issues, list):
            logger.warning("Invalid technicalAccuracyIssues type: %s", type(accuracy_issues))
            accuracy_issues = []

        boost = DIFFICULTY_BOOST.get(difficulty.upper(), 0)

        return {
            "clarityScore":              _clamp(parsed["clarityScore"] + boost),
            "clarityEvidence":           parsed.get("clarityEvidence", ""),
            "structureScore":            _clamp(parsed["structureScore"] + boost),
            "structureEvidence":         parsed.get("structureEvidence", ""),
            "depthScore":                _clamp(parsed["depthScore"] + boost),
            "depthEvidence":             parsed.get("depthEvidence", ""),
            "confidenceScore":           _clamp(parsed["confidenceScore"]),
            "confidenceEvidence":        parsed.get("confidenceEvidence", ""),
            "communicationScore":        _clamp(parsed["communicationScore"]),
            "communicationEvidence":     parsed.get("communicationEvidence", ""),
            "technicalScore":            _clamp(tech + boost) if tech is not None else None,
            "technicalEvidence":         parsed.get("technicalEvidence"),
            "technicalAccuracyIssues":   [i for i in (accuracy_issues or []) if isinstance(i, str)],
            "technicalAccuracyEvidence": parsed.get("technicalAccuracyEvidence"),
        }

    # ── Server-side timing scores (spec §2) ───────────────────────────────────

    def _compute_pressure_score(self, response_time_ms: int) -> float:
        """
        Optimal response time sweet spot: 15–45s.
        Too fast (< 10s) = likely panicked/rushing.
        Too slow (> 90s) = likely rambling.
        """
        if not response_time_ms:
            return 50.0
        seconds = response_time_ms / 1000.0
        if seconds < 5:
            return 20.0
        if seconds < 10:
            return 40.0
        if seconds <= 45:
            return _clamp(80.0 + round((45 - seconds) / 35 * 15))
        if seconds <= 90:
            return _clamp(80.0 - round((seconds - 45) / 45 * 30))
        return 30.0

    def _compute_thinking_depth_score(self, thinking_time_ms: int) -> float:
        """
        Optimal pause: 4–12s (deliberate composition).
        < 2s = reactive, no thought. > 20s = stuck/frozen.
        """
        if not thinking_time_ms:
            return 50.0
        seconds = thinking_time_ms / 1000.0
        if seconds < 1:
            return 20.0
        if seconds < 3:
            return 50.0
        if seconds <= 12:
            return _clamp(65.0 + round((seconds - 3) / 9 * 30))
        if seconds <= 20:
            return _clamp(95.0 - round((seconds - 12) / 8 * 30))
        return 35.0

    # ── Server-side weighted overall score (spec §4) ─────────────────────────

    def _compute_overall_score(
        self,
        *,
        clarity_score: float,
        structure_score: float,
        depth_score: float,
        confidence_score: float,
        communication_score: float,
        technical_score: Optional[float],
        pressure_score: float,
        thinking_depth_score: float,
        interview_type: str,
    ) -> float:
        timing_score = (pressure_score + thinking_depth_score) / 2.0

        if interview_type.upper() == "TECHNICAL" and technical_score is not None:
            content_avg = (clarity_score + structure_score + depth_score) / 3.0
            score = (
                content_avg * 0.45
                + technical_score * 0.30
                + communication_score * 0.10
                + confidence_score * 0.05
                + timing_score * 0.10
            )
        else:
            content_avg = (clarity_score + structure_score + depth_score) / 3.0
            score = (
                content_avg * 0.45
                + confidence_score * 0.20
                + communication_score * 0.15
                + timing_score * 0.10
                + (technical_score if technical_score is not None else 50.0) * 0.10
            )

        return _clamp(score)
