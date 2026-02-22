"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { identityApi } from "@/lib/api/identity.api";

export default function EmailOtpRequestPage() {
    const router = useRouter();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        const formData = new FormData(e.currentTarget);
        const email = formData.get("email") as string;

        try {
            const response = await identityApi.requestOtp(email);
            if (response.success) {
                router.push(`/verify-otp?email=${encodeURIComponent(email)}`);
            } else {
                setError(response.message || "Failed to request OTP");
            }
        } catch (err: any) {
            setError(err.response?.data?.message || "An error occurred");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="w-full max-w-[400px] bg-surface-light dark:bg-surface-dark shadow-[0_8px_30px_rgb(0,0,0,0.04)] rounded-lg overflow-hidden border border-slate-200 dark:border-slate-700">
            <div className="h-1.5 w-full bg-primary"></div>
            <div className="p-8">
                <div className="mb-8 text-center">
                    <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
                        Sign in with OTP
                    </h1>
                    <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                        Enter your registered email address to receive a secure one-time password.
                    </p>
                </div>

                {error && (
                    <div className="mb-4 p-3 bg-rose-50 border border-rose-100 text-rose-600 text-xs font-bold rounded-lg">
                        {error}
                    </div>
                )}

                <form className="flex flex-col gap-5" onSubmit={handleSubmit}>
                    <div className="space-y-1.5">
                        <label
                            className="block text-sm font-semibold text-slate-700 dark:text-slate-300"
                            htmlFor="email"
                        >
                            Email address
                        </label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <span className="material-symbols-outlined text-slate-400 text-[20px]">
                                    mail
                                </span>
                            </div>
                            <input
                                className="w-full pl-10 pr-4 py-2.5 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all sm:text-sm disabled:opacity-50"
                                id="email"
                                name="email"
                                placeholder="name@company.com"
                                required
                                type="email"
                                disabled={isLoading}
                            />
                        </div>
                    </div>

                    <button
                        className="flex items-center justify-center w-full py-2.5 px-4 rounded-lg bg-primary hover:bg-primary-hover text-white font-semibold shadow-sm transition-all active:scale-[0.98] gap-2 disabled:bg-primary/50 disabled:cursor-not-allowed"
                        disabled={isLoading}
                    >
                        <span>{isLoading ? "Requesting..." : "Request OTP"}</span>
                        {!isLoading && (
                            <span className="material-symbols-outlined text-[18px]">
                                arrow_forward
                            </span>
                        )}
                    </button>

                    <div className="text-center pt-2">
                        <Link
                            className="inline-flex items-center text-sm font-medium text-slate-500 hover:text-primary dark:text-slate-400 dark:hover:text-primary transition-colors"
                            href="/login"
                        >
                            Back to Login
                        </Link>
                    </div>
                </form>
            </div>
        </div>
    );
}
