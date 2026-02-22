import { Injectable, ForbiddenException, Logger } from '@nestjs/common';
import { Cron, CronExpression } from '@nestjs/schedule';
import { PrismaService } from '../../prisma/prisma.service';

/** Plan limits — hardcoded for lean bootstrap */
const PLAN_LIMITS: Record<string, { sessions: number }> = {
    FREE: { sessions: 3 },
    PRO: { sessions: 20 },
};

@Injectable()
export class UsageService {
    private readonly logger = new Logger(UsageService.name);

    constructor(private readonly prisma: PrismaService) { }

    /**
     * Check if user is within their monthly session limit.
     * Throws 403 ForbiddenException if limit exceeded.
     */
    async checkSessionLimit(userId: string): Promise<void> {
        const user = await this.prisma.user.findUniqueOrThrow({
            where: { id: userId },
            select: {
                planType: true,
                monthlySessionCount: true,
                usagePeriodStart: true,
            },
        });

        const plan = user.planType ?? 'FREE';
        const limit = PLAN_LIMITS[plan]?.sessions ?? PLAN_LIMITS['FREE'].sessions;

        if (user.monthlySessionCount >= limit) {
            throw new ForbiddenException(
                `Monthly session limit reached (${limit} sessions on ${plan} plan). ` +
                `Upgrade to PRO for 20 sessions/month.`,
            );
        }
    }

    /** Increment monthly session count after successful session creation. */
    async incrementSessionCount(userId: string): Promise<void> {
        await this.prisma.user.update({
            where: { id: userId },
            data: { monthlySessionCount: { increment: 1 } },
        });
    }

    /**
     * Monthly reset cron — runs at midnight on the 1st of each month.
     * Resets all users' session and evaluation counters.
     */
    @Cron(CronExpression.EVERY_1ST_DAY_OF_MONTH_AT_MIDNIGHT)
    async resetMonthlyUsage(): Promise<void> {
        this.logger.log('Resetting monthly usage counters for all users...');

        const result = await this.prisma.user.updateMany({
            data: {
                monthlySessionCount: 0,
                monthlyEvaluationCredits: 0,
                usagePeriodStart: new Date(),
            },
        });

        this.logger.log(`Monthly usage reset complete — ${result.count} users updated.`);
    }

    /** Get current usage info for a user (for profile/dashboard display). */
    async getUserUsage(userId: string) {
        const user = await this.prisma.user.findUniqueOrThrow({
            where: { id: userId },
            select: {
                planType: true,
                monthlySessionCount: true,
                monthlyEvaluationCredits: true,
                usagePeriodStart: true,
            },
        });

        const plan = user.planType ?? 'FREE';
        const sessionLimit = PLAN_LIMITS[plan]?.sessions ?? PLAN_LIMITS['FREE'].sessions;

        return {
            plan,
            monthlySessionCount: user.monthlySessionCount,
            sessionLimit,
            sessionsRemaining: Math.max(0, sessionLimit - user.monthlySessionCount),
            usagePeriodStart: user.usagePeriodStart,
        };
    }
}
