"use client";

import { StatCard } from "@/components/dashboard/StatCard";
import TrendChart from "@/components/analytics/TrendChart";
import {
    Target,
    BarChart3,
    TrendingUp,
    LayoutDashboard,
    AlertCircle
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function AnalyticsPage() {
    return (
        <div className="flex flex-col gap-8 w-full pb-12">
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold text-gray-900 tracking-tight">Performance Analytics</h2>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    label="Average Score"
                    value="82"
                    unit="%"
                    trend={4}
                    icon={Target}
                    iconColor="text-primary"
                    iconBg="bg-primary/10"
                />
                <StatCard
                    label="Total Sessions"
                    value="24"
                    unit="total"
                    trend={12}
                    icon={LayoutDashboard}
                    iconColor="text-blue-600"
                    iconBg="bg-blue-50"
                />
                <StatCard
                    label="Improvement"
                    value="+15"
                    unit="pts"
                    trend={8}
                    icon={TrendingUp}
                    iconColor="text-emerald-600"
                    iconBg="bg-emerald-50"
                />
                <StatCard
                    label="Weak Points"
                    value="3"
                    unit="areas"
                    trend={-2}
                    icon={AlertCircle}
                    iconColor="text-rose-600"
                    iconBg="bg-rose-50"
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 bg-white rounded-2xl border border-gray-100 shadow-sm p-6 flex flex-col">
                    <div className="p-0 pb-6">
                        <h3 className="text-lg font-bold text-gray-900 leading-none">Performance Trends</h3>
                        <p className="text-sm text-gray-500 mt-1">Detailed score history across all interview types</p>
                    </div>
                    <div className="flex-1 w-full min-h-[350px]">
                        <TrendChart />
                    </div>
                </div>

                <div className="lg:col-span-1 bg-white rounded-2xl border border-gray-100 shadow-sm p-6 flex flex-col">
                    <div className="p-0 pb-6">
                        <h3 className="text-lg font-bold text-gray-900 leading-none tracking-tight">Top Weaknesses</h3>
                        <p className="text-sm text-gray-500 mt-1">Areas identified for improvement</p>
                    </div>
                    <div className="space-y-4">
                        {[
                            { title: "System Design (Scalability)", desc: "Mentioned in 4 recent sessions", color: "bg-rose-500" },
                            { title: "Behavioral (Conflict)", desc: "Mentioned in 2 recent sessions", color: "bg-amber-500" },
                            { title: "Technical Depth", desc: "Need more focus on edge cases", color: "bg-indigo-500" },
                        ].map((weakness, idx) => (
                            <div key={idx} className="flex items-center p-3 rounded-xl hover:bg-gray-50 transition-colors border border-transparent hover:border-gray-100">
                                <div className={cn("size-2 rounded-full mr-4", weakness.color)} />
                                <div className="space-y-1">
                                    <p className="text-sm font-bold text-gray-900 leading-none">{weakness.title}</p>
                                    <p className="text-xs text-muted-foreground">{weakness.desc}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
