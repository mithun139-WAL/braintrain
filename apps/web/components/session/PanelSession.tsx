import React, { useEffect, useRef } from "react";
import {
    Timer,
    Mic,
    MicOff,
    Activity,
    Send,
    Check,
    Users,
    Lightbulb,
    Paperclip,
    Code,
    ChevronLeft,
    Loader2,
    Volume2,
    VolumeX,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
    LIVE_SESSION_MAX_QUESTIONS,
    type LiveSessionProps,
    SessionBrand,
    SessionEndButton,
    useLiveSessionComposer,
} from "@/components/session/LiveSessionShared";
import { useSpeechSynthesis } from "@/hooks/useSpeechSynthesis";
import { useSpeechRecognition } from "@/hooks/useSpeechRecognition";

export const PanelSession: React.FC<LiveSessionProps> = ({
    session,
    seconds,
    formatTime,
    isEnding,
    onEndSession,
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

    const speakerIndex = questions.length > 0 ? (questions.length - 1) % 3 : -1;
    const isMarcusSpeaking = isSpeaking && speakerIndex === 0;
    const isSarahSpeaking = isSpeaking && speakerIndex === 1;
    const isDavidSpeaking = isSpeaking && speakerIndex === 2;

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

    // Auto-speak each new question
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
            <header className="flex items-center justify-between border-b border-border bg-card px-6 py-4 sticky top-0 z-50">
                <div className="flex items-center gap-4">
                    <button
                        onClick={onEndSession}
                        disabled={isEnding}
                        className="flex items-center justify-center size-8 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50"
                    >
                            <ChevronLeft size={20} />
                        </button>
                    <div className="h-6 w-px bg-border mx-1"></div>
                        <SessionBrand labelClassName="text-xl font-bold tracking-tight" />
                </div>
                <div className="flex items-center gap-4">
                    <SessionEndButton
                        isEnding={isEnding}
                        onClick={onEndSession}
                        className="rounded-lg border border-red-500/30 px-4 py-2 text-sm font-semibold text-red-500 hover:bg-red-500/20 hover:text-white disabled:cursor-wait disabled:opacity-50"
                    />
                    <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-muted border border-border text-primary text-xs font-semibold uppercase tracking-wider">
                        <span className="size-2 rounded-full bg-red-500 animate-pulse"></span>
                        Live Session
                    </div>
                    <div className="flex items-center gap-3">
                        <span className="text-sm font-medium text-muted-foreground hidden md:block">Candidate</span>
                        <div className="bg-center bg-no-repeat bg-cover rounded-full size-10 ring-2 ring-border" style={{ backgroundImage: "url('https://api.dicebear.com/7.x/avataaars/svg?seed=Felix')" }}></div>
                    </div>
                </div>
            </header>


            <main className="flex-1 w-full max-w-[1600px] mx-auto p-4 md:p-6 lg:p-8 flex flex-col lg:flex-row gap-6 h-[calc(100vh-80px)] overflow-hidden">
                <div className="flex-1 flex flex-col gap-6 h-full overflow-y-auto pr-2 pb-4 custom-scrollbar">
                    {/* Panel Members */}
                    <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {/* Sarah Chen (Panel Member) */}
                        <div className={cn(
                            "relative bg-card rounded-xl p-5 border border-border shadow-lg flex flex-col items-center gap-3 transition-all duration-300",
                            isSarahSpeaking ? "border-primary border-t-[3px] scale-105 z-10 bg-muted/30 shadow-primary/10" : "border-t-emerald-500 border-t-[3px] opacity-80 hover:opacity-100"
                        )}>
                            {isSarahSpeaking && (
                                <div className="absolute top-3 right-3 flex items-center gap-1 bg-primary/20 px-2 py-0.5 rounded text-[10px] font-bold text-primary uppercase tracking-wider">
                                    <Activity className="animate-pulse" size={10} />
                                    Speaking
                                </div>
                            )}
                            <div className="relative">
                                <div className={cn(
                                    "size-20 rounded-full bg-muted bg-cover bg-center border-2 transition-all duration-300",
                                    isSarahSpeaking ? "border-primary size-24" : "border-border"
                                )} style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuAV25uqcrWjzm0uyImmy_Hv8judeMlCBAhNV7HbQwaedKzWlTKvYJfbh8cc9qKPY_NQQi0cRl5tWl1T2hjtom3VIztWUieLg60XBCpiyDw0PC1aZak87opH091cpOUys6-4d2EMc07hdlbwUjV_QtiNdKRU8uzHGf9LKKpcXBP7SvLi1EckD017J0cA6hbY0TaElB4HP-YsM4zCiphK2kM4t0lJK4dUMmtPviGrghTEG77OJfgpfEq4Gu0SaWvqxp9Kn1SIJcEn6pk')" }}></div>
                                <div className={cn(
                                    "absolute bottom-0 right-0 rounded-full flex items-center justify-center border transition-all duration-300",
                                    isSarahSpeaking ? "-bottom-1 -right-1 size-7 bg-primary border-2 border-background" : "size-5 bg-card border-border"
                                )}>
                                    {isSarahSpeaking ? <Mic className="text-white" size={14} /> : <MicOff className="text-muted-foreground" size={12} />}
                                </div>
                            </div>
                            <div className="text-center">
                                <h3 className={cn("font-semibold text-sm", isSarahSpeaking ? "font-bold text-base" : "italic")}>Sarah</h3>
                            </div>
                        </div>

                        {/* Marcus Johnson (Panel Member) */}
                        <div className={cn(
                            "relative bg-card rounded-xl p-5 border border-border shadow-lg flex flex-col items-center gap-3 transition-all duration-300",
                            isMarcusSpeaking ? "border-primary border-t-[3px] scale-105 z-10 bg-muted/30 shadow-primary/10" : "border-t-emerald-500 border-t-[3px] opacity-80 hover:opacity-100"
                        )}>
                            {isMarcusSpeaking && (
                                <div className="absolute top-3 right-3 flex items-center gap-1 bg-primary/20 px-2 py-0.5 rounded text-[10px] font-bold text-primary uppercase tracking-wider">
                                    <Activity className="animate-pulse" size={10} />
                                    Speaking
                                </div>
                            )}
                            <div className="relative">
                                <div className={cn(
                                    "size-20 rounded-full bg-muted bg-cover bg-center border-2 transition-all duration-300",
                                    isMarcusSpeaking ? "border-primary size-24" : "border-border"
                                )} style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuBtkhzmd3n507non6jInf7K0NM3nWA_t_08DZe4M_RQrKGeUEy5FGthJz81zQwJIWCpeKnyWEEHorz8Po47joiG6tuevxvZC-oWKc1zy5KcSU0NuKkemYdJ65kj6kiSsY5GR55ErvW3hRiTA5EZBz4xSr_zy5RfrZ6X16-NaMn8h-PWru4G3jX3G05zabAdFDKHuC6V4X1-uC_Sjl-Y6YtuYb2oyVaAl_ILU1qeiBTiT7OGMP79CoUV0hSDbz2dqGe9Rh8vaskDuoc')" }}></div>
                                <div className={cn(
                                    "absolute bottom-0 right-0 rounded-full flex items-center justify-center border transition-all duration-300",
                                    isMarcusSpeaking ? "-bottom-1 -right-1 size-7 bg-primary border-2 border-background" : "size-5 bg-card border-border"
                                )}>
                                    {isMarcusSpeaking ? <Mic className="text-white" size={14} /> : <MicOff className="text-muted-foreground" size={12} />}
                                </div>
                            </div>
                            <div className="text-center">
                                <h3 className={cn("font-semibold text-sm", isMarcusSpeaking ? "font-bold text-base" : "italic")}>Marcus</h3>
                            </div>
                        </div>

                        {/* David Wright (Panel Member) */}
                        <div className={cn(
                            "relative bg-card rounded-xl p-5 border border-border shadow-lg flex flex-col items-center gap-3 transition-all duration-300",
                            isDavidSpeaking ? "border-primary border-t-[3px] scale-105 z-10 bg-muted/30 shadow-primary/10" : "border-t-emerald-500 border-t-[3px] opacity-80 hover:opacity-100"
                        )}>
                            {isDavidSpeaking && (
                                <div className="absolute top-3 right-3 flex items-center gap-1 bg-primary/20 px-2 py-0.5 rounded text-[10px] font-bold text-primary uppercase tracking-wider">
                                    <Activity className="animate-pulse" size={10} />
                                    Speaking
                                </div>
                            )}
                            <div className="relative">
                                <div className={cn(
                                    "size-20 rounded-full bg-muted bg-cover bg-center border-2 transition-all duration-300",
                                    isDavidSpeaking ? "border-primary size-24" : "border-border"
                                )} style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuB17zDeUEnok2_UtbAFmM554O2SXBzjMiBm1jQID86EnetT6vTUNfk6LyPJJdIyDcx1xUZJqcXthryBDpWiqO3bFX9irYFfGJDdECbo9NhBkY28nm-knjk4iU-YZiU6HuBFdIIxlfpPocPer_K2g5RuO_lsiWG4RhOJcNemOuYQ_BwGbYm-W-r3BsCy4HF_VtCuFc8ijgQwjQMvmwAFH9gmZC74dOobzax5YFcwm18edgieAPeK9R_ZTcwB-e9wd0StAA1of3gaiBI')" }}></div>
                                <div className={cn(
                                    "absolute bottom-0 right-0 rounded-full flex items-center justify-center border transition-all duration-300",
                                    isDavidSpeaking ? "-bottom-1 -right-1 size-7 bg-primary border-2 border-background" : "size-5 bg-card border-border"
                                )}>
                                    {isDavidSpeaking ? <Mic className="text-white" size={14} /> : <MicOff className="text-muted-foreground" size={12} />}
                                </div>
                            </div>
                            <div className="text-center">
                                <h3 className={cn("font-semibold text-sm", isDavidSpeaking ? "font-bold text-base" : "italic")}>David</h3>
                            </div>
                        </div>
                    </section>

                    {/* Question Card */}
                    <section className="flex-1 min-h-[200px] flex flex-col">
                        <div className={cn(
                            "bg-card rounded-xl border p-8 shadow-lg flex flex-col gap-4 relative overflow-hidden transition-all duration-300",
                            followupState.isActive ? "border-amber-500/30 border-t-[3px] border-t-amber-500" : "border-border border-t-emerald-500 border-t-[3px]"
                        )}>
                            <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3 pointer-events-none"></div>
                            <div className="flex items-center justify-between mb-2">
                                <span className={cn(
                                    "text-xs font-bold tracking-wider uppercase transition-colors",
                                    followupState.isActive ? "text-amber-500" : "text-primary"
                                )}>
                                    {followupState.isActive ? `Follow-up Probe (Round ${followupState.exchanges.length + 1})` : "Current Question"}
                                </span>
                                <div className="flex items-center gap-3 text-muted-foreground text-xs">
                                    {isTTSSupported && (followupState.isActive ? followupState.currentFollowupQuestion : currentQuestion?.content) && (
                                        <button
                                            onClick={() => {
                                                const txt = followupState.isActive ? followupState.currentFollowupQuestion : currentQuestion?.content;
                                                if (txt) {
                                                    isSpeaking ? stopSpeaking() : speak(txt);
                                                }
                                            }}
                                            title={isSpeaking ? "Stop speaking" : "Replay question"}
                                            className="p-1 hover:bg-muted rounded transition-colors text-muted-foreground hover:text-foreground"
                                        >
                                            {isSpeaking ? <VolumeX size={15} /> : <Volume2 size={15} />}
                                        </button>
                                    )}
                                    <Timer size={14} />
                                    {formatTime(seconds)}
                                </div>
                            </div>
                            <h2 className="text-2xl md:text-3xl font-medium leading-relaxed">
                                {followupState.isActive && followupState.currentFollowupQuestion
                                    ? `"${followupState.currentFollowupQuestion}"`
                                    : currentQuestion
                                    ? `"${currentQuestion.content}"`
                                    : isPendingNext
                                    ? "AI is generating the next question..."
                                    : "Waiting for interview to begin..."}
                            </h2>
                            {followupState.isActive && followupState.acknowledgement && (
                                <p className="text-xs text-amber-500/80 italic font-medium">
                                    "{followupState.acknowledgement}"
                                </p>
                            )}
                            {followupState.exchanges.length > 0 && (
                                <div className="mt-4 pt-4 border-t border-border/80 space-y-3 max-h-[150px] overflow-y-auto custom-scrollbar">
                                    <h4 className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Follow-up History</h4>
                                    {followupState.exchanges.map((exchange, exIdx) => (
                                        <div key={exIdx} className="space-y-1 text-xs">
                                            <p className="text-amber-500 font-semibold">Follow-up: <span className="text-muted-foreground font-normal">{exchange.followupQuestion}</span></p>
                                            <p className="text-foreground font-semibold">Your Answer: <span className="text-muted-foreground font-normal">{exchange.followupAnswer}</span></p>
                                        </div>
                                    ))}
                                </div>
                            )}
                            {currentQuestion && !followupState.isActive && (
                                <div className="mt-4 flex gap-2">
                                    <span className="px-2.5 py-1 rounded bg-muted text-muted-foreground text-xs border border-border capitalize">{session.topicName}</span>
                                    <span className="px-2.5 py-1 rounded bg-muted text-muted-foreground text-xs border border-border capitalize">{session.difficulty.toLowerCase()}</span>
                                    <span className="px-2.5 py-1 rounded bg-muted text-muted-foreground text-xs border border-border capitalize">{session.interviewType.toLowerCase()}</span>
                                </div>
                            )}
                        </div>
                    </section>

                    {/* Input Section */}
                    <section className={cn(
                        "bg-card rounded-xl border p-1 flex flex-col shadow-lg transition-all duration-300",
                        followupState.isActive ? "border-amber-500/30 focus-within:ring-amber-500/20" : "border-border"
                    )}>
                        <div className="relative w-full">
                            <textarea
                                className="w-full bg-transparent text-foreground placeholder-muted-foreground rounded-lg border-0 p-4 focus:ring-1 focus:ring-primary focus:bg-muted/30 resize-none h-32 md:h-40 leading-relaxed outline-none"
                                placeholder={
                                    isPendingNext
                                        ? "AI is thinking..."
                                        : isCheckingFollowup
                                        ? "AI is analysing your answer..."
                                        : followupState.isActive
                                        ? "Answer the follow-up question..."
                                        : isAnswered && !followupState.isActive
                                        ? "Waiting for next question..."
                                        : "Type your answer here or speak to answer..."
                                }
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
                        </div>
                        <div className="flex items-center justify-between px-4 py-3 border-t border-border">
                            <div className="flex items-center gap-4">
                                <button className="text-muted-foreground hover:text-foreground text-xs font-medium flex items-center gap-1 transition-colors">
                                    <Paperclip size={14} />
                                    Attach Diagram
                                </button>
                                <button className="text-muted-foreground hover:text-foreground text-xs font-medium flex items-center gap-1 transition-colors">
                                    <Code size={14} />
                                    Code Snippet
                                </button>
                                {/* Mic toggle */}
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
                                        className={`text-xs font-medium flex items-center gap-1 transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${
                                            isListening
                                                ? "text-red-500 animate-pulse"
                                                : "text-muted-foreground hover:text-foreground"
                                        }`}
                                    >
                                        {isListening ? <MicOff size={14} /> : <Mic size={14} />}
                                        {isListening ? "Stop" : "Speak"}
                                    </button>
                                ) : null}
                            </div>
                            <div className="flex items-center gap-3">
                                <span className="text-xs text-muted-foreground hidden sm:block">Press Cmd+Enter to submit</span>
                                <button
                                    onClick={followupState.isActive ? handleFollowupSubmit : handleSubmit}
                                    disabled={followupState.isActive ? !canSubmitFollowup : !canSubmit}
                                    className={cn(
                                        "text-white px-6 py-2 rounded-lg font-medium text-sm transition-colors shadow-lg flex items-center gap-2 group",
                                        followupState.isActive
                                            ? "bg-amber-500 hover:bg-amber-600 shadow-amber-500/20"
                                            : "bg-primary hover:bg-primary-dark shadow-primary/20"
                                    )}
                                >
                                    {submitResponse.isPending || isCheckingFollowup || isPendingNext || questions.length === 0 ? (
                                        <Loader2 className="animate-spin" size={16} />
                                    ) : (
                                        <>
                                            {followupState.isActive ? "Answer Follow-up" : "Submit Answer"}
                                            <Send size={16} className="group-hover:translate-x-0.5 transition-transform" />
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    </section>
                </div>

                {/* Sidebar */}
                <aside className="w-full lg:w-80 shrink-0 flex flex-col gap-4">
                    <div className="bg-card rounded-xl border border-border border-t-emerald-500 border-t-[3px] p-5 shadow-lg flex flex-col gap-4">
                        <div className="flex items-center justify-between border-b border-border pb-3">
                            <h3 className="font-semibold uppercase text-xs tracking-widest">Interview Progress</h3>
                            <span className="text-xs text-primary font-bold bg-primary/10 px-2 py-1 rounded tracking-tighter">Q{questions.length} / {LIVE_SESSION_MAX_QUESTIONS}</span>
                        </div>
                        <div className="space-y-4 max-h-[300px] overflow-y-auto custom-scrollbar pr-1">
                            {questions.map((q, idx) => (
                                <div key={q.id} className="flex gap-3 relative">
                                    <div className="flex flex-col items-center">
                                        <div className={cn(
                                            "size-6 rounded-full flex items-center justify-center border transition-all",
                                            q.responses?.length > 0
                                                ? "bg-emerald-500/20 text-emerald-500 border-emerald-500/50"
                                                : "bg-primary text-white border-primary shadow-lg shadow-primary/30 ring-2 ring-primary/20"
                                        )}>
                                            {q.responses?.length > 0 ? <Check size={12} /> : idx + 1}
                                        </div>
                                        {idx < questions.length - 1 && (
                                            <div className="w-px h-full bg-border my-1"></div>
                                        )}
                                    </div>
                                    <div className="pb-4">
                                        <p className={cn(
                                            "text-xs font-medium",
                                            q.responses?.length > 0 ? "text-muted-foreground" : "text-foreground"
                                        )}>
                                            {idx === 0 ? "Introduction" : `Question ${idx + 1}`}
                                        </p>
                                        <p className="text-[10px] text-muted-foreground mt-0.5">
                                            {q.responses?.length > 0 ? "Completed" : "In Progress..."}
                                        </p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="bg-card rounded-xl border border-border border-t-emerald-500 border-t-[3px] p-5 shadow-lg flex-1">
                        <div className="flex items-center justify-between border-b border-border pb-3 mb-4">
                            <h3 className="font-semibold uppercase text-xs tracking-widest">Panel Status</h3>
                            <Users size={16} className="text-muted-foreground" />
                        </div>
                        <div className="flex flex-col gap-3">
                            {[
                                { name: "Marcus", avatar: "https://lh3.googleusercontent.com/aida-public/AB6AXuBtkhzmd3n507non6jInf7K0NM3nWA_t_08DZe4M_RQrKGeUEy5FGthJz81zQwJIWCpeKnyWEEHorz8Po47joiG6tuevxvZC-oWKc1zy5KcSU0NuKkemYdJ65kj6kiSsY5GR55ErvW3hRiTA5EZBz4xSr_zy5RfrZ6X16-NaMn8h-PWru4G3jX3G05zabAdFDKHuC6V4X1-uC_Sjl-Y6YtuYb2oyVaAl_ILU1qeiBTiT7OGMP79CoUV0hSDbz2dqGe9Rh8vaskDuoc", isActive: isMarcusSpeaking },
                                { name: "Sarah", avatar: "https://lh3.googleusercontent.com/aida-public/AB6AXuAV25uqcrWjzm0uyImmy_Hv8judeMlCBAhNV7HbQwaedKzWlTKvYJfbh8cc9qKPY_NQQi0cRl5tWl1T2hjtom3VIztWUieLg60XBCpiyDw0PC1aZak87opH091cpOUys6-4d2EMc07hdlbwUjV_QtiNdKRU8uzHGf9LKKpcXBP7SvLi1EckD017J0cA6hbY0TaElB4HP-YsM4zCiphK2kM4t0lJK4dUMmtPviGrghTEG77OJfgpfEq4Gu0SaWvqxp9Kn1SIJcEn6pk", isActive: isSarahSpeaking },
                                { name: "David", avatar: "https://lh3.googleusercontent.com/aida-public/AB6AXuB17zDeUEnok2_UtbAFmM554O2SXBzjMiBm1jQID86EnetT6vTUNfk6LyPJJdIyDcx1xUZJqcXthryBDpWiqO3bFX9irYFfGJDdECbo9NhBkY28nm-knjk4iU-YZiU6HuBFdIIxlfpPocPer_K2g5RuO_lsiWG4RhOJcNemOuYQ_BwGbYm-W-r3BsCy4HF_VtCuFc8ijgQwjQMvmwAFH9gmZC74dOobzax5YFcwm18edgieAPeK9R_ZTcwB-e9wd0StAA1of3gaiBI", isActive: isDavidSpeaking },
                            ].map((panelist) => (
                                <div
                                    key={panelist.name}
                                    className={cn(
                                        "flex items-center gap-3 p-3 rounded-lg border transition-all duration-300",
                                        panelist.isActive
                                            ? "bg-primary/10 border-primary/30 shadow-sm"
                                            : "hover:bg-muted/50 border-transparent hover:border-border"
                                    )}
                                >
                                    <div className="relative">
                                        <div className="size-8 rounded-full bg-muted bg-cover bg-center" style={{ backgroundImage: `url('${panelist.avatar}')` }}></div>
                                        <span className={cn("absolute bottom-0 right-0 size-2.5 border border-card rounded-full transition-colors", panelist.isActive ? "bg-green-500" : "bg-gray-500")}></span>
                                    </div>
                                    <div className="flex-1">
                                        <div className="flex justify-between items-center text-[11px]">
                                            <span className={cn("font-semibold", !panelist.isActive && "text-muted-foreground")}>{panelist.name}</span>
                                            <span className={cn("uppercase font-bold tracking-widest text-[9px] transition-colors", panelist.isActive ? "text-primary animate-pulse" : "text-muted-foreground")}>
                                                {panelist.isActive ? "Speaking" : "Listening"}
                                            </span>
                                        </div>
                                        <div className="w-full bg-muted h-1 mt-2 rounded-full overflow-hidden">
                                            <div
                                                className={cn("h-full rounded-full transition-all duration-500", panelist.isActive ? "bg-primary animate-pulse" : "bg-muted-foreground/30")}
                                                style={{ width: panelist.isActive ? "75%" : "10%" }}
                                            ></div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="mt-6 pt-4 border-t border-border">
                            <div className="flex items-center gap-2 mb-2">
                                <Lightbulb className="text-yellow-500" size={14} />
                                <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Real-time Hint</span>
                            </div>
                            <p className="text-[11px] text-muted-foreground italic bg-muted/40 p-3 rounded border border-border/50 leading-relaxed">
                                {followupState.isActive
                                    ? "Explain details of the missing concept to address the panel's concerns."
                                    : questions.length <= 2 
                                    ? "Start by providing a concise overview of your relevant experience."
                                    : "Consider mentioning the CAP theorem trade-offs when discussing consistency vs availability."}
                            </p>
                        </div>
                    </div>
                </aside>
            </main>
        </div>
    );
};
