"use client";

import React from "react";
import {
    Activity,
    Calendar,
    ChevronDown,
    Download,
    TrendingUp,
    ArrowDown,
    Plus,
    Sparkles,
    Radar,
    MicOff,
    AlignLeft,
    Timer,
    Code,
    MessageSquare,
    Layers,
    Binary
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function PerformanceTrendsPage() {
    return (
        <div className="flex flex-col gap-8 relative w-full font-display">
            {/* Background Gradients for atmosphere */}
            <div className="absolute top-[-2rem] left-[-2rem] right-[-2rem] h-96 bg-gradient-to-b from-primary/5 to-transparent pointer-events-none -mr-8 -ml-8"></div>
            <div className="absolute top-[-2rem] right-[-2rem] w-1/2 h-96 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-primary/10 via-transparent to-transparent pointer-events-none -mr-8"></div>

            {/* Header Section */}
            <header className="flex flex-wrap items-end justify-between gap-4 relative z-10 w-full">
                <div className="flex flex-col gap-2">
                    <div className="flex items-center gap-2 text-primary dark:text-indigo-400">
                        <Activity size={20} />
                        <span className="text-xs font-bold tracking-widest uppercase">Analytics</span>
                    </div>
                    <h2 className="text-3xl md:text-4xl font-bold leading-tight tracking-tight text-slate-900 dark:text-white">
                        Performance Trends
                    </h2>
                    <p className="text-slate-500 dark:text-slate-400 text-sm md:text-base max-w-xl">
                        Track your AI-evaluated interview readiness and cognitive patterns over time.
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="bg-white/60 dark:bg-gray-900/60 backdrop-blur-xl border border-gray-200 dark:border-white/5 flex items-center gap-2 rounded-lg px-3 py-2 text-slate-700 dark:text-slate-300 shadow-sm transition-colors cursor-pointer hover:bg-slate-50 dark:hover:bg-gray-800">
                        <Calendar size={16} />
                        <span className="text-sm font-medium">Last 30 Days</span>
                        <ChevronDown size={16} className="ml-2" />
                    </div>
                    <button className="flex h-10 items-center gap-2 rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 px-4 text-sm font-bold text-slate-700 dark:text-white hover:bg-slate-50 dark:hover:bg-gray-800 transition-colors shadow-sm">
                        <Download size={18} />
                        <span className="hidden sm:inline">Export Report</span>
                    </button>
                </div>
            </header>

            {/* KPI Cards */}
            <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 relative z-10 w-full">
                {/* Card 1 */}
                <div className="bg-white/60 dark:bg-gray-900/60 backdrop-blur-xl border border-gray-200 dark:border-white/5 group relative overflow-hidden rounded-xl p-6 transition-all hover:border-primary/30 hover:shadow-md dark:shadow-none shadow-sm">
                    <div className="absolute top-0 left-0 h-1 w-full bg-gradient-to-r from-primary/0 via-primary to-primary/0 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    <div className="flex flex-col gap-1">
                        <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Current Streak</p>
                        <div className="flex items-baseline gap-2">
                            <h3 className="text-3xl font-black text-slate-900 dark:text-white">12</h3>
                            <span className="text-sm text-slate-500">days</span>
                        </div>
                        <div className="mt-2 flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
                            <TrendingUp size={14} />
                            <span className="text-xs font-bold">+2 days</span>
                        </div>
                    </div>
                </div>

                {/* Card 2 */}
                <div className="bg-white/60 dark:bg-gray-900/60 backdrop-blur-xl border border-gray-200 dark:border-white/5 group relative overflow-hidden rounded-xl p-6 transition-all hover:border-primary/30 hover:shadow-md dark:shadow-none shadow-sm">
                    <div className="absolute top-0 left-0 h-1 w-full bg-gradient-to-r from-primary/0 via-primary to-primary/0 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    <div className="flex flex-col gap-1">
                        <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Avg Response Time</p>
                        <div className="flex items-baseline gap-2">
                            <h3 className="text-3xl font-black text-slate-900 dark:text-white">45s</h3>
                        </div>
                        <div className="mt-2 flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
                            <ArrowDown size={14} />
                            <span className="text-xs font-bold">-5s (Improved)</span>
                        </div>
                    </div>
                </div>

                {/* Card 3 */}
                <div className="bg-white/60 dark:bg-gray-900/60 backdrop-blur-xl border border-gray-200 dark:border-white/5 group relative overflow-hidden rounded-xl p-6 transition-all hover:border-primary/30 hover:shadow-md dark:shadow-none shadow-sm">
                    <div className="absolute top-0 left-0 h-1 w-full bg-gradient-to-r from-primary/0 via-primary to-primary/0 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    <div className="flex flex-col gap-1">
                        <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Sessions Completed</p>
                        <div className="flex items-baseline gap-2">
                            <h3 className="text-3xl font-black text-slate-900 dark:text-white">28</h3>
                        </div>
                        <div className="mt-2 flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
                            <Plus size={14} />
                            <span className="text-xs font-bold">+4 this week</span>
                        </div>
                    </div>
                </div>

                {/* Card 4 */}
                <div className="bg-white/60 dark:bg-gray-900/60 backdrop-blur-xl border border-gray-200 dark:border-white/5 group relative overflow-hidden rounded-xl p-6 transition-all hover:border-primary/30 hover:shadow-md dark:shadow-none shadow-sm">
                    <div className="absolute top-0 left-0 h-1 w-full bg-gradient-to-r from-primary/0 via-primary to-primary/0 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    <div className="flex flex-col gap-1">
                        <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Consistency Score</p>
                        <div className="flex items-baseline gap-2">
                            <h3 className="text-3xl font-black text-slate-900 dark:text-white">94%</h3>
                        </div>
                        <div className="mt-2 flex items-center gap-1 text-primary">
                            <Sparkles size={14} />
                            <span className="text-xs font-bold">Top 5%</span>
                        </div>
                    </div>
                </div>
            </section>

            {/* Charts Section Row 1 */}
            <section className="grid grid-cols-1 gap-6 lg:grid-cols-3 relative z-10 w-full">
                {/* Main Chart: Overall Score */}
                <div className="bg-white/60 dark:bg-gray-900/60 backdrop-blur-xl border border-gray-200 dark:border-white/5 col-span-1 lg:col-span-2 flex flex-col rounded-xl p-6 md:p-8 shadow-sm dark:shadow-none">
                    <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
                        <div>
                            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Overall Score Progression</h3>
                            <p className="text-sm text-slate-500 dark:text-slate-400">Composite metric based on technical & behavioral analysis</p>
                        </div>
                        <div className="flex items-center gap-4">
                            <div className="flex flex-col items-end">
                                <span className="text-2xl font-black bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 to-primary">85/100</span>
                                <span className="text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-1 font-semibold">
                                    <TrendingUp size={14} /> 15% vs last month
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Chart SVG Area */}
                    <div className="relative flex-1 min-h-[240px] w-full">
                        {/* Grid lines */}
                        <div className="absolute inset-0 flex flex-col justify-between text-xs text-slate-400 dark:text-slate-600 font-medium">
                            <div className="border-b border-gray-100 dark:border-white/5 pb-1">100</div>
                            <div className="border-b border-gray-100 dark:border-white/5 pb-1">75</div>
                            <div className="border-b border-gray-100 dark:border-white/5 pb-1">50</div>
                            <div className="border-b border-gray-100 dark:border-white/5 pb-1">25</div>
                            <div className="border-b border-gray-100 dark:border-white/5 pb-1">0</div>
                        </div>

                        {/* Chart Lines */}
                        <svg className="absolute inset-0 h-full w-full pt-6" preserveAspectRatio="none" viewBox="0 0 400 150">
                            {/* Gradient Fill */}
                            <defs>
                                <linearGradient id="chartGradient" x1="0" x2="0" y1="0" y2="1">
                                    <stop offset="0%" stopColor="var(--primary, #4f46e5)" stopOpacity="0.2"></stop>
                                    <stop offset="100%" stopColor="var(--primary, #4f46e5)" stopOpacity="0"></stop>
                                </linearGradient>
                            </defs>
                            <path d="M0,120 Q40,110 80,90 T160,80 T240,50 T320,40 T400,20 L400,150 L0,150 Z" fill="url(#chartGradient)"></path>
                            {/* Main Line */}
                            <path className="drop-shadow-[0_0_8px_rgba(79,70,229,0.5)]" d="M0,120 Q40,110 80,90 T160,80 T240,50 T320,40 T400,20" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" color="var(--primary, #4f46e5)"></path>
                            {/* Data Points */}
                            <circle cx="80" cy="90" fill="currentColor" r="4" stroke="var(--primary, #4f46e5)" strokeWidth="2" className="text-white dark:text-gray-900"></circle>
                            <circle cx="160" cy="80" fill="currentColor" r="4" stroke="var(--primary, #4f46e5)" strokeWidth="2" className="text-white dark:text-gray-900"></circle>
                            <circle cx="240" cy="50" fill="currentColor" r="4" stroke="var(--primary, #4f46e5)" strokeWidth="2" className="text-white dark:text-gray-900"></circle>
                            <circle cx="320" cy="40" fill="currentColor" r="4" stroke="var(--primary, #4f46e5)" strokeWidth="2" className="text-white dark:text-gray-900"></circle>
                            <circle cx="400" cy="20" fill="currentColor" r="5" stroke="var(--primary, #4f46e5)" strokeWidth="2" className="text-white"></circle>
                        </svg>
                    </div>
                    <div className="flex justify-between px-2 pt-4 text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                        <span>Week 1</span>
                        <span>Week 2</span>
                        <span>Week 3</span>
                        <span>Week 4</span>
                    </div>
                </div>

                {/* Weakness Detection */}
                <div className="flex flex-col gap-4">
                    <div className="bg-white/60 dark:bg-gray-900/60 backdrop-blur-xl border border-gray-200 dark:border-white/5 flex-1 rounded-xl p-6 shadow-sm dark:shadow-none">
                        <h3 className="mb-4 text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                            <Radar size={20} className="text-primary" />
                            Weakness Detection
                        </h3>
                        <div className="flex flex-col gap-3">
                            <div className="relative overflow-hidden rounded-lg bg-slate-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-800 border-l-4 border-l-primary p-4 shadow-sm">
                                <div className="flex items-start justify-between">
                                    <div>
                                        <p className="text-sm font-bold text-slate-800 dark:text-slate-200">Filler Words</p>
                                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Detected 'um' frequency &gt; 5% in technical answers.</p>
                                    </div>
                                    <MicOff size={18} className="text-primary" />
                                </div>
                            </div>

                            <div className="relative overflow-hidden rounded-lg bg-slate-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-800 border-l-4 border-l-slate-400 dark:border-l-slate-500 p-4 opacity-80 hover:opacity-100 transition-opacity shadow-sm">
                                <div className="flex items-start justify-between">
                                    <div>
                                        <p className="text-sm font-bold text-slate-800 dark:text-slate-200">Structure</p>
                                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">STAR method missing in behavioral question #3.</p>
                                    </div>
                                    <AlignLeft size={18} className="text-slate-400" />
                                </div>
                            </div>

                            <div className="relative overflow-hidden rounded-lg bg-slate-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-800 border-l-4 border-l-slate-400 dark:border-l-slate-500 p-4 opacity-80 hover:opacity-100 transition-opacity shadow-sm">
                                <div className="flex items-start justify-between">
                                    <div>
                                        <p className="text-sm font-bold text-slate-800 dark:text-slate-200">Pacing</p>
                                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Speaking rate dropped significantly during "Weaknesses".</p>
                                    </div>
                                    <Timer size={18} className="text-slate-400" />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Charts Section Row 2 */}
            <section className="grid grid-cols-1 gap-6 lg:grid-cols-2 relative z-10 w-full pb-8">
                {/* Adaptive Difficulty */}
                <div className="bg-white/60 dark:bg-gray-900/60 backdrop-blur-xl border border-gray-200 dark:border-white/5 rounded-xl p-6 shadow-sm dark:shadow-none">
                    <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
                        <h3 className="text-lg font-bold text-slate-900 dark:text-white">Adaptive Difficulty Journey</h3>
                        <span className="rounded-lg bg-primary/10 border border-primary/20 px-3 py-1.5 text-xs font-bold text-primary dark:text-indigo-400">Current: Level 5</span>
                    </div>

                    <div className="relative h-48 w-full mt-4">
                        {/* Step Graph Simulation */}
                        <div className="absolute bottom-0 left-0 right-0 top-0 flex items-end gap-1">
                            <div className="h-[20%] w-full rounded-t-lg bg-slate-200 hover:bg-slate-300 dark:bg-gray-800 dark:hover:bg-gray-700 transition-colors relative group">
                                <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-800 text-white dark:bg-black px-2 py-1 text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none transition-all">Lvl 1</div>
                            </div>
                            <div className="h-[20%] w-full rounded-t-lg bg-slate-200 hover:bg-slate-300 dark:bg-gray-800 dark:hover:bg-gray-700 transition-colors"></div>
                            <div className="h-[40%] w-full rounded-t-lg bg-slate-200 hover:bg-slate-300 dark:bg-gray-800 dark:hover:bg-gray-700 transition-colors relative group">
                                <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-800 text-white dark:bg-black px-2 py-1 text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none transition-all">Lvl 2</div>
                            </div>
                            <div className="h-[40%] w-full rounded-t-lg bg-slate-200 hover:bg-slate-300 dark:bg-gray-800 dark:hover:bg-gray-700 transition-colors"></div>
                            <div className="h-[60%] w-full rounded-t-lg bg-slate-200 hover:bg-slate-300 dark:bg-gray-800 dark:hover:bg-gray-700 transition-colors relative group">
                                <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-800 text-white dark:bg-black px-2 py-1 text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none transition-all">Lvl 3</div>
                            </div>
                            <div className="h-[60%] w-full rounded-t-lg bg-slate-200 hover:bg-slate-300 dark:bg-gray-800 dark:hover:bg-gray-700 transition-colors"></div>
                            <div className="h-[60%] w-full rounded-t-lg bg-slate-200 hover:bg-slate-300 dark:bg-gray-800 dark:hover:bg-gray-700 transition-colors"></div>

                            <div className="h-[80%] w-full rounded-t-lg bg-primary/40 hover:bg-primary/60 transition-colors relative group shadow-[0_0_15px_rgba(79,70,229,0.1)]">
                                <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-primary px-2 py-1 text-xs text-white font-bold rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none transition-all">Lvl 4</div>
                            </div>
                            <div className="h-[80%] w-full rounded-t-lg bg-primary/40 hover:bg-primary/60 transition-colors shadow-[0_0_15px_rgba(79,70,229,0.1)]"></div>
                            <div className="h-[100%] w-full rounded-t-lg bg-primary hover:bg-primary-dark transition-colors relative group shadow-[0_0_20px_rgba(79,70,229,0.3)]">
                                <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-primary px-2 py-1 text-xs text-white font-bold rounded opacity-100 transition-all">Lvl 5</div>
                            </div>
                        </div>
                    </div>
                    <div className="mt-4 flex justify-between text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                        <span>Session 1</span>
                        <span>Session 10</span>
                    </div>
                </div>

                {/* Skill Growth Comparison */}
                <div className="bg-white/60 dark:bg-gray-900/60 backdrop-blur-xl border border-gray-200 dark:border-white/5 rounded-xl p-6 shadow-sm dark:shadow-none">
                    <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
                        <h3 className="text-lg font-bold text-slate-900 dark:text-white">Skill Breakdown</h3>
                        <div className="flex gap-2">
                            <button className="flex items-center gap-1.5 rounded-full bg-slate-50 border border-gray-200 dark:bg-gray-800/50 dark:border-gray-700 px-3 py-1.5 text-xs text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors font-semibold">
                                <span className="h-2 w-2 rounded-full bg-primary"></span> Technical
                            </button>
                            <button className="flex items-center gap-1.5 rounded-full bg-slate-50 border border-gray-200 dark:bg-gray-800/50 dark:border-gray-700 px-3 py-1.5 text-xs text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-white transition-colors font-semibold opacity-80">
                                <span className="h-2 w-2 rounded-full bg-slate-300 dark:bg-gray-500"></span> Soft Skills
                            </button>
                        </div>
                    </div>

                    <div className="space-y-5">
                        {/* Skill 1 */}
                        <div className="group">
                            <div className="flex justify-between text-sm mb-1.5">
                                <span className="font-semibold text-slate-600 dark:text-slate-300 flex items-center gap-2"><Layers size={14} /> System Design</span>
                                <span className="font-bold text-slate-900 dark:text-white">92%</span>
                            </div>
                            <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-gray-800 inset-shadow">
                                <div className="h-full w-[92%] rounded-full bg-gradient-to-r from-primary/60 to-primary dark:shadow-[0_0_10px_rgba(79,70,229,0.4)]"></div>
                            </div>
                        </div>

                        {/* Skill 2 */}
                        <div className="group">
                            <div className="flex justify-between text-sm mb-1.5">
                                <span className="font-semibold text-slate-600 dark:text-slate-300 flex items-center gap-2"><Code size={14} /> Algorithms</span>
                                <span className="font-bold text-slate-900 dark:text-white">78%</span>
                            </div>
                            <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-gray-800 inset-shadow">
                                <div className="h-full w-[78%] rounded-full bg-gradient-to-r from-primary/60 to-primary dark:shadow-[0_0_10px_rgba(79,70,229,0.4)]"></div>
                            </div>
                        </div>

                        {/* Skill 3 */}
                        <div className="group">
                            <div className="flex justify-between text-sm mb-1.5">
                                <span className="font-semibold text-slate-600 dark:text-slate-300 flex items-center gap-2"><Binary size={14} /> Data Structures</span>
                                <span className="font-bold text-slate-900 dark:text-white">85%</span>
                            </div>
                            <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-gray-800 inset-shadow">
                                <div className="h-full w-[85%] rounded-full bg-gradient-to-r from-primary/60 to-primary dark:shadow-[0_0_10px_rgba(79,70,229,0.4)]"></div>
                            </div>
                        </div>

                        {/* Skill 4 */}
                        <div className="group">
                            <div className="flex justify-between text-sm mb-1.5">
                                <span className="font-semibold text-slate-600 dark:text-slate-300 flex items-center gap-2"><MessageSquare size={14} /> Communication</span>
                                <span className="font-bold text-slate-900 dark:text-white">65%</span>
                            </div>
                            <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-gray-800 inset-shadow">
                                <div className="h-full w-[65%] rounded-full bg-slate-300 dark:bg-slate-600"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    );
}
