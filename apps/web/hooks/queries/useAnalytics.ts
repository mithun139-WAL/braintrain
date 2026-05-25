import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api/analytics.api";

/**
 * useAnalytics — fetches full user performance analytics.
 *
 * Returns trend data, improvement deltas, and per-topic breakdown.
 * Stale time: 5 minutes — analytics don't change between sessions.
 */
export const useAnalytics = () => {
    return useQuery({
        queryKey: ["analytics", "overview"],
        queryFn: () => analyticsApi.getAnalytics(),
        staleTime: 5 * 60 * 1000,
        retry: 1,
    });
};

/**
 * useProgression — fetches the last-vs-previous session delta.
 *
 * Powers the "You improved by +X.X points!" dopamine-loop banner
 * on the dashboard homepage.
 */
export const useProgression = () => {
    return useQuery({
        queryKey: ["analytics", "progression"],
        queryFn: () => analyticsApi.getProgression(),
        staleTime: 5 * 60 * 1000,
        retry: 1,
    });
};

export const useCognitiveAnalytics = () => {
    return useQuery({
        queryKey: ["analytics", "cognitive"],
        queryFn: () => analyticsApi.getCognitiveAnalytics(),
        staleTime: 5 * 60 * 1000,
        retry: 1,
    });
};
