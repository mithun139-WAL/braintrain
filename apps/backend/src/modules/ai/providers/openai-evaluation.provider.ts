import { Injectable, Logger } from '@nestjs/common';
import OpenAI from 'openai';
import { DifficultyLevel } from '@prisma/client';
import { AnswerEvaluationProvider } from '../interfaces/answer-evaluation-provider.interface';
import { EvaluationInput } from '../interfaces/evaluation-input.interface';
import { PerformanceSignal } from '../interfaces/performance-signal.interface';
import { StubEvaluationProvider } from './stub-evaluation.provider';
import {
    EVALUATION_SYSTEM_PROMPT,
    buildEvaluationUserPrompt,
    PROMPT_VERSION,
    MODEL_USED,
} from '../prompts/evaluation.prompts';

/** gpt-4o-mini pricing (update if model changes) */
const COST_PER_INPUT_TOKEN = 0.00000015;  // $0.15 / 1M input tokens
const COST_PER_OUTPUT_TOKEN = 0.0000006;   // $0.60 / 1M output tokens

/** Hard cap — we only need a tiny JSON blob back */
const MAX_OUTPUT_TOKENS = 150;

/** Difficulty boost applied to overallScore before clamp (spec §7) */
const DIFFICULTY_BOOST: Record<DifficultyLevel, number> = {
    BEGINNER: 0,
    INTERMEDIATE: 0,
    ADVANCED: 4, // +4 for HARD — fairness adjustment
};

/** Fields the LLM is responsible for scoring (6 content dimensions) */
const LLM_SCORE_FIELDS = [
    'clarityScore',
    'structureScore',
    'depthScore',
    'confidenceScore',
    'communicationScore',
] as const;

type LlmScoreField = (typeof LLM_SCORE_FIELDS)[number];

/** Parsed response from LLM — 6 fields only */
interface LlmScores {
    clarityScore: number;
    structureScore: number;
    depthScore: number;
    confidenceScore: number;
    communicationScore: number;
    technicalScore: number | null;
}

export interface EvaluationCostMeta {
    inputTokens: number;
    outputTokens: number;
    estimatedCostUsd: number;
    modelUsed: string;
    promptVersion: string;
    degraded: boolean;
}

function clamp(value: number): number {
    return Math.max(0, Math.min(100, Math.round(value)));
}

@Injectable()
export class OpenAIEvaluationProvider implements AnswerEvaluationProvider {
    private readonly logger = new Logger(OpenAIEvaluationProvider.name);
    private readonly client: OpenAI;
    private readonly fallback: StubEvaluationProvider;

    constructor() {
        if (!process.env.OPENAI_API_KEY) {
            throw new Error('OPENAI_API_KEY is required for OpenAIEvaluationProvider');
        }
        this.client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
        this.fallback = new StubEvaluationProvider();
    }

    async evaluate(input: EvaluationInput): Promise<PerformanceSignal> {
        const userPrompt = buildEvaluationUserPrompt({
            question: input.question,
            answer: input.text ?? '',
            questionType: input.questionType,
            difficulty: input.difficulty,
        });

        // ── Call LLM with one retry ─────────────────────────────────────────
        const llmScores = await this.callWithRetry(userPrompt, input.difficulty);

        if (!llmScores) {
            this.logger.warn('LLM returned malformed JSON after retry — degraded mode (stub)');
            const stub = await this.fallback.evaluate(input);
            // Tag as degraded via __meta
            (stub as any).__meta = {
                inputTokens: 0, outputTokens: 0, estimatedCostUsd: 0,
                modelUsed: 'stub-degraded', promptVersion: PROMPT_VERSION, degraded: true,
            } satisfies EvaluationCostMeta;
            return stub;
        }

        const { scores, meta } = llmScores;

        // ── Gap 1: pressure + thinkingDepth computed server-side ──────────
        const pressureScore = this.computePressureScore(input.responseTimeMs);
        const thinkingDepthScore = this.computeThinkingDepthScore(input.thinkingTimeMs);

        // ── Gap 2: overallScore computed server-side with weighted formula ─
        const overallScore = this.computeOverallScore({
            clarityScore: scores.clarityScore,
            structureScore: scores.structureScore,
            depthScore: scores.depthScore,
            confidenceScore: scores.confidenceScore,
            communicationScore: scores.communicationScore,
            technicalScore: scores.technicalScore,
            pressureScore,
            thinkingDepthScore,
            questionType: input.questionType,
            difficulty: input.difficulty,
        });

        const signal: PerformanceSignal = {
            clarityScore: scores.clarityScore,
            structureScore: scores.structureScore,
            depthScore: scores.depthScore,
            confidenceScore: scores.confidenceScore,
            communicationScore: scores.communicationScore,
            hesitationScore: 0, // deprecated — replaced by pressureScore + thinkingDepthScore
            technicalScore: scores.technicalScore,
            pressureScore,
            thinkingDepthScore,
            overallScore,
            explanation: '', // Not requested from LLM — keeps tokens low
        };

        (signal as any).__meta = meta satisfies EvaluationCostMeta;

        this.logger.debug(
            `Evaluated | Overall: ${overallScore} | ` +
            `Tokens: ${meta.inputTokens}in/${meta.outputTokens}out | ` +
            `Cost: $${meta.estimatedCostUsd.toFixed(6)} | ` +
            `Model: ${meta.modelUsed} | Prompt: ${meta.promptVersion}`,
        );

        return signal;
    }

    // ── Retry logic (spec §5) ─────────────────────────────────────────────
    private async callWithRetry(
        userPrompt: string,
        difficulty: DifficultyLevel,
    ): Promise<{ scores: LlmScores; meta: EvaluationCostMeta } | null> {
        for (let attempt = 1; attempt <= 2; attempt++) {
            try {
                const completion = await this.client.chat.completions.create({
                    model: MODEL_USED,
                    response_format: { type: 'json_object' },
                    temperature: 0.1,         // spec: 0–0.2 for determinism
                    max_tokens: MAX_OUTPUT_TOKENS,
                    messages: [
                        { role: 'system', content: EVALUATION_SYSTEM_PROMPT },
                        { role: 'user', content: userPrompt },
                    ],
                });

                const raw = completion.choices[0]?.message?.content ?? '';
                const inputTokens = completion.usage?.prompt_tokens ?? 0;
                const outputTokens = completion.usage?.completion_tokens ?? 0;
                const estimatedCostUsd =
                    inputTokens * COST_PER_INPUT_TOKEN + outputTokens * COST_PER_OUTPUT_TOKEN;

                const scores = this.parseAndValidate(raw, difficulty);

                if (scores) {
                    return {
                        scores,
                        meta: {
                            inputTokens,
                            outputTokens,
                            estimatedCostUsd,
                            modelUsed: MODEL_USED,
                            promptVersion: PROMPT_VERSION,
                            degraded: false,
                        },
                    };
                }

                this.logger.warn(
                    `Attempt ${attempt}: malformed JSON from LLM. Raw: ${raw.slice(0, 200)}`,
                );
            } catch (err: unknown) {
                const message = err instanceof Error ? err.message : String(err);
                this.logger.error(`Attempt ${attempt}: OpenAI API call failed — ${message}`);
            }
        }
        return null;
    }

    // ── Parse + validate 6-field LLM response ────────────────────────────
    private parseAndValidate(raw: string, difficulty: DifficultyLevel): LlmScores | null {
        try {
            const parsed = JSON.parse(raw);

            // Validate all 5 required numeric content fields
            for (const field of LLM_SCORE_FIELDS) {
                const value = parsed[field];
                if (typeof value !== 'number' || isNaN(value)) {
                    this.logger.warn(`Validation failed: ${field} = ${value}`);
                    return null;
                }
            }

            // technicalScore may be null for behavioral questions
            if (parsed.technicalScore !== null && typeof parsed.technicalScore !== 'number') {
                this.logger.warn(`Invalid technicalScore: ${parsed.technicalScore}`);
                return null;
            }

            const boost = DIFFICULTY_BOOST[difficulty] ?? 0;

            return {
                clarityScore: clamp(parsed.clarityScore + boost),
                structureScore: clamp(parsed.structureScore + boost),
                depthScore: clamp(parsed.depthScore + boost),
                confidenceScore: clamp(parsed.confidenceScore),
                communicationScore: clamp(parsed.communicationScore),
                technicalScore: parsed.technicalScore !== null
                    ? clamp(parsed.technicalScore + boost)
                    : null,
            };
        } catch {
            return null;
        }
    }

    // ── Gap 1: Deterministic pressure score from responseTimeMs (spec §2) ─
    // Optimal response time sweet spot: 15–45s
    // Too fast (< 10s) = likely panicked/rushing
    // Too slow (> 90s) = likely rambling
    private computePressureScore(responseTimeMs?: number): number {
        if (!responseTimeMs) return 50; // neutral if not recorded

        const seconds = responseTimeMs / 1000;

        if (seconds < 5) return 20;  // panicked rush
        if (seconds < 10) return 40;  // rushed
        if (seconds <= 45) return 80 + Math.round((45 - seconds) / 35 * 15); // 80–95 sweet spot
        if (seconds <= 90) return clamp(80 - Math.round((seconds - 45) / 45 * 30)); // degrading
        return 30; // rambling
    }

    // ── Gap 1: Deterministic thinking depth score from thinkingTimeMs ─────
    // Optimal pause: 4–12s (deliberate composition)
    // < 2s = reactive, no thought
    // > 20s = stuck / frozen
    private computeThinkingDepthScore(thinkingTimeMs?: number): number {
        if (!thinkingTimeMs) return 50; // neutral

        const seconds = thinkingTimeMs / 1000;

        if (seconds < 1) return 20;  // zero pause = reactive
        if (seconds < 3) return 50;  // minimal pause
        if (seconds <= 12) return clamp(65 + Math.round((seconds - 3) / 9 * 30)); // 65–95
        if (seconds <= 20) return clamp(95 - Math.round((seconds - 12) / 8 * 30)); // 65–95 fading
        return 35; // frozen / stuck
    }

    // ── Gap 2: Server-side weighted overallScore (spec §4) ─────────────────
    // Weights:
    //   - Behavioral: content 55%, communication/confidence 35%, timing 10%
    //   - Technical:  content 45%, technical 30%, communication 15%, timing 10%
    private computeOverallScore(params: {
        clarityScore: number;
        structureScore: number;
        depthScore: number;
        confidenceScore: number;
        communicationScore: number;
        technicalScore: number | null;
        pressureScore: number;
        thinkingDepthScore: number;
        questionType: string;
        difficulty: DifficultyLevel;
    }): number {
        const timingScore = (params.pressureScore + params.thinkingDepthScore) / 2;

        let score: number;

        if (params.questionType === 'technical' && params.technicalScore !== null) {
            // Technical weighting
            const contentAvg = (params.clarityScore + params.structureScore + params.depthScore) / 3;
            score =
                contentAvg * 0.45 +
                params.technicalScore * 0.30 +
                params.communicationScore * 0.10 +
                params.confidenceScore * 0.05 +
                timingScore * 0.10;
        } else {
            // Behavioral weighting
            const contentAvg = (params.clarityScore + params.structureScore + params.depthScore) / 3;
            score =
                contentAvg * 0.45 +
                params.confidenceScore * 0.20 +
                params.communicationScore * 0.15 +
                timingScore * 0.10 +
                (params.technicalScore ?? 50) * 0.10;
        }

        // Difficulty boost (spec §7) already applied to individual scores in parseAndValidate
        return clamp(score);
    }
}
