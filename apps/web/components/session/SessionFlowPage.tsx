"use client";

import { useEffect, useState } from "react";
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

    useEffect(() => {
        if (!session || !sessionId) return;

        if (session.status === SessionStatus.CREATED && !startSession.isPending && !started) {
            setStarted(true);
            startSession.mutate(sessionId, {
                onSuccess: (response) => {
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
            !started
        ) {
            setStarted(true);
            generateQuestion.mutate(sessionId);
        }
    }, [session, sessionId, startSession, generateQuestion, started]);

    useEffect(() => {
        if (!session || session.status !== SessionStatus.ACTIVE) return;

        const interval = setInterval(() => setSeconds((value) => value + 1), 1000);
        return () => clearInterval(interval);
    }, [session]);

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

        try {
            await completeSession.mutateAsync(session.id);
            await analyzeSession.mutateAsync(session.id);
        } catch {
            // If analysis fails, the canonical session route still renders the retry state.
        }

        window.location.href = `/dashboard/sessions/${session.id}`;
    };

    if (isLoading) {
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
