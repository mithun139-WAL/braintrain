import { useMutation, useQueryClient } from "@tanstack/react-query";
import { sessionsApi } from "@/lib/api/sessions.api";

export const useStartSession = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (id: string) => sessionsApi.start(id),
        onSuccess: (_, id) => {
            queryClient.invalidateQueries({ queryKey: ["session", id] });
        }
    });
};
