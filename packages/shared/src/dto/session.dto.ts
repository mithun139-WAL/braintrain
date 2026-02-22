import { Difficulty } from "../enums/difficulty.enum";
import { InterviewLevel } from "../enums/interview-level.enum";

export interface CreateSessionDto {
    topicId?: string;
    title?: string;
    difficulty?: Difficulty;
    adaptive?: boolean;
    interviewLevel?: InterviewLevel;
}

export interface SubmitAnswerDto {
    questionId: string;
    answerText?: string;
    audioUrl?: string;
    responseTimeSeconds?: number;
}
