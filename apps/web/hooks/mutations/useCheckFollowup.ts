import { useMutation } from "@tanstack/react-query";
import { responsesApi, type FollowupExchange, type FollowupResponse } from "@/lib/api/responses.api";

interface CheckFollowupParams {
    questionId: string;
    responseId: string;
    priorExchanges: FollowupExchange[];
}

export const useCheckFollowup = () => {
    return useMutation<FollowupResponse, Error, CheckFollowupParams>({
        mutationFn: ({ questionId, responseId, priorExchanges }) =>
            responsesApi.checkFollowup(questionId, responseId, priorExchanges),
    });
};
