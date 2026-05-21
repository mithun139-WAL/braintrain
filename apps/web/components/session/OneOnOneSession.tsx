import React, { useRef } from "react";
import {
    Bot,
    Lightbulb,
    Mic,
    Code,
    Send,
    TrendingUp,
    Trash2,
    Loader2,
    ChevronRight,
    AlertCircle,
} from "lucide-react";
import {
    LIVE_SESSION_MAX_QUESTIONS,
    type LiveSessionProps,
    SessionBrand,
    SessionEndButton,
    SessionTimerPill,
    useLiveSessionComposer,
} from "@/components/session/LiveSessionShared";

export const OneOnOneSession: React.FC<LiveSessionProps> = ({
    session,
    seconds,
    formatTime,
    isEnding,
    onEndSession
}) => {
    const scrollRef = useRef<HTMLDivElement>(null);
    const {
        answerText,
        setAnswerText,
        followupAnswerText,
        setFollowupAnswerText,
        followupState,
        canSubmit,
        canSubmitFollowup,
        handleKeyDown,
        handleSubmit,
        handleFollowupSubmit,
        isAnswered,
        isPendingNext,
        isCheckingFollowup,
        questions,
        submitResponse,
    } = useLiveSessionComposer({
        session,
        isEnding,
        onSubmitSuccess: () => {
            setTimeout(() => {
                scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
            }, 100);
        },
    });

    const progressPct = Math.min((questions.length / LIVE_SESSION_MAX_QUESTIONS) * 100, 100);

    // Dynamic insight based on progress
    const liveInsight =
        questions.length === 0
            ? "Your AI interviewer is preparing the first question…"
            : questions.length <= 2
            ? "Strong start. Be specific — back every claim with a concrete example."
            : questions.length <= 5
            ? "You're in the zone. Deepen your answers with implementation details."
            : "Final stretch. Show your edge — think about trade-offs and edge cases.";

    // Determine textarea placeholder based on current state
    const textareaPlaceholder = (() => {
        if (isPendingNext) return "AI is formulating the next question…";
        if (isCheckingFollowup) return "AI is analysing your answer…";
        if (followupState.isActive) return "Answer the follow-up question above…";
        if (isAnswered && !followupState.isActive) return "Waiting for next question…";
        return "Type your answer here… be thorough and specific.";
    })();

    // Whether the textarea should accept input
    const textareaDisabled =
        isPendingNext ||
        isCheckingFollowup ||
        submitResponse.isPending ||
        (isAnswered && !followupState.isActive);

    return (
        <div className="min-h-screen flex flex-col bg-gray-950 text-white selection:bg-primary/30 selection:text-white">

            {/* ── Header ─────────────────────────────────────────────────── */}
            <header className="sticky top-0 z-50 w-full bg-gray-950/90 backdrop-blur-md border-b border-gray-800">
                <div className="max-w-[1400px] mx-auto px-4 h-16 flex items-center justify-between gap-4">

                    {/* Left — brand + meta */}
                    <div className="flex items-center gap-3 min-w-0">
                        <SessionBrand
                            className="flex-shrink-0 gap-2"
                            iconWrapperClassName="size-7 rounded-lg bg-primary/15 flex items-center justify-center"
                            iconSize={16}
                            labelClassName="hidden text-sm font-bold tracking-tight text-white sm:block"
                        />
                        <ChevronRight size={14} className="text-gray-600 hidden sm:block flex-shrink-0" />
                        <h1 className="font-semibold text-sm text-gray-200 capitalize truncate">
                            {session.topicName || "Session"}
                        </h1>
                        <span className="hidden md:inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-bold bg-gray-800 border border-gray-700 text-gray-400 capitalize flex-shrink-0">
                            {session.interviewType.toLowerCase()}
                        </span>
                        <span className="hidden md:inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-bold bg-gray-800 border border-gray-700 text-gray-400 capitalize flex-shrink-0">
                            {session.difficulty.toLowerCase()}
                        </span>
                        {session.adaptive && (
                            <span className="hidden lg:inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[10px] font-bold bg-primary/10 border border-primary/30 text-primary flex-shrink-0">
                                <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                                Adaptive
                            </span>
                        )}
                    </div>

                    {/* Center — timer */}
                    <SessionTimerPill
                        time={formatTime(seconds)}
                        className="absolute left-1/2 top-1/2 hidden -translate-x-1/2 -translate-y-1/2 border border-gray-700 bg-gray-900 sm:flex"
                        iconSize={14}
                        textClassName="text-sm font-semibold tracking-widest text-white"
                    />

                    {/* Right — end session */}
                    <SessionEndButton
                        isEnding={isEnding}
                        onClick={onEndSession}
                        className="flex-shrink-0 rounded-lg px-4 py-2 text-sm font-semibold text-red-400 hover:bg-red-500/20 hover:text-white disabled:cursor-wait disabled:opacity-50"
                        labelClassName="hidden sm:inline"
                    />
                </div>

                {/* Progress bar — full width under header */}
                <div className="h-[2px] bg-gray-800 w-full">
                    <div
                        className="h-full bg-primary transition-all duration-700 ease-out"
                        style={{ width: `${progressPct}%`, boxShadow: "0 0 8px rgba(99,102,241,0.6)" }}
                    />
                </div>
            </header>

            {/* ── Main ───────────────────────────────────────────────────── */}
            <main className="flex-1 w-full max-w-[1400px] mx-auto p-4 md:p-6 lg:p-8 flex gap-6 lg:gap-8 overflow-hidden" style={{ height: "calc(100vh - 66px)" }}>

                {/* ── Conversation Area ─────────────────────────── */}
                <section className="flex-1 flex flex-col h-full gap-0 max-w-[860px] mx-auto w-full">

                    {/* Message feed */}
                    <div
                        ref={scrollRef}
                        className="flex-1 overflow-y-auto space-y-6 pb-4 pr-1"
                        style={{ scrollbarWidth: "thin", scrollbarColor: "rgba(99,102,241,0.2) transparent" }}
                    >
                        {questions.map((q, idx) => {
                            // Determine whether this is the current (last) question
                            const isCurrentQ = idx === questions.length - 1;

                            return (
                                <React.Fragment key={q.id}>
                                    {/* ── AI Question ── */}
                                    <div className="flex gap-4 animate-fade-in">
                                        <div className="flex-shrink-0 mt-1">
                                            <div className="size-9 rounded-xl bg-gradient-to-br from-primary to-violet-700 flex items-center justify-center shadow-[0_0_12px_rgba(99,102,241,0.35)]">
                                                <Bot className="text-white" size={17} />
                                            </div>
                                        </div>
                                        <div className="flex flex-col items-start max-w-[88%] lg:max-w-[78%]">
                                            <div className="flex items-center gap-2 mb-2">
                                                <span className="text-[10px] font-bold text-primary uppercase tracking-widest">
                                                    AI Interviewer
                                                </span>
                                                <span className="text-[10px] text-gray-600 font-medium">
                                                    · Q{idx + 1} of {LIVE_SESSION_MAX_QUESTIONS}
                                                </span>
                                            </div>
                                            <div className="relative bg-gray-900 border border-gray-700/80 text-gray-100 rounded-2xl rounded-tl-sm p-5 shadow-lg">
                                                {/* Accent stripe */}
                                                <div className="absolute left-0 top-3 bottom-3 w-[3px] bg-primary rounded-full" />
                                                <p className="pl-3 leading-relaxed text-gray-200 whitespace-pre-wrap text-sm">
                                                    {q.content}
                                                </p>
                                            </div>
                                        </div>
                                    </div>

                                    {/* ── User Response ── */}
                                    {q.responses?.[0] && (
                                        <div className="flex flex-row-reverse gap-4 animate-fade-in">
                                            <div className="flex-shrink-0 mt-1">
                                                <div className="size-9 rounded-xl bg-gray-800 border border-gray-700 flex items-center justify-center font-bold text-xs text-gray-300">
                                                    You
                                                </div>
                                            </div>
                                            <div className="flex flex-col items-end max-w-[85%] lg:max-w-[75%]">
                                                <span className="text-[10px] font-medium text-gray-600 mb-2 uppercase tracking-widest">
                                                    Your Answer
                                                </span>
                                                <div className="bg-gray-800/70 border border-gray-700 text-gray-200 rounded-2xl rounded-tr-sm p-5">
                                                    <p className="leading-relaxed whitespace-pre-wrap text-sm">
                                                        {q.responses[0].answerText}
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {/* ── Follow-up Exchange History (completed rounds) ── */}
                                    {isCurrentQ && followupState.exchanges.map((exchange, exIdx) => (
                                        <React.Fragment key={`exchange-${exIdx}`}>
                                            {/* Follow-up probe from AI */}
                                            <div className="flex gap-4 animate-fade-in">
                                                <div className="flex-shrink-0 mt-1">
                                                    <div className="size-9 rounded-xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center">
                                                        <AlertCircle className="text-amber-400" size={16} />
                                                    </div>
                                                </div>
                                                <div className="flex flex-col items-start max-w-[88%] lg:max-w-[78%]">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <span className="text-[10px] font-bold text-amber-400 uppercase tracking-widest">
                                                            Follow-up
                                                        </span>
                                                        <span className="text-[10px] text-gray-600 font-medium">
                                                            · Round {exIdx + 1}
                                                        </span>
                                                    </div>
                                                    <div className="relative bg-amber-950/30 border border-amber-500/20 text-gray-100 rounded-2xl rounded-tl-sm p-5">
                                                        <div className="absolute left-0 top-3 bottom-3 w-[3px] bg-amber-500 rounded-full" />
                                                        <p className="pl-3 leading-relaxed text-gray-200 whitespace-pre-wrap text-sm">
                                                            {exchange.followupQuestion}
                                                        </p>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* User's follow-up answer */}
                                            <div className="flex flex-row-reverse gap-4 animate-fade-in">
                                                <div className="flex-shrink-0 mt-1">
                                                    <div className="size-9 rounded-xl bg-gray-800 border border-gray-700 flex items-center justify-center font-bold text-xs text-gray-300">
                                                        You
                                                    </div>
                                                </div>
                                                <div className="flex flex-col items-end max-w-[85%] lg:max-w-[75%]">
                                                    <span className="text-[10px] font-medium text-gray-600 mb-2 uppercase tracking-widest">
                                                        Your Answer
                                                    </span>
                                                    <div className="bg-gray-800/70 border border-gray-700 text-gray-200 rounded-2xl rounded-tr-sm p-5">
                                                        <p className="leading-relaxed whitespace-pre-wrap text-sm">
                                                            {exchange.followupAnswer}
                                                        </p>
                                                    </div>
                                                </div>
                                            </div>
                                        </React.Fragment>
                                    ))}

                                    {/* ── Active Follow-up Probe (current unanswered round) ── */}
                                    {isCurrentQ && followupState.isActive && followupState.currentFollowupQuestion && (
                                        <div className="flex gap-4 animate-fade-in">
                                            <div className="flex-shrink-0 mt-1">
                                                <div className="size-9 rounded-xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center">
                                                    <AlertCircle className="text-amber-400" size={16} />
                                                </div>
                                            </div>
                                            <div className="flex flex-col items-start max-w-[88%] lg:max-w-[78%]">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <span className="text-[10px] font-bold text-amber-400 uppercase tracking-widest">
                                                        Follow-up
                                                    </span>
                                                    <span className="text-[10px] text-gray-600 font-medium">
                                                        · Round {followupState.exchanges.length + 1}
                                                    </span>
                                                </div>
                                                <div className="relative bg-amber-950/30 border border-amber-500/20 text-gray-100 rounded-2xl rounded-tl-sm p-5">
                                                    <div className="absolute left-0 top-3 bottom-3 w-[3px] bg-amber-500 rounded-full" />
                                                    <p className="pl-3 leading-relaxed text-gray-200 whitespace-pre-wrap text-sm">
                                                        {followupState.currentFollowupQuestion}
                                                    </p>
                                                </div>
                                                {/* Subtle gap hint badge */}
                                                {followupState.acknowledgement && (
                                                    <p className="mt-2 pl-1 text-[11px] text-amber-400/70 italic">
                                                        {followupState.acknowledgement}
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </React.Fragment>
                            );
                        })}

                        {/* Thinking / Analysing indicator */}
                        {(isPendingNext || isCheckingFollowup) && (
                            <div className="flex gap-4">
                                <div className="flex-shrink-0 mt-1">
                                    <div className={`size-9 rounded-xl flex items-center justify-center ${isCheckingFollowup ? "bg-amber-500/10" : "bg-gray-800"}`}>
                                        <Bot className={isCheckingFollowup ? "text-amber-500/60" : "text-gray-600"} size={17} />
                                    </div>
                                </div>
                                <div className="flex flex-col gap-2.5 mt-2">
                                    <div className="flex items-center gap-1.5">
                                        {[0, 1, 2].map((i) => (
                                            <span
                                                key={i}
                                                className={`size-1.5 rounded-full animate-bounce ${isCheckingFollowup ? "bg-amber-400" : "bg-primary"}`}
                                                style={{ animationDelay: `${i * 0.15}s` }}
                                            />
                                        ))}
                                        <span className="text-xs text-gray-600 ml-1">
                                            {isCheckingFollowup ? "AI is analysing your answer…" : "AI is thinking…"}
                                        </span>
                                    </div>
                                    <div className="h-16 w-64 bg-gray-900 rounded-xl animate-pulse" />
                                </div>
                            </div>
                        )}
                    </div>

                    {/* ── Input area ─────────────────────────── */}
                    <div className="shrink-0 pt-4">
                        <div className={`bg-gray-900 border rounded-2xl shadow-2xl ring-1 ring-transparent transition-all duration-200 ${
                            followupState.isActive
                                ? "border-amber-500/30 focus-within:ring-amber-400/30 focus-within:border-amber-500/50"
                                : "border-gray-700 focus-within:ring-primary/40 focus-within:border-primary/50"
                        }`}>
                            <textarea
                                className="w-full bg-transparent border-0 text-gray-100 placeholder-gray-600 focus:ring-0 px-5 pt-4 pb-2 min-h-[110px] resize-none leading-relaxed outline-none text-sm"
                                placeholder={textareaPlaceholder}
                                value={followupState.isActive ? followupAnswerText : answerText}
                                onChange={(e) =>
                                    followupState.isActive
                                        ? setFollowupAnswerText(e.target.value)
                                        : setAnswerText(e.target.value)
                                }
                                onKeyDown={handleKeyDown}
                                disabled={textareaDisabled}
                            />
                            <div className="flex items-center justify-between px-4 pb-3 pt-2 border-t border-gray-800">
                                <div className="flex items-center gap-1 text-gray-600">
                                    <button className="p-1.5 hover:bg-gray-800 rounded-lg text-gray-600 hover:text-gray-300 transition-colors">
                                        <Mic size={15} />
                                    </button>
                                    <button className="p-1.5 hover:bg-gray-800 rounded-lg text-gray-600 hover:text-gray-300 transition-colors">
                                        <Code size={15} />
                                    </button>
                                    <div className="w-px h-3.5 bg-gray-800 mx-1" />
                                    <span className={`text-[10px] font-mono tabular-nums transition-colors ${
                                        (followupState.isActive ? followupAnswerText : answerText).length > 1800
                                            ? "text-red-400"
                                            : "text-gray-600"
                                    }`}>
                                        {(followupState.isActive ? followupAnswerText : answerText).length} / 2000
                                    </span>
                                </div>
                                <div className="flex items-center gap-3">
                                    <span className="hidden sm:block text-[10px] text-gray-700">
                                        <kbd className="font-mono bg-gray-800 px-1.5 py-0.5 rounded border border-gray-700 text-gray-500">⌘</kbd>
                                        {" "}+{" "}
                                        <kbd className="font-mono bg-gray-800 px-1.5 py-0.5 rounded border border-gray-700 text-gray-500">↵</kbd>
                                        {" "}to submit
                                    </span>
                                    <button
                                        onClick={followupState.isActive ? handleFollowupSubmit : handleSubmit}
                                        disabled={followupState.isActive ? !canSubmitFollowup : !canSubmit}
                                        className={`disabled:bg-gray-800 disabled:text-gray-600 text-white px-5 py-2 rounded-xl text-sm font-semibold shadow-lg transition-all active:scale-95 flex items-center gap-2 group ${
                                            followupState.isActive
                                                ? "bg-amber-500 hover:bg-amber-400 shadow-amber-500/20"
                                                : "bg-primary hover:bg-violet-600 shadow-primary/30"
                                        }`}
                                    >
                                        {submitResponse.isPending || isCheckingFollowup || isPendingNext || questions.length === 0 ? (
                                            <Loader2 className="animate-spin" size={15} />
                                        ) : (
                                            <Send size={15} className="group-hover:translate-x-0.5 transition-transform" />
                                        )}
                                        <span>
                                            {submitResponse.isPending
                                                ? "Submitting…"
                                                : isCheckingFollowup
                                                ? "Analysing…"
                                                : isPendingNext
                                                ? "Thinking…"
                                                : questions.length === 0
                                                ? "Loading…"
                                                : followupState.isActive
                                                ? "Answer Follow-up"
                                                : "Submit Answer"}
                                        </span>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                {/* ── Right Sidebar ──────────────────────────── */}
                <aside className="hidden lg:flex flex-col w-[300px] gap-4 shrink-0 h-full overflow-y-auto">

                    {/* Progress card */}
                    <div className="bg-gray-900 rounded-2xl p-5 border border-gray-800">
                        <div className="flex items-center justify-between mb-4">
                            <h4 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">
                                Session Progress
                            </h4>
                            <span className="text-xs font-mono text-primary font-bold tabular-nums">
                                {questions.length} / {LIVE_SESSION_MAX_QUESTIONS}
                            </span>
                        </div>
                        {/* Segmented bar */}
                        <div className="flex gap-1 mb-5">
                            {Array.from({ length: LIVE_SESSION_MAX_QUESTIONS }).map((_, i) => (
                                <div
                                    key={i}
                                    className={`flex-1 h-1.5 rounded-full transition-all duration-500 ${
                                        i < questions.length
                                            ? "bg-primary shadow-[0_0_6px_rgba(99,102,241,0.5)]"
                                            : "bg-gray-800"
                                    }`}
                                />
                            ))}
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                            <div className="bg-gray-800/60 rounded-xl p-3 border border-gray-700/50">
                                <span className="block text-[10px] text-gray-500 mb-1 font-medium">Topic</span>
                                <span className="block text-xs font-semibold text-gray-200 truncate">
                                    {session.topicName || "—"}
                                </span>
                            </div>
                            <div className="bg-gray-800/60 rounded-xl p-3 border border-gray-700/50">
                                <span className="block text-[10px] text-gray-500 mb-1 font-medium">Difficulty</span>
                                <span className="block text-xs font-semibold text-primary capitalize">
                                    {session.difficulty.toLowerCase()}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Live Insight */}
                    <div className="bg-gray-900 rounded-2xl p-5 border border-l-[3px] border-amber-500/20 border-l-amber-500">
                        <div className="flex items-center gap-2 mb-3">
                            <TrendingUp size={15} className="text-amber-500" />
                            <h4 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">
                                Live Insight
                            </h4>
                        </div>
                        <p className="text-xs text-gray-400 leading-relaxed">
                            {followupState.isActive
                                ? "The AI spotted a gap in your answer. Answer the follow-up to demonstrate your full understanding."
                                : liveInsight}
                        </p>
                    </div>

                    {/* Tips */}
                    <div className="bg-gray-900 rounded-2xl p-5 border border-gray-800">
                        <div className="flex items-center gap-2 mb-3">
                            <Lightbulb size={15} className="text-primary" />
                            <h4 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">
                                Quick Tips
                            </h4>
                        </div>
                        <ul className="flex flex-col gap-2">
                            {[
                                "Use the STAR method for behavioral questions",
                                "Think out loud — show your reasoning",
                                "Ask clarifying questions if needed",
                            ].map((tip) => (
                                <li key={tip} className="flex items-start gap-2 text-[11px] text-gray-500 leading-relaxed">
                                    <span className="mt-1.5 size-1 rounded-full bg-primary/50 flex-shrink-0" />
                                    {tip}
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Private Notes */}
                    <div className="bg-gray-900 rounded-2xl flex flex-col flex-1 overflow-hidden border border-gray-800 min-h-[160px]">
                        <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between">
                            <h4 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">
                                Private Notes
                            </h4>
                            <button className="text-gray-700 hover:text-gray-400 transition-colors">
                                <Trash2 size={14} />
                            </button>
                        </div>
                        <textarea
                            className="flex-1 w-full bg-transparent border-0 px-4 py-3 text-xs text-gray-300 placeholder-gray-700 focus:ring-0 resize-none leading-relaxed outline-none"
                            placeholder="Jot down thoughts… not shared with AI."
                        />
                    </div>
                </aside>
            </main>
        </div>
    );
};
