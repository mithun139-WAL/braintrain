"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
    Activity,
    AlertCircle,
    AlertTriangle,
    ArrowLeft,
    ArrowRight,
    Brain,
    Calendar,
    CheckCircle2,
    Code,
    Layers,
    Lightbulb,
    Loader2,
    MessageSquare,
    RotateCcw,
    Sparkles,
    Target,
    TrendingUp,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useEvaluation } from "@/hooks/queries/useEvaluation";
import { useAnalyzeSession } from "@/hooks/mutations/useAnalyzeSession";
import type { SessionEvaluationResponse } from "@braintrain/shared";

function scoreColor(score: number) {
    if (score >= 80) return "text-emerald-600 dark:text-emerald-400";
    if (score >= 60) return "text-amber-600 dark:text-amber-500";
    return "text-rose-600 dark:text-rose-400";
}

function barColor(score: number) {
    if (score >= 80) return "bg-emerald-500";
    if (score >= 60) return "bg-amber-500";
    return "bg-rose-500";
}

function formatDate(iso: string) {
    return new Date(iso).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
    });
}

function circleOffset(score: number) {
    const circumference = 283;
    return circumference - (score / 100) * circumference;
}

function DimCard({
    label,
    score,
    icon: Icon,
    description,
}: {
    label: string;
    score: number;
    icon: React.ElementType;
    description: string;
}) {
    const rounded = Math.round(score);

    return (
        <div
            className={cn(
                "rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition-all dark:border-gray-800 dark:bg-gray-900",
                rounded >= 80
                    ? "hover:border-emerald-500/30"
                    : rounded >= 60
                    ? "hover:border-amber-500/30"
                    : "hover:border-rose-500/30"
            )}
        >
            <div className="mb-4 flex items-start justify-between">
                <div className="flex items-center gap-3">
                    <div
                        className={cn(
                            "rounded-lg p-2.5",
                            rounded >= 80
                                ? "bg-emerald-100 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-500"
                                : rounded >= 60
                                ? "bg-amber-100 text-amber-600 dark:bg-amber-500/10 dark:text-amber-500"
                                : "bg-rose-100 text-rose-600 dark:bg-rose-500/10 dark:text-rose-400"
                        )}
                    >
                        <Icon size={20} />
                    </div>
                    <span className="font-bold text-slate-900 dark:text-white">{label}</span>
                </div>
                <span className={cn("text-xl font-black", scoreColor(rounded))}>{rounded}%</span>
            </div>
            <div className="mb-2 h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-gray-800">
                <div className={cn("h-2 rounded-full", barColor(rounded))} style={{ width: `${rounded}%` }} />
            </div>
            <p className="text-sm text-slate-500 dark:text-gray-400">{description}</p>
        </div>
    );
}

function AnalyzingState({ message }: { message: string }) {
    return (
        <div className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-gray-950">
            <div className="flex max-w-sm flex-col items-center gap-6 text-center">
                <div className="relative">
                    <div className="flex size-20 items-center justify-center rounded-full bg-primary/10">
                        <Brain size={36} className="text-primary" />
                    </div>
                    <div className="absolute -bottom-1 -right-1 flex size-8 items-center justify-center rounded-full bg-primary">
                        <Loader2 size={18} className="animate-spin text-white" />
                    </div>
                </div>
                <div className="space-y-2">
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-white">AI Analysis in Progress</h2>
                    <p className="text-sm leading-relaxed text-slate-500 dark:text-gray-400">{message}</p>
                </div>
                <div className="flex gap-1.5">
                    {[0, 1, 2].map((i) => (
                        <div
                            key={i}
                            className="size-2 animate-bounce rounded-full bg-primary"
                            style={{ animationDelay: `${i * 0.15}s` }}
                        />
                    ))}
                </div>
            </div>
        </div>
    );
}

export function SessionEvaluationView({ sessionId }: { sessionId: string }) {
    const [expandedQ, setExpandedQ] = useState<number | null>(0);
    const {
        data: evaluationResponse,
        isLoading: isLoadingEval,
        error: evalError,
    } = useEvaluation(sessionId);
    const analyzeSession = useAnalyzeSession();

    useEffect(() => {
        if (
            sessionId &&
            !isLoadingEval &&
            evalError &&
            !analyzeSession.isPending &&
            !analyzeSession.isSuccess &&
            !analyzeSession.isError
        ) {
            analyzeSession.mutate(sessionId);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [sessionId, isLoadingEval, evalError]);

    if (isLoadingEval || analyzeSession.isPending) {
        return (
            <AnalyzingState
                message={
                    analyzeSession.isPending
                        ? "Transcribing responses and evaluating your answers with GPT-4o-mini…"
                        : "Loading your evaluation report…"
                }
            />
        );
    }

    if (analyzeSession.isError && !evaluationResponse) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-gray-950">
                <div className="flex max-w-sm flex-col items-center gap-4 text-center">
                    <AlertCircle size={40} className="text-rose-500" />
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">Analysis Failed</h2>
                    <p className="text-sm text-slate-500 dark:text-gray-400">
                        Something went wrong generating your evaluation. Please try again.
                    </p>
                    <div className="flex flex-col gap-3 w-full">
                        <button
                            onClick={() => analyzeSession.mutate(sessionId)}
                            className="flex items-center justify-center gap-2 rounded-xl bg-primary px-6 py-2.5 text-sm font-semibold text-white w-full hover:bg-primary-dark transition-all"
                        >
                            <RotateCcw size={16} />
                            Retry Analysis
                        </button>
                        <Link href="/dashboard" className="w-full">
                            <button className="flex items-center justify-center gap-2 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-6 py-2.5 text-sm font-semibold text-slate-700 dark:text-slate-200 w-full hover:bg-slate-50 dark:hover:bg-gray-800 transition-all">
                                <ArrowLeft size={16} />
                                Back to Dashboard
                            </button>
                        </Link>
                    </div>
                </div>
            </div>
        );
    }

    const evaluation: SessionEvaluationResponse | undefined =
        evaluationResponse?.data ?? (analyzeSession.data?.data as SessionEvaluationResponse | undefined);

    if (!evaluation) {
        return null;
    }

    const overallRounded = Math.round(evaluation.overallScore);
    const dims = evaluation.dimensions;
    const dimensionCards = [
        {
            label: "Confidence",
            score: dims.confidence,
            icon: Activity,
            description:
                dims.confidence >= 75
                    ? "Strong vocal presence and self-assurance throughout."
                    : "Work on reducing hesitation and projecting certainty.",
        },
        {
            label: "Clarity",
            score: dims.clarity,
            icon: MessageSquare,
            description:
                dims.clarity >= 75
                    ? "Clear and easy-to-follow communication style."
                    : "Improve articulation and sentence structure.",
        },
        {
            label: "Structure",
            score: dims.structure,
            icon: Layers,
            description:
                dims.structure >= 75
                    ? "Well-organized answers with logical flow."
                    : "Use STAR format to add structure to your answers.",
        },
        {
            label: "Depth",
            score: dims.depth,
            icon: Code,
            description:
                dims.depth >= 75
                    ? "Detailed and specific examples provided."
                    : "Add more concrete details and technical specifics.",
        },
    ].concat(
        dims.technical !== undefined && dims.technical !== null
            ? [
                  {
                      label: "Technical",
                      score: dims.technical,
                      icon: Lightbulb,
                      description:
                          dims.technical >= 75
                              ? "Strong command of technical concepts."
                              : "Revisit core technical concepts for this domain.",
                  },
              ]
            : []
    );

    return (
        <div className="min-h-screen bg-background px-4 py-8 text-foreground sm:px-6 lg:px-8">
            <div className="mx-auto max-w-4xl space-y-8">
                <header className="flex flex-col gap-4 border-b border-border/60 pb-6 md:flex-row md:items-center md:justify-between">
                    <div className="space-y-1">
                        <div className="flex items-center gap-2 text-xs font-semibold text-primary uppercase tracking-wider">
                            <Calendar size={14} />
                            <span>{formatDate(evaluation.evaluatedAt)}</span>
                        </div>
                        <h1 className="text-2xl md:text-3xl font-semibold tracking-tight text-foreground">
                            AI Evaluation Report
                        </h1>
                        <p className="text-sm text-muted-foreground">
                            Overall Score: <span className="font-semibold text-foreground">{overallRounded}/100</span>
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <Link href="/dashboard">
                            <button className="flex h-9 items-center gap-1.5 rounded-lg border border-border bg-card px-4 text-xs font-semibold text-foreground hover:bg-muted/50 transition-colors">
                                <ArrowLeft size={14} />
                                <span>Dashboard</span>
                            </button>
                        </Link>
                        <Link href="/dashboard/sessions/start">
                            <button className="flex h-9 items-center gap-1.5 rounded-lg bg-primary px-4 text-xs font-semibold text-white hover:brightness-105 transition-all shadow-sm">
                                <RotateCcw size={14} />
                                <span>New Session</span>
                            </button>
                        </Link>
                    </div>
                </header>

                {/* 1. Human-readable Summary */}
                <div className="bg-card border border-border p-6 md:p-8 rounded-xl space-y-3">
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-primary">Executive Summary</h3>
                    <p className="text-base leading-relaxed text-foreground font-normal">
                        {evaluation.summary}
                    </p>
                </div>

                {/* 2 & 3. Strengths & Growth Areas */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Strengths */}
                    <div className="bg-card border border-border p-6 rounded-xl space-y-4">
                        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Key Strengths</h3>
                        <ul className="space-y-3">
                            {evaluation.strengths.map((str, idx) => (
                                <li key={idx} className="flex items-start gap-2.5 text-xs text-foreground leading-relaxed">
                                    <span className="size-1.5 rounded-full bg-emerald mt-1.5 shrink-0" />
                                    <span>{str}</span>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Growth Areas */}
                    <div className="bg-card border border-border p-6 rounded-xl space-y-4">
                        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Critical Focus Areas</h3>
                        <ul className="space-y-3">
                            {evaluation.improvements.map((imp, idx) => (
                                <li key={idx} className="flex items-start gap-2.5 text-xs text-foreground leading-relaxed">
                                    <span className="size-1.5 rounded-full bg-gold mt-1.5 shrink-0" />
                                    <span>{imp}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>

                {/* 4. Recommendations */}
                <div className="bg-card border border-border p-6 rounded-xl space-y-3">
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Next Suggested Steps</h3>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                        To build on this session's momentum, we recommend reviewing your response flow with the AI coach. Focus on structural completeness when detailing past technical decisions.
                    </p>
                    <div className="pt-2">
                        <Link
                            href="/dashboard/coach"
                            className="inline-flex h-9 items-center justify-center rounded-lg bg-primary/10 hover:bg-primary/15 px-4 text-xs font-semibold text-primary transition-colors"
                        >
                            Open AI Coaching Session
                        </Link>
                    </div>
                </div>

                {/* 5. Metrics & Subscores */}
                <div className="bg-card border border-border p-6 rounded-xl space-y-6">
                    <div>
                        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Performance Metrics</h3>
                        <p className="text-xs text-muted-foreground mt-1">Quantitative scoring of core communication components.</p>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-6 pt-2">
                        {dimensionCards.map((card) => (
                            <div key={card.label} className="space-y-2 border-b sm:border-b-0 sm:border-r border-border last:border-none pb-4 sm:pb-0 sm:pr-4">
                                <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider block">
                                    {card.label}
                                </span>
                                <div className="flex items-baseline gap-1">
                                    <span className="text-xl font-bold text-foreground">{Math.round(card.score)}</span>
                                    <span className="text-xs text-muted-foreground">/100</span>
                                </div>
                                <div className="h-1 w-full bg-muted rounded-full overflow-hidden">
                                    <div className="h-full bg-primary" style={{ width: `${card.score}%` }} />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Footer margin spacer */}
                <div className="h-8" />
            </div>
        </div>
    );
}
