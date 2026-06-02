"use client";

import Link from "next/link";
import { TopicDto } from "@braintrain/shared";
import { Trash2, History, Award, ArrowRight } from "lucide-react";
import { format } from "date-fns";
import { cn } from "@/lib/utils";

interface TopicCardProps {
    topic: TopicDto;
    onDelete?: (id: string) => void;
}

export function TopicCard({ topic, onDelete }: TopicCardProps) {
    const scoreColor = topic.avgScore && topic.avgScore >= 80
        ? "bg-green-500"
        : topic.avgScore && topic.avgScore >= 50
            ? "bg-primary"
            : "bg-orange-400";

    return (
        <Link
            href={`/dashboard/topics/${topic.id}`}
            className="group relative flex h-full flex-col rounded-3xl border border-border bg-card p-6 shadow-card transition-all duration-300 hover:border-primary/30 hover:shadow-card-hover"
        >
            <div className="flex justify-between items-start mb-4">
                <div className="flex flex-col gap-1">
                    <span className={cn(
                        "inline-flex items-center rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.18em] w-fit border",
                        topic.isGlobal
                            ? "border-border bg-muted text-muted-foreground"
                            : "border-primary/20 bg-primary/10 text-primary"
                    )}>
                        {topic.isGlobal ? "System" : "Custom"}
                    </span>
                    <h3 className="mt-3 font-display text-title-md text-foreground transition-colors group-hover:text-primary">
                        {topic.name}
                    </h3>
                </div>

                {!topic.isGlobal && onDelete && (
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            e.preventDefault();
                            onDelete(topic.id);
                        }}
                        className="rounded-xl p-2 text-muted-foreground opacity-0 transition-all hover:bg-ruby/10 hover:text-ruby group-hover:opacity-100"
                        title="Delete custom topic"
                        aria-label={`Delete ${topic.name}`}
                    >
                        <Trash2 size={16} />
                    </button>
                )}
            </div>

            <p className="mb-6 min-h-[40px] line-clamp-2 text-body-sm text-muted-foreground leading-relaxed">
                {topic.description || "No description provided for this topic."}
            </p>

            <div className="mt-auto flex flex-col gap-4">
                {/* Progress Bar */}
                <div className="flex flex-col gap-2">
                    <div className="flex justify-between items-end">
                        <span className="text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">Avg Score</span>
                        <span className="text-sm font-bold text-foreground">{topic.avgScore ?? 0}%</span>
                    </div>
                    <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                        <div
                            className={cn("h-full rounded-full transition-all duration-500", scoreColor)}
                            style={{ width: `${topic.avgScore ?? 0}%` }}
                        />
                    </div>
                </div>

                {/* Footer Stats */}
                <div className="flex items-center justify-between border-t border-border pt-4 text-[11px] font-bold uppercase tracking-[0.15em] text-muted-foreground">
                    <div className="flex items-center gap-1.5">
                        <History size={14} className="text-primary/60" />
                        <span>{topic.sessionCount || 0} Sessions</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                        <Award size={14} className="text-primary/60" />
                        <span>{topic.lastSessionDate ? format(new Date(topic.lastSessionDate), "MMM dd") : "No practice"}</span>
                    </div>
                </div>

                <div className="flex items-center gap-2 pt-1 text-sm font-semibold text-primary">
                    Open topic
                    <ArrowRight size={14} />
                </div>
            </div>
        </Link>
    );
}
