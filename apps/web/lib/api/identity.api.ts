import { apiClient } from "./client";
import { LoginDto, RegisterDto, ApiResponse, User } from "@braintrain/shared";

export const identityApi = {
    login: async (data: LoginDto) => {
        const response = await apiClient.post<ApiResponse<User>>("/identity/login", data);
        return response.data;
    },

    register: async (data: RegisterDto) => {
        const response = await apiClient.post<ApiResponse<User>>("/identity/register", data);
        return response.data;
    },

    logout: async () => {
        const response = await apiClient.post<ApiResponse<void>>("/identity/logout");
        return response.data;
    },

    getCurrentUser: async () => {
        const response = await apiClient.get<ApiResponse<User>>("/identity/me");
        return response.data;
    },

    requestOtp: async (identifier: string) => {
        const response = await apiClient.post<ApiResponse<void>>("/identity/request-otp", { identifier });
        return response.data;
    },

    verifyOtp: async (identifier: string, code: string) => {
        const response = await apiClient.post<ApiResponse<User>>("/identity/verify-otp", { identifier, code });
        return response.data;
    }
};
