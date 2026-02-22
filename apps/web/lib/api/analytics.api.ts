import { apiClient } from "./client";
import { ApiResponse, AnalyticsSummaryDto, TrendPoint } from "@braintrain/shared";

export const analyticsApi = {
    getOverview: async () => {
        const response = await apiClient.get<ApiResponse<AnalyticsSummaryDto>>("/analytics/overview");
        return response.data;
    },

    getTrend: async () => {
        const response = await apiClient.get<ApiResponse<TrendPoint[]>>("/analytics/trend");
        return response.data;
    },
};
