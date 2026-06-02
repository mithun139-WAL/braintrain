"use client";

import Link from "next/link";
import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { format, formatDistanceToNow } from "date-fns";
import {
    BarChart2,
    Calendar,
    CalendarDays,
    ChevronRight,
    Layers,
    Loader2,
    Play,
    Sparkles,
    ArrowRight,
    Clock3,
} from "lucide-react";
import { Difficulty, InterviewMode, InterviewType, SessionStatus, type TopicDto } from "@braintrain/shared";
import { PageHeader } from "@/core/components/ui/PageHeader";
import { Surface } from "@/core/components/ui/Surface";
import { buttonStyles } from "@/core/components/ui/button";
import { cn } from "@/lib/utils";
import { analyticsApi } from "@/lib/api/analytics.api";
import { topicsApi } from "@/lib/api/topics.api";
import { sessionsApi, type SessionListItem } from "@/lib/api/sessions.api";

const difficultyClasses: Record<string, string> = {
    [Difficulty.EASY]: "border-emerald/20 bg-emerald/10 text-emerald",
    [Difficulty.MEDIUM]: "border-gold/20 bg-gold/10 text-gold",
    [Difficulty.HARD]: "border-ruby/20 bg-ruby/10 text-ruby",
};

const statusClasses: Record<string, string> = {
    [SessionStatus.CREATED]: "border-border bg-muted text-muted-foreground",
    [SessionStatus.ACTIVE]: "border-primary/20 bg-primary/10 text-primary",
    [SessionStatus.COMPLETED]: "border-gold/20 bg-gold/10 text-gold",
    [SessionStatus.ANALYZED]: "border-emerald/20 bg-emerald/10 text-emerald",
    [SessionStatus.CANCELLED]: "border-ruby/20 bg-ruby/10 text-ruby",
};

function formatInterviewType(type?: string | null) {
    switch (type) {
        case InterviewType.TECHNICAL:
            return "Technical";
        case InterviewType.BEHAVIORAL:
            return "Behavioral";
        case InterviewType.MIXED:
            return "Mixed";
        case InterviewType.GROUP_DISCUSSION:
            return "Group Discussion";
        case InterviewType.RAPID_FIRE:
            return "Rapid Fire";
        default:
            return "Practice";
    }
}

function formatInterviewMode(mode?: string | null) {
    switch (mode) {
        case InterviewMode.ONE_ON_ONE_AI:
            return "1:1 AI";
        case InterviewMode.PANEL_AI:
            return "Panel AI";
        case InterviewMode.HYBRID:
            return "Hybrid";
        default:
            return "Standard";
    }
}

function formatDifficulty(difficulty: string) {
    return difficulty.charAt(0) + difficulty.slice(1).toLowerCase();
}

function formatSessionDate(value?: string | null) {
    if (!value) return "Not started";
    return new Date(value).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
    });
}

function getSessionTimestamp(session: SessionListItem) {
    return new Date(session.endedAt ?? session.updatedAt ?? session.createdAt).getTime();
}

function reportHref(session: SessionListItem) {
    return `/dashboard/sessions/${session.id}`;
}

function scoreTone(score: number) {
    if (score >= 80) return "bg-emerald";
    if (score >= 60) return "bg-gold";
    return "bg-ruby";
}

export default function TopicDetailScreen() {
    const params = useParams<{ id: string }>();
    const topicId = params?.id;

    const { data: topicResponse, isLoading: isTopicLoading, isError: isTopicError } = useQuery({
        queryKey: ["topics", "detail", topicId],
        queryFn: () => topicsApi.getById(topicId),
        enabled: Boolean(topicId),
        staleTime: 60 * 1000,
    });

    const {
        data: sessionsResponse,
        isLoading: isSessionsLoading,
        isError: isSessionsError,
    } = useQuery({
        queryKey: ["sessions", "topic-detail", topicId],
        queryFn: () => sessionsApi.getSessions({ topicId, limit: 100 }),
        enabled: Boolean(topicId),
        staleTime: 60 * 1000,
    });

    const {
        data: topicAnalyticsResponse,
        isLoading: isTopicAnalyticsLoading,
        isError: isTopicAnalyticsError,
    } = useQuery({
        queryKey: ["analytics", "topic", topicId],
        queryFn: () => analyticsApi.getTopicAnalytics(topicId),
        enabled: Boolean(topicId),
        staleTime: 60 * 1000,
    });

    const topic = topicResponse?.data as TopicDto | undefined;
    const topicSessions = sessionsResponse?.data ?? [];
    const topicAnalytics = topicAnalyticsResponse?.data;

    const topicSignal = useMemo(() => {
        const now = Date.now();
        const oneWeekMs = 7 * 24 * 60 * 60 * 1000;
        const trend = topicAnalytics?.trend ?? [];

        return {
            sessionsThisWeek: topicSessions.filter((session) => now - getSessionTimestamp(session) <= oneWeekMs)
                .length,
            recentScoredSessions: trend.slice(-10),
            latestScore: topicAnalytics?.latestScore != null ? Math.round(topicAnalytics.latestScore) : null,
            scoreDelta: topicAnalytics?.scoreDelta != null ? Math.round(topicAnalytics.scoreDelta) : null,
        };
    }, [topicAnalytics, topicSessions]);

    if (isTopicLoading) {
        return (
            <div className="flex min-h-[50vh] items-center justify-center">
                <Loader2 className="animate-spin text-primary" size={40} />
            </div>
        );
    }

    if (isTopicError || !topic) {
        return (
            <div className="flex min-h-[50vh] flex-col items-center justify-center gap-3 text-center">
                <Layers size={28} className="text-muted-foreground" />
                <div className="space-y-1">
                    <p className="text-sm font-semibold text-foreground">Topic not found</p>
                    <p className="text-body-sm text-muted-foreground">
                        This topic is no longer available or you do not have access to it.
                    </p>
                </div>
                <Link href="/dashboard/topics" className={buttonStyles({ variant: "secondary", size: "sm" })}>
                    Back to Topics
                </Link>
            </div>
        );
    }

    const totalSessions = topicAnalytics?.totalSessions ?? topic.sessionCount ?? 0;
    const averageScore = topicAnalytics?.averageScore ?? topic.avgScore ?? 0;
    const hasScores = topicSignal.recentScoredSessions.length > 0;
    const lastSessionAt = topicAnalytics?.lastSessionAt ?? topic.lastSessionDate;
    const lastPracticed = lastSessionAt
        ? format(new Date(lastSessionAt), "MMM dd, yyyy")
        : "Never";
    const lastPracticedAgo = lastSessionAt
        ? formatDistanceToNow(new Date(lastSessionAt), { addSuffix: true })
        : "No history yet";
    const subtopicCount = topic.subtopics?.length ?? 0;

    return (
        <div className="flex-1 space-y-8 pb-12">
            <PageHeader
                eyebrow="Knowledge Map"
                title={topic.name}
                description={topic.description || "This topic is ready to anchor focused interview practice."}
                meta={
                    <>
                        <div className="inline-flex items-center rounded-full border border-border bg-card px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground shadow-card">
                            <Link href="/dashboard/topics" className="transition-colors hover:text-primary">
                                Topics
                            </Link>
                            <ChevronRight size={12} className="mx-2" />
                            <span className="text-foreground">{topic.name}</span>
                        </div>
                        <div className="inline-flex items-center rounded-full border border-border bg-card px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground shadow-card">
                            {topic.isGlobal ? "System Topic" : "Custom Topic"}
                        </div>
                        <div className="inline-flex items-center rounded-full border border-border bg-card px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground shadow-card">
                            {totalSessions} session{totalSessions === 1 ? "" : "s"}
                        </div>
                    </>
                }
                actions={
                    <Link href={`/dashboard/sessions/start?topicId=${topic.id}`} className={buttonStyles()}>
                        <Play size={16} />
                        Start Session
                    </Link>
                }
            />

            <Surface
                variant="hero"
                padding="xl"
                className="grid gap-6 lg:grid-cols-[minmax(0,1.4fr)_minmax(18rem,0.9fr)] lg:items-center"
            >
                <div className="space-y-3">
                    <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.22em] text-primary/80">
                        <Sparkles size={14} />
                        Topic Signal
                    </div>
                    <h2 className="font-display text-display-lg text-foreground">
                        {totalSessions > 0
                            ? `${topic.name} is ${averageScore >= 75 ? "holding up well" : averageScore >= 55 ? "still volatile" : "a clear recovery area"} in recent practice.`
                            : `You have not generated a practice signal for ${topic.name} yet.`}
                    </h2>
                    <p className="max-w-reading text-body-md text-muted-foreground">
                        {totalSessions > 0
                            ? `This view is built from topic analytics and recent session history so you can decide whether ${topic.name} needs another focused rep.`
                            : `Start a session from this topic to create the first real readiness signal and let the rest of the workspace react to it.`}
                    </p>
                </div>
                <Surface variant="subtle" padding="lg" className="border-primary/10 bg-primary/5">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-primary/80">
                        Topic Summary
                    </p>
                    <div className="mt-4 grid gap-4 sm:grid-cols-2">
                        <MetricMini label="Average score" value={hasScores ? `${Math.round(averageScore)}%` : "No scores yet"} />
                        <MetricMini label="Last practiced" value={lastPracticedAgo} />
                        <MetricMini
                            label="Parent topic"
                            value={topic.parentTopic?.name ?? "Standalone topic"}
                        />
                        <MetricMini label="Subtopics" value={subtopicCount} />
                    </div>
                </Surface>
            </Surface>

            <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
                <Surface padding="lg" className="relative overflow-hidden">
                    <div className="mb-4 flex items-start justify-between">
                        <h3 className="text-sm font-medium text-muted-foreground">Total Sessions</h3>
                        <CalendarDays className="text-muted-foreground" size={20} />
                    </div>
                    <div className="flex items-end gap-3">
                        <span className="text-4xl font-extrabold text-foreground">{totalSessions}</span>
                    </div>
                    <p className="mt-3 text-sm font-medium text-muted-foreground">
                        {topicSignal.sessionsThisWeek > 0
                            ? `${topicSignal.sessionsThisWeek} session${topicSignal.sessionsThisWeek === 1 ? "" : "s"} in the last 7 days`
                            : "No recent activity this week"}
                    </p>
                </Surface>

                <Surface padding="lg" className="relative overflow-hidden">
                    <div className="mb-4 flex items-start justify-between">
                        <h3 className="text-sm font-medium text-muted-foreground">Average Score</h3>
                        <BarChart2 className="text-primary/80" size={20} />
                    </div>
                    <div className="flex items-end gap-3">
                        <span className="text-4xl font-extrabold text-foreground">
                            {hasScores ? `${Math.round(averageScore)}%` : "-"}
                        </span>
                    </div>
                    <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-muted">
                        <div
                            className="h-full rounded-full bg-primary transition-all duration-700"
                            style={{ width: `${hasScores ? Math.round(averageScore) : 0}%` }}
                        />
                    </div>
                    <p className="mt-3 text-sm font-medium text-muted-foreground">
                        {topicSignal.scoreDelta == null
                            ? "Need at least two scored sessions for momentum"
                            : `${topicSignal.scoreDelta > 0 ? "+" : ""}${topicSignal.scoreDelta} pts from the previous scored session`}
                    </p>
                </Surface>

                <Surface padding="lg" className="relative overflow-hidden">
                    <div className="mb-4 flex items-start justify-between">
                        <h3 className="text-sm font-medium text-muted-foreground">Last Practiced</h3>
                        <Calendar className="text-muted-foreground" size={20} />
                    </div>
                    <div className="flex items-end gap-3">
                        <span className="text-2xl font-extrabold text-foreground">{lastPracticed}</span>
                    </div>
                    <p className="mt-3 text-sm font-medium text-muted-foreground">{lastPracticedAgo}</p>
                </Surface>
            </div>

            <Surface padding="xl">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                    <div>
                        <h2 className="font-display text-title-lg text-foreground">Recent score signal</h2>
                        <p className="mt-1 text-body-sm text-muted-foreground">
                            Up to the last 10 analyzed sessions for this topic.
                        </p>
                    </div>
                    {topicSignal.latestScore != null && (
                        <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 text-sm font-semibold text-foreground shadow-card">
                            <Clock3 size={14} className="text-primary" />
                            Latest score {topicSignal.latestScore}/100
                        </div>
                    )}
                </div>

                {isTopicAnalyticsLoading ? (
                    <div className="flex min-h-[260px] items-center justify-center">
                        <Loader2 className="animate-spin text-primary" size={24} />
                    </div>
                ) : isTopicAnalyticsError ? (
                    <EmptyPanel
                        title="Unable to load topic analytics"
                        description="The topic is available, but its historical score trend could not be loaded right now."
                    />
                ) : topicSignal.recentScoredSessions.length === 0 ? (
                    <EmptyPanel
                        title="No scored sessions yet"
                        description="Complete and analyze a session in this topic to see score movement over time."
                    />
                ) : (
                    <div className="mt-8 overflow-x-auto pb-2">
                        <div className="flex h-72 min-w-[32rem] items-end gap-3">
                            {topicSignal.recentScoredSessions.map((trendPoint) => {
                                const score = Math.round(trendPoint.overallScore);
                                const barHeight = Math.max(score, 8);

                                return (
                                    <div key={trendPoint.sessionId} className="flex flex-1 flex-col items-center gap-3">
                                        <div className="flex h-full w-full items-end">
                                            <div
                                                className={cn(
                                                    "w-full rounded-t-[1.25rem] transition-colors",
                                                    scoreTone(score)
                                                )}
                                                style={{ height: `${barHeight}%` }}
                                                title={`${score}/100`}
                                            />
                                        </div>
                                        <div className="text-center">
                                            <p className="text-xs font-semibold text-foreground">{score}</p>
                                            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                                                {format(new Date(trendPoint.analyzedAt), "MMM d")}
                                            </p>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}
            </Surface>

            <div className="space-y-4 pt-4">
                <div className="flex items-end justify-between gap-4">
                    <div>
                        <h2 className="font-display text-title-lg text-foreground">Recent session history</h2>
                        <p className="mt-1 text-body-sm text-muted-foreground">
                            The latest practice runs tied to this topic.
                        </p>
                    </div>
                    {topicSessions.length > 0 && (
                        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                            Showing {topicSessions.length}
                            {sessionsResponse?.meta?.total && sessionsResponse.meta.total > topicSessions.length
                                ? ` of ${sessionsResponse.meta.total}`
                                : ""}
                        </div>
                    )}
                </div>

                <Surface padding="none" className="overflow-hidden">
                    {isSessionsLoading ? (
                        <div className="flex min-h-[260px] items-center justify-center">
                            <Loader2 className="animate-spin text-primary" size={24} />
                        </div>
                    ) : isSessionsError ? (
                        <EmptyPanel
                            title="Session history unavailable"
                            description="Try refreshing this topic after the workspace reconnects to the sessions API."
                        />
                    ) : topicSessions.length === 0 ? (
                        <div className="flex min-h-[260px] flex-col items-center justify-center gap-4 px-6 text-center">
                            <div className="flex size-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                                <Layers size={20} />
                            </div>
                            <div className="space-y-1">
                                <p className="text-sm font-semibold text-foreground">No sessions for this topic yet</p>
                                <p className="max-w-reading text-body-sm text-muted-foreground">
                                    Start a session from this topic to create the first real record in its history.
                                </p>
                            </div>
                            <Link href={`/dashboard/sessions/start?topicId=${topic.id}`} className={buttonStyles({ size: "sm" })}>
                                Start Session
                            </Link>
                        </div>
                    ) : (
                        <>
                            <div className="overflow-x-auto">
                                <table className="w-full min-w-[860px] text-left text-sm">
                                    <thead className="bg-muted/40 text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                                        <tr>
                                            <th className="px-6 py-4">Date</th>
                                            <th className="px-6 py-4">Type</th>
                                            <th className="px-6 py-4">Format</th>
                                            <th className="px-6 py-4">Difficulty</th>
                                            <th className="px-6 py-4">Score</th>
                                            <th className="px-6 py-4">Duration</th>
                                            <th className="px-6 py-4">Status</th>
                                            <th className="px-6 py-4 text-right">Action</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-border">
                                        {topicSessions.map((session) => (
                                            <tr key={session.id} className="transition-colors hover:bg-muted/20">
                                                <td className="px-6 py-4 font-medium text-foreground">
                                                    {formatSessionDate(session.endedAt ?? session.updatedAt)}
                                                </td>
                                                <td className="px-6 py-4 text-muted-foreground">
                                                    {formatInterviewType(session.interviewType)}
                                                </td>
                                                <td className="px-6 py-4 text-muted-foreground">
                                                    {formatInterviewMode(session.interviewMode)}
                                                </td>
                                                <td className="px-6 py-4">
                                                    <span
                                                        className={cn(
                                                            "inline-flex rounded-full border px-2.5 py-1 text-[11px] font-semibold",
                                                            difficultyClasses[session.difficulty] ??
                                                                "border-border bg-muted text-muted-foreground"
                                                        )}
                                                    >
                                                        {formatDifficulty(session.difficulty)}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 font-semibold text-foreground">
                                                    {session.evaluation?.overallScore != null
                                                        ? `${Math.round(session.evaluation.overallScore)}/100`
                                                        : "Pending"}
                                                </td>
                                                <td className="px-6 py-4 text-muted-foreground">
                                                    {session.durationMinutes} min
                                                </td>
                                                <td className="px-6 py-4">
                                                    <span
                                                        className={cn(
                                                            "inline-flex rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em]",
                                                            statusClasses[session.status] ??
                                                                "border-border bg-muted text-muted-foreground"
                                                        )}
                                                    >
                                                        {session.status}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 text-right">
                                                    <Link
                                                        href={reportHref(session)}
                                                        className="inline-flex items-center gap-1 text-sm font-semibold text-primary transition-colors hover:text-primary-dark"
                                                    >
                                                        {session.status === SessionStatus.ANALYZED
                                                            ? "Open report"
                                                            : "Open session"}
                                                        <ArrowRight size={14} />
                                                    </Link>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                            <div className="border-t border-border/80 bg-muted/20 px-6 py-4 text-xs text-muted-foreground">
                                Recent history only. The topic aggregate above reflects the full dataset.
                            </div>
                        </>
                    )}
                </Surface>
            </div>
        </div>
    );
}

function MetricMini({ label, value }: { label: string; value: string | number }) {
    return (
        <div className="rounded-2xl border border-border bg-card px-4 py-3 shadow-card">
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                {label}
            </p>
            <p className="mt-1 text-sm font-semibold text-foreground">{value}</p>
        </div>
    );
}

function EmptyPanel({ title, description }: { title: string; description: string }) {
    return (
        <div className="flex min-h-[260px] flex-col items-center justify-center gap-3 px-6 text-center">
            <Layers size={28} className="text-muted-foreground" />
            <div className="space-y-1">
                <p className="text-sm font-semibold text-foreground">{title}</p>
                <p className="max-w-reading text-body-sm text-muted-foreground">{description}</p>
            </div>
        </div>
    );
}
