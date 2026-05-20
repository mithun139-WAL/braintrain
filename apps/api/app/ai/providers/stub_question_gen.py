"""
Stub question generation provider — zero-cost local dev fallback.

Returns a deterministic question derived from the topic name and difficulty.
Used when OPENAI_API_KEY is not configured.
"""
from app.ai.protocols import GeneratedQuestion, QuestionGenerationInput


class StubQuestionGenerationProvider:
    async def generate(self, input: QuestionGenerationInput) -> GeneratedQuestion:
        question_text = (
            f"Explain the core concepts of {input.topic_name} at the "
            f"{input.difficulty.lower()} level, including real-world applications."
        )
        return GeneratedQuestion(
            question_text=question_text,
            expected_answer_traits=[
                "Clear explanation of core concept",
                "Practical examples or use cases",
                "Awareness of trade-offs or limitations",
            ],
            estimated_difficulty=input.difficulty,
        )
