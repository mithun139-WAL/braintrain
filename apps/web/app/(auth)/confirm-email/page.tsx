"use client";

import Link from "next/link";
import React, { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "@/lib/store/auth.store";
import { identityApi } from "@/lib/api/identity.api";

function ConfirmEmailContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const token = searchParams.get("token") || "";
    const setAuth = useAuthStore((state) => state.setAuth);

    const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
    const [message, setMessage] = useState("");

    useEffect(() => {
        if (!token) {
            setStatus("error");
            setMessage("No confirmation token found. The link may be invalid or expired.");
            return;
        }

        const confirm = async () => {
            try {
                const response = await identityApi.confirmEmail(token);
                if (response.success && response.data) {
                    const { accessToken, user } = response.data as any;
                    setAuth(user, accessToken);
                    setStatus("success");
                    setTimeout(() => router.push("/dashboard"), 2000);
                } else {
                    setStatus("error");
                    setMessage(response.message || "Confirmation failed. The link may be invalid or expired.");
                }
            } catch (err: any) {
                setStatus("error");
                setMessage(typeof err === "string" ? err : err.message || "An error occurred during confirmation.");
            }
        };

        confirm();
    }, [token, setAuth, router]);

    if (status === "loading") {
        return (
            <div className="w-full max-w-[420px] animate-fade-in group/card relative">
                {/* Ambient card shadow glow */}
                <div className="absolute -inset-0.5 bg-gradient-to-r from-primary/25 to-violet-500/25 rounded-2xl blur-lg opacity-75 group-hover/card:opacity-100 transition duration-500" />
                
                {/* Card Container */}
                <div className="relative rounded-2xl bg-card/85 backdrop-blur-xl border border-border/80 dark:border-border/30 shadow-card overflow-hidden">
                    {/* Top gradient accent line */}
                    <div className="h-1.5 w-full bg-gradient-to-r from-primary via-sky-400 to-violet-500" />

                    {/* Card body */}
                    <div className="px-8 pt-10 pb-8 text-center">
                        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-primary/10 to-violet-500/10 border border-primary/20 shadow-inner mb-5">
                            <svg className="animate-spin h-6 w-6 text-primary" viewBox="0 0 24 24" fill="none">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                            </svg>
                        </div>
                        <h1 className="font-display text-2xl font-black tracking-tight text-foreground mb-2">
                            Confirming your email...
                        </h1>
                        <p className="text-muted-foreground text-sm font-medium leading-relaxed">
                            Please wait while we verify your account.
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    if (status === "success") {
        return (
            <div className="w-full max-w-[420px] animate-fade-in group/card relative">
                {/* Ambient card shadow glow */}
                <div className="absolute -inset-0.5 bg-gradient-to-r from-primary/25 to-violet-500/25 rounded-2xl blur-lg opacity-75 group-hover/card:opacity-100 transition duration-500" />
                
                {/* Card Container */}
                <div className="relative rounded-2xl bg-card/85 backdrop-blur-xl border border-border/80 dark:border-border/30 shadow-card overflow-hidden">
                    {/* Top gradient accent line */}
                    <div className="h-1.5 w-full bg-gradient-to-r from-primary via-sky-400 to-violet-500" />

                    {/* Card body */}
                    <div className="px-8 pt-10 pb-8 text-center">
                        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald/10 to-teal-500/10 border border-emerald/20 shadow-inner mb-5">
                            <span className="material-symbols-outlined text-emerald text-[28px] drop-shadow-sm" style={{ fontVariationSettings: "'FILL' 1" }}>
                                check_circle
                            </span>
                        </div>
                        <h1 className="font-display text-2xl font-black tracking-tight text-foreground mb-2">
                            Email confirmed!
                        </h1>
                        <p className="text-muted-foreground text-sm font-medium mb-6 leading-relaxed">
                            Your account is now active. Redirecting you to the dashboard...
                        </p>
                        <Link
                            href="/dashboard"
                            className="w-full flex items-center justify-center gap-2 h-11 rounded-xl bg-primary hover:bg-primary-dark text-white font-bold text-body-sm shadow-lg shadow-primary/20 hover:shadow-xl hover:shadow-primary/30 transition-all duration-200 active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-primary/40 focus:ring-offset-2 focus:ring-offset-card"
                        >
                            Go to Dashboard
                            <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                        </Link>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="w-full max-w-[420px] animate-fade-in group/card relative">
            {/* Ambient card shadow glow */}
            <div className="absolute -inset-0.5 bg-gradient-to-r from-primary/25 to-violet-500/25 rounded-2xl blur-lg opacity-75 group-hover/card:opacity-100 transition duration-500" />
            
            {/* Card Container */}
            <div className="relative rounded-2xl bg-card/85 backdrop-blur-xl border border-border/80 dark:border-border/30 shadow-card overflow-hidden">
                {/* Top gradient accent line */}
                <div className="h-1.5 w-full bg-gradient-to-r from-primary via-sky-400 to-violet-500" />

                {/* Card body */}
                <div className="px-8 pt-10 pb-8 text-center">
                    <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-ruby/10 to-red-500/10 border border-ruby/20 shadow-inner mb-5">
                        <span className="material-symbols-outlined text-ruby text-[28px] drop-shadow-sm" style={{ fontVariationSettings: "'FILL' 1" }}>
                            error
                        </span>
                    </div>
                    <h1 className="font-display text-2xl font-black tracking-tight text-foreground mb-2">
                        Confirmation failed
                    </h1>
                    <p className="text-muted-foreground text-sm font-medium mb-6 leading-relaxed">
                        {message}
                    </p>
                    <div className="flex flex-col gap-3">
                        <Link
                            href="/register"
                            className="w-full flex items-center justify-center gap-2 h-11 rounded-xl bg-primary hover:bg-primary-dark text-white font-bold text-body-sm shadow-lg shadow-primary/20 hover:shadow-xl hover:shadow-primary/30 transition-all duration-200 active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-primary/40 focus:ring-offset-2 focus:ring-offset-card"
                        >
                            Create a new account
                        </Link>
                        <Link
                            href="/login"
                            className="w-full flex items-center justify-center gap-2 h-11 rounded-xl border border-border/80 dark:border-border/30 bg-background/50 hover:bg-muted/80 dark:hover:bg-muted/30 text-foreground text-body-sm font-semibold transition-all duration-200 hover:border-border dark:hover:border-border/60 active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-primary/20"
                        >
                            Back to Sign In
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default function ConfirmEmailPage() {
    return (
        <Suspense fallback={
            <div className="w-full max-w-[420px] relative">
                <div className="absolute -inset-0.5 bg-gradient-to-r from-primary/25 to-violet-500/25 rounded-2xl blur-lg opacity-75" />
                <div className="relative rounded-2xl bg-card border border-border/80 dark:border-border/30 shadow-card h-60 animate-pulse" />
            </div>
        }>
            <ConfirmEmailContent />
        </Suspense>
    );
}
