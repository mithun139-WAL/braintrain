import { apiClient } from "./client";
import { ApiResponse, TopicDto, CreateTopicDto } from "@braintrain/shared";

export const topicsApi = {
    list: async () => {
        const response = await apiClient.get<ApiResponse<TopicDto[]>>("/topics");
        return response.data;
    },
    getById: async (id: string) => {
        const response = await apiClient.get<ApiResponse<TopicDto>>(`/topics/${id}`);
        return response.data;
    },
    create: async (dto: CreateTopicDto) => {
        const response = await apiClient.post<ApiResponse<TopicDto>>("/topics", dto);
        return response.data;
    },
    delete: async (id: string) => {
        const response = await apiClient.delete<ApiResponse<{ message: string }>>(`/topics/${id}`);
        return response.data;
    }
};

