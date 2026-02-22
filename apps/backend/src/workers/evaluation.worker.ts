import { Injectable, Logger } from '@nestjs/common';
import { Cron, CronExpression } from '@nestjs/schedule';
import { EvaluationJobService } from '../modules/evaluation-job/evaluation-job.service';
import { EvaluationService } from '../modules/evaluation/evaluation.service';

/**
 * EvaluationWorker — cron-based async evaluation processor.
 *
 * Design decisions:
 * - Polls every 10s for PENDING jobs that are ready (respects nextRetryAt backoff)
 * - isRunning guard prevents overlapping executions on the same instance
 * - Handles idempotency: if the session was already evaluated (ConflictException),
 *   the job is marked COMPLETED rather than FAILED — crash-safe (spec §5)
 * - Separate zombie recovery cron resets PROCESSING jobs stuck >10min (spec §6)
 * - Processes up to N_CONCURRENT jobs per tick to drain backlogs faster without
 *   overwhelming the OpenAI rate limits
 */
@Injectable()
export class EvaluationWorker {
    private readonly logger = new Logger(EvaluationWorker.name);
    private isRunning = false;

    // Max jobs to process per tick — balances throughput vs rate limit safety
    private readonly BATCH_SIZE = 3;

    constructor(
        private readonly evaluationJobService: EvaluationJobService,
        private readonly evaluationService: EvaluationService,
    ) { }

    // ── Main processing loop — every 10s ─────────────────────────────────────
    @Cron(CronExpression.EVERY_10_SECONDS)
    async processNextJobs() {
        if (this.isRunning) {
            this.logger.debug('Worker tick skipped — previous run still active');
            return;
        }
        this.isRunning = true;

        try {
            let processed = 0;

            // Process up to BATCH_SIZE jobs per tick
            while (processed < this.BATCH_SIZE) {
                const job = await this.evaluationJobService.claimNextPendingJob();
                if (!job) break; // queue empty or all remaining jobs are in backoff window

                processed++;
                const startTime = Date.now();
                this.logger.log(
                    `Processing EvaluationJob ${job.id} | Session: ${job.sessionId} | ` +
                    `Attempt: ${job.attempts + 1}`,
                );

                try {
                    await this.evaluationService.analyzeSessionInternal(job.sessionId);
                    const durationMs = Date.now() - startTime;
                    await this.evaluationJobService.markCompleted(job.id);
                    this.logger.log(
                        `EvaluationJob ${job.id} COMPLETED in ${durationMs}ms`,
                    );
                } catch (err: unknown) {
                    await this.handleJobError(job.id, job.sessionId, err);
                }
            }

            if (processed > 0) {
                this.logger.debug(`Worker tick processed ${processed} job(s)`);
            }
        } finally {
            this.isRunning = false;
        }
    }

    // ── Zombie recovery cron — every 5 minutes (spec §6) ─────────────────────
    // Finds PROCESSING jobs stuck >10min (worker crashed mid-execution) and
    // resets them to PENDING so they'll be retried with a 30s delay.
    @Cron('0 */5 * * * *')  // every 5 minutes
    async recoverZombieJobs() {
        const count = await this.evaluationJobService.recoverZombieJobs();
        if (count > 0) {
            this.logger.warn(`Zombie recovery: reset ${count} stuck job(s) to PENDING`);
        }
    }

    /**
     * Handle job error with idempotency protection (spec §5).
     *
     * ConflictException means the EvaluationReport was already saved
     * (worker crashed after saving report but before markCompleted).
     * In this case, marking the job COMPLETED is correct, not FAILED.
     *
     * All other errors → markFailed (which applies exponential backoff).
     */
    private async handleJobError(
        jobId: string,
        sessionId: string,
        err: unknown,
    ): Promise<void> {
        const message = err instanceof Error ? err.message : String(err);

        // ConflictException = report already exists = evaluation was actually successful
        // This is the idempotency recovery path (spec §5)
        const isAlreadyEvaluated =
            message.includes('Evaluation already exists') ||
            message.includes('ConflictException') ||
            message.includes('Unique constraint');

        if (isAlreadyEvaluated) {
            this.logger.warn(
                `EvaluationJob ${jobId} (session ${sessionId}): ` +
                `report already exists — marking COMPLETED (idempotent recovery)`,
            );
            await this.evaluationJobService.markCompleted(jobId);
            return;
        }

        // Real failure — apply exponential backoff retry
        this.logger.error(
            `EvaluationJob ${jobId} (session ${sessionId}) failed: ${message}`,
        );
        await this.evaluationJobService.markFailed(jobId, message);
    }
}
