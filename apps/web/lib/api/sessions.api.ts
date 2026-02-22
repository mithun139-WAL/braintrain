import { apiClient } from "./client";
import { CreateSessionDto, SubmitAnswerDto, ApiResponse, Session } from "@braintrain/shared";

export const sessionsApi = {
    getSessions: async () => {
        const response = await apiClient.get<ApiResponse<Session[]>>("/sessions");
        return response.data;
    },

    getById: async (id: string) => {
        const response = await apiClient.get<ApiResponse<Session>>(`/sessions/${id}`);
        return response.data;
    },

    create: async (data: CreateSessionDto) => {
        const response = await apiClient.post<ApiResponse<Session>>("/sessions", data);
        return response.data;
    },

    submitAnswer: async (id: string, data: SubmitAnswerDto) => {
        const response = await apiClient.post<ApiResponse<void>>(`/sessions/${id}/answers`, data);
        return response.data;
    },

    getStatus: async (id: string) => {
        const response = await apiClient.get<ApiResponse<{ status: Session["status"] }>>(`/sessions/${id}/status`);
        return response.data;
    },

    complete: async (id: string) => {
        const response = await apiClient.post<ApiResponse<void>>(`/sessions/${id}/complete`);
        return response.data;
    }
};
