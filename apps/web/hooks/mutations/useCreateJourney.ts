import { useMutation, useQueryClient } from "@tanstack/react-query";
import { journeysApi, type CreateJourneyDto } from "@/lib/api/journeys.api";
import { useRouter } from "next/navigation";

export const useCreateJourney = () => {
    const queryClient = useQueryClient();
    const router = useRouter();

    return useMutation({
        mutationFn: (data: CreateJourneyDto) => journeysApi.create(data),
        onSuccess: (response) => {
            queryClient.invalidateQueries({ queryKey: ["journeys"] });
            const journeyId = response.data?.id;
            if (journeyId) {
                router.push(`/dashboard/interview-journey/${journeyId}/analysis`);
            }
        },
        onError: (error: unknown) => {
            const message =
                typeof error === "string"
                    ? error
                    : error instanceof Error
                    ? error.message
                    : "Failed to create journey";
            alert(message);
        },
    });
};

export const useUploadResume = () => {
    return useMutation({
        mutationFn: (file: File) => journeysApi.uploadResume(file),
    });
};

export const useAnalyzeJourney = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (journeyId: string) => journeysApi.analyze(journeyId),
        onSuccess: (response, journeyId) => {
            queryClient.invalidateQueries({ queryKey: ["journey", journeyId] });
            queryClient.invalidateQueries({ queryKey: ["journey-analysis", journeyId] });
            queryClient.invalidateQueries({ queryKey: ["journey-rounds", journeyId] });
        },
    });
};

export const useStartRound = () => {
    return useMutation({
        mutationFn: ({ journeyId, roundIndex }: { journeyId: string; roundIndex: number }) =>
            journeysApi.startRound(journeyId, roundIndex),
    });
};

export const useCompleteRound = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            journeyId,
            journeySessionId,
            interviewSessionId,
        }: {
            journeyId: string;
            journeySessionId: string;
            interviewSessionId: string;
        }) => journeysApi.completeRound(journeyId, journeySessionId, interviewSessionId),
        onSuccess: (_, { journeyId }) => {
            queryClient.invalidateQueries({ queryKey: ["journey", journeyId] });
            queryClient.invalidateQueries({ queryKey: ["journey-rounds", journeyId] });
        },
    });
};

export const useEditJourney = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ journeyId, data }: { journeyId: string; data: Partial<CreateJourneyDto> }) =>
            journeysApi.edit(journeyId, data),
        onSuccess: (response) => {
            queryClient.invalidateQueries({ queryKey: ["journeys"] });
            const journeyId = response.data?.id;
            if (journeyId) {
                queryClient.invalidateQueries({ queryKey: ["journey", journeyId] });
            }
        },
    });
};

export const useDeleteJourney = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (journeyId: string) => journeysApi.delete(journeyId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["journeys"] });
        },
    });
};

