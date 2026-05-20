"use client";

import Link from "next/link";
import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/store/auth.store";
import { useRegisterMutation } from "@/hooks/mutations/useRegisterMutation";
import { useGoogleLoginMutation } from "@/hooks/mutations/useGoogleLoginMutation";

export default function RegisterPage() {
    const router = useRouter();
    const setAuth = useAuthStore((state) => state.setAuth);
    const [error, setError] = useState<string | null>(null);

    const registerMutation = useRegisterMutation();
    const googleLoginMutation = useGoogleLoginMutation();

    const isLoading = registerMutation.isPending || googleLoginMutation.isPending;

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setError(null);

        const formData = new FormData(e.currentTarget);
        const name = formData.get("fullname") as string;
        const email = formData.get("email") as string;
        const password = formData.get("password") as string;

        try {
            const response = await registerMutation.mutateAsync({ name, email, password });
            if (response.success && response.data) {
                const { accessToken, user } = response.data as any;
                setAuth(user, accessToken);
                router.push("/dashboard");
            } else {
                setError(response.message || "Registration failed");
            }
        } catch (err: any) {
            setError(typeof err === "string" ? err : err.message || "An error occurred during registration");
        }
    };

    const handleGoogleRegister = async () => {
        setError(null);
        try {
            const mockToken = "mock_google_token_" + Date.now();
            const response = await googleLoginMutation.mutateAsync({ token: mockToken });

            if (response.success && response.data) {
                const { accessToken, user } = response.data as any;
                setAuth(user, accessToken);
                router.push("/dashboard");
            } else {
                setError(response.message || "Google registration failed");
            }
        } catch (err: any) {
            setError(typeof err === "string" ? err : err.message || "Google authentication failed");
        }
    };

    return (
        <div className="w-full max-w-md bg-white dark:bg-slate-900 rounded-2xl shadow-xl border border-slate-100 dark:border-slate-800 overflow-hidden relative">
            <div className="p-8 sm:p-10">
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-6 text-primary">
                        <span className="material-symbols-outlined text-[32px]">
                            person_add
                        </span>
                    </div>
                    <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white mb-3 tracking-tight">
                        Create an account
                    </h1>
                    <p className="text-slate-500 dark:text-slate-400 text-base leading-relaxed">
                        Train smarter. Perform confidently.
                    </p>
                </div>

                {error && (
                    <div className="mb-4 p-3 bg-rose-50 border border-rose-100 text-rose-600 text-xs font-bold rounded-lg animate-shake">
                        {error}
                    </div>
                )}

                <form className="space-y-5" onSubmit={handleSubmit}>
                    <div className="space-y-2">
                        <label
                            className="block text-sm font-semibold text-slate-700 dark:text-slate-300"
                            htmlFor="fullname"
                        >
                            Full Name
                        </label>
                        <div className="relative group">
                            <input
                                className="w-full pl-10 pr-4 py-3 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all disabled:opacity-50"
                                id="fullname"
                                name="fullname"
                                placeholder="John Doe"
                                type="text"
                                required
                                disabled={isLoading}
                            />
                            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400 group-focus-within:text-primary transition-colors">
                                <span className="material-symbols-outlined text-[20px]">
                                    person
                                </span>
                            </div>
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label
                            className="block text-sm font-semibold text-slate-700 dark:text-slate-300"
                            htmlFor="email"
                        >
                            Email
                        </label>
                        <div className="relative group">
                            <input
                                className="w-full pl-10 pr-4 py-3 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all disabled:opacity-50"
                                id="email"
                                name="email"
                                placeholder="name@company.com"
                                type="email"
                                required
                                disabled={isLoading}
                            />
                            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400 group-focus-within:text-primary transition-colors">
                                <span className="material-symbols-outlined text-[20px]">
                                    mail
                                </span>
                            </div>
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label
                            className="block text-sm font-semibold text-slate-700 dark:text-slate-300"
                            htmlFor="password"
                        >
                            Password
                        </label>
                        <div className="relative group">
                            <input
                                className="w-full pl-10 pr-4 py-3 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all disabled:opacity-50"
                                id="password"
                                name="password"
                                placeholder="Create a strong password"
                                type="password"
                                required
                                disabled={isLoading}
                            />
                            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400 group-focus-within:text-primary transition-colors">
                                <span className="material-symbols-outlined text-[20px]">
                                    lock
                                </span>
                            </div>
                        </div>
                    </div>

                    <button
                        className="w-full flex items-center justify-center gap-2 bg-primary hover:bg-primary-dark text-white font-bold h-12 rounded-lg shadow-md shadow-primary/20 hover:shadow-primary/30 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 dark:focus:ring-offset-slate-900 mt-2 disabled:bg-primary/50 disabled:cursor-not-allowed"
                        type="submit"
                        disabled={isLoading}
                    >
                        <span>{isLoading ? "Creating account..." : "Create Account"}</span>
                        {!isLoading && (
                            <span className="material-symbols-outlined text-[20px]">
                                arrow_forward
                            </span>
                        )}
                    </button>

                    <div className="relative py-4">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-slate-200 dark:border-slate-700"></div>
                        </div>
                        <div className="relative flex justify-center text-sm">
                            <span className="px-2 bg-white dark:bg-slate-900 text-slate-500 font-semibold tracking-wider">
                                Or register with
                            </span>
                        </div>
                    </div>

                    <button
                        className="w-full flex items-center justify-center px-4 py-2.5 border border-slate-300 dark:border-slate-700 rounded-lg shadow-sm bg-white dark:bg-slate-800 text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-200 transition-colors disabled:opacity-50"
                        type="button"
                        onClick={handleGoogleRegister}
                    >
                        <svg
                            aria-hidden="true"
                            className="h-5 w-5 mr-2"
                            viewBox="0 0 24 24"
                        >
                            <path
                                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                                fill="#4285F4"
                            ></path>
                            <path
                                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                                fill="#34A853"
                            ></path>
                            <path
                                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.84z"
                                fill="#FBBC05"
                            ></path>
                            <path
                                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                                fill="#EA4335"
                            ></path>
                        </svg>
                        Sign up with Google
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
                <p className="text-sm text-slate-500 dark:text-slate-400">
                    Already have an account?{" "}
                    <Link
                        className="font-semibold text-primary hover:text-primary-dark transition-colors"
                        href="/login"
                    >
                        Sign In
                    </Link>
                </p>
            </div>
        </div>
    );
}
