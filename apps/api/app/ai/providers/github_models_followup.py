"""
GitHub Models follow-up analysis provider.

Mirrors OpenAIFollowupProvider — real-time probing after each answer.
Uses the Azure AI Foundry GitHub Models endpoint (AsyncOpenAI-compatible).

Microsoft AI stack compliance: powered by Azure AI Foundry.
"""
import json
import logging
import re
from typing import Optional

from app.ai.prompts.followup import (
    FOLLOWUP_MODEL_USED,
    FOLLOWUP_SYSTEM_PROMPT,
    build_followup_user_prompt,
)
from app.ai.protocols import FollowupInput, FollowupSignal

logger = logging.getLogger(__name__)

MAX_OUTPUT_TOKENS = 200

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def _extract_json(raw: str) -> str:
    match = _JSON_FENCE_RE.search(raw)
    if match:
        return match.group(1).strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw[start : end + 1]
    return raw


class GitHubModelsFollowupProvider:
    """
    GitHub Models (Azure AI Foundry) follow-up analysis provider.
    Implements the FollowupProvider protocol.
    """

    def __init__(self, token: str, model: str, base_url: str) -> None:
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=token, base_url=base_url)
        self._model = model or FOLLOWUP_MODEL_USED
        from app.ai.providers.stub_followup import StubFollowupProvider
        self._fallback = StubFollowupProvider()

    async def analyze(self, input: FollowupInput) -> FollowupSignal:
        user_prompt = build_followup_user_prompt(
            question=input.question_text,
            answer=input.answer_text,
            interview_type=input.interview_type,
            difficulty=input.difficulty,
            prior_exchanges=[
                {"followup_question": ex.followup_question, "followup_answer": ex.followup_answer}
                for ex in input.prior_exchanges
            ],
        )

        result = await self._call_with_retry(user_prompt)

        if result is None:
            logger.warning("GitHub Models followup returned malformed JSON — degraded to stub")
            return await self._fallback.analyze(input)

        return result

    async def _call_with_retry(self, user_prompt: str) -> Optional[FollowupSignal]:
        for attempt in range(1, 3):
            try:
                completion = await self._client.chat.completions.create(
                    model=self._model,
                    response_format={"type": "json_object"},
                    temperature=0.4,
                    max_tokens=MAX_OUTPUT_TOKENS,
                    messages=[
                        {"role": "system", "content": FOLLOWUP_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                raw = completion.choices[0].message.content or ""
                cleaned = _extract_json(raw)
                signal = self._parse(cleaned)
                if signal is not None:
                    logger.debug(
                        "GitHub Models followup | needs_followup=%s | gap=%s",
                        signal.needs_followup,
                        signal.gap_identified,
                    )
                    return signal

                logger.warning("Attempt %d: malformed followup JSON. Raw: %.200s", attempt, raw)
            except Exception as exc:
                logger.error("Attempt %d: GitHub Models followup call failed — %s", attempt, exc)

        return None

    def _parse(self, raw: str) -> Optional[FollowupSignal]:
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return None

        needs_followup = parsed.get("needs_followup")
        if not isinstance(needs_followup, bool):
            return None

        acknowledgement = parsed.get("acknowledgement", "")
        if not isinstance(acknowledgement, str):
            return None

        followup_question = parsed.get("followup_question")
        gap_identified = parsed.get("gap_identified")

        if needs_followup and not followup_question:
            return None

        return FollowupSignal(
            needs_followup=needs_followup,
            followup_question=followup_question if needs_followup else None,
            acknowledgement=acknowledgement.strip(),
            gap_identified=gap_identified if needs_followup else None,
        )
