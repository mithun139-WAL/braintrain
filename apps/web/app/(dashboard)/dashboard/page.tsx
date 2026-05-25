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

    const isPro = user?.planType === "PRO";

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
        isPro
            ? {
                  tone: "bg-sky-500",
                  title: "Turn insight into drills",
                  body: "Open your adaptive plan to turn the latest session signal into deliberate practice.",
              }
            : null,
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
                        ? isPro
                            ? `Your score moved ${progressionDelta!.toFixed(1)} points from the previous session. Use the coach and plan to recover quickly.`
                            : `Your score moved ${progressionDelta!.toFixed(1)} points from the previous session. Practice again to recover quickly.`
                        : analytics?.analyzedSessions && analytics.analyzedSessions > 0
                        ? `${analytics.analyzedSessions} analyzed sessions are shaping your practice loop. Review the signal, then act on the next best move.`
                        : isPro
                        ? "Run your first session to unlock readiness scoring, adaptive coaching, and a personalized training plan."
                        : "Run your first session to unlock readiness scoring and start practicing."
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
                        {isPro && (
                            <Link href="/dashboard/coach" className={buttonStyles({ variant: "secondary" })}>
                                <Compass size={16} />
                                Open Coach
                            </Link>
                        )}
                        <Link href="/dashboard/sessions/start" className={buttonStyles()}>
                            <Zap size={16} />
                            Start Session
                        </Link>
                    </>
                }
            />

            <Surface variant="default" padding="lg" className="relative overflow-hidden bg-card">
                <div className="relative grid gap-6 lg:grid-cols-[minmax(0,1.35fr)_minmax(20rem,0.95fr)] lg:items-center">
                    <div className="space-y-3">
                        <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-primary">
                            Status Overview
                        </p>
                        <h2 className="max-w-2xl font-display text-display-md text-foreground">
                            {readinessScore !== null
                                ? `You are ${readinessScore >= 75 ? "close to interview ready" : readinessScore >= 50 ? "building real momentum" : "still early in the climb"}.`
                                : "Your AI mentor is waiting for the first real signal."}
                        </h2>
                        <p className="max-w-reading text-body-sm text-muted-foreground">
                            {readinessScore !== null
                                ? "Use one more session to confirm whether your current trend is becoming a reliable strength or still volatile under pressure."
                                : isPro
                                ? "A single session is enough to generate your first readiness score, identify weak dimensions, and create an adaptive plan."
                                : "A single session is enough to generate your first readiness score and identify weak dimensions."}
                        </p>
                    </div>

                    <Surface variant="subtle" padding="md" className="border-border bg-muted/40">
                        <div className="space-y-4">
                            <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground">
                                <Lightbulb size={13} className="text-primary" />
                                AI Next Best Move
                            </div>
                            <div className="space-y-2">
                                {focusSignals.map((signal) => (
                                    <CoachTip key={signal.title} dot={signal.tone} title={signal.title} body={signal.body} />
                                ))}
                            </div>
                            <div className="flex flex-wrap gap-2 pt-1">
                                {isPro && (
                                    <Link href="/dashboard/training" className={cn(buttonStyles({ variant: "secondary", size: "sm" }), "rounded-md border-border bg-card hover:bg-muted") }>
                                        <Sparkles size={12} />
                                        Open Plan
                                    </Link>
                                )}
                                <Link href="/dashboard/analytics" className={cn(buttonStyles({ variant: "ghost", size: "sm" }), "text-muted-foreground hover:text-foreground") }>
                                    View Insights
                                    <ArrowRight size={12} />
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
                        <div key={i} className="h-32 rounded-xl bg-card border border-border animate-pulse" />
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
                            iconColor="text-primary"
                            iconBg="bg-primary/10"
                            accentColor="bg-primary"
                        />
                        <StatCard
                            label="Clarity"
                            value={clarityScore !== null ? Math.round(clarityScore) : "—"}
                            unit="%"
                            trend={Math.round(clarityDelta)}
                            icon={MessageSquare}
                            iconColor="text-primary"
                            iconBg="bg-primary/10"
                            accentColor="bg-primary"
                        />
                        <StatCard
                            label="Technical Depth"
                            value={depthScore !== null ? Math.round(depthScore) : "—"}
                            unit="%"
                            trend={0}
                            icon={Database}
                            iconColor="text-primary"
                            iconBg="bg-primary/10"
                            accentColor="bg-primary"
                        />
                    </>
                )}
            </div>

            {/* ── Main Content Grid ─────────────────────────────────────── */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                {/* Chart */}
                <div className={cn(isPro ? "lg:col-span-2" : "lg:col-span-3")}>
                    <PerformanceChart trend={analytics?.trend} />
                </div>

                {/* AI Coaching Panel */}
                {isPro && (
                    <Surface padding="none" className="lg:col-span-1 flex flex-col overflow-hidden bg-card border border-border rounded-xl">
                        <div className="flex items-center justify-between border-b border-border px-5 py-4">
                            <div className="flex items-center gap-2">
                                <div className="size-6 rounded bg-primary/10 flex items-center justify-center text-primary">
                                    <Lightbulb size={13} />
                                </div>
                                <h3 className="text-xs font-semibold uppercase tracking-wider text-foreground">AI Coaching</h3>
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
                                    <div className="size-10 rounded bg-muted flex items-center justify-center mb-3 text-muted-foreground">
                                        <Brain size={18} />
                                    </div>
                                    <p className="text-xs text-muted-foreground font-medium leading-relaxed">
                                        Complete your first session to unlock personalized AI coaching insights.
                                    </p>
                                </div>
                            )}

                        </div>

                        <div className="p-4 border-t border-border bg-muted/20">
                            <Link href="/dashboard/training" className={cn(buttonStyles({ variant: "secondary", size: "sm", fullWidth: true }), "border-dashed rounded-md bg-card") }>
                                <Sparkles size={12} />
                                View Training Plan
                            </Link>
                        </div>
                    </Surface>
                )}
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
