"use client";

import { use, useState } from "react";
import Link from "next/link";
import { PageHeader } from "@/core/components/ui/PageHeader";
import { Surface } from "@/core/components/ui/Surface";
import { buttonStyles } from "@/core/components/ui/button";
import { cn } from "@/lib/utils";
import { useJourney, useJourneyRounds, useJourneyAnalysis } from "@/hooks/queries/useJourneys";
import { useStartRound } from "@/hooks/mutations/useCreateJourney";
import {
    ArrowLeft,
    ArrowRight,
    Play,
    CheckCircle2,
    Clock,
    User,
} from "lucide-react";

export default function JourneyRoundsPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const { data: journeyResponse } = useJourney(id);
    const { data: roundsResponse, isLoading: roundsLoading } = useJourneyRounds(
        journeyResponse?.data?.status !== "CREATED" ? id : null
    );
    const startRound = useStartRound();
    const [selectedRound, setSelectedRound] = useState<number | null>(null);

    const journey = journeyResponse?.data;
    const rounds = roundsResponse?.data ?? [];
    const plan = journey?.generatedPlan as { rounds?: Array<{ name: string; estimatedDurationMinutes: number }> } | null;

    const handleStartRound = async (index: number) => {
        setSelectedRound(index);
        try {
            const result = await startRound.mutateAsync({ journeyId: id, roundIndex: index });
            if (result.data) {
                const ctx = result.data.sessionContext?.interviewJourneyContext;
                if (ctx) {
                    sessionStorage.setItem(`journey-round-${id}-${index}`, JSON.stringify(ctx));
                }
                const sessionId = result.data.interviewSessionId;
                if (sessionId) {
                    window.location.href = `/dashboard/sessions/${sessionId}`;
                }
            }
        } catch (err) {
            console.error("Failed to start round:", err);
        } finally {
            setSelectedRound(null);
        }
    };

    return (
        <div className="flex flex-col gap-8 pb-12">
            <PageHeader
                eyebrow={journey?.roleTitle || "Interview Journey"}
                title="Interview Rounds"
                description="Select a round to begin your interview simulation."
                actions={
                    <Link
                        href={`/dashboard/interview-journey/${id}/analysis`}
                        className={buttonStyles({ variant: "ghost", size: "sm" })}
                    >
                        <ArrowLeft size={14} />
                        Back to Analysis
                    </Link>
                }
            />

            {roundsLoading ? (
                <div className="space-y-3">
                    {Array.from({ length: 3 }).map((_, i) => (
                        <div key={i} className="h-28 rounded-xl bg-card border border-border animate-pulse" />
                    ))}
                </div>
            ) : rounds.length === 0 ? (
                <Surface variant="default" padding="lg" className="text-center py-12">
                    <p className="text-muted-foreground">
                        No rounds generated yet. Run the analysis first.
                    </p>
                    <Link
                        href={`/dashboard/interview-journey/${id}/analysis`}
                        className={cn(buttonStyles(), "mt-4")}
                    >
                        Go to Analysis
                    </Link>
                </Surface>
            ) : (
                <div className="space-y-3">
                    {rounds.map((round, i) => {
                        const planRound = plan?.rounds?.[i];
                        const persona = round.interviewerPersona as {
                            name?: string;
                            role?: string;
                            personaType?: string;
                        } | null;

                        return (
                            <Surface
                                key={round.id}
                                variant="default"
                                padding="md"
                                className={cn(
                                    "flex items-start justify-between gap-4 transition-all",
                                    round.completed && "opacity-60"
                                )}
                            >
                                <div className="flex items-start gap-4 flex-1">
                                    <div className={cn(
                                        "size-10 rounded-lg flex items-center justify-center shrink-0 text-xs font-bold",
                                        round.completed
                                            ? "bg-emerald-500/10 text-emerald-500"
                                            : "bg-primary/10 text-primary"
                                    )}>
                                        {round.completed ? <CheckCircle2 size={18} /> : i + 1}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 flex-wrap">
                                            <h3 className="font-semibold text-foreground text-sm">
                                                {round.roundName}
                                            </h3>
                                            <span className={cn(
                                                "text-[10px] font-medium px-1.5 py-0.5 rounded",
                                                round.difficulty === "HARD" ? "bg-red-500/10 text-red-500" :
                                                round.difficulty === "MEDIUM" ? "bg-amber-500/10 text-amber-500" :
                                                "bg-emerald-500/10 text-emerald-500"
                                            )}>
                                                {round.difficulty}
                                            </span>
                                            <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                                                {round.roundType}
                                            </span>
                                        </div>

                                        {persona && (
                                            <div className="flex items-center gap-1.5 mt-1.5 text-xs text-muted-foreground">
                                                <User size={11} />
                                                <span>{persona.name}, {persona.role}</span>
                                            </div>
                                        )}

                                        {(round.roundFocus as { focus?: { areas?: string[] } } | null)?.focus?.areas && (
                                            <div className="flex flex-wrap gap-1 mt-2">
                                                {(round.roundFocus as { focus: { areas: string[] } }).focus.areas.map((area: string, j: number) => (
                                                    <span key={j} className="text-[10px] text-muted-foreground bg-muted/30 px-1.5 py-0.5 rounded">
                                                        {area}
                                                    </span>
                                                ))}
                                            </div>
                                        )}

                                        {round.completed && (
                                            <div className="flex items-center gap-1 mt-2 text-xs text-emerald-500">
                                                <CheckCircle2 size={11} />
                                                Completed
                                            </div>
                                        )}
                                    </div>
                                </div>

                                <div className="flex items-center gap-2 shrink-0">
                                    {!round.completed && (
                                        <button
                                            type="button"
                                            onClick={() => handleStartRound(i)}
                                            disabled={selectedRound === i || startRound.isPending}
                                            className={cn(
                                                buttonStyles({ size: "sm" }),
                                                "flex items-center gap-1.5"
                                            )}
                                        >
                                            <Play size={12} />
                                            {selectedRound === i ? "Starting..." : "Start"}
                                        </button>
                                    )}
                                    {round.completed && round.sessionId && (
                                        <Link
                                            href={`/dashboard/sessions/${round.sessionId}`}
                                            className={buttonStyles({ variant: "secondary", size: "sm" })}
                                        >
                                            View Session
                                        </Link>
                                    )}
                                </div>
                            </Surface>
                        );
                    })}

                    {/* Final Report Link */}
                    {rounds.every((r) => r.completed) && (
                        <div className="pt-4 flex justify-center">
                            <Link
                                href={`/dashboard/interview-journey/${id}/report`}
                                className={buttonStyles({ size: "lg" })}
                            >
                                View Final Report
                                <ArrowRight size={16} />
                            </Link>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
