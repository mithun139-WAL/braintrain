// Coaching types — AI Communication Coach module
// All fields camelCase (converted from snake_case by axios interceptor)

export type CoachingFocusArea =
    | "confidence"
    | "storytelling"
    | "technical_explanation"
    | "leadership_communication"
    | "public_speaking"
    | "interview_skills"
    | "persuasion"
    | "emotional_expression"
    | "clarity"
    | "general";

export type CoachingSessionStatus = "ACTIVE" | "ENDED";
export type MessageRole = "user" | "assistant";

export interface CoachingMessageAnalysis {
    fillerWordCount?: number;
    confidenceScore?: number;
    clarityScore?: number;
    keyInsight?: string;
    improvementSuggestion?: string;
}

export interface CoachingMessage {
    id: string;
    role: MessageRole;
    content: string;
    analysis?: CoachingMessageAnalysis;
    createdAt: string;
}

export interface CoachingSession {
    id: string;
    userId: string;
    title?: string;                     // not returned by backend — optional for compat
    interviewSessionId?: string;
    focusArea: CoachingFocusArea;
    status: CoachingSessionStatus;
    messageCount: number;               // computed by backend (_build_session_response)
    startedAt: string;
    endedAt?: string;
    createdAt: string;
    updatedAt: string;
    messages?: CoachingMessage[];
}

export interface SendMessageRequest {
    content: string;
}

export interface SendMessageResponse {
    userMessage: CoachingMessage;
    assistantMessage: CoachingMessage;
    sessionInsights?: {
        patternsDetected: string[];
        overallProgress: string;
    };
}

export interface CreateCoachingSessionRequest {
    focusArea: CoachingFocusArea;
    title?: string;
    context?: string;               // optional user-provided context
}
