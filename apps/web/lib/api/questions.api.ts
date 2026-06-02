import { apiClient } from "./client";
import { ApiResponse } from "@braintrain/shared";

export const questionsApi = {
    generateNext: async (sessionId: string) => {
        const response = await apiClient.post<ApiResponse<any>>(`/sessions/${sessionId}/questions/next`);
        return response.data;
    },

    submitResponse: async (questionId: string, answerText: string) => {
        const response = await apiClient.post<ApiResponse<any>>(`/questions/${questionId}/responses`, {
            answerText,
            responseTimeMs: 0,
            thinkingTimeMs: 0
        });
        return response.data;
    }
};
