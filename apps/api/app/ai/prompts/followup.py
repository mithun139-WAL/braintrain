"""
Follow-up analysis prompt — drives real-time interview coaching during practice sessions.

Design principle:
  Analyse the candidate's answer immediately after submission.
  If gaps exist, generate ONE targeted follow-up question to help the candidate
  discover what they missed — exactly as a real interviewer would probe.
  Never reveal the answer; only guide through Socratic questioning.
  Max 2 follow-up rounds per question; after that always return needs_followup=false.

Response format: strict JSON only (json_object mode).
"""

FOLLOWUP_PROMPT_VERSION = "v1.0.0"
FOLLOWUP_MODEL_USED = "gpt-4o-mini"

FOLLOWUP_SYSTEM_PROMPT = """You are an expert technical and behavioral interviewer conducting a real-time practice session.

Your role is to analyse the candidate's answer and decide whether a follow-up probe is needed.

Rules:
- Return ONLY a strict JSON object — no markdown, no prose outside JSON.
- If the answer is incomplete, missing key concepts, or too vague, set needs_followup to true and provide ONE targeted follow-up question.
- The follow-up question must be Socratic — guide the candidate toward the gap without revealing the answer.
- If the answer is sufficiently complete, set needs_followup to false and write a brief acknowledgement.
- Keep acknowledgement under 30 words — it is shown inline in the chat.
- Keep followup_question under 25 words — sharp and specific.
- gap_identified should name the missing concept/area concisely (max 10 words).
- Do NOT ask follow-ups that are entirely off-topic from the original question.
- Do NOT be overly harsh — only flag genuine gaps that matter for the role.

Return ONLY this JSON object:
{
  "needs_followup": <true|false>,
  "followup_question": <string or null>,
  "acknowledgement": <string>,
  "gap_identified": <string or null>
}""".strip()


def build_followup_user_prompt(
    *,
    question: str,
    answer: str,
    interview_type: str,
    difficulty: str,
    prior_exchanges: list[dict],  # [{"followup_question": str, "followup_answer": str}, ...]
) -> str:
    """
    Build the user message for follow-up analysis.

    prior_exchanges carries the conversation history so the LLM can detect
    whether a previously-identified gap was addressed in a follow-up round.
    """
    lines = [
        "Interview Context:",
        f"Interview Type: {interview_type}",
        f"Difficulty: {difficulty}",
        "",
        "Original Question:",
        question.strip(),
        "",
        "Candidate's Initial Answer:",
        answer.strip() if answer.strip() else "[No answer provided]",
    ]

    if prior_exchanges:
        lines += ["", "Follow-up Exchange History:"]
        for i, ex in enumerate(prior_exchanges, start=1):
            lines += [
                f"  Round {i} — Interviewer asked: {ex.get('followup_question', '')}",
                f"  Round {i} — Candidate replied: {ex.get('followup_answer', '')}",
            ]

    lines += [
        "",
        "Analyse the full conversation above.",
        "Determine if the candidate has adequately covered the key concepts for this question.",
        "Return JSON in this format:",
        "{",
        '  "needs_followup": boolean,',
        '  "followup_question": string or null,',
        '  "acknowledgement": string,',
        '  "gap_identified": string or null',
        "}",
    ]

    return "\n".join(lines)
