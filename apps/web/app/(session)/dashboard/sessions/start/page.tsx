"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
    ChevronLeft,
    Brain,
    MessageSquare,
    Code,
    Shuffle,
    CheckCircle2,
    SlidersHorizontal,
    ChevronDown,
    BarChart2,
    Timer,
    ArrowRight
} from "lucide-react";
import { cn } from "@/lib/utils";

type InterviewType = "behavioral" | "technical" | "mixed";
type Difficulty = "beginner" | "intermediate" | "advanced";

export default function StartSessionPage() {
    const [interviewType, setInterviewType] = useState<InterviewType>("behavioral");
    const [difficulty, setDifficulty] = useState<Difficulty>("intermediate");
    const [questionCount, setQuestionCount] = useState(5);
    const [adaptiveMode, setAdaptiveMode] = useState(true);

    const interviewTypes = [
        {
            id: "behavioral",
            title: "Behavioral",
            description: "Soft skills, leadership, and culture fit questions.",
            icon: MessageSquare,
        },
        {
            id: "technical",
            title: "Technical",
            description: "Coding challenges, system design, and architecture.",
            icon: Code,
        },
        {
            id: "mixed",
            title: "Mixed",
            description: "A balanced combination of technical and behavioral.",
            icon: Shuffle,
        },
    ];

    const getEstimatedDuration = () => {
        // Assume roughly 5 mins per question
        return questionCount * 5;
    };

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-gray-950 flex flex-col text-slate-900 dark:text-gray-100 font-display transition-colors">
            {/* Header */}
            <header className="flex items-center justify-between whitespace-nowrap border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 px-6 py-4 sticky top-0 z-50 transition-colors">
                <div className="flex items-center gap-4">
                    <Link href="/dashboard" className="flex items-center justify-center text-slate-500 hover:text-slate-800 dark:text-gray-400 dark:hover:text-gray-100 transition-colors">
                        <ChevronLeft size={24} />
                    </Link>
                    <div className="h-6 w-px bg-gray-200 dark:bg-gray-800 mx-2 transition-colors"></div>
                    <div className="flex items-center gap-3 text-slate-900 dark:text-white">
                        <div className="text-primary">
                            <Brain size={28} />
                        </div>
                        <h2 className="text-xl font-bold tracking-tight">BrainTrain</h2>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    <span className="text-sm font-medium text-slate-600 dark:text-gray-400 hidden sm:block">Practice Mode</span>
                    <div className="h-10 w-10 flex items-center justify-center rounded-full bg-primary/10 text-primary font-bold ring-2 ring-gray-100 dark:ring-gray-800">
                        JD
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-1 w-full max-w-7xl mx-auto p-4 md:p-8 lg:p-12">
                <div className="flex flex-col lg:flex-row gap-8">
                    {/* Left Column: Configuration */}
                    <div className="flex-1 flex flex-col gap-8">
                        <div className="flex flex-col gap-2">
                            <h1 className="text-3xl md:text-4xl font-black text-slate-900 dark:text-white tracking-tight">Start Practice Session</h1>
                            <p className="text-slate-500 dark:text-gray-400 text-lg">Configure your AI interview parameters to focus your training.</p>
                        </div>

                        {/* Section A: Interview Type */}
                        <section className="flex flex-col gap-4">
                            <div className="flex items-center gap-2">
                                <span className="flex items-center justify-center size-6 rounded-full bg-slate-200 dark:bg-gray-800 text-slate-600 dark:text-gray-300 text-xs font-bold transition-colors">1</span>
                                <h3 className="text-lg font-bold text-slate-800 dark:text-gray-200">Select Interview Type</h3>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                {interviewTypes.map(type => (
                                    <label key={type.id} className="cursor-pointer group relative">
                                        <input
                                            type="radio"
                                            name="interview_type"
                                            value={type.id}
                                            checked={interviewType === type.id}
                                            onChange={() => setInterviewType(type.id as InterviewType)}
                                            className="peer sr-only"
                                        />
                                        <div className={cn(
                                            "h-full flex flex-col gap-4 rounded-xl border-2 bg-white dark:bg-gray-900 p-6 shadow-sm transition-all",
                                            interviewType === type.id
                                                ? "border-primary bg-primary/5 shadow-primary/10 dark:shadow-none"
                                                : "border-transparent ring-1 ring-slate-200 dark:ring-gray-800 hover:ring-slate-300 dark:hover:ring-gray-700"
                                        )}>
                                            <div className={cn(
                                                "absolute top-4 right-4 text-primary transition-opacity",
                                                interviewType === type.id ? "opacity-100" : "opacity-0"
                                            )}>
                                                <CheckCircle2 className="fill-current text-primary" size={20} />
                                            </div>
                                            <div className={cn(
                                                "size-12 rounded-lg flex items-center justify-center transition-colors",
                                                interviewType === type.id
                                                    ? "bg-primary/10 text-primary"
                                                    : "bg-slate-100 dark:bg-gray-800 text-slate-600 dark:text-gray-400 group-hover:bg-slate-200 dark:group-hover:bg-gray-700"
                                            )}>
                                                <type.icon size={24} />
                                            </div>
                                            <div>
                                                <h4 className="text-lg font-bold text-slate-900 dark:text-white">{type.title}</h4>
                                                <p className="text-sm text-slate-500 dark:text-gray-400 mt-1">{type.description}</p>
                                            </div>
                                        </div>
                                    </label>
                                ))}
                            </div>
                        </section>

                        {/* Section B: Difficulty */}
                        <section className="flex flex-col gap-4">
                            <div className="flex items-center gap-2">
                                <span className="flex items-center justify-center size-6 rounded-full bg-slate-200 dark:bg-gray-800 text-slate-600 dark:text-gray-300 text-xs font-bold transition-colors">2</span>
                                <h3 className="text-lg font-bold text-slate-800 dark:text-gray-200">Select Difficulty</h3>
                            </div>
                            <div className="bg-white dark:bg-gray-900 p-1.5 rounded-xl ring-1 ring-slate-200 dark:ring-gray-800 flex transition-colors shadow-sm dark:shadow-none">
                                {["beginner", "intermediate", "advanced"].map(lvl => (
                                    <label key={lvl} className="flex-1 relative cursor-pointer">
                                        <input
                                            type="radio"
                                            name="difficulty"
                                            value={lvl}
                                            checked={difficulty === lvl}
                                            onChange={() => setDifficulty(lvl as Difficulty)}
                                            className="peer sr-only"
                                        />
                                        <div className={cn(
                                            "capitalize h-10 flex items-center justify-center rounded-lg text-sm font-semibold transition-all",
                                            difficulty === lvl
                                                ? "bg-primary/10 text-primary shadow-sm"
                                                : "text-slate-500 dark:text-gray-400 hover:bg-slate-50 dark:hover:bg-gray-800"
                                        )}>
                                            {lvl}
                                        </div>
                                    </label>
                                ))}
                            </div>
                        </section>

                        {/* Section C: Advanced Settings */}
                        <section className="flex flex-col gap-4">
                            <details className="group bg-white dark:bg-gray-900 rounded-xl ring-1 ring-slate-200 dark:ring-gray-800 shadow-sm dark:shadow-none overflow-hidden transition-colors">
                                <summary className="flex cursor-pointer items-center justify-between px-6 py-4 hover:bg-slate-50 dark:hover:bg-gray-800/50 transition-colors">
                                    <div className="flex items-center gap-3">
                                        <div className="size-8 rounded-full bg-slate-100 dark:bg-gray-800 flex items-center justify-center text-slate-500 dark:text-gray-400 transition-colors">
                                            <SlidersHorizontal size={18} />
                                        </div>
                                        <span className="font-bold text-slate-800 dark:text-gray-200">Advanced Settings</span>
                                    </div>
                                    <ChevronDown size={20} className="text-slate-400 dark:text-gray-500 group-open:rotate-180 transition-transform" />
                                </summary>
                                <div className="px-6 pb-6 pt-2 flex flex-col gap-6 border-t border-slate-100 dark:border-gray-800">
                                    {/* Question Count Slider */}
                                    <div className="flex flex-col gap-3">
                                        <div className="flex justify-between items-center">
                                            <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">Number of Questions</label>
                                            <span className="text-sm font-bold text-primary bg-primary/10 px-2 py-0.5 rounded">{questionCount} Questions</span>
                                        </div>
                                        <input
                                            type="range"
                                            min="1"
                                            max="10"
                                            value={questionCount}
                                            onChange={(e) => setQuestionCount(parseInt(e.target.value))}
                                            className="w-full h-2 bg-slate-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary"
                                        />
                                        <div className="flex justify-between text-xs text-slate-400 dark:text-gray-500 font-medium">
                                            <span>1</span>
                                            <span>10</span>
                                        </div>
                                    </div>

                                    {/* Adaptive Mode Toggle */}
                                    <div className="flex items-center justify-between">
                                        <div className="flex flex-col gap-0.5">
                                            <span className="text-sm font-semibold text-slate-700 dark:text-gray-300">Adaptive Difficulty</span>
                                            <span className="text-xs text-slate-500 dark:text-gray-400">AI adjusts difficulty based on your answers</span>
                                        </div>
                                        <label className="relative inline-flex items-center cursor-pointer">
                                            <input
                                                type="checkbox"
                                                checked={adaptiveMode}
                                                onChange={(e) => setAdaptiveMode(e.target.checked)}
                                                className="sr-only peer"
                                            />
                                            <div className="w-11 h-6 bg-slate-200 dark:bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary transition-colors"></div>
                                        </label>
                                    </div>
                                </div>
                            </details>
                        </section>
                    </div>

                    {/* Right Column: Preview Panel */}
                    <aside className="w-full lg:w-[380px] shrink-0">
                        <div className="sticky top-28 flex flex-col gap-4">
                            <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm dark:shadow-none ring-1 ring-slate-200 dark:ring-gray-800 p-6 flex flex-col gap-6 transition-colors">
                                <h3 className="text-sm font-bold text-slate-400 dark:text-gray-500 uppercase tracking-wider">Session Preview</h3>

                                <div className="flex flex-col gap-4">
                                    <div className="flex items-start gap-3">
                                        <div className="mt-1 size-8 rounded bg-primary/10 flex items-center justify-center text-primary shrink-0">
                                            <MessageSquare size={18} />
                                        </div>
                                        <div>
                                            <p className="text-xs text-slate-500 dark:text-gray-400 font-medium">Type</p>
                                            <p className="text-base font-bold text-slate-900 dark:text-white capitalize">{interviewType} Interview</p>
                                        </div>
                                    </div>

                                    <div className="h-px w-full bg-slate-100 dark:bg-gray-800 transition-colors"></div>

                                    <div className="flex items-start gap-3">
                                        <div className="mt-1 size-8 rounded bg-primary/10 flex items-center justify-center text-primary shrink-0">
                                            <BarChart2 size={18} />
                                        </div>
                                        <div>
                                            <p className="text-xs text-slate-500 dark:text-gray-400 font-medium">Difficulty</p>
                                            <p className="text-base font-bold text-slate-900 dark:text-white capitalize">{difficulty}</p>
                                        </div>
                                    </div>

                                    <div className="h-px w-full bg-slate-100 dark:bg-gray-800 transition-colors"></div>

                                    <div className="flex items-start gap-3">
                                        <div className="mt-1 size-8 rounded bg-primary/10 flex items-center justify-center text-primary shrink-0">
                                            <Timer size={18} />
                                        </div>
                                        <div>
                                            <p className="text-xs text-slate-500 dark:text-gray-400 font-medium">Est. Duration</p>
                                            <p className="text-base font-bold text-slate-900 dark:text-white">~{getEstimatedDuration()} Minutes</p>
                                        </div>
                                    </div>
                                </div>

                                <div className="bg-slate-50 dark:bg-gray-800/50 rounded-lg p-3 text-xs text-slate-500 dark:text-gray-400 leading-relaxed border border-slate-100 dark:border-gray-800 transition-colors">
                                    <span className="font-bold text-slate-700 dark:text-gray-300">Note:</span> This session will focus on {interviewType === 'behavioral' ? 'STAR method responses and communication clarity.' : interviewType === 'technical' ? 'problem solving, optimal solutions, and code quality.' : 'both behavioral responses and technical capabilities.'}
                                </div>

                                <Link href="/dashboard/sessions/active" className="w-full">
                                    <button className="w-full h-12 bg-primary hover:bg-primary-dark text-white font-bold rounded-xl shadow-md shadow-primary/20 transition-all active:scale-[0.98] flex items-center justify-center gap-2 group">
                                        <span>Start Session</span>
                                        <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                                    </button>
                                </Link>
                            </div>

                            <div className="text-center">
                                <p className="text-xs text-slate-400 dark:text-gray-500">Need help? <a className="text-primary hover:underline font-medium" href="#">View Guide</a></p>
                            </div>
                        </div>
                    </aside>
                </div>
            </main>
        </div>
    );
}
