import type { SkillPreference } from "./skill.types";

export interface User {
    id: string;
    email: string;
    name?: string;
    displayName?: string | null;
    phoneNumber?: string | null;
    googleId?: string | null;
    avatarUrl?: string | null;
    bio?: string | null;
    planType?: string;
    stripeCustomerId?: string | null;
    stripeSubscriptionId?: string | null;
    stripeSubscriptionStatus?: string | null;
    monthlySessionCount?: number;
    monthlyEvaluationCredits?: number;
    voiceSessionCount?: number;
    chatSessionCount?: number;
    voiceSessionLimit?: number;
    chatSessionLimit?: number;
    skills?: string[];
    skillPreferences?: SkillPreference[];
    createdAt: string;
    updatedAt?: string;
    usagePeriodStart?: string;
}
