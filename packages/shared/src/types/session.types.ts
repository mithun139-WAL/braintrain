import { Difficulty } from "../enums/difficulty.enum";
import { SessionStatus } from "../enums/session-status.enum";
import { InterviewLevel } from "../enums/interview-level.enum";

export interface Session {
    id: string;
    topicId: string;
    difficulty: Difficulty;
    interviewLevel: InterviewLevel;
    status: SessionStatus;
    createdAt: string;
    completedAt?: string;
}
