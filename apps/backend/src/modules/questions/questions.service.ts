import { Injectable, NotFoundException, BadRequestException } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';
import { SessionStatus } from '@prisma/client';
import { AdaptiveEngineService } from '../adaptive/adaptive-engine.service';

@Injectable()
export class QuestionsService {
    constructor(
        private readonly prisma: PrismaService,
        private readonly adaptiveEngine: AdaptiveEngineService,
    ) { }

    async generateNextQuestion(sessionId: string, userId: string) {
        // 1. Validate session exists, belongs to user, and is ACTIVE
        const session = await this.prisma.interviewSession.findFirst({
            where: {
                id: sessionId,
                userId,
                deletedAt: null,
            },
            include: {
                topic: true, // We might need topic details for the prompt later
            }
        });

        if (!session) {
            throw new NotFoundException('Session not found');
        }

        if (session.status !== SessionStatus.ACTIVE) {
            throw new BadRequestException('Questions can only be generated for ACTIVE sessions');
        }

        // 2. Count existing questions to determine sequenceOrder
        const questionCount = await this.prisma.questionInstance.count({
            where: {
                sessionId,
                deletedAt: null,
            },
        });

        if (questionCount >= 20) {
            throw new BadRequestException('Maximum questions reached for this session');
        }

        const sequenceOrder = questionCount + 1;

        // 3. Determine next difficulty
        const difficulty = session.adaptive
            ? await this.adaptiveEngine.determineNextDifficulty(sessionId)
            : session.difficulty;

        // 4. Call "AI generator" (stubbed for now)
        const generatedContent = this.stubAiGeneration(session.topic.name, difficulty, sequenceOrder, session.adaptive);

        // 5. Save QuestionInstance
        return this.prisma.questionInstance.create({
            data: {
                sessionId,
                content: generatedContent,
                difficulty, // The dynamically or statically determined difficulty
                sequenceOrder,
            },
        });
    }

    /**
     * Stub for AI Question Generation
     * Real implementation will be injected later (e.g., via a specialized AI service)
     */
    private stubAiGeneration(topicName: string, difficulty: string, sequenceNumber: number, isAdaptive: boolean): string {
        return `[Mock AI - ${difficulty} - ${isAdaptive ? 'Adaptive' : 'Static'}] Question #${sequenceNumber}: Explain the core concepts of ${topicName} in detail.`;
    }
}
