import { apiClient } from "./client";
import type { ApiResponse } from "@braintrain/shared";
import type {
    InterviewJourney,
    JourneyAnalysis,
    StartRoundResult,
    JourneyFinalReport,
    InterviewJourneySession,
} from "@braintrain/shared";

export interface CreateJourneyDto {
    roleTitle: string;
    jobDescription: string;
    resumeText: string;
    companyName?: string;
}

export interface UploadResumeResult {
    resumeText: string;
    filename: string;
}

export interface JourneyListResponse {
    data: InterviewJourney[];
    total: number;
    page: number;
    limit: number;
}

export const journeysApi = {
    create: async (data: CreateJourneyDto) => {
        const response = await apiClient.post<ApiResponse<InterviewJourney>>("/journeys", data);
        return response.data;
    },

    list: async (params?: { page?: number; limit?: number }) => {
        const response = await apiClient.get<ApiResponse<JourneyListResponse>>("/journeys", { params });
        return response.data?.data as JourneyListResponse;
    },

    getById: async (id: string) => {
        const response = await apiClient.get<ApiResponse<InterviewJourney>>(`/journeys/${id}`);
        return response.data;
    },

    uploadResume: async (file: File) => {
        const formData = new FormData();
        formData.append("file", file);
        const response = await apiClient.post<ApiResponse<UploadResumeResult>>(
            "/journeys/upload-resume",
            formData,
            { headers: { "Content-Type": "multipart/form-data" } }
        );
        return response.data;
    },

    analyze: async (journeyId: string) => {
        const response = await apiClient.post<ApiResponse<JourneyAnalysis>>(
            "/journeys/analyze",
            { journey_id: journeyId }
        );
        return response.data;
    },

    getRounds: async (journeyId: string) => {
        const response = await apiClient.get<ApiResponse<InterviewJourneySession[]>>(
            `/journeys/${journeyId}/rounds`
        );
        return response.data;
    },

    startRound: async (journeyId: string, roundIndex: number) => {
        const response = await apiClient.post<ApiResponse<StartRoundResult>>(
            `/journeys/${journeyId}/start-round`,
            { journey_id: journeyId, round_index: roundIndex }
        );
        return response.data;
    },

    completeRound: async (journeyId: string, journeySessionId: string, interviewSessionId: string) => {
        const response = await apiClient.post<ApiResponse<{ completed: boolean; journeyCompleted: boolean }>>(
            `/journeys/${journeyId}/complete-round`,
            { journey_session_id: journeySessionId, interview_session_id: interviewSessionId }
        );
        return response.data;
    },

    getFinalReport: async (journeyId: string) => {
        const response = await apiClient.get<ApiResponse<JourneyFinalReport>>(
            `/journeys/${journeyId}/final-report`
        );
        return response.data;
    },

    edit: async (journeyId: string, data: Partial<CreateJourneyDto>) => {
        const response = await apiClient.patch<ApiResponse<InterviewJourney>>(`/journeys/${journeyId}`, data);
        return response.data;
    },

    delete: async (journeyId: string) => {
        await apiClient.delete<ApiResponse<void>>(`/journeys/${journeyId}`);
    },
};

