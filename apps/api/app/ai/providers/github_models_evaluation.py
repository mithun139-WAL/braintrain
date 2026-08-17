"""
GitHub Models evaluation provider.

Uses Azure AI Foundry's GitHub Models endpoint (models.inference.ai.azure.com)
with a GitHub Personal Access Token via the OpenAI AsyncClient.

Design:
  - LLM scores 6 content dimensions + enumerates factual contradictions (JSON mode, temp=0.1)
  - RAG reference_facts injected when available; LLM must enumerate contradictions or
    explicitly confirm "no contradictions found".
  - Conditional second call: dimensions scoring < EVIDENCE_SCORE_THRESHOLD trigger a
    single batched follow-up for per-dimension evidence quotes.
  - pressure_score + thinking_depth_score computed SERVER-SIDE from timing
  - overall_score computed SERVER-SIDE with weighted formula (BEHAVIORAL vs TECHNICAL)
  - Difficulty boost +4 for HARD applied to content scores (not timing)
  - One retry on malformed JSON; JSON extracted from markdown fences if needed
  - Falls back to stub on second failure
  - MAX_OUTPUT_TOKENS set higher than openai/nim to accommodate Azure model verbosity

Microsoft AI stack compliance: powered by Azure AI Foundry.
"""
import json
import logging
import math
import re
from typing import Optional

from app.ai.prompts.evaluation import (
    EVALUATION_SYSTEM_PROMPT,
    EVIDENCE_SCORE_THRESHOLD,
    EVIDENCE_SYSTEM_PROMPT,
    PROMPT_VERSION,
    build_evaluation_user_prompt,
    build_evidence_user_prompt,
    find_low_score_dimensions,
)
from app.ai.protocols import EvaluationCostMeta, EvaluationInput, PerformanceSignal

logger = logging.getLogger(__name__)

MAX_OUTPUT_TOKENS = 600   # Higher cap — Azure models tend toward verbosity
MAX_EVIDENCE_OUTPUT_TOKENS = 400

DIFFICULTY_BOOST: dict[str, int] = {"EASY": 0, "MEDIUM": 0, "HARD": 4}

LLM_REQUIRED_SCORE_FIELDS = [
    "clarityScore",
    "structureScore",
    "depthScore",
    "confidenceScore",
    "communicationScore",
]

LLM_REQUIRED_EVIDENCE_FIELDS = [
    "clarityEvidence",
    "structureEvidence",
    "depthEvidence",
    "confidenceEvidence",
    "communicationEvidence",
]

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, round(value)))


def _extract_json(raw: str) -> str:
    match = _JSON_FENCE_RE.search(raw)
    if match:
        return match.group(1).strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw[start : end + 1]
    return raw


class GitHubModelsEvaluationProvider:
    """
    GitHub Models (Azure AI Foundry) evaluation provider.
    Implements the AnswerEvaluationProvider protocol.
    """

    def __init__(self, token: str, model: str, base_url: str) -> None:
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=token, base_url=base_url)
        self._model = model
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
            logger.warning("GitHub Models returned malformed JSON after retry — degraded mode (stub)")
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

        pressure_score = self._compute_pressure_score(input.response_time_ms)
        thinking_depth_score = self._compute_thinking_depth_score(input.thinking_time_ms)
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

        def _evidence(key: str, fallback: str) -> str:
            return evidence_map.get(key) or scores.get(f"{key}Evidence") or fallback

        explanation_parts: list[str] = []
        if evidence_map:
            explanation_parts.append(
                " | ".join(f"{k}: {v}" for k, v in evidence_map.items())
            )

        logger.debug(
            "GitHub Models Evaluated | Overall: %.1f | Tokens: %din/%dout | Model: %s",
            overall_score,
            meta.input_tokens,
            meta.output_tokens,
            meta.model_used,
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

    async def _call_with_retry(
        self, user_prompt: str, difficulty: str
    ) -> Optional[tuple[dict, EvaluationCostMeta]]:
        for attempt in range(1, 3):
            try:
                completion = await self._client.chat.completions.create(
                    model=self._model,
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

                cleaned = _extract_json(raw)
                scores = self._parse_and_validate(cleaned, difficulty)
                if scores is not None:
                    meta = EvaluationCostMeta(
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        estimated_cost_usd=0.0,  # GitHub Models free tier
                        model_used=self._model,
                        prompt_version=PROMPT_VERSION,
                        degraded=False,
                    )
                    return scores, meta

                logger.warning("Attempt %d: malformed JSON from GitHub Models. Raw: %.200s", attempt, raw)
            except Exception as exc:
                logger.error("Attempt %d: GitHub Models API call failed — %s", attempt, exc)

        return None

    async def _fetch_evidence(
        self,
        *,
        question: str,
        answer: str,
        low_score_dimensions: dict[str, float],
    ) -> dict[str, str]:
        prompt = build_evidence_user_prompt(
            question=question,
            answer=answer,
            low_score_dimensions=low_score_dimensions,
        )
        try:
            completion = await self._client.chat.completions.create(
                model=self._model,
                response_format={"type": "json_object"},
                temperature=0.0,
                max_tokens=MAX_EVIDENCE_OUTPUT_TOKENS,
                messages=[
                    {"role": "system", "content": EVIDENCE_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )
            raw = completion.choices[0].message.content or ""
            cleaned = _extract_json(raw)
            parsed = json.loads(cleaned)
            return {k: v for k, v in parsed.items() if isinstance(v, str)}
        except Exception as exc:
            logger.warning("GitHub Models evidence call failed (non-fatal, skipping): %s", exc)
            return {}

    def _parse_and_validate(self, raw: str, difficulty: str) -> Optional[dict]:
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return None

        for f in LLM_REQUIRED_SCORE_FIELDS:
            value = parsed.get(f)
            if not isinstance(value, (int, float)) or math.isnan(value):
                logger.warning("GitHub Models validation failed: %s = %s", f, value)
                return None

        for f in LLM_REQUIRED_EVIDENCE_FIELDS:
            value = parsed.get(f)
            if not isinstance(value, str):
                logger.warning("GitHub Models validation failed (evidence): %s = %s", f, value)
                return None

        tech = parsed.get("technicalScore")
        if tech is not None and not isinstance(tech, (int, float)):
            return None

        accuracy_issues = parsed.get("technicalAccuracyIssues")
        if accuracy_issues is not None and not isinstance(accuracy_issues, list):
            accuracy_issues = []

        boost = DIFFICULTY_BOOST.get(difficulty.upper(), 0)
        return {
            "clarityScore":              _clamp(parsed["clarityScore"] + boost),
            "clarityEvidence":           parsed["clarityEvidence"],
            "structureScore":            _clamp(parsed["structureScore"] + boost),
            "structureEvidence":         parsed["structureEvidence"],
            "depthScore":                _clamp(parsed["depthScore"] + boost),
            "depthEvidence":             parsed["depthEvidence"],
            "confidenceScore":           _clamp(parsed["confidenceScore"]),
            "confidenceEvidence":        parsed["confidenceEvidence"],
            "communicationScore":        _clamp(parsed["communicationScore"]),
            "communicationEvidence":     parsed["communicationEvidence"],
            "technicalScore":            _clamp(tech + boost) if tech is not None else None,
            "technicalEvidence":         parsed.get("technicalEvidence") if tech is not None else None,
            "technicalAccuracyIssues":   [i for i in (accuracy_issues or []) if isinstance(i, str)],
            "technicalAccuracyEvidence": parsed.get("technicalAccuracyEvidence"),
        }

    def _compute_pressure_score(self, response_time_ms: int) -> float:
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
