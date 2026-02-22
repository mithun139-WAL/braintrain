import { useMutation } from "@tanstack/react-query";
import { identityApi } from "@/lib/api/identity.api";
import { RegisterDto } from "@braintrain/shared";

export const useRegisterMutation = () => {
    return useMutation({
        mutationFn: (data: RegisterDto) => identityApi.register(data),
    });
};
