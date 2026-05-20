"use client";

import React, { useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Info } from "lucide-react";
import { PageHeader } from "@/core/components/ui/PageHeader";
import { Surface } from "@/core/components/ui/Surface";
import { useGetProfile } from "@/hooks/queries/useGetProfile";
import { ProfileTab } from "@/components/settings/ProfileTab";
import { SubscriptionTab } from "@/components/settings/SubscriptionTab";
import { SkillPreferencesCard } from "@/components/settings/SkillPreferencesCard";
import { AccountInformationCard } from "@/components/settings/AccountInformationCard";
import { PromoCard } from "@/components/settings/PromoCard";

export default function SettingsPage() {
    const searchParams = useSearchParams();
    const queryClient = useQueryClient();
    const { data: profileResponse, isLoading } = useGetProfile();
    const profile = profileResponse?.data;
    const isPro = (profile?.planType || "FREE").toUpperCase() === "PRO";
    const billingState = searchParams.get("billing");

    useEffect(() => {
        if (billingState !== "success") return;

        queryClient.invalidateQueries({ queryKey: ["profile"] });
        queryClient.invalidateQueries({ queryKey: ["billing", "status"] });
    }, [billingState, queryClient]);

    if (isLoading) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center h-full gap-4">
                <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
                <p className="text-slate-500 font-medium animate-pulse">Loading settings...</p>
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-8 pb-12">
            {billingState === "success" ? (
                <Surface variant="subtle" padding="lg" className="border-primary/10 bg-primary/5">
                    <div className="flex items-start gap-3 text-sm text-foreground">
                        <CheckCircle2 size={18} className="mt-0.5 text-primary" />
                        <div className="space-y-1">
                            <p className="font-semibold">Checkout completed.</p>
                            <p className="text-muted-foreground">
                                We are syncing your subscription status. If the PRO badge does not appear immediately, refresh this page in a few seconds.
                            </p>
                        </div>
                    </div>
                </Surface>
            ) : null}

            {billingState === "cancelled" ? (
                <Surface variant="subtle" padding="lg" className="border-border bg-muted/40">
                    <div className="flex items-start gap-3 text-sm text-foreground">
                        <Info size={18} className="mt-0.5 text-muted-foreground" />
                        <div className="space-y-1">
                            <p className="font-semibold">Upgrade cancelled.</p>
                            <p className="text-muted-foreground">
                                Your current plan is unchanged. You can reopen checkout at any time from this page.
                            </p>
                        </div>
                    </div>
                </Surface>
            ) : null}

            <PageHeader
                eyebrow="Account"
                title="Settings"
                description="Manage your profile, plan usage, connected accounts, and the skills that shape your interview practice."
                meta={
                    <>
                        <SettingsMeta label="Plan" value={isPro ? "PRO" : "FREE"} />
                        <SettingsMeta label="Sessions this month" value={profile?.monthlySessionCount ?? 0} />
                        <SettingsMeta label="Evaluation credits" value={profile?.monthlyEvaluationCredits ?? 0} />
                    </>
                }
            />

            <Surface variant="hero" padding="xl" className="grid gap-6 lg:grid-cols-[minmax(0,1.3fr)_minmax(18rem,0.9fr)] lg:items-center">
                <div className="space-y-3">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-primary/80">Account Overview</p>
                    <h2 className="font-display text-display-lg text-foreground">
                        {isPro ? "Your PRO workspace is configured for deeper, higher-frequency practice." : "Your FREE workspace is set up for light, signal-driven practice."}
                    </h2>
                    <p className="max-w-reading text-body-md text-muted-foreground">
                        Keep profile details current, tune skill focus, and make sure your plan limits match the intensity of the practice loop you want to maintain.
                    </p>
                </div>
                <Surface variant="subtle" padding="lg" className="border-primary/10 bg-primary/5">
                    <div className="space-y-3">
                        <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-primary/80">Current Status</p>
                        <div className="grid gap-4 sm:grid-cols-2">
                            <SettingsMini label="Plan" value={isPro ? "PRO" : "FREE"} />
                            <SettingsMini label="Usage reset" value={profile?.usagePeriodStart ? new Date(profile.usagePeriodStart).toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "-"} />
                            <SettingsMini label="Profile completion" value={profile?.bio ? "In progress" : "Needs bio"} />
                            <SettingsMini label="Focus skills" value={profile?.skillPreferences?.length ?? 0} />
                        </div>
                    </div>
                </Surface>
            </Surface>

            <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1.4fr)_minmax(20rem,0.9fr)] gap-6">
                <div className="space-y-6">
                    <ProfileTab profile={profile} isLoading={isLoading} />
                    <SubscriptionTab profile={profile} isLoading={isLoading} />
                    <AccountInformationCard profile={profile} isLoading={isLoading} />
                </div>

                <div className="space-y-6">
                    <SkillPreferencesCard profile={profile} isLoading={isLoading} />
                    <PromoCard />
                </div>
            </div>
        </div>
    );
}

function SettingsMeta({ label, value }: { label: string; value: string | number }) {
    return (
        <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 text-sm text-foreground shadow-card">
            <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">{label}</span>
            <span className="font-semibold text-foreground">{value}</span>
        </div>
    );
}

function SettingsMini({ label, value }: { label: string; value: string | number }) {
    return (
        <div className="rounded-2xl border border-border bg-card px-4 py-3 shadow-card">
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">{label}</p>
            <p className="mt-1 text-sm font-semibold text-foreground">{value}</p>
        </div>
    );
}
