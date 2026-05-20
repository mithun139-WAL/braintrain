// Evaluation types — mirrors FastAPI SessionEvaluationResponseSchema
// All fields are camelCase (converted from snake_case by axios interceptor)

export interface EvaluationDimensions {
    clarity: number;
    structure: number;
    depth: number;
    confidence: number;
    communication: number;
    hesitation: number;           // inverted: higher = better (less hesitation)
    technical?: number;           // null for behavioral sessions
    pressure: number;             // server-computed from response_time_ms
    thinkingDepth: number;        // server-computed from thinking_time_ms
}

export interface DifficultyProgression {
    startedAt: string;            // e.g. "MEDIUM"
    endedAt: string;              // difficulty of last question
}

export interface SessionEvaluationResponse {
    sessionId: string;
    overallScore: number;
    summary: string;
    dimensions: EvaluationDimensions;
    strengths: string[];
    improvements: string[];
    difficultyProgression: DifficultyProgression;
    evaluatedAt: string;          // ISO-8601
}

// ─── Performance signal used in evaluation requests ───────────────────────────
export interface PerformanceSignal {
    clarityScore: number;
    structureScore: number;
    depthScore: number;
    confidenceScore: number;
    communicationScore: number;
    hesitationScore: number;
    technicalScore?: number;
    overallScore: number;
}

// ─── Legacy alias (kept for backwards compatibility) ─────────────────────────
/** @deprecated Use SessionEvaluationResponse instead */
export interface SessionEvaluationReport {
    sessionId: string;
    overallScore: number;
    averageScores: PerformanceSignal;
    strengths: string[];
    improvementAreas: string[];
    summary: string;
}
