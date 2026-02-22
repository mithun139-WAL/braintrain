import { DifficultyLevel } from '@prisma/client';

export interface EvaluationInput {
    /** Plain text answer from the user */
    text?: string;
    /** URL to the recorded audio response */
    audioUrl?: string;
    /** The original question asked */
    question: string;
    /** behavioral | technical — drives scoring weights */
    questionType: 'behavioral' | 'technical';
    /** Session difficulty at time of question */
    difficulty: DifficultyLevel;
    /** Total time from question display to response submission (ms) */
    responseTimeMs?: number;
    /** Pause duration before the candidate started answering (ms) */
    thinkingTimeMs?: number;
}
