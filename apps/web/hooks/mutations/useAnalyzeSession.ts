import { useMutation, useQueryClient } from "@tanstack/react-query";
import { evaluationApi } from "@/lib/api/evaluation.api";

/**
 * useAnalyzeSession — triggers AI evaluation for a COMPLETED session.
 *
 * Pipeline:
 *   1. Transcribes audio responses (Whisper) if any
 *   2. Evaluates all responses with GPT-4o-mini
 *   3. Aggregates scores into an EvaluationReport
 *   4. Transitions session to ANALYZED
 *
 * This is idempotent — calling twice returns the existing report (409 guard).
 * PRO users with credits get real AI; FREE users get stub scores.
 */
export const useAnalyzeSession = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (sessionId: string) => evaluationApi.analyzeSession(sessionId),
        onSuccess: (data, sessionId) => {
            // Cache the evaluation report immediately
            queryClient.setQueryData(["evaluation", sessionId], data);
            // Refresh session status (now ANALYZED)
            queryClient.invalidateQueries({ queryKey: ["session", sessionId] });
            queryClient.invalidateQueries({ queryKey: ["sessions"] });
            // Invalidate analytics so the dashboard reflects the new session
            queryClient.invalidateQueries({ queryKey: ["analytics"] });
        },
    });
};
