"use client";

import Link from "next/link";
import { PageHeader } from "@/core/components/ui/PageHeader";
import { buttonStyles } from "@/core/components/ui/button";
import { RecentSessionsTable } from "@/components/dashboard/RecentSessionsTable";
import { BookOpen, Plus } from "lucide-react";

export default function SessionsPage() {
    return (
        <div className="flex flex-col gap-8 pb-12">
            <PageHeader
                eyebrow="Practice Workspace"
                title="Practice sessions"
                description="Review recent runs, reopen active sessions, and jump back into analyzed reports without losing context."
                actions={
                    <Link href="/dashboard/sessions/start" className={buttonStyles()}>
                        <Plus size={16} />
                        New Session
                    </Link>
                }
            />

            <RecentSessionsTable
                title="Session history"
                description="A truthful view of current practice status, question volume, and available reports."
                limit={20}
            />
        </div>
    );
}
