"use client";

import Link from "next/link";
import { PageHeader } from "@/core/components/ui/PageHeader";
import { Surface } from "@/core/components/ui/Surface";
import { buttonStyles } from "@/core/components/ui/button";
import { StatCard } from "@/components/dashboard/StatCard";
import { PerformanceChart } from "@/components/dashboard/PerformanceChart";
import { RecentSessionsTable } from "@/components/dashboard/RecentSessionsTable";
import { useAnalytics, useProgression } from "@/hooks/queries/useAnalytics";
import { useGetProfile } from "@/hooks/queries/useGetProfile";
import {
    Activity,
    Smile,
    MessageSquare,
    Database,
    Zap,
    Lightbulb,
    Sparkles,
    Brain,
    ArrowRight,
    Compass,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function DashboardPage() {
    const { data: profileResponse } = useGetProfile();
    const { data: analyticsResponse, isLoading: analyticsLoading } = useAnalytics();
    const { data: progressionResponse } = useProgression();

    const user       = profileResponse?.data;
    const analytics  = analyticsResponse?.data;
    const progression = progressionResponse?.data;

    const displayName      = user?.displayName || user?.email?.split("@")[0] || "there";
    const overallScore     = analytics?.trend?.at(-1)?.overallScore ?? null;
    const confidenceScore  = analytics?.trend?.at(-1)?.confidenceScore ?? null;
    const clarityScore     = analytics?.trend?.at(-1)?.clarityScore ?? null;
    const depthScore       = analytics?.trend?.at(-1)?.depthScore ?? null;

    const overallDelta    = analytics?.improvement.overallDelta ?? 0;
    const confidenceDelta = analytics?.improvement.confidenceDelta ?? 0;
    const clarityDelta    = analytics?.improvement.clarityDelta ?? 0;

    const progressionDelta = progression?.delta;
    const hasImprovement   = progressionDelta !== undefined && progressionDelta !== null;

    const readinessScore = overallScore !== null ? Math.round(overallScore) : null;

    // Determine greeting
    const hour = new Date().getHours();
    const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

    const focusSignals = [
        analytics?.improvement.topWeakDimension
            ? {
                  tone: "bg-gold",
                  title: `Strengthen ${analytics.improvement.topWeakDimension}`,
                  body: "This dimension is dragging overall readiness the most right now.",
              }
            : null,
        analytics?.improvement.topImprovedDimension
            ? {
                  tone: "bg-emerald",
                  title: `${analytics.improvement.topImprovedDimension} is compounding`,
                  body: "This is becoming a repeatable strength. Keep reinforcing it.",
              }
            : null,
        {
            tone: "bg-sky-500",
            title: "Turn insight into drills",
            body: "Open your adaptive plan to turn the latest session signal into deliberate practice.",
        },
    ].filter(Boolean) as Array<{ tone: string; title: string; body: string }>;

    return (
        <div className="flex flex-col gap-6 pb-12">
            <PageHeader
                eyebrow={`${greeting}, ${displayName}`}
                title={
                    readinessScore !== null
                        ? `Your readiness is ${readinessScore}/100`
                        : "Start building your interview confidence"
                }
                description={
                    hasImprovement && progressionDelta! > 0
                        ? `You improved by +${progressionDelta!.toFixed(1)} points since your last session. Keep the momentum going with another focused practice run.`
                        : hasImprovement && progressionDelta! < 0
                        ? `Your score moved ${progressionDelta!.toFixed(1)} points from the previous session. Use the coach and plan to recover quickly.`
                        : analytics?.analyzedSessions && analytics.analyzedSessions > 0
                        ? `${analytics.analyzedSessions} analyzed sessions are shaping your practice loop. Review the signal, then act on the next best move.`
                        : "Run your first session to unlock readiness scoring, adaptive coaching, and a personalized training plan."
                }
                meta={
                    <>
                        <SignalPill label="Analyzed sessions" value={analytics?.analyzedSessions ?? 0} />
                        <SignalPill label="Current focus" value={analytics?.improvement.topWeakDimension ?? "Find first signal"} />
                        <SignalPill label="Momentum" value={hasImprovement ? `${progressionDelta! > 0 ? "+" : ""}${progressionDelta!.toFixed(1)} pts` : "No baseline yet"} />
                    </>
                }
                actions={
                    <>
                        <Link href="/dashboard/coach" className={buttonStyles({ variant: "secondary" })}>
                            <Compass size={16} />
                            Open Coach
                        </Link>
                        <Link href="/dashboard/sessions/start" className={buttonStyles()}>
                            <Zap size={16} />
                            Start Session
                        </Link>
                    </>
                }
            />

            <Surface variant="hero" padding="xl" className="relative overflow-hidden bg-background-dark text-white">
                <div className="absolute inset-0 pointer-events-none">
                    <div className="absolute right-[-8rem] top-[-8rem] h-72 w-72 rounded-full bg-primary/25 blur-3xl" />
                    <div className="absolute bottom-[-6rem] left-[20%] h-56 w-56 rounded-full bg-emerald/15 blur-3xl" />
                </div>
                <div className="relative grid gap-6 lg:grid-cols-[minmax(0,1.35fr)_minmax(20rem,0.95fr)] lg:items-center">
                    <div className="space-y-4">
                        <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-primary/80">
                            Mission Brief
                        </p>
                        <h2 className="max-w-2xl font-display text-display-lg text-white">
                            {readinessScore !== null
                                ? `You are ${readinessScore >= 75 ? "close to interview ready" : readinessScore >= 50 ? "building real momentum" : "still early in the climb"}.`
                                : "Your AI mentor is waiting for the first real signal."}
                        </h2>
                        <p className="max-w-reading text-body-md text-white/70">
                            {readinessScore !== null
                                ? "Use one more session to confirm whether your current trend is becoming a reliable strength or still volatile under pressure."
                                : "A single session is enough to generate your first readiness score, identify weak dimensions, and create an adaptive plan."}
                        </p>
                    </div>

                    <Surface variant="subtle" padding="lg" className="border-white/10 bg-white/5 backdrop-blur-xl">
                        <div className="space-y-4">
                            <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.22em] text-white/55">
                                <Lightbulb size={14} className="text-primary" />
                                AI Next Best Move
                            </div>
                            <div className="space-y-3">
                                {focusSignals.map((signal) => (
                                    <CoachTip key={signal.title} dot={signal.tone} title={signal.title} body={signal.body} />
                                ))}
                            </div>
                            <div className="flex flex-wrap gap-3 pt-2">
                                <Link href="/dashboard/training" className={cn(buttonStyles({ variant: "secondary", size: "sm" }), "border-white/10 bg-white/5 text-white hover:bg-white/10") }>
                                    <Sparkles size={14} />
                                    Open Plan
                                </Link>
                                <Link href="/dashboard/analytics" className={cn(buttonStyles({ variant: "ghost", size: "sm" }), "text-white/70 hover:bg-white/10 hover:text-white") }>
                                    View Insights
                                    <ArrowRight size={14} />
                                </Link>
                            </div>
                        </div>
                    </Surface>
                </div>
            </Surface>

            {/* ── Stat Cards ────────────────────────────────────────────── */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {analyticsLoading ? (
                    Array.from({ length: 4 }).map((_, i) => (
                        <div key={i} className="h-36 rounded-2xl bg-card border border-border animate-pulse" />
                    ))
                ) : (
                    <>
                        <StatCard
                            label="Overall Score"
                            value={overallScore !== null ? Math.round(overallScore) : "—"}
                            unit="/100"
                            trend={Math.round(overallDelta)}
                            icon={Activity}
                            iconColor="text-primary"
                            iconBg="bg-primary/10"
                            accentColor="bg-primary"
                        />
                        <StatCard
                            label="Confidence"
                            value={confidenceScore !== null ? Math.round(confidenceScore) : "—"}
                            unit="%"
                            trend={Math.round(confidenceDelta)}
                            icon={Smile}
                            iconColor="text-sky-500"
                            iconBg="bg-sky-500/10"
                            accentColor="bg-sky-500"
                        />
                        <StatCard
                            label="Clarity"
                            value={clarityScore !== null ? Math.round(clarityScore) : "—"}
                            unit="%"
                            trend={Math.round(clarityDelta)}
                            icon={MessageSquare}
                            iconColor="text-violet-500"
                            iconBg="bg-violet-500/10"
                            accentColor="bg-violet-500"
                        />
                        <StatCard
                            label="Technical Depth"
                            value={depthScore !== null ? Math.round(depthScore) : "—"}
                            unit="%"
                            trend={0}
                            icon={Database}
                            iconColor="text-amber-500"
                            iconBg="bg-amber-500/10"
                            accentColor="bg-amber-500"
                        />
                    </>
                )}
            </div>

            {/* ── Main Content Grid ─────────────────────────────────────── */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                {/* Chart */}
                <div className="lg:col-span-2">
                    <PerformanceChart trend={analytics?.trend} />
                </div>

                {/* AI Coaching Panel */}
                <Surface padding="none" className="lg:col-span-1 flex flex-col overflow-hidden">
                    <div className="flex items-center justify-between border-b border-border px-5 pb-4 pt-5">
                        <div className="flex items-center gap-2">
                            <div className="size-7 rounded-lg bg-primary/10 flex items-center justify-center">
                                <Lightbulb size={15} className="text-primary" />
                            </div>
                            <h3 className="text-sm font-bold text-foreground">AI Coaching</h3>
                        </div>
                        <Link
                            href="/dashboard/coach"
                            className="text-xs font-semibold text-primary hover:text-primary-dark transition-colors flex items-center gap-1"
                        >
                            Open Coach
                            <ArrowRight size={12} />
                        </Link>
                    </div>

                    <div className="flex flex-col gap-2 p-4 flex-1">
                        {focusSignals.map((signal) => (
                            <CoachTip key={`panel-${signal.title}`} dot={signal.tone} title={signal.title} body={signal.body} />
                        ))}

                        {/* Empty state */}
                        {(!analytics || analytics.totalSessions === 0) && (
                            <div className="flex-1 flex flex-col items-center justify-center text-center py-8 px-4">
                                <div className="size-10 rounded-xl bg-muted flex items-center justify-center mb-3">
                                    <Brain size={20} className="text-muted-foreground" />
                                </div>
                                <p className="text-xs text-muted-foreground font-medium leading-relaxed">
                                    Complete your first session to unlock personalised AI coaching insights.
                                </p>
                            </div>
                        )}

                    </div>

                    <div className="p-4 pt-2 border-t border-border">
                        <Link href="/dashboard/training" className={cn(buttonStyles({ variant: "secondary", size: "sm", fullWidth: true }), "border-dashed") }>
                            <Sparkles size={13} />
                            View Training Plan
                        </Link>
                    </div>
                </Surface>
            </div>

            {/* ── Recent Sessions ───────────────────────────────────────── */}
            <RecentSessionsTable />
        </div>
    );
}

// ── Sub-component: coaching tip card ──────────────────────────────────────
function CoachTip({
    dot,
    title,
    body,
}: {
    dot:   string;
    title: string;
    body:  string;
}) {
    return (
        <div className="flex items-start gap-3 rounded-2xl border border-border-subtle bg-muted/40 p-3.5 transition-all hover:border-border group">
            <div className={`mt-1.5 size-1.5 rounded-full flex-shrink-0 ${dot}`} />
            <div>
                <p className="text-xs font-semibold text-foreground mb-0.5 capitalize">{title}</p>
                <p className="text-[11px] text-muted-foreground leading-relaxed">{body}</p>
            </div>
        </div>
    );
}

function SignalPill({ label, value }: { label: string; value: string | number }) {
    return (
        <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 text-sm text-foreground shadow-card">
            <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                {label}
            </span>
            <span className="font-semibold text-foreground">{value}</span>
        </div>
    );
}
