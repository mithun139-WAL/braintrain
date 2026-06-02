import { useEffect, useRef } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { billingApi } from "@/lib/api/billing.api";

export function useBillingStatus() {
    const queryClient = useQueryClient();
    const query = useQuery({
        queryKey: ["billing", "status"],
        queryFn: () => billingApi.getStatus(),
        staleTime: 60 * 1000,
    });

    // GET /billing/status calls Stripe live and writes the reconciled plan_type back
    // to the DB before responding. GET /identity/me is a pure DB read and may be
    // stale relative to that. Invalidate the profile cache whenever a new billing
    // status fetch completes so that session counts, credits, and plan_type in the
    // profile all reflect the post-reconciliation DB state.
    const lastUpdatedAtRef = useRef<number>(0);
    useEffect(() => {
        if (query.dataUpdatedAt && query.dataUpdatedAt !== lastUpdatedAtRef.current) {
            lastUpdatedAtRef.current = query.dataUpdatedAt;
            queryClient.invalidateQueries({ queryKey: ["profile"] });
        }
    }, [query.dataUpdatedAt, queryClient]);

    return query;
}
