import { useState, type KeyboardEvent } from "react";
import { Brain, Loader2, StopCircle, Timer } from "lucide-react";
import { Session } from "@braintrain/shared";
import { useGenerateQuestion } from "@/hooks/mutations/useGenerateQuestion";
import { useSubmitResponse } from "@/hooks/mutations/useSubmitResponse";
import { useCheckFollowup } from "@/hooks/mutations/useCheckFollowup";
import { type FollowupExchange } from "@/lib/api/responses.api";
import { cn } from "@/lib/utils";

export interface LiveSessionProps {
    session: Session;
    seconds: number;
    formatTime: (s: number) => string;
    isEnding: boolean;
    onEndSession: () => void;
}

interface UseLiveSessionComposerOptions {
    session: Session;
    isEnding: boolean;
    onSubmitSuccess?: () => void;
}

interface SessionBrandProps {
    className?: string;
    iconClassName?: string;
    iconWrapperClassName?: string;
    iconSize?: number;
    label?: string;
    labelClassName?: string;
}

interface SessionTimerPillProps {
    time: string;
    className?: string;
    iconClassName?: string;
    iconSize?: number;
    textClassName?: string;
}

interface SessionEndButtonProps {
    isEnding: boolean;
    onClick: () => void;
    className?: string;
    iconSize?: number;
    labelClassName?: string;
}

/**
 * State for the real-time follow-up coaching loop.
 *
 * When `isActive` is true, the UI shows the current follow-up question
 * and the textarea is repurposed for answering it.
 * `exchanges` accumulates all prior follow-up Q&A rounds for the current question.
 * `currentResponseId` links back to the DB response so the backend can load the
 * original answer without us re-sending it on every probe call.
 */
export interface FollowupState {
    isActive: boolean;
    currentResponseId: string | null;
    currentFollowupQuestion: string | null;
    acknowledgement: string | null;
    exchanges: FollowupExchange[];
}

const INITIAL_FOLLOWUP_STATE: FollowupState = {
    isActive: false,
    currentResponseId: null,
    currentFollowupQuestion: null,
    acknowledgement: null,
    exchanges: [],
};

export const LIVE_SESSION_MAX_QUESTIONS = 8;

export function useLiveSessionComposer({
    session,
    isEnding,
    onSubmitSuccess,
}: UseLiveSessionComposerOptions) {
    const [answerText, setAnswerText] = useState("");
    const [followupAnswerText, setFollowupAnswerText] = useState("");
    const [followupState, setFollowupState] = useState<FollowupState>(INITIAL_FOLLOWUP_STATE);

    const submitResponse = useSubmitResponse(session.id);
    const generateQuestion = useGenerateQuestion();
    const checkFollowup = useCheckFollowup();

    const questions = session.questions || [];
    const currentQuestion = questions[questions.length - 1];
    const isAnswered = currentQuestion?.responses?.length > 0;
    const isPendingNext = generateQuestion.isPending;
    const isCheckingFollowup = checkFollowup.isPending;

    // Main answer can only be submitted if no follow-up is active
    const canSubmit =
        Boolean(answerText.trim()) &&
        questions.length > 0 &&
        !isAnswered &&
        !isPendingNext &&
        !submitResponse.isPending &&
        !followupState.isActive;

    // Follow-up answer requires the follow-up to be active and non-empty
    const canSubmitFollowup =
        followupState.isActive &&
        Boolean(followupAnswerText.trim()) &&
        !isCheckingFollowup &&
        !isPendingNext;

    // ── After the follow-up signal is resolved, advance to next question ─────
    const _advanceToNextQuestion = () => {
        setFollowupState(INITIAL_FOLLOWUP_STATE);
        setFollowupAnswerText("");
        if (!isEnding) {
            generateQuestion.mutate(session.id);
        }
    };

    // ── Initial answer submit ─────────────────────────────────────────────────
    const handleSubmit = () => {
        if (!canSubmit || !currentQuestion) return;

        submitResponse.mutate(
            { questionId: currentQuestion.id, answerText },
            {
                onSuccess: (data) => {
                    setAnswerText("");
                    onSubmitSuccess?.();

                    // Immediately check whether a follow-up probe is needed
                    const responseId = data?.data?.id;
                    if (!responseId) {
                        // Fallback: no response ID means we can't run follow-up
                        _advanceToNextQuestion();
                        return;
                    }

                    checkFollowup.mutate(
                        {
                            questionId: currentQuestion.id,
                            responseId,
                            priorExchanges: [],
                        },
                        {
                            onSuccess: (result) => {
                                if (result.needsFollowup && result.followupQuestion) {
                                    // Activate follow-up mode
                                    setFollowupState({
                                        isActive: true,
                                        currentResponseId: responseId,
                                        currentFollowupQuestion: result.followupQuestion,
                                        acknowledgement: result.acknowledgement,
                                        exchanges: [],
                                    });
                                } else {
                                    // Answer is complete — show acknowledgement briefly then advance
                                    setFollowupState({
                                        isActive: false,
                                        currentResponseId: responseId,
                                        currentFollowupQuestion: null,
                                        acknowledgement: result.acknowledgement,
                                        exchanges: [],
                                    });
                                    _advanceToNextQuestion();
                                }
                            },
                            onError: () => {
                                // If follow-up check fails, gracefully proceed
                                _advanceToNextQuestion();
                            },
                        }
                    );
                },
            }
        );
    };

    // ── Follow-up answer submit ───────────────────────────────────────────────
    const handleFollowupSubmit = () => {
        if (!canSubmitFollowup || !currentQuestion || !followupState.currentResponseId || !followupState.currentFollowupQuestion) return;

        const newExchange: FollowupExchange = {
            followupQuestion: followupState.currentFollowupQuestion,
            followupAnswer: followupAnswerText,
        };
        const updatedExchanges = [...followupState.exchanges, newExchange];

        checkFollowup.mutate(
            {
                questionId: currentQuestion.id,
                responseId: followupState.currentResponseId,
                priorExchanges: updatedExchanges,
            },
            {
                onSuccess: (result) => {
                    setFollowupAnswerText("");

                    if (result.needsFollowup && result.followupQuestion) {
                        // Another gap found — present next probe
                        setFollowupState((prev) => ({
                            ...prev,
                            currentFollowupQuestion: result.followupQuestion!,
                            acknowledgement: result.acknowledgement,
                            exchanges: updatedExchanges,
                        }));
                    } else {
                        // Complete or max rounds reached — move on
                        setFollowupState({
                            isActive: false,
                            currentResponseId: followupState.currentResponseId,
                            currentFollowupQuestion: null,
                            acknowledgement: result.acknowledgement,
                            exchanges: updatedExchanges,
                        });
                        _advanceToNextQuestion();
                    }
                },
                onError: () => {
                    setFollowupAnswerText("");
                    _advanceToNextQuestion();
                },
            }
        );
    };

    const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
        if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
            if (followupState.isActive) {
                handleFollowupSubmit();
            } else {
                handleSubmit();
            }
        }
    };

    return {
        answerText,
        setAnswerText,
        followupAnswerText,
        setFollowupAnswerText,
        followupState,
        canSubmit,
        canSubmitFollowup,
        currentQuestion,
        handleKeyDown,
        handleSubmit,
        handleFollowupSubmit,
        isAnswered,
        isPendingNext,
        isCheckingFollowup,
        questions,
        submitResponse,
        checkFollowup,
    };
}

export function SessionBrand({
    className,
    iconClassName,
    iconWrapperClassName,
    iconSize = 24,
    label = "BrainTrain",
    labelClassName,
}: SessionBrandProps) {
    const icon = <Brain className={cn("text-primary", iconClassName)} size={iconSize} />;

    return (
        <div className={cn("flex items-center gap-3", className)}>
            {iconWrapperClassName ? (
                <div className={iconWrapperClassName}>{icon}</div>
            ) : (
                icon
            )}
            <span className={labelClassName}>{label}</span>
        </div>
    );
}

export function SessionTimerPill({
    time,
    className,
    iconClassName,
    iconSize = 16,
    textClassName,
}: SessionTimerPillProps) {
    return (
        <div className={cn("flex items-center gap-2 rounded-full px-4 py-1.5", className)}>
            <Timer className={cn("text-primary", iconClassName)} size={iconSize} />
            <span className={cn("font-mono", textClassName)}>{time}</span>
        </div>
    );
}

export function SessionEndButton({
    isEnding,
    onClick,
    className,
    iconSize = 16,
    labelClassName,
}: SessionEndButtonProps) {
    return (
        <button
            onClick={onClick}
            disabled={isEnding}
            className={cn("group flex items-center gap-2 transition-all", className)}
        >
            {isEnding ? (
                <Loader2 size={iconSize} className="animate-spin" />
            ) : (
                <StopCircle size={iconSize} className="transition-transform group-hover:scale-110" />
            )}
            <span className={labelClassName}>{isEnding ? "Ending..." : "End Session"}</span>
        </button>
    );
}
