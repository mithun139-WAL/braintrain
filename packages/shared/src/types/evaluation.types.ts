// Evaluation types — mirrors FastAPI SessionEvaluationResponseSchema
// All fields are camelCase (converted from snake_case by axios interceptor)

export interface EvaluationDimensions {
    clarity: number;
    structure: number;
    depth: number;
    confidence: number;
    communication: number;
    // hesitation removed in v1.1.0 — was always 100 (hardcoded 0.0 inverted).
    // Composure signal is now covered by pressure + thinkingDepth.
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
    // hesitationScore removed in v1.1.0 — see EvaluationDimensions comment above
    technicalScore?: number;
    technicalAccuracyIssues?: string[];   // factual contradictions vs reference KB
    technicalAccuracyEvidence?: string;   // "Reference facts confirm/contradict: ..."
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
