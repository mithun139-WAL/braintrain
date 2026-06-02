import { useMutation } from "@tanstack/react-query";
import { identityApi } from "@/lib/api/identity.api";
import { LoginDto, ApiResponse, User } from "@braintrain/shared";

export const useLoginMutation = () => {
    return useMutation({
        mutationFn: (data: LoginDto) => identityApi.login(data),
    });
};
