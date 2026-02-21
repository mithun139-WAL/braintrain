import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';

@Injectable()
export class AnalyticsService {
    constructor(private readonly prisma: PrismaService) { }

    async getAnalytics(userId: string) {
        // 1. Fetch all sessions for user with evaluation reports
        const sessions = await this.prisma.interviewSession.findMany({
            where: { userId, deletedAt: null },
            include: {
                topic: { select: { id: true, name: true } },
                evaluation: {
                    select: {
                        overallScore: true,
                        confidenceScore: true,
                        clarityScore: true,
                        structureScore: true,
                        depthScore: true,
                        pressureScore: true,
                        thinkingDepthScore: true,
                        createdAt: true,
                    },
                },
            },
            orderBy: { createdAt: 'asc' },
        });

        const totalSessions = sessions.length;
        const analyzedSessions = sessions.filter(s => s.evaluation !== null);

        // 2. Build chronological trend array from analyzed sessions
        const trend = analyzedSessions.map(s => ({
            sessionId: s.id,
            topicName: s.topic.name,
            interviewLevel: s.interviewLevel ?? null,
            analyzedAt: s.evaluation!.createdAt.toISOString(),
            overallScore: s.evaluation!.overallScore,
            confidenceScore: s.evaluation!.confidenceScore,
            clarityScore: s.evaluation!.clarityScore,
            structureScore: s.evaluation!.structureScore,
            depthScore: s.evaluation!.depthScore,
        }));

        // 3. Improvement delta (latest minus first analyzed session)
        let improvement = {
            overallDelta: 0,
            confidenceDelta: 0,
            clarityDelta: 0,
            topImprovedDimension: null as string | null,
            topWeakDimension: null as string | null,
        };

        if (analyzedSessions.length >= 2) {
            const first = analyzedSessions[0].evaluation!;
            const latest = analyzedSessions[analyzedSessions.length - 1].evaluation!;

            const deltas: Record<string, number> = {
                overall: latest.overallScore - first.overallScore,
                confidence: latest.confidenceScore - first.confidenceScore,
                clarity: latest.clarityScore - first.clarityScore,
                structure: latest.structureScore - first.structureScore,
                depth: latest.depthScore - first.depthScore,
            };

            improvement = {
                overallDelta: parseFloat(deltas.overall.toFixed(1)),
                confidenceDelta: parseFloat(deltas.confidence.toFixed(1)),
                clarityDelta: parseFloat(deltas.clarity.toFixed(1)),
                topImprovedDimension: Object.entries(deltas).sort((a, b) => b[1] - a[1])[0]?.[0] ?? null,
                topWeakDimension: Object.entries(deltas)
                    .filter(([, v]) => v < 0)
                    .sort((a, b) => a[1] - b[1])[0]?.[0] ?? null,
            };
        }

        // 4. Per-topic breakdown
        const topicMap = new Map<string, { name: string; scores: number[] }>();
        for (const s of analyzedSessions) {
            const key = s.topic.id;
            if (!topicMap.has(key)) {
                topicMap.set(key, { name: s.topic.name, scores: [] });
            }
            topicMap.get(key)!.scores.push(s.evaluation!.overallScore);
        }

        const byTopic = Array.from(topicMap.entries()).map(([topicId, { name, scores }]) => ({
            topicId,
            topicName: name,
            sessionCount: scores.length,
            avgOverallScore: parseFloat((scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1)),
        }));

        return {
            totalSessions,
            analyzedSessions: analyzedSessions.length,
            trend,
            improvement,
            byTopic,
        };
    }

    /**
     * GET /analytics/progression — dopamine loop endpoint.
     * Returns last session score, previous session score, and the delta.
     * Perfect for a "you improved by +X.X points!" banner on the app.
     */
    async getProgression(userId: string) {
        const lastTwo = await this.prisma.interviewSession.findMany({
            where: { userId, deletedAt: null, status: 'ANALYZED' },
            include: {
                evaluation: {
                    select: { overallScore: true, createdAt: true },
                },
            },
            orderBy: { createdAt: 'desc' },
            take: 2,
        });

        if (lastTwo.length === 0) {
            return { lastSession: null, previousSession: null, delta: null };
        }

        const lastSession = lastTwo[0];
        const previousSession = lastTwo[1] ?? null;

        const lastScore = lastSession.evaluation?.overallScore ?? null;
        const prevScore = previousSession?.evaluation?.overallScore ?? null;

        const delta =
            lastScore !== null && prevScore !== null
                ? parseFloat((lastScore - prevScore).toFixed(1))
                : null;

        return {
            lastSession: {
                sessionId: lastSession.id,
                overallScore: lastScore,
                analyzedAt: lastSession.evaluation?.createdAt?.toISOString() ?? null,
            },
            previousSession: previousSession
                ? {
                    sessionId: previousSession.id,
                    overallScore: prevScore,
                    analyzedAt: previousSession.evaluation?.createdAt?.toISOString() ?? null,
                }
                : null,
            delta,
        };
    }
}
