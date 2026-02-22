export interface User {
    id: string;
    email: string;
    name?: string;
    displayName?: string | null;
    avatarUrl?: string | null;
    bio?: string | null;
    planType?: string;
    monthlySessionCount?: number;
    monthlyEvaluationCredits?: number;
    skills?: string[];
    createdAt: string;
    updatedAt?: string;
    usagePeriodStart?: string;
}
