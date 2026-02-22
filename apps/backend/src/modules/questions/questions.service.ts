import { Injectable, Inject, NotFoundException, BadRequestException, Logger } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';
import { SessionStatus } from '@prisma/client';
import { AdaptiveEngineService } from '../adaptive/adaptive-engine.service';
import { QuestionBankService } from '../question-bank/question-bank.service';
import { AI_QUESTION_GENERATION_PROVIDER } from '../ai/ai.tokens';
import { QuestionGenerationProvider } from '../ai/interfaces/question-generation-provider.interface';

@Injectable()
export class QuestionsService {
    private readonly logger = new Logger(QuestionsService.name);

    constructor(
        private readonly prisma: PrismaService,
        private readonly adaptiveEngine: AdaptiveEngineService,
        private readonly questionBankService: QuestionBankService,
        @Inject(AI_QUESTION_GENERATION_PROVIDER)
        private readonly questionGenerator: QuestionGenerationProvider,
    ) { }

    async generateNextQuestion(sessionId: string, userId: string) {
        // 1. Validate session exists, belongs to user, and is ACTIVE
        const session = await this.prisma.interviewSession.findFirst({
            where: { id: sessionId, userId, deletedAt: null },
            include: { topic: true },
        });

        if (!session) {
            throw new NotFoundException('Session not found');
        }

        if (session.status !== SessionStatus.ACTIVE) {
            throw new BadRequestException('Questions can only be generated for ACTIVE sessions');
        }

        // 2. Fetch existing questions (for sequenceOrder and duplicate prevention)
        const existingQuestions = await this.prisma.questionInstance.findMany({
            where: { sessionId, deletedAt: null },
            select: { content: true },
            orderBy: { sequenceOrder: 'asc' },
        });

        if (existingQuestions.length >= 20) {
            throw new BadRequestException('Maximum questions reached for this session');
        }

        const sequenceOrder = existingQuestions.length + 1;

        // 3. Determine next difficulty (adaptive or static)
        const difficulty = session.adaptive
            ? await this.adaptiveEngine.determineNextDifficulty(sessionId)
            : session.difficulty;

        // 4. Bank-first selection: use existing bank question if available
        const bankContent = await this.questionBankService.pickQuestion(
            session.topicId,
            difficulty,
            userId,
        );

        let questionContent: string;

        if (bankContent) {
            // ✅ Bank hit — free, zero AI cost
            questionContent = bankContent;
            this.logger.debug(`Session ${sessionId} Q${sequenceOrder}: served from bank`);
        } else {
            // 🤖 Bank miss → generate via LLM (OpenAI or Stub depending on env)
            this.logger.log(`Session ${sessionId} Q${sequenceOrder}: bank miss → LLM generation`);

            const generated = await this.questionGenerator.generate({
                topicName: session.topic.name,
                topicId: session.topicId,
                difficulty,
                questionType: 'behavioral', // TODO: derive from topic/session metadata
                existingQuestions: existingQuestions.map(q => q.content),
            });

            // Note: OpenAIQuestionGenerationProvider auto-saves to QuestionBank
            // so the next session hitting this topic/difficulty gets a bank hit
            questionContent = generated.questionText;
        }

        // 5. Persist QuestionInstance
        return this.prisma.questionInstance.create({
            data: {
                sessionId,
                content: questionContent,
                difficulty,
                sequenceOrder,
            },
        });
    }
}
