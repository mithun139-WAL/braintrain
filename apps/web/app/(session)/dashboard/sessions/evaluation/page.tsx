"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
    Brain,
    Calendar,
    TrendingUp,
    Download,
    RotateCcw,
    Code,
    MessageSquare,
    Lightbulb,
    Layers,
    ChevronDown,
    Bot,
    ArrowRight,
    Sparkles,
    CheckCircle2,
    AlertTriangle,
    Flag,
    Activity,
    Target
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function EvaluationPage() {
    const [expandedQ, setExpandedQ] = useState<number | null>(1);

    return (
        <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 dark:bg-gray-950 dark:text-gray-100 font-display transition-colors">
            {/* Top Navigation Bar */}
            <header className="sticky top-0 z-50 w-full border-b border-gray-200 bg-white/80 dark:border-gray-800 dark:bg-gray-900/80 backdrop-blur-md transition-colors">
                <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center gap-3">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-white shadow-md shadow-primary/20">
                            <Brain size={20} />
                        </div>
                        <span className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">BrainTrain</span>
                    </div>
                    <div className="hidden md:flex items-center gap-8">
                        <Link href="/dashboard" className="text-sm font-medium text-slate-500 hover:text-primary dark:text-gray-400 dark:hover:text-indigo-400 transition-colors">Dashboard</Link>
                        <span className="text-sm font-bold text-slate-900 dark:text-white border-b-2 border-primary pb-0.5">Evaluations</span>
                        <Link href="/dashboard/sessions" className="text-sm font-medium text-slate-500 hover:text-primary dark:text-gray-400 dark:hover:text-indigo-400 transition-colors">Practice</Link>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-sm ring-2 ring-primary/20">
                            JD
                        </div>
                    </div>
                </div>
            </header>

            <main className="flex-grow py-8 px-4 sm:px-6 lg:px-8 w-full max-w-7xl mx-auto space-y-8">
                {/* Header Section */}
                <header className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-gray-200 dark:border-gray-800 transition-colors">
                    <div className="space-y-2">
                        <div className="flex items-center gap-2 text-sm font-semibold text-primary dark:text-indigo-400">
                            <Calendar size={16} />
                            <span>Oct 24, 2023 • 45m Duration</span>
                        </div>
                        <h1 className="text-3xl md:text-4xl font-black tracking-tight text-slate-900 dark:text-white">AI Evaluation Report</h1>
                        <p className="text-slate-500 dark:text-gray-400 font-medium">Senior Software Engineer Mock Interview</p>
                    </div>
                    <div className="flex gap-3">
                        <button className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 hover:bg-slate-50 dark:hover:bg-gray-800 transition-all text-sm font-bold text-slate-700 dark:text-gray-200 shadow-sm">
                            <Download size={18} />
                            <span className="hidden sm:inline">Export PDF</span>
                        </button>
                        <Link href="/dashboard/sessions/start">
                            <button className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-primary hover:bg-primary-dark text-white transition-all text-sm font-bold shadow-md shadow-primary/20">
                                <RotateCcw size={18} />
                                <span>Retake Interview</span>
                            </button>
                        </Link>
                    </div>
                </header>

                {/* KPI Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                    {/* Hero Score Card */}
                    <div className="lg:col-span-4 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-8 flex flex-col items-center justify-center relative overflow-hidden group shadow-sm dark:shadow-none transition-colors">
                        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent opacity-50 group-hover:opacity-100 transition-opacity"></div>
                        <h3 className="text-slate-500 dark:text-gray-400 font-bold mb-6 uppercase tracking-wider text-xs z-10 flex items-center gap-2">
                            <Activity size={16} className="text-primary" />
                            Overall Performance Score
                        </h3>
                        <div className="relative flex items-center justify-center w-40 h-40 mb-6 z-10">
                            {/* SVG Progress Circle */}
                            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                                <circle cx="50" cy="50" fill="none" r="45" stroke="currentColor" strokeWidth="8" className="text-slate-100 dark:text-gray-800"></circle>
                                <circle cx="50" cy="50" fill="none" r="45" stroke="currentColor" strokeDasharray="283" strokeDashoffset="60" strokeLinecap="round" strokeWidth="8" className="text-primary drop-shadow-[0_0_8px_rgba(79,70,229,0.4)]"></circle>
                            </svg>
                            <div className="absolute flex flex-col items-center">
                                <span className="text-5xl font-black text-slate-900 dark:text-white tracking-tighter">78</span>
                                <span className="text-sm text-slate-500 dark:text-gray-400 font-bold">/ 100</span>
                            </div>
                        </div>
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-100 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/20 text-emerald-700 dark:text-emerald-400 text-sm font-bold mb-3 z-10">
                            <TrendingUp size={16} />
                            <span>Top 20% Percentile</span>
                        </div>
                        <p className="text-center text-sm text-slate-600 dark:text-gray-400 max-w-[280px] z-10 font-medium">You scored higher than 80% of candidates applying for Senior Engineering roles.</p>
                    </div>

                    {/* Detailed Metrics Grid */}
                    <div className="lg:col-span-8 grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5 flex flex-col justify-between hover:border-primary/30 transition-all shadow-sm dark:shadow-none group">
                            <div className="flex justify-between items-start mb-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2.5 rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-white transition-colors">
                                        <Code size={20} />
                                    </div>
                                    <span className="font-bold text-slate-900 dark:text-white">Technical Depth</span>
                                </div>
                                <span className="text-xl font-black text-slate-900 dark:text-white">92%</span>
                            </div>
                            <div className="w-full bg-slate-100 dark:bg-gray-800 rounded-full h-2 mb-2 overflow-hidden">
                                <div className="bg-primary h-2 rounded-full" style={{ width: '92%' }}></div>
                            </div>
                            <p className="text-sm text-slate-500 dark:text-gray-400">Exceptional grasp of core algorithms and optimal caching mechanisms.</p>
                        </div>

                        <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5 flex flex-col justify-between hover:border-amber-500/30 transition-all shadow-sm dark:shadow-none group">
                            <div className="flex justify-between items-start mb-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2.5 rounded-lg bg-amber-100 dark:bg-amber-500/10 text-amber-600 dark:text-amber-500 group-hover:bg-amber-500 group-hover:text-white transition-colors">
                                        <MessageSquare size={20} />
                                    </div>
                                    <span className="font-bold text-slate-900 dark:text-white">Communication</span>
                                </div>
                                <span className="text-xl font-black text-slate-900 dark:text-white">65%</span>
                            </div>
                            <div className="w-full bg-slate-100 dark:bg-gray-800 rounded-full h-2 mb-2 overflow-hidden">
                                <div className="bg-amber-500 h-2 rounded-full" style={{ width: '65%' }}></div>
                            </div>
                            <p className="text-sm text-slate-500 dark:text-gray-400">Pacing rushed during behavioral sections. Needs more STAR structure.</p>
                        </div>

                        <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5 flex flex-col justify-between hover:border-emerald-500/30 transition-all shadow-sm dark:shadow-none group">
                            <div className="flex justify-between items-start mb-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2.5 rounded-lg bg-emerald-100 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-500 group-hover:bg-emerald-500 group-hover:text-white transition-colors">
                                        <Lightbulb size={20} />
                                    </div>
                                    <span className="font-bold text-slate-900 dark:text-white">Problem Solving</span>
                                </div>
                                <span className="text-xl font-black text-slate-900 dark:text-white">88%</span>
                            </div>
                            <div className="w-full bg-slate-100 dark:bg-gray-800 rounded-full h-2 mb-2 overflow-hidden">
                                <div className="bg-emerald-500 h-2 rounded-full" style={{ width: '88%' }}></div>
                            </div>
                            <p className="text-sm text-slate-500 dark:text-gray-400">Strong analytical approach to edge cases and error handling patterns.</p>
                        </div>

                        <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5 flex flex-col justify-between hover:border-primary/30 transition-all shadow-sm dark:shadow-none group">
                            <div className="flex justify-between items-start mb-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2.5 rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-white transition-colors">
                                        <Layers size={20} />
                                    </div>
                                    <span className="font-bold text-slate-900 dark:text-white">System Design</span>
                                </div>
                                <span className="text-xl font-black text-slate-900 dark:text-white">82%</span>
                            </div>
                            <div className="w-full bg-slate-100 dark:bg-gray-800 rounded-full h-2 mb-2 overflow-hidden">
                                <div className="bg-primary h-2 rounded-full" style={{ width: '82%' }}></div>
                            </div>
                            <p className="text-sm text-slate-500 dark:text-gray-400">Excellent theoretical knowledge of sharding and high-availability setups.</p>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Executive Summary */}
                    <div className="lg:col-span-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 sm:p-8 flex flex-col shadow-sm dark:shadow-none">
                        <h3 className="text-xl font-black text-slate-900 dark:text-white mb-6 flex items-center gap-2">
                            <Sparkles className="text-primary" />
                            Executive AI Feedback
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 h-full">
                            {/* Strengths */}
                            <div className="space-y-4">
                                <h4 className="text-sm font-bold text-slate-400 dark:text-gray-500 uppercase tracking-wider mb-2 border-b border-gray-100 dark:border-gray-800 pb-2">Top Strengths</h4>
                                <div className="flex gap-3 items-start">
                                    <div className="mt-1 min-w-[20px] text-emerald-500">
                                        <CheckCircle2 size={20} />
                                    </div>
                                    <div>
                                        <p className="text-slate-900 dark:text-white font-bold text-sm">Deep Technical Knowledge</p>
                                        <p className="text-slate-600 dark:text-gray-400 text-sm leading-relaxed mt-1">Demonstrated advanced understanding of distributed systems and CAP theorem nuances perfectly.</p>
                                    </div>
                                </div>
                                <div className="flex gap-3 items-start">
                                    <div className="mt-1 min-w-[20px] text-emerald-500">
                                        <CheckCircle2 size={20} />
                                    </div>
                                    <div>
                                        <p className="text-slate-900 dark:text-white font-bold text-sm">Structured Problem Solving</p>
                                        <p className="text-slate-600 dark:text-gray-400 text-sm leading-relaxed mt-1">Consistently broke down complex requirements into manageable components before coding gracefully.</p>
                                    </div>
                                </div>
                            </div>

                            {/* Improvements */}
                            <div className="space-y-4">
                                <h4 className="text-sm font-bold text-slate-400 dark:text-gray-500 uppercase tracking-wider mb-2 border-b border-gray-100 dark:border-gray-800 pb-2">Critical Focus Areas</h4>
                                <div className="bg-slate-50 dark:bg-gray-800/50 border border-primary/20 rounded-xl p-4 relative overflow-hidden transition-colors">
                                    <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary"></div>
                                    <div className="flex gap-3 items-start">
                                        <div className="min-w-[20px] text-primary">
                                            <Target size={20} />
                                        </div>
                                        <div>
                                            <p className="text-slate-900 dark:text-white font-bold text-sm">Communication Pacing</p>
                                            <p className="text-slate-600 dark:text-gray-400 text-sm leading-relaxed mt-1">Tendency to rush through initial behavioral explanations. Pause to check for understanding.</p>
                                        </div>
                                    </div>
                                </div>
                                <div className="bg-slate-50 dark:bg-gray-800/50 border border-amber-500/20 rounded-xl p-4 relative overflow-hidden transition-colors">
                                    <div className="absolute left-0 top-0 bottom-0 w-1 bg-amber-500"></div>
                                    <div className="flex gap-3 items-start">
                                        <div className="min-w-[20px] text-amber-500">
                                            <AlertTriangle size={20} />
                                        </div>
                                        <div>
                                            <p className="text-slate-900 dark:text-white font-bold text-sm">Edge Case Coverage</p>
                                            <p className="text-slate-600 dark:text-gray-400 text-sm leading-relaxed mt-1">Missed two potential race conditions in the database locking mechanism discussion.</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Skill Radar Chart */}
                    <div className="lg:col-span-1 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 flex flex-col shadow-sm dark:shadow-none transition-colors">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-lg font-black text-slate-900 dark:text-white">Skill Distribution</h3>
                            <div className="flex items-center gap-2 text-xs font-bold">
                                <span className="w-3 h-3 rounded-full bg-primary"></span> You
                                <span className="w-3 h-3 rounded-full bg-slate-300 dark:bg-gray-600 ml-2"></span> Avg
                            </div>
                        </div>
                        <div className="flex-grow flex items-center justify-center relative py-4 bg-slate-50 dark:bg-[#111624] rounded-xl border border-gray-100 dark:border-gray-800">
                            {/* Abstract Radar Chart SVG mapped to Light/Dark Mode */}
                            <svg className="w-full h-64" viewBox="0 0 200 200">
                                <polygon fill="none" points="100,20 180,65 180,145 100,190 20,145 20,65" stroke="currentColor" strokeWidth="1" className="text-slate-200 dark:text-gray-700"></polygon>
                                <polygon fill="none" points="100,40 160,75 160,135 100,170 40,135 40,75" stroke="currentColor" strokeWidth="1" className="text-slate-200 dark:text-gray-700"></polygon>
                                <polygon fill="none" points="100,60 140,82 140,128 100,150 60,128 60,82" stroke="currentColor" strokeWidth="1" className="text-slate-200 dark:text-gray-700"></polygon>
                                {/* Benchmark Data */}
                                <polygon fill="currentColor" className="text-slate-300/30 dark:text-gray-600/30" points="100,50 150,80 150,130 100,160 50,130 50,80" stroke="currentColor" strokeDasharray="4" strokeWidth="2"></polygon>
                                {/* User Data (Primary) */}
                                <polygon fill="var(--primary)" fillOpacity="0.25" points="100,30 170,70 160,140 100,180 30,140 35,70" stroke="var(--primary)" strokeWidth="3"></polygon>
                                {/* Labels */}
                                <text x="100" y="15" textAnchor="middle" fontSize="10" fontWeight="bold" fill="currentColor" className="text-slate-500 dark:text-gray-400">Coding</text>
                                <text x="190" y="65" textAnchor="start" fontSize="10" fontWeight="bold" fill="currentColor" className="text-slate-500 dark:text-gray-400">System</text>
                                <text x="190" y="155" textAnchor="start" fontSize="10" fontWeight="bold" fill="currentColor" className="text-slate-500 dark:text-gray-400">Soft Skills</text>
                                <text x="100" y="200" textAnchor="middle" fontSize="10" fontWeight="bold" fill="currentColor" className="text-slate-500 dark:text-gray-400">Testing</text>
                                <text x="10" y="155" textAnchor="end" fontSize="10" fontWeight="bold" fill="currentColor" className="text-slate-500 dark:text-gray-400">DB</text>
                                <text x="10" y="65" textAnchor="end" fontSize="10" fontWeight="bold" fill="currentColor" className="text-slate-500 dark:text-gray-400">Arch</text>
                            </svg>
                        </div>
                    </div>
                </div>

                {/* Detailed Transcript Analysis Accordion */}
                <div className="space-y-4 pt-4">
                    <h3 className="text-2xl font-black text-slate-900 dark:text-white mb-6">Question Analysis & Transcripts</h3>

                    {/* Accordion Item 1 */}
                    <div className="bg-white dark:bg-gray-900 rounded-xl overflow-hidden border border-gray-200 dark:border-gray-800 shadow-sm transition-all group">
                        <button
                            onClick={() => setExpandedQ(expandedQ === 1 ? null : 1)}
                            className="w-full p-5 flex justify-between items-center bg-white hover:bg-slate-50 dark:bg-gray-900 dark:hover:bg-gray-800 transition-colors focus:outline-none"
                        >
                            <div className="flex gap-4 items-center text-left">
                                <div className="flex-shrink-0 size-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary font-black">
                                    Q1
                                </div>
                                <div>
                                    <h4 className="font-bold text-slate-900 dark:text-white pr-4">Explain the difference between REST and GraphQL.</h4>
                                    <div className="flex gap-2 mt-1.5">
                                        <span className="text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-gray-800 text-slate-600 dark:text-gray-400 border border-gray-200 dark:border-gray-700 font-medium">System Design</span>
                                        <span className="text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-gray-800 text-slate-600 dark:text-gray-400 border border-gray-200 dark:border-gray-700 font-medium">02:15m</span>
                                    </div>
                                </div>
                            </div>
                            <div className="flex items-center gap-4 flex-shrink-0 pl-4">
                                <span className="bg-emerald-100 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 font-black px-3 py-1 rounded-lg">95/100</span>
                                <ChevronDown className={cn("text-slate-400 transition-transform", expandedQ === 1 ? "rotate-180" : "")} />
                            </div>
                        </button>

                        {/* Expanded Content */}
                        {expandedQ === 1 && (
                            <div className="p-6 border-t border-gray-100 dark:border-gray-800 bg-slate-50 dark:bg-[#111624]">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div className="bg-white dark:bg-gray-900 p-5 rounded-xl border border-gray-200 dark:border-gray-800">
                                        <p className="text-xs font-black text-slate-400 dark:text-gray-500 uppercase mb-3 tracking-wider flex items-center gap-1.5 border-b border-gray-100 dark:border-gray-800 pb-2">
                                            <Flag size={14} /> Transcript Summary
                                        </p>
                                        <p className="text-sm text-slate-700 dark:text-gray-300 leading-relaxed font-medium">
                                            "REST is strictly an architectural style based on multiple resource endpoints, while GraphQL is a query language operating typically on a single endpoint. You highlighted the critical over-fetching/under-fetching problem that GraphQL solves optimally."
                                        </p>
                                    </div>
                                    <div className="bg-primary/5 dark:bg-primary/10 p-5 rounded-xl border border-primary/20">
                                        <p className="text-xs font-black text-primary uppercase mb-3 tracking-wider flex items-center gap-1.5 border-b border-primary/10 pb-2">
                                            <Bot size={14} /> AI Recommendation
                                        </p>
                                        <p className="text-sm text-slate-700 dark:text-gray-300 leading-relaxed font-medium">
                                            Excellent technical explanation. To secure a full 100%, you could have briefly cited caching strategies, noting how REST securely leverages HTTP caching natively, which requires significantly more complex implementations in GraphQL architectures.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Accordion Item 2 */}
                    <div className="bg-white dark:bg-gray-900 rounded-xl overflow-hidden border border-gray-200 dark:border-gray-800 shadow-sm transition-all group">
                        <button
                            onClick={() => setExpandedQ(expandedQ === 2 ? null : 2)}
                            className="w-full p-5 flex justify-between items-center bg-white hover:bg-slate-50 dark:bg-gray-900 dark:hover:bg-gray-800 transition-colors focus:outline-none"
                        >
                            <div className="flex gap-4 items-center text-left">
                                <div className="flex-shrink-0 size-10 rounded-xl bg-amber-100 dark:bg-amber-500/10 flex items-center justify-center text-amber-600 dark:text-amber-500 font-black">
                                    Q2
                                </div>
                                <div>
                                    <h4 className="font-bold text-slate-900 dark:text-white pr-4">How would you handle database sharding for a global user base?</h4>
                                    <div className="flex gap-2 mt-1.5">
                                        <span className="text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-gray-800 text-slate-600 dark:text-gray-400 border border-gray-200 dark:border-gray-700 font-medium">Database</span>
                                        <span className="text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-gray-800 text-slate-600 dark:text-gray-400 border border-gray-200 dark:border-gray-700 font-medium">04:30m</span>
                                    </div>
                                </div>
                            </div>
                            <div className="flex items-center gap-4 flex-shrink-0 pl-4">
                                <span className="bg-amber-100 dark:bg-amber-500/10 text-amber-600 dark:text-amber-500 font-black px-3 py-1 rounded-lg">72/100</span>
                                <ChevronDown className={cn("text-slate-400 transition-transform", expandedQ === 2 ? "rotate-180" : "")} />
                            </div>
                        </button>
                    </div>

                </div>

                {/* Footer Actions */}
                <div className="flex justify-center pt-8 pb-12">
                    <p className="text-slate-500 dark:text-gray-400 font-medium text-sm flex items-center gap-1.5">
                        Next suggested step:
                        <Link href="/dashboard/sessions/start" className="text-primary hover:text-primary-dark dark:hover:text-indigo-400 font-bold underline decoration-primary/30 underline-offset-4 transition-colors">
                            Advanced System Design Practice
                        </Link>
                    </p>
                </div>

            </main>
        </div>
    );
}
