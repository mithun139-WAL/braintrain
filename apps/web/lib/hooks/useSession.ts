"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { sessionsApi } from "../api/sessions.api";
import { questionsApi } from "../api/questions.api";
import { SubmitAnswerDto } from "@braintrain/shared";

// Polls the status of the session. Automatically stops polling if completed.
export const useSessionStatus = (sessionId: string) => {
    return useQuery({
        queryKey: ["session-status", sessionId],
        queryFn: () => sessionsApi.getStatus(sessionId),
        refetchInterval: (query) =>
            (query.state.data?.data?.status === "COMPLETED" ? false : 3000),
        enabled: !!sessionId
    });
};

export const useSession = (sessionId: string) => {
    const queryClient = useQueryClient();

    // Fetch static session detail
    const { data: session, isLoading, error } = useQuery({
        queryKey: ["session", sessionId],
        queryFn: () => sessionsApi.getById(sessionId),
        enabled: !!sessionId
    });

    // Mutate for submitting an answer
    const submitAnswerMutation = useMutation({
        mutationFn: (payload: SubmitAnswerDto) =>
            questionsApi.submitResponse(payload.questionId, payload.answerText ?? ""),
        onSuccess: () => {
            // Re-fetch session context to get the next step in the interview
            queryClient.invalidateQueries({ queryKey: ["session", sessionId] });
        },
    });

    // Mutate for completing the interview early / naturally
    const completeSessionMutation = useMutation({
        mutationFn: () => sessionsApi.complete(sessionId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["session", sessionId] });
            queryClient.invalidateQueries({ queryKey: ["session-status", sessionId] });
        }
    });

    return {
        session,
        isLoading,
        error,
        submitAnswer: submitAnswerMutation.mutateAsync,
        isSubmitting: submitAnswerMutation.isPending,
        completeSession: completeSessionMutation.mutateAsync,
        isCompleting: completeSessionMutation.isPending
    };
};
