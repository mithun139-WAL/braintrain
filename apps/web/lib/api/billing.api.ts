import { apiClient } from "./client";
import { ApiResponse } from "@braintrain/shared";

export interface BillingRedirectResponse {
    url: string;
}

export interface BillingStatusResponse {
    configured: boolean;
    hasActiveSubscription: boolean;
    planType: string;
    subscriptionStatus?: string | null;
}

export const billingApi = {
    getStatus: async (): Promise<ApiResponse<BillingStatusResponse>> => {
        const response = await apiClient.get<ApiResponse<BillingStatusResponse>>("/billing/status");
        return response.data;
    },

    createCheckoutSession: async (): Promise<ApiResponse<BillingRedirectResponse>> => {
        const response = await apiClient.post<ApiResponse<BillingRedirectResponse>>("/billing/checkout");
        return response.data;
    },

    createPortalSession: async (): Promise<ApiResponse<BillingRedirectResponse>> => {
        const response = await apiClient.post<ApiResponse<BillingRedirectResponse>>("/billing/portal");
        return response.data;
    },
};
