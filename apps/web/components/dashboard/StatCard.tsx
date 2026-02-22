"use client";

import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface StatCardProps {
    label: string;
    value: string | number;
    unit?: string;
    trend: number;
    icon: LucideIcon;
    iconColor: string;
    iconBg: string;
}

export function StatCard({
    label,
    value,
    unit = "",
    trend,
    icon: Icon,
    iconColor,
    iconBg
}: StatCardProps) {
    const isPositive = trend > 0;
    const isNeutral = trend === 0;

    return (
        <div className="bg-white dark:bg-gray-950 p-6 rounded-2xl border border-gray-100 dark:border-gray-800 shadow-sm flex flex-col justify-between gap-4 hover:shadow-premium transition-all group">
            <div className="flex justify-between items-start">
                <div className={cn("p-2.5 rounded-xl transition-colors", iconBg, iconColor)}>
                    <Icon size={22} />
                </div>
                <span className={cn(
                    "flex items-center gap-1 text-[10px] font-bold px-2.5 py-1 rounded-full border",
                    isPositive ? "text-primary bg-primary/5 border-primary/10" :
                        isNeutral ? "text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-900 border-gray-100 dark:border-gray-800" :
                            "text-rose-500 bg-rose-50 dark:bg-rose-500/10 border-rose-100 dark:border-rose-500/20"
                )}>
                    {isPositive ? <TrendingUp size={12} /> : isNeutral ? <Minus size={12} /> : <TrendingDown size={12} />}
                    {isPositive ? "+" : ""}{trend}%
                </span>
            </div>
            <div>
                <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1 uppercase tracking-wider">{label}</p>
                <div className="flex items-end gap-1">
                    <h3 className="text-3xl font-bold text-gray-900 dark:text-gray-100 tracking-tight">{value}</h3>
                    {unit && <span className="text-sm text-gray-400 dark:text-gray-500 font-medium mb-1">{unit}</span>}
                </div>
            </div>
        </div>
    );
}
