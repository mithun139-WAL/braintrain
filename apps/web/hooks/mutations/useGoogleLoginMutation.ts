import { useMutation } from "@tanstack/react-query";
import { identityApi } from "@/lib/api/identity.api";
import { GoogleLoginDto } from "@braintrain/shared";

export const useGoogleLoginMutation = () => {
    return useMutation({
        mutationFn: (data: GoogleLoginDto) => identityApi.googleLogin(data),
    });
};
