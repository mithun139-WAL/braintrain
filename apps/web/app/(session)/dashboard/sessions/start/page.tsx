"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import {
    ChevronLeft,
    Brain,
    MessageSquare,
    Code,
    Shuffle,
    CheckCircle2,
    SlidersHorizontal,
    ChevronDown,
    BarChart2,
    Timer,
    ArrowRight,
    Users,
    User,
    Zap,
    Target,
    Settings,
    History,
    TrendingUp,
    Terminal,
    Bolt,
    Check,
    ChevronRight,
    Play,
    Sparkles,
    Layers,
    Bot,
    Gauge,
    Crown,
    AlertTriangle,
} from "lucide-react";
import { Logo } from "@/components/ui/Logo";
import { cn } from "@/lib/utils";
import { useSessionBuilderStore } from "@/lib/store/sessionBuilder.store";
import { InterviewType, InterviewMode, Difficulty } from "@braintrain/shared";
import { useTopics } from "@/hooks/queries/useTopics";
import { useCreateSession } from "@/hooks/mutations/useCreateSession";
import { useStartCheckout } from "@/hooks/mutations/useBillingMutations";
import { useBillingStatus } from "@/hooks/queries/useBillingStatus";
import { useGetProfile } from "@/hooks/queries/useGetProfile";
import { Surface } from "@/core/components/ui/Surface";
import { buttonStyles } from "@/core/components/ui/button";
import { Loader2 } from "lucide-react";
import { useSearchParams } from "next/navigation";

export default function StartSessionPage() {
    const searchParams = useSearchParams();
    const presetTopicId = searchParams.get("topicId");
    const {
        step,
        topicId,
        interviewType,
        interviewMode,
        difficulty,
        adaptive,
        durationMinutes,
        setTopicId,
        setInterviewType,
        setInterviewMode,
        setDifficulty,
        setAdaptive,
        setDurationMinutes,
        nextStep,
        prevStep,
        reset
    } = useSessionBuilderStore();

    const { data: topicsData, isLoading: isLoadingTopics } = useTopics();
    const { data: profileResponse, isLoading: isLoadingProfile } = useGetProfile();
    const { data: billingStatusResponse, isLoading: isBillingStatusLoading } = useBillingStatus();
    const createSession = useCreateSession();
    const startCheckout = useStartCheckout();

    const profile = profileResponse?.data;
    const billingStatus = billingStatusResponse?.data;
    const isPro = (profile?.planType || "FREE").toUpperCase() === "PRO";
    const isBillingConfigured = billingStatus?.configured ?? false;
    const sessionLimit = isPro ? 20 : 3;
    const sessionsUsed = profile?.monthlySessionCount || 0;
    const sessionsRemaining = Math.max(0, sessionLimit - sessionsUsed);
    const hasReachedSessionLimit = sessionsRemaining === 0;
    const canStartSession =
        !hasReachedSessionLimit &&
        !isLoadingProfile &&
        Boolean(topicId && interviewType && interviewMode && difficulty) &&
        !createSession.isPending;

    useEffect(() => {
        // Reset on mount for a fresh flow
        reset();
        if (presetTopicId) {
            setTopicId(presetTopicId);
        }
    }, [presetTopicId, reset, setTopicId]);

    const handleStartSession = () => {
        if (!topicId || !interviewType || !interviewMode || hasReachedSessionLimit) return;

        createSession.mutate({
            topicId,
            interviewType: interviewType as any,
            interviewMode: interviewMode as any,
            difficulty: difficulty as any,
            adaptive,
            durationMinutes
        });
    };

    const topics = topicsData?.data || [];

    const interviewTypes = [
        { id: InterviewType.TECHNICAL, title: "Technical", description: "Hard skills & Code", icon: Terminal },
        { id: InterviewType.BEHAVIORAL, title: "Behavioral", description: "STAR Method", icon: MessageSquare },
        { id: InterviewType.MIXED, title: "Mixed", description: "Tech + Soft Skills", icon: Shuffle },
    ];

    const interviewModes = [
        { id: InterviewMode.ONE_ON_ONE_AI, title: "1:1 AI Interview", description: "Standard single interviewer format.", icon: User },
        { id: InterviewMode.PANEL_AI, title: "Panel AI", description: "Multiple AI personas with different criteria.", icon: Users },
        { id: InterviewMode.HYBRID, title: "Hybrid", description: "Human supervision with AI-driven analysis.", icon: Zap },
    ];

    return (
        <div className="min-h-screen bg-background text-foreground font-display antialiased selection:bg-primary/10 selection:text-primary">
            <div className="min-h-screen flex flex-col">
                {/* Header */}
                <header className="flex items-center justify-between border-b border-border bg-background/90 px-6 py-4 sticky top-0 z-50 backdrop-blur-sm">
                    <div className="flex items-center gap-4">
                        <Link href="/dashboard">
                            <button className="flex items-center justify-center size-8 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors">
                                <ChevronLeft size={20} />
                            </button>
                        </Link>
                        <div className="h-5 w-px bg-border"></div>
                        <Logo iconWrapperClassName="size-7 rounded-lg" iconSize={14} textClassName="text-lg font-bold tracking-tight" />
                    </div>
                    <div className="flex items-center gap-6">
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/5 border border-primary/10 text-primary text-xs font-bold uppercase tracking-wider">
                            <span className="size-2 rounded-full bg-primary animate-pulse"></span>
                            Configuring New Session
                        </div>
                    </div>
                </header>

                <main className="flex-1 w-full max-w-[1200px] mx-auto p-6 md:p-10">
                    <div className="flex flex-col xl:flex-row gap-10 relative">
                        <div className="flex-1 flex flex-col gap-12">
                            {hasReachedSessionLimit ? (
                                <Surface variant="subtle" padding="lg" className="border-amber-500/20 bg-amber-500/5">
                                    <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
                                        <div className="space-y-3">
                                            <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.22em] text-amber-600 dark:text-amber-300">
                                                <AlertTriangle size={14} />
                                                Session limit reached
                                            </div>
                                            <div className="space-y-2">
                                                <h2 className="text-xl font-bold tracking-tight text-foreground">
                                                    You have used all {sessionLimit} sessions in your current {(profile?.planType || "FREE").toUpperCase()} cycle.
                                                </h2>
                                                <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">
                                                    New sessions are blocked until your monthly usage resets or your plan changes. You can still review past sessions, analytics, and current plan details from Settings.
                                                </p>
                                                {!isBillingConfigured ? (
                                                    <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">
                                                        This environment does not have Stripe configured yet, so in-app upgrade checkout is currently unavailable.
                                                    </p>
                                                ) : null}
                                            </div>
                                        </div>

                                        <div className="flex flex-col gap-2 sm:flex-row">
                                            <Link href="/dashboard/settings" className={buttonStyles()}>
                                                <Gauge size={16} />
                                                Manage plan
                                            </Link>
                                            <button
                                                type="button"
                                                onClick={() => startCheckout.mutate()}
                                                disabled={startCheckout.isPending || !isBillingConfigured || isBillingStatusLoading}
                                                className={buttonStyles({ variant: "secondary" })}
                                            >
                                                <Crown size={16} />
                                                {!isBillingConfigured
                                                    ? "Billing unavailable"
                                                    : startCheckout.isPending
                                                    ? "Opening checkout..."
                                                    : "Upgrade to PRO"}
                                            </button>
                                        </div>
                                    </div>
                                </Surface>
                            ) : null}

                            {/* Hero Section */}
                            <div className="mb-16">
                                <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-4">
                                    New Practice <span className="text-primary relative inline-block">
                                        Session
                                        <span className="absolute bottom-1.5 left-0 w-full h-3 bg-primary/10 -z-10"></span>
                                    </span>
                                </h1>
                                <p className="text-muted-foreground text-base">Configure your AI interview parameters to simulate real-world scenarios.</p>
                            </div>

                            {/* Step 1: Select Topic */}
                            <section className="relative pl-12">
                                <div className="absolute left-[15px] top-[40px] bottom-[-48px] w-[2px] bg-primary/20 z-0"></div>
                                <div className={cn(
                                    "absolute left-0 top-0 size-8 rounded-full flex items-center justify-center text-sm font-bold shadow-md z-10 transition-colors",
                                    topicId ? "bg-primary text-white" : "bg-foreground text-background"
                                )}>
                                    {topicId ? <CheckCircle2 size={16} /> : "1"}
                                </div>
                                <div className="flex flex-col gap-5">
                                    <div className="flex justify-between items-end">
                                        <h3 className="text-lg font-bold">Select Topic</h3>
                                        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Required</span>
                                    </div>
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                        {isLoadingTopics ? (
                                            <div className="col-span-full h-32 flex items-center justify-center">
                                                <Loader2 className="animate-spin text-primary" />
                                            </div>
                                        ) : (
                                            topics.map((topic) => (
                                                <button
                                                    key={topic.id}
                                                    onClick={() => setTopicId(topic.id)}
                                                    className={cn(
                                                        "group p-5 rounded-2xl border-2 transition-all flex items-center gap-4 text-left relative overflow-hidden",
                                                        topicId === topic.id
                                                            ? "bg-primary/5 border-primary shadow-md"
                                                            : "bg-card border-border hover:border-primary/30 hover:shadow-sm"
                                                    )}
                                                >
                                                    <div className={cn(
                                                        "size-12 rounded-xl flex items-center justify-center transition-colors",
                                                        topicId === topic.id ? "bg-primary text-white" : "bg-muted text-muted-foreground group-hover:bg-primary/10 group-hover:text-primary"
                                                    )}>
                                                        <Brain size={24} />
                                                    </div>
                                                    <div>
                                                        <h4 className="font-bold">{topic.name}</h4>
                                                        <p className="text-xs text-muted-foreground font-medium">Core technical concepts & common interview questions</p>
                                                    </div>
                                                    {topicId === topic.id && <Check className="absolute top-4 right-4 text-primary" size={20} />}
                                                </button>
                                            ))
                                        )}
                                    </div>
                                </div>
                            </section>

                            {/* Step 2: Select Interview Type */}
                            <section className="relative pl-12 opacity-90 transition-opacity hover:opacity-100">
                                <div className="absolute left-[15px] top-[40px] bottom-[-48px] w-[2px] bg-primary/20 z-0"></div>
                                <div className={cn(
                                    "absolute left-0 top-0 size-8 rounded-full border-2 flex items-center justify-center text-sm font-bold z-10 transition-colors",
                                    interviewType ? "bg-primary text-white border-primary" : "bg-card border-border text-muted-foreground"
                                )}>
                                    {interviewType ? <CheckCircle2 size={16} /> : "2"}
                                </div>
                                <div className="flex flex-col gap-5">
                                    <h3 className="text-lg font-bold">Select Interview Type</h3>
                                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                                        {interviewTypes.map((type) => (
                                            <button
                                                key={type.id}
                                                onClick={() => setInterviewType(type.id)}
                                                className={cn(
                                                    "flex flex-col justify-between p-4 rounded-xl border transition-all text-center gap-3 min-h-[140px]",
                                                    interviewType === type.id ? "border-primary bg-primary/5 ring-1 ring-primary" : "border-border bg-card hover:border-primary/40"
                                                )}
                                            >
                                                <div className={cn(
                                                    "mx-auto size-10 rounded-full flex items-center justify-center transition-colors",
                                                    interviewType === type.id ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"
                                                )}>
                                                    <type.icon size={20} />
                                                </div>
                                                <div>
                                                    <h4 className="font-bold text-sm whitespace-nowrap">{type.title}</h4>
                                                    <p className="text-[10px] text-muted-foreground mt-1 leading-tight">{type.description}</p>
                                                </div>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </section>

                            {/* Step 3: Select Interview Format */}
                            <section className="relative pl-12">
                                <div className="absolute left-[15px] top-[40px] bottom-[-48px] w-[2px] bg-primary/20 z-0"></div>
                                <div className={cn(
                                    "absolute left-0 top-0 size-8 rounded-full border-2 flex items-center justify-center text-sm font-bold z-10 transition-colors",
                                    interviewMode ? "bg-primary text-white border-primary" : "bg-card border-border text-muted-foreground"
                                )}>
                                    {interviewMode ? <CheckCircle2 size={16} /> : "3"}
                                </div>
                                <div className="flex flex-col gap-5">
                                    <h3 className="text-lg font-bold">Select Interview Format</h3>
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                        {interviewModes.map((mode) => (
                                            <button
                                                key={mode.id}
                                                onClick={() => setInterviewMode(mode.id)}
                                                className={cn(
                                                    "p-5 rounded-xl border transition-all flex flex-col gap-4 text-left",
                                                    interviewMode === mode.id ? "border-primary bg-primary/5 ring-1 ring-primary" : "border-border bg-card hover:border-primary/40"
                                                )}
                                            >
                                                <div className="flex justify-between">
                                                    <span className="text-sm font-bold">{mode.title}</span>
                                                    <div className={cn(
                                                        "size-4 rounded-full border flex items-center justify-center transition-colors",
                                                        interviewMode === mode.id ? "border-primary bg-primary" : "border-border bg-card"
                                                    )}>
                                                        <div className="size-1.5 rounded-full bg-white"></div>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-2 pl-1">
                                                    <div className="size-8 rounded-full bg-muted border border-border flex items-center justify-center text-muted-foreground">
                                                        <mode.icon size={18} />
                                                    </div>
                                                </div>
                                                <p className="text-xs text-muted-foreground leading-relaxed">{mode.description}</p>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </section>

                            {/* Step 4: Difficulty */}
                            <section className="relative pl-12">
                                <div className="absolute left-[15px] top-[40px] bottom-[-48px] w-[2px] bg-primary/20 z-0"></div>
                                <div className={cn(
                                    "absolute left-0 top-0 size-8 rounded-full border-2 flex items-center justify-center text-sm font-bold z-10 transition-colors",
                                    difficulty ? "bg-primary text-white border-primary" : "bg-card border-border text-muted-foreground"
                                )}>
                                    {difficulty ? <CheckCircle2 size={16} /> : "4"}
                                </div>
                                <div className="flex flex-col gap-5">
                                    <h3 className="text-lg font-bold">Select Difficulty</h3>
                                    <div className="inline-flex rounded-xl p-1 bg-muted border border-border w-full md:w-auto self-start">
                                        {[Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD].map((lvl) => (
                                            <button
                                                key={lvl}
                                                onClick={() => setDifficulty(lvl)}
                                                className={cn(
                                                    "flex-1 md:flex-none px-8 py-2.5 rounded-lg text-sm font-bold transition-all",
                                                    difficulty === lvl ? "bg-primary text-white shadow-md scale-[1.02]" : "text-muted-foreground hover:text-foreground hover:bg-card/50"
                                                )}
                                            >
                                                {lvl.charAt(0) + lvl.slice(1).toLowerCase()}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </section>

                            {/* Step 5: Final Settings */}
                            <section className="relative pl-12 pb-20">
                                <div className="absolute left-0 top-0 size-8 rounded-full bg-card border-2 border-border text-muted-foreground flex items-center justify-center text-sm font-bold z-10">
                                    5
                                </div>
                                <div className="flex flex-col gap-5">
                                    <div className="bg-card rounded-xl shadow-sm border border-border overflow-hidden">
                                        <div className="flex items-center justify-between px-6 py-4 hover:bg-muted/50 transition-colors cursor-default">
                                            <div className="flex items-center gap-3">
                                                <div className="size-8 rounded-full bg-muted flex items-center justify-center text-muted-foreground">
                                                    <SlidersHorizontal size={18} />
                                                </div>
                                                <div>
                                                    <span className="block font-bold">Advanced Settings</span>
                                                    <span className="text-xs text-muted-foreground">Adaptive mode, duration</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="px-6 pb-6 pt-2 flex flex-col gap-6 border-t border-border">
                                            <div className="flex items-center justify-between">
                                                <div className="flex flex-col gap-0.5">
                                                    <span className="text-sm font-semibold">Adaptive Difficulty</span>
                                                    <span className="text-xs text-muted-foreground">AI adjusts difficulty based on performance</span>
                                                </div>
                                                <button
                                                    onClick={() => setAdaptive(!adaptive)}
                                                    className={cn(
                                                        "relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
                                                        adaptive ? "bg-primary" : "bg-muted"
                                                    )}
                                                >
                                                    <span className={cn(
                                                        "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
                                                        adaptive ? "translate-x-6" : "translate-x-1"
                                                    )} />
                                                </button>
                                            </div>
                                            <div className="flex flex-col gap-4">
                                                <div className="flex justify-between text-sm font-semibold">
                                                    <span>Session Duration</span>
                                                    <span className="text-primary font-bold">{durationMinutes}m</span>
                                                </div>
                                                <input
                                                    type="range"
                                                    min="15"
                                                    max="60"
                                                    step="5"
                                                    value={durationMinutes}
                                                    onChange={(e) => setDurationMinutes(parseInt(e.target.value))}
                                                    className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </section>
                        </div>

                        {/* Sidebar: Session Preview */}
                        <aside className="w-full xl:w-[360px] shrink-0">
                            <div className="sticky top-28 flex flex-col gap-4">
                                <div className="bg-card rounded-xl shadow-lg ring-1 ring-border p-6 flex flex-col gap-6">
                                    <div className="flex items-center justify-between border-b border-border pb-4">
                                        <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Session Preview</h3>
                                        <div className={cn(
                                            "flex items-center gap-2 rounded px-2 py-1 text-xs font-medium",
                                            hasReachedSessionLimit
                                                ? "bg-amber-500/10 text-amber-700 dark:text-amber-300"
                                                : "bg-primary/10 text-primary"
                                        )}>
                                            <span className={cn(
                                                "size-1.5 rounded-full",
                                                hasReachedSessionLimit ? "bg-amber-500" : "bg-primary animate-pulse"
                                            )}></span>
                                            {hasReachedSessionLimit ? "Limit reached" : "Ready"}
                                        </div>
                                    </div>

                                    <div className="flex flex-col gap-4">
                                        <div className="bg-muted/50 rounded-lg p-3 flex gap-4 items-center border border-border">
                                            <div className="size-10 bg-card rounded-md shadow-sm border border-border flex items-center justify-center text-primary shrink-0">
                                                <Gauge size={20} />
                                            </div>
                                            <div className="flex flex-col">
                                                <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider">Plan usage</span>
                                                <span className="text-sm font-bold truncate max-w-[180px]">
                                                    {isLoadingProfile ? "Loading..." : `${sessionsUsed} / ${sessionLimit} sessions used`}
                                                </span>
                                                <span className="text-xs text-muted-foreground">
                                                    {isLoadingProfile
                                                        ? "Checking current plan limits"
                                                        : hasReachedSessionLimit
                                                        ? "Start a new cycle or update your plan in Settings"
                                                        : `${sessionsRemaining} session${sessionsRemaining === 1 ? "" : "s"} remaining this cycle`}
                                                </span>
                                            </div>
                                        </div>

                                        <div className="bg-muted/50 rounded-lg p-3 flex gap-4 items-center border border-border">
                                            <div className="size-10 bg-card rounded-md shadow-sm border border-border flex items-center justify-center text-primary shrink-0">
                                                <Timer size={20} />
                                            </div>
                                            <div className="flex flex-col">
                                                <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider">Topic</span>
                                                <span className="text-sm font-bold truncate max-w-[180px]">
                                                    {topics.find(t => t.id === topicId)?.name || "Not Selected"}
                                                </span>
                                            </div>
                                        </div>

                                        <div className="space-y-4 pt-2">
                                            <div className="flex justify-between items-center text-sm">
                                                <span className="text-muted-foreground">Type</span>
                                                <span className="font-semibold capitalize">
                                                    {interviewType?.toLowerCase() || "—"}
                                                </span>
                                            </div>
                                            <div className="h-px bg-border w-full"></div>
                                            <div className="flex justify-between items-center text-sm">
                                                <span className="text-muted-foreground">Format</span>
                                                <span className="font-semibold capitalize">
                                                    {interviewMode ? interviewModes.find(m => m.id === interviewMode)?.title : "—"}
                                                </span>
                                            </div>
                                            <div className="h-px bg-border w-full"></div>
                                            <div className="flex justify-between items-center text-sm">
                                                <span className="text-muted-foreground">Difficulty</span>
                                                <span className="font-semibold flex items-center gap-1.5">
                                                    {difficulty ? (
                                                        <>
                                                            <span className={cn(
                                                                "size-2 rounded-full",
                                                                difficulty === Difficulty.EASY ? "bg-green-500" :
                                                                    difficulty === Difficulty.MEDIUM ? "bg-yellow-500" : "bg-red-500"
                                                            )}></span>
                                                            <span className="capitalize">{difficulty.toLowerCase()}</span>
                                                        </>
                                                    ) : "—"}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="pt-2">
                                        <button
                                            onClick={handleStartSession}
                                            disabled={!canStartSession}
                                            className="w-full group relative h-12 bg-primary hover:bg-primary/90 disabled:bg-muted disabled:text-muted-foreground disabled:cursor-not-allowed text-white font-bold rounded-xl shadow-md shadow-primary/10 transition-all active:scale-[0.98] flex items-center justify-center gap-2 overflow-hidden"
                                        >
                                            {createSession.isPending ? (
                                                <Loader2 className="animate-spin" size={20} />
                                            ) : (
                                                <>
                                                    <span className="relative z-10">{hasReachedSessionLimit ? "Session limit reached" : "Start Session"}</span>
                                                    {!hasReachedSessionLimit ? <ArrowRight size={20} className="relative z-10 group-hover:translate-x-1 transition-transform" /> : null}
                                                </>
                                            )}
                                        </button>
                                        <p className="text-[10px] text-muted-foreground text-center leading-relaxed mt-3 uppercase font-bold tracking-widest">
                                            {hasReachedSessionLimit
                                                ? "Open settings to review plan limits and upgrade options."
                                                : "Session recorded for AI analysis."}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </aside>
                    </div>
                </main>
            </div>
        </div>
    );
}
