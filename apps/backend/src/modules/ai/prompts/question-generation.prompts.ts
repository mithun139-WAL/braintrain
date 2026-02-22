/**
 * Question generation prompt definitions — versioned for dataset consistency.
 * Generated questions are saved back to QuestionBank to build proprietary dataset.
 */

export const CURRENT_QUESTION_GEN_PROMPT_VERSION = 'qgen-v1';

export const QUESTION_GEN_SYSTEM_PROMPT = `
You are an expert technical interviewer and question designer.
Your job is to generate ONE high-quality interview question and return ONLY a valid JSON object.
No explanations outside the JSON. No markdown. No code blocks. Pure JSON only.

Question design rules:
- Questions must be specific, not generic
- BEHAVIORAL questions should follow STAR-method format triggers  
- TECHNICAL questions should test deep practical understanding, not just definitions
- Difficulty calibration: BEGINNER = foundational, INTERMEDIATE = applied, ADVANCED = system-level or edge-cases
- Never repeat cliché questions like "Tell me about yourself"

Return exactly this JSON schema and nothing else:
{
  "questionText": "<the full interview question>",
  "expectedAnswerTraits": ["<trait1>", "<trait2>", "<trait3>"],
  "estimatedDifficulty": "<BEGINNER|INTERMEDIATE|ADVANCED>"
}
`.trim();

export function buildQuestionGenUserPrompt(params: {
    topicName: string;
    difficulty: string;
    questionType: 'behavioral' | 'technical';
    existingQuestions?: string[];
}): string {
    const lines = [
        `Generate ONE ${params.questionType} interview question about: ${params.topicName}`,
        `Required difficulty level: ${params.difficulty}`,
    ];

    if (params.existingQuestions && params.existingQuestions.length > 0) {
        lines.push('');
        lines.push('Do NOT generate any of these already-asked questions:');
        params.existingQuestions.forEach((q, i) => {
            lines.push(`${i + 1}. ${q}`);
        });
    }

    lines.push('');
    lines.push('Return only the JSON object described in your instructions.');

    return lines.join('\n');
}
