import { useQuery } from "@tanstack/react-query";
import { billingApi } from "@/lib/api/billing.api";

export function useBillingStatus() {
    return useQuery({
        queryKey: ["billing", "status"],
        queryFn: () => billingApi.getStatus(),
        staleTime: 60 * 1000,
    });
}
