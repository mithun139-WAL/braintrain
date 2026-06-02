import { useQuery } from "@tanstack/react-query";
import { sessionsApi } from "@/lib/api/sessions.api";

export const useSession = (id: string | null) => {
    return useQuery({
        queryKey: ["session", id],
        queryFn: () => (id ? sessionsApi.getById(id) : Promise.reject("No session ID")),
        enabled: !!id,
    });
};
