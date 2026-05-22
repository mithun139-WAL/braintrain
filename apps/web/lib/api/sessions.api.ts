import { apiClient } from "./client";
import { CreateSessionDto, ApiResponse, Session } from "@braintrain/shared";

export interface SessionListItem {
    id: string;
    userId: string;
    topicId: string;
    interviewMode?: string | null;
    interviewType?: string | null;
    difficulty: string;
    adaptive: boolean;
    durationMinutes: number;
    status: string;
    startedAt?: string | null;
    endedAt?: string | null;
    createdAt: string;
    updatedAt: string;
    topic?: {
        id: string;
        name: string;
    } | null;
    evaluation?: {
        overallScore: number;
    } | null;
    questionCount: number;
}

export interface SessionListMeta {
    total: number;
    page: number;
    limit: number;
    totalPages: number;
}

export interface SessionListResponse {
    data: SessionListItem[];
    meta: SessionListMeta;
}

const EMPTY_SESSION_LIST_RESPONSE: SessionListResponse = {
    data: [],
    meta: {
        total: 0,
        page: 1,
        limit: 20,
        totalPages: 0,
    },
};

export const sessionsApi = {
    getSessions: async (params?: { status?: string; page?: number; limit?: number; topicId?: string }): Promise<SessionListResponse> => {
        const response = await apiClient.get<ApiResponse<SessionListResponse>>("/sessions", { params });

        const payload = response.data?.data as SessionListResponse | undefined;
        if (payload && Array.isArray(payload.data) && payload.meta) {
            return payload;
        }

        return EMPTY_SESSION_LIST_RESPONSE;
    },

    getById: async (id: string) => {
        const response = await apiClient.get<ApiResponse<Session>>(`/sessions/${id}`);
        return response.data;
    },

    create: async (data: CreateSessionDto) => {
        const response = await apiClient.post<ApiResponse<Session>>("/sessions", data);
        return response.data;
    },

    start: async (id: string) => {
        const response = await apiClient.put<ApiResponse<Session>>(`/sessions/${id}/start`);
        return response.data;
    },

    /**
     * PUT /sessions/{id}/complete
     * Transitions session ACTIVE → COMPLETED and enqueues an EvaluationJob.
     * NOTE: Backend uses PUT, not POST.
     */
    complete: async (id: string) => {
        const response = await apiClient.put<ApiResponse<Session>>(`/sessions/${id}/complete`);
        return response.data;
    },

    getStatus: async (id: string) => {
        const response = await apiClient.get<ApiResponse<{ status: Session["status"] }>>(`/sessions/${id}/status`);
        return response.data;
    },

    getWebRTCToken: async (id: string) => {
        const response = await apiClient.get<ApiResponse<{ token: string }>>(`/sessions/${id}/webrtc-token`);
        return response.data;
    },
};

