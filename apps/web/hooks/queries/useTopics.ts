import { useQuery } from "@tanstack/react-query";
import { topicsApi } from "@/lib/api/topics.api";

export const useTopics = () => {
    return useQuery({
        queryKey: ["topics"],
        queryFn: topicsApi.list
    });
};
