"""
Question generation prompt strings — versioned for dataset consistency.

Generated questions are saved back to QuestionBank automatically by the
OpenAI provider to build a proprietary question dataset over time.
"""

CURRENT_QUESTION_GEN_PROMPT_VERSION = "qgen-v1"

QUESTION_GEN_SYSTEM_PROMPT = """You are an expert technical interviewer and question designer.
Your job is to generate ONE high-quality interview question and return ONLY a valid JSON object.
No explanations outside the JSON. No markdown. No code blocks. Pure JSON only.

Question design rules:
- Questions must be specific, not generic
- BEHAVIORAL questions should follow STAR-method format triggers
- TECHNICAL questions should test deep practical understanding, not just definitions
- Difficulty calibration: EASY = foundational, MEDIUM = applied, HARD = system-level or edge-cases
- Never repeat cliché questions like "Tell me about yourself"

Return exactly this JSON schema and nothing else:
{
  "questionText": "<the full interview question>",
  "expectedAnswerTraits": ["<trait1>", "<trait2>", "<trait3>"],
  "estimatedDifficulty": "<EASY|MEDIUM|HARD>"
}""".strip()


def build_question_gen_user_prompt(
    *,
    topic_name: str,
    difficulty: str,
    interview_type: str,
    existing_questions: list[str] | None = None,
    reference_facts: str | None = None,
) -> str:
    lines = [
        f"Generate ONE {interview_type} interview question about: {topic_name}",
        f"Required difficulty level: {difficulty}",
    ]

    if reference_facts:
        lines.append("")
        lines.append("Base the question strictly on the following authoritative knowledge:")
        lines.append("---")
        lines.append(reference_facts.strip())
        lines.append("---")

    if existing_questions:
        lines.append("")
        lines.append("Do NOT generate any of these already-asked questions:")
        for i, q in enumerate(existing_questions, 1):
            lines.append(f"{i}. {q}")

    lines.append("")
    lines.append("Return only the JSON object described in your instructions.")
    return "\n".join(lines)
