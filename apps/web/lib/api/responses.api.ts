import { apiClient } from "./client";
import { ApiResponse } from "@braintrain/shared";

export interface FollowupExchange {
    followupQuestion: string;
    followupAnswer: string;
}

export interface FollowupResponse {
    needsFollowup: boolean;
    followupQuestion: string | null;
    acknowledgement: string;
    gapIdentified: string | null;
    exchangeNumber: number;
}

export const responsesApi = {
    checkFollowup: async (
        questionId: string,
        responseId: string,
        priorExchanges: FollowupExchange[] = []
    ): Promise<FollowupResponse> => {
        const response = await apiClient.post<ApiResponse<FollowupResponse>>(
            `/questions/${questionId}/responses/${responseId}/followup`,
            { priorExchanges }
        );
        return response.data.data;
    },
};
