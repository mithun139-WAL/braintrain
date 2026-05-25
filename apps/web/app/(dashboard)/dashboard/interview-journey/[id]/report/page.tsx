"use client";

import { use } from "react";
import Link from "next/link";
import { PageHeader } from "@/core/components/ui/PageHeader";
import { Surface } from "@/core/components/ui/Surface";
import { buttonStyles } from "@/core/components/ui/button";
import { cn } from "@/lib/utils";
import { useJourney, useJourneyFinalReport } from "@/hooks/queries/useJourneys";
import type { JourneyFinalReport, JourneyRoundReport } from "@braintrain/shared";
import {
    ArrowLeft,
    Award,
    TrendingUp,
    TrendingDown,
    AlertTriangle,
    CheckCircle2,
    FileText,
    User,
    MessageSquare,
    Code,
} from "lucide-react";

const recommendationConfig: Record<string, { color: string; label: string }> = {
    STRONG_HIRE: { color: "text-emerald-500", label: "Strong Hire" },
    HIRE: { color: "text-blue-500", label: "Hire" },
    NO_HIRE: { color: "text-red-500", label: "No Hire" },
    STRONG_NO_HIRE: { color: "text-red-600", label: "Strong No Hire" },
    INCONCLUSIVE: { color: "text-amber-500", label: "Inconclusive" },
};

const signalConfig: Record<string, { color: string }> = {
    STRONG: { color: "bg-emerald-500" },
    MODERATE: { color: "bg-blue-500" },
    WEAK: { color: "bg-amber-500" },
    NEGATIVE: { color: "bg-red-500" },
};

export default function JourneyFinalReportPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const { data: journeyResponse } = useJourney(id);
    const { data: reportResponse, isLoading } = useJourneyFinalReport(id);

    const journey = journeyResponse?.data;
    const report = reportResponse?.data as JourneyFinalReport | undefined;

    if (isLoading) {
        return (
            <div className="flex flex-col gap-8 pb-12">
                <div className="h-32 rounded-xl bg-card border border-border animate-pulse" />
                <div className="h-96 rounded-xl bg-card border border-border animate-pulse" />
            </div>
        );
    }

    if (!report) {
        return (
            <div className="text-center py-16">
                <p className="text-muted-foreground">Report not available. Complete all rounds first.</p>
                <Link href={`/dashboard/interview-journey/${id}/rounds`} className={cn(buttonStyles(), "mt-4")}>
                    <ArrowLeft size={14} /> Back to Rounds
                </Link>
            </div>
        );
    }

    const rec = recommendationConfig[report.hireRecommendation] ?? recommendationConfig.INCONCLUSIVE;
    const signal = signalConfig[report.overallHiringSignal] ?? signalConfig.WEAK;

    return (
        <div className="flex flex-col gap-8 pb-12 max-w-3xl mx-auto">
            <PageHeader
                eyebrow={journey?.companyName || "Interview Journey"}
                title="Final Hiring Report"
                description="Recruiter-style briefing based on all interview rounds."
                actions={
                    <Link
                        href={`/dashboard/interview-journey/${id}/rounds`}
                        className={buttonStyles({ variant: "ghost", size: "sm" })}
                    >
                        <ArrowLeft size={14} />
                        Back to Rounds
                    </Link>
                }
            />

            {/* Recommendation Banner */}
            <Surface
                variant="default"
                padding="lg"
                className={cn(
                    "border-l-4",
                    report.hireRecommendation.includes("HIRE") ? "border-l-emerald-500" : "border-l-red-500"
                )}
            >
                <div className="flex items-center gap-4">
                    <Award size={32} className={rec.color} />
                    <div>
                        <div className="flex items-center gap-2">
                            <h2 className={cn("text-xl font-bold", rec.color)}>{rec.label}</h2>
                            <div className={cn("size-2 rounded-full", signal.color)} />
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">
                            {journey?.roleTitle} at {journey?.companyName || "Company"}
                        </p>
                    </div>
                </div>
            </Surface>

            {/* Summary Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Surface variant="default" padding="md" className="space-y-3">
                    <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        <User size={14} />
                        Candidate
                    </div>
                    <p className="text-foreground font-medium">{report.candidateLevel}</p>
                    <div className="text-xs text-muted-foreground space-y-1">
                        <p>Strongest round: {report.strongestRound || "N/A"}</p>
                        <p>Weakest round: {report.weakestRound || "N/A"}</p>
                    </div>
                </Surface>

                <Surface variant="default" padding="md" className="space-y-3">
                    <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        <FileText size={14} />
                        Company Fit
                    </div>
                    <p className="text-sm text-foreground">{report.companyFit}</p>
                </Surface>
            </div>

            {/* Risk Areas */}
            {report.hiringRiskAreas.length > 0 && (
                <Surface variant="default" padding="md" className="space-y-3">
                    <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-amber-500">
                        <AlertTriangle size={14} />
                        Hiring Risks
                    </div>
                    <ul className="space-y-2">
                        {report.hiringRiskAreas.map((risk, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm text-foreground">
                                <div className="size-1.5 rounded-full bg-amber-500 mt-1.5 shrink-0" />
                                {risk}
                            </li>
                        ))}
                    </ul>
                </Surface>
            )}

            {/* Summaries */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Surface variant="default" padding="md" className="space-y-3">
                    <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        <MessageSquare size={14} />
                        Communication
                    </div>
                    <p className="text-sm text-foreground leading-relaxed">{report.communicationSummary}</p>
                </Surface>

                <Surface variant="default" padding="md" className="space-y-3">
                    <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        <Code size={14} />
                        Technical
                    </div>
                    <p className="text-sm text-foreground leading-relaxed">{report.technicalSummary}</p>
                </Surface>
            </div>

            {/* Round Reports */}
            <Surface variant="default" padding="lg" className="space-y-4">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Round Breakdowns
                </h3>
                <div className="space-y-4">
                    {report.roundReports.map((roundReport, i) => (
                        <Surface key={i} variant="subtle" padding="md" className="space-y-3">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h4 className="font-medium text-foreground text-sm">{roundReport.roundName}</h4>
                                    <div className="flex items-center gap-2 mt-0.5">
                                        <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                                            {roundReport.roundType}
                                        </span>
                                        <span className={cn(
                                            "text-[10px] px-1.5 py-0.5 rounded",
                                            roundReport.difficulty === "HARD" ? "bg-red-500/10 text-red-500" :
                                            roundReport.difficulty === "MEDIUM" ? "bg-amber-500/10 text-amber-500" :
                                            "bg-emerald-500/10 text-emerald-500"
                                        )}>
                                            {roundReport.difficulty}
                                        </span>
                                    </div>
                                </div>
                                <span className="text-[11px] text-muted-foreground">
                                    {roundReport.communicationQuality}
                                </span>
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                <div>
                                    <p className="text-xs font-medium text-emerald-500 mb-1 flex items-center gap-1">
                                        <TrendingUp size={11} /> Strengths
                                    </p>
                                    <ul className="space-y-1">
                                        {roundReport.strengths.map((s, j) => (
                                            <li key={j} className="text-xs text-foreground/80 flex items-start gap-1.5">
                                                <span className="text-emerald-500">+</span> {s}
                                            </li>
                                        ))}
                                        {roundReport.strengths.length === 0 && (
                                            <li className="text-xs text-muted-foreground italic">No significant strengths</li>
                                        )}
                                    </ul>
                                </div>
                                <div>
                                    <p className="text-xs font-medium text-amber-500 mb-1 flex items-center gap-1">
                                        <TrendingDown size={11} /> Weaknesses
                                    </p>
                                    <ul className="space-y-1">
                                        {roundReport.weaknesses.map((w, j) => (
                                            <li key={j} className="text-xs text-foreground/80 flex items-start gap-1.5">
                                                <span className="text-amber-500">-</span> {w}
                                            </li>
                                        ))}
                                        {roundReport.weaknesses.length === 0 && (
                                            <li className="text-xs text-muted-foreground italic">No significant weaknesses</li>
                                        )}
                                    </ul>
                                </div>
                            </div>

                            {roundReport.technicalGaps.length > 0 && (
                                <div>
                                    <p className="text-xs font-medium text-red-500 mb-1">Technical Gaps</p>
                                    <ul className="space-y-1">
                                        {roundReport.technicalGaps.map((g, j) => (
                                            <li key={j} className="text-xs text-foreground/80 flex items-start gap-1.5">
                                                <AlertTriangle size={10} className="text-red-500 shrink-0 mt-0.5" /> {g}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </Surface>
                    ))}
                </div>
            </Surface>

            {/* Recruiter Notes */}
            <Surface variant="default" padding="lg" className="space-y-3">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Recruiter Notes
                </h3>
                <p className="text-sm text-foreground leading-relaxed whitespace-pre-line">
                    {report.recruiterNotes}
                </p>
            </Surface>
        </div>
    );
}
