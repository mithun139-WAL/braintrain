import { useMutation, useQueryClient } from "@tanstack/react-query";
import { questionsApi } from "@/lib/api/questions.api";

export const useGenerateQuestion = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (sessionId: string) => questionsApi.generateNext(sessionId),
        onSuccess: (_, sessionId) => {
            queryClient.invalidateQueries({ queryKey: ["session", sessionId] });
        }
    });
};
