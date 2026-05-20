"""
OpenAIEvaluationProvider — GPT-4o-mini based answer evaluation.

Design:
  - LLM scores 6 content dimensions (JSON mode, temp=0.1)
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
    MODEL_USED,
    PROMPT_VERSION,
    build_evaluation_user_prompt,
)
from app.ai.protocols import EvaluationCostMeta, EvaluationInput, PerformanceSignal

logger = logging.getLogger(__name__)

# ── Pricing (gpt-4o-mini, as of 2024) ─────────────────────────────────────────
COST_PER_INPUT_TOKEN = 0.00000015   # $0.15 / 1M input tokens
COST_PER_OUTPUT_TOKEN = 0.0000006   # $0.60 / 1M output tokens

# Hard cap — we only need a tiny JSON blob back
MAX_OUTPUT_TOKENS = 150

# Difficulty boost applied to content scores before clamping (spec §7)
DIFFICULTY_BOOST: dict[str, int] = {
    "EASY": 0,
    "MEDIUM": 0,
    "HARD": 4,   # +4 for HARD — fairness adjustment
}

# Fields the LLM is responsible for scoring (5 required + 1 optional)
LLM_REQUIRED_FIELDS = [
    "clarityScore",
    "structureScore",
    "depthScore",
    "confidenceScore",
    "communicationScore",
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
            structure_score=scores["structureScore"],
            depth_score=scores["depthScore"],
            confidence_score=scores["confidenceScore"],
            communication_score=scores["communicationScore"],
            hesitation_score=0.0,   # deprecated — replaced by pressure + thinking
            technical_score=scores.get("technicalScore"),
            pressure_score=pressure_score,
            thinking_depth_score=thinking_depth_score,
            overall_score=overall_score,
            evaluation_explanation="",   # not requested — keeps tokens low
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

    # ── Parse + validate 6-field LLM response ────────────────────────────────

    def _parse_and_validate(self, raw: str, difficulty: str) -> Optional[dict]:
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return None

        # Validate 5 required numeric content fields
        for field in LLM_REQUIRED_FIELDS:
            value = parsed.get(field)
            if not isinstance(value, (int, float)) or math.isnan(value):
                logger.warning("Validation failed: %s = %s", field, value)
                return None

        # technicalScore may be null for behavioral
        tech = parsed.get("technicalScore")
        if tech is not None and not isinstance(tech, (int, float)):
            logger.warning("Invalid technicalScore: %s", tech)
            return None

        boost = DIFFICULTY_BOOST.get(difficulty.upper(), 0)

        return {
            "clarityScore":      _clamp(parsed["clarityScore"] + boost),
            "structureScore":    _clamp(parsed["structureScore"] + boost),
            "depthScore":        _clamp(parsed["depthScore"] + boost),
            "confidenceScore":   _clamp(parsed["confidenceScore"]),
            "communicationScore": _clamp(parsed["communicationScore"]),
            "technicalScore":    _clamp(tech + boost) if tech is not None else None,
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
