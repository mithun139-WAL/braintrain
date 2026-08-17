"""
OpenAI question generation provider.

Uses gpt-4o with JSON mode to generate interview questions.
Auto-saves generated questions to QuestionBank (dataset flywheel).
Falls back to StubQuestionGenerationProvider on parse or API errors.
"""
import json
import logging
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


class OpenAIQuestionGenerationProvider:
    """
    Generates interview questions using GPT-4o with JSON mode.
    Requires OPENAI_API_KEY to be set.
    """

    def __init__(self, api_key: str) -> None:
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=api_key)
        self._fallback = StubQuestionGenerationProvider()

    async def generate(self, input: QuestionGenerationInput) -> GeneratedQuestion:
        user_prompt = build_question_gen_user_prompt(
            topic_name=input.topic_name,
            difficulty=input.difficulty,
            interview_type=input.interview_type,
            existing_questions=input.existing_questions,
            reference_facts=input.reference_facts,
        )

        try:
            completion = await self._client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                temperature=0.7,
                messages=[
                    {"role": "system", "content": QUESTION_GEN_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )

            raw = completion.choices[0].message.content or ""
            parsed = self._parse_and_validate(raw, input.difficulty)

            if not parsed:
                logger.warning(
                    "Malformed question gen response — falling back to stub. Raw: %.200s", raw
                )
                return await self._fallback.generate(input)

            logger.info(
                'Generated question for topic "%s" | difficulty: %s',
                input.topic_name,
                parsed.estimated_difficulty,
            )
            parsed.reference_facts = input.reference_facts
            return parsed

        except Exception as exc:
            logger.error("OpenAI question gen failed: %s — falling back to stub", exc)
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
                reference_facts=question.reference_facts,
                topic_id=input.topic_id,
                difficulty=question.estimated_difficulty,
                interview_type=input.interview_type,
                source="GENERATED",
                is_global=False,
                created_by_user_id=None,  # system-generated
            )
            db.add(item)
            await db.flush()
            logger.debug("Auto-saved generated question to QuestionBank")
        except Exception as exc:
            logger.warning("Failed to auto-save question to bank: %s", exc)

    def _parse_and_validate(self, raw: str, fallback_difficulty: str) -> GeneratedQuestion | None:
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
