import { useQuery } from "@tanstack/react-query";
import { identityApi } from "@/lib/api/identity.api";

export function useGetProfile() {
    return useQuery({
        queryKey: ["profile"],
        queryFn: () => identityApi.getCurrentUser(),
        staleTime: 5 * 60 * 1000, // 5 minutes
    });
}
