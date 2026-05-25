import { apiClient } from "./client";
import {
    ApiResponse,
    AnalyticsResponse,
    ProgressionResponse,
    TopicAnalyticsResponse,
    CognitiveAnalyticsResponse,
} from "@braintrain/shared";

export const analyticsApi = {
    /**
     * GET /analytics/me
     * Full user performance analytics: trend, improvement delta, per-topic breakdown.
     */
    getAnalytics: async (): Promise<ApiResponse<AnalyticsResponse>> => {
        const response = await apiClient.get<ApiResponse<AnalyticsResponse>>("/analytics/me");
        return response.data;
    },

    /**
     * GET /analytics/progression
     * Last-vs-previous session score delta (dopamine-loop banner data).
     */
    getProgression: async (): Promise<ApiResponse<ProgressionResponse>> => {
        const response = await apiClient.get<ApiResponse<ProgressionResponse>>("/analytics/progression");
        return response.data;
    },

    getTopicAnalytics: async (topicId: string): Promise<ApiResponse<TopicAnalyticsResponse>> => {
        const response = await apiClient.get<ApiResponse<TopicAnalyticsResponse>>(`/analytics/topics/${topicId}`);
        return response.data;
    },

    getCognitiveAnalytics: async (): Promise<ApiResponse<CognitiveAnalyticsResponse>> => {
        const response = await apiClient.get<ApiResponse<CognitiveAnalyticsResponse>>("/analytics/cognitive");
        return response.data;
    },
};
