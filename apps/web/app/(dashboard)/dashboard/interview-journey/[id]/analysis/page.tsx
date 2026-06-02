"use client";

import { useState, use } from "react";
import Link from "next/link";
import { PageHeader } from "@/core/components/ui/PageHeader";
import { Surface } from "@/core/components/ui/Surface";
import { buttonStyles } from "@/core/components/ui/button";
import { cn } from "@/lib/utils";
import { useJourney, useJourneyAnalysis } from "@/hooks/queries/useJourneys";
import { useAnalyzeJourney } from "@/hooks/mutations/useCreateJourney";
import type { JourneyAnalysis } from "@braintrain/shared";
import {
    ArrowLeft,
    Brain,
    Target,
    AlertTriangle,
    CheckCircle2,
    Lightbulb,
    Sparkles,
    ArrowRight,
    BarChart3,
} from "lucide-react";

export default function JourneyAnalysisPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const { data: journeyResponse, isLoading: journeyLoading } = useJourney(id);
    const { data: analysisResponse, isLoading: analysisLoading } = useJourneyAnalysis(
        journeyResponse?.data?.status === "CREATED" ? null : id
    );
    const analyzeJourney = useAnalyzeJourney();

    const journey = journeyResponse?.data;
    const analysis = analysisResponse?.data as JourneyAnalysis | undefined;

    const needsAnalysis = journey?.status === "CREATED";

    const handleAnalyze = async () => {
        await analyzeJourney.mutateAsync(id);
    };

    if (journeyLoading) {
        return (
            <div className="flex flex-col gap-8 pb-12">
                <div className="h-32 rounded-xl bg-card border border-border animate-pulse" />
                <div className="h-64 rounded-xl bg-card border border-border animate-pulse" />
            </div>
        );
    }

    if (!journey) {
        return (
            <div className="text-center py-16">
                <p className="text-muted-foreground">Journey not found</p>
                <Link href="/dashboard/interview-journey" className={cn(buttonStyles({ variant: "ghost" }), "mt-4")}>
                    <ArrowLeft size={14} /> Back
                </Link>
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-8 pb-12">
            <PageHeader
                eyebrow={journey.companyName || "Interview Journey"}
                title={journey.roleTitle}
                description={
                    journey.status === "CREATED"
                        ? "Ready for analysis. Generate your hiring plan to begin."
                        : "Hiring plan generated. Review the analysis below."
                }
                actions={
                    <Link href="/dashboard/interview-journey" className={buttonStyles({ variant: "ghost", size: "sm" })}>
                        <ArrowLeft size={14} />
                        All Journeys
                    </Link>
                }
            />

            {needsAnalysis ? (
                <Surface variant="default" padding="lg" className="text-center py-12 space-y-4">
                    <div className="size-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto text-primary">
                        <Brain size={28} />
                    </div>
                    <h3 className="text-lg font-semibold text-foreground">Ready for AI Analysis</h3>
                    <p className="text-sm text-muted-foreground max-w-md mx-auto">
                        We'll analyze your resume against the job description to generate a
                        personalized interview plan with dynamic rounds and interviewer personas.
                    </p>
                    <button
                        type="button"
                        onClick={handleAnalyze}
                        disabled={analyzeJourney.isPending}
                        className={buttonStyles({ size: "lg" })}
                    >
                        <Sparkles size={16} />
                        {analyzeJourney.isPending ? "Analyzing..." : "Generate Hiring Plan"}
                    </button>
                </Surface>
            ) : analysisLoading ? (
                <div className="h-96 rounded-xl bg-card border border-border animate-pulse" />
            ) : analysis ? (
                <>
                    {/* Candidate Overview */}
                    <Surface variant="default" padding="lg" className="space-y-4">
                        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                            <BarChart3 size={14} />
                            Candidate Overview
                        </div>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                            <div className="space-y-1">
                                <p className="text-xs text-muted-foreground">Level</p>
                                <p className="font-semibold text-foreground">{analysis.candidateLevel}</p>
                            </div>
                            <div className="space-y-1">
                                <p className="text-xs text-muted-foreground">Category</p>
                                <p className="font-semibold text-foreground">{analysis.roleCategory}</p>
                            </div>
                            <div className="space-y-1">
                                <p className="text-xs text-muted-foreground">Rounds</p>
                                <p className="font-semibold text-foreground">{analysis.rounds.length}</p>
                            </div>
                            <div className="space-y-1">
                                <p className="text-xs text-muted-foreground">Status</p>
                                <p className="font-semibold text-emerald-500">Active</p>
                            </div>
                        </div>
                    </Surface>

                    {/* Strengths & Weaknesses */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <Surface variant="default" padding="md" className="space-y-3">
                            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-emerald-500">
                                <CheckCircle2 size={14} />
                                Strengths
                            </div>
                            <ul className="space-y-2">
                                {analysis.strengths.map((s, i) => (
                                    <li key={i} className="flex items-start gap-2 text-sm text-foreground">
                                        <div className="size-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
                                        {s}
                                    </li>
                                ))}
                                {analysis.strengths.length === 0 && (
                                    <li className="text-sm text-muted-foreground">No specific strengths identified</li>
                                )}
                            </ul>
                        </Surface>

                        <Surface variant="default" padding="md" className="space-y-3">
                            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-amber-500">
                                <AlertTriangle size={14} />
                                Areas to Watch
                            </div>
                            <ul className="space-y-2">
                                {analysis.weaknesses.map((w, i) => (
                                    <li key={i} className="flex items-start gap-2 text-sm text-foreground">
                                        <div className="size-1.5 rounded-full bg-amber-500 mt-1.5 shrink-0" />
                                        {w}
                                    </li>
                                ))}
                                {analysis.weaknesses.length === 0 && (
                                    <li className="text-sm text-muted-foreground">No specific concerns identified</li>
                                )}
                            </ul>
                        </Surface>
                    </div>

                    {/* Plan Summary & Rounds */}
                    <Surface variant="default" padding="lg" className="space-y-4">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                                <Target size={14} />
                                Generated Hiring Plan
                            </div>
                            <Link
                                href={`/dashboard/interview-journey/${id}/rounds`}
                                className={buttonStyles({ size: "sm" })}
                            >
                                View All Rounds
                                <ArrowRight size={14} />
                            </Link>
                        </div>

                        <div className="grid gap-3">
                            {analysis.rounds.map((round, i) => (
                                <Surface
                                    key={i}
                                    variant="subtle"
                                    padding="md"
                                    className="flex items-start justify-between gap-4"
                                >
                                    <div className="flex items-start gap-3">
                                        <div className="size-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary shrink-0 text-xs font-bold">
                                            {i + 1}
                                        </div>
                                        <div>
                                            <h4 className="font-medium text-foreground text-sm">{round.name}</h4>
                                            <div className="flex items-center gap-2 mt-1">
                                                <span className="text-[11px] text-muted-foreground px-1.5 py-0.5 rounded bg-muted">
                                                    {round.roundType}
                                                </span>
                                                <span className="text-[11px] text-muted-foreground">
                                                    {round.estimatedDurationMinutes} min
                                                </span>
                                                <span className={cn(
                                                    "text-[11px] px-1.5 py-0.5 rounded",
                                                    round.difficulty === "HARD" ? "bg-red-500/10 text-red-500" :
                                                    round.difficulty === "MEDIUM" ? "bg-amber-500/10 text-amber-500" :
                                                    "bg-emerald-500/10 text-emerald-500"
                                                )}>
                                                    {round.difficulty}
                                                </span>
                                            </div>
                                            {round.focus?.areas && (
                                                <div className="flex flex-wrap gap-1.5 mt-2">
                                                    {round.focus.areas.map((area, j) => (
                                                        <span key={j} className="text-[10px] text-muted-foreground bg-muted/50 px-1.5 py-0.5 rounded">
                                                            {area}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                    <Link
                                        href={`/dashboard/interview-journey/${id}/rounds?round=${i}`}
                                        className={cn(buttonStyles({ variant: "ghost", size: "sm" }), "shrink-0")}
                                    >
                                        <ArrowRight size={14} />
                                    </Link>
                                </Surface>
                            ))}
                        </div>
                    </Surface>
                </>
            ) : null}
        </div>
    );
}
