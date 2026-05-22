import React, { useEffect, useRef } from "react";
import {
    Bot,
    Eye,
    Mic,
    MicOff,
    Send,
    ThumbsUp,
    ThumbsDown,
    ChevronLeft,
    Loader2,
} from "lucide-react";
import { Code } from "lucide-react";
import { cn } from "@/lib/utils";
import {
    type LiveSessionProps,
    SessionBrand,
    SessionEndButton,
    SessionTimerPill,
    useLiveSessionComposer,
} from "@/components/session/LiveSessionShared";
import { useSpeechSynthesis } from "@/hooks/useSpeechSynthesis";
import { useSpeechRecognition } from "@/hooks/useSpeechRecognition";

export const HybridSession: React.FC<LiveSessionProps> = ({
    session,
    seconds,
    formatTime,
    isEnding,
    onEndSession,
    setIsVoiceMode,
}) => {
    const prevQuestionCountRef = useRef(0);

    const {
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
    } = useLiveSessionComposer({ session, isEnding });

    // ── Text-to-Speech ────────────────────────────────────────────────────────
    const { speak, stop: stopSpeaking, isSpeaking, isSupported: isTTSSupported } = useSpeechSynthesis();

    // ── Speech-to-Text ────────────────────────────────────────────────────────
    const { startListening, stopListening, isListening, isSupported: isSTTSupported } = useSpeechRecognition({
        onTranscriptChange: (fullText) => {
            if (followupState.isActive) {
                setFollowupAnswerText(fullText);
            } else {
                setAnswerText(fullText);
            }
        },
    });

    // Auto-speak each new AI question
    useEffect(() => {
        if (!isTTSSupported) return;
        if (questions.length > prevQuestionCountRef.current) {
            prevQuestionCountRef.current = questions.length;
            const latest = questions[questions.length - 1];
            if (latest?.content) {
                setTimeout(() => speak(latest.content), 500);
            }
        }
    }, [questions.length, speak, isTTSSupported]);

    const prevFollowupQuestionRef = useRef<string | null>(null);

    // Auto-speak follow-up probes when they arrive
    useEffect(() => {
        if (!isTTSSupported) return;
        const fq = followupState.currentFollowupQuestion;
        if (fq && fq !== prevFollowupQuestionRef.current) {
            prevFollowupQuestionRef.current = fq;
            setTimeout(() => speak(fq), 300);
        }
    }, [followupState.currentFollowupQuestion, speak, isTTSSupported]);

    // Stop speech when session ends
    useEffect(() => {
        if (isEnding) stopSpeaking();
    }, [isEnding, stopSpeaking]);

    const handleMicToggle = () => {
        if (isListening) {
            stopListening();
        } else {
            if (isSpeaking) stopSpeaking();
            const base = followupState.isActive ? followupAnswerText : answerText;
            startListening(base);
        }
    };

    return (
        <div className="min-h-screen flex flex-col bg-background text-foreground font-display selection:bg-primary/30 selection:text-white">
            {/* Header */}
            <header className="sticky top-0 z-50 w-full bg-background/80 backdrop-blur-md border-b border-border flex items-center justify-between whitespace-nowrap px-6 py-4 shrink-0">
                <div className="flex items-center gap-4">
                    <button
                        onClick={onEndSession}
                        disabled={isEnding}
                        className="flex items-center justify-center size-8 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50"
                    >
                            <ChevronLeft size={20} />
                        </button>
                    <SessionTimerPill
                        time={formatTime(seconds)}
                        className="absolute left-1/2 top-1/2 hidden -translate-x-1/2 -translate-y-1/2 border border-border bg-muted sm:flex"
                        textClassName="font-medium tracking-wide text-foreground"
                    />
                    <SessionBrand labelClassName="text-xl font-bold tracking-tight" />
                </div>
                <div className="flex items-center gap-4">
                    {setIsVoiceMode && (
                        <button
                            onClick={() => setIsVoiceMode(true)}
                            className="flex-shrink-0 flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-semibold text-primary border border-primary/20 bg-primary/10 hover:bg-primary/25 hover:border-primary/40 transition-all"
                        >
                            <Mic size={12} className="animate-pulse" />
                            Real-time Voice
                        </button>
                    )}
                    <SessionEndButton
                        isEnding={isEnding}
                        onClick={onEndSession}
                        className="rounded-lg border border-red-500/30 px-4 py-2 text-sm font-semibold text-red-500 hover:bg-red-500/20 hover:text-white disabled:cursor-wait disabled:opacity-50"
                    />
                    <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-primary-200 text-xs font-semibold uppercase tracking-wider">
                        <span className="size-2 rounded-full bg-primary animate-pulse shadow-[0_0_8px_rgba(79,70,229,0.6)]"></span>
                        Hybrid Live Session
                    </div>
                    <div className="bg-center bg-no-repeat bg-cover rounded-full size-10 ring-2 ring-primary/30" style={{ backgroundImage: "url('https://api.dicebear.com/7.x/avataaars/svg?seed=Felix')" }}></div>
                </div>
            </header>


            <main className="flex-1 flex overflow-hidden">
                <section className="flex-1 flex flex-col border-r border-border bg-card relative">
                    {/* Viewport Area */}
                    <div className="h-48 shrink-0 border-b border-border bg-muted/50 flex divide-x divide-border">
                        <div className="flex-1 flex flex-col items-center justify-center p-4 relative overflow-hidden group">
                            <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent pointer-events-none"></div>
                            <div className={cn(
                                "relative z-10 size-20 rounded-full p-0.5 bg-gradient-to-br from-primary to-primary-dark shadow-lg transition-all duration-300",
                                isSpeaking ? "shadow-primary/40 ring-4 ring-primary/20 scale-105" : "shadow-primary/20"
                            )}>
                                <div className="w-full h-full rounded-full bg-neutral-900 flex items-center justify-center overflow-hidden">
                                    <Bot className="text-primary-light" size={40} />
                                </div>
                                <div className="absolute bottom-0 right-0 size-6 bg-green-500 rounded-full border-4 border-neutral-900 z-20"></div>
                            </div>
                            <div className="mt-3 text-center">
                                <h3 className="text-sm font-bold text-white">AI Lead</h3>
                                {isSpeaking ? (
                                    <div className="flex items-center justify-center gap-1.5 mt-1">
                                        <span className="flex gap-0.5 h-3 items-end">
                                            <span className="w-0.5 h-2 bg-primary animate-pulse"></span>
                                            <span className="w-0.5 h-3 bg-primary animate-pulse delay-75"></span>
                                            <span className="w-0.5 h-1.5 bg-primary animate-pulse delay-150"></span>
                                        </span>
                                        <span className="text-[10px] text-primary-light font-bold tracking-widest uppercase">Speaking</span>
                                    </div>
                                ) : (
                                    <div className="flex items-center justify-center gap-1.5 mt-1">
                                        <span className="text-[10px] text-muted-foreground uppercase tracking-widest">Listening</span>
                                    </div>
                                )}
                            </div>
                        </div>
                        <div className="w-1/3 flex flex-col items-center justify-center p-4 bg-muted/50 grayscale opacity-80">
                            <div className="relative size-16 rounded-full border-2 border-dashed border-border flex items-center justify-center bg-muted/20">
                                <Eye className="text-muted-foreground" size={32} />
                            </div>
                            <div className="mt-3 text-center">
                                <h3 className="text-sm font-semibold text-muted-foreground">Human Observer</h3>
                                <span className="text-[10px] text-muted-foreground mt-1 block uppercase font-bold tracking-wider">Monitoring Session</span>
                            </div>
                        </div>
                    </div>

                    {/* Chat Flow */}
                    <div className="flex-1 overflow-y-auto p-6 space-y-6 scroll-smooth bg-background custom-scrollbar">
                        {questions.map((q, idx) => {
                            const isCurrent = idx === questions.length - 1;
                            return (
                                <React.Fragment key={q.id}>
                                    <div className="flex gap-4 max-w-3xl">
                                        <div className="size-8 rounded-full bg-primary/20 flex items-center justify-center text-primary-light shrink-0 mt-1">
                                            <Bot size={16} />
                                        </div>
                                        <div className="flex flex-col gap-1">
                                            <span className="text-[10px] font-bold text-primary-light ml-1 uppercase tracking-wider">AI Interviewer</span>
                                            <div className="bg-muted text-foreground rounded-2xl rounded-tl-none p-4 shadow-sm border border-border text-sm leading-relaxed">
                                                <p className="whitespace-pre-wrap">{q.content}</p>
                                            </div>
                                        </div>
                                    </div>

                                    {q.responses?.[0] && (
                                        <div className="flex flex-row-reverse gap-4 max-w-3xl ml-auto">
                                            <div className="size-8 rounded-full bg-muted bg-cover bg-center border border-border" style={{ backgroundImage: "url('https://api.dicebear.com/7.x/avataaars/svg?seed=Felix')" }}></div>
                                            <div className="flex-1">
                                                <div className="flex items-center gap-2 mb-1 justify-end">
                                                    <span className="text-xs font-bold text-foreground">You</span>
                                                    <span className="text-[10px] text-muted-foreground">Response</span>
                                                </div>
                                                <div className="bg-muted/50 rounded-2xl rounded-tr-none p-3 border border-border/50">
                                                    <p className="text-xs text-foreground/90 leading-relaxed whitespace-pre-wrap">
                                                        {q.responses[0].answerText}
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {/* Render prior follow-up exchanges */}
                                    {isCurrent && followupState.exchanges.map((exchange, exIdx) => (
                                        <React.Fragment key={exIdx}>
                                            <div className="flex gap-4 max-w-3xl animate-fade-in">
                                                <div className="size-8 rounded-full bg-amber-500/20 flex items-center justify-center text-amber-500 shrink-0 mt-1">
                                                    <Bot size={16} />
                                                </div>
                                                <div className="flex flex-col gap-1">
                                                    <span className="text-[10px] font-bold text-amber-500 ml-1 uppercase tracking-wider">
                                                        AI Follow-up (Round {exIdx + 1})
                                                    </span>
                                                    <div className="bg-muted text-foreground rounded-2xl rounded-tl-none p-4 shadow-sm border border-amber-500/20 text-sm leading-relaxed">
                                                        <p className="whitespace-pre-wrap">{exchange.followupQuestion}</p>
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="flex flex-row-reverse gap-4 max-w-3xl ml-auto animate-fade-in">
                                                <div className="size-8 rounded-full bg-muted bg-cover bg-center border border-border" style={{ backgroundImage: "url('https://api.dicebear.com/7.x/avataaars/svg?seed=Felix')" }}></div>
                                                <div className="flex-1">
                                                    <div className="flex items-center gap-2 mb-1 justify-end">
                                                        <span className="text-xs font-bold text-foreground">You</span>
                                                        <span className="text-[10px] text-amber-500 font-semibold">Response</span>
                                                    </div>
                                                    <div className="bg-amber-500/5 rounded-2xl rounded-tr-none p-3 border border-amber-500/20">
                                                        <p className="text-xs text-foreground/90 leading-relaxed whitespace-pre-wrap">
                                                            {exchange.followupAnswer}
                                                        </p>
                                                    </div>
                                                </div>
                                            </div>
                                        </React.Fragment>
                                    ))}

                                    {/* Render active follow-up question */}
                                    {isCurrent && followupState.isActive && followupState.currentFollowupQuestion && (
                                        <div className="flex gap-4 max-w-3xl animate-fade-in">
                                            <div className="size-8 rounded-full bg-amber-500/20 flex items-center justify-center text-amber-500 shrink-0 mt-1 animate-pulse">
                                                <Bot size={16} />
                                            </div>
                                            <div className="flex flex-col gap-1">
                                                <span className="text-[10px] font-bold text-amber-500 ml-1 uppercase tracking-wider animate-pulse">
                                                    AI Follow-up
                                                </span>
                                                <div className="bg-muted text-foreground rounded-2xl rounded-tl-none p-4 shadow-sm border border-amber-500/30 text-sm leading-relaxed">
                                                    <p className="whitespace-pre-wrap">{followupState.currentFollowupQuestion}</p>
                                                </div>
                                                {followupState.acknowledgement && (
                                                    <p className="text-[10px] text-amber-500/80 italic font-medium mt-1 ml-1 animate-fade-in">
                                                        "{followupState.acknowledgement}"
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </React.Fragment>
                            );
                        })}

                        {isCheckingFollowup && (
                            <div className="flex gap-4 max-w-3xl animate-pulse">
                                <div className="size-8 rounded-full bg-amber-500/10 flex items-center justify-center text-amber-500 shrink-0 mt-1">
                                    <Bot size={16} />
                                </div>
                                <div className="flex flex-col gap-2 w-full">
                                    <div className="h-3 bg-amber-500/20 rounded w-1/4"></div>
                                    <div className="h-16 bg-amber-500/10 rounded w-3/4"></div>
                                </div>
                            </div>
                        )}

                        {isPendingNext && (
                            <div className="flex gap-4 max-w-3xl animate-pulse">
                                <div className="size-8 rounded-full bg-muted flex items-center justify-center text-muted-foreground shrink-0 mt-1">
                                    <Bot size={16} />
                                </div>
                                <div className="flex flex-col gap-2 w-full">
                                    <div className="h-3 bg-muted rounded w-1/4"></div>
                                    <div className="h-16 bg-muted rounded w-3/4"></div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Input Area */}
                    <div className="p-4 bg-muted/20 border-t border-border">
                        <div className="relative">
                            <textarea
                                className="w-full bg-card/50 border border-border rounded-xl p-3 pr-12 text-xs text-foreground placeholder-muted-foreground focus:ring-1 focus:ring-primary focus:border-primary resize-none outline-none leading-relaxed"
                                placeholder={
                                    isPendingNext
                                        ? "AI is thinking..."
                                        : isCheckingFollowup
                                        ? "AI is analysing your answer..."
                                        : followupState.isActive
                                        ? "Answer the follow-up question..."
                                        : isAnswered && !followupState.isActive
                                        ? "Waiting for next question..."
                                        : "Type your response..."
                                }
                                rows={3}
                                value={followupState.isActive ? followupAnswerText : answerText}
                                onChange={(e) =>
                                    followupState.isActive
                                        ? setFollowupAnswerText(e.target.value)
                                        : setAnswerText(e.target.value)
                                }
                                onKeyDown={handleKeyDown}
                                disabled={
                                    isPendingNext ||
                                    isCheckingFollowup ||
                                    submitResponse.isPending ||
                                    (isAnswered && !followupState.isActive)
                                }
                            ></textarea>
                            <button
                                onClick={followupState.isActive ? handleFollowupSubmit : handleSubmit}
                                disabled={followupState.isActive ? !canSubmitFollowup : !canSubmit}
                                className={cn(
                                    "absolute bottom-3 right-3 p-1.5 text-white rounded-lg transition-colors shadow-md",
                                    followupState.isActive
                                        ? "bg-amber-500 hover:bg-amber-600 shadow-amber-500/20"
                                        : "bg-primary hover:bg-primary-dark shadow-primary/20"
                                )}
                            >
                                {submitResponse.isPending || isCheckingFollowup || isPendingNext || (questions?.length || 0) === 0 ? (
                                    <Loader2 size={14} className="animate-spin" />
                                ) : (
                                    <Send size={14} />
                                )}
                            </button>
                        </div>
                        <div className="flex items-center justify-between mt-2">
                            <div className="flex gap-2">
                                {isSTTSupported ? (
                                    <button
                                        onClick={handleMicToggle}
                                        disabled={
                                            isPendingNext ||
                                            isCheckingFollowup ||
                                            submitResponse.isPending ||
                                            (isAnswered && !followupState.isActive)
                                        }
                                        title={isListening ? "Stop recording" : "Speak your answer"}
                                        className={`p-1.5 rounded transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${
                                            isListening
                                                ? "text-red-500 bg-red-500/10 animate-pulse"
                                                : "hover:bg-muted text-muted-foreground"
                                        }`}
                                    >
                                        {isListening ? <MicOff size={14} /> : <Mic size={14} />}
                                    </button>
                                ) : (
                                    <button
                                        disabled
                                        title="Speech input not supported in this browser (use Chrome or Edge)"
                                        className="p-1.5 hover:bg-muted rounded text-muted-foreground transition-colors opacity-40 cursor-not-allowed"
                                    >
                                        <Mic size={14} />
                                    </button>
                                )}
                                <button className="p-1.5 hover:bg-muted rounded text-muted-foreground transition-colors">
                                    <Code size={14} />
                                </button>
                            </div>
                            <div className="flex items-center gap-2">
                                {isListening && (
                                    <span className="text-[10px] text-red-400 font-medium animate-pulse">
                                        Listening…
                                    </span>
                                )}
                                <span className="text-[10px] text-muted-foreground">Press Cmd+Enter to send</span>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Observer Aside */}
                <aside className="w-80 bg-card/10 border-l border-border flex flex-col shrink-0">
                    <div className="p-4 border-b border-border flex items-center justify-between bg-muted/30">
                        <h3 className="font-bold text-muted-foreground flex items-center gap-2 text-xs uppercase tracking-widest">
                            <Eye className="text-primary" size={16} />
                            Observer Feed
                        </h3>
                        <span className="flex h-2 w-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]"></span>
                    </div>
                    <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
                        <div className="relative pl-4 border-l-2 border-border hover:border-primary/50 transition-colors group">
                            <div className="absolute -left-[5px] top-0 size-2.5 rounded-full bg-muted-foreground transition-colors border border-background"></div>
                            <span className="text-[10px] font-mono text-muted-foreground mb-1 block">Live</span>
                            <div className="bg-card p-3 rounded-lg rounded-tl-none border border-border">
                                <p className="text-xs text-foreground/80 leading-normal">
                                    {questions.length <= 1 
                                        ? "Session started. Monitoring initial rapport building."
                                        : `Question ${questions.length} delivered. Analyzing candidate's technical depth.`}
                                </p>
                            </div>
                        </div>
                    </div>
                    <div className="p-4 bg-muted/20 border-t border-border">
                        <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-bold mb-3">Quick Flags</p>
                        <div className="grid grid-cols-2 gap-2">
                            <button className="flex items-center justify-center gap-1.5 py-2 px-3 rounded bg-muted hover:bg-green-500/20 hover:text-green-600 border border-border hover:border-green-500/30 transition-all text-xs font-medium text-muted-foreground">
                                <ThumbsUp size={14} /> Strong
                            </button>
                            <button className="flex items-center justify-center gap-1.5 py-2 px-3 rounded bg-muted hover:bg-red-500/20 hover:text-red-600 border border-border hover:border-red-500/30 transition-all text-xs font-medium text-muted-foreground">
                                <ThumbsDown size={14} /> Weak
                            </button>
                        </div>
                    </div>
                </aside>
            </main>
        </div>
    );
};
