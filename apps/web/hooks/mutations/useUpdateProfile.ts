import { useMutation, useQueryClient } from "@tanstack/react-query";
import { identityApi } from "@/lib/api/identity.api";
import { UpdateProfileDto } from "@braintrain/shared";

export function useUpdateProfile() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: UpdateProfileDto) => identityApi.updateProfile(data),
        onSuccess: () => {
            // Invalidate the profile query to refetch the updated data
            queryClient.invalidateQueries({ queryKey: ["profile"] });
        },
    });
}
