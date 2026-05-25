"use client";

import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface StatCardProps {
    label:       string;
    value:       string | number;
    unit?:       string;
    trend:       number;
    icon:        LucideIcon;
    iconColor:   string;
    iconBg:      string;
    /** Tailwind bg-* class for the left accent bar, e.g. "bg-primary" */
    accentColor?: string;
}

export function StatCard({
    label,
    value,
    unit       = "",
    trend,
    icon: Icon,
    iconColor,
    iconBg,
    accentColor = "bg-primary",
}: StatCardProps) {
    const isPositive = trend > 0;

    return (
        <div className="bg-card rounded-xl border border-border p-5 flex flex-col justify-between">
            <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                {label}
            </span>
            <div className="flex items-baseline gap-1 mt-2">
                <span className="text-2xl font-bold text-foreground tracking-tight tabular">
                    {value}
                </span>
                {unit && (
                    <span className="text-xs text-muted-foreground font-medium">
                        {unit}
                    </span>
                )}
            </div>
            {trend !== 0 && (
                <div className={cn("text-[10px] font-medium mt-2", isPositive ? "text-emerald" : "text-ruby")}>
                    {isPositive ? "▲" : "▼"} {Math.abs(trend)}% from baseline
                </div>
            )}
        </div>
    );
}
