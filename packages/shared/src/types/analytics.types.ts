// Analytics types — mirrors FastAPI AnalyticsResponseSchema + ProgressionResponseSchema
// All fields are camelCase (converted from snake_case by axios interceptor)

export interface TrendItem {
    sessionId: string;
    topicName: string;
    interviewType?: string;
    analyzedAt: string;           // ISO-8601
    overallScore: number;
    confidenceScore: number;
    clarityScore: number;
    structureScore: number;
    depthScore: number;
}

export interface ImprovementData {
    overallDelta: number;
    confidenceDelta: number;
    clarityDelta: number;
    topImprovedDimension?: string;
    topWeakDimension?: string;
}

export interface TopicBreakdown {
    topicId: string;
    topicName: string;
    sessionCount: number;
    avgOverallScore: number;
}

export interface AnalyticsResponse {
    totalSessions: number;
    analyzedSessions: number;
    trend: TrendItem[];
    improvement: ImprovementData;
    byTopic: TopicBreakdown[];
}

export interface TopicTrendItem {
    sessionId: string;
    analyzedAt: string;
    overallScore: number;
    confidenceScore: number;
    clarityScore: number;
    structureScore: number;
    depthScore: number;
    interviewType?: string;
    interviewMode?: string;
    difficulty: string;
}

export interface TopicAnalyticsResponse {
    topicId: string;
    totalSessions: number;
    analyzedSessions: number;
    averageScore: number;
    scoreDelta?: number | null;
    latestScore?: number | null;
    lastSessionAt?: string | null;
    trend: TopicTrendItem[];
}

export interface SessionRef {
    sessionId: string;
    overallScore?: number;
    analyzedAt?: string;        // ISO-8601
}

export interface ProgressionResponse {
    lastSession?: SessionRef;
    previousSession?: SessionRef;
    delta?: number;             // positive = improvement, negative = regression
}

// ─── Legacy aliases (kept for backwards compatibility) ────────────────────────
/** @deprecated Use AnalyticsResponse instead */
export interface TrendPoint {
    date: string;
    averageScore: number;
}


// ─── Cognitive Analytics Types ────────────────────────────────────────────────

export interface CognitiveMindState {
    confidenceLevel: number;
    stressTolerance: number;
    communicationClarity: number;
    responseStructure: number;
    fillerWordControl: number;
    speakingConsistency: number;
    executivePresence: number;
    memoryRecallStrength: number;
    strategicThinking: number;
    cognitiveLoadTolerance: number;
    sessionCount: number;
}

export interface CognitiveNode {
    id: string;
    conceptName: string;
    conceptType: string;
    familiarityScore: number;
    confidenceScore: number;
    recallLatency: number;
    retentionStrength: number;
    pressureRecallStability: number;
    exposureCount: number;
    masteryLevel: number;
    isFragile: boolean;
    isWeakRecall: boolean;
    isStrongRecall: boolean;
    nextReviewAt?: string | null;
}

export interface CognitiveEdge {
    id: string;
    sourceNodeId: string;
    targetNodeId: string;
    relationshipType: string;
    strength: number;
}

export interface Drill {
    conceptName: string;
    drillType: string;
    recommendedDifficulty: string;
    instruction: string;
}

export interface RecoveryExercise {
    conceptName: string;
    anchors: string[];
    exercise: string;
}

export interface CognitiveAnalyticsResponse {
    mindState?: CognitiveMindState | null;
    nodes: CognitiveNode[];
    edges: CognitiveEdge[];
    drills: Drill[];
    recoveryExercises: RecoveryExercise[];
    trajectory: Record<string, number[]>;
}

