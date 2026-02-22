export interface PerformanceSignal {
    clarityScore: number;
    structureScore: number;
    depthScore: number;
    confidenceScore: number;
    communicationScore: number;
    hesitationScore: number;
    technicalScore: number;
    overallScore: number;
}

export interface SessionEvaluationReport {
    sessionId: string;
    overallScore: number;
    averageScores: PerformanceSignal;
    strengths: string[];
    improvementAreas: string[];
    summary: string;
}
