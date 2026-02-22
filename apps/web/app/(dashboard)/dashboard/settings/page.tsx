"use client";

import React from "react";
import { useAuthStore } from "@/lib/store/auth.store";
import { useGetProfile } from "@/hooks/queries/useGetProfile";
import { ProfileTab } from "@/components/settings/ProfileTab";
import { SubscriptionTab } from "@/components/settings/SubscriptionTab";
import { SkillPreferencesCard } from "@/components/settings/SkillPreferencesCard";
import { AccountInformationCard } from "@/components/settings/AccountInformationCard";
import { PromoCard } from "@/components/settings/PromoCard";

export default function SettingsPage() {
    const { user: authUser } = useAuthStore();
    const { data: profileResponse, isLoading } = useGetProfile();
    const profile = profileResponse?.data;
    const isPro = (profile?.planType || "FREE").toUpperCase() === "PRO";

    if (isLoading) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center h-full gap-4">
                <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
                <p className="text-slate-500 font-medium animate-pulse">Loading settings...</p>
            </div>
        );
    }

    if (!isPro) {
        return (
            <div className="flex-1 flex flex-col h-full bg-background-light dark:bg-black/10 transition-colors pb-24 overflow-auto">
                <main className="w-full max-w-7xl mx-auto">
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                        {/* Left Column: Profile & Usage */}
                        <div className="lg:col-span-4 flex flex-col gap-6">
                            <ProfileTab profile={profile} isLoading={isLoading} />
                            <SubscriptionTab profile={profile} isLoading={isLoading} />
                        </div>
                        {/* Right Column: Settings & Details */}
                        <div className="lg:col-span-8 flex flex-col gap-6">
                            <AccountInformationCard profile={profile} isLoading={isLoading} />
                            <SkillPreferencesCard profile={profile} isLoading={isLoading} />
                        </div>
                    </div>
                </main>
            </div>
        );
    }

    return (
        <div className="flex-1 flex flex-col h-full bg-background-light dark:bg-black/10 transition-colors pb-24 overflow-auto">
            <main className="w-full max-w-[960px] mx-auto px-4 sm:px-6 py-8">
                <header className="mb-8">
                    <h1 className="text-3xl font-bold text-neutral-900 dark:text-white tracking-tight">Profile Settings</h1>
                    <p className="text-neutral-500 dark:text-neutral-400 mt-1 font-medium">Manage your account settings and preferences.</p>
                </header>

                <ProfileTab profile={profile} isLoading={isLoading} />

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
                    <div className="lg:col-span-2 flex flex-col gap-6">
                        <SubscriptionTab profile={profile} isLoading={isLoading} />
                        <AccountInformationCard profile={profile} isLoading={isLoading} />
                    </div>
                    <div className="flex flex-col gap-6">
                        <SkillPreferencesCard profile={profile} isLoading={isLoading} />
                        <PromoCard />
                    </div>
                </div>
            </main>
        </div>
    );
}
