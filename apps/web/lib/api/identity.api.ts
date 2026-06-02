import { apiClient } from "./client";
import { LoginDto, RegisterDto, ApiResponse, User, RequestOtpDto, VerifyOtpDto, GoogleLoginDto, UpdateProfileDto, SkillTag, AddSkillPreferenceDto } from "@braintrain/shared";

export const identityApi = {
    login: async (data: LoginDto) => {
        const response = await apiClient.post<ApiResponse<{ accessToken: string; user: User }>>("/identity/login", data);
        return response.data;
    },

    register: async (data: RegisterDto) => {
        const response = await apiClient.post<ApiResponse<{ message: string }>>("/identity/register", data);
        return response.data;
    },

    confirmEmail: async (token: string) => {
        const response = await apiClient.post<ApiResponse<{ accessToken: string; user: User }>>("/identity/confirm-email", { token });
        return response.data;
    },

    resendConfirmation: async (email: string) => {
        const response = await apiClient.post<ApiResponse<{ message: string }>>("/identity/resend-confirmation", { email });
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

    requestOtp: async (data: RequestOtpDto) => {
        const response = await apiClient.post<ApiResponse<void>>("/identity/request-otp", data);
        return response.data;
    },

    verifyOtp: async (data: VerifyOtpDto) => {
        const response = await apiClient.post<ApiResponse<{ accessToken: string; user: User }>>("/identity/verify-otp", data);
        return response.data;
    },

    googleLogin: async (data: GoogleLoginDto) => {
        const response = await apiClient.post<ApiResponse<{ accessToken: string; user: User }>>("/identity/google", data);
        return response.data;
    },
    updateProfile: async (data: UpdateProfileDto) => {
        const response = await apiClient.put<ApiResponse<User>>("/identity/me", data);
        return response.data;
    },
    getSkillTags: async () => {
        const response = await apiClient.get<ApiResponse<SkillTag[]>>("/identity/skill-tags");
        return response.data;
    },
    addSkillPreference: async (data: AddSkillPreferenceDto) => {
        const response = await apiClient.post<ApiResponse<any>>("/identity/me/skills", data);
        return response.data;
    },
    removeSkillPreference: async (skillTagId: string) => {
        const response = await apiClient.delete<ApiResponse<any>>(`/identity/me/skills/${skillTagId}`);
        return response.data;
    }
};
