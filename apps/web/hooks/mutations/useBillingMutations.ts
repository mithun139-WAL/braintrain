import { useMutation, useQueryClient } from "@tanstack/react-query";
import { billingApi } from "@/lib/api/billing.api";

function getErrorMessage(error: unknown) {
    if (typeof error === "string") return error;
    if (error instanceof Error) return error.message;
    return "Billing action failed";
}

function redirectTo(url?: string) {
    if (!url || typeof window === "undefined") return;
    window.location.href = url;
}

export function useStartCheckout() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: () => billingApi.createCheckoutSession(),
        onSuccess: (response) => {
            queryClient.invalidateQueries({ queryKey: ["profile"] });
            queryClient.invalidateQueries({ queryKey: ["billing", "status"] });
            redirectTo(response.data.url);
        },
        onError: (error: unknown) => {
            alert(getErrorMessage(error));
        },
    });
}

export function useOpenBillingPortal() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: () => billingApi.createPortalSession(),
        onSuccess: (response) => {
            queryClient.invalidateQueries({ queryKey: ["profile"] });
            queryClient.invalidateQueries({ queryKey: ["billing", "status"] });
            redirectTo(response.data.url);
        },
        onError: (error: unknown) => {
            alert(getErrorMessage(error));
        },
    });
}
