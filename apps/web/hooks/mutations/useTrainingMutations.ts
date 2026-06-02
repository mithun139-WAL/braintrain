import { useMutation, useQueryClient } from "@tanstack/react-query";
import { trainingApi } from "@/lib/api/training.api";
import { GeneratePlanRequest } from "@braintrain/shared";

/**
 * useGenerateTrainingPlan — generates an AI-personalized training plan.
 *
 * The AI analyzes:
 *   - Previous session evaluation reports
 *   - Recurring weaknesses (structure, confidence, depth)
 *   - Improvement velocity
 *   - User skill preferences
 *
 * Then generates a targeted 7-day plan with specific micro-exercises.
 */
export const useGenerateTrainingPlan = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data?: GeneratePlanRequest) => trainingApi.generatePlan(data),
        onSuccess: (data) => {
            // Update the current plan cache immediately
            queryClient.setQueryData(["training", "plan", "current"], data);
            queryClient.invalidateQueries({ queryKey: ["training", "plan", "history"] });
        },
    });
};

/**
 * useCompleteTrainingTask — marks a training task as done.
 *
 * Returns updated plan progress including encouragement message.
 */
export const useCompleteTrainingTask = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (taskId: string) => trainingApi.completeTask(taskId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["training", "plan", "current"] });
        },
    });
};
