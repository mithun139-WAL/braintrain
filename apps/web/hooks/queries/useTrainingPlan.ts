import { useQuery } from "@tanstack/react-query";
import { trainingApi } from "@/lib/api/training.api";

/**
 * useCurrentTrainingPlan — fetches the user's active training plan.
 *
 * Returns null if no active plan exists (user needs to generate one).
 */
export const useCurrentTrainingPlan = () => {
    return useQuery({
        queryKey: ["training", "plan", "current"],
        queryFn: () => trainingApi.getCurrentPlan(),
        staleTime: 5 * 60 * 1000,
        retry: false,           // 404 = no plan exists, don't retry
    });
};

/**
 * useTrainingHistory — fetches all past training plans.
 */
export const useTrainingHistory = () => {
    return useQuery({
        queryKey: ["training", "plan", "history"],
        queryFn: () => trainingApi.getPlanHistory(),
        staleTime: 10 * 60 * 1000,
    });
};
