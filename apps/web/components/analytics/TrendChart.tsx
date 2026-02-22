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
import { TrendPoint } from "@braintrain/shared";

interface TrendChartProps {
    data?: TrendPoint[];
}

export default function TrendChart({ data = [] }: TrendChartProps) {
    const chartData = useMemo(() => {
        if (data.length === 0) {
            return [
                { date: "Mon", averageScore: 65 },
                { date: "Tue", averageScore: 72 },
                { date: "Wed", averageScore: 68 },
                { date: "Thu", averageScore: 85 },
                { date: "Fri", averageScore: 82 },
                { date: "Sat", averageScore: 90 },
                { date: "Sun", averageScore: 95 },
            ]
        }
        return data;
    }, [data])

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
                        contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
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
