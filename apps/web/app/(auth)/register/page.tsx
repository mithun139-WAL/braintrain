"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { identityApi } from "@/lib/api/identity.api";
import { useAuthStore } from "@/lib/store/auth.store";

export default function RegisterPage() {
    const router = useRouter();
    const setAuth = useAuthStore((state) => state.setAuth);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        const formData = new FormData(e.currentTarget);
        const name = formData.get("fullname") as string;
        const email = formData.get("email") as string;
        const password = formData.get("password") as string;

        try {
            const response = await identityApi.register({ name, email, password });
            if (response.success && response.data) {
                const { access_token, user } = response.data as any;
                setAuth(user, access_token || "mock-jwt-token");
                router.push("/dashboard");
            } else {
                setError(response.message || "Registration failed");
            }
        } catch (err: any) {
            setError(err.response?.data?.message || "An error occurred during registration");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="w-full max-w-md bg-surface-light dark:bg-surface-dark rounded-xl shadow-lg border-t-4 border-primary dark:border-primary overflow-hidden">
            <div className="px-8 pt-8 pb-8">
                <div className="text-center mb-8">
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2 tracking-tight">
                        Create an account
                    </h1>
                    <p className="text-gray-500 dark:text-gray-400 text-sm">
                        Train smarter. Perform confidently.
                    </p>
                </div>

                {error && (
                    <div className="mb-4 p-3 bg-rose-50 border border-rose-100 text-rose-600 text-xs font-bold rounded-lg animate-shake">
                        {error}
                    </div>
                )}

                <form className="space-y-5" onSubmit={handleSubmit}>
                    <div className="space-y-1.5">
                        <label
                            className="block text-sm font-semibold text-gray-700 dark:text-gray-200"
                            htmlFor="fullname"
                        >
                            Full Name
                        </label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                                <span className="material-symbols-outlined text-[20px]">
                                    person
                                </span>
                            </div>
                            <input
                                className="block w-full pl-10 pr-3 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary sm:text-sm bg-gray-50 dark:bg-gray-800 transition-colors"
                                id="fullname"
                                name="fullname"
                                placeholder="John Doe"
                                type="text"
                                required
                                disabled={isLoading}
                            />
                        </div>
                    </div>

                    <div className="space-y-1.5">
                        <label
                            className="block text-sm font-semibold text-gray-700 dark:text-gray-200"
                            htmlFor="email"
                        >
                            Email
                        </label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                                <span className="material-symbols-outlined text-[20px]">
                                    mail
                                </span>
                            </div>
                            <input
                                className="block w-full pl-10 pr-3 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary sm:text-sm bg-gray-50 dark:bg-gray-800 transition-colors"
                                id="email"
                                name="email"
                                placeholder="name@company.com"
                                type="email"
                                required
                                disabled={isLoading}
                            />
                        </div>
                    </div>

                    <div className="space-y-1.5">
                        <label
                            className="block text-sm font-semibold text-gray-700 dark:text-gray-200"
                            htmlFor="password"
                        >
                            Password
                        </label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                                <span className="material-symbols-outlined text-[20px]">
                                    lock
                                </span>
                            </div>
                            <input
                                className="block w-full pl-10 pr-3 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary sm:text-sm bg-gray-50 dark:bg-gray-800 transition-colors"
                                id="password"
                                name="password"
                                placeholder="Create a strong password"
                                type="password"
                                required
                                disabled={isLoading}
                            />
                        </div>
                    </div>

                    <button
                        className="w-full group flex justify-center items-center gap-2 py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-bold text-white bg-primary hover:bg-primary-dark disabled:bg-primary/50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary transition-all duration-200"
                        type="submit"
                        disabled={isLoading}
                    >
                        {isLoading ? "Creating account..." : "Create Account"}
                        {!isLoading && (
                            <span className="material-symbols-outlined text-lg group-hover:translate-x-1 transition-transform">
                                arrow_forward
                            </span>
                        )}
                    </button>

                    <div className="relative py-2">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-gray-200 dark:border-gray-700"></div>
                        </div>
                        <div className="relative flex justify-center text-sm">
                            <span className="px-2 bg-white dark:bg-surface-dark text-gray-500 text-xs uppercase tracking-wider font-semibold">
                                Or register with
                            </span>
                        </div>
                    </div>

                    <button
                        className="w-full flex items-center justify-center px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm bg-white dark:bg-gray-800 text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-200 transition-colors"
                        type="button"
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

                    <div className="flex items-center justify-center text-sm text-center pt-2">
                        <div className="text-gray-500">
                            Already have an account?{" "}
                            <Link
                                className="font-semibold text-primary hover:text-primary-hover transition-colors"
                                href="/login"
                            >
                                Sign In
                            </Link>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    );
}
