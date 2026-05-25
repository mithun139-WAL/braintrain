import { Difficulty } from "../enums/difficulty.enum";
import { SessionStatus } from "../enums/session-status.enum";
import { InterviewType } from "../enums/interview-type.enum";
import { InterviewMode } from "../enums/interview-mode.enum";

export interface Session {
    id: string;
    topicId: string;
    topicName?: string;
    difficulty: Difficulty;
    interviewType: InterviewType;
    interviewMode: InterviewMode;
    status: SessionStatus;
    createdAt: string;
    completedAt?: string;
    questions: any[];
    adaptive?: boolean;
    durationMinutes: number;
    isVoice?: boolean;
    personalityConfig?: Record<string, unknown>;
}
