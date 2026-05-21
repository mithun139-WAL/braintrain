"""
OpenAIFollowupProvider — GPT-4o-mini based real-time follow-up analysis.

Design:
  - Called immediately after the user submits an answer during a live session.
  - LLM decides if the answer has gaps and returns one targeted probe question.
  - Stateless: the full conversation history is sent on each call.
  - One retry on malformed JSON; falls back to stub (allow next question) on failure.
  - Max 2 follow-up rounds enforced in the service layer, not here.
"""
import asyncio
import json
import logging
from typing import Optional

from app.ai.prompts.followup import (
    FOLLOWUP_MODEL_USED,
    FOLLOWUP_SYSTEM_PROMPT,
    build_followup_user_prompt,
)
from app.ai.protocols import FollowupExchange, FollowupInput, FollowupSignal

logger = logging.getLogger(__name__)

MAX_OUTPUT_TOKENS = 200


class OpenAIFollowupProvider:
    """
    GPT-4o-mini follow-up analysis provider.
    Implements the FollowupProvider protocol.
    """

    def __init__(self, api_key: str) -> None:
        import openai
        self._client = openai.OpenAI(api_key=api_key)
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
            logger.warning("Followup LLM returned malformed JSON after retry — degraded to stub")
            return await self._fallback.analyze(input)

        return result

    async def _call_with_retry(self, user_prompt: str) -> Optional[FollowupSignal]:
        for attempt in range(1, 3):
            try:
                completion = await asyncio.to_thread(
                    self._client.chat.completions.create,
                    model=FOLLOWUP_MODEL_USED,
                    response_format={"type": "json_object"},
                    temperature=0.4,
                    max_tokens=MAX_OUTPUT_TOKENS,
                    messages=[
                        {"role": "system", "content": FOLLOWUP_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                raw = completion.choices[0].message.content or ""
                signal = self._parse(raw)
                if signal is not None:
                    logger.debug(
                        "Followup analysis | needs_followup=%s | gap=%s",
                        signal.needs_followup,
                        signal.gap_identified,
                    )
                    return signal

                logger.warning("Attempt %d: malformed followup JSON. Raw: %.200s", attempt, raw)
            except Exception as exc:
                logger.error("Attempt %d: followup OpenAI call failed — %s", attempt, exc)

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

        # If needs_followup is True, a question must be present
        if needs_followup and not followup_question:
            return None

        return FollowupSignal(
            needs_followup=needs_followup,
            followup_question=followup_question if needs_followup else None,
            acknowledgement=acknowledgement.strip(),
            gap_identified=gap_identified if needs_followup else None,
        )
