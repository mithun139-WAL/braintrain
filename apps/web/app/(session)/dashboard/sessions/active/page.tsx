"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
    Brain,
    Settings,
    Pause,
    X,
    Bookmark,
    Mic,
    Keyboard,
    RotateCcw,
    Square,
    Check,
    Info,
    Lightbulb,
    ChevronDown,
    CircleDot
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function ActiveSessionPage() {
    const [seconds, setSeconds] = useState(14 * 60 + 23); // 14:23
    const [responseMode, setResponseMode] = useState<"audio" | "text">("audio");
    const [textResponse, setTextResponse] = useState("");

    useEffect(() => {
        const interval = setInterval(() => setSeconds(s => s + 1), 1000);
        return () => clearInterval(interval);
    }, []);

    const formatTime = (totalSeconds: number) => {
        const m = Math.floor(totalSeconds / 60).toString().padStart(2, '0');
        const s = (totalSeconds % 60).toString().padStart(2, '0');
        return `${m}:${s}`;
    };

    return (
        <div className="min-h-screen flex flex-col overflow-hidden bg-slate-50 text-slate-900 dark:bg-gray-950 dark:text-gray-100 transition-colors relative font-display">

            {/* Ambient Background Glow (Dark Mode only or light mode variant) */}
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
                <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-primary/10 dark:bg-primary/5 rounded-full blur-[120px]"></div>
                <div className="absolute bottom-[-20%] right-[-10%] w-[40%] h-[40%] bg-primary/10 dark:bg-indigo-900/10 rounded-full blur-[120px]"></div>
            </div>

            {/* Top Navigation / Status Bar */}
            <header className="h-16 border-b border-gray-200 dark:border-white/10 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md sticky top-0 z-50 flex items-center justify-between px-6 lg:px-10 transition-colors">
                {/* Left: Branding & Status */}
                <div className="flex items-center gap-6">
                    <div className="flex items-center gap-3">
                        <div className="size-8 rounded bg-gradient-to-br from-primary to-indigo-700 flex items-center justify-center text-white shadow-lg shadow-primary/20">
                            <Brain size={20} />
                        </div>
                        <span className="font-bold text-lg tracking-tight text-slate-900 dark:text-white">BrainTrain</span>
                    </div>
                    <div className="h-6 w-px bg-gray-200 dark:bg-white/10 mx-2"></div>
                    <div className="flex items-center gap-2 text-slate-500 dark:text-gray-400 text-sm hidden sm:flex">
                        <CircleDot className="text-emerald-500" size={14} />
                        <span className="font-medium text-emerald-600 dark:text-emerald-400">Live Session</span>
                        <span className="text-gray-400 dark:text-gray-600 px-1">•</span>
                        <span>Senior Engineer Mock</span>
                    </div>
                </div>

                {/* Center: Timer */}
                <div className="absolute left-1/2 -translate-x-1/2 flex items-center gap-2 bg-slate-100 dark:bg-white/5 px-4 py-1.5 rounded-full border border-gray-200 dark:border-white/5">
                    <TimerIcon className="text-primary dark:text-indigo-400" size={18} />
                    <span className="font-mono text-lg font-medium text-slate-900 dark:text-white tracking-widest">{formatTime(seconds)}</span>
                </div>

                {/* Right: Controls */}
                <div className="flex items-center gap-4">
                    <button className="size-10 flex items-center justify-center rounded-full hover:bg-slate-200 dark:hover:bg-white/5 text-slate-500 dark:text-gray-400 transition-colors" title="Settings">
                        <Settings size={20} />
                    </button>
                    <div className="flex gap-2 sm:gap-3">
                        <button className="flex items-center gap-2 px-3 sm:px-4 py-2 rounded-lg bg-slate-100 dark:bg-white/5 border border-gray-200 dark:border-white/10 text-sm font-medium hover:bg-slate-200 dark:hover:bg-white/10 transition-all text-slate-700 dark:text-gray-100">
                            <Pause size={16} />
                            <span className="hidden sm:inline">Pause</span>
                        </button>
                        <Link href="/dashboard/sessions/evaluation">
                            <button className="flex items-center gap-2 px-3 sm:px-4 py-2 rounded-lg bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-600 dark:text-red-400 text-sm font-medium hover:bg-red-100 dark:hover:bg-red-500/20 transition-all">
                                <X size={16} />
                                <span className="hidden sm:inline">End Session</span>
                            </button>
                        </Link>
                    </div>
                    <div className="hidden sm:flex ml-2 size-9 rounded-full items-center justify-center bg-primary/10 border border-primary/20 text-primary font-bold text-sm">
                        JD
                    </div>
                </div>
            </header>

            {/* Main Content Area */}
            <main className="flex-1 flex overflow-hidden relative z-10 w-full max-w-[1600px] mx-auto p-4 lg:p-10">
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-full w-full">

                    {/* LEFT COLUMN: Interaction Area (8 cols) */}
                    <div className="lg:col-span-8 flex flex-col gap-6 h-full">

                        {/* Question Card */}
                        <div className="bg-white/60 dark:bg-gray-900/40 backdrop-blur-xl border border-gray-200 dark:border-white/10 p-6 sm:p-8 rounded-2xl shadow-xl dark:shadow-2xl relative overflow-hidden group">
                            <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-primary to-transparent"></div>
                            <div className="flex justify-between items-start mb-6">
                                <div className="flex items-center gap-2">
                                    <span className="px-2.5 py-1 rounded bg-primary/10 dark:bg-primary/20 text-primary dark:text-indigo-400 text-xs font-bold uppercase tracking-wider border border-primary/20">Question 3 of 5</span>
                                    <span className="px-2.5 py-1 rounded bg-gray-100 dark:bg-white/5 text-slate-500 dark:text-gray-400 text-xs font-medium uppercase tracking-wider border border-gray-200 dark:border-white/5">System Design</span>
                                </div>
                                <button className="text-slate-400 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white transition-colors">
                                    <Bookmark size={20} />
                                </button>
                            </div>
                            <h1 className="text-2xl lg:text-3xl font-semibold leading-tight text-slate-900 dark:text-white mb-4">
                                Describe a challenging technical tradeoff you've made in a distributed system.
                            </h1>
                            <p className="text-base sm:text-lg text-slate-600 dark:text-gray-400 font-light leading-relaxed max-w-3xl">
                                Focus on the context, the options you considered (e.g., consistency vs. availability), and why you chose the final path. How did this impact the system's long-term scalability?
                            </p>
                        </div>

                        {/* Response Area */}
                        <div className="flex-1 flex flex-col bg-white/60 dark:bg-gray-900/40 backdrop-blur-xl border border-gray-200 dark:border-white/10 rounded-2xl p-1 overflow-hidden">
                            {/* Tabs */}
                            <div className="flex border-b border-gray-200 dark:border-white/5 px-4 pt-4 gap-6 bg-slate-100/50 dark:bg-black/20">
                                <button
                                    onClick={() => setResponseMode("audio")}
                                    className={cn(
                                        "flex items-center gap-2 pb-3 px-2 font-medium text-sm transition-colors border-b-2",
                                        responseMode === "audio"
                                            ? "text-primary dark:text-indigo-400 border-primary"
                                            : "text-slate-500 dark:text-gray-400 border-transparent hover:text-slate-900 dark:hover:text-white"
                                    )}>
                                    <Mic size={18} />
                                    Audio Response
                                </button>
                                <button
                                    onClick={() => setResponseMode("text")}
                                    className={cn(
                                        "flex items-center gap-2 pb-3 px-2 font-medium text-sm transition-colors border-b-2",
                                        responseMode === "text"
                                            ? "text-primary dark:text-indigo-400 border-primary"
                                            : "text-slate-500 dark:text-gray-400 border-transparent hover:text-slate-900 dark:hover:text-white"
                                    )}>
                                    <Keyboard size={18} />
                                    Text Response
                                </button>
                            </div>

                            {/* Active Input Area */}
                            {responseMode === "audio" ? (
                                <div className="flex-1 relative flex flex-col items-center justify-center p-8 bg-gradient-to-b from-transparent to-slate-100/50 dark:to-black/40">
                                    {/* Visualization Box */}
                                    <div className="w-full max-w-xl h-32 flex items-center justify-center gap-1.5 mb-8">
                                        {/* Simulated static waves for react component visual */}
                                        <div className="w-1.5 bg-primary/40 rounded-full h-8 animate-pulse"></div>
                                        <div className="w-1.5 bg-primary/40 rounded-full h-12 animate-pulse" style={{ animationDelay: '0.1s' }}></div>
                                        <div className="w-1.5 bg-primary/40 rounded-full h-6 animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                                        <div className="w-1.5 bg-primary/40 rounded-full h-16 animate-pulse" style={{ animationDelay: '0.3s' }}></div>
                                        <div className="w-1.5 bg-primary/40 rounded-full h-10 animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                                        <div className="w-1.5 bg-primary/40 rounded-full h-20 animate-pulse" style={{ animationDelay: '0.1s' }}></div>
                                        <div className="w-1.5 bg-primary/40 rounded-full h-14 animate-pulse" style={{ animationDelay: '0.5s' }}></div>
                                        <div className="w-1.5 bg-primary/60 rounded-full h-24 animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                                        <div className="w-1.5 bg-primary/40 rounded-full h-12 animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                                        <div className="w-1.5 bg-primary/40 rounded-full h-20 animate-pulse" style={{ animationDelay: '0.1s' }}></div>
                                        <div className="w-1.5 bg-primary/40 rounded-full h-10 animate-pulse" style={{ animationDelay: '0.3s' }}></div>
                                        <div className="w-1.5 bg-primary/40 rounded-full h-24 animate-pulse" style={{ animationDelay: '0.5s' }}></div>
                                        <div className="w-1.5 bg-primary/40 rounded-full h-8 animate-pulse"></div>
                                        <div className="w-1.5 bg-primary/40 rounded-full h-14 animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                                        <div className="w-1.5 bg-primary/40 rounded-full h-6 animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                                    </div>

                                    {/* Status Text */}
                                    <div className="text-center mb-8">
                                        <p className="text-slate-900 dark:text-white text-lg font-medium mb-1">Listening...</p>
                                        <p className="text-slate-500 dark:text-gray-400 text-sm">Speak clearly. We are analyzing your tone and pacing.</p>
                                    </div>

                                    {/* Controls */}
                                    <div className="flex items-center gap-6">
                                        <button className="size-12 rounded-full bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 flex items-center justify-center text-slate-500 dark:text-gray-400 hover:bg-slate-100 dark:hover:bg-white/10 hover:text-slate-900 dark:hover:text-white transition-all shadow-sm dark:shadow-none" title="Restart">
                                            <RotateCcw size={20} />
                                        </button>
                                        <button className="size-20 rounded-full bg-gradient-to-br from-primary to-indigo-700 shadow-[0_0_30px_-5px_var(--tw-shadow-color)] shadow-primary/40 dark:shadow-[0_0_40px_-10px_var(--tw-shadow-color)] dark:shadow-primary/50 flex items-center justify-center text-white hover:scale-105 active:scale-95 transition-all border-4 border-white dark:border-gray-900 relative z-10 group">
                                            <Square className="fill-current" size={24} />
                                            {/* Ripple Effect Ring */}
                                            <div className="absolute inset-0 rounded-full border border-primary/50 scale-100 group-hover:scale-110 opacity-0 group-hover:opacity-100 transition-all duration-700"></div>
                                        </button>
                                        <button className="size-12 rounded-full bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 flex items-center justify-center text-slate-500 dark:text-gray-400 hover:bg-slate-100 dark:hover:bg-white/10 hover:text-slate-900 dark:hover:text-white transition-all shadow-sm dark:shadow-none" title="Done">
                                            <Check size={24} />
                                        </button>
                                    </div>
                                </div>
                            ) : (
                                <div className="flex-1 p-6 flex flex-col relative bg-transparent">
                                    <textarea
                                        className="w-full h-full flex-1 resize-none bg-transparent border-none focus:ring-0 p-0 text-slate-800 dark:text-slate-200 text-lg leading-relaxed placeholder:text-slate-400 dark:placeholder:text-slate-600 outline-none"
                                        placeholder="Type your response here. Focus on the STAR method..."
                                        value={textResponse}
                                        onChange={(e) => setTextResponse(e.target.value)}
                                    ></textarea>
                                    <div className="absolute bottom-6 right-6 flex items-center gap-4 bg-white/50 dark:bg-[#1a2026]/80 backdrop-blur-md rounded-lg pl-4 pr-4 py-2 border border-gray-100 dark:border-white/5">
                                        <div className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                                            <span className="text-primary dark:text-indigo-400 font-bold">{textResponse.trim().split(/\s+/).filter(x => x).length}</span> words
                                        </div>
                                        <div className="h-4 w-px bg-slate-200 dark:bg-slate-700"></div>
                                        <div className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide flex items-center gap-1.5">
                                            <span className="size-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                                            Saving...
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* RIGHT COLUMN: Context & Support (4 cols) */}
                    <div className="lg:col-span-4 flex flex-col gap-6 h-full">
                        {/* Evaluation Context Panel */}
                        <div className="bg-white/60 dark:bg-gray-900/40 backdrop-blur-xl border border-gray-200 dark:border-white/10 p-6 rounded-2xl flex flex-col gap-4 shadow-sm dark:shadow-none">
                            <div className="flex items-center justify-between">
                                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500 dark:text-gray-400">Evaluation Context</h3>
                                <Info className="text-slate-400 dark:text-gray-500" size={18} />
                            </div>
                            <div className="space-y-4">
                                <div className="flex gap-3 items-start">
                                    <div className="mt-1 size-8 rounded bg-primary/10 flex-shrink-0 flex items-center justify-center text-primary dark:text-indigo-400 border border-primary/20">
                                        <Settings size={16} />
                                    </div>
                                    <div>
                                        <h4 className="text-slate-900 dark:text-white text-sm font-semibold">Technical Depth</h4>
                                        <p className="text-xs text-slate-500 dark:text-gray-400 mt-1 leading-relaxed">Assessing your ability to justify architectural decisions based on CAP theorem constraints.</p>
                                    </div>
                                </div>
                                <div className="flex gap-3 items-start">
                                    <div className="mt-1 size-8 rounded bg-primary/10 flex-shrink-0 flex items-center justify-center text-primary dark:text-indigo-400 border border-primary/20">
                                        <Mic size={16} />
                                    </div>
                                    <div>
                                        <h4 className="text-slate-900 dark:text-white text-sm font-semibold">Communication</h4>
                                        <p className="text-xs text-slate-500 dark:text-gray-400 mt-1 leading-relaxed">Clarity in explaining complex concepts to mixed stakeholders.</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* AI Tips Widget */}
                        <div className="bg-white/60 dark:bg-gray-900/40 backdrop-blur-xl border border-gray-200 dark:border-white/10 p-0 rounded-2xl overflow-hidden flex-1 flex flex-col shadow-sm dark:shadow-none max-h-[400px]">
                            <div className="p-4 sm:p-5 border-b border-gray-200 dark:border-white/5 bg-slate-50 dark:bg-white/5 flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <Lightbulb className="text-amber-500 dark:text-yellow-400" size={18} />
                                    <h3 className="font-bold text-slate-900 dark:text-white text-sm">Real-time Tips</h3>
                                </div>
                            </div>
                            <div className="p-4 sm:p-5 flex-1 overflow-y-auto custom-scrollbar">
                                <div className="bg-amber-50 dark:bg-yellow-500/5 border border-amber-200 dark:border-yellow-500/20 rounded-lg p-4 mb-4">
                                    <p className="text-amber-700 dark:text-yellow-200 text-xs font-semibold mb-1">Structure suggestion</p>
                                    <p className="text-slate-600 dark:text-gray-400 text-sm leading-relaxed">Consider using the STAR method. Start briefly with the <strong>Situation</strong> before diving deep into the technical <strong>Action</strong>.</p>
                                </div>
                                <div className="bg-slate-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg p-4">
                                    <p className="text-primary dark:text-indigo-400 text-xs font-semibold mb-1">Key Terminology</p>
                                    <p className="text-slate-600 dark:text-gray-400 text-sm leading-relaxed">Don't forget to mention latency implications if you chose consistency over availability.</p>
                                </div>
                            </div>
                            <div className="p-3 sm:p-4 border-t border-gray-200 dark:border-white/5 bg-slate-50 dark:bg-black/20 text-center">
                                <button className="text-xs font-medium text-slate-500 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white flex items-center justify-center gap-1 transition-colors w-full">
                                    <span>View Transcript History</span>
                                    <ChevronDown size={14} />
                                </button>
                            </div>
                        </div>

                    </div>
                </div>
            </main>
        </div>
    );
}

// Inline timer icon component just to match UI
function TimerIcon(props: any) {
    return (
        <svg
            {...props}
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <line x1="10" x2="14" y1="2" y2="2" />
            <line x1="12" x2="15" y1="14" y2="11" />
            <circle cx="12" cy="14" r="8" />
        </svg>
    )
}
