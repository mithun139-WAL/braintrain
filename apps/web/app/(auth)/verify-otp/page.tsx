"use client";

import Link from "next/link";
import React, { useRef, KeyboardEvent, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "@/lib/store/auth.store";
import { useVerifyOtpMutation } from "@/hooks/mutations/useVerifyOtpMutation";
import { useRequestOtpMutation } from "@/hooks/mutations/useRequestOtpMutation";

function VerifyOtpForm() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const email = searchParams.get("email") || "";
    const phone = searchParams.get("phone") || "";
    const identifier = email || phone;
    const setAuth = useAuthStore((state) => state.setAuth);

    const inputRefs = useRef<(HTMLInputElement | null)[]>(Array(6).fill(null));
    const [error, setError] = useState<string | null>(null);

    const verifyOtpMutation = useVerifyOtpMutation();
    const requestOtpMutation = useRequestOtpMutation();

    const isLoading = verifyOtpMutation.isPending || requestOtpMutation.isPending;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        const code = inputRefs.current.map(input => input?.value || "").join("");

        if (code.length < 6) {
            setError("Please enter the full 6-digit code");
            return;
        }

        try {
            const response = await verifyOtpMutation.mutateAsync({ identifier, code });
            if (response.success && response.data) {
                const { access_token, user } = response.data as any;
                setAuth(user, access_token || "mock-jwt-token");
                router.push("/dashboard");
            } else {
                setError(response.message || "Invalid or expired OTP");
            }
        } catch (err: any) {
            setError(typeof err === "string" ? err : err.message || "An error occurred");
        }
    };

    const handleResend = async () => {
        if (!identifier) return;
        setError(null);
        try {
            const response = await requestOtpMutation.mutateAsync({ identifier });
            if (!response.success) {
                setError(response.message || "Failed to resend OTP");
            }
        } catch (err: any) {
            setError(typeof err === "string" ? err : err.message || "An error occurred");
        }
    }

    const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>, index: number) => {
        if (e.key >= "0" && e.key <= "9") {
            const input = inputRefs.current[index];
            if (input) input.value = ""; // Clear for new input
        }
        if (e.key === "Backspace") {
            const input = inputRefs.current[index];
            if (input && input.value.length === 0 && index > 0) {
                inputRefs.current[index - 1]?.focus();
                e.preventDefault();
            }
        }
    };

    const handleInput = (
        e: React.FormEvent<HTMLInputElement>,
        index: number
    ) => {
        const input = e.currentTarget;
        const val = input.value;
        if (val.length === 1 && index < 5) {
            inputRefs.current[index + 1]?.focus();
        }
    };

    return (
        <div className="w-full max-w-md bg-white dark:bg-slate-900 rounded-2xl shadow-xl border border-slate-100 dark:border-slate-800 overflow-hidden relative">
            <div className="p-8 sm:p-10">
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-6 text-primary">
                        <span className="material-symbols-outlined text-[32px]">
                            lock_reset
                        </span>
                    </div>
                    <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white mb-3 tracking-tight">
                        Verify Your Identity
                    </h1>
                    <p className="text-slate-500 dark:text-slate-400 text-base leading-relaxed">
                        We've sent a 6-digit code to{" "}
                        <span className="font-medium text-slate-700 dark:text-slate-200">
                            {identifier || "your device"}
                        </span>
                        . Enter it below to confirm your account.
                    </p>
                </div>

                {error && (
                    <div className="mb-6 p-3 bg-rose-50 border border-rose-100 text-rose-600 text-xs font-bold rounded-lg text-center animate-shake">
                        {error}
                    </div>
                )}

                <form className="space-y-8" onSubmit={handleSubmit}>
                    <div className="flex justify-center gap-2 sm:gap-3">
                        {[...Array(6)].map((_, index) => (
                            <input
                                key={index}
                                ref={(el) => { inputRefs.current[index] = el; }}
                                autoComplete="one-time-code"
                                className="w-10 h-12 sm:w-12 sm:h-14 text-center text-xl font-bold rounded-lg border-2 border-slate-200 dark:border-slate-700 bg-transparent focus:border-primary focus:ring-0 focus:outline-none transition-all placeholder-transparent text-slate-900 dark:text-white caret-primary disabled:opacity-50"
                                inputMode="numeric"
                                maxLength={1}
                                pattern="[0-9]*"
                                type="text"
                                onKeyDown={(e) => handleKeyDown(e, index)}
                                onInput={(e) => handleInput(e, index)}
                                required
                                disabled={isLoading}
                            />
                        ))}
                    </div>

                    <button
                        className="w-full flex items-center justify-center gap-2 bg-primary hover:bg-primary-dark text-white font-bold h-12 rounded-lg shadow-md shadow-primary/20 hover:shadow-primary/30 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 dark:focus:ring-offset-slate-900 disabled:bg-primary/50 disabled:cursor-not-allowed"
                        type="submit"
                        disabled={isLoading}
                    >
                        <span>{isLoading ? "Verifying..." : "Verify OTP"}</span>
                        {!isLoading && (
                            <span className="material-symbols-outlined text-[20px]">
                                arrow_forward
                            </span>
                        )}
                    </button>
                </form>

                <div className="mt-8 pt-6 border-t border-slate-100 dark:border-slate-800 flex flex-col items-center gap-3">
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                        Didn't receive the code?
                    </p>
                    <button
                        className="group flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold text-primary hover:bg-primary/10 transition-colors disabled:opacity-50"
                        onClick={handleResend}
                        disabled={isLoading || !identifier}
                    >
                        <span className="material-symbols-outlined text-[18px] group-hover:rotate-180 transition-transform duration-500">
                            refresh
                        </span>
                        Resend Code
                    </button>
                    <p className="text-xs text-slate-400 dark:text-slate-500 font-medium">
                        Resend available in 00:30
                    </p>
                </div>
            </div>

            <div className="bg-slate-50 dark:bg-slate-800/50 p-4 text-center border-t border-slate-100 dark:border-slate-800">
                <Link
                    className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 transition-colors"
                    href="/login"
                >
                    <span className="material-symbols-outlined text-[16px]">
                        arrow_back
                    </span>
                    Back to Login
                </Link>
            </div>
        </div>
    );
}

export default function VerifyOtpPage() {
    return (
        <Suspense fallback={<div className="flex h-screen w-full items-center justify-center">Loading...</div>}>
            <VerifyOtpForm />
        </Suspense>
    );
}
