/**
 * Evaluation prompt definitions — versioned for analytics consistency.
 * PROMPT_VERSION stored in EvaluationReport so score comparisons are traceable.
 *
 * Design principle:
 *   LLM scores ONLY content-based dimensions (6 fields).
 *   pressureScore + thinkingDepthScore are computed SERVER-SIDE from timing data.
 *   overallScore is computed SERVER-SIDE with weighted formula.
 *   This keeps scoring defensible, cheap, and auditable.
 */

export const PROMPT_VERSION = 'v1.0.0';
export const MODEL_USED = 'gpt-4o-mini';

/**
 * System prompt — strict JSON only, 6 content dimensions.
 * Calibration anchors keep scores consistent across sessions.
 */
export const EVALUATION_SYSTEM_PROMPT = `
You are an expert technical and behavioral interview evaluator.

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
}
`.trim();

/**
 * User message for a specific answer evaluation.
 * Keeps to the 6 LLM-scorable content dimensions.
 * Does NOT include timing data — timing is evaluated server-side.
 */
export function buildEvaluationUserPrompt(params: {
    question: string;
    answer: string;
    questionType: 'behavioral' | 'technical';
    difficulty: string;
}): string {
    return [
        `Interview Context:`,
        `Question Type: ${params.questionType}`,
        `Difficulty: ${params.difficulty}`,
        ``,
        `Question:`,
        params.question,
        ``,
        `Candidate Answer:`,
        params.answer || '[No answer provided — candidate did not respond]',
        ``,
        `Return JSON in this format:`,
        `{`,
        `  "clarityScore": number,`,
        `  "structureScore": number,`,
        `  "depthScore": number,`,
        `  "confidenceScore": number,`,
        `  "communicationScore": number,`,
        `  "technicalScore": number or null`,
        `}`,
    ].join('\n');
}
