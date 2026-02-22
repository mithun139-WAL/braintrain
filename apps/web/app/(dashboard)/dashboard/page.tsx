"use client";

import { StatCard } from "@/components/dashboard/StatCard";
import { PerformanceChart } from "@/components/dashboard/PerformanceChart";
import { RecentSessionsTable } from "@/components/dashboard/RecentSessionsTable";
import {
    Activity,
    Smile,
    MessageSquare,
    Database,
    PlayCircle,
    Brain,
    Lightbulb
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function DashboardPage() {
    return (
        <div className="flex flex-col gap-8 pb-12">
            {/* Welcome Section */}
            <div className="rounded-2xl overflow-hidden bg-gray-900 shadow-xl border border-gray-800 relative group p-8 sm:p-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
                <div className="absolute top-0 right-0 w-96 h-96 bg-primary opacity-10 rounded-full blur-3xl transform translate-x-20 -translate-y-20"></div>

                <div className="flex flex-col gap-3 max-w-2xl relative z-10">
                    <h1 className="text-3xl md:text-4xl font-bold text-white tracking-tight">Welcome back, Alex!</h1>
                    <p className="text-gray-400 text-lg font-light leading-relaxed">
                        Let’s continue sharpening your interview performance. Your confidence score has improved by <span className="text-primary font-bold">12%</span> this week.
                    </p>
                </div>

                <button className="bg-white hover:bg-gray-100 text-gray-900 font-bold py-3.5 px-8 rounded-xl shadow-lg transition-all whitespace-nowrap flex items-center gap-2 transform active:scale-95 relative z-10">
                    <PlayCircle size={20} className="text-primary" />
                    Start New Session
                </button>
            </div>

            {/* Stats Overview */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    label="Overall Score"
                    value={88}
                    unit="/100"
                    trend={5}
                    icon={Activity}
                    iconColor="text-primary"
                    iconBg="bg-primary/10"
                />
                <StatCard
                    label="Confidence"
                    value={92}
                    unit="%"
                    trend={2}
                    icon={Smile}
                    iconColor="text-blue-600"
                    iconBg="bg-blue-50"
                />
                <StatCard
                    label="Communication"
                    value={85}
                    unit="%"
                    trend={0}
                    icon={MessageSquare}
                    iconColor="text-purple-600"
                    iconBg="bg-purple-50"
                />
                <StatCard
                    label="Technical Depth"
                    value={78}
                    unit="%"
                    trend={-3}
                    icon={Database}
                    iconColor="text-amber-600"
                    iconBg="bg-amber-50"
                />
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Chart Section */}
                <div className="lg:col-span-2">
                    <PerformanceChart />
                </div>

                {/* AI Coaching Tips */}
                <div className="lg:col-span-1 bg-white rounded-2xl border border-gray-100 shadow-sm p-6 flex flex-col">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                            <Lightbulb size={20} className="text-primary" />
                            AI Coaching Tips
                        </h3>
                        <button className="text-xs font-bold text-primary hover:text-primary-dark bg-primary/5 px-3 py-1.5 rounded-lg transition-colors">
                            View All
                        </button>
                    </div>

                    <div className="flex flex-col gap-4">
                        {[
                            { title: "Slow down your pace", desc: "You tend to speak 15% faster during technical explanations. Try pausing more often.", color: "bg-amber-400" },
                            { title: "Great STAR structure", desc: "Your last behavioral answer perfectly followed the Situation-Task-Action-Result format.", color: "bg-primary" },
                            { title: "Expand on \"Why\"", desc: "In system design, explicitly state trade-offs before making a technology choice.", color: "bg-blue-500" },
                        ].map((tip, idx) => (
                            <div key={idx} className="p-4 bg-gray-50/50 rounded-xl border border-gray-50 hover:border-primary/20 transition-all group cursor-pointer">
                                <div className="flex items-start gap-4">
                                    <div className={cn("mt-1.5 size-2 rounded-full flex-shrink-0", tip.color)} />
                                    <div>
                                        <h4 className="text-sm font-bold text-gray-900 mb-1 group-hover:text-primary transition-colors">{tip.title}</h4>
                                        <p className="text-xs text-gray-500 leading-relaxed font-medium">{tip.desc}</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>

                    <button className="w-full mt-6 py-2.5 border border-dashed border-gray-200 rounded-xl text-xs font-bold text-gray-400 hover:text-gray-600 hover:border-gray-300 transition-all uppercase tracking-wider">
                        Generate New Insights
                    </button>
                </div>
            </div>

            {/* Sessions Table */}
            <RecentSessionsTable />
        </div>
    );
}
