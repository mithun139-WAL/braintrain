import { Injectable, Logger } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';
import { EvaluationJobStatus } from '@prisma/client';

const MAX_ATTEMPTS = 3;

/**
 * Exponential backoff delays per attempt number (spec §4).
 * attempt 1 → 30s, attempt 2 → 2min, attempt 3 → 10min
 */
const RETRY_DELAYS_MS: Record<number, number> = {
    1: 30_000,          //  30 seconds
    2: 2 * 60_000,      //  2 minutes
    3: 10 * 60_000,     // 10 minutes
};

/** Jobs stuck in PROCESSING longer than this are considered zombies (spec §6) */
const ZOMBIE_THRESHOLD_MS = 10 * 60_000; // 10 minutes

@Injectable()
export class EvaluationJobService {
    private readonly logger = new Logger(EvaluationJobService.name);

    constructor(private readonly prisma: PrismaService) { }

    /** Create a PENDING job when a session is completed. */
    async createJob(sessionId: string) {
        return this.prisma.evaluationJob.create({
            data: { sessionId, status: EvaluationJobStatus.PENDING },
        });
    }

    /**
     * Claim the next PENDING job that is ready to run.
     * Respects nextRetryAt — jobs with a future nextRetryAt are skipped (backoff delay).
     * Uses a transaction to prevent double-claiming under concurrent polls (spec §2).
     */
    async claimNextPendingJob() {
        return this.prisma.$transaction(async (tx) => {
            const now = new Date();
            const job = await tx.evaluationJob.findFirst({
                where: {
                    status: EvaluationJobStatus.PENDING,
                    OR: [
                        { nextRetryAt: null },
                        { nextRetryAt: { lte: now } },
                    ],
                },
                orderBy: { createdAt: 'asc' },
            });

            if (!job) return null;

            return tx.evaluationJob.update({
                where: { id: job.id },
                data: {
                    status: EvaluationJobStatus.PROCESSING,
                    evaluationStartedAt: now,
                    nextRetryAt: null,
                },
            });
        });
    }

    /** Mark job COMPLETED after successful evaluation. */
    async markCompleted(jobId: string) {
        return this.prisma.evaluationJob.update({
            where: { id: jobId },
            data: {
                status: EvaluationJobStatus.COMPLETED,
                evaluationCompletedAt: new Date(),
            },
        });
    }

    /**
     * Mark job failed or reset to PENDING with exponential backoff delay (spec §4).
     *
     * Idempotency note: if the worker calls this after the evaluation report
     * was already saved (crash-before-markCompleted), the caller should detect
     * the ConflictException and call markCompleted instead.
     */
    async markFailed(jobId: string, error: string) {
        const job = await this.prisma.evaluationJob.findUniqueOrThrow({
            where: { id: jobId },
        });

        const newAttempts = job.attempts + 1;
        const isFinal = newAttempts >= MAX_ATTEMPTS;
        const delayMs = RETRY_DELAYS_MS[newAttempts] ?? RETRY_DELAYS_MS[MAX_ATTEMPTS];
        const nextRetryAt = isFinal ? null : new Date(Date.now() + delayMs);

        this.logger.warn(
            `EvaluationJob ${jobId} failed (attempt ${newAttempts}/${MAX_ATTEMPTS}): ${error}` +
            (isFinal ? ' — PERMANENTLY FAILED' : ` — retry in ${delayMs / 1000}s`),
        );

        return this.prisma.evaluationJob.update({
            where: { id: jobId },
            data: {
                status: isFinal ? EvaluationJobStatus.FAILED : EvaluationJobStatus.PENDING,
                attempts: newAttempts,
                lastError: error.slice(0, 1000), // guard against oversized errors
                evaluationStartedAt: null,
                nextRetryAt,
            },
        });
    }

    /**
     * Zombie recovery — called by a separate cron (spec §6).
     * Finds PROCESSING jobs stuck longer than ZOMBIE_THRESHOLD_MS and resets them to PENDING.
     * Prevents jobs from being stuck forever if the worker process crashes mid-execution.
     */
    async recoverZombieJobs(): Promise<number> {
        const stuckBefore = new Date(Date.now() - ZOMBIE_THRESHOLD_MS);

        const result = await this.prisma.evaluationJob.updateMany({
            where: {
                status: EvaluationJobStatus.PROCESSING,
                evaluationStartedAt: { lte: stuckBefore },
            },
            data: {
                status: EvaluationJobStatus.PENDING,
                evaluationStartedAt: null,
                lastError: 'Recovered from zombie state (worker crashed mid-execution)',
                nextRetryAt: new Date(Date.now() + RETRY_DELAYS_MS[1]), // 30s delay
            },
        });

        if (result.count > 0) {
            this.logger.warn(`Zombie recovery: reset ${result.count} stuck PROCESSING job(s) to PENDING`);
        }

        return result.count;
    }

    /** Fetch job status for a session (used by status polling endpoint). */
    async getJobBySessionId(sessionId: string) {
        return this.prisma.evaluationJob.findUnique({
            where: { sessionId },
        });
    }
}
