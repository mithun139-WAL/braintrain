import { useState, type KeyboardEvent } from "react";
import { Brain, Loader2, StopCircle, Timer } from "lucide-react";
import { Session } from "@braintrain/shared";
import { useGenerateQuestion } from "@/hooks/mutations/useGenerateQuestion";
import { useSubmitResponse } from "@/hooks/mutations/useSubmitResponse";
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

export const LIVE_SESSION_MAX_QUESTIONS = 8;

export function useLiveSessionComposer({
    session,
    isEnding,
    onSubmitSuccess,
}: UseLiveSessionComposerOptions) {
    const [answerText, setAnswerText] = useState("");
    const submitResponse = useSubmitResponse(session.id);
    const generateQuestion = useGenerateQuestion();

    const questions = session.questions || [];
    const currentQuestion = questions[questions.length - 1];
    const isAnswered = currentQuestion?.responses?.length > 0;
    const isPendingNext = generateQuestion.isPending;
    const canSubmit =
        Boolean(answerText.trim()) &&
        questions.length > 0 &&
        !isAnswered &&
        !isPendingNext &&
        !submitResponse.isPending;

    const handleSubmit = () => {
        if (!canSubmit || !currentQuestion) return;

        submitResponse.mutate(
            {
                questionId: currentQuestion.id,
                answerText,
            },
            {
                onSuccess: () => {
                    setAnswerText("");

                    if (!isEnding) {
                        generateQuestion.mutate(session.id);
                    }

                    onSubmitSuccess?.();
                },
            }
        );
    };

    const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
        if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
            handleSubmit();
        }
    };

    return {
        answerText,
        canSubmit,
        currentQuestion,
        handleKeyDown,
        handleSubmit,
        isAnswered,
        isPendingNext,
        questions,
        setAnswerText,
        submitResponse,
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
