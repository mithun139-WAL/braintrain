import { useMutation, useQueryClient } from "@tanstack/react-query";
import { coachingApi } from "@/lib/api/coaching.api";
import { CreateCoachingSessionRequest } from "@braintrain/shared";

/**
 * useSendCoachMessage — sends a user message and receives an AI coaching response.
 *
 * The AI coach:
 *   - Analyzes the communication quality of the message
 *   - Detects patterns (filler words, confidence, structure)
 *   - Responds as a behavioral psychologist + communication expert
 *   - Provides specific, actionable feedback (never generic)
 *
 * Accepts { sessionId, content } at mutate time so the same hook instance
 * can be reused across dynamically-changing session IDs.
 */
export const useSendCoachMessage = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ sessionId, content }: { sessionId: string; content: string }) =>
            coachingApi.sendMessage(sessionId, content),
        onSuccess: (_data, { sessionId }) => {
            // Refresh the coaching session to show new messages
            queryClient.invalidateQueries({ queryKey: ["coaching", "session", sessionId] });
        },
    });
};

/**
 * useCreateCoachingSession — creates a new coaching session for a focus area.
 */
export const useCreateCoachingSession = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: CreateCoachingSessionRequest) => coachingApi.createSession(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["coaching", "sessions"] });
        },
    });
};
