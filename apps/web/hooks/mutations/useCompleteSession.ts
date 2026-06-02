import { useMutation, useQueryClient } from "@tanstack/react-query";
import { sessionsApi } from "@/lib/api/sessions.api";

/**
 * useCompleteSession — transitions a session from ACTIVE → COMPLETED.
 *
 * This must be called before triggering evaluation.
 * The backend atomically creates an EvaluationJob (PENDING) on completion.
 */
export const useCompleteSession = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (sessionId: string) => sessionsApi.complete(sessionId),
        onSuccess: (_, sessionId) => {
            // Invalidate session cache so status refreshes
            queryClient.invalidateQueries({ queryKey: ["session", sessionId] });
            queryClient.invalidateQueries({ queryKey: ["sessions"] });
        },
    });
};
