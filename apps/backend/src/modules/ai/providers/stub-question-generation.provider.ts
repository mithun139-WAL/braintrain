import { Injectable } from '@nestjs/common';
import { DifficultyLevel } from '@prisma/client';
import {
    QuestionGenerationProvider,
    QuestionGenerationInput,
    GeneratedQuestion,
} from '../interfaces/question-generation-provider.interface';

@Injectable()
export class StubQuestionGenerationProvider implements QuestionGenerationProvider {
    async generate(input: QuestionGenerationInput): Promise<GeneratedQuestion> {
        const questionText =
            `Explain the core concepts of ${input.topicName} at the ` +
            `${input.difficulty.toLowerCase()} level, including real-world applications.`;

        return {
            questionText,
            expectedAnswerTraits: [
                'Clear explanation of core concept',
                'Practical examples or use cases',
                'Awareness of trade-offs or limitations',
            ],
            estimatedDifficulty: input.difficulty as DifficultyLevel,
        };
    }
}
