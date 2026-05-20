"use client";

import { useMemo } from "react";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
} from "recharts";
import { TrendItem, TrendPoint } from "@braintrain/shared";

interface TrendChartProps {
    data?: TrendPoint[] | TrendItem[];
}

export default function TrendChart({ data = [] }: TrendChartProps) {
    const chartData = useMemo(() => {
        if (data.length === 0) {
            return [];
        }

        const first = data[0] as TrendPoint | TrendItem;
        if ("averageScore" in first) {
            return data as TrendPoint[];
        }

        return (data as TrendItem[]).map((item) => ({
            date: new Date(item.analyzedAt).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
            }),
            averageScore: Math.round(item.overallScore),
        }));
    }, [data]);

    if (chartData.length === 0) {
        return (
            <div className="flex h-[350px] w-full items-center justify-center rounded-3xl border border-dashed border-border bg-muted/20 px-6 text-center">
                <div className="space-y-1">
                    <p className="text-sm font-semibold text-foreground">No trend data yet</p>
                    <p className="text-body-sm text-muted-foreground">
                        Complete and analyze a session to see score movement over time.
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="h-[350px] w-full">
            <ResponsiveContainer width="100%" height="100%">
                <LineChart
                    data={chartData}
                    margin={{
                        top: 5,
                        right: 10,
                        left: 10,
                        bottom: 0,
                    }}
                >
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis
                        dataKey="date"
                        className="text-xs fill-muted-foreground"
                        tickLine={false}
                        axisLine={false}
                    />
                    <YAxis
                        className="text-xs fill-muted-foreground"
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={(value) => `${value}`}
                    />
                    <Tooltip
                        contentStyle={{
                            borderRadius: "12px",
                            border: "1px solid hsl(var(--border))",
                            background: "hsl(var(--card))",
                            color: "hsl(var(--foreground))",
                            boxShadow: "0 12px 32px -20px rgb(0 0 0 / 0.35)",
                        }}
                    />
                    <Line
                        type="monotone"
                        dataKey="averageScore"
                        stroke="hsl(var(--primary))"
                        strokeWidth={2}
                        activeDot={{ r: 8 }}
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
}
