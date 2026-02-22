import { useQuery } from "@tanstack/react-query";
import { identityApi } from "@/lib/api/identity.api";

export function useGetSkillTags() {
    return useQuery({
        queryKey: ["skill-tags"],
        queryFn: () => identityApi.getSkillTags(),
        staleTime: 10 * 60 * 1000, // 10 minutes
    });
}
