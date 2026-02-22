// Server Component
import { Suspense } from "react";
// import PerformanceSummary from "@/components/report/PerformanceSummary"
// import ImprovementList from "@/components/report/ImprovementList"
// import ScoreRadar from "@/components/report/ScoreRadar.client"

export default async function SessionReportPage({ params }: { params: { id: string } }) {
    // Server-side fetch example
    // const reportData = await evaluationApi.getEvaluationForSession(params.id)

    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Session Report</h1>
                <p className="text-muted-foreground pt-2">Comprehensive analysis of your performance.</p>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                <div className="md:col-span-2 space-y-4">
                    {/* Server Components */}
                    {/* <PerformanceSummary data={reportData} /> */}
                    {/* <ImprovementList items={reportData.identifiedWeaknesses} /> */}
                    <div className="h-64 border rounded-xl flex items-center justify-center bg-card text-muted-foreground p-4 text-sm text-center">
                        Server Component: Performance Summary Placeholder
                    </div>
                    <div className="h-64 border rounded-xl flex items-center justify-center bg-card text-muted-foreground p-4 text-sm text-center">
                        Server Component: Improvement List Placeholder
                    </div>
                </div>

                <div>
                    {/* Client Component (e.g. Recharts requires 'use client') */}
                    {/* <ScoreRadar score={reportData.score} /> */}
                    <div className="h-[528px] border rounded-xl flex items-center justify-center bg-card text-muted-foreground p-4 text-sm text-center">
                        Client Component: Score Radar Chart Placeholder
                    </div>
                </div>
            </div>
        </div>
    );
}
