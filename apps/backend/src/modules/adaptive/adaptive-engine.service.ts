import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';
import { DifficultyLevel } from '@prisma/client';

/**
 * Thresholds for signal-driven difficulty transitions.
 *
 * These are tuned for a confidence simulator where overall score
 * is a composite of clarity, structure, depth, confidence, and hesitation.
 *
 * Future: make these configurable per-tenant or per-topic.
 */
const DIFFICULTY_THRESHOLDS = {
    /**
     * Score above this → candidate is coping comfortably → increase difficulty.
     * Lowered from 75 → 72: strong candidates no longer stall at the exact boundary.
     */
    INCREASE_ABOVE: 72,
    /**
     * Score below this → candidate is struggling → decrease difficulty.
     * Raised from 50 → 55: catches genuinely weak performers (~52 avg)
     * who were previously skating just above the old floor.
     */
    DECREASE_BELOW: 55,
} as const;

/** Minimum scored responses required before attempting any difficulty change */
const MIN_SCORED_RESPONSES = 2;

@Injectable()
export class AdaptiveEngineService {
    constructor(private readonly prisma: PrismaService) { }

    async determineNextDifficulty(sessionId: string): Promise<DifficultyLevel> {
        // 1. Fetch session base difficulty independently (no external dependency)
        const session = await this.prisma.interviewSession.findUnique({
            where: { id: sessionId },
            select: { difficulty: true },
        });

        if (!session) throw new Error('Session not found for adaptive logic');

        // 2. Fetch the last 3 answered questions that have been AI-evaluated
        const recentQuestions = await this.prisma.questionInstance.findMany({
            where: {
                sessionId,
                deletedAt: null,
                responses: { some: { deletedAt: null } },
            },
            include: {
                responses: {
                    where: { deletedAt: null },
                    orderBy: { createdAt: 'desc' },
                    take: 1,
                },
            },
            orderBy: { sequenceOrder: 'desc' },
            take: 3,
        });

        // 3. No answered questions yet → return session base difficulty
        if (recentQuestions.length === 0) return session.difficulty;

        // 4. Use the difficulty from the most recently answered question as our baseline
        const currentDifficulty = recentQuestions[0].difficulty;

        // 5. Collect overallScore values from AI-evaluated responses only
        //    (null means evaluation hasn't run yet → fall back gracefully)
        const scoredResponses = recentQuestions
            .map(q => q.responses[0]?.overallScore)
            .filter((score): score is number => score !== null && score !== undefined);

        // 6. Guard: not enough evaluated responses → stay at current difficulty
        //    This prevents premature transitions before we have enough signal
        if (scoredResponses.length < MIN_SCORED_RESPONSES) {
            return currentDifficulty;
        }

        // 7. Compute rolling average of overallScore
        const avgOverall = scoredResponses.reduce((sum, s) => sum + s, 0) / scoredResponses.length;

        // 8. Signal-driven transition (confidence-based, not word-count-based)
        if (avgOverall > DIFFICULTY_THRESHOLDS.INCREASE_ABOVE) {
            return this.increaseDifficulty(currentDifficulty);
        }

        if (avgOverall < DIFFICULTY_THRESHOLDS.DECREASE_BELOW) {
            return this.decreaseDifficulty(currentDifficulty);
        }

        // 9. Score in neutral band → maintain current difficulty
        return currentDifficulty;
    }

    // ─── Private Transition Logic ────────────────────────────────────────────

    private increaseDifficulty(level: DifficultyLevel): DifficultyLevel {
        if (level === DifficultyLevel.BEGINNER) return DifficultyLevel.INTERMEDIATE;
        if (level === DifficultyLevel.INTERMEDIATE) return DifficultyLevel.ADVANCED;
        return DifficultyLevel.ADVANCED;
    }

    private decreaseDifficulty(level: DifficultyLevel): DifficultyLevel {
        if (level === DifficultyLevel.ADVANCED) return DifficultyLevel.INTERMEDIATE;
        if (level === DifficultyLevel.INTERMEDIATE) return DifficultyLevel.BEGINNER;
        return DifficultyLevel.BEGINNER;
    }
}
