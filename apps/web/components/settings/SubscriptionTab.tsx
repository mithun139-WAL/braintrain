import type { User } from "@braintrain/shared";
import { CreditCard, Gauge, Settings2, Sparkles } from "lucide-react";
import { Surface } from "@/core/components/ui/Surface";
import { buttonStyles } from "@/core/components/ui/button";
import { useOpenBillingPortal, useStartCheckout } from "@/hooks/mutations/useBillingMutations";
import { useBillingStatus } from "@/hooks/queries/useBillingStatus";

interface SubscriptionTabProps {
    profile?: User;
    isLoading: boolean;
}

function formatResetDate(value?: string) {
    if (!value) return "-";
    const date = new Date(value);
    date.setMonth(date.getMonth() + 1);
    return date.toLocaleDateString("en-US", {
        month: "long",
        day: "numeric",
        year: "numeric",
    });
}

export function SubscriptionTab({ profile, isLoading }: SubscriptionTabProps) {
    const startCheckout = useStartCheckout();
    const openBillingPortal = useOpenBillingPortal();
    const { data: billingStatusResponse, isLoading: isBillingStatusLoading } = useBillingStatus();

    if (isLoading) {
        return <Surface padding="xl" className="min-h-[220px] animate-pulse" />;
    }

    const billingStatus = billingStatusResponse?.data;
    const isPro = (profile?.planType || "FREE").toUpperCase() === "PRO";
    const isBillingConfigured = billingStatus?.configured ?? false;
    const hasActiveSubscription = billingStatus?.hasActiveSubscription ?? false;
    const sessionsUsed = profile?.monthlySessionCount || 0;
    const sessionsLimit = isPro ? 20 : 3;
    const sessionsPercent = Math.min(100, Math.round((sessionsUsed / sessionsLimit) * 100));
    const creditsAvailable = profile?.monthlyEvaluationCredits || 0;
    const creditsLimit = isPro ? 100 : 0;
    const creditsUsed = isPro ? creditsLimit - creditsAvailable : 0;
    const creditsPercent = isPro && creditsLimit > 0 ? Math.min(100, Math.round((creditsUsed / creditsLimit) * 100)) : 0;
    const isBillingPending = startCheckout.isPending || openBillingPortal.isPending;

    return (
        <Surface padding="xl" className="space-y-8">
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div className="space-y-2">
                    <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.22em] text-primary/80">
                        <Gauge size={14} />
                        Plan Usage
                    </div>
                    <h3 className="font-display text-title-lg text-foreground">
                        {isPro ? "Your PRO plan is active and ready for heavier weekly reps." : "Your FREE plan is tuned for lighter signal collection."}
                    </h3>
                    <p className="max-w-reading text-body-sm text-muted-foreground">
                        Monthly limits reset on {formatResetDate(profile?.usagePeriodStart)}. Keep an eye on usage so the next practice block matches your current plan.
                    </p>
                    {!isBillingConfigured ? (
                        <p className="text-body-sm text-muted-foreground">
                            Billing is not configured in this environment yet. Plan badges still render from your account state, but checkout and portal actions will stay unavailable until Stripe keys are set.
                        </p>
                    ) : null}
                </div>

                <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 text-sm font-semibold text-foreground shadow-card">
                    <Sparkles size={14} className="text-primary" />
                    {(profile?.planType || "FREE").toUpperCase()} plan
                </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
                <UsageMeter
                    label="Practice sessions"
                    value={`${sessionsUsed} / ${sessionsLimit}`}
                    percent={sessionsPercent}
                    description={isPro ? "High-frequency session allowance." : "Starter monthly session allowance."}
                />
                <UsageMeter
                    label="Evaluation credits"
                    value={isPro ? `${creditsUsed} / ${creditsLimit}` : "Upgrade required"}
                    percent={creditsPercent}
                    description={isPro ? `${creditsAvailable} credits still available this cycle.` : "Detailed AI evaluations unlock with PRO."}
                />
            </div>

            {!isPro ? (
                <Surface variant="subtle" padding="lg" className="border-primary/10 bg-primary/5">
                    <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                        <div className="space-y-1">
                            <p className="text-sm font-semibold text-foreground">Need more room for practice?</p>
                            <p className="text-body-sm text-muted-foreground">
                                {isBillingConfigured
                                    ? "PRO increases monthly session allowance and unlocks full evaluation capacity."
                                    : "PRO exists in the product model, but checkout is unavailable until Stripe is configured for this environment."}
                            </p>
                        </div>
                        {isBillingConfigured ? (
                            <button
                                type="button"
                                onClick={() => startCheckout.mutate()}
                                disabled={isBillingPending || isBillingStatusLoading}
                                className={buttonStyles()}
                            >
                                <CreditCard size={16} />
                                {startCheckout.isPending ? "Opening checkout..." : "Upgrade to PRO"}
                            </button>
                        ) : (
                            <span className={buttonStyles({ variant: "secondary" })}>
                                <Settings2 size={16} />
                                Billing unavailable
                            </span>
                        )}
                    </div>
                </Surface>
            ) : (
                <Surface variant="subtle" padding="lg" className="border-primary/10 bg-primary/5">
                    <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                        <div className="space-y-1">
                            <p className="text-sm font-semibold text-foreground">Manage your subscription</p>
                            <p className="text-body-sm text-muted-foreground">
                                {isBillingConfigured && hasActiveSubscription
                                    ? "Open the Stripe billing portal to update payment details or manage your PRO subscription."
                                    : isBillingConfigured
                                    ? "Stripe is configured, but we do not currently see an active subscription linked to this account."
                                    : "This environment does not have Stripe configured, so billing management is unavailable here."}
                            </p>
                        </div>
                        {isBillingConfigured && hasActiveSubscription ? (
                            <button
                                type="button"
                                onClick={() => openBillingPortal.mutate()}
                                disabled={isBillingPending || isBillingStatusLoading}
                                className={buttonStyles({ variant: "secondary" })}
                            >
                                <CreditCard size={16} />
                                {openBillingPortal.isPending ? "Opening portal..." : "Manage billing"}
                            </button>
                        ) : (
                            <span className={buttonStyles({ variant: "secondary" })}>
                                <Settings2 size={16} />
                                {isBillingConfigured ? "No active portal yet" : "Billing unavailable"}
                            </span>
                        )}
                    </div>
                </Surface>
            )}
        </Surface>
    );
}

function UsageMeter({
    label,
    value,
    percent,
    description,
}: {
    label: string;
    value: string;
    percent: number;
    description: string;
}) {
    return (
        <div className="rounded-3xl border border-border bg-muted/30 p-5">
            <div className="flex items-end justify-between gap-4">
                <div>
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">{label}</p>
                    <p className="mt-2 text-xl font-bold text-foreground">{value}</p>
                </div>
                <span className="text-xs font-semibold text-muted-foreground">{percent}%</span>
            </div>
            <div className="mt-4 h-2 overflow-hidden rounded-full bg-background">
                <div className="h-full rounded-full bg-primary transition-all duration-700" style={{ width: `${percent}%` }} />
            </div>
            <p className="mt-3 text-body-sm text-muted-foreground">{description}</p>
        </div>
    );
}
