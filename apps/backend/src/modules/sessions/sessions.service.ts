import { Injectable, NotFoundException, BadRequestException, ForbiddenException } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';
import { CreateSessionDto } from './dto/create-session.dto';
import { ListSessionsDto } from './dto/list-sessions.dto';
import { SessionStatus } from '@prisma/client';

@Injectable()
export class SessionsService {
    constructor(private readonly prisma: PrismaService) { }

    async createSession(dto: CreateSessionDto, userId: string) {
        // 1. Validate topic exists and is not soft-deleted
        const topic = await this.prisma.topic.findFirst({
            where: {
                id: dto.topicId,
                deletedAt: null,
            },
        });

        if (!topic) {
            throw new NotFoundException('Topic not found');
        }

        // Ensure topic is accessible (global or created by this user)
        if (!topic.isGlobal && topic.createdByUserId !== userId) {
            throw new ForbiddenException('You do not have access to this topic');
        }

        // 2. Create session with controlled status
        return this.prisma.interviewSession.create({
            data: {
                userId,
                topicId: dto.topicId,
                mode: dto.mode,
                interviewLevel: dto.interviewLevel ?? null,
                difficulty: dto.difficulty,
                adaptive: dto.adaptive,
                durationMinutes: dto.durationMinutes,
                personalityConfig: dto.personalityConfig ? dto.personalityConfig : undefined,
                status: SessionStatus.CREATED,
            },
        });
    }

    async getSessionById(sessionId: string, userId: string) {
        // Safe lookup: Must match id AND userId AND not be soft-deleted
        const session = await this.prisma.interviewSession.findFirst({
            where: {
                id: sessionId,
                userId,
                deletedAt: null,
            },
        });

        if (!session) {
            throw new NotFoundException('Session not found');
        }

        return session;
    }

    async startSession(sessionId: string, userId: string) {
        const session = await this.getSessionById(sessionId, userId);

        // Controlled State Transition
        if (session.status !== SessionStatus.CREATED) {
            throw new BadRequestException('Session is not in CREATED state. Cannot start.');
        }

        return this.prisma.interviewSession.update({
            where: { id: sessionId },
            data: {
                status: SessionStatus.ACTIVE,
                startedAt: new Date(),
            },
        });
    }

    async completeSession(sessionId: string, userId: string) {
        const session = await this.getSessionById(sessionId, userId);

        // Controlled State Transition
        if (session.status !== SessionStatus.ACTIVE) {
            throw new BadRequestException('Only ACTIVE sessions can be completed.');
        }

        return this.prisma.interviewSession.update({
            where: { id: sessionId },
            data: {
                status: SessionStatus.COMPLETED,
                endedAt: new Date(),
            },
        });
    }

    async listSessions(userId: string, dto: ListSessionsDto) {
        const page = dto.page ?? 1;
        const limit = dto.limit ?? 20;
        const skip = (page - 1) * limit;

        const where: any = {
            userId,
            deletedAt: null,
            ...(dto.status && { status: dto.status as SessionStatus }),
        };

        const [sessions, total] = await Promise.all([
            this.prisma.interviewSession.findMany({
                where,
                include: {
                    topic: { select: { id: true, name: true } },
                    evaluation: { select: { overallScore: true } },
                    _count: { select: { questions: true } },
                },
                orderBy: { createdAt: 'desc' },
                skip,
                take: limit,
            }),
            this.prisma.interviewSession.count({ where }),
        ]);

        return {
            data: sessions,
            meta: {
                total,
                page,
                limit,
                totalPages: Math.ceil(total / limit),
            },
        };
    }
}
