import {
    Injectable,
    Inject,
    NotFoundException,
    BadRequestException,
    ConflictException,
} from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';
import { SessionStatus } from '@prisma/client';
import { AI_EVALUATION_PROVIDER } from '../ai/ai.tokens';
import { AnswerEvaluationProvider } from '../ai/interfaces/answer-evaluation-provider.interface';
import { EvaluationInput } from '../ai/interfaces/evaluation-input.interface';
import { PerformanceSignal } from '../ai/interfaces/performance-signal.interface';
import { SessionEvaluationResponseDto } from './dto/session-evaluation-response.dto';
import { toEvaluationResponseDto } from './dto/evaluation-response.mapper';

// ─── Shared Query Include ────────────────────────────────────────────────────
// Reused by analyze + getReport so the shape is identical in both places
const EVALUATION_QUERY_INCLUDE = {
    session: {
        include: {
            questions: {
                where: { deletedAt: null },
                orderBy: { sequenceOrder: 'asc' as const },
            },
        },
    },
} as const;

@Injectable()
export class EvaluationService {
    constructor(
        private readonly prisma: PrismaService,
        @Inject(AI_EVALUATION_PROVIDER)
        private readonly aiProvider: AnswerEvaluationProvider,
    ) { }

    // ─────────────────────────────────────────────────────────────────────────
    // POST /sessions/:id/evaluation/analyze
    // ─────────────────────────────────────────────────────────────────────────

    async analyzeSession(
        sessionId: string,
        userId: string,
    ): Promise<SessionEvaluationResponseDto> {
        // 1. Validate and authorise session
        const session = await this.prisma.interviewSession.findFirst({
            where: { id: sessionId, userId, deletedAt: null },
            include: { evaluation: true },
        });

        if (!session) throw new NotFoundException('Session not found or forbidden.');
        if (session.status !== SessionStatus.COMPLETED)
            throw new BadRequestException('Session must be COMPLETED before analysis.');
        if (session.evaluation)
            throw new ConflictException('Evaluation already exists for this session.');

        // 2. Load all questions + their responses
        const questionsWithResponses = await this.prisma.questionInstance.findMany({
            where: { sessionId, deletedAt: null },
            include: { responses: { where: { deletedAt: null } } },
            orderBy: { sequenceOrder: 'asc' },
        });

        if (!questionsWithResponses.length)
            throw new BadRequestException('Cannot analyze a session without questions.');

        const unanswered = questionsWithResponses.some(q => !q.responses.length);
        if (unanswered)
            throw new BadRequestException('All questions must have responses before analysis.');

        // 3. Run per-response AI evaluation sequentially
        const signals: PerformanceSignal[] = [];

        for (const q of questionsWithResponses) {
            const response = q.responses[0];

            const input: EvaluationInput = {
                question: q.content,
                text: response.answerText ?? undefined,
                audioUrl: response.audioUrl ?? undefined,
                questionType: 'behavioral', // TODO: derive from topic metadata
                difficulty: q.difficulty,
            };

            const signal = await this.aiProvider.evaluate(input);
            signals.push(signal);

            // 4. Persist per-response signal scores immediately
            await this.prisma.responseInstance.update({
                where: { id: response.id },
                data: {
                    clarityScore: signal.clarityScore,
                    structureScore: signal.structureScore,
                    depthScore: signal.depthScore,
                    confidenceScore: signal.confidenceScore,
                    communicationScore: signal.communicationScore,
                    hesitationScore: signal.hesitationScore,
                    technicalScore: signal.technicalScore,
                    overallScore: signal.overallScore,
                    evaluationExplanation: signal.explanation,
                },
            });
        }

        // 5. Aggregate signals → session-level averages
        const aggregated = this.aggregateSignals(signals);

        // 6. Atomic: create EvaluationReport + transition session to ANALYZED
        const [evaluationReport] = await this.prisma.$transaction([
            this.prisma.evaluationReport.create({
                data: {
                    sessionId,
                    overallScore: aggregated.overallScore,
                    clarityScore: aggregated.clarityScore,
                    structureScore: aggregated.structureScore,
                    depthScore: aggregated.depthScore,
                    confidenceScore: aggregated.confidenceScore,
                    communicationScore: aggregated.communicationScore,
                    hesitationScore: aggregated.hesitationScore,
                    technicalScore: aggregated.technicalScore,
                    feedbackSummary: aggregated.feedbackSummary,
                    improvementSuggestions: aggregated.improvementSuggestions,
                },
            }),
            this.prisma.interviewSession.updateMany({
                where: { id: sessionId, userId },
                data: { status: SessionStatus.ANALYZED },
            }),
        ]);

        // 7. Fetch full report + session shape needed by the mapper
        const fullReport = await this.prisma.evaluationReport.findUniqueOrThrow({
            where: { id: evaluationReport.id },
            include: EVALUATION_QUERY_INCLUDE,
        });

        return toEvaluationResponseDto(fullReport);
    }

    // ─────────────────────────────────────────────────────────────────────────
    // GET /sessions/:id/evaluation
    // ─────────────────────────────────────────────────────────────────────────

    async getEvaluation(
        sessionId: string,
        userId: string,
    ): Promise<SessionEvaluationResponseDto> {
        // Verify the session belongs to this user before exposing its report
        const session = await this.prisma.interviewSession.findFirst({
            where: { id: sessionId, userId, deletedAt: null },
        });

        if (!session) throw new NotFoundException('Session not found or forbidden.');

        const report = await this.prisma.evaluationReport.findUnique({
            where: { sessionId },
            include: EVALUATION_QUERY_INCLUDE,
        });

        if (!report)
            throw new NotFoundException('No evaluation found for this session. Run analyze first.');

        return toEvaluationResponseDto(report);
    }

    // ─── Private Helpers ────────────────────────────────────────────────────

    private aggregateSignals(signals: PerformanceSignal[]): {
        overallScore: number;
        clarityScore: number;
        structureScore: number;
        depthScore: number;
        confidenceScore: number;
        communicationScore: number;
        hesitationScore: number;
        technicalScore: number | null;
        feedbackSummary: string;
        improvementSuggestions: Record<string, string[]>;
    } {
        const avg = (key: keyof PerformanceSignal) =>
            signals.reduce((sum, s) => sum + (Number(s[key]) || 0), 0) / signals.length;

        const technicalScores = signals
            .map(s => s.technicalScore)
            .filter((v): v is number => v !== null);

        const aggregated = {
            overallScore: avg('overallScore'),
            clarityScore: avg('clarityScore'),
            structureScore: avg('structureScore'),
            depthScore: avg('depthScore'),
            confidenceScore: avg('confidenceScore'),
            communicationScore: avg('communicationScore'),
            hesitationScore: avg('hesitationScore'),
            technicalScore: technicalScores.length
                ? technicalScores.reduce((a, b) => a + b, 0) / technicalScores.length
                : null,
        };

        const feedbackSummary = this.buildFeedbackSummary(aggregated);
        const improvementSuggestions = this.buildImprovementSuggestions(aggregated);

        return { ...aggregated, feedbackSummary, improvementSuggestions };
    }

    private buildFeedbackSummary(scores: {
        overallScore: number;
        clarityScore: number;
        structureScore: number;
        confidenceScore: number;
        hesitationScore: number;
    }): string {
        const overall = scores.overallScore.toFixed(1);
        if (scores.overallScore >= 75)
            return `Strong performance with an overall score of ${overall}/100. Clarity and structure were highlights.`;
        if (scores.overallScore >= 50)
            return `Solid foundation with an overall score of ${overall}/100. Key areas for growth: structure and confidence.`;
        return `Developing performance with an overall score of ${overall}/100. Focus on answer depth and reducing hesitation.`;
    }

    private buildImprovementSuggestions(scores: {
        structureScore: number;
        confidenceScore: number;
        communicationScore: number;
        hesitationScore: number;
        depthScore: number;
    }): Record<string, string[]> {
        const suggestions: Record<string, string[]> = {};

        if (scores.structureScore < 60)
            suggestions['structure'] = [
                'Use the STAR format (Situation, Task, Action, Result)',
                'Practice with structured outlines before answering',
            ];

        if (scores.confidenceScore < 60)
            suggestions['confidence'] = [
                'Eliminate hedging phrases like "I think" and "maybe"',
                'State your position assertively, then support it',
            ];

        if (scores.hesitationScore > 40)
            suggestions['delivery'] = [
                'Reduce filler words (um, uh, like)',
                'Pause deliberately instead of filling silence',
            ];

        if (scores.depthScore < 60)
            suggestions['depth'] = [
                'Provide specific examples for every claim',
                'Quantify outcomes where possible',
            ];

        if (scores.communicationScore < 60)
            suggestions['communication'] = [
                'Practice concise delivery — aim for 90–120 seconds per answer',
            ];

        return suggestions;
    }
}
