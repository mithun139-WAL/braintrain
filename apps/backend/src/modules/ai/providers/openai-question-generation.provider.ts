import { Injectable, Logger } from '@nestjs/common';
import { PrismaService } from '../../../prisma/prisma.service';
import { DifficultyLevel } from '@prisma/client';
import OpenAI from 'openai';
import {
    QuestionGenerationProvider,
    QuestionGenerationInput,
    GeneratedQuestion,
} from '../interfaces/question-generation-provider.interface';
import { StubQuestionGenerationProvider } from './stub-question-generation.provider';
import {
    QUESTION_GEN_SYSTEM_PROMPT,
    buildQuestionGenUserPrompt,
} from '../prompts/question-generation.prompts';

@Injectable()
export class OpenAIQuestionGenerationProvider implements QuestionGenerationProvider {
    private readonly logger = new Logger(OpenAIQuestionGenerationProvider.name);
    private readonly client: OpenAI;
    private readonly fallback: StubQuestionGenerationProvider;

    constructor(private readonly prisma: PrismaService) {
        if (!process.env.OPENAI_API_KEY) {
            throw new Error('OPENAI_API_KEY required for OpenAIQuestionGenerationProvider');
        }
        this.client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
        this.fallback = new StubQuestionGenerationProvider();
    }

    async generate(input: QuestionGenerationInput): Promise<GeneratedQuestion> {
        const userPrompt = buildQuestionGenUserPrompt({
            topicName: input.topicName,
            difficulty: input.difficulty,
            questionType: input.questionType,
            existingQuestions: input.existingQuestions,
        });

        try {
            const completion = await this.client.chat.completions.create({
                model: 'gpt-4o',
                response_format: { type: 'json_object' },
                temperature: 0.7,  // Higher creativity for question generation
                messages: [
                    { role: 'system', content: QUESTION_GEN_SYSTEM_PROMPT },
                    { role: 'user', content: userPrompt },
                ],
            });

            const raw = completion.choices[0]?.message?.content ?? '';
            const parsed = this.parseAndValidate(raw, input.difficulty as DifficultyLevel);

            if (!parsed) {
                this.logger.warn(`Malformed question gen response — falling back to stub. Raw: ${raw.slice(0, 200)}`);
                return this.fallback.generate(input);
            }

            // Auto-save generated question to QuestionBank (proprietary dataset flywheel)
            await this.saveToBank(parsed, input);

            this.logger.log(
                `Generated question for topic "${input.topicName}" | Difficulty: ${parsed.estimatedDifficulty}`,
            );

            return parsed;
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : String(err);
            this.logger.error(`OpenAI question gen failed: ${message} — falling back to stub`);
            return this.fallback.generate(input);
        }
    }

    /**
     * Auto-save generated questions to QuestionBank.
     * This builds a proprietary question dataset over time —
     * next time the same topic/difficulty is requested, it comes from the bank (zero AI cost).
     */
    private async saveToBank(
        question: GeneratedQuestion,
        input: QuestionGenerationInput,
    ): Promise<void> {
        try {
            await this.prisma.questionBank.create({
                data: {
                    content: question.questionText,
                    topicId: input.topicId,
                    difficulty: question.estimatedDifficulty,
                    questionType: input.questionType,
                    source: 'GENERATED',       // ← proprietary dataset tagging
                    isGlobal: false,
                    createdByUserId: null,      // system-generated
                },
            });
        } catch (err) {
            // Non-fatal: if it fails (e.g., duplicate), we still return the question
            this.logger.warn(`Failed to auto-save question to bank: ${String(err)}`);
        }
    }

    private parseAndValidate(raw: string, fallbackDifficulty: DifficultyLevel): GeneratedQuestion | null {
        try {
            const parsed = JSON.parse(raw);

            if (typeof parsed.questionText !== 'string' || !parsed.questionText.trim()) {
                return null;
            }

            const traits = Array.isArray(parsed.expectedAnswerTraits)
                ? parsed.expectedAnswerTraits.filter((t: unknown) => typeof t === 'string')
                : ['Structured answer', 'Concrete examples', 'Clear reasoning'];

            const validDifficulties = ['BEGINNER', 'INTERMEDIATE', 'ADVANCED'];
            const estimatedDifficulty: DifficultyLevel = validDifficulties.includes(parsed.estimatedDifficulty)
                ? (parsed.estimatedDifficulty as DifficultyLevel)
                : fallbackDifficulty;

            return {
                questionText: parsed.questionText.trim(),
                expectedAnswerTraits: traits,
                estimatedDifficulty,
            };
        } catch {
            return null;
        }
    }
}
