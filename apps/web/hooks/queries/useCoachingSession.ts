import { useQuery } from "@tanstack/react-query";
import { coachingApi } from "@/lib/api/coaching.api";

/**
 * useCoachingSessions — lists all coaching sessions for the current user.
 */
export const useCoachingSessions = () => {
    return useQuery({
        queryKey: ["coaching", "sessions"],
        queryFn: () => coachingApi.getSessions(),
        staleTime: 2 * 60 * 1000,
    });
};

/**
 * useCoachingSession — fetches a single coaching session with messages.
 */
export const useCoachingSession = (id: string | null) => {
    return useQuery({
        queryKey: ["coaching", "session", id],
        queryFn: () =>
            id ? coachingApi.getSession(id) : Promise.reject("No session ID"),
        enabled: !!id,
        staleTime: 30 * 1000,   // 30s — coaching sessions update frequently
    });
};
