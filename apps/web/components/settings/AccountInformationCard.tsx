import type { User } from "@braintrain/shared";
import { BadgeInfo, CalendarDays, Mail, Phone } from "lucide-react";
import { Surface } from "@/core/components/ui/Surface";

interface AccountInformationCardProps {
    profile?: User;
    isLoading: boolean;
}

function formatDate(dateString?: string) {
    if (!dateString) return "-";
    return new Date(dateString).toLocaleDateString("en-US", {
        year: "numeric",
        month: "long",
        day: "numeric",
    });
}

export function AccountInformationCard({ profile, isLoading }: AccountInformationCardProps) {
    if (isLoading) {
        return <Surface padding="xl" className="min-h-[220px] animate-pulse" />;
    }

    const accountRows = [
        {
            label: "Email",
            value: profile?.email || "-",
            icon: Mail,
            hint: "Primary sign-in identifier",
        },
        {
            label: "Phone",
            value: profile?.phoneNumber || "No phone added",
            icon: Phone,
            hint: "Optional fallback identity",
        },
        {
            label: "Account created",
            value: formatDate(profile?.createdAt),
            icon: CalendarDays,
            hint: "Workspace origin",
        },
        {
            label: "Last updated",
            value: formatDate(profile?.updatedAt || profile?.createdAt),
            icon: BadgeInfo,
            hint: "Most recent profile change",
        },
    ];

    return (
        <Surface padding="xl" className="space-y-6">
            <div className="space-y-2">
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-primary/80">
                    Account Identity
                </p>
                <h3 className="font-display text-title-lg text-foreground">Your account metadata at a glance</h3>
                <p className="max-w-reading text-body-sm text-muted-foreground">
                    These values come directly from your account record and help confirm how this workspace is identified across authentication and billing flows.
                </p>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
                {accountRows.map((row) => (
                    <div key={row.label} className="rounded-3xl border border-border bg-muted/30 p-5">
                        <div className="flex items-start gap-3">
                            <div className="flex size-10 items-center justify-center rounded-2xl bg-card text-primary shadow-card">
                                <row.icon size={18} />
                            </div>
                            <div className="space-y-1">
                                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                                    {row.label}
                                </p>
                                <p className="text-sm font-semibold text-foreground">{row.value}</p>
                                <p className="text-body-sm text-muted-foreground">{row.hint}</p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </Surface>
    );
}
