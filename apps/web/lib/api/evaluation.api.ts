import { apiClient } from "./client";
import { ApiResponse, SessionEvaluationReport } from "@braintrain/shared";

export const evaluationApi = {
    getReport: async (sessionId: string) => {
        const response = await apiClient.get<ApiResponse<SessionEvaluationReport>>(`/evaluation/${sessionId}`);
        return response.data;
    },
};
