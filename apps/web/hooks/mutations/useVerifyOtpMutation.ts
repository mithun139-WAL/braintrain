import { useMutation } from "@tanstack/react-query";
import { identityApi } from "@/lib/api/identity.api";
import { VerifyOtpDto } from "@braintrain/shared";

export const useVerifyOtpMutation = () => {
    return useMutation({
        mutationFn: (data: VerifyOtpDto) => identityApi.verifyOtp(data),
    });
};
