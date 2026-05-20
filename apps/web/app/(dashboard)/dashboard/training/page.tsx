"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
    Dumbbell,
    CheckCircle2,
    Circle,
    Sparkles,
    Loader2,
    AlertCircle,
    Clock,
    Target,
    ChevronDown,
    ChevronUp,
    Brain,
    Zap,
    BookOpen,
    RefreshCw,
    Trophy,
    Calendar,
    BarChart3,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useCurrentTrainingPlan } from "@/hooks/queries/useTrainingPlan";
import {
    useGenerateTrainingPlan,
    useCompleteTrainingTask,
} from "@/hooks/mutations/useTrainingMutations";
import type { TrainingTask, TrainingTaskType, TrainingDifficulty } from "@braintrain/shared";

// ── Helpers ────────────────────────────────────────────────────────────────────

const TASK_TYPE_META: Record<TrainingTaskType, { icon: React.ReactNode; label: string; color: string }> = {
    DRILL: { icon: <Zap size={14} />, label: "Drill", color: "text-amber-400 bg-amber-400/10 border-amber-400/20" },
    EXERCISE: { icon: <Dumbbell size={14} />, label: "Exercise", color: "text-blue-400 bg-blue-400/10 border-blue-400/20" },
    REFLECTION: { icon: <Brain size={14} />, label: "Reflection", color: "text-purple-400 bg-purple-400/10 border-purple-400/20" },
    PRACTICE: { icon: <Target size={14} />, label: "Practice", color: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20" },
    READING: { icon: <BookOpen size={14} />, label: "Reading", color: "text-sky-400 bg-sky-400/10 border-sky-400/20" },
};

const DIFFICULTY_COLOR: Record<TrainingDifficulty, string> = {
    BEGINNER: "text-emerald-400",
    INTERMEDIATE: "text-amber-400",
    ADVANCED: "text-rose-400",
};

function groupTasksByDay(tasks: TrainingTask[]) {
    // Group into chunks of 2 (the backend generates 2 per day)
    const days: TrainingTask[][] = [];
    for (let i = 0; i < tasks.length; i += 2) {
        days.push(tasks.slice(i, i + 2));
    }
    return days;
}

// ── Task Card ─────────────────────────────────────────────────────────────────

interface TaskCardProps {
    task: TrainingTask;
    onComplete: (id: string) => void;
    isCompleting: boolean;
}

function TaskCard({ task, onComplete, isCompleting }: TaskCardProps) {
    const [expanded, setExpanded] = useState(false);
    const meta = TASK_TYPE_META[task.taskType] ?? TASK_TYPE_META.EXERCISE;

    return (
        <div className={cn(
            "rounded-xl border transition-all",
            task.completed
                ? "bg-gray-900/30 border-gray-800/50 opacity-70"
                : "bg-gray-900 border-gray-800 hover:border-gray-700"
        )}>
            <div className="p-4">
                <div className="flex items-start gap-3">
                    {/* Checkbox */}
                    <button
                        onClick={() => !task.completed && onComplete(task.id)}
                        disabled={task.completed || isCompleting}
                        className={cn(
                            "flex-shrink-0 mt-0.5 transition-all",
                            task.completed ? "cursor-default" : "hover:scale-110"
                        )}
                    >
                        {isCompleting ? (
                            <Loader2 size={20} className="animate-spin text-primary" />
                        ) : task.completed ? (
                            <CheckCircle2 size={20} className="text-emerald-500" />
                        ) : (
                            <Circle size={20} className="text-gray-600 hover:text-primary transition-colors" />
                        )}
                    </button>

                    <div className="flex-1 min-w-0">
                        {/* Title row */}
                        <div className="flex items-start justify-between gap-2">
                            <h4 className={cn(
                                "font-semibold text-sm leading-snug",
                                task.completed ? "text-gray-500 line-through" : "text-white"
                            )}>
                                {task.title}
                            </h4>
                            <button
                                onClick={() => setExpanded(v => !v)}
                                className="flex-shrink-0 text-gray-600 hover:text-gray-400 transition-colors"
                            >
                                {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                            </button>
                        </div>

                        {/* Badges */}
                        <div className="flex items-center flex-wrap gap-2 mt-2">
                            <span className={cn(
                                "inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full border",
                                meta.color
                            )}>
                                {meta.icon}
                                {meta.label}
                            </span>
                            <span className={cn(
                                "text-[11px] font-medium",
                                DIFFICULTY_COLOR[task.difficulty]
                            )}>
                                {task.difficulty.charAt(0) + task.difficulty.slice(1).toLowerCase()}
                            </span>
                            <span className="flex items-center gap-1 text-[11px] text-gray-600">
                                <Clock size={11} />
                                {task.durationMinutes}m
                            </span>
                        </div>

                        {/* Description (always visible) */}
                        <p className="text-xs text-gray-500 mt-2 leading-relaxed">{task.description}</p>
                    </div>
                </div>

                {/* Expanded: instructions + success criteria */}
                {expanded && (
                    <div className="mt-4 ml-8 space-y-3">
                        {task.instructions.length > 0 && (
                            <div>
                                <p className="text-[11px] font-semibold text-gray-500 uppercase tracking-wide mb-2">Instructions</p>
                                <ol className="space-y-1.5">
                                    {task.instructions.map((step, i) => (
                                        <li key={i} className="flex gap-2 text-xs text-gray-400">
                                            <span className="flex-shrink-0 size-4 rounded-full bg-gray-800 text-[10px] font-bold flex items-center justify-center text-gray-500">
                                                {i + 1}
                                            </span>
                                            {step}
                                        </li>
                                    ))}
                                </ol>
                            </div>
                        )}
                        {task.successCriteria && (
                            <div className="bg-emerald-950/30 border border-emerald-900/40 rounded-lg p-3">
                                <p className="text-[11px] font-semibold text-emerald-500 mb-1">Success Criteria</p>
                                <p className="text-xs text-emerald-300/70">{task.successCriteria}</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

// ── Empty / Generate State ────────────────────────────────────────────────────

interface EmptyStateProps {
    onGenerate: () => void;
    isGenerating: boolean;
}

function EmptyState({ onGenerate, isGenerating }: EmptyStateProps) {
    return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] gap-6 text-center">
            <div className="size-20 rounded-2xl bg-primary/10 flex items-center justify-center">
                <Dumbbell size={36} className="text-primary" />
            </div>
            <div className="space-y-2">
                <h2 className="text-2xl font-bold text-white">No Training Plan Yet</h2>
                <p className="text-gray-500 max-w-sm text-sm leading-relaxed">
                    Generate a personalized 7-day training plan. The AI analyzes your session
                    history and builds targeted micro-exercises for your weakest dimensions.
                </p>
            </div>
            <button
                onClick={onGenerate}
                disabled={isGenerating}
                className="flex items-center gap-2 px-6 py-3 rounded-xl bg-primary text-white font-bold hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
                {isGenerating ? (
                    <>
                        <Loader2 size={18} className="animate-spin" />
                        Generating Plan…
                    </>
                ) : (
                    <>
                        <Sparkles size={18} />
                        Generate My Plan
                    </>
                )}
            </button>
        </div>
    );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function TrainingPage() {
    const { data: planResponse, isLoading, error } = useCurrentTrainingPlan();
    const generatePlan = useGenerateTrainingPlan();
    const completeTask = useCompleteTrainingTask();
    const [completingTaskId, setCompletingTaskId] = useState<string | null>(null);

    const plan = planResponse?.data;
    const isNetworkError = error && typeof error !== "string";
    const isEmpty = !plan;
    const isError = isNetworkError;

    const handleGenerate = () => generatePlan.mutate({});

    const handleCompleteTask = async (taskId: string) => {
        setCompletingTaskId(taskId);
        try {
            await completeTask.mutateAsync(taskId);
        } finally {
            setCompletingTaskId(null);
        }
    };

    const days = plan ? groupTasksByDay(plan.tasks) : [];
    const pct = plan?.completionPercentage ?? 0;

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <Loader2 size={28} className="animate-spin text-primary" />
            </div>
        );
    }

    if (isError) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4 text-center">
                <AlertCircle size={32} className="text-rose-500" />
                <p className="text-gray-400">Failed to load training plan.</p>
                <button
                    onClick={handleGenerate}
                    className="px-4 py-2 rounded-lg bg-primary/10 text-primary text-sm font-semibold hover:bg-primary/20 transition-colors"
                >
                    Try generating one
                </button>
            </div>
        );
    }

    if (!plan) {
        return (
            <EmptyState onGenerate={handleGenerate} isGenerating={generatePlan.isPending} />
        );
    }

    return (
        <div className="max-w-2xl mx-auto space-y-8">
            {/* Header */}
            <div className="flex items-start justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-white">Training Plan</h1>
                    <p className="text-gray-500 text-sm mt-1">
                        {plan.focusAreas.map(f =>
                            f.charAt(0).toUpperCase() + f.slice(1)
                        ).join(" · ")}
                    </p>
                </div>
                <button
                    onClick={handleGenerate}
                    disabled={generatePlan.isPending}
                    className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-300 disabled:opacity-40 transition-colors"
                >
                    <RefreshCw size={14} className={cn(generatePlan.isPending && "animate-spin")} />
                    Regenerate
                </button>
            </div>

            {/* Progress bar */}
            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-3">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Trophy size={18} className={cn(pct === 100 ? "text-amber-400" : "text-gray-600")} />
                        <span className="text-sm font-semibold text-white">
                            {plan.completedTaskCount}/{plan.totalTaskCount} tasks completed
                        </span>
                    </div>
                    <span className="text-lg font-bold text-primary">{Math.round(pct)}%</span>
                </div>
                <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                    <div
                        className="h-full bg-gradient-to-r from-primary to-primary/70 rounded-full transition-all duration-500"
                        style={{ width: `${pct}%` }}
                    />
                </div>
                {pct === 100 && (
                    <p className="text-xs text-amber-400 font-medium text-center">
                        Plan complete! Generate a new one to keep improving.
                    </p>
                )}
            </div>

            {/* AI Reasoning */}
            {plan.aiReasoning && (
                <div className="bg-primary/5 border border-primary/15 rounded-xl p-4 flex gap-3">
                    <Sparkles size={16} className="text-primary flex-shrink-0 mt-0.5" />
                    <p className="text-xs text-gray-400 leading-relaxed">{plan.aiReasoning}</p>
                </div>
            )}

            {/* Days */}
            <div className="space-y-6">
                {days.map((dayTasks, dayIdx) => {
                    const dayComplete = dayTasks.every(t => t.completed);
                    return (
                        <div key={dayIdx}>
                            {/* Day header */}
                            <div className="flex items-center gap-3 mb-3">
                                <div className={cn(
                                    "flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold",
                                    dayComplete
                                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                        : "bg-gray-800 text-gray-400 border border-gray-700"
                                )}>
                                    {dayComplete ? <CheckCircle2 size={13} /> : <Calendar size={13} />}
                                    Day {dayIdx + 1}
                                </div>
                                <div className="flex-1 h-px bg-gray-800" />
                            </div>

                            {/* Tasks */}
                            <div className="space-y-3">
                                {dayTasks.map(task => (
                                    <TaskCard
                                        key={task.id}
                                        task={task}
                                        onComplete={handleCompleteTask}
                                        isCompleting={completingTaskId === task.id}
                                    />
                                ))}
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Expiry note */}
            <p className="text-center text-[11px] text-gray-700 pb-4">
                Plan expires{" "}
                {new Date(plan.expiresAt).toLocaleDateString("en-US", {
                    weekday: "long",
                    month: "short",
                    day: "numeric",
                })}
            </p>
        </div>
    );
}
