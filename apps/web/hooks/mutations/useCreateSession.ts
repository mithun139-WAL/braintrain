import { useMutation, useQueryClient } from "@tanstack/react-query";
import { sessionsApi } from "@/lib/api/sessions.api";
import { CreateSessionDto } from "@braintrain/shared";
import { useRouter } from "next/navigation";

export const useCreateSession = () => {
    const queryClient = useQueryClient();
    const router = useRouter();

    return useMutation({
        mutationFn: (data: CreateSessionDto) => sessionsApi.create(data),
        onSuccess: (response) => {
            queryClient.invalidateQueries({ queryKey: ["sessions"] });
            queryClient.invalidateQueries({ queryKey: ["profile"] });
            router.push(`/dashboard/sessions/${response.data.id}`);
        },
        onError: (error: unknown) => {
            const message =
                typeof error === "string"
                    ? error
                    : error instanceof Error
                    ? error.message
                    : "Failed to create session";

            alert(message);
        }
    });
};
