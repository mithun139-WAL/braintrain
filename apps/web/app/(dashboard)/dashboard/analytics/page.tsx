"use client";

import Link from "next/link";
import { AlertCircle, ArrowRight, Brain, CheckCircle2, LayoutDashboard, Loader2, Sparkles, Target, TrendingUp } from "lucide-react";
import { PageHeader } from "@/core/components/ui/PageHeader";
import { Surface } from "@/core/components/ui/Surface";
import { buttonStyles } from "@/core/components/ui/button";
import { StatCard } from "@/components/dashboard/StatCard";
import TrendChart from "@/components/analytics/TrendChart";
import { useAnalytics } from "@/hooks/queries/useAnalytics";
import { cn } from "@/lib/utils";

export default function AnalyticsPage() {
    const { data: analyticsResponse, isLoading, error } = useAnalytics();
    const analytics = analyticsResponse?.data;

    const latestTrend = analytics?.trend?.at(-1);
    const avgOverallScore =
        analytics && analytics.trend.length > 0
            ? Math.round(analytics.trend.reduce((sum, item) => sum + item.overallScore, 0) / analytics.trend.length)
            : null;

    const weaknesses: Array<{ title: string; desc: string; tone: string }> = [];
    if (analytics?.improvement.topWeakDimension) {
        weaknesses.push({
            title:
                analytics.improvement.topWeakDimension.charAt(0).toUpperCase() +
                analytics.improvement.topWeakDimension.slice(1),
            desc: "Consistent weakness across recent analyzed sessions.",
            tone: "bg-ruby",
        });
    }
    if (latestTrend?.structureScore != null && latestTrend.structureScore < 60) {
        weaknesses.push({
            title: "Answer Structure",
            desc: "Responses still need clearer sequencing and stronger framing.",
            tone: "bg-gold",
        });
    }
    if (latestTrend?.depthScore != null && latestTrend.depthScore < 60) {
        weaknesses.push({
            title: "Technical Depth",
            desc: "Answers need more specificity, implementation detail, or trade-off reasoning.",
            tone: "bg-primary",
        });
    }

    return (
        <div className="flex w-full flex-col gap-8 pb-12">
            <PageHeader
                eyebrow="Insight Mode"
                title="Performance insights"
                description="See how readiness changes over time, where your answers still break down, and which topics deserve the next focused rep."
                meta={
                    analytics ? (
                        <>
                            <InsightMeta label="Analyzed" value={`${analytics.analyzedSessions}`} />
                            <InsightMeta label="Average score" value={avgOverallScore != null ? `${avgOverallScore}/100` : "-"} />
                            <InsightMeta label="Top weakness" value={analytics.improvement.topWeakDimension ?? "Not enough data"} />
                        </>
                    ) : null
                }
                actions={
                    <>
                        <Link href="/dashboard/training" className={buttonStyles({ variant: "secondary" })}>
                            <Sparkles size={16} />
                            Open Plan
                        </Link>
                        <Link href="/dashboard/sessions/start" className={buttonStyles()}>
                            New Session
                        </Link>
                    </>
                }
            />

            {isLoading ? (
                <div className="flex h-64 items-center justify-center">
                    <Loader2 className="animate-spin text-primary" size={36} />
                </div>
            ) : error || !analytics ? (
                <Surface padding="xl" className="flex min-h-[24rem] flex-col items-center justify-center gap-4 text-center">
                    <div className="flex size-14 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                        <Brain size={24} />
                    </div>
                    <div className="space-y-1">
                        <p className="text-sm font-semibold text-foreground">No insight signal yet</p>
                        <p className="max-w-reading text-body-sm text-muted-foreground">
                            Complete at least one analyzed session to unlock trend lines, topic breakdowns, and coach-ready focus areas.
                        </p>
                    </div>
                    <Link href="/dashboard/sessions/start" className={buttonStyles({ size: "sm" })}>
                        Start First Session
                    </Link>
                </Surface>
            ) : (
                <>
                    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
                        <StatCard
                            label="Average Score"
                            value={avgOverallScore ?? "—"}
                            unit="%"
                            trend={Math.round(analytics.improvement.overallDelta)}
                            icon={Target}
                            iconColor="text-primary"
                            iconBg="bg-primary/10"
                        />
                        <StatCard
                            label="Total Sessions"
                            value={analytics.totalSessions}
                            unit="total"
                            trend={0}
                            icon={LayoutDashboard}
                            iconColor="text-sky-500"
                            iconBg="bg-sky-500/10"
                            accentColor="bg-sky-500"
                        />
                        <StatCard
                            label="Improvement"
                            value={`${analytics.improvement.overallDelta > 0 ? "+" : ""}${analytics.improvement.overallDelta.toFixed(1)}`}
                            unit="pts"
                            trend={Math.round(analytics.improvement.overallDelta)}
                            icon={TrendingUp}
                            iconColor="text-emerald"
                            iconBg="bg-emerald/10"
                            accentColor="bg-emerald"
                        />
                        <StatCard
                            label="Focus Areas"
                            value={weaknesses.length || "—"}
                            unit="areas"
                            trend={0}
                            icon={AlertCircle}
                            iconColor="text-ruby"
                            iconBg="bg-ruby/10"
                            accentColor="bg-ruby"
                        />
                    </div>

                    <Surface variant="hero" padding="xl" className="grid gap-6 lg:grid-cols-[minmax(0,1.45fr)_minmax(18rem,0.85fr)] lg:items-center">
                        <div className="space-y-3">
                            <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-primary/80">Readiness Story</p>
                            <h2 className="font-display text-display-lg text-foreground">
                                {analytics.improvement.overallDelta > 0
                                    ? `Your readiness is compounding by ${analytics.improvement.overallDelta.toFixed(1)} points across analyzed sessions.`
                                    : analytics.improvement.overallDelta < 0
                                    ? `Recent sessions show a ${Math.abs(analytics.improvement.overallDelta).toFixed(1)} point regression that needs active recovery.`
                                    : "Your readiness is holding steady, but the next few reps will determine whether it compounds or stalls."}
                            </h2>
                            <p className="max-w-reading text-body-md text-muted-foreground">
                                Use the trend and topic breakdown below to decide whether to reinforce a growing strength or interrupt a recurring weak pattern before it calcifies.
                            </p>
                        </div>
                        <Surface variant="subtle" padding="lg" className="border-primary/10 bg-primary/5">
                            <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-primary/80">Current signal</p>
                            <div className="mt-4 grid gap-4 sm:grid-cols-2">
                                <InsightMini label="Latest score" value={latestTrend ? `${Math.round(latestTrend.overallScore)}/100` : "-"} />
                                <InsightMini label="Top topic" value={analytics.byTopic[0]?.topicName ?? "No ranking yet"} />
                                <InsightMini label="Top strength" value={analytics.improvement.topImprovedDimension ?? "Still emerging"} />
                                <InsightMini label="Coach focus" value={analytics.improvement.topWeakDimension ?? "Collect more data"} />
                            </div>
                        </Surface>
                    </Surface>

                    <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
                        <Surface padding="lg" className="flex flex-col lg:col-span-2">
                            <div className="pb-6">
                                <h3 className="font-display text-title-md text-foreground">Performance Trend</h3>
                                <p className="mt-1 text-body-sm text-muted-foreground">
                                    Overall score movement across your analyzed session history.
                                </p>
                            </div>
                            <div className="min-h-[350px] flex-1 w-full">
                                <TrendChart data={analytics.trend} />
                            </div>
                        </Surface>

                        <div className="flex flex-col gap-6">
                            <Surface padding="lg" className="flex flex-col">
                                <div className="pb-4">
                                    <h3 className="font-display text-title-md text-foreground">Focus Areas</h3>
                                    <p className="mt-1 text-body-sm text-muted-foreground">
                                        The signals most likely to change your next readiness score.
                                    </p>
                                </div>

                                {weaknesses.length > 0 ? (
                                    <div className="space-y-3">
                                        {weaknesses.map((weakness) => (
                                            <div
                                                key={weakness.title}
                                                className="flex items-start gap-3 rounded-2xl border border-border bg-muted/20 p-4"
                                            >
                                                <div className={cn("mt-1 size-2 rounded-full", weakness.tone)} />
                                                <div className="space-y-1">
                                                    <p className="text-sm font-semibold text-foreground">{weakness.title}</p>
                                                    <p className="text-body-sm text-muted-foreground">{weakness.desc}</p>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="flex flex-col items-center justify-center py-8 text-center">
                                        <CheckCircle2 size={32} className="mb-2 text-emerald" />
                                        <p className="text-sm font-medium text-foreground/80">No major weaknesses detected yet.</p>
                                        <p className="mt-1 text-xs text-muted-foreground">
                                            Complete more sessions for a sharper breakdown.
                                        </p>
                                    </div>
                                )}
                            </Surface>

                            <Surface padding="lg" className="space-y-4">
                                <div>
                                    <h3 className="font-display text-title-md text-foreground">Next best move</h3>
                                    <p className="mt-1 text-body-sm text-muted-foreground">
                                        Turn insight into a concrete practice action.
                                    </p>
                                </div>
                                <Link href="/dashboard/training" className={cn(buttonStyles({ variant: "secondary", size: "sm", fullWidth: true }), "justify-between")}>
                                    Open adaptive plan
                                    <ArrowRight size={14} />
                                </Link>
                                <Link href="/dashboard/coach" className={cn(buttonStyles({ variant: "ghost", size: "sm", fullWidth: true }), "justify-between")}>
                                    Ask the coach about this pattern
                                    <ArrowRight size={14} />
                                </Link>
                            </Surface>
                        </div>
                    </div>

                    <Surface padding="lg" className="space-y-4">
                        <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                            <div>
                                <h3 className="font-display text-title-md text-foreground">Topic Breakdown</h3>
                                <p className="mt-1 text-body-sm text-muted-foreground">
                                    The strongest and weakest topics currently shaping your readiness curve.
                                </p>
                            </div>
                            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                                {analytics.byTopic.length} ranked topic{analytics.byTopic.length === 1 ? "" : "s"}
                            </div>
                        </div>

                        {analytics.byTopic.length > 0 ? (
                            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                                {analytics.byTopic.slice(0, 6).map((topic) => (
                                    <Link key={topic.topicId} href={`/dashboard/topics/${topic.topicId}`}>
                                        <div className="rounded-3xl border border-border bg-muted/20 p-5 transition-colors hover:border-primary/20 hover:bg-primary/5">
                                            <div className="flex items-start justify-between gap-4">
                                                <div>
                                                    <p className="text-sm font-semibold text-foreground">{topic.topicName}</p>
                                                    <p className="mt-1 text-body-sm text-muted-foreground">
                                                        {topic.sessionCount} analyzed session{topic.sessionCount === 1 ? "" : "s"}
                                                    </p>
                                                </div>
                                                <span className="text-sm font-bold text-foreground">
                                                    {Math.round(topic.avgOverallScore)}
                                                </span>
                                            </div>
                                            <div className="mt-4 h-2 overflow-hidden rounded-full bg-background">
                                                <div
                                                    className={cn(
                                                        "h-full rounded-full",
                                                        topic.avgOverallScore >= 70
                                                            ? "bg-emerald"
                                                            : topic.avgOverallScore >= 50
                                                            ? "bg-gold"
                                                            : "bg-ruby"
                                                    )}
                                                    style={{ width: `${topic.avgOverallScore}%` }}
                                                />
                                            </div>
                                        </div>
                                    </Link>
                                ))}
                            </div>
                        ) : (
                            <div className="rounded-3xl border border-dashed border-border bg-muted/20 px-6 py-12 text-center">
                                <p className="text-sm font-semibold text-foreground">No topic breakdown yet</p>
                                <p className="mt-1 text-body-sm text-muted-foreground">
                                    Finish analyzed sessions across a few topics to see where your practice is strongest and most fragile.
                                </p>
                            </div>
                        )}
                    </Surface>
                </>
            )}
        </div>
    );
}

function InsightMeta({ label, value }: { label: string; value: string }) {
    return (
        <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 text-sm text-foreground shadow-card">
            <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">{label}</span>
            <span className="font-semibold text-foreground">{value}</span>
        </div>
    );
}

function InsightMini({ label, value }: { label: string; value: string }) {
    return (
        <div className="rounded-2xl border border-border bg-card px-4 py-3 shadow-card">
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">{label}</p>
            <p className="mt-1 text-sm font-semibold text-foreground">{value}</p>
        </div>
    );
}
