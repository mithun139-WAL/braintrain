/**
 * PerformanceSignal — the structured output of any AI evaluation provider.
 *
 * All scores are in the range 0–100.
 * The structure deliberately mirrors the EvaluationReport DB model
 * so scores can be persisted without transformation.
 */
export interface PerformanceSignal {
    /** Structure and coherence of the answer (is it easy to follow?) */
    clarityScore: number;
    /** STAR / logical flow — how well the response is structured */
    structureScore: number;
    /** Quality, completeness, and depth of content */
    depthScore: number;
    /** Assertiveness, tone, and confidence of delivery */
    confidenceScore: number;
    /** Filler-word density, pacing, and articulation */
    communicationScore: number;
    /**
     * Hesitation signal — computed deterministically from pauses/fillers.
     * Lower is better (0 = no hesitation, 100 = severe hesitation).
     */
    hesitationScore: number;
    /**
     * Factual/technical correctness — only meaningful for technical questions.
     * null for behavioral questions.
     */
    technicalScore: number | null;
    /**
     * Weighted aggregate across all dimensions.
     * This is the primary signal consumed by the AdaptiveEngine.
     */
    overallScore: number;
    /** Human-readable explanation from the LLM or stub */
    explanation: string;
}
