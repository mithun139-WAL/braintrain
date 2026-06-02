import { useMutation, useQueryClient } from "@tanstack/react-query";
import { identityApi } from "@/lib/api/identity.api";
import { AddSkillPreferenceDto } from "@braintrain/shared";

export function useAddSkillPreference() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: AddSkillPreferenceDto) => identityApi.addSkillPreference(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["profile"] });
        },
    });
}

export function useRemoveSkillPreference() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (skillTagId: string) => identityApi.removeSkillPreference(skillTagId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["profile"] });
        },
    });
}
