"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Loader2 } from "lucide-react";
import { InterviewMode, SessionStatus } from "@braintrain/shared";
import { useSession } from "@/hooks/queries/useSession";
import { useStartSession } from "@/hooks/mutations/useStartSession";
import { useGenerateQuestion } from "@/hooks/mutations/useGenerateQuestion";
import { useCompleteSession } from "@/hooks/mutations/useCompleteSession";
import { useAnalyzeSession } from "@/hooks/mutations/useAnalyzeSession";
import { OneOnOneSession } from "@/components/session/OneOnOneSession";
import { PanelSession } from "@/components/session/PanelSession";
import { HybridSession } from "@/components/session/HybridSession";
import { SessionEvaluationView } from "@/components/session/SessionEvaluationView";
import { VoiceInterviewSession } from "@/components/session/VoiceInterviewSession";
import { SessionBrand, SessionTimerPill, SessionEndButton } from "@/components/session/LiveSessionShared";
import { ChevronRight } from "lucide-react";
import { journeysApi } from "@/lib/api/journeys.api";

export function SessionFlowPage({ sessionId }: { sessionId: string }) {
    const { data: sessionData, isLoading } = useSession(sessionId);
    const session = sessionData?.data;
    const startSession = useStartSession();
    const generateQuestion = useGenerateQuestion();
    const completeSession = useCompleteSession();
    const analyzeSession = useAnalyzeSession();

    const [seconds, setSeconds] = useState(0);
    const [started, setStarted] = useState(false);
    const [isEnding, setIsEnding] = useState(false);
    // Voice mode state (initialized from session isVoice flag once loaded)
    const [isVoiceMode, setIsVoiceMode] = useState<boolean | null>(null);
    // Ref keeps the latest isVoiceMode value accessible inside stale callbacks.
    const isVoiceModeRef = useRef<boolean | null>(null);

    useEffect(() => {
        isVoiceModeRef.current = isVoiceMode;
    }, [isVoiceMode]);

    // Initialize voice mode once session is loaded
    useEffect(() => {
        if (session && isVoiceMode === null) {
            const initialMode = session.isVoice ?? true;
            setIsVoiceMode(initialMode);
            isVoiceModeRef.current = initialMode;
        }
    }, [session, isVoiceMode]);

    // localStorage key that persists this session's wall-clock start time across refreshes
    const timerStorageKey = `braintrain-timer-${sessionId}`;
    // Ensures timer-init logic runs only once per page load
    const timerInitializedRef = useRef(false);
    // Always-fresh ref to handleEndSession used by the auto-end effect
    const handleEndSessionRef = useRef<() => void>(() => {});


    useEffect(() => {
        if (!session || !sessionId || isVoiceMode === null) return;

        if (session.status === SessionStatus.CREATED && !startSession.isPending && !started) {
            setStarted(true);
            startSession.mutate(sessionId, {
                onSuccess: (response) => {
                    // In voice mode the voice agent manages its own questions —
                    // skip the chat question generator to avoid a redundant API call.
                    if (isVoiceModeRef.current) return;
                    const sessionQuestions = response.data.questions || [];
                    if (sessionQuestions.length === 0) {
                        generateQuestion.mutate(sessionId);
                    }
                },
            });
        }

        const hasNoQuestions = (session.questions?.length || 0) === 0;
        if (
            session.status === SessionStatus.ACTIVE &&
            hasNoQuestions &&
            !generateQuestion.isPending &&
            !startSession.isPending &&
            !started &&
            !isVoiceModeRef.current   // voice agent self-generates; skip in voice mode
        ) {
            setStarted(true);
            generateQuestion.mutate(sessionId);
        }
    }, [session, sessionId, startSession, generateQuestion, started]);

    // Restore or record the timer's wall-clock start when the session first becomes ACTIVE.
    // Reading from localStorage makes elapsed time survive page refreshes.
    useEffect(() => {
        if (!session || session.status !== SessionStatus.ACTIVE) return;
        if (timerInitializedRef.current) return;
        timerInitializedRef.current = true;

        const stored = localStorage.getItem(timerStorageKey);
        if (stored) {
            // Session was already running before the refresh — restore elapsed seconds
            const startedAt = parseInt(stored, 10);
            if (!isNaN(startedAt)) {
                const elapsed = Math.max(0, Math.floor((Date.now() - startedAt) / 1000));
                setSeconds(elapsed);
            }
        } else {
            // First time this session becomes active — record the start timestamp
            localStorage.setItem(timerStorageKey, String(Date.now()));
        }
    }, [session, timerStorageKey]);

    // Increment the elapsed counter every second while the session is ACTIVE
    useEffect(() => {
        if (!session || session.status !== SessionStatus.ACTIVE) return;

        const interval = setInterval(() => setSeconds((v) => v + 1), 1000);
        return () => clearInterval(interval);
    }, [session]);

    // Auto-end the session when elapsed time reaches the configured duration limit
    useEffect(() => {
        if (!session || session.status !== SessionStatus.ACTIVE || isEnding) return;
        if (!session.durationMinutes) return;

        const limitSeconds = session.durationMinutes * 60;
        if (seconds >= limitSeconds) {
            handleEndSessionRef.current();
        }
    }, [seconds, session, isEnding]);

    const formatTime = (totalSeconds: number) => {
        const minutes = Math.floor(totalSeconds / 60)
            .toString()
            .padStart(2, "0");
        const remainingSeconds = (totalSeconds % 60).toString().padStart(2, "0");
        return `${minutes}:${remainingSeconds}`;
    };

    const handleEndSession = async () => {
        if (!session || isEnding) return;

        setIsEnding(true);
        localStorage.removeItem(timerStorageKey);

        try {
            await completeSession.mutateAsync(session.id);

            // If this session was created by a journey round, mark the round complete
            const journeyCtx = session.personalityConfig?.journeyContext as
                { journeyId: string; journeySessionId: string } | undefined;
            if (journeyCtx) {
                await journeysApi.completeRound(
                    journeyCtx.journeyId,
                    journeyCtx.journeySessionId,
                    session.id,
                );
            }

            await analyzeSession.mutateAsync(session.id);
        } catch {
            // If analysis fails, the canonical session route still renders the retry state.
        }

        window.location.href = `/dashboard/sessions/${session.id}`;
    };
    // Keep the ref in sync so the auto-end effect always invokes the latest closure
    handleEndSessionRef.current = handleEndSession;

    if (isLoading || isVoiceMode === null) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-gray-950">
                <Loader2 className="animate-spin text-primary" size={48} />
            </div>
        );
    }

    if (!session) {
        return (
            <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-slate-50 dark:bg-gray-950">
                <h1 className="text-2xl font-bold">Session not found</h1>
                <Link href="/dashboard" className="text-primary hover:underline">
                    Return to Dashboard
                </Link>
            </div>
        );
    }

    if (session.status === SessionStatus.ANALYZED || session.status === SessionStatus.COMPLETED) {
        return <SessionEvaluationView sessionId={sessionId} />;
    }

    if (isVoiceMode) {
        return (
            <div className="flex flex-col h-screen bg-slate-950 text-white overflow-hidden">
                <header className="sticky top-0 z-50 w-full flex-shrink-0 bg-gray-950/90 backdrop-blur-md border-b border-gray-800">
                    <div className="max-w-[1400px] mx-auto px-4 h-16 flex items-center justify-between gap-4">
                        <div className="flex items-center gap-3">
                            <SessionBrand
                                className="flex-shrink-0 gap-2"
                                iconWrapperClassName="size-7 rounded-lg bg-primary/15 flex items-center justify-center"
                                iconSize={16}
                                labelClassName="hidden text-sm font-bold tracking-tight text-white sm:block"
                            />
                            <ChevronRight size={14} className="text-gray-600 hidden sm:block" />
                            <h1 className="font-semibold text-sm text-gray-200 capitalize truncate">
                                {session.topicName || "Session"} (Voice Mode)
                            </h1>
                        </div>
                        
                        <div className="flex items-center gap-4">
                            <SessionTimerPill
                                time={formatTime(seconds)}
                                className="border border-gray-700 bg-gray-900 flex"
                                iconSize={14}
                                textClassName="text-sm font-semibold tracking-widest text-white"
                            />
                            <SessionEndButton
                                isEnding={isEnding}
                                onClick={handleEndSession}
                                className="rounded-lg px-4 py-2 text-sm font-semibold text-red-400 hover:bg-red-500/20 hover:text-white"
                                labelClassName="hidden sm:inline"
                            />
                        </div>
                    </div>
                </header>
                <main className="flex-1 flex flex-col p-4 md:p-6 max-w-[1400px] mx-auto w-full min-h-0 overflow-hidden" style={{ height: "calc(100vh - 64px)" }}>
                    <VoiceInterviewSession
                        sessionId={session.id}
                        candidateName="Candidate"
                        onEndSession={handleEndSession}
                        interviewMode={session.interviewMode}
                    />
                </main>
            </div>
        );
    }

    const sessionProps = {
        session,
        seconds,
        formatTime,
        isEnding,
        onEndSession: handleEndSession,
    };

    switch (session.interviewMode) {
        case InterviewMode.ONE_ON_ONE_AI:
            return <OneOnOneSession {...sessionProps} />;
        case InterviewMode.PANEL_AI:
            return <PanelSession {...sessionProps} />;
        case InterviewMode.HYBRID:
            return <HybridSession {...sessionProps} />;
        default:
            return <OneOnOneSession {...sessionProps} />;
    }

}
