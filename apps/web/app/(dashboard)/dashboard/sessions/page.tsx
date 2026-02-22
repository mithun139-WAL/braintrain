"use client";

import { RecentSessionsTable } from "@/components/dashboard/RecentSessionsTable";
import { BookOpen, Plus } from "lucide-react";

export default function SessionsPage() {
    return (
        <div className="flex flex-col gap-8 pb-12">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 tracking-tight flex items-center gap-2">
                        <BookOpen className="text-primary" />
                        Practice Sessions
                    </h1>
                    <p className="text-gray-500 mt-1">Manage and review your AI-powered interview sessions.</p>
                </div>

                <button className="bg-primary hover:bg-primary-dark text-white font-bold py-2.5 px-6 rounded-xl shadow-lg shadow-primary/20 transition-all flex items-center gap-2 w-fit">
                    <Plus size={20} />
                    New Session
                </button>
            </div>

            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                <RecentSessionsTable />
            </div>
        </div>
    );
}
