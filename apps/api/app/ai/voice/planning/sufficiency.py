"""
Cheap sufficiency scoring for a candidate's last answer — "did they already
demonstrate enough depth/detail unprompted?" Used by turn_decision.py to
short-circuit forced follow-ups when the candidate has already nailed it.

Deliberately a single small/fast LLM call (low max_tokens, terse prompt) —
this runs on every turn, so it must stay cheap relative to the main
interviewer response generation.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from app.ai.voice.llm.response_generator import ResponseGenerator

logger = logging.getLogger("sufficiency_scorer")


@dataclass
class AnswerSufficiency:
    score: int  # 1-5, 5 = fully sufficient, no follow-up needed
    rationale: str


class SufficiencyScorer:
    def __init__(self, response_generator: ResponseGenerator | None = None):
        self.response_generator = response_generator or ResponseGenerator()

    async def score(self, *, topic_label: str, question_text: str, answer_text: str) -> AnswerSufficiency:
        try:
            raw = await self.response_generator.generate([
                {
                    "role": "system",
                    "content": (
                        "Score how completely the candidate's answer already covers "
                        f"the topic '{topic_label}', on a 1-5 scale (5 = fully sufficient, "
                        "no follow-up needed; 1 = superficial, needs probing). "
                        "Reply with ONLY JSON: {\"score\": <int 1-5>, \"rationale\": \"<one short sentence>\"}.\n\n"
                        f"Question: {question_text}\nAnswer: {answer_text}"
                    ),
                }
            ])
            return self._parse(raw)
        except Exception as exc:
            logger.warning("sufficiency_scoring_failed | falling back to heuristic | error: %s", exc)
            return self._heuristic_fallback(answer_text)

    @staticmethod
    def _parse(raw: str) -> AnswerSufficiency:
        match = re.search(r"\{.*\}", raw or "", re.DOTALL)
        if not match:
            raise ValueError("no JSON object in response")
        data = json.loads(match.group(0))
        score = int(data["score"])
        score = max(1, min(5, score))
        return AnswerSufficiency(score=score, rationale=str(data.get("rationale", "")))

    @staticmethod
    def _heuristic_fallback(answer_text: str) -> AnswerSufficiency:
        # ponytail: word-count proxy, only used when the LLM call itself fails
        # (network/API outage) — never the primary signal.
        word_count = len((answer_text or "").split())
        score = 4 if word_count >= 60 else (3 if word_count >= 25 else 2)
        return AnswerSufficiency(score=score, rationale="heuristic fallback (word count)")
