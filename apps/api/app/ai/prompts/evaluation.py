"""
Evaluation prompt definitions — versioned for analytics consistency.
PROMPT_VERSION stored in EvaluationReport so score comparisons are traceable.

Design principle:
  LLM scores ONLY content-based dimensions (6 fields).
  pressure_score + thinking_depth_score are computed SERVER-SIDE from timing data.
  overall_score is computed SERVER-SIDE with weighted formula.
  This keeps scoring defensible, cheap, and auditable.

v1.1.0 changes (RAG grounding):
  - System prompt now requires technicalAccuracyIssues (list) and
    technicalAccuracyEvidence (string) when Reference Facts are provided.
  - Providers enforce the contradiction enumeration path, not just a soft
    instruction to "deduct points if wrong."
  - build_evaluation_user_prompt() accepts optional reference_facts.
  - build_evidence_user_prompt() added for the conditional second call
    that provides per-dimension evidence quotes for scores below threshold.

Matches NestJS: apps/backend/src/modules/ai/prompts/evaluation.prompts.ts
"""
from typing import Optional

PROMPT_VERSION = "v1.1.0"
MODEL_USED = "gpt-4o-mini"

# Dimensions below this threshold trigger the conditional evidence call.
EVIDENCE_SCORE_THRESHOLD = 70

# ── System prompt — strict JSON, 6 content dimensions + RAG accuracy ──────────
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
- Evaluate based only on the answer text and reference facts provided.

FACTUAL ACCURACY (mandatory when Reference Facts are present):
- Read the Reference Facts section before scoring technicalScore.
- In "technicalAccuracyIssues", list EVERY specific claim in the candidate's
  answer that directly contradicts the reference facts. Quote the candidate's
  exact claim in each entry (e.g. "Claimed IVFFlat has better recall than HNSW
  at high memory budgets — reference states the opposite for high-recall regimes").
- If no contradictions are found, return an empty list [] — do NOT omit the field.
- In "technicalAccuracyEvidence", write either:
    "Reference facts confirm answer" (no contradictions found), or
    "Reference facts contradict: <brief summary of what is wrong>"
  Never omit this field when Reference Facts are present.
- Deduct technicalScore proportionally to contradiction severity.
  A single clear factual inversion should cost at least 20 points.
- When no Reference Facts are provided, set technicalAccuracyIssues to []
  and technicalAccuracyEvidence to null.

Return ONLY this JSON object and nothing else:
{
  "clarityScore": <integer 0-100>,
  "clarityEvidence": "<1-sentence justification quoting or referencing the answer>",
  "structureScore": <integer 0-100>,
  "structureEvidence": "<1-sentence justification>",
  "depthScore": <integer 0-100>,
  "depthEvidence": "<1-sentence justification>",
  "confidenceScore": <integer 0-100>,
  "confidenceEvidence": "<1-sentence justification>",
  "communicationScore": <integer 0-100>,
  "communicationEvidence": "<1-sentence justification>",
  "technicalScore": <integer 0-100 or null>,
  "technicalEvidence": "<1-sentence justification or null>",
  "technicalAccuracyIssues": ["<specific contradicted claim>", ...],
  "technicalAccuracyEvidence": "<confirmation or contradiction summary, or null>"
}""".strip()


# ── Evidence system prompt — used only in the conditional second call ──────────

EVIDENCE_SYSTEM_PROMPT = """You are a precise interview evaluation analyst.
Return only valid JSON. No prose, no markdown outside the JSON object.
For each dimension provided, quote the specific sentence or phrase from the
candidate's answer that best explains the low score. Quote directly — do not
paraphrase.""".strip()


def build_evaluation_user_prompt(
    *,
    question: str,
    answer: str,
    interview_type: str,
    difficulty: str,
    reference_facts: Optional[str] = None,
) -> str:
    """
    User message for a specific answer evaluation.
    Keeps to the 6 LLM-scorable content dimensions + RAG accuracy fields.
    Injects reference_facts when available so the model can enumerate
    factual contradictions token-by-token rather than eyeballing them.
    Does NOT include timing data — timing is evaluated server-side.
    """
    answer_text = answer.strip() if answer.strip() else "[No answer provided — candidate did not respond]"
    parts = [
        "Interview Context:",
        f"Interview Type: {interview_type}",
        f"Difficulty: {difficulty}",
        "",
        "Question:",
        question,
        "",
        "Candidate Answer:",
        answer_text,
    ]

    if reference_facts and reference_facts.strip():
        parts += [
            "",
            "Reference Facts (authoritative knowledge base — use to verify technical claims):",
            reference_facts.strip(),
        ]

    parts += [
        "",
        "Return JSON in the format specified in the system prompt.",
    ]

    return "\n".join(parts)


def find_low_score_dimensions(scores: dict) -> dict[str, float]:
    """
    Return score dimensions that fell below EVIDENCE_SCORE_THRESHOLD.
    Module-level so all three providers share one copy.
    """
    candidates = {
        "clarity":       scores.get("clarityScore"),
        "structure":     scores.get("structureScore"),
        "depth":         scores.get("depthScore"),
        "confidence":    scores.get("confidenceScore"),
        "communication": scores.get("communicationScore"),
        "technical":     scores.get("technicalScore"),
    }
    return {
        dim: score
        for dim, score in candidates.items()
        if score is not None and score < EVIDENCE_SCORE_THRESHOLD
    }


def build_evidence_user_prompt(
    *,
    question: str,
    answer: str,
    low_score_dimensions: dict[str, float],
) -> str:
    """
    User message for the conditional second call.
    Only fired when one or more dimensions scored below EVIDENCE_SCORE_THRESHOLD.
    Asks the model to quote the specific part of the answer that led to each low score.
    Batches all low-scoring dimensions into one call to avoid per-dimension round trips.
    """
    answer_text = answer.strip() if answer.strip() else "[No answer provided]"
    dim_lines = "\n".join(
        f"- {dim} (scored {score:.0f}/100)"
        for dim, score in low_score_dimensions.items()
    )
    evidence_fields = "\n".join(
        f'  "{dim}Evidence": "<direct quote from the answer explaining the low score>"'
        for dim in low_score_dimensions
    )

    return "\n".join([
        "Question:",
        question,
        "",
        "Candidate Answer:",
        answer_text,
        "",
        "The following dimensions scored below 70. For each, quote the specific",
        "sentence or phrase from the answer that explains the low score.",
        "Quote directly — do not paraphrase.",
        "",
        dim_lines,
        "",
        "Return JSON:",
        "{",
        evidence_fields,
        "}",
    ])
