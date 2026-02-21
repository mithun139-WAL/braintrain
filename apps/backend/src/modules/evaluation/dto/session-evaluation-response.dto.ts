import { DifficultyLevel } from '@prisma/client';

/**
 * Structured score dimensions — one value per evaluation axis (0–100).
 * Maps directly to a radar chart or score card on the frontend.
 */
export class EvaluationDimensionsDto {
    /** Coherence and ease of understanding */
    clarity!: number;
    /** STAR / logical flow of the answer */
    structure!: number;
    /** Quality and completeness of content */
    depth!: number;
    /** Assertiveness and tone */
    confidence!: number;
    /** Filler-word density, pacing */
    communication!: number;
    /**
     * Inverse hesitation signal (0 = severe hesitation, 100 = no hesitation).
     * Normalised so higher is always better, consistent with other dimensions.
     */
    hesitation!: number;
    /** Technical correctness — null for behavioral sessions */
    technical!: number | null;
    /** Pressure signal — how composed the candidate was under time pressure (higher = calmer) */
    pressure!: number;
    /** Thinking depth — quality of deliberate pause before answering (higher = more thoughtful) */
    thinkingDepth!: number;
}

/**
 * How difficulty changed over the course of the session.
 * Gives the frontend a simple before/after narrative.
 */
export class DifficultyProgressionDto {
    /** Difficulty the session started at */
    startedAt!: DifficultyLevel;
    /** Difficulty the last question was asked at */
    endedAt!: DifficultyLevel;
}

/**
 * SessionEvaluationResponseDto
 *
 * The canonical product-facing shape returned from:
 *   POST /sessions/:id/evaluation/analyze
 *   GET  /sessions/:id/evaluation
 *
 * Intentionally NOT a Prisma object — all fields are
 * business-meaningful names that the frontend can consume directly.
 */
export class SessionEvaluationResponseDto {
    sessionId!: string;

    /** Weighted aggregate across all dimensions (0–100) */
    overallScore!: number;

    /** One or two sentence human-readable feedback */
    summary!: string;

    /** Per-dimension scores for radar chart / score breakdown */
    dimensions!: EvaluationDimensionsDto;

    /**
     * Top 1–3 things the candidate did well.
     * Derived from dimensions scoring above 70.
     */
    strengths!: string[];

    /**
     * Actionable coaching suggestions, grouped by dimension.
     * Empty array if no significant weaknesses detected.
     */
    improvements!: string[];

    /** How difficulty evolved during the session */
    difficultyProgression!: DifficultyProgressionDto;

    /** ISO timestamp of when the evaluation was created */
    evaluatedAt!: string;
}
