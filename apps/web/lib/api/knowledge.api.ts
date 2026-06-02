import { apiClient } from "./client";

export interface AgentPersona {
    id?: string;
    name: string;
    archetype: string;
    pacingSpeed: number;
    interruptionFrequency: number;
    silenceTolerance: number;
    skepticismLevel: number;
    technicalDepth: number;
    followupAggressiveness: number;
    verbosityTolerance: number;
    ambiguityTolerance: number;
    pressureIntensity: number;
    conversationalWarmth: number;
    challengeEscalation: string;
    acknowledgmentPatterns: string[];
    customPrompts: Record<string, string>;
    createdAt?: string;
    updatedAt?: string;
}

export interface KnowledgeDocument {
    id?: string;
    title: string;
    source: string;
    sourceType: string;
    domain: string;
    topic: string;
    difficulty: string;
    content: string;
    metaData: Record<string, any>;
    chunkCount?: number;
    tokenCount?: number;
    createdAt?: string;
    updatedAt?: string;
}

export interface ApiResponse<T> {
    success: boolean;
    data: T;
}

export const knowledgeApi = {
    listPersonas: async () => {
        const response = await apiClient.get<ApiResponse<AgentPersona[]>>("/knowledge/personas");
        return response.data.data;
    },
    getPersona: async (name: string) => {
        const response = await apiClient.get<ApiResponse<AgentPersona>>(`/knowledge/personas/${name}`);
        return response.data.data;
    },
    createPersona: async (data: AgentPersona) => {
        const response = await apiClient.post<ApiResponse<AgentPersona>>("/knowledge/personas", data);
        return response.data.data;
    },
    updatePersona: async (name: string, data: Partial<AgentPersona>) => {
        const response = await apiClient.put<ApiResponse<AgentPersona>>(`/knowledge/personas/${name}`, data);
        return response.data.data;
    },
    deletePersona: async (name: string) => {
        await apiClient.delete(`/knowledge/personas/${name}`);
    },
    listDocuments: async () => {
        const response = await apiClient.get<ApiResponse<KnowledgeDocument[]>>("/knowledge/documents");
        return response.data.data;
    },
    getDocument: async (id: string) => {
        const response = await apiClient.get<ApiResponse<KnowledgeDocument>>(`/knowledge/documents/${id}`);
        return response.data.data;
    },
    createDocument: async (data: KnowledgeDocument) => {
        const response = await apiClient.post<ApiResponse<KnowledgeDocument>>("/knowledge/documents", data);
        return response.data.data;
    },
    updateDocument: async (id: string, data: Partial<KnowledgeDocument>) => {
        const response = await apiClient.put<ApiResponse<KnowledgeDocument>>(`/knowledge/documents/${id}`, data);
        return response.data.data;
    },
    deleteDocument: async (id: string) => {
        await apiClient.delete(`/knowledge/documents/${id}`);
    },
    analyzeJob: async (data: JobAnalysisRequest) => {
        const response = await apiClient.post<ApiResponse<JobAnalysisResponse>>("/knowledge/analyze-job", data);
        return response.data.data;
    },
    optimizeProfile: async (
        currentRole: string,
        targetRole: string,
        resume?: File | null,
        linkedinPdf?: File | null,
        naukriPdf?: File | null
    ) => {
        const formData = new FormData();
        formData.append("current_role", currentRole);
        formData.append("target_role", targetRole);
        if (resume) formData.append("resume", resume);
        if (linkedinPdf) formData.append("linkedin_pdf", linkedinPdf);
        if (naukriPdf) formData.append("naukri_pdf", naukriPdf);
        
        const response = await apiClient.post<ApiResponse<CareerProfileResponse>>(
            "/knowledge/career-optimize",
            formData,
            {
                headers: {
                    "Content-Type": "multipart/form-data",
                },
            }
        );
        return response.data.data;
    },
    listOptimizationHistory: async () => {
        const response = await apiClient.get<ApiResponse<CareerProfileResponse[]>>("/knowledge/career-optimize/history");
        return response.data.data;
    },
    getOptimizationDetail: async (id: string) => {
        const response = await apiClient.get<ApiResponse<CareerProfileResponse>>(`/knowledge/career-optimize/${id}`);
        return response.data.data;
    },
    deleteOptimization: async (id: string) => {
        await apiClient.delete(`/knowledge/career-optimize/${id}`);
    }
};

export interface CareerProfileResponse {
    id: string;
    userId: string;
    currentRole: string;
    targetRole: string;
    resumeFilename?: string;
    resumeContent?: string;
    linkedinFilename?: string;
    linkedinContent?: string;
    naukriFilename?: string;
    naukriContent?: string;
    extractedData?: {
        experience?: Array<{ title: string; company: string; details: string[] }>;
        skills?: string[];
        projects?: Array<{ name: string; details: string[] }>;
        education?: Array<{ text: string }>;
        certifications?: string[];
        headlines?: string[];
        summaries?: string[];
        technologies?: string[];
        careerProgression?: string;
    };
    analysisResult?: {
        scores?: {
            careerScore: number;
            roleAlignmentScore: number;
            marketReadinessScore: number;
            recruiterVisibilityScore: number;
        };
        gapAnalysis?: {
            missingSkills: string[];
            missingKeywords: string[];
            weakPositioning: string[];
            missingProjects: string[];
            missingCertifications: string[];
            missingProof?: string[];
            weakHeadlines: string[];
            weakSummaries: string[];
        };
        roadmap?: {
            high: string[];
            medium: string[];
            low: string[];
        };
        generatedContent?: {
            linkedinHeadlines: string[];
            linkedinAbout?: {
                professional: string;
                story: string;
                recruiter: string;
            };
            resumeSummary?: string;
            naukriHeadline?: string;
            naukriSummary?: string;
            skillsSuggestions?: {
                alreadyPresent: string[];
                missingSkills: string[];
                recommendedSkills: string[];
            };
        };
    };
    createdAt: string;
    updatedAt: string;
}


export interface JobAnalysisRequest {
    roleTitle: string;
    jobDescription: string;
}

export interface SimilarRoleInfo {
    id: string;
    roleTitle: string;
    companyName?: string;
}

export interface JobAnalysisResponse {
    inputRoleTitle: string;
    commonSkills: string[];
    uniqueSkills: string[];
    similarRolesCompared: SimilarRoleInfo[];
}

