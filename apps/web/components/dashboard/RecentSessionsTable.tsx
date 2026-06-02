"use client";

import Link from "next/link";
import { useState } from "react";
import {
    ArrowRight,
    Filter,
    ChevronDown,
    Loader2,
    Brain,
    CheckCircle2,
} from "lucide-react";
import { Difficulty, InterviewType, SessionStatus } from "@braintrain/shared";
import { sessionsApi, type SessionListItem } from "@/lib/api/sessions.api";
import { cn } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";
import { buttonStyles } from "@/core/components/ui/button";
import { Surface } from "@/core/components/ui/Surface";

type SessionFilter = "ALL" | SessionStatus;

const FILTER_OPTIONS: Array<{ label: string; value: SessionFilter }> = [
    { label: "All sessions", value: "ALL" },
    { label: "Active", value: SessionStatus.ACTIVE },
    { label: "Completed", value: SessionStatus.COMPLETED },
    { label: "Analyzed", value: SessionStatus.ANALYZED },
];

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

function formatDifficulty(difficulty: string) {
    return difficulty.charAt(0) + difficulty.slice(1).toLowerCase();
}

function formatDate(value?: string | null) {
    if (!value) return "Not started";
    return new Date(value).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
    });
}

function reportHref(session: SessionListItem) {
    return `/dashboard/sessions/${session.id}`;
}

export function RecentSessionsTable({
    title = "Recent Practice Sessions",
    description = "Review your latest sessions, current status, and available reports.",
    limit = 8,
}: {
    title?: string;
    description?: string;
    limit?: number;
}) {
    const [statusFilter, setStatusFilter] = useState<SessionFilter>("ALL");

    const { data, isLoading, isError } = useQuery({
        queryKey: ["sessions", "list", statusFilter, limit],
        queryFn: () =>
            sessionsApi.getSessions({
                status: statusFilter === "ALL" ? undefined : statusFilter,
                limit,
            }),
        staleTime: 60 * 1000,
    });

    const sessions = data?.data ?? [];

    return (
        <Surface padding="none" className="overflow-hidden">
            <div className="flex flex-col gap-4 border-b border-border/80 px-6 py-6 sm:flex-row sm:items-start sm:justify-between">
                <div>
                    <h3 className="font-display text-title-md text-foreground">{title}</h3>
                    <p className="mt-1 text-body-sm text-muted-foreground">{description}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                    <div className="relative">
                        <Filter size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                        <select
                            value={statusFilter}
                            onChange={(event) => setStatusFilter(event.target.value as SessionFilter)}
                            className="h-10 appearance-none rounded-2xl border border-border bg-card pl-9 pr-10 text-sm font-medium text-foreground outline-none transition-colors hover:border-border focus:border-primary"
                            aria-label="Filter sessions by status"
                        >
                            {FILTER_OPTIONS.map((option) => (
                                <option key={option.value} value={option.value}>
                                    {option.label}
                                </option>
                            ))}
                        </select>
                        <ChevronDown size={14} className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                    </div>
                    <Link href="/dashboard/sessions" className={buttonStyles({ variant: "secondary", size: "sm" })}>
                        View All
                    </Link>
                </div>
            </div>

            {isLoading ? (
                <div className="flex min-h-[260px] items-center justify-center">
                    <div className="flex items-center gap-3 text-body-sm text-muted-foreground">
                        <Loader2 size={18} className="animate-spin text-primary" />
                        Loading sessions...
                    </div>
                </div>
            ) : isError ? (
                <div className="flex min-h-[260px] flex-col items-center justify-center gap-3 px-6 text-center">
                    <Brain size={28} className="text-muted-foreground" />
                    <div className="space-y-1">
                        <p className="text-sm font-semibold text-foreground">Unable to load sessions</p>
                        <p className="text-body-sm text-muted-foreground">
                            Try again in a moment or start a new session to refresh the workspace.
                        </p>
                    </div>
                </div>
            ) : sessions.length === 0 ? (
                <div className="flex min-h-[260px] flex-col items-center justify-center gap-4 px-6 text-center">
                    <div className="flex size-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                        <CheckCircle2 size={20} />
                    </div>
                    <div className="space-y-1">
                        <p className="text-sm font-semibold text-foreground">No sessions in this view yet</p>
                        <p className="max-w-reading text-body-sm text-muted-foreground">
                            Start a session to create a fresh signal, then return here to review progress and reports.
                        </p>
                    </div>
                    <Link href="/dashboard/sessions/start" className={buttonStyles({ size: "sm" })}>
                        Start Session
                    </Link>
                </div>
            ) : (
                <>
                    <div className="overflow-x-auto">
                        <table className="w-full min-w-[720px] text-left">
                            <thead>
                                <tr className="border-b border-border/80 bg-muted/40 text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                                    <th className="px-6 py-4">Session</th>
                                    <th className="px-6 py-4">Status</th>
                                    <th className="px-6 py-4">Difficulty</th>
                                    <th className="px-6 py-4">Questions</th>
                                    <th className="px-6 py-4">Score</th>
                                    <th className="px-6 py-4">Updated</th>
                                    <th className="px-6 py-4 text-right">Action</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border/70 text-sm">
                                {sessions.map((session) => (
                                    <tr key={session.id} className="group transition-colors hover:bg-muted/20">
                                        <td className="px-6 py-4 align-top">
                                            <div className="space-y-1">
                                                <p className="font-semibold text-foreground">
                                                    {session.topic?.name ?? formatInterviewType(session.interviewType)}
                                                </p>
                                                <p className="text-body-sm text-muted-foreground">
                                                    {formatInterviewType(session.interviewType)} · {session.durationMinutes} min
                                                </p>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 align-top">
                                            <span
                                                className={cn(
                                                    "inline-flex rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em]",
                                                    statusClasses[session.status] ?? "border-border bg-muted text-muted-foreground"
                                                )}
                                            >
                                                {session.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 align-top">
                                            <span
                                                className={cn(
                                                    "inline-flex rounded-full border px-2.5 py-1 text-[11px] font-semibold",
                                                    difficultyClasses[session.difficulty] ?? "border-border bg-muted text-muted-foreground"
                                                )}
                                            >
                                                {formatDifficulty(session.difficulty)}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 align-top font-medium text-foreground">
                                            {session.questionCount}
                                        </td>
                                        <td className="px-6 py-4 align-top">
                                            <span className="font-semibold text-foreground">
                                                {session.evaluation?.overallScore != null
                                                    ? `${Math.round(session.evaluation.overallScore)}/100`
                                                    : "Pending"}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 align-top text-body-sm text-muted-foreground">
                                            {formatDate(session.endedAt ?? session.updatedAt)}
                                        </td>
                                        <td className="px-6 py-4 text-right align-top">
                                            <Link
                                                href={reportHref(session)}
                                                className="inline-flex items-center gap-1 text-sm font-semibold text-primary transition-colors hover:text-primary-dark"
                                            >
                                                {session.status === SessionStatus.ANALYZED ? "Open report" : "Open session"}
                                                <ArrowRight size={14} />
                                            </Link>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    <div className="border-t border-border/80 bg-muted/20 px-6 py-4 text-xs text-muted-foreground">
                        Showing {sessions.length} session{sessions.length === 1 ? "" : "s"}
                        {data?.meta?.total ? ` of ${data.meta.total}` : ""}.
                    </div>
                </>
            )}
        </Surface>
    );
}
