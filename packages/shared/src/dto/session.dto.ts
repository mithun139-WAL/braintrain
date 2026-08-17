import { Difficulty } from "../enums/difficulty.enum";
import { InterviewType } from "../enums/interview-type.enum";
import { InterviewMode } from "../enums/interview-mode.enum";

export interface CreateSessionDto {
    topicId: string;
    interviewType: InterviewType;
    interviewMode: InterviewMode;
    difficulty: Difficulty;
    adaptive: boolean;
    durationMinutes: number;
    isVoice?: boolean;
    interviewCategory?: "GENERAL" | "CODING" | "DSA" | "SYSTEM_DESIGN";
}

export interface SubmitAnswerDto {
    questionId: string;
    answerText?: string;
    audioUrl?: string;
    responseTimeSeconds?: number;
}
