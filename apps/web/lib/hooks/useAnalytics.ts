"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "../api/analytics.api";
// import { TrendDataPointDto } from "@braintrain/shared";

export function useAnalyticsTrends() {
    return useQuery({
        queryKey: ["analytics", "trends"],
        queryFn: () => analyticsApi.getAnalytics(),
    });
}
