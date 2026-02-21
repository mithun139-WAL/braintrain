import { Injectable, NotFoundException, BadRequestException, ForbiddenException } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';
import { SubmitResponseDto } from './dto/submit-response.dto';
import { SessionStatus } from '@prisma/client';

@Injectable()
export class ResponsesService {
    constructor(private readonly prisma: PrismaService) { }

    async submitResponse(questionId: string, userId: string, dto: SubmitResponseDto) {
        // 1 & 2 & 3. Fetch question and firmly validate ownership through nested relations
        const question = await this.prisma.questionInstance.findFirst({
            where: {
                id: questionId,
                deletedAt: null,
                session: {
                    userId,
                    deletedAt: null,
                }
            },
            include: {
                session: true,
            }
        });

        if (!question) {
            throw new NotFoundException('Question not found or you do not have permission to access it');
        }

        // 4. Validate session is ACTIVE
        if (question.session.status !== SessionStatus.ACTIVE) {
            throw new BadRequestException('Responses can only be submitted for ACTIVE sessions');
        }

        // 5. Prevent duplicate response for same question
        const existingResponse = await this.prisma.responseInstance.findFirst({
            where: {
                questionId,
                deletedAt: null,
            },
        });

        if (existingResponse) {
            throw new BadRequestException('A response has already been submitted for this question');
        }

        // 6. Compute metrics at submission time (lightweight, no AI cost)
        const answerLength = dto.answerText?.length || 0;
        // hesitationScore, overallScore, etc. are evaluated post-session by EvaluationService

        // 7. Save ResponseInstance
        return this.prisma.responseInstance.create({
            data: {
                questionId,
                answerText: dto.answerText,
                audioUrl: dto.audioUrl || null,
                responseTimeMs: dto.responseTimeMs,
                thinkingTimeMs: dto.thinkingTimeMs,
                answerLength,
                // Signal scores are null until EvaluationService runs
            },
        });
    }
}
