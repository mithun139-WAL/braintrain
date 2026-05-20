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
