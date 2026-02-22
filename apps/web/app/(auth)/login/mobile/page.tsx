"use client";

import Link from "next/link";
import React, { useState } from "react";
import { useRouter } from "next/navigation";

import { useRequestOtpMutation } from "@/hooks/mutations/useRequestOtpMutation";

export default function MobileLoginPage() {
    const router = useRouter();
    const [error, setError] = useState<string | null>(null);
    const requestOtpMutation = useRequestOtpMutation();

    const isLoading = requestOtpMutation.isPending;

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setError(null);

        const formData = new FormData(e.currentTarget);
        const countryCode = formData.get("country-code") as string;
        const mobileNumber = formData.get("mobile-number") as string;
        const identifier = `${countryCode}${mobileNumber}`;

        try {
            const response = await requestOtpMutation.mutateAsync({ identifier });
            if (response.success) {
                router.push(`/verify-otp?phone=${encodeURIComponent(identifier)}`);
            } else {
                setError(response.message || "Failed to request OTP");
            }
        } catch (err: any) {
            setError(typeof err === "string" ? err : err.message || "An error occurred");
        }
    };

    return (
        <div className="w-full max-w-md bg-white dark:bg-slate-900 rounded-2xl shadow-xl border border-slate-100 dark:border-slate-800 overflow-hidden relative">
            <div className="p-8 sm:p-10">
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-6 text-primary">
                        <span className="material-symbols-outlined text-[32px]">
                            smartphone
                        </span>
                    </div>
                    <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white mb-3 tracking-tight">
                        Mobile Login
                    </h1>
                    <p className="text-slate-500 dark:text-slate-400 text-base leading-relaxed">
                        Enter your mobile number to receive a secure code.
                    </p>
                </div>
                <form className="space-y-6" onSubmit={handleSubmit}>
                    {error && (
                        <div className="mb-4 p-3 bg-rose-50 border border-rose-100 text-rose-600 text-xs font-bold rounded-lg animate-shake text-center">
                            {error}
                        </div>
                    )}

                    <div className="space-y-2">
                        <label
                            className="block text-sm font-semibold text-slate-700 dark:text-slate-300"
                            htmlFor="mobile-number"
                        >
                            Mobile Number
                        </label>
                        <div className="flex gap-3">
                            <div className="relative w-1/3">
                                <select
                                    name="country-code"
                                    disabled={isLoading}
                                    className="appearance-none w-full pl-3 pr-8 py-3 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all font-medium disabled:opacity-50"
                                >
                                    <option value="+1">+1 (US)</option>
                                    <option value="+44">+44 (UK)</option>
                                    <option value="+61">+61 (AU)</option>
                                    <option value="+91">+91 (IN)</option>
                                    <option value="+81">+81 (JP)</option>
                                </select>
                                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-500 dark:text-slate-400">
                                    <span className="material-symbols-outlined text-[20px]">
                                        expand_more
                                    </span>
                                </div>
                            </div>
                            <div className="relative flex-1">
                                <input
                                    className="w-full pl-10 pr-4 py-3 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all disabled:opacity-50"
                                    id="mobile-number"
                                    name="mobile-number"
                                    placeholder="555-0123"
                                    type="tel"
                                    required
                                    disabled={isLoading}
                                />
                                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
                                    <span className="material-symbols-outlined text-[20px]">
                                        call
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        <input
                            className="w-4 h-4 text-primary border-slate-300 rounded focus:ring-primary focus:ring-offset-0 bg-white dark:bg-slate-800 dark:border-slate-700"
                            id="remember"
                            type="checkbox"
                        />
                        <label
                            className="text-sm text-slate-600 dark:text-slate-400 select-none cursor-pointer"
                            htmlFor="remember"
                        >
                            Remember this device
                        </label>
                    </div>

                    <button
                        className="w-full flex items-center justify-center gap-2 bg-primary hover:bg-primary-dark text-white font-bold h-12 rounded-lg shadow-md shadow-primary/20 hover:shadow-primary/30 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 dark:focus:ring-offset-slate-900 mt-2 disabled:bg-primary/50 disabled:cursor-not-allowed"
                        type="submit"
                        disabled={isLoading}
                    >
                        <span>{isLoading ? "Requesting..." : "Request OTP"}</span>
                        {!isLoading && (
                            <span className="material-symbols-outlined text-[20px]">
                                arrow_forward
                            </span>
                        )}
                    </button>
                </form>

                <div className="mt-8 text-center">
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                        By continuing, you agree to our{" "}
                        <Link
                            className="text-primary dark:text-primary hover:text-primary-dark font-medium transition-colors"
                            href="#"
                        >
                            Terms of Service
                        </Link>{" "}
                        and{" "}
                        <Link
                            className="text-primary dark:text-primary hover:text-primary-dark font-medium transition-colors"
                            href="#"
                        >
                            Privacy Policy
                        </Link>
                        .
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
        </div >
    );
}
