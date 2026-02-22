import { BadRequestException, ForbiddenException, Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';
import { CreateTopicDto } from './dto/create-topic.dto';

@Injectable()
export class TopicsService {
    constructor(private readonly prisma: PrismaService) { }

    async createTopic(dto: CreateTopicDto, userId: string) {
        // Validate parent topic exists if provided
        if (dto.parentTopicId) {
            const parent = await this.prisma.topic.findFirst({
                where: { id: dto.parentTopicId, deletedAt: null },
            });
            if (!parent) throw new NotFoundException('Parent topic not found');
        }

        // Check for duplicate name within the same scope (global or user-owned)
        const existing = await this.prisma.topic.findFirst({
            where: {
                name: dto.name,
                createdByUserId: userId,
                deletedAt: null,
            },
        });
        if (existing) throw new BadRequestException(`You already have a topic named "${dto.name}"`);

        return this.prisma.topic.create({
            data: {
                name: dto.name,
                isGlobal: false,
                createdByUserId: userId,
                parentTopicId: dto.parentTopicId ?? null,
            },
            include: {
                parentTopic: { select: { id: true, name: true } },
                _count: { select: { subtopics: true, sessions: true } },
            },
        });
    }

    async listTopics(userId: string) {
        // Returns all global topics + all topics owned by this user, without soft-deleted
        return this.prisma.topic.findMany({
            where: {
                deletedAt: null,
                OR: [
                    { isGlobal: true },
                    { createdByUserId: userId },
                ],
            },
            include: {
                parentTopic: { select: { id: true, name: true } },
                subtopics: {
                    where: { deletedAt: null },
                    select: { id: true, name: true },
                },
                _count: { select: { sessions: true } },
            },
            orderBy: [
                { isGlobal: 'desc' },  // global topics first
                { name: 'asc' },
            ],
        });
    }

    async getTopicById(topicId: string, userId: string) {
        const topic = await this.prisma.topic.findFirst({
            where: {
                id: topicId,
                deletedAt: null,
                OR: [
                    { isGlobal: true },
                    { createdByUserId: userId },
                ],
            },
            include: {
                parentTopic: { select: { id: true, name: true } },
                subtopics: {
                    where: { deletedAt: null },
                    select: { id: true, name: true },
                },
                _count: { select: { sessions: true } },
            },
        });

        if (!topic) {
            throw new NotFoundException('Topic not found');
        }

        return topic;
    }

    async deleteTopic(topicId: string, userId: string) {
        const topic = await this.prisma.topic.findFirst({
            where: { id: topicId, deletedAt: null },
        });

        if (!topic) throw new NotFoundException('Topic not found');

        if (topic.isGlobal || topic.createdByUserId !== userId) {
            throw new ForbiddenException('You do not have permission to delete this topic');
        }

        await this.prisma.topic.update({
            where: { id: topicId },
            data: { deletedAt: new Date() },
        });

        return { message: 'Topic deleted successfully' };
    }
}
