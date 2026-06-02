"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
    ChevronLeft,
    Brain,
    MessageSquare,
    Terminal,
    Users,
    SlidersHorizontal,
    Crown,
    AlertTriangle,
    Loader2,
    ArrowRight,
    Volume2,
    Keyboard,
    Activity,
    Check,
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

export default function StartSessionPage() {
    const searchParams = useSearchParams();
    const presetTopicId = searchParams.get("topicId");
    const router = useRouter();

    const {
        step,
        topicId,
        interviewType,
        interviewMode,
        difficulty,
        adaptive,
        durationMinutes,
        isVoice,
        setTopicId,
        setInterviewType,
        setInterviewMode,
        setDifficulty,
        setAdaptive,
        setDurationMinutes,
        setIsVoice,
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

    // Session limits check
    const sessionLimit = isPro
        ? 20
        : (isVoice ? (profile?.voiceSessionLimit ?? 1) : (profile?.chatSessionLimit ?? 3));
    const sessionsUsed = isPro
        ? (profile?.monthlySessionCount ?? 0)
        : (isVoice ? (profile?.voiceSessionCount ?? 0) : (profile?.chatSessionCount ?? 0));

    const sessionsRemaining = Math.max(0, sessionLimit - sessionsUsed);
    const hasReachedSessionLimit = sessionsRemaining === 0;

    useEffect(() => {
        reset();
        if (presetTopicId) {
            setTopicId(presetTopicId);
        }
    }, [presetTopicId, reset, setTopicId]);

    useEffect(() => {
        if (!isLoadingProfile && !isPro) {
            setDurationMinutes(15);
            setInterviewMode(InterviewMode.ONE_ON_ONE_AI);
        }
    }, [isPro, isLoadingProfile, setDurationMinutes, setInterviewMode]);

    const handleStartSession = () => {
        if (!topicId || !interviewType || !interviewMode || hasReachedSessionLimit) return;

        createSession.mutate({
            topicId,
            interviewType: interviewType as any,
            interviewMode: interviewMode as any,
            difficulty: difficulty as any,
            adaptive,
            durationMinutes,
            isVoice
        });
    };

    const topics = topicsData?.data || [];

    // Experience mapping helper
    const getExperienceLabel = (diff: Difficulty) => {
        if (diff === Difficulty.EASY) return "Junior";
        if (diff === Difficulty.MEDIUM) return "Mid-Level";
        return "Senior";
    };

    const handleSelectStyle = (styleKey: "conversational" | "technical" | "panel") => {
        if (styleKey === "conversational") {
            setInterviewType(InterviewType.BEHAVIORAL);
            setInterviewMode(InterviewMode.ONE_ON_ONE_AI);
        } else if (styleKey === "technical") {
            setInterviewType(InterviewType.TECHNICAL);
            setInterviewMode(InterviewMode.ONE_ON_ONE_AI);
        } else if (styleKey === "panel") {
            setInterviewType(InterviewType.MIXED);
            setInterviewMode(InterviewMode.PANEL_AI);
        }
    };

    const currentStyleKey = () => {
        if (interviewMode === InterviewMode.PANEL_AI) return "panel";
        if (interviewType === InterviewType.TECHNICAL) return "technical";
        if (interviewType === InterviewType.BEHAVIORAL) return "conversational";
        return null;
    };

    const canContinue = () => {
        if (step === 1) return !!topicId;
        if (step === 2) return !!currentStyleKey();
        if (step === 3) return !!difficulty;
        if (step === 4) return true;
        return false;
    };

    // Calculate step state for custom rendering
    const maxSteps = 5;

    return (
        <div className="min-h-screen bg-background text-foreground flex flex-col font-sans selection:bg-primary/10 selection:text-primary">
            {/* Simple Top Header */}
            <header className="flex items-center justify-between border-b border-border/60 bg-background/50 px-6 py-4 sticky top-0 z-50 backdrop-blur-md">
                <div className="flex items-center gap-3">
                    <Link href="/dashboard">
                        <button className="flex items-center justify-center size-8 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors">
                            <ChevronLeft size={16} />
                        </button>
                    </Link>
                    <div className="h-4 w-px bg-border/60"></div>
                    <span className="text-xs font-medium text-muted-foreground">Cancel practice</span>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground font-medium">
                    <span>Step {step} of {maxSteps}</span>
                </div>
            </header>

            {/* Main setup area */}
            <main className="flex-grow flex items-center justify-center p-6">
                <div className="w-full max-w-lg mx-auto flex flex-col gap-8">
                    
                    {/* Progress Indicator line */}
                    {step < 5 && (
                        <div className="flex gap-2 w-full justify-between items-center px-1">
                            {Array.from({ length: 4 }).map((_, i) => (
                                <div
                                    key={i}
                                    className={cn(
                                        "h-1 flex-1 rounded-full transition-all duration-300",
                                        step > i ? "bg-primary" : "bg-border/60"
                                    )}
                                />
                            ))}
                        </div>
                    )}

                    {/* Step Content */}
                    <div className="min-h-[350px] flex flex-col justify-between">
                        <div>
                            {step === 1 && (
                                <div className="space-y-6 animate-fade-in">
                                    <div className="space-y-1">
                                        <h2 className="text-display-md font-semibold text-foreground">What area are you focusing on?</h2>
                                        <p className="text-body-sm text-muted-foreground">Select a topic for your interview simulation.</p>
                                    </div>

                                    {hasReachedSessionLimit && (
                                        <div className="p-4 rounded-xl border border-warning/20 bg-warning/5 text-warning text-xs space-y-2">
                                            <div className="flex items-center gap-2 font-semibold">
                                                <AlertTriangle size={14} />
                                                Session Limit Reached
                                            </div>
                                            <p className="text-muted-foreground">
                                                You have used your limit of {sessionLimit} sessions. Please update your subscription in settings to continue.
                                            </p>
                                        </div>
                                    )}

                                    <div className="flex flex-col gap-2">
                                        {isLoadingTopics ? (
                                            <div className="h-40 flex items-center justify-center">
                                                <Loader2 className="animate-spin text-primary" size={24} />
                                            </div>
                                        ) : (
                                            topics.map((topic) => (
                                                <button
                                                    key={topic.id}
                                                    type="button"
                                                    onClick={() => setTopicId(topic.id)}
                                                    className={cn(
                                                        "w-full text-left p-4 rounded-xl border transition-colors flex items-center justify-between",
                                                        topicId === topic.id
                                                            ? "border-primary bg-primary/5 text-primary"
                                                            : "border-border hover:border-primary/40 text-foreground bg-card"
                                                    )}
                                                >
                                                    <div className="flex items-center gap-3">
                                                        <Brain size={16} className={cn(topicId === topic.id ? "text-primary" : "text-muted-foreground")} />
                                                        <span className="text-sm font-medium">{topic.name}</span>
                                                    </div>
                                                    {topicId === topic.id && <Check size={16} />}
                                                </button>
                                            ))
                                        )}
                                    </div>
                                </div>
                            )}

                            {step === 2 && (
                                <div className="space-y-6 animate-fade-in">
                                    <div className="space-y-1">
                                        <h2 className="text-display-md font-semibold text-foreground">Select Interview Style & Medium</h2>
                                        <p className="text-body-sm text-muted-foreground">Choose your communication mode and interviewer format.</p>
                                    </div>

                                    {/* Medium Selection Toggle */}
                                    <div className="space-y-2">
                                        <label className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Medium</label>
                                        <div className="grid grid-cols-2 gap-2 bg-muted/30 p-1 rounded-xl border border-border/40">
                                            <button
                                                type="button"
                                                onClick={() => setIsVoice(true)}
                                                className={cn(
                                                    "py-2.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-all",
                                                    isVoice ? "bg-card text-primary border border-border/50 shadow-sm" : "text-muted-foreground hover:text-foreground"
                                                )}
                                            >
                                                <Volume2 size={14} />
                                                Real-time Voice
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => setIsVoice(false)}
                                                className={cn(
                                                    "py-2.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-all",
                                                    !isVoice ? "bg-card text-primary border border-border/50 shadow-sm" : "text-muted-foreground hover:text-foreground"
                                                )}
                                            >
                                                <Keyboard size={14} />
                                                Chat / Text
                                            </button>
                                        </div>
                                    </div>

                                    {/* Style Selection Options */}
                                    <div className="space-y-2">
                                        <label className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Format</label>
                                        <div className="flex flex-col gap-2">
                                            {[
                                                {
                                                    key: "conversational",
                                                    label: "Conversational",
                                                    desc: "1:1 discussion focusing on behavioral questions and STAR alignment.",
                                                    icon: MessageSquare
                                                },
                                                {
                                                    key: "technical",
                                                    label: "Technical",
                                                    desc: "1:1 session focusing on technical knowledge, problem solving, and analytical thinking.",
                                                    icon: Terminal
                                                },
                                                {
                                                    key: "panel",
                                                    label: "Panel Interview",
                                                    desc: "Practice with multiple AI personas, each evaluating different criteria.",
                                                    icon: Users,
                                                    proOnly: true
                                                }
                                            ].map((style) => {
                                                const isLocked = style.proOnly && !isPro;
                                                const isSelected = currentStyleKey() === style.key;
                                                return (
                                                    <button
                                                        key={style.key}
                                                        type="button"
                                                        disabled={isLocked}
                                                        onClick={() => handleSelectStyle(style.key as any)}
                                                        className={cn(
                                                            "w-full text-left p-4 rounded-xl border transition-colors relative flex items-start gap-3",
                                                            isSelected
                                                                ? "border-primary bg-primary/5 text-primary"
                                                                : "border-border text-foreground bg-card hover:border-primary/40",
                                                            isLocked && "opacity-50 cursor-not-allowed bg-muted/10 hover:border-border"
                                                        )}
                                                    >
                                                        <style.icon size={16} className="mt-0.5 shrink-0 text-muted-foreground" />
                                                        <div className="space-y-0.5">
                                                            <div className="flex items-center gap-2">
                                                                <span className="text-sm font-semibold">{style.label}</span>
                                                                {isLocked && (
                                                                    <span className="flex items-center gap-0.5 text-[9px] font-semibold text-warning bg-warning/10 px-1.5 py-0.5 rounded-full uppercase tracking-wider">
                                                                        <Crown size={8} /> Pro
                                                                    </span>
                                                                )}
                                                            </div>
                                                            <p className="text-xs text-muted-foreground leading-relaxed">{style.desc}</p>
                                                        </div>
                                                        {isSelected && <Check size={16} className="absolute right-4 top-4 shrink-0" />}
                                                    </button>
                                                );
                                            })}
                                        </div>
                                    </div>
                                </div>
                            )}

                            {step === 3 && (
                                <div className="space-y-6 animate-fade-in">
                                    <div className="space-y-1">
                                        <h2 className="text-display-md font-semibold text-foreground">Select Experience Level</h2>
                                        <p className="text-body-sm text-muted-foreground">Adjusts the complexity and tone of the interviewer's prompts.</p>
                                    </div>

                                    <div className="flex flex-col gap-2">
                                        {[
                                            { lvl: Difficulty.EASY, label: "Junior", desc: "Foundational questions, supportive guidance, focus on core skills." },
                                            { lvl: Difficulty.MEDIUM, label: "Mid-Level", desc: "Standard production scenarios, typical architectural trade-offs." },
                                            { lvl: Difficulty.HARD, label: "Senior", desc: "Complex systems design, ambiguous challenges, high-pressure leadership." }
                                        ].map((item) => (
                                            <button
                                                key={item.lvl}
                                                type="button"
                                                onClick={() => setDifficulty(item.lvl)}
                                                className={cn(
                                                    "w-full text-left p-4 rounded-xl border transition-colors flex items-start gap-3 justify-between",
                                                    difficulty === item.lvl
                                                        ? "border-primary bg-primary/5 text-primary"
                                                        : "border-border text-foreground bg-card hover:border-primary/40"
                                                )}
                                            >
                                                <div className="space-y-0.5">
                                                    <span className="text-sm font-semibold">{item.label}</span>
                                                    <p className="text-xs text-muted-foreground leading-relaxed">{item.desc}</p>
                                                </div>
                                                {difficulty === item.lvl && <Check size={16} className="mt-1 shrink-0" />}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {step === 4 && (
                                <div className="space-y-6 animate-fade-in">
                                    <div className="space-y-1">
                                        <h2 className="text-display-md font-semibold text-foreground">Duration & Complexity</h2>
                                        <p className="text-body-sm text-muted-foreground">Configure the length and adaptiveness of this session.</p>
                                    </div>

                                    <div className="space-y-5 p-6 border border-border/80 bg-card rounded-xl">
                                        {/* Adaptive Toggle */}
                                        <div className="flex items-center justify-between">
                                            <div className="space-y-0.5">
                                                <span className="text-sm font-semibold text-foreground">Adaptive Response Mode</span>
                                                <p className="text-xs text-muted-foreground leading-normal">
                                                    AI adjusts complexity based on your answers
                                                </p>
                                            </div>
                                            <button
                                                type="button"
                                                onClick={() => setAdaptive(!adaptive)}
                                                className={cn(
                                                    "relative inline-flex h-5 w-9 items-center rounded-full transition-colors",
                                                    adaptive ? "bg-primary" : "bg-muted"
                                                )}
                                            >
                                                <span className={cn(
                                                    "inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform",
                                                    adaptive ? "translate-x-5" : "translate-x-0.5"
                                                )} />
                                            </button>
                                        </div>

                                        <div className="h-px bg-border/60" />

                                        {/* Duration Selector */}
                                        <div className="space-y-3">
                                            <div className="flex justify-between items-baseline">
                                                <span className="text-sm font-semibold text-foreground">Session Duration</span>
                                                <span className="text-sm font-bold text-primary">{durationMinutes}m</span>
                                            </div>
                                            <input
                                                type="range"
                                                min="15"
                                                max={isPro ? "60" : "15"}
                                                step="15"
                                                value={durationMinutes}
                                                disabled={!isPro}
                                                onChange={(e) => setDurationMinutes(parseInt(e.target.value))}
                                                className="w-full h-1 bg-muted rounded-lg appearance-none cursor-pointer accent-primary disabled:opacity-50"
                                            />
                                            {!isPro && (
                                                <span className="text-[10px] text-warning font-medium flex items-center gap-1 mt-1.5">
                                                    <Crown size={11} /> Longer custom durations require a PRO account. Max 15 mins for Free plan.
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            )}

                            {step === 5 && (
                                <div className="space-y-8 text-center py-8 animate-fade-in flex flex-col items-center">
                                    <div className="size-12 rounded-full bg-primary/10 text-primary flex items-center justify-center mb-2">
                                        <Activity size={20} className="animate-pulse" />
                                    </div>
                                    
                                    <div className="max-w-md space-y-4">
                                        <h2 className="text-display-md font-semibold tracking-tight text-foreground">Take a moment.</h2>
                                        <p className="text-body-md text-muted-foreground leading-relaxed">
                                            This session is designed to help you improve, <br />
                                            not judge you.
                                        </p>
                                        <p className="text-body-md text-muted-foreground leading-relaxed">
                                            The interviewer will challenge your thinking <br />
                                            like a real interview.
                                        </p>
                                        <p className="text-body-md text-foreground font-medium pt-2">
                                            Ready when you are.
                                        </p>
                                    </div>

                                    {hasReachedSessionLimit && (
                                        <div className="p-4 rounded-xl border border-warning/20 bg-warning/5 text-warning text-xs text-left max-w-sm mt-4">
                                            <div className="flex items-center gap-2 font-bold mb-1">
                                                <AlertTriangle size={14} />
                                                Usage Limit Exceeded
                                            </div>
                                            <p className="text-muted-foreground leading-normal">
                                                You cannot start a new session because your account has exhausted its cycles. You can manage or upgrade your plan in settings.
                                            </p>
                                        </div>
                                    )}

                                    <div className="w-full pt-6">
                                        <button
                                            type="button"
                                            onClick={handleStartSession}
                                            disabled={hasReachedSessionLimit || createSession.isPending}
                                            className="w-full h-11 bg-primary text-white text-[13px] font-semibold rounded-lg hover:brightness-105 active:scale-[0.98] transition-all flex items-center justify-center gap-1.5 shadow-sm disabled:opacity-40 disabled:pointer-events-none"
                                        >
                                            {createSession.isPending ? (
                                                <Loader2 className="animate-spin" size={16} />
                                            ) : (
                                                <>
                                                    <span>Ready when you are</span>
                                                    <ArrowRight size={14} />
                                                </>
                                            )}
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Navigation Buttons for Step 1-4 */}
                        {step < 5 && (
                            <div className="flex justify-between items-center pt-8 border-t border-border/40 mt-8">
                                <button
                                    type="button"
                                    onClick={prevStep}
                                    disabled={step === 1}
                                    className="h-10 px-4 rounded-lg text-xs font-semibold text-muted-foreground hover:bg-muted/50 hover:text-foreground disabled:opacity-0 transition-all"
                                >
                                    Back
                                </button>
                                <button
                                    type="button"
                                    onClick={nextStep}
                                    disabled={!canContinue()}
                                    className="h-10 px-6 rounded-lg text-xs font-semibold bg-primary text-white hover:brightness-105 disabled:opacity-30 disabled:pointer-events-none transition-all flex items-center gap-1.5"
                                >
                                    <span>Continue</span>
                                    <ArrowRight size={12} />
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}
