import { apiClient } from "./client";
import {
    ApiResponse,
    TrainingPlan,
    GeneratePlanRequest,
    CompleteTaskResponse,
} from "@braintrain/shared";

export const trainingApi = {
    /**
     * POST /training/plans
     * Generate (or regenerate) an AI training plan based on session history.
     */
    generatePlan: async (data?: GeneratePlanRequest): Promise<ApiResponse<TrainingPlan>> => {
        const response = await apiClient.post<ApiResponse<TrainingPlan>>("/training-plans/generate", data || {});
        return response.data;
    },

    /**
     * GET /training/plans/current
     * Get the user's active training plan.
     */
    getCurrentPlan: async (): Promise<ApiResponse<TrainingPlan>> => {
        const response = await apiClient.get<ApiResponse<TrainingPlan>>("/training-plans/current");
        return response.data;
    },

    /**
     * GET /training/plans/history
     * List all past training plans.
     */
    getPlanHistory: async (): Promise<ApiResponse<TrainingPlan[]>> => {
        const response = await apiClient.get<ApiResponse<TrainingPlan[]>>("/training-plans");
        return response.data;
    },

    /**
     * POST /training/tasks/{id}/complete
     * Mark a training task as completed.
     */
    completeTask: async (taskId: string): Promise<ApiResponse<CompleteTaskResponse>> => {
        const response = await apiClient.post<ApiResponse<CompleteTaskResponse>>(
            `/training-plans/tasks/${taskId}/complete`
        );
        return response.data;
    },
};
