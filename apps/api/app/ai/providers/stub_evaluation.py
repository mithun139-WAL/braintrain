"""
StubEvaluationProvider — deterministic, zero-cost evaluation.

Used when:
  - OPENAI_API_KEY is not set (offline / dev mode)
  - User has no evaluation credits (degraded mode)

All scoring is based on simple heuristics so the pipeline produces
plausible, varied output without any external API call.

Matches NestJS: apps/backend/src/modules/ai/providers/stub-evaluation.provider.ts
"""
import re

from app.ai.protocols import AnswerEvaluationProvider, EvaluationInput, PerformanceSignal


class StubEvaluationProvider:
    """
    Deterministic heuristic evaluator — no LLM calls, no cost.
    Implements the AnswerEvaluationProvider protocol.
    """

    async def evaluate(self, input: EvaluationInput) -> PerformanceSignal:
        text = input.answer_text or ""
        words = [w for w in text.strip().split() if w]
        word_count = len(words)

        clarity_score = self._score_clarity(text, word_count)
        structure_score = self._score_structure(text)
        depth_score = self._score_depth(word_count)
        confidence_score = self._score_confidence(text)
        communication_score = self._score_communication(text, word_count)
        hesitation_score = self._score_hesitation(text)
        technical_score = (
            self._score_technical(text)
            if input.interview_type.upper() == "TECHNICAL"
            else None
        )

        pressure_score = self._score_pressure(input.response_time_ms)
        thinking_depth_score = self._score_thinking_depth(input.thinking_time_ms)

        overall_score = self._compute_overall(
            clarity_score=clarity_score,
            structure_score=structure_score,
            depth_score=depth_score,
            confidence_score=confidence_score,
            communication_score=communication_score,
            hesitation_score=hesitation_score,
            technical_score=technical_score,
            pressure_score=pressure_score,
            thinking_depth_score=thinking_depth_score,
            interview_type=input.interview_type,
        )

        explanation = (
            f"[Stub] Evaluated {word_count} words. "
            f"Overall: {overall_score:.1f}/100. "
            f"Pressure: {pressure_score:.0f}, Thinking Depth: {thinking_depth_score:.0f}."
        )

        return PerformanceSignal(
            clarity_score=clarity_score,
            structure_score=structure_score,
            depth_score=depth_score,
            confidence_score=confidence_score,
            communication_score=communication_score,
            hesitation_score=hesitation_score,
            technical_score=technical_score,
            pressure_score=pressure_score,
            thinking_depth_score=thinking_depth_score,
            overall_score=overall_score,
            evaluation_explanation=explanation,
            cost_meta=None,
        )

    # ── Heuristic scorers ──────────────────────────────────────────────────────

    def _score_clarity(self, text: str, word_count: int) -> float:
        """Penalise very short or extremely long responses."""
        if word_count < 10:
            return 30.0
        if word_count < 30:
            return 55.0
        if word_count < 200:
            return 75.0
        return 65.0  # penalise rambling

    def _score_structure(self, text: str) -> float:
        """Looks for STAR-like transition markers."""
        markers = ["situation", "task", "action", "result", "because", "therefore", "finally"]
        lc = text.lower()
        found = sum(1 for m in markers if m in lc)
        return min(30.0 + found * 10.0, 100.0)

    def _score_depth(self, word_count: int) -> float:
        """Based on word count — more content = more depth (up to a ceiling)."""
        if word_count < 20:
            return 25.0
        if word_count < 80:
            return 55.0
        if word_count < 200:
            return 80.0
        return 90.0

    def _score_confidence(self, text: str) -> float:
        """Penalises hedging phrases."""
        hedges = ["i think", "i guess", "maybe", "i'm not sure", "kind of", "sort of"]
        lc = text.lower()
        count = sum(1 for h in hedges if h in lc)
        return max(80.0 - count * 10.0, 30.0)

    def _score_communication(self, text: str, word_count: int) -> float:
        """Penalises filler words."""
        fillers = ["um", "uh", "like", "you know", "basically", "literally"]
        lc = text.lower()
        filler_count = 0
        for f in fillers:
            filler_count += len(re.findall(r"\b" + re.escape(f) + r"\b", lc))
        density = filler_count / word_count if word_count > 0 else 0.0
        return max(90.0 - density * 200.0, 20.0)

    def _score_hesitation(self, text: str) -> float:
        """Filler words + ellipsis patterns. Lower is better."""
        fillers = ["um", "uh", "er", "hmm"]
        lc = text.lower()
        filler_count = 0
        for f in fillers:
            filler_count += len(re.findall(r"\b" + re.escape(f) + r"\b", lc))
        ellipsis_count = text.count("...")
        return min((filler_count + ellipsis_count) * 15.0, 100.0)

    def _score_technical(self, text: str) -> float:
        """Presence of domain-specific vocabulary (naive proxy)."""
        tech_terms = [
            "algorithm", "complexity", "database", "query", "api",
            "async", "cache", "index", "scaling",
        ]
        lc = text.lower()
        found = sum(1 for t in tech_terms if t in lc)
        return min(40.0 + found * 8.0, 100.0)

    def _score_pressure(self, response_time_ms: int) -> float:
        """
        Derived from total response time.
        Optimal range: 15–45 seconds. Very fast = rushed/stressed. Very slow = stuck.
        """
        if not response_time_ms:
            return 50.0
        seconds = response_time_ms / 1000.0
        if seconds < 5:
            return 20.0
        if seconds < 10:
            return 40.0
        if seconds < 15:
            return 60.0
        if seconds <= 45:
            return 85.0
        if seconds <= 90:
            return 65.0
        return 40.0

    def _score_thinking_depth(self, thinking_time_ms: int) -> float:
        """
        Derived from pre-answer thinking pause.
        A short deliberate pause (4–12s) = composed, thoughtful.
        """
        if not thinking_time_ms:
            return 50.0
        seconds = thinking_time_ms / 1000.0
        if seconds < 1:
            return 30.0
        if seconds < 3:
            return 50.0
        if seconds < 6:
            return 70.0
        if seconds <= 12:
            return 90.0
        if seconds <= 20:
            return 65.0
        return 35.0

    # ── Weighted aggregation ───────────────────────────────────────────────────

    def _compute_overall(
        self,
        *,
        clarity_score: float,
        structure_score: float,
        depth_score: float,
        confidence_score: float,
        communication_score: float,
        hesitation_score: float,
        technical_score: float | None,
        pressure_score: float,
        thinking_depth_score: float,
        interview_type: str,
    ) -> float:
        hesitation_penalty = hesitation_score * 0.08
        behavioral_bonus = (pressure_score * 0.05) + (thinking_depth_score * 0.05)

        if interview_type.upper() == "TECHNICAL" and technical_score is not None:
            score = (
                0.18 * clarity_score
                + 0.13 * structure_score
                + 0.18 * depth_score
                + 0.13 * confidence_score
                + 0.08 * communication_score
                + 0.18 * technical_score
                - hesitation_penalty
                + behavioral_bonus
            )
        else:
            # Behavioral weighting — confidence and structure matter more
            score = (
                0.18 * clarity_score
                + 0.18 * structure_score
                + 0.18 * depth_score
                + 0.18 * confidence_score
                + 0.08 * communication_score
                + 0.08 * (100.0 - hesitation_score)
                + behavioral_bonus
            )

        return max(round(score, 1), 0.0)
