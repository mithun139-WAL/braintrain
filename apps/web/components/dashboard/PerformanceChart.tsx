"use client";

import { useState } from "react";
import { TrendItem } from "@braintrain/shared";
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
} from "recharts";

const PERIODS = ["Week", "Month", "Year"] as const;

function formatTrendDate(iso: string) {
    return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function PerformanceChart({ trend }: { trend?: TrendItem[] }) {
    const [activePeriod, setActivePeriod] = useState<typeof PERIODS[number]>("Month");
    const chartData =
        trend && trend.length > 0
            ? trend.map((item) => ({
                  name: formatTrendDate(item.analyzedAt),
                  score: Math.round(item.overallScore),
              }))
            : [];

    if (chartData.length === 0) {
        return (
            <div className="flex h-full min-h-[320px] flex-col rounded-2xl border border-border bg-card p-6 shadow-card">
                <div>
                    <h3 className="text-base font-bold text-foreground">Score Progression</h3>
                    <p className="mt-0.5 text-xs text-muted-foreground">Performance trajectory appears after your first analyzed session.</p>
                </div>
                <div className="flex flex-1 items-center justify-center rounded-3xl border border-dashed border-border bg-muted/20 px-6 text-center">
                    <div className="space-y-1">
                        <p className="text-sm font-semibold text-foreground">No score progression yet</p>
                        <p className="text-body-sm text-muted-foreground">
                            Complete a session to replace this empty state with real performance movement.
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-card rounded-2xl border border-border shadow-card flex flex-col h-full">
            {/* Header */}
            <div className="flex items-start justify-between px-6 pt-6 pb-4">
                <div>
                    <h3 className="text-base font-bold text-foreground">Score Progression</h3>
                    <p className="text-xs text-muted-foreground mt-0.5">
                        Performance trajectory · last 30 days
                    </p>
                </div>
                <div className="flex bg-muted rounded-lg p-0.5 gap-0.5">
                    {PERIODS.map((p) => (
                        <button
                            key={p}
                            onClick={() => setActivePeriod(p)}
                            className={
                                p === activePeriod
                                    ? "px-3 py-1.5 text-xs font-semibold rounded-md bg-card text-foreground shadow-card"
                                    : "px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors rounded-md"
                            }
                        >
                            {p}
                        </button>
                    ))}
                </div>
            </div>

            {/* Chart */}
            <div className="flex-1 w-full min-h-[280px] px-2 pb-5">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData} margin={{ top: 8, right: 8, left: -24, bottom: 0 }}>
                        <defs>
                            <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%"  stopColor="#6366f1" stopOpacity={0.15} />
                                <stop offset="95%" stopColor="#6366f1" stopOpacity={0}    />
                            </linearGradient>
                        </defs>
                        <CartesianGrid
                            strokeDasharray="3 3"
                            vertical={false}
                            stroke="hsl(var(--border))"
                            strokeOpacity={0.6}
                        />
                        <XAxis
                            dataKey="name"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))", fontWeight: 500 }}
                            dy={8}
                        />
                        <YAxis
                            axisLine={false}
                            tickLine={false}
                            tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))", fontWeight: 500 }}
                            domain={[0, 100]}
                        />
                        <Tooltip
                            contentStyle={{
                                borderRadius:    "10px",
                                border:          "1px solid hsl(var(--border))",
                                background:      "hsl(var(--card))",
                                color:           "hsl(var(--foreground))",
                                boxShadow:       "0 8px 24px rgba(0,0,0,0.12)",
                                fontSize:        "12px",
                                fontWeight:      "600",
                            }}
                            cursor={{ stroke: "#6366f1", strokeWidth: 1, strokeDasharray: "4 2" }}
                        />
                        <Area
                            type="monotone"
                            dataKey="score"
                            stroke="#6366f1"
                            strokeWidth={2.5}
                            fillOpacity={1}
                            fill="url(#scoreGradient)"
                            dot={{ fill: "hsl(var(--card))", stroke: "#6366f1", strokeWidth: 2.5, r: 4 }}
                            activeDot={{ r: 6, fill: "#6366f1", strokeWidth: 0 }}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
