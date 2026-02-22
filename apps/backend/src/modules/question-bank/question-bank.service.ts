import { BadRequestException, Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';
import { CreateQuestionBankDto } from './dto/create-question-bank.dto';
import { DifficultyLevel } from '@prisma/client';

@Injectable()
export class QuestionBankService {
    constructor(private readonly prisma: PrismaService) { }

    async createQuestion(dto: CreateQuestionBankDto, userId: string) {
        // Validate topic exists
        const topic = await this.prisma.topic.findFirst({
            where: { id: dto.topicId, deletedAt: null },
        });
        if (!topic) throw new NotFoundException('Topic not found');

        return this.prisma.questionBank.create({
            data: {
                content: dto.content,
                topicId: dto.topicId,
                difficulty: dto.difficulty,
                questionType: dto.questionType,
                isGlobal: dto.isGlobal ?? false,
                createdByUserId: userId,
            },
            include: {
                topic: { select: { id: true, name: true } },
            },
        });
    }

    async listQuestions(topicId: string, difficulty?: DifficultyLevel, userId?: string) {
        return this.prisma.questionBank.findMany({
            where: {
                topicId,
                deletedAt: null,
                ...(difficulty && { difficulty }),
                // Return global questions + user-created ones
                OR: [
                    { isGlobal: true },
                    { createdByUserId: userId ?? '' },
                ],
            },
            include: {
                topic: { select: { id: true, name: true } },
            },
            orderBy: [{ isGlobal: 'desc' }, { createdAt: 'desc' }],
        });
    }

    async getById(id: string) {
        const question = await this.prisma.questionBank.findFirst({
            where: { id, deletedAt: null },
            include: { topic: { select: { id: true, name: true } } },
        });
        if (!question) throw new NotFoundException('Question not found');
        return question;
    }

    async incrementUsage(id: string) {
        return this.prisma.questionBank.update({
            where: { id },
            data: { usageCount: { increment: 1 } },
        });
    }

    /**
     * Bank-first lookup: find a random question for the given topic + difficulty.
     * Returns null if no bank questions available — caller falls back to generation.
     */
    async pickQuestion(topicId: string, difficulty: DifficultyLevel, userId: string): Promise<string | null> {
        const candidates = await this.prisma.questionBank.findMany({
            where: {
                topicId,
                difficulty,
                deletedAt: null,
                OR: [{ isGlobal: true }, { createdByUserId: userId }],
            },
            select: { id: true, content: true },
        });

        if (!candidates.length) return null;

        // Random selection for variety
        const picked = candidates[Math.floor(Math.random() * candidates.length)];
        await this.incrementUsage(picked.id);
        return picked.content;
    }
}
