"""
NIM question generation provider.

Uses NVIDIA NIM's OpenAI-compatible endpoint with JSON mode to generate
interview questions. Falls back to StubQuestionGenerationProvider on
parse or API errors.

Auto-saves generated questions to QuestionBank (dataset flywheel) via
generate_and_save(), matching the same contract as the OpenAI provider.
"""
import json
import logging
import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts.question_gen import (
    QUESTION_GEN_SYSTEM_PROMPT,
    build_question_gen_user_prompt,
)
from app.ai.protocols import GeneratedQuestion, QuestionGenerationInput
from app.ai.providers.stub_question_gen import StubQuestionGenerationProvider

logger = logging.getLogger(__name__)

_VALID_DIFFICULTIES = {"EASY", "MEDIUM", "HARD"}
_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def _extract_json(raw: str) -> str:
    """Strip markdown fences; fall back to first '{' ... last '}'."""
    match = _JSON_FENCE_RE.search(raw)
    if match:
        return match.group(1).strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw[start : end + 1]
    return raw


class NIMQuestionGenerationProvider:
    """
    Generates interview questions using NVIDIA NIM (OpenAI-compatible API).
    Requires NVIDIA_API_KEY to be set.
    """

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._fallback = StubQuestionGenerationProvider()

    async def generate(self, input: QuestionGenerationInput) -> GeneratedQuestion:
        user_prompt = build_question_gen_user_prompt(
            topic_name=input.topic_name,
            difficulty=input.difficulty,
            interview_type=input.interview_type,
            existing_questions=input.existing_questions,
        )

        try:
            completion = await self._client.chat.completions.create(
                model=self._model,
                response_format={"type": "json_object"},
                temperature=0.7,
                messages=[
                    {"role": "system", "content": QUESTION_GEN_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )

            raw = completion.choices[0].message.content or ""
            cleaned = _extract_json(raw)
            parsed = self._parse_and_validate(cleaned, input.difficulty)

            if not parsed:
                logger.warning(
                    "NIM malformed question gen response — falling back to stub. Raw: %.200s",
                    raw,
                )
                return await self._fallback.generate(input)

            logger.info(
                'NIM generated question for topic "%s" | difficulty: %s',
                input.topic_name,
                parsed.estimated_difficulty,
            )
            return parsed

        except Exception as exc:
            logger.error("NIM question gen failed: %s — falling back to stub", exc)
            return await self._fallback.generate(input)

    async def generate_and_save(
        self,
        input: QuestionGenerationInput,
        db: AsyncSession,
    ) -> GeneratedQuestion:
        """
        Generate a question AND auto-save it to QuestionBank (dataset flywheel).
        Used by the questions service during LLM generation path.
        """
        result = await self.generate(input)
        await self._save_to_bank(result, input, db)
        return result

    async def _save_to_bank(
        self,
        question: GeneratedQuestion,
        input: QuestionGenerationInput,
        db: AsyncSession,
    ) -> None:
        """Non-fatal: bank save failure does not block question delivery."""
        try:
            from app.db.models.question_bank import QuestionBank

            item = QuestionBank(
                content=question.question_text,
                topic_id=input.topic_id,
                difficulty=question.estimated_difficulty,
                interview_type=input.interview_type,
                source="GENERATED",
                is_global=False,
                created_by_user_id=None,
            )
            db.add(item)
            await db.flush()
            logger.debug("NIM: Auto-saved generated question to QuestionBank")
        except Exception as exc:
            logger.warning("NIM: Failed to auto-save question to bank: %s", exc)

    def _parse_and_validate(
        self, raw: str, fallback_difficulty: str
    ) -> GeneratedQuestion | None:
        try:
            data = json.loads(raw)

            question_text = data.get("questionText", "").strip()
            if not question_text:
                return None

            traits = [
                t for t in data.get("expectedAnswerTraits", []) if isinstance(t, str)
            ] or ["Structured answer", "Concrete examples", "Clear reasoning"]

            difficulty = data.get("estimatedDifficulty", "")
            if difficulty not in _VALID_DIFFICULTIES:
                difficulty = fallback_difficulty

            return GeneratedQuestion(
                question_text=question_text,
                expected_answer_traits=traits,
                estimated_difficulty=difficulty,
            )
        except (json.JSONDecodeError, AttributeError):
            return None
