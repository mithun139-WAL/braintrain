"""
Evaluation prompt definitions — versioned for analytics consistency.
PROMPT_VERSION stored in EvaluationReport so score comparisons are traceable.

Design principle:
  LLM scores ONLY content-based dimensions (6 fields).
  pressure_score + thinking_depth_score are computed SERVER-SIDE from timing data.
  overall_score is computed SERVER-SIDE with weighted formula.
  This keeps scoring defensible, cheap, and auditable.

Matches NestJS: apps/backend/src/modules/ai/prompts/evaluation.prompts.ts
"""

PROMPT_VERSION = "v1.0.0"
MODEL_USED = "gpt-4o-mini"

# ── System prompt — strict JSON only, 6 content dimensions ────────────────────
# Calibration anchors keep scores consistent across sessions.

EVALUATION_SYSTEM_PROMPT = """You are an expert technical and behavioral interview evaluator.

You must evaluate candidate responses objectively and return a strict JSON object.

Scoring Rules:
- All scores must be integers from 0 to 100.
- Do not return explanations outside the JSON.
- Do not include markdown, prose, or any text outside the JSON object.
- Be consistent and conservative in scoring.
- 50 represents average interview performance.
- 70 represents strong hire-level performance.
- 85+ represents exceptional clarity and depth.

Evaluate based only on the answer text provided.

Return ONLY this JSON object and nothing else:
{
  "clarityScore": <integer 0-100>,
  "structureScore": <integer 0-100>,
  "depthScore": <integer 0-100>,
  "confidenceScore": <integer 0-100>,
  "communicationScore": <integer 0-100>,
  "technicalScore": <integer 0-100 or null>
}""".strip()


def build_evaluation_user_prompt(
    *,
    question: str,
    answer: str,
    interview_type: str,
    difficulty: str,
) -> str:
    """
    User message for a specific answer evaluation.
    Keeps to the 6 LLM-scorable content dimensions.
    Does NOT include timing data — timing is evaluated server-side.
    """
    answer_text = answer.strip() if answer.strip() else "[No answer provided — candidate did not respond]"
    return "\n".join([
        "Interview Context:",
        f"Interview Type: {interview_type}",
        f"Difficulty: {difficulty}",
        "",
        "Question:",
        question,
        "",
        "Candidate Answer:",
        answer_text,
        "",
        "Return JSON in this format:",
        "{",
        '  "clarityScore": number,',
        '  "structureScore": number,',
        '  "depthScore": number,',
        '  "confidenceScore": number,',
        '  "communicationScore": number,',
        '  "technicalScore": number or null',
        "}",
    ])
