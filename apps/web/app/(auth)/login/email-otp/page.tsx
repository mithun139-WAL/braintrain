"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import React, { useState } from "react";
import { useRequestOtpMutation } from "@/hooks/mutations/useRequestOtpMutation";

export default function EmailOtpRequestPage() {
    const router = useRouter();
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);
    const [sentEmail, setSentEmail] = useState("");
    const requestOtpMutation = useRequestOtpMutation();

    const isLoading = requestOtpMutation.isPending;

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setError(null);

        const formData = new FormData(e.currentTarget);
        const email = formData.get("email") as string;

        try {
            const response = await requestOtpMutation.mutateAsync({ identifier: email });
            if (response.success) {
                setSentEmail(email);
                setSuccess(true);
                router.push(`/verify-otp?email=${encodeURIComponent(email)}`);
            } else {
                setError(response.message || "Failed to send OTP. Please try again.");
            }
        } catch (err: any) {
            setError(typeof err === "string" ? err : err.message || "An error occurred");
        }
    };

    return (
        <div className="w-full max-w-[400px] animate-fade-in group/card relative">
            {/* Ambient card shadow glow */}
            <div className="absolute -inset-0.5 bg-gradient-to-r from-primary/25 to-violet-500/25 rounded-2xl blur-lg opacity-75 group-hover/card:opacity-100 transition duration-500" />
            
            {/* Card Container */}
            <div className="relative rounded-2xl bg-card/85 backdrop-blur-xl border border-border/80 dark:border-border/30 shadow-card overflow-hidden">
                {/* Top gradient accent line */}
                <div className="h-1.5 w-full bg-gradient-to-r from-primary via-sky-400 to-violet-500" />

                {/* Card body */}
                <div className="px-6 py-6 sm:px-8 sm:py-7">
                    {/* Header */}
                    <div className="text-center mb-5">
                        <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-br from-primary/10 to-violet-500/10 border border-primary/20 shadow-inner mb-3.5">
                            <span className="material-symbols-outlined text-primary text-[22px] drop-shadow-sm" style={{ fontVariationSettings: "'FILL' 1" }}>
                                mark_email_unread
                            </span>
                        </div>
                        <h1 className="font-display text-xl sm:text-2xl font-black tracking-tight text-foreground mb-1.5">
                            Sign in with OTP
                        </h1>
                        <p className="text-muted-foreground text-xs sm:text-sm font-medium leading-relaxed">
                            Enter your email and we&apos;ll send a 6-digit code to sign you in — no password needed.
                        </p>
                    </div>

                    {/* Error banner */}
                    {error && (
                        <div className="mb-4.5 flex items-start gap-3 p-3 rounded-2xl bg-gradient-to-r from-ruby/12 to-ruby/4 dark:from-ruby/10 dark:to-transparent backdrop-blur-md border border-ruby/30 dark:border-ruby/20 text-ruby text-xs font-medium shadow-md shadow-ruby/5 animate-fade-in relative overflow-hidden group">
                            <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-ruby to-rose-500" />
                            <span className="material-symbols-outlined text-ruby text-[18px] flex-shrink-0 mt-0.5 select-none drop-shadow-[0_2px_4px_rgba(var(--ruby),0.2)] animate-pulse" style={{ fontVariationSettings: "'FILL' 1" }}>
                                error
                            </span>
                            <div className="flex-grow pr-5 leading-relaxed">
                                <span className="font-semibold block mb-0.5 text-foreground/90">Request error</span>
                                <span className="text-ruby/90 dark:text-ruby/95 font-medium">{error}</span>
                            </div>
                            <button
                                type="button"
                                onClick={() => setError(null)}
                                className="absolute top-2.5 right-2.5 text-ruby/60 hover:text-ruby p-1 rounded-lg hover:bg-ruby/10 transition-colors"
                            >
                                <span className="material-symbols-outlined text-[15px] block">close</span>
                            </button>
                        </div>
                    )}

                    <form className="space-y-3.5" onSubmit={handleSubmit}>
                        <div className="space-y-1">
                            <label className="block text-xs font-semibold text-foreground/80" htmlFor="email">
                                Email Address
                            </label>
                            <div className="relative group">
                                <input
                                    id="email"
                                    name="email"
                                    type="email"
                                    placeholder="you@example.com"
                                    required
                                    disabled={isLoading}
                                    autoFocus
                                    className="w-full h-10 pl-9 pr-3 rounded-xl border border-border/80 dark:border-border/30 bg-background/50 hover:bg-background/80 focus:bg-background text-foreground placeholder-muted-foreground/60 text-xs focus:border-primary focus:ring-4 focus:ring-primary/10 outline-none transition-all duration-200 disabled:opacity-50"
                                />
                                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-muted-foreground group-focus-within:text-primary transition-colors">
                                    <span className="material-symbols-outlined text-[16px]">mail</span>
                                </div>
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full flex items-center justify-center gap-2 h-10 rounded-xl bg-primary hover:bg-primary-dark text-white font-bold text-xs shadow-lg shadow-primary/20 hover:shadow-xl hover:shadow-primary/30 transition-all duration-200 active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-primary/40 focus:ring-offset-2 focus:ring-offset-card disabled:opacity-50 disabled:cursor-not-allowed mt-1"
                        >
                            {isLoading ? (
                                <>
                                    <svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24" fill="none">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                    </svg>
                                    Sending code...
                                </>
                            ) : (
                                <>
                                    Send OTP Code
                                    <span className="material-symbols-outlined text-[16px] group-hover:translate-x-0.5 transition-transform">arrow_forward</span>
                                </>
                            )}
                        </button>
                    </form>

                    {/* Info note */}
                    <div className="mt-4 flex items-start gap-2 px-3 py-2.5 rounded-xl bg-muted/20 border border-border/80 dark:border-border/30">
                        <span className="material-symbols-outlined text-muted-foreground text-[14px] mt-0.5 flex-shrink-0">info</span>
                        <p className="text-xs text-muted-foreground leading-relaxed">
                            The code expires in <strong className="text-foreground/80 font-semibold">2 minutes</strong>. Make sure to enter it quickly after receiving.
                        </p>
                    </div>
                </div>

                {/* Footer */}
                <div className="px-6 py-3 bg-muted/20 border-t border-border/80 dark:border-border/30 text-center">
                    <Link
                        href="/login"
                        className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground hover:underline transition-colors font-medium"
                    >
                        <span className="material-symbols-outlined text-[14px]">arrow_back</span>
                        Back to Sign In
                    </Link>
                </div>
            </div>
        </div>
    );
}
