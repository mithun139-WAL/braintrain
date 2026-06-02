"use client";

import Link from "next/link";
import React, { useRef, KeyboardEvent, useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "@/lib/store/auth.store";
import { useVerifyOtpMutation } from "@/hooks/mutations/useVerifyOtpMutation";
import { useRequestOtpMutation } from "@/hooks/mutations/useRequestOtpMutation";

const RESEND_COOLDOWN = 30;

function VerifyOtpForm() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const email = searchParams.get("email") || "";
    const identifier = email;
    const setAuth = useAuthStore((state) => state.setAuth);

    const inputRefs = useRef<(HTMLInputElement | null)[]>(Array(6).fill(null));
    const [error, setError] = useState<string | null>(null);
    const [cooldown, setCooldown] = useState(RESEND_COOLDOWN);
    const [resendSuccess, setResendSuccess] = useState(false);

    const verifyOtpMutation = useVerifyOtpMutation();
    const requestOtpMutation = useRequestOtpMutation();

    const isLoading = verifyOtpMutation.isPending || requestOtpMutation.isPending;

    // Countdown timer
    useEffect(() => {
        if (cooldown <= 0) return;
        const timer = setTimeout(() => setCooldown((c) => c - 1), 1000);
        return () => clearTimeout(timer);
    }, [cooldown]);

    const formatTime = (s: number) => {
        const m = Math.floor(s / 60);
        const sec = s % 60;
        return `${m.toString().padStart(2, "0")}:${sec.toString().padStart(2, "0")}`;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setResendSuccess(false);

        const code = inputRefs.current.map((input) => input?.value || "").join("");

        if (code.length < 6) {
            setError("Please enter all 6 digits");
            return;
        }

        try {
            const response = await verifyOtpMutation.mutateAsync({ identifier, code });
            if (response.success && response.data) {
                const { accessToken, user } = response.data as any;
                setAuth(user, accessToken);
                router.push("/dashboard");
            } else {
                setError(response.message || "Invalid or expired code. Please try again.");
                // Clear inputs on error
                inputRefs.current.forEach((input) => {
                    if (input) input.value = "";
                });
                inputRefs.current[0]?.focus();
            }
        } catch (err: any) {
            setError(typeof err === "string" ? err : err.message || "An error occurred");
            inputRefs.current.forEach((input) => {
                if (input) input.value = "";
            });
            inputRefs.current[0]?.focus();
        }
    };

    const handleResend = async () => {
        if (!identifier || cooldown > 0 || isLoading) return;
        setError(null);
        setResendSuccess(false);
        try {
            const response = await requestOtpMutation.mutateAsync({ identifier });
            if (response.success) {
                setCooldown(RESEND_COOLDOWN);
                setResendSuccess(true);
                inputRefs.current.forEach((input) => {
                    if (input) input.value = "";
                });
                inputRefs.current[0]?.focus();
            } else {
                setError(response.message || "Failed to resend code");
            }
        } catch (err: any) {
            setError(typeof err === "string" ? err : err.message || "An error occurred");
        }
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>, index: number) => {
        if (e.key >= "0" && e.key <= "9") {
            const input = inputRefs.current[index];
            if (input) input.value = "";
        }
        if (e.key === "Backspace") {
            const input = inputRefs.current[index];
            if (input && input.value.length === 0 && index > 0) {
                inputRefs.current[index - 1]?.focus();
                e.preventDefault();
            }
        }
        if (e.key === "ArrowLeft" && index > 0) {
            inputRefs.current[index - 1]?.focus();
        }
        if (e.key === "ArrowRight" && index < 5) {
            inputRefs.current[index + 1]?.focus();
        }
    };

    const handleInput = (e: React.FormEvent<HTMLInputElement>, index: number) => {
        const input = e.currentTarget;
        const val = input.value.replace(/\D/g, "");
        input.value = val.slice(-1); // keep only last digit
        if (val.length >= 1 && index < 5) {
            inputRefs.current[index + 1]?.focus();
        }
    };

    const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
        e.preventDefault();
        const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
        pasted.split("").forEach((char, i) => {
            if (inputRefs.current[i]) {
                inputRefs.current[i]!.value = char;
            }
        });
        const nextEmpty = Math.min(pasted.length, 5);
        inputRefs.current[nextEmpty]?.focus();
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
                                verified
                            </span>
                        </div>
                        <h1 className="font-display text-xl sm:text-2xl font-black tracking-tight text-foreground mb-1.5">
                            Enter verification code
                        </h1>
                        <p className="text-muted-foreground text-xs sm:text-sm font-medium leading-relaxed">
                            We sent a 6-digit code to{" "}
                            <span className="font-bold text-foreground">
                                {identifier || "your email"}
                            </span>
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
                                <span className="font-semibold block mb-0.5 text-foreground/90">Verification error</span>
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

                    {/* Resend success */}
                    {resendSuccess && (
                        <div className="mb-4 flex items-center gap-2 py-2 px-3 rounded-lg bg-emerald/10 border border-emerald/20 text-emerald text-xs animate-fade-in">
                            <span className="material-symbols-outlined text-[14px] flex-shrink-0" style={{ fontVariationSettings: "'FILL' 1" }}>
                                check_circle
                            </span>
                            <span>New code sent! Check your inbox.</span>
                        </div>
                    )}

                    <form className="space-y-4" onSubmit={handleSubmit}>
                        {/* OTP inputs */}
                        <div className="flex justify-center gap-2">
                            {[...Array(6)].map((_, index) => (
                                <input
                                    key={index}
                                    ref={(el) => { inputRefs.current[index] = el; }}
                                    autoComplete={index === 0 ? "one-time-code" : "off"}
                                    className="w-10 h-11 sm:w-11 sm:h-12 text-center text-lg font-bold rounded-xl border border-border/80 dark:border-border/30 bg-background/50 hover:bg-background/80 focus:bg-background text-foreground placeholder-muted-foreground/60 focus:border-primary focus:ring-4 focus:ring-primary/10 outline-none transition-all duration-200 disabled:opacity-50"
                                    inputMode="numeric"
                                    maxLength={1}
                                    pattern="[0-9]*"
                                    type="text"
                                    onKeyDown={(e) => handleKeyDown(e, index)}
                                    onInput={(e) => handleInput(e, index)}
                                    onPaste={handlePaste}
                                    required
                                    disabled={isLoading}
                                />
                            ))}
                        </div>

                        {/* Verify button */}
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
                                    Verifying...
                                </>
                            ) : (
                                <>
                                    Verify & Sign In
                                    <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
                                </>
                            )}
                        </button>
                    </form>

                    {/* Resend section */}
                    <div className="mt-4 pt-3.5 border-t border-border/80 dark:border-border/30 flex flex-col items-center gap-1.5">
                        <p className="text-xs text-muted-foreground font-medium">
                            Didn&apos;t receive the code?
                        </p>
                        {cooldown > 0 ? (
                            <p className="text-xs text-muted-foreground font-medium">
                                Resend available in{" "}
                                <span className="font-bold text-foreground tabular">{formatTime(cooldown)}</span>
                            </p>
                        ) : (
                            <button
                                type="button"
                                onClick={handleResend}
                                disabled={isLoading}
                                className="flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-semibold text-primary hover:bg-primary/10 hover:text-primary-dark transition-all duration-200 disabled:opacity-50"
                            >
                                <span className="material-symbols-outlined text-[14px]">refresh</span>
                                Resend Code
                            </button>
                        )}
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

export default function VerifyOtpPage() {
    return (
        <Suspense fallback={
            <div className="w-full max-w-[420px] relative">
                <div className="absolute -inset-0.5 bg-gradient-to-r from-primary/25 to-violet-500/25 rounded-2xl blur-lg opacity-75" />
                <div className="relative rounded-2xl bg-card border border-border/80 dark:border-border/30 shadow-card h-80 animate-pulse" />
            </div>
        }>
            <VerifyOtpForm />
        </Suspense>
    );
}
