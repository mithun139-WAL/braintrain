import { apiClient } from "./client";
import {
    ApiResponse,
    CoachingSession,
    SendMessageResponse,
    CreateCoachingSessionRequest,
} from "@braintrain/shared";

export const coachingApi = {
    /**
     * POST /coaching
     * Create a new coaching session for a specific focus area.
     */
    createSession: async (
        data: CreateCoachingSessionRequest
    ): Promise<ApiResponse<CoachingSession>> => {
        const response = await apiClient.post<ApiResponse<CoachingSession>>("/coaching", data);
        return response.data;
    },

    /**
     * GET /coaching
     * List all coaching sessions for the authenticated user.
     *
     * NOTE: The backend returns CoachingSessionListResponse { data: [...], total: N }.
     * After ResponseEnvelopeMiddleware this becomes { success, data: { data: [...], total: N } }.
     * We unwrap the nested data here so callers always get ApiResponse<CoachingSession[]>.
     */
    getSessions: async (): Promise<ApiResponse<CoachingSession[]>> => {
        type ListEnvelope = { data: CoachingSession[]; total: number };
        const response = await apiClient.get<ApiResponse<ListEnvelope>>("/coaching");
        return {
            success: response.data.success,
            data: response.data.data?.data ?? [],
        };
    },

    /**
     * GET /coaching/{id}
     * Get a coaching session with its message history.
     */
    getSession: async (id: string): Promise<ApiResponse<CoachingSession>> => {
        const response = await apiClient.get<ApiResponse<CoachingSession>>(`/coaching/${id}`);
        return response.data;
    },

    /**
     * POST /coaching/{id}/messages
     * Send a message and receive an AI coaching response.
     */
    sendMessage: async (
        sessionId: string,
        content: string
    ): Promise<ApiResponse<SendMessageResponse>> => {
        const response = await apiClient.post<ApiResponse<SendMessageResponse>>(
            `/coaching/${sessionId}/messages`,
            { content }
        );
        return response.data;
    },

    /**
     * PUT /coaching/{id}/end
     * End a coaching session.
     */
    endSession: async (id: string): Promise<ApiResponse<CoachingSession>> => {
        const response = await apiClient.put<ApiResponse<CoachingSession>>(
            `/coaching/${id}/end`
        );
        return response.data;
    },
};
