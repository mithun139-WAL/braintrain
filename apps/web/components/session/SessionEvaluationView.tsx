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
        <div className="min-h-screen bg-slate-50 px-4 py-8 text-slate-900 dark:bg-gray-950 dark:text-gray-100 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-7xl space-y-8">
                <header className="flex flex-col gap-6 border-b border-gray-200 pb-6 dark:border-gray-800 md:flex-row md:items-end md:justify-between">
                    <div className="space-y-2">
                        <div className="flex items-center gap-2 text-sm font-semibold text-primary dark:text-indigo-400">
                            <Calendar size={16} />
                            <span>{formatDate(evaluation.evaluatedAt)}</span>
                        </div>
                        <h1 className="text-3xl font-black tracking-tight text-slate-900 dark:text-white md:text-4xl">
                            AI Evaluation Report
                        </h1>
                        <p className="font-medium text-slate-500 dark:text-gray-400">
                            {evaluation.summary.slice(0, 100)}
                            {evaluation.summary.length > 100 ? "…" : ""}
                        </p>
                    </div>
                    <div className="flex gap-3">
                        <Link href="/dashboard">
                            <button className="flex items-center gap-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm font-bold text-slate-700 dark:text-slate-200 transition-all hover:bg-slate-50 dark:hover:bg-gray-800">
                                <ArrowLeft size={18} />
                                <span>Back to Dashboard</span>
                            </button>
                        </Link>
                        <Link href="/dashboard/sessions/start">
                            <button className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-bold text-white shadow-md shadow-primary/20 transition-all hover:bg-primary-dark">
                                <RotateCcw size={18} />
                                <span>New Session</span>
                            </button>
                        </Link>
                    </div>
                </header>

                <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
                    <div className="relative overflow-hidden rounded-2xl border border-gray-200 bg-white p-8 shadow-sm dark:border-gray-800 dark:bg-gray-900 lg:col-span-4">
                        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent opacity-50" />
                        <h3 className="z-10 mb-6 flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-gray-400">
                            <Activity size={16} className="text-primary" />
                            Overall Performance Score
                        </h3>
                        <div className="relative z-10 mb-6 flex h-40 w-40 items-center justify-center">
                            <svg className="h-full w-full -rotate-90 transform" viewBox="0 0 100 100">
                                <circle
                                    cx="50"
                                    cy="50"
                                    fill="none"
                                    r="45"
                                    stroke="currentColor"
                                    strokeWidth="8"
                                    className="text-slate-100 dark:text-gray-800"
                                />
                                <circle
                                    cx="50"
                                    cy="50"
                                    fill="none"
                                    r="45"
                                    stroke="currentColor"
                                    strokeDasharray="283"
                                    strokeDashoffset={circleOffset(overallRounded)}
                                    strokeLinecap="round"
                                    strokeWidth="8"
                                    className="text-primary drop-shadow-[0_0_8px_rgba(79,70,229,0.4)]"
                                />
                            </svg>
                            <div className="absolute flex flex-col items-center">
                                <span className="text-5xl font-black tracking-tighter text-slate-900 dark:text-white">
                                    {overallRounded}
                                </span>
                                <span className="text-sm font-bold text-slate-500 dark:text-gray-400">/ 100</span>
                            </div>
                        </div>
                        <div
                            className={cn(
                                "z-10 mb-3 flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm font-bold",
                                overallRounded >= 80
                                    ? "border-emerald-200 bg-emerald-100 text-emerald-700 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-400"
                                    : overallRounded >= 60
                                    ? "border-amber-200 bg-amber-100 text-amber-700 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-400"
                                    : "border-rose-200 bg-rose-100 text-rose-700 dark:border-rose-500/20 dark:bg-rose-500/10 dark:text-rose-400"
                            )}
                        >
                            <TrendingUp size={16} />
                            <span>
                                {overallRounded >= 80
                                    ? "Excellent Performance"
                                    : overallRounded >= 60
                                    ? "Good Progress"
                                    : "Needs Improvement"}
                            </span>
                        </div>
                        <p className="z-10 max-w-[280px] text-sm font-medium text-slate-600 dark:text-gray-400">
                            {evaluation.summary}
                        </p>
                    </div>

                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:col-span-8">
                        {dimensionCards.map((card) => (
                            <DimCard key={card.label} {...card} />
                        ))}
                    </div>
                </div>

                <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
                    <div className="flex flex-col rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900 lg:col-span-2 sm:p-8">
                        <h3 className="mb-6 flex items-center gap-2 text-xl font-black text-slate-900 dark:text-white">
                            <Sparkles className="text-primary" />
                            Executive AI Feedback
                        </h3>
                        <div className="grid h-full grid-cols-1 gap-8 md:grid-cols-2">
                            <div className="space-y-4">
                                <h4 className="mb-2 border-b border-gray-100 pb-2 text-sm font-bold uppercase tracking-wider text-slate-400 dark:border-gray-800 dark:text-gray-500">
                                    Top Strengths
                                </h4>
                                {evaluation.strengths.slice(0, 3).map((strength, index) => (
                                    <div key={index} className="flex items-start gap-3">
                                        <div className="mt-1 min-w-[20px] text-emerald-500">
                                            <CheckCircle2 size={20} />
                                        </div>
                                        <p className="text-sm leading-relaxed text-slate-700 dark:text-gray-300">
                                            {strength}
                                        </p>
                                    </div>
                                ))}
                            </div>

                            <div className="space-y-4">
                                <h4 className="mb-2 border-b border-gray-100 pb-2 text-sm font-bold uppercase tracking-wider text-slate-400 dark:border-gray-800 dark:text-gray-500">
                                    Critical Focus Areas
                                </h4>
                                {evaluation.improvements.slice(0, 3).map((improvement, index) => (
                                    <div
                                        key={index}
                                        className={cn(
                                            "relative overflow-hidden rounded-xl border p-4",
                                            index === 0
                                                ? "border-primary/20 bg-slate-50 dark:bg-gray-800/50"
                                                : "border-amber-500/20 bg-slate-50 dark:bg-gray-800/50"
                                        )}
                                    >
                                        <div
                                            className={cn(
                                                "absolute bottom-0 left-0 top-0 w-1",
                                                index === 0 ? "bg-primary" : "bg-amber-500"
                                            )}
                                        />
                                        <div className="flex items-start gap-3">
                                            <div className={cn("min-w-[20px]", index === 0 ? "text-primary" : "text-amber-500")}>
                                                {index === 0 ? <Target size={20} /> : <AlertTriangle size={20} />}
                                            </div>
                                            <p className="text-sm leading-relaxed text-slate-700 dark:text-gray-300">
                                                {improvement}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    <div className="flex flex-col rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
                        <h3 className="mb-4 text-lg font-black text-slate-900 dark:text-white">Session Metrics</h3>
                        <div className="flex-1 space-y-4">
                            <div className="rounded-xl border border-gray-100 bg-slate-50 p-4 dark:border-gray-800 dark:bg-gray-800/50">
                                <p className="mb-3 text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-gray-500">
                                    Difficulty Progression
                                </p>
                                <div className="flex items-center gap-3">
                                    <span className="rounded-lg bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700 dark:bg-gray-900 dark:text-gray-300">
                                        {evaluation.difficultyProgression.startedAt}
                                    </span>
                                    <ArrowRight size={14} className="text-slate-400 dark:text-gray-600" />
                                    <span className="rounded-lg bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700 dark:bg-gray-900 dark:text-gray-300">
                                        {evaluation.difficultyProgression.endedAt}
                                    </span>
                                </div>
                            </div>

                            <div className="space-y-3">
                                {[
                                    { label: "Confidence", value: Math.round(dims.confidence) },
                                    { label: "Clarity", value: Math.round(dims.clarity) },
                                    { label: "Structure", value: Math.round(dims.structure) },
                                    { label: "Depth", value: Math.round(dims.depth) },
                                    { label: "Communication", value: Math.round(dims.communication) },
                                ].map(({ label, value }) => (
                                    <div key={label} className="flex items-center gap-3">
                                        <span className="w-24 flex-shrink-0 text-xs text-slate-500 dark:text-gray-400">
                                            {label}
                                        </span>
                                        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100 dark:bg-gray-800">
                                            <div className={cn("h-full rounded-full", barColor(value))} style={{ width: `${value}%` }} />
                                        </div>
                                        <span className={cn("w-8 text-right text-xs font-bold", scoreColor(value))}>
                                            {value}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                <div className="flex justify-center pb-12 pt-4">
                    <p className="flex items-center gap-1.5 text-sm font-medium text-slate-500 dark:text-gray-400">
                        Next suggested step:
                        <Link
                            href="/dashboard/coach"
                            className="font-bold text-primary underline decoration-primary/30 underline-offset-4 transition-colors hover:text-primary-dark"
                        >
                            AI Coaching Session
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}
