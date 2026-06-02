import { useMutation } from "@tanstack/react-query";
import { identityApi } from "@/lib/api/identity.api";
import { RequestOtpDto } from "@braintrain/shared";

export const useRequestOtpMutation = () => {
    return useMutation({
        mutationFn: (data: RequestOtpDto) => identityApi.requestOtp(data),
    });
};
