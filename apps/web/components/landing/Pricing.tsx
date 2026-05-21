"use client";

import Link from "next/link";
import { Check, Sparkles } from "lucide-react";
import { useAuthStore } from "@/lib/store/auth.store";
import { useEffect, useState } from "react";

const FREE_FEATURES = [
    "3 practice sessions per month",
    "Basic AI response analysis",
    "500+ professional paths & roles",
    "Standard AI interviewer persona",
];

const PRO_FEATURES = [
    "20 practice sessions per month",
    "100 evaluation credits per month",
    "Deep-dive technical & behavioral reports",
    "Adaptive AI difficulty matching",
    "Multiple panel AI persona formats",
    "Priority training plan updates",
];

export function Pricing() {
    const { isAuthenticated, hasHydrated } = useAuthStore();
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    const isUserLoggedIn = mounted && hasHydrated && isAuthenticated;

    return (
        <section id="pricing" className="bg-background-light py-24 dark:bg-background-dark/30">
            <div className="mx-auto max-w-7xl px-6 lg:px-12">
                <div className="mb-20 text-center">
                    <div className="inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-xs font-semibold text-primary mb-4">
                        <Sparkles size={12} />
                        Flexible Plans
                    </div>
                    <h2 className="text-3xl font-black tracking-tight text-charcoal sm:text-4xl dark:text-white">
                        Simple, Transparent Pricing
                    </h2>
                    <p className="mt-4 text-slate-500 dark:text-slate-400">
                        Start training for free and upgrade as your career prep scales.
                    </p>
                </div>

                <div className="mx-auto grid max-w-lg grid-cols-1 gap-8 lg:max-w-4xl lg:grid-cols-2">
                    {/* Free Plan */}
                    <div className="flex flex-col justify-between rounded-3xl border border-slate-100 bg-white p-8 shadow-sm transition-all hover:border-slate-200 hover:shadow-md dark:border-slate-800 dark:bg-slate-900/40 dark:hover:border-slate-700">
                        <div>
                            <h3 className="text-xl font-bold text-charcoal dark:text-white">Free Plan</h3>
                            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                                Perfect for getting started and test-driving the AI mentor.
                            </p>
                            <p className="mt-6 flex items-baseline gap-1">
                                <span className="text-4xl font-black tracking-tight text-charcoal dark:text-white">$0</span>
                                <span className="text-sm font-semibold text-slate-500">/month</span>
                            </p>
                            <ul className="mt-8 space-y-3">
                                {FREE_FEATURES.map((feature) => (
                                    <li key={feature} className="flex items-start gap-3 text-sm text-slate-600 dark:text-slate-300">
                                        <div className="mt-0.5 rounded-full bg-emerald/10 p-0.5 text-emerald">
                                            <Check size={14} className="stroke-[3]" />
                                        </div>
                                        <span>{feature}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                        <div className="mt-8">
                            <Link
                                href={isUserLoggedIn ? "/dashboard" : "/register"}
                                className="block w-full rounded-xl border border-slate-200 bg-white py-3 text-center text-sm font-bold text-charcoal shadow-sm hover:bg-slate-50 dark:border-slate-700 dark:bg-transparent dark:text-white dark:hover:bg-slate-800/50 transition-colors"
                            >
                                {isUserLoggedIn ? "Go to Dashboard" : "Get Started Free"}
                            </Link>
                        </div>
                    </div>

                    {/* Pro Plan */}
                    <div className="relative flex flex-col justify-between rounded-3xl border-2 border-primary bg-white p-8 shadow-lg dark:bg-slate-900/60">
                        <div className="absolute -top-4 left-1/2 -translate-x-1/2 rounded-full bg-primary px-4 py-1 text-xs font-extrabold uppercase tracking-widest text-white shadow-md">
                            Most Popular
                        </div>
                        <div>
                            <div className="flex items-center justify-between">
                                <h3 className="text-xl font-bold text-charcoal dark:text-white">Pro Plan</h3>
                            </div>
                            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                                For serious professionals targeting tier-1 technical/behavioral roles.
                            </p>
                            <p className="mt-6 flex items-baseline gap-1">
                                <span className="text-4xl font-black tracking-tight text-charcoal dark:text-white">$29</span>
                                <span className="text-sm font-semibold text-slate-500">/month</span>
                            </p>
                            <ul className="mt-8 space-y-3">
                                {PRO_FEATURES.map((feature) => (
                                    <li key={feature} className="flex items-start gap-3 text-sm text-slate-600 dark:text-slate-300">
                                        <div className="mt-0.5 rounded-full bg-primary/10 p-0.5 text-primary">
                                            <Check size={14} className="stroke-[3]" />
                                        </div>
                                        <span>{feature}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                        <div className="mt-8">
                            <Link
                                href={isUserLoggedIn ? "/dashboard/settings" : "/register?plan=pro"}
                                className="block w-full rounded-xl bg-primary py-3 text-center text-sm font-bold text-white shadow-md shadow-primary/20 hover:brightness-110 active:scale-[0.98] transition-all"
                            >
                                {isUserLoggedIn ? "Manage Subscription" : "Upgrade to Pro"}
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
