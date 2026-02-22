import React from "react";
import { User } from "@braintrain/shared";

interface SubscriptionTabProps {
    profile?: User;
    isLoading: boolean;
}

export function SubscriptionTab({ profile, isLoading }: SubscriptionTabProps) {
    const isPro = (profile?.planType || "FREE").toUpperCase() === "PRO";

    if (isLoading) {
        return (
            <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 p-6 animate-pulse min-h-[150px]">
                <div className="h-4 w-1/3 bg-slate-200 dark:bg-gray-800 rounded mb-4"></div>
                <div className="h-2 w-full bg-slate-100 dark:bg-gray-800 rounded-full mb-2"></div>
                <div className="h-2 w-2/3 bg-slate-100 dark:bg-gray-800 rounded-full"></div>
            </div>
        );
    }

    const sessionsUsed = profile?.monthlySessionCount || 0;
    const sessionsLimit = isPro ? 20 : 3;
    const sessionsPercent = Math.min(100, Math.round((sessionsUsed / sessionsLimit) * 100));

    const creditsAvailable = profile?.monthlyEvaluationCredits || 0;
    const creditsLimit = isPro ? 100 : 0;
    const creditsUsed = isPro ? creditsLimit - creditsAvailable : 0;
    const creditsPercent = isPro ? Math.min(100, Math.round((creditsUsed / creditsLimit) * 100)) : 0;

    let resetDate = "-";
    if (profile?.usagePeriodStart) {
        const date = new Date(profile.usagePeriodStart);
        date.setMonth(date.getMonth() + 1);
        resetDate = date.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
    }

    if (!isPro) {
        return (
            <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm border border-gray-100 dark:border-neutral-700 p-6 transition-colors">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">Monthly Usage</h3>
                    <span className="text-[10px] font-bold text-slate-500 dark:text-neutral-400">Resets monthly</span>
                </div>
                <div className="space-y-4">
                    <div>
                        <div className="flex justify-between text-xs mb-2">
                            <span className="text-slate-600 dark:text-neutral-400 font-medium">Sessions Used</span>
                            <span className="font-bold text-slate-900 dark:text-white">{sessionsUsed} / {sessionsLimit}</span>
                        </div>
                        <div className="h-2 w-full bg-gray-100 dark:bg-neutral-700 rounded-full overflow-hidden">
                            <div className="h-full bg-slate-800 dark:bg-primary rounded-full transition-all duration-500" style={{ width: `${sessionsPercent}%` }}></div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm border border-neutral-200 dark:border-neutral-700 p-6 transition-colors">
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-bold text-neutral-900 dark:text-white flex items-center gap-2 tracking-tight">
                    <span className="material-symbols-outlined text-primary">pie_chart</span>
                    Your Plan & Usage
                </h3>
                <span className="text-xs font-bold text-primary bg-primary/10 px-3 py-1 rounded-full uppercase tracking-wider">Pro Plan Active</span>
            </div>
            <div className="space-y-6">
                {/* Usage Item 1 */}
                <div>
                    <div className="flex justify-between items-end mb-2">
                        <label className="text-sm font-bold text-neutral-700 dark:text-neutral-300">Live Interview Sessions</label>
                        <span className="text-sm font-bold text-neutral-900 dark:text-white">{sessionsUsed} <span className="text-neutral-400 font-normal">/ {sessionsLimit}</span></span>
                    </div>
                    <div className="w-full bg-neutral-100 dark:bg-neutral-700 rounded-full h-2.5 overflow-hidden">
                        <div className="bg-primary h-2.5 rounded-full transition-all duration-500" style={{ width: `${sessionsPercent}%` }}></div>
                    </div>
                </div>
                {/* Usage Item 2 */}
                <div>
                    <div className="flex justify-between items-end mb-2">
                        <label className="text-sm font-bold text-neutral-700 dark:text-neutral-300">AI Evaluation Credits Used</label>
                        <span className="text-sm font-bold text-neutral-900 dark:text-white">{creditsUsed} <span className="text-neutral-400 font-normal">/ {creditsLimit}</span></span>
                    </div>
                    <div className="w-full bg-neutral-100 dark:bg-neutral-700 rounded-full h-2.5 overflow-hidden">
                        <div className="bg-primary h-2.5 rounded-full transition-all duration-500" style={{ width: `${creditsPercent}%` }}></div>
                    </div>
                </div>
            </div>
            <div className="mt-6 pt-4 border-t border-neutral-100 dark:border-neutral-700 flex items-center gap-2 text-xs text-neutral-500 font-medium">
                <span className="material-symbols-outlined text-[18px]">event_repeat</span>
                <span>Monthly limits reset on <span className="font-bold text-neutral-900 dark:text-white">{resetDate}</span></span>
            </div>
        </div>
    );
}
