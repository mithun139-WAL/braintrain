"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
    Brain,
    Send,
    Bot,
    User,
    Loader2,
    Sparkles,
    ChevronDown,
    Plus,
    MessageCircle,
    AlertCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useCoachingSessions, useCoachingSession } from "@/hooks/queries/useCoachingSession";
import {
    useCreateCoachingSession,
    useSendCoachMessage,
} from "@/hooks/mutations/useCoachingMutations";
import type { CoachingSession, CoachingFocusArea } from "@braintrain/shared";

// ── Types ──────────────────────────────────────────────────────────────────────

type FocusArea = CoachingFocusArea;

const FOCUS_OPTIONS: { value: FocusArea; label: string; description: string; color: string }[] = [
    { value: "general", label: "General Coaching", description: "Broad interview preparation and communication skills", color: "text-primary" },
    { value: "confidence", label: "Confidence", description: "Reduce anxiety, project authority, control pacing", color: "text-amber-500" },
    { value: "clarity", label: "Clarity & Structure", description: "STAR method, precision vocabulary, answer flow", color: "text-blue-500" },
    { value: "technical_explanation", label: "Technical Depth", description: "System design, algorithm explanation, code reviews", color: "text-emerald-500" },
];

// ── Message bubble ─────────────────────────────────────────────────────────────

interface MessageBubbleProps {
    role: "user" | "assistant";
    content: string;
    isStreaming?: boolean;
}

function MessageBubble({ role, content, isStreaming }: MessageBubbleProps) {
    const isAssistant = role === "assistant";
    return (
        <div className={cn("flex gap-3", isAssistant ? "items-start" : "items-start flex-row-reverse")}>
            {/* Avatar */}
            <div className={cn(
                "flex-shrink-0 size-9 rounded-full flex items-center justify-center mt-0.5",
                isAssistant
                    ? "bg-gradient-to-br from-primary to-primary/70 shadow-lg shadow-primary/20"
                    : "bg-gray-700 border border-gray-600"
            )}>
                {isAssistant ? <Bot size={18} className="text-white" /> : <User size={16} className="text-gray-300" />}
            </div>

            {/* Bubble */}
            <div className={cn(
                "max-w-[78%] rounded-2xl px-4 py-3 text-sm leading-relaxed",
                isAssistant
                    ? "bg-gray-900 border border-gray-800 text-gray-100 rounded-tl-sm"
                    : "bg-primary/10 border border-primary/20 text-gray-100 rounded-tr-sm"
            )}>
                {isStreaming ? (
                    <span className="flex items-center gap-1.5 text-muted-foreground">
                        <span>Thinking</span>
                        <span className="flex gap-0.5">
                            {[0, 1, 2].map(i => (
                                <span
                                    key={i}
                                    className="size-1 rounded-full bg-primary animate-bounce"
                                    style={{ animationDelay: `${i * 0.12}s` }}
                                />
                            ))}
                        </span>
                    </span>
                ) : (
                    <p className="whitespace-pre-wrap">{content}</p>
                )}
            </div>
        </div>
    );
}

// ── New Session Modal ──────────────────────────────────────────────────────────

interface NewSessionModalProps {
    onClose: () => void;
    onStart: (focusArea: FocusArea, sessionId?: string) => void;
}

function NewSessionModal({ onClose, onStart }: NewSessionModalProps) {
    const [selected, setSelected] = useState<FocusArea>("general");

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="bg-gray-950 border border-gray-800 rounded-2xl p-8 w-full max-w-md shadow-2xl">
                <div className="flex items-center gap-3 mb-6">
                    <div className="size-10 rounded-xl bg-primary/10 flex items-center justify-center">
                        <Sparkles size={20} className="text-primary" />
                    </div>
                    <div>
                        <h2 className="text-lg font-bold text-white">New Coaching Session</h2>
                        <p className="text-xs text-gray-500">Choose what to focus on today</p>
                    </div>
                </div>

                <div className="space-y-3 mb-6">
                    {FOCUS_OPTIONS.map(opt => (
                        <button
                            key={opt.value}
                            onClick={() => setSelected(opt.value)}
                            className={cn(
                                "w-full text-left p-4 rounded-xl border transition-all",
                                selected === opt.value
                                    ? "border-primary/40 bg-primary/5"
                                    : "border-gray-800 hover:border-gray-700 hover:bg-gray-900/50"
                            )}
                        >
                            <div className="flex items-center justify-between">
                                <span className={cn("font-semibold text-sm", selected === opt.value ? "text-white" : "text-gray-300")}>
                                    {opt.label}
                                </span>
                                {selected === opt.value && (
                                    <div className="size-2 rounded-full bg-primary" />
                                )}
                            </div>
                            <p className="text-xs text-gray-500 mt-1">{opt.description}</p>
                        </button>
                    ))}
                </div>

                <div className="flex gap-3">
                    <button
                        onClick={onClose}
                        className="flex-1 py-2.5 rounded-xl border border-gray-800 text-gray-400 text-sm font-medium hover:bg-gray-900 transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={() => onStart(selected)}
                        className="flex-1 py-2.5 rounded-xl bg-primary text-white text-sm font-bold hover:bg-primary/90 transition-colors flex items-center justify-center gap-2"
                    >
                        <Sparkles size={16} />
                        Start Session
                    </button>
                </div>
            </div>
        </div>
    );
}

// ── Main page ──────────────────────────────────────────────────────────────────

export default function CoachPage() {
    const searchParams = useSearchParams();
    const urlSessionId = searchParams.get("session");

    const [activeSessionId, setActiveSessionId] = useState<string | null>(urlSessionId);
    const [inputText, setInputText] = useState("");
    const [showNewModal, setShowNewModal] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const { data: sessionsResponse } = useCoachingSessions();
    const { data: sessionResponse, isLoading: isLoadingSession } = useCoachingSession(activeSessionId);
    const createSession = useCreateCoachingSession();
    const sendMessage = useSendCoachMessage();

    // useQuery stores ApiResponse<T> as `data`, so `.data` unwraps to the payload
    const sessions = sessionsResponse?.data ?? [];
    const activeSession = sessionResponse?.data;
    const messages = activeSession?.messages ?? [];

    // Auto-scroll to bottom on new messages
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages.length, sendMessage.isPending]);

    const handleStartSession = async (focusArea: FocusArea) => {
        setShowNewModal(false);
        const result = await createSession.mutateAsync({ focusArea });
        if (result?.data?.id) {
            setActiveSessionId(result.data.id);
        }
    };

    const handleSend = async () => {
        if (!inputText.trim() || !activeSessionId || sendMessage.isPending) return;
        const text = inputText;
        setInputText("");
        await sendMessage.mutateAsync({ sessionId: activeSessionId, content: text });
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleSend();
    };

    const isEnded = activeSession?.status === "ENDED";

    return (
        <div className="flex h-[calc(100vh-4rem)] gap-0 -m-6 overflow-hidden">
            {/* Session history sidebar */}
            <div className="w-64 flex-shrink-0 bg-gray-950 border-r border-gray-800 flex flex-col">
                <div className="p-4 border-b border-gray-800">
                    <button
                        onClick={() => setShowNewModal(true)}
                        className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-primary/10 border border-primary/20 text-primary text-sm font-semibold hover:bg-primary/20 transition-colors"
                    >
                        <Plus size={16} />
                        New Session
                    </button>
                </div>
                <div className="flex-1 overflow-y-auto p-2 space-y-1">
                    {sessions.length === 0 ? (
                        <div className="p-4 text-center">
                            <p className="text-xs text-gray-600">No sessions yet</p>
                        </div>
                    ) : (
                        sessions.map(s => (
                            <button
                                key={s.id}
                                onClick={() => setActiveSessionId(s.id)}
                                className={cn(
                                    "w-full text-left p-3 rounded-xl transition-all",
                                    activeSessionId === s.id
                                        ? "bg-primary/10 border border-primary/20"
                                        : "hover:bg-gray-900 border border-transparent"
                                )}
                            >
                                <div className="flex items-center justify-between mb-1">
                                    <span className={cn(
                                        "text-xs font-semibold capitalize",
                                        activeSessionId === s.id ? "text-primary" : "text-gray-400"
                                    )}>
                                        {s.focusArea}
                                    </span>
                                    {s.status === "ENDED" && (
                                        <span className="text-[10px] text-gray-600 bg-gray-800 px-1.5 py-0.5 rounded">
                                            Ended
                                        </span>
                                    )}
                                </div>
                                <p className="text-[11px] text-gray-600">
                                        {s.messageCount} messages
                                    </p>
                            </button>
                        ))
                    )}
                </div>
            </div>

            {/* Main chat area */}
            <div className="flex-1 flex flex-col bg-[#0a0a0f] overflow-hidden">
                {!activeSessionId ? (
                    /* Empty state */
                    <div className="flex-1 flex flex-col items-center justify-center gap-6 p-8 text-center">
                        <div className="size-20 rounded-2xl bg-primary/10 flex items-center justify-center">
                            <Brain size={36} className="text-primary" />
                        </div>
                        <div className="space-y-2">
                            <h2 className="text-2xl font-bold text-white">AI Communication Coach</h2>
                            <p className="text-gray-500 max-w-sm text-sm leading-relaxed">
                                Get personalized coaching to improve your interview performance.
                                The AI coach adapts to your specific needs and growth areas.
                            </p>
                        </div>
                        <div className="grid grid-cols-2 gap-3 w-full max-w-sm">
                            {FOCUS_OPTIONS.map(opt => (
                                <button
                                    key={opt.value}
                                    onClick={() => handleStartSession(opt.value)}
                                    disabled={createSession.isPending}
                                    className="p-4 rounded-xl border border-gray-800 hover:border-gray-700 hover:bg-gray-900/50 transition-all text-left"
                                >
                                    <p className={cn("font-semibold text-sm mb-1", opt.color)}>{opt.label}</p>
                                    <p className="text-xs text-gray-600 leading-snug">{opt.description}</p>
                                </button>
                            ))}
                        </div>
                        {createSession.isPending && (
                            <div className="flex items-center gap-2 text-gray-500 text-sm">
                                <Loader2 size={16} className="animate-spin" />
                                Starting session…
                            </div>
                        )}
                    </div>
                ) : (
                    <>
                        {/* Chat header */}
                        <div className="h-14 px-6 border-b border-gray-800 flex items-center justify-between flex-shrink-0">
                            <div className="flex items-center gap-3">
                                <div className="size-8 rounded-full bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center">
                                    <Bot size={16} className="text-white" />
                                </div>
                                <div>
                                    <p className="text-sm font-semibold text-white">
                                        AI Coach
                                        {activeSession && (
                                            <span className="text-gray-500 font-normal ml-2 capitalize text-xs">
                                                · {activeSession.focusArea}
                                            </span>
                                        )}
                                    </p>
                                </div>
                                {isEnded && (
                                    <span className="text-xs text-gray-600 bg-gray-900 px-2 py-1 rounded border border-gray-800">
                                        Session ended
                                    </span>
                                )}
                            </div>
                            {!isEnded && (
                                <button
                                    onClick={() => setShowNewModal(true)}
                                    className="text-xs text-gray-500 hover:text-gray-300 flex items-center gap-1.5 transition-colors"
                                >
                                    <Plus size={14} />
                                    New Session
                                </button>
                            )}
                        </div>

                        {/* Messages */}
                        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
                            {isLoadingSession ? (
                                <div className="flex justify-center py-8">
                                    <Loader2 size={24} className="animate-spin text-primary" />
                                </div>
                            ) : (
                                <>
                                    {messages.map(msg => (
                                        <MessageBubble
                                            key={msg.id}
                                            role={msg.role as "user" | "assistant"}
                                            content={msg.content}
                                        />
                                    ))}
                                    {sendMessage.isPending && (
                                        <MessageBubble role="assistant" content="" isStreaming />
                                    )}
                                    <div ref={messagesEndRef} />
                                </>
                            )}
                        </div>

                        {/* Input */}
                        {!isEnded && (
                            <div className="px-6 pb-6 flex-shrink-0">
                                <div className="bg-gray-900 border border-gray-800 rounded-2xl p-1 focus-within:border-primary/30 transition-colors">
                                    <textarea
                                        className="w-full bg-transparent text-gray-100 placeholder-gray-600 text-sm px-4 pt-3 pb-2 resize-none outline-none min-h-[80px] leading-relaxed"
                                        placeholder="Ask your AI coach anything… (Cmd+Enter to send)"
                                        value={inputText}
                                        onChange={e => setInputText(e.target.value)}
                                        onKeyDown={handleKeyDown}
                                        disabled={sendMessage.isPending}
                                    />
                                    <div className="flex items-center justify-between px-4 pb-3 pt-1 border-t border-gray-800/50">
                                        <span className="text-xs text-gray-600 font-mono">{inputText.length}/1000</span>
                                        <button
                                            onClick={handleSend}
                                            disabled={!inputText.trim() || sendMessage.isPending}
                                            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-white text-sm font-semibold disabled:opacity-40 disabled:cursor-not-allowed hover:bg-primary/90 transition-colors"
                                        >
                                            {sendMessage.isPending ? (
                                                <Loader2 size={16} className="animate-spin" />
                                            ) : (
                                                <>
                                                    <Send size={15} />
                                                    Send
                                                </>
                                            )}
                                        </button>
                                    </div>
                                </div>
                                <p className="text-center text-[11px] text-gray-700 mt-2">
                                    Press{" "}
                                    <kbd className="font-mono bg-gray-900 px-1 rounded border border-gray-800 text-gray-500">⌘</kbd>
                                    {" + "}
                                    <kbd className="font-mono bg-gray-900 px-1 rounded border border-gray-800 text-gray-500">Enter</kbd>{" "}
                                    to send
                                </p>
                            </div>
                        )}
                    </>
                )}
            </div>

            {/* New session modal */}
            {showNewModal && (
                <NewSessionModal
                    onClose={() => setShowNewModal(false)}
                    onStart={handleStartSession}
                />
            )}
        </div>
    );
}
