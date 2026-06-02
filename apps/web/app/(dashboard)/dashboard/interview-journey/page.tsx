"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { PageHeader } from "@/core/components/ui/PageHeader";
import { Surface } from "@/core/components/ui/Surface";
import { buttonStyles } from "@/core/components/ui/button";
import { useJourneys } from "@/hooks/queries/useJourneys";
import { useEditJourney, useDeleteJourney } from "@/hooks/mutations/useCreateJourney";
import { cn } from "@/lib/utils";
import type { InterviewJourney } from "@braintrain/shared";
import {
    Briefcase,
    Plus,
    ArrowRight,
    CheckCircle2,
    Clock,
    AlertCircle,
    FileText,
    Pencil,
    Trash2,
    X,
} from "lucide-react";

const statusConfig: Record<string, { color: string; icon: typeof Clock; label: string }> = {
    CREATED: { color: "text-amber-500", icon: Clock, label: "Draft" },
    ACTIVE: { color: "text-blue-500", icon: AlertCircle, label: "In Progress" },
    COMPLETED: { color: "text-emerald-500", icon: CheckCircle2, label: "Completed" },
    ANALYZED: { color: "text-purple-500", icon: FileText, label: "Report Ready" },
};

export default function InterviewJourneyPage() {
    const router = useRouter();
    const { data: journeysData, isLoading } = useJourneys();
    const editMutation = useEditJourney();
    const deleteMutation = useDeleteJourney();

    const [editingJourney, setEditingJourney] = useState<InterviewJourney | null>(null);
    const [deletingJourney, setDeletingJourney] = useState<InterviewJourney | null>(null);
    const [editRoleTitle, setEditRoleTitle] = useState("");
    const [editCompanyName, setEditCompanyName] = useState("");

    const journeys = journeysData?.data ?? [];

    const handleCardClick = (e: React.MouseEvent, id: string) => {
        if ((e.target as HTMLElement).closest(".action-btn")) {
            return;
        }
        router.push(`/dashboard/interview-journey/${id}/analysis`);
    };

    return (
        <div className="flex flex-col gap-8 pb-12">
            <PageHeader
                eyebrow="Hiring Simulation"
                title="Interview Journeys"
                description="Simulate a real company hiring process from resume to final report."
                actions={
                    <Link href="/dashboard/interview-journey/new" className={buttonStyles()}>
                        <Plus size={16} />
                        New Journey
                    </Link>
                }
            />

            {isLoading ? (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {Array.from({ length: 3 }).map((_, i) => (
                        <div key={i} className="h-48 rounded-xl bg-card border border-border animate-pulse" />
                    ))}
                </div>
            ) : journeys.length === 0 ? (
                <Surface variant="default" padding="lg" className="text-center py-16">
                    <div className="size-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4 text-primary">
                        <Briefcase size={24} />
                    </div>
                    <h3 className="text-lg font-semibold text-foreground mb-2">No interview journeys yet</h3>
                    <p className="text-sm text-muted-foreground max-w-md mx-auto mb-6">
                        Create your first interview journey by uploading a resume and pasting a job description.
                        We'll generate a complete hiring simulation.
                    </p>
                    <Link href="/dashboard/interview-journey/new" className={buttonStyles()}>
                        <Plus size={16} />
                        Start Your First Journey
                    </Link>
                </Surface>
            ) : (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {journeys.map((journey) => {
                        const status = statusConfig[journey.status] ?? statusConfig.CREATED;
                        const StatusIcon = status.icon;
                        return (
                            <div
                                key={journey.id}
                                onClick={(e) => handleCardClick(e, journey.id)}
                                className="h-full cursor-pointer group"
                            >
                                <Surface
                                    variant="default"
                                    padding="md"
                                    className="h-full flex flex-col gap-3 hover:border-primary/30 transition-colors"
                                >
                                    <div className="flex items-start justify-between">
                                        <div className="size-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                                            <Briefcase size={18} />
                                        </div>
                                        <div className="flex items-center gap-1">
                                            <div className={cn("flex items-center gap-1.5 text-xs font-medium mr-2", status.color)}>
                                                <StatusIcon size={12} />
                                                {status.label}
                                            </div>
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    setEditingJourney(journey);
                                                    setEditRoleTitle(journey.roleTitle);
                                                    setEditCompanyName(journey.companyName || "");
                                                }}
                                                className="action-btn p-1.5 rounded-md hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                                                title="Edit Journey"
                                            >
                                                <Pencil size={13} />
                                            </button>
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    setDeletingJourney(journey);
                                                }}
                                                className="action-btn p-1.5 rounded-md hover:bg-red-500/10 text-muted-foreground hover:text-red-500 transition-colors"
                                                title="Delete Journey"
                                            >
                                                <Trash2 size={13} />
                                            </button>
                                        </div>
                                    </div>
                                    <div className="flex-1">
                                        <h3 className="font-semibold text-foreground text-sm mb-1">
                                            {journey.roleTitle}
                                        </h3>
                                        {journey.companyName && (
                                            <p className="text-xs text-muted-foreground">{journey.companyName}</p>
                                        )}
                                        {journey.candidateLevel && (
                                            <p className="text-[11px] text-muted-foreground/60 mt-1">
                                                Level: {journey.candidateLevel}
                                            </p>
                                        )}
                                    </div>
                                    <div className="flex items-center justify-between pt-2 border-t border-border/50">
                                        <span className="text-[11px] text-muted-foreground">
                                            {journey.sessions?.length ?? 0} rounds
                                        </span>
                                        <ArrowRight size={14} className="text-muted-foreground group-hover:text-primary transition-colors" />
                                    </div>
                                </Surface>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Edit Journey Modal */}
            {editingJourney && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
                    <Surface variant="default" padding="lg" className="w-full max-w-md space-y-4 border border-border shadow-2xl relative">
                        <button
                            onClick={() => setEditingJourney(null)}
                            className="absolute top-4 right-4 p-1.5 rounded-md hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                        >
                            <X size={16} />
                        </button>
                        
                        <div>
                            <h3 className="text-lg font-semibold text-foreground">Edit Journey</h3>
                            <p className="text-xs text-muted-foreground mt-0.5">Update the details for this hiring simulation.</p>
                        </div>

                        <div className="space-y-4 pt-2">
                            <div className="space-y-1.5">
                                <label className="text-xs font-semibold text-foreground">Role Title</label>
                                <input
                                    type="text"
                                    value={editRoleTitle}
                                    onChange={(e) => setEditRoleTitle(e.target.value)}
                                    placeholder="e.g. Senior Frontend Engineer"
                                    className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/30"
                                />
                            </div>

                            <div className="space-y-1.5">
                                <label className="text-xs font-semibold text-foreground">Company Name</label>
                                <input
                                    type="text"
                                    value={editCompanyName}
                                    onChange={(e) => setEditCompanyName(e.target.value)}
                                    placeholder="e.g. Acme Corp"
                                    className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/30"
                                />
                            </div>
                        </div>

                        <div className="flex justify-end gap-3 pt-4 border-t border-border/50">
                            <button
                                onClick={() => setEditingJourney(null)}
                                className={buttonStyles({ variant: "ghost", size: "sm" })}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={async () => {
                                    if (!editRoleTitle.trim()) return;
                                    await editMutation.mutateAsync({
                                        journeyId: editingJourney.id,
                                        data: {
                                            roleTitle: editRoleTitle.trim(),
                                            companyName: editCompanyName.trim() || undefined,
                                        },
                                    });
                                    setEditingJourney(null);
                                }}
                                disabled={editMutation.isPending}
                                className={buttonStyles({ size: "sm" })}
                            >
                                {editMutation.isPending ? "Saving..." : "Save Changes"}
                            </button>
                        </div>
                    </Surface>
                </div>
            )}

            {/* Delete Journey Modal */}
            {deletingJourney && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
                    <Surface variant="default" padding="lg" className="w-full max-w-sm space-y-4 border border-border shadow-2xl relative">
                        <button
                            onClick={() => setDeletingJourney(null)}
                            className="absolute top-4 right-4 p-1.5 rounded-md hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                        >
                            <X size={16} />
                        </button>
                        
                        <div>
                            <h3 className="text-lg font-semibold text-foreground">Delete Journey</h3>
                            <p className="text-xs text-muted-foreground mt-1">
                                Are you sure you want to delete <span className="font-semibold text-foreground">"{deletingJourney.roleTitle}"</span>?
                            </p>
                        </div>

                        <p className="text-xs text-muted-foreground leading-relaxed">
                            This will permanently delete this journey and all its associated mock rounds. This action cannot be undone.
                        </p>

                        <div className="flex justify-end gap-3 pt-4 border-t border-border/50">
                            <button
                                onClick={() => setDeletingJourney(null)}
                                className={buttonStyles({ variant: "ghost", size: "sm" })}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={async () => {
                                    await deleteMutation.mutateAsync(deletingJourney.id);
                                    setDeletingJourney(null);
                                }}
                                disabled={deleteMutation.isPending}
                                className={cn(
                                    buttonStyles({ variant: "primary", size: "sm" }),
                                    "bg-red-600 hover:bg-red-700 text-white hover:brightness-100"
                                )}
                            >
                                {deleteMutation.isPending ? "Deleting..." : "Delete"}
                            </button>
                        </div>
                    </Surface>
                </div>
            )}
        </div>
    );
}
