import { DifficultyLevel } from '@prisma/client';

export interface QuestionGenerationInput {
    topicName: string;
    topicId: string;
    difficulty: DifficultyLevel;
    questionType: 'behavioral' | 'technical';
    /** Already-asked question contents in this session (to avoid duplicates) */
    existingQuestions?: string[];
}

export interface GeneratedQuestion {
    questionText: string;
    expectedAnswerTraits: string[];
    estimatedDifficulty: DifficultyLevel;
}

export interface QuestionGenerationProvider {
    generate(input: QuestionGenerationInput): Promise<GeneratedQuestion>;
}
