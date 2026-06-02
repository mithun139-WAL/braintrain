import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { knowledgeApi, AgentPersona, KnowledgeDocument } from "@/lib/api/knowledge.api";

export const usePersonas = () => {
    return useQuery({
        queryKey: ["knowledge", "personas"],
        queryFn: () => knowledgeApi.listPersonas(),
    });
};

export const usePersona = (name: string) => {
    return useQuery({
        queryKey: ["knowledge", "personas", name],
        queryFn: () => knowledgeApi.getPersona(name),
        enabled: !!name,
    });
};

export const useDocuments = () => {
    return useQuery({
        queryKey: ["knowledge", "documents"],
        queryFn: () => knowledgeApi.listDocuments(),
    });
};

export const useDocument = (id: string) => {
    return useQuery({
        queryKey: ["knowledge", "documents", id],
        queryFn: () => knowledgeApi.getDocument(id),
        enabled: !!id,
    });
};

export const usePersonaMutations = () => {
    const queryClient = useQueryClient();

    const createMutation = useMutation({
        mutationFn: (data: AgentPersona) => knowledgeApi.createPersona(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["knowledge", "personas"] });
        },
    });

    const updateMutation = useMutation({
        mutationFn: ({ name, data }: { name: string; data: Partial<AgentPersona> }) =>
            knowledgeApi.updatePersona(name, data),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ["knowledge", "personas"] });
            queryClient.invalidateQueries({ queryKey: ["knowledge", "personas", variables.name] });
        },
    });

    const deleteMutation = useMutation({
        mutationFn: (name: string) => knowledgeApi.deletePersona(name),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["knowledge", "personas"] });
        },
    });

    return { createMutation, updateMutation, deleteMutation };
};

export const useDocumentMutations = () => {
    const queryClient = useQueryClient();

    const createMutation = useMutation({
        mutationFn: (data: KnowledgeDocument) => knowledgeApi.createDocument(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["knowledge", "documents"] });
        },
    });

    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: string; data: Partial<KnowledgeDocument> }) =>
            knowledgeApi.updateDocument(id, data),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ["knowledge", "documents"] });
            queryClient.invalidateQueries({ queryKey: ["knowledge", "documents", variables.id] });
        },
    });

    const deleteMutation = useMutation({
        mutationFn: (id: string) => knowledgeApi.deleteDocument(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["knowledge", "documents"] });
        },
    });

    return { createMutation, updateMutation, deleteMutation };
};

export const useJobAnalysisMutation = () => {
    return useMutation({
        mutationFn: (data: { roleTitle: string; jobDescription: string }) =>
            knowledgeApi.analyzeJob(data),
    });
};

export const useOptimizationHistory = () => {
    return useQuery({
        queryKey: ["knowledge", "career-optimizations"],
        queryFn: () => knowledgeApi.listOptimizationHistory(),
    });
};

export const useOptimizationDetail = (id: string) => {
    return useQuery({
        queryKey: ["knowledge", "career-optimizations", id],
        queryFn: () => knowledgeApi.getOptimizationDetail(id),
        enabled: !!id,
    });
};

export const useOptimizeProfileMutation = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (data: {
            currentRole: string;
            targetRole: string;
            resume?: File | null;
            linkedinPdf?: File | null;
            naukriPdf?: File | null;
        }) =>
            knowledgeApi.optimizeProfile(
                data.currentRole,
                data.targetRole,
                data.resume,
                data.linkedinPdf,
                data.naukriPdf
            ),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["knowledge", "career-optimizations"] });
        },
    });
};

export const useDeleteOptimizationMutation = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (id: string) => knowledgeApi.deleteOptimization(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["knowledge", "career-optimizations"] });
        },
    });
};


