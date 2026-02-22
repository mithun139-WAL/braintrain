import React from "react";
import { User } from "@braintrain/shared";

interface AccountInformationCardProps {
    profile?: User;
    isLoading: boolean;
}

export function AccountInformationCard({ profile, isLoading }: AccountInformationCardProps) {
    if (isLoading) {
        return (
            <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm border border-neutral-200 dark:border-neutral-700 p-8 animate-pulse">
                <div className="h-6 w-1/3 bg-slate-200 dark:bg-neutral-700 rounded mb-8"></div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="h-12 bg-slate-100 dark:bg-neutral-700 rounded"></div>
                    <div className="h-12 bg-slate-100 dark:bg-neutral-700 rounded"></div>
                </div>
            </div>
        );
    }

    const formatDate = (dateString?: string) => {
        if (!dateString) return "-";
        return new Date(dateString).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
    };

    return (
        <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm border border-neutral-200 dark:border-neutral-700 p-6 md:p-8 transition-colors">
            <h3 className="text-lg font-bold text-neutral-900 dark:text-white mb-8 flex items-center gap-2 tracking-tight">
                <span className="material-symbols-outlined text-primary">badge</span>
                Account Information
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-y-8 gap-x-10">
                {/* Email */}
                <div className="flex flex-col gap-2">
                    <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest">Email Address</label>
                    <div className="flex items-center gap-3 px-4 py-3 bg-neutral-50 dark:bg-neutral-900/50 border border-neutral-100 dark:border-neutral-700 rounded-lg text-neutral-900 dark:text-white transition-colors">
                        <span className="material-symbols-outlined text-neutral-400 text-[20px]">mail</span>
                        <span className="text-sm font-medium">{profile?.email}</span>
                        <span className="ml-auto material-symbols-outlined text-emerald-500 text-[18px] filled">verified</span>
                    </div>
                </div>

                {/* Phone Number */}
                <div className="flex flex-col gap-2">
                    <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest">Phone Number</label>
                    <div className="flex items-center gap-3 px-4 py-3 bg-neutral-50 dark:bg-neutral-900/50 border border-neutral-100 dark:border-neutral-700 rounded-lg transition-colors group">
                        <span className="material-symbols-outlined text-neutral-400 text-[20px]">phone</span>
                        <span className="text-sm font-medium text-neutral-400 italic">No phone added</span>
                        <button className="ml-auto text-xs font-bold text-primary hover:underline transition-all">Add</button>
                    </div>
                </div>

                {/* Connected Accounts */}
                <div className="flex flex-col gap-2">
                    <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest">Connected Accounts</label>
                    <div className="flex items-center gap-3 px-4 py-3 bg-neutral-50 dark:bg-neutral-900/50 border border-neutral-100 dark:border-neutral-700 rounded-lg transition-colors">
                        <img src="https://www.gstatic.com/images/branding/product/1x/googleg_48dp.png" alt="Google" className="h-5 w-5 grayscale opacity-50" />
                        <span className="text-sm font-medium text-neutral-400">Google Account</span>
                        <button className="ml-auto text-xs font-bold text-neutral-600 dark:text-neutral-300 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-600 px-3 py-1.5 rounded shadow-sm hover:bg-neutral-50 dark:hover:bg-neutral-700 transition-colors">Connect</button>
                    </div>
                </div>

                {/* Dates */}
                <div className="grid grid-cols-2 gap-4">
                    <div className="flex flex-col gap-2">
                        <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest text-nowrap">Account Created</label>
                        <p className="text-sm text-neutral-600 dark:text-neutral-300 font-bold px-1">{formatDate(profile?.createdAt)}</p>
                    </div>
                    <div className="flex flex-col gap-2">
                        <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest text-nowrap">Last Updated</label>
                        <p className="text-sm text-neutral-600 dark:text-neutral-300 font-bold px-1">{formatDate(profile?.updatedAt || profile?.createdAt)}</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
