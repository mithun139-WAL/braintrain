import { useMutation, useQueryClient } from "@tanstack/react-query";
import { questionsApi } from "@/lib/api/questions.api";

export const useSubmitResponse = (sessionId: string) => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ questionId, answerText }: { questionId: string, answerText: string }) =>
            questionsApi.submitResponse(questionId, answerText),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["session", sessionId] });
        }
    });
};
