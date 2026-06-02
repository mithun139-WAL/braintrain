import { TrendPoint, TopicBreakdown } from "../types/analytics.types";

export interface AnalyticsSummaryDto {
    totalSessions: number;
    averageScore: number;
    skillsImproved: number;
    recentTrend: "up" | "down" | "flat";
    trends: TrendPoint[];
    topicPerformance: TopicBreakdown[];
}
