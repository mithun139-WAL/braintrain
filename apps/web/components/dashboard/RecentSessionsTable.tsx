"use client";

import {
    Server,
    Users,
    Terminal,
    Mic,
    ArrowRight,
    Filter,
    Download,
    ChevronDown
} from "lucide-react";
import { cn } from "@/lib/utils";

const sessions = [
    {
        date: "Oct 26, 2023",
        type: "System Design",
        icon: Server,
        difficulty: "Hard",
        difficultyColor: "text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-500/10 border-rose-100 dark:border-rose-500/20",
        score: 92,
        duration: "45m",
    },
    {
        date: "Oct 25, 2023",
        type: "Behavioral",
        icon: Users,
        difficulty: "Medium",
        difficultyColor: "text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-500/10 border-amber-100 dark:border-amber-500/20",
        score: 85,
        duration: "30m",
    },
    {
        date: "Oct 24, 2023",
        type: "Algorithms",
        icon: Terminal,
        difficulty: "Hard",
        difficultyColor: "text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-500/10 border-rose-100 dark:border-rose-500/20",
        score: 76,
        duration: "60m",
    },
    {
        date: "Oct 22, 2023",
        type: "Mock Interview",
        icon: Mic,
        difficulty: "Easy",
        difficultyColor: "text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-500/10 border-emerald-100 dark:border-emerald-500/20",
        score: 89,
        duration: "25m",
    },
];

export function RecentSessionsTable() {
    return (
        <div className="bg-white dark:bg-gray-950 rounded-2xl border border-gray-100 dark:border-gray-800 shadow-sm flex flex-col">
            <div className="p-6 border-b border-gray-50 dark:border-gray-800/50 flex items-center justify-between">
                <div>
                    <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">Recent Practice Sessions</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">Review your past interviews and detailed feedback reports.</p>
                </div>
                <div className="flex gap-3">
                    <div className="relative">
                        <Filter size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-gray-500" />
                        <select className="pl-9 pr-8 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl text-xs text-gray-600 dark:text-gray-300 focus:ring-primary focus:border-primary appearance-none outline-none">
                            <option>All Types</option>
                            <option>System Design</option>
                            <option>Behavioral</option>
                            <option>Coding</option>
                        </select>
                        <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-gray-500 pointer-events-none" />
                    </div>
                    <button className="p-2.5 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 border border-gray-100 dark:border-gray-800 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors">
                        <Download size={18} />
                    </button>
                </div>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="bg-gray-50/50 dark:bg-gray-900/50 text-gray-500 dark:text-gray-400 text-[10px] uppercase tracking-wider font-bold border-b border-gray-50 dark:border-gray-800/50">
                            <th className="px-6 py-4">Date</th>
                            <th className="px-6 py-4">Type</th>
                            <th className="px-6 py-4">Difficulty</th>
                            <th className="px-6 py-4">Score</th>
                            <th className="px-6 py-4">Duration</th>
                            <th className="px-6 py-4 text-right">Action</th>
                        </tr>
                    </thead>
                    <tbody className="text-sm text-gray-600 dark:text-gray-300 divide-y divide-gray-50 dark:divide-gray-800/50">
                        {sessions.map((session, idx) => (
                            <tr key={idx} className="hover:bg-gray-50/50 dark:hover:bg-gray-900/50 transition-colors group">
                                <td className="px-6 py-4 text-gray-900 dark:text-gray-100 font-semibold">{session.date}</td>
                                <td className="px-6 py-4">
                                    <div className="flex items-center gap-2">
                                        <session.icon size={16} className="text-gray-400 dark:text-gray-500" />
                                        {session.type}
                                    </div>
                                </td>
                                <td className="px-6 py-4">
                                    <span className={cn(
                                        "px-2.5 py-1 rounded-lg text-[10px] font-bold border whitespace-nowrap",
                                        session.difficultyColor
                                    )}>
                                        {session.difficulty}
                                    </span>
                                </td>
                                <td className="px-6 py-4">
                                    <div className="flex items-center gap-3">
                                        <div className="w-16 h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                                            <div
                                                className={cn(
                                                    "h-full rounded-full transition-all",
                                                    session.score >= 80 ? "bg-primary" : "bg-gray-400 dark:bg-gray-600"
                                                )}
                                                style={{ width: `${session.score}%` }}
                                            />
                                        </div>
                                        <span className="font-bold text-gray-900 dark:text-gray-100">{session.score}</span>
                                    </div>
                                </td>
                                <td className="px-6 py-4 font-medium text-gray-500 dark:text-gray-400">{session.duration}</td>
                                <td className="px-6 py-4 text-right">
                                    <button className="text-primary hover:text-primary-dark font-bold text-xs inline-flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all transform group-hover:translate-x-0 translate-x-1">
                                        View Report
                                        <ArrowRight size={14} />
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <div className="p-4 border-t border-gray-50 dark:border-gray-800/50 flex justify-center bg-gray-50/30 dark:bg-gray-900/30">
                <button className="text-xs font-bold text-gray-500 dark:text-gray-400 hover:text-primary transition-colors flex items-center gap-1 uppercase tracking-wider">
                    View all history
                    <ChevronDown size={14} />
                </button>
            </div>
        </div>
    );
}
