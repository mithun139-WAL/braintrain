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
    const isNeutral  = trend === 0;

    return (
        <div className="relative bg-card rounded-2xl border border-border shadow-card hover:shadow-card-hover transition-shadow duration-200 overflow-hidden group">
            {/* Left accent bar */}
            <div className={cn("absolute left-0 top-0 bottom-0 w-[3px]", accentColor)} />

            <div className="p-5 pl-6">
                {/* Top row — icon + trend */}
                <div className="flex items-start justify-between mb-4">
                    <div className={cn("flex items-center justify-center size-9 rounded-xl", iconBg, iconColor)}>
                        <Icon size={18} />
                    </div>
                    <span className={cn(
                        "inline-flex items-center gap-1 text-[10px] font-bold px-2 py-1 rounded-full",
                        isPositive
                            ? "text-emerald bg-emerald/10"
                            : isNeutral
                            ? "text-muted-foreground bg-muted"
                            : "text-ruby bg-ruby/10"
                    )}>
                        {isPositive
                            ? <TrendingUp  size={10} />
                            : isNeutral
                            ? <Minus       size={10} />
                            : <TrendingDown size={10} />
                        }
                        {isPositive ? "+" : ""}{trend}%
                    </span>
                </div>

                {/* Metric */}
                <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-widest mb-1.5">
                    {label}
                </p>
                <div className="flex items-baseline gap-1">
                    <span className="text-[2rem] font-black text-foreground leading-none tabular tracking-tight">
                        {value}
                    </span>
                    {unit && (
                        <span className="text-sm text-muted-foreground font-medium">
                            {unit}
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
}
