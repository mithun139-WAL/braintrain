import {
    Injectable,
    Inject,
    Logger,
    NotFoundException,
    BadRequestException,
    ConflictException,
} from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';
import { AudioProcessingStatus, SessionStatus } from '@prisma/client';
import { AI_EVALUATION_PROVIDER, AI_TRANSCRIPTION_PROVIDER } from '../ai/ai.tokens';
import { AnswerEvaluationProvider } from '../ai/interfaces/answer-evaluation-provider.interface';
import { AudioTranscriptionProvider } from '../ai/interfaces/audio-transcription-provider.interface';
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
    private readonly logger = new Logger(EvaluationService.name);

    constructor(
        private readonly prisma: PrismaService,
        @Inject(AI_EVALUATION_PROVIDER)
        private readonly aiProvider: AnswerEvaluationProvider,
        @Inject(AI_TRANSCRIPTION_PROVIDER)
        private readonly transcriptionProvider: AudioTranscriptionProvider,
    ) { }

    // ─── Worker-facing — called by EvaluationWorker (no userId guard) ───────
    async analyzeSessionInternal(sessionId: string): Promise<SessionEvaluationResponseDto> {
        return this.runAnalysis(sessionId);
    }

    // ─── POST /sessions/:id/evaluation/analyze (manual / admin trigger) ────────
    async analyzeSession(
        sessionId: string,
        userId: string,
    ): Promise<SessionEvaluationResponseDto> {
        // Verify session belongs to user before allowing manual re-trigger
        const session = await this.prisma.interviewSession.findFirst({
            where: { id: sessionId, userId, deletedAt: null },
        });
        if (!session) throw new NotFoundException('Session not found or forbidden.');
        return this.runAnalysis(sessionId);
    }

    // ─── Core analysis logic (shared by both entry points) ──────────────────
    private async runAnalysis(sessionId: string): Promise<SessionEvaluationResponseDto> {
        // 1. Load session + check state
        const session = await this.prisma.interviewSession.findFirst({
            where: { id: sessionId, deletedAt: null },
            include: { evaluation: true },
        });

        if (!session) throw new NotFoundException('Session not found.');
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

        // 3. Credit check — never call LLM for users with no evaluation credits (spec §Cost)
        const user = await this.prisma.user.findUnique({
            where: { id: session.userId },
            select: { planType: true, monthlyEvaluationCredits: true },
        });

        const hasCredits =
            user?.planType === 'PRO' &&
            (user?.monthlyEvaluationCredits ?? 0) > 0;

        // If no credits, use stub provider inline; otherwise use the injected AI provider
        const provider = hasCredits ? this.aiProvider : null;

        if (!hasCredits) {
            this.logger.warn(
                `Session ${sessionId}: no evaluation credits (plan=${user?.planType ?? 'FREE'}) — ` +
                `running stub evaluation (degraded mode)`,
            );
        }

        // 4. Run per-response transcription + AI evaluation sequentially
        const signals: PerformanceSignal[] = [];
        let totalInputTokens = 0;
        let totalOutputTokens = 0;
        let totalCostUsd = 0;

        const evalStart = Date.now();

        for (const q of questionsWithResponses) {
            const response = q.responses[0];

            // ── Step 4a: Audio Transcription (Whisper) ───────────────────────
            // If the candidate submitted an audioUrl, transcribe it before LLM eval.
            // Transcription is non-blocking in the sense that failures degrade gracefully —
            // we fall back to the typed answerText without failing the job.
            let transcribedText: string | null = null;
            let audioDurationSeconds: number | null = null;
            let audioProcessingStatus: AudioProcessingStatus = response.audioProcessingStatus;

            if (response.audioUrl) {
                this.logger.debug(
                    `Transcribing audio for response ${response.id} | url: ${response.audioUrl}`,
                );

                // Update status to PROCESSING before the API call
                await this.prisma.responseInstance.update({
                    where: { id: response.id },
                    data: { audioProcessingStatus: AudioProcessingStatus.PROCESSING },
                });

                const result = await this.transcriptionProvider.transcribe(response.audioUrl);

                transcribedText = result.text || null;
                audioDurationSeconds = result.durationSeconds;
                audioProcessingStatus = AudioProcessingStatus.COMPLETED;

                // Whisper cost contributes to total session cost
                if (result.estimatedCostUsd !== null) {
                    totalCostUsd += result.estimatedCostUsd;
                }

                this.logger.log(
                    `Audio transcribed for response ${response.id} | ` +
                    `model=${result.modelUsed} | ` +
                    `words=${result.text.split(/\s+/).filter(Boolean).length} | ` +
                    `duration=${audioDurationSeconds?.toFixed(1) ?? '?'}s`,
                );
            }

            // ── Step 4b: Merge text sources ──────────────────────────────────
            // Transcribed text takes precedence over typed text (richer signal).
            // If both are absent, the LLM will evaluate based on metadata alone.
            const effectiveText = transcribedText?.trim()
                ? transcribedText
                : (response.answerText ?? undefined);

            const input: EvaluationInput = {
                question: q.content,
                text: effectiveText,
                audioUrl: response.audioUrl ?? undefined,
                questionType: 'behavioral', // TODO: derive from topic metadata
                difficulty: q.difficulty,
                responseTimeMs: response.responseTimeMs,
                thinkingTimeMs: response.thinkingTimeMs,
            };

            // ── Step 4c: LLM Evaluation ──────────────────────────────────────
            // Use injected provider (OpenAI or Stub based on credits); null = stub mode
            const signal = provider
                ? await provider.evaluate(input)
                : await this.aiProvider.evaluate(input); // aiProvider may itself be stub
            signals.push(signal);

            // Accumulate LLM cost metadata if provider returns it
            const meta = (signal as any).__meta;
            if (meta) {
                totalInputTokens += meta.inputTokens ?? 0;
                totalOutputTokens += meta.outputTokens ?? 0;
                totalCostUsd += meta.estimatedCostUsd ?? 0;
            }

            // ── Step 4d: Persist all signal data for this response ────────────
            await this.prisma.responseInstance.update({
                where: { id: response.id },
                data: {
                    // Audio signal fields
                    transcribedText,
                    audioDurationSeconds,
                    audioProcessingStatus,
                    // LLM + server-computed evaluation scores
                    clarityScore: signal.clarityScore,
                    structureScore: signal.structureScore,
                    depthScore: signal.depthScore,
                    confidenceScore: signal.confidenceScore,
                    communicationScore: signal.communicationScore,
                    hesitationScore: signal.hesitationScore,
                    technicalScore: signal.technicalScore,
                    pressureScore: signal.pressureScore,
                    thinkingDepthScore: signal.thinkingDepthScore,
                    overallScore: signal.overallScore,
                    evaluationExplanation: signal.explanation,
                },
            });
        }

        const evalDurationMs = Date.now() - evalStart;

        // 5. Aggregate signals → session-level averages
        const aggregated = this.aggregateSignals(signals);

        // Extract cost metadata from the last signal that has it (they all use same model)
        const lastMeta = signals.map(s => (s as any).__meta).filter(Boolean).pop() ?? {};
        const promptVersion = lastMeta.promptVersion ?? 'stub';
        const modelUsed = lastMeta.modelUsed ?? 'stub';

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
                    pressureScore: aggregated.pressureScore,
                    thinkingDepthScore: aggregated.thinkingDepthScore,
                    feedbackSummary: aggregated.feedbackSummary,
                    improvementSuggestions: aggregated.improvementSuggestions,
                    promptVersion,
                    modelUsed,
                    inputTokens: totalInputTokens || null,
                    outputTokens: totalOutputTokens || null,
                    estimatedCostUsd: totalCostUsd || null,
                },
            }),
            this.prisma.interviewSession.update({
                where: { id: sessionId },
                data: { status: SessionStatus.ANALYZED },
            }),
        ]);

        this.logger.log(
            `Session ${sessionId} ANALYZED in ${evalDurationMs}ms | ` +
            `Provider: ${promptVersion} | ` +
            `Overall: ${aggregated.overallScore.toFixed(1)} | ` +
            `Cost: $${totalCostUsd.toFixed(6)}`,
        );

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
            throw new NotFoundException('No evaluation found for this session.');

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
        pressureScore: number;
        thinkingDepthScore: number;
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
            pressureScore: avg('pressureScore'),
            thinkingDepthScore: avg('thinkingDepthScore'),
        };

        const feedbackSummary = this.buildFeedbackSummary(aggregated);
        const improvementSuggestions = this.buildImprovementSuggestions({
            ...aggregated,
            pressureScore: aggregated.pressureScore,
            thinkingDepthScore: aggregated.thinkingDepthScore,
        });

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
        pressureScore: number;
        thinkingDepthScore: number;
    }): Record<string, string[]> {
        const suggestions: Record<string, string[]> = {};

        if (scores.structureScore < 60)
            suggestions['structure'] = [
                'Use the STAR format (Situation, Task, Action, Result)',
                'Outline your answer mentally before speaking',
            ];

        if (scores.confidenceScore < 60)
            suggestions['confidence'] = [
                'Eliminate hedging phrases like "I think" and "maybe"',
                'State your position assertively, then support it with evidence',
            ];

        if (scores.depthScore < 60)
            suggestions['depth'] = [
                'Provide specific, quantified examples for every claim',
                'Explain the "why" behind your decisions, not just the "what"',
            ];

        if (scores.communicationScore < 60)
            suggestions['communication'] = [
                'Practice concise delivery — aim for 60–120 seconds per answer',
                'Record yourself answering and review for filler words',
            ];

        // Timing-based suggestions (server-computed signals)
        if (scores.pressureScore < 50)
            suggestions['pace'] = [
                'You answered too quickly — take a breath before responding',
                'It is fine to say "let me think about that for a moment"',
            ];

        if (scores.thinkingDepthScore < 50)
            suggestions['composure'] = [
                'Practice pausing 4–8 seconds before answering to organize your thoughts',
                'Deliberate pauses signal confidence, not uncertainty',
            ];

        return suggestions;
    }
}
