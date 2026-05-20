import { useQuery } from "@tanstack/react-query";
import { evaluationApi } from "@/lib/api/evaluation.api";

/**
 * useEvaluation — fetches an existing evaluation report for a session.
 *
 * Only works for sessions with status = ANALYZED.
 * For sessions that are COMPLETED but not yet analyzed, use useAnalyzeSession.
 */
export const useEvaluation = (sessionId: string | null) => {
    return useQuery({
        queryKey: ["evaluation", sessionId],
        queryFn: () =>
            sessionId
                ? evaluationApi.getReport(sessionId)
                : Promise.reject("No session ID"),
        enabled: !!sessionId,
        staleTime: Infinity,    // evaluation reports never change once created
        retry: false,           // don't retry on 404 (session not yet analyzed)
    });
};
