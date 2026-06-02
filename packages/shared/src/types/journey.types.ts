export interface InterviewJourney {
    id: string;
    userId: string;
    companyName?: string | null;
    roleTitle: string;
    status: string;
    candidateLevel?: string | null;
    roleCategory?: string | null;
    extractedSkills?: Record<string, unknown> | null;
    extractedSignals?: Record<string, unknown> | null;
    generatedPlan?: Record<string, unknown> | null;
    prerequisites?: JourneyPrerequisites | null;
    createdAt: string;
    updatedAt: string;
    sessions: InterviewJourneySession[];
}

export interface InterviewJourneySession {
    id: string;
    roundName: string;
    roundType: string;
    difficulty: string;
    orderIndex: number;
    completed: boolean;
    sessionId?: string | null;
    interviewerPersona?: Record<string, unknown> | null;
    roundFocus?: Record<string, unknown> | null;
    createdAt: string;
}

export interface JourneyAnalysis {
    journeyId: string;
    status: string;
    candidateLevel: string;
    roleCategory: string;
    strengths: string[];
    weaknesses: string[];
    rounds: JourneyRound[];
    verifiedProfile: Record<string, unknown>;
    prerequisites?: JourneyPrerequisites | null;
}

export interface JourneyPrerequisites {
    topics: string[];
    issues: string[];
    minimumCriteria: string[];
}

export interface JourneyRound {
    name: string;
    roundType: string;
    focus: {
        areas: string[];
    };
    difficulty: string;
    estimatedDurationMinutes: number;
    goals: string[];
    strategy?: Record<string, unknown>;
}

export interface StartRoundResult {
    journeySessionId: string;
    journeyId: string;
    roundName: string;
    roundType: string;
    difficulty: string;
    persona?: Record<string, unknown> | null;
    roundFocus?: Record<string, unknown> | null;
    sessionContext: Record<string, unknown>;
    interviewSessionId?: string | null;
}

export interface JourneyFinalReport {
    journeyId: string;
    roleTitle: string;
    companyName?: string | null;
    candidateLevel: string;
    hireRecommendation: string;
    overallHiringSignal: string;
    strongestRound?: string | null;
    weakestRound?: string | null;
    hiringRiskAreas: string[];
    companyFit: string;
    communicationSummary: string;
    technicalSummary: string;
    recruiterNotes: string;
    roundReports: JourneyRoundReport[];
}

export interface JourneyRoundReport {
    roundName: string;
    roundType: string;
    difficulty: string;
    strengths: string[];
    weaknesses: string[];
    missedOpportunities: string[];
    communicationQuality: string;
    technicalGaps: string[];
}
