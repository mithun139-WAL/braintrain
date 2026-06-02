import { apiClient } from "./client";
import { ApiResponse, SessionEvaluationResponse } from "@braintrain/shared";

export const evaluationApi = {
    /**
     * GET /sessions/{sessionId}/evaluation
     * Fetch an existing evaluation report for an analyzed session.
     */
    getReport: async (sessionId: string): Promise<ApiResponse<SessionEvaluationResponse>> => {
        const response = await apiClient.get<ApiResponse<SessionEvaluationResponse>>(
            `/sessions/${sessionId}/evaluation`
        );
        return response.data;
    },

    /**
     * POST /sessions/{sessionId}/evaluation/analyze
     * Trigger AI evaluation for a COMPLETED session.
     * This is idempotent — calling it twice returns the existing report on the second call (409 guard).
     */
    analyzeSession: async (sessionId: string): Promise<ApiResponse<SessionEvaluationResponse>> => {
        const response = await apiClient.post<ApiResponse<SessionEvaluationResponse>>(
            `/sessions/${sessionId}/evaluation/analyze`
        );
        return response.data;
    },
};
