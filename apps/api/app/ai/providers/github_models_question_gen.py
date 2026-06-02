"""
GitHub Models question generation provider.

Uses Azure AI Foundry's GitHub Models endpoint (models.inference.ai.azure.com)
with a GitHub Personal Access Token — free tier, no credit card required.

The endpoint is OpenAI-SDK-compatible, so we reuse the same interface as the
OpenAI provider with a different base_url and auth header.

Microsoft AI stack compliance: powered by Azure AI Foundry.
"""
import json
import logging

from app.ai.prompts.question_gen import (
    QUESTION_GEN_SYSTEM_PROMPT,
    build_question_gen_user_prompt,
)
from app.ai.protocols import GeneratedQuestion, QuestionGenerationInput
from app.ai.providers.stub_question_gen import StubQuestionGenerationProvider

logger = logging.getLogger(__name__)

_VALID_DIFFICULTIES = {"EASY", "MEDIUM", "HARD"}


class GitHubModelsQuestionGenerationProvider:
    """
    Generates interview questions via GitHub Models (Azure AI Foundry).

    Requires GITHUB_TOKEN to be set in settings.
    Falls back to StubQuestionGenerationProvider on parse or API errors.
    """

    def __init__(self, token: str, model: str, base_url: str) -> None:
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(
            api_key=token,
            base_url=base_url,
        )
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
            parsed = self._parse_and_validate(raw, input.difficulty)

            if not parsed:
                logger.warning(
                    "Malformed GitHub Models question gen response — falling back to stub. Raw: %.200s",
                    raw,
                )
                return await self._fallback.generate(input)

            logger.info(
                'GitHub Models: generated question for topic "%s" | difficulty: %s | model: %s',
                input.topic_name,
                parsed.estimated_difficulty,
                self._model,
            )
            return parsed

        except Exception as exc:
            logger.error("GitHub Models question gen failed: %s — falling back to stub", exc)
            return await self._fallback.generate(input)

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
