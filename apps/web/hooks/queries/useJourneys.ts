import { useQuery } from "@tanstack/react-query";
import { journeysApi } from "@/lib/api/journeys.api";

export const useJourneys = (page: number = 1, limit: number = 20) => {
    return useQuery({
        queryKey: ["journeys", page, limit],
        queryFn: () => journeysApi.list({ page, limit }),
    });
};

export const useJourney = (id: string | null) => {
    return useQuery({
        queryKey: ["journey", id],
        queryFn: () => (id ? journeysApi.getById(id) : Promise.reject("No journey ID")),
        enabled: !!id,
    });
};

export const useJourneyAnalysis = (journeyId: string | null) => {
    return useQuery({
        queryKey: ["journey-analysis", journeyId],
        queryFn: () => (journeyId ? journeysApi.analyze(journeyId) : Promise.reject("No journey ID")),
        enabled: !!journeyId,
    });
};

export const useJourneyRounds = (journeyId: string | null) => {
    return useQuery({
        queryKey: ["journey-rounds", journeyId],
        queryFn: () => (journeyId ? journeysApi.getRounds(journeyId) : Promise.reject("No journey ID")),
        enabled: !!journeyId,
    });
};

export const useJourneyFinalReport = (journeyId: string | null) => {
    return useQuery({
        queryKey: ["journey-final-report", journeyId],
        queryFn: () => (journeyId ? journeysApi.getFinalReport(journeyId) : Promise.reject("No journey ID")),
        enabled: !!journeyId,
    });
};
