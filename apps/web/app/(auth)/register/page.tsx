"use client";

import Link from "next/link";
import React, { useState } from "react";
import { useGoogleLogin } from "@react-oauth/google";
import { useAuthStore } from "@/lib/store/auth.store";
import { useRegisterMutation } from "@/hooks/mutations/useRegisterMutation";
import { useGoogleLoginMutation } from "@/hooks/mutations/useGoogleLoginMutation";
import { useRouter } from "next/navigation";

export default function RegisterPage() {
    const router = useRouter();
    const setAuth = useAuthStore((state) => state.setAuth);
    const [error, setError] = useState<string | null>(null);
    const [showPassword, setShowPassword] = useState(false);
    const [registeredEmail, setRegisteredEmail] = useState<string | null>(null);

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
            if (response.success) {
                setRegisteredEmail(email);
            } else {
                setError(response.message || "Registration failed");
            }
        } catch (err: any) {
            setError(typeof err === "string" ? err : err.message || "An error occurred during registration");
        }
    };

    const googleLogin = useGoogleLogin({
        onSuccess: async (tokenResponse) => {
            setError(null);
            try {
                const response = await googleLoginMutation.mutateAsync({
                    token: tokenResponse.access_token,
                });
                if (response.success && response.data) {
                    const { accessToken, user } = response.data as any;
                    setAuth(user, accessToken);
                    router.push("/dashboard");
                } else {
                    setError(response.message || "Google sign-up failed");
                }
            } catch (err: any) {
                setError(typeof err === "string" ? err : err.message || "Google authentication failed");
            }
        },
        onError: () => setError("Google authentication was cancelled or failed"),
    });

    // ── Check-your-email state ──────────────────────────────────────────────────
    if (registeredEmail) {
        return (
            <div className="w-full max-w-[400px] animate-fade-in group/card relative">
                {/* Ambient card shadow glow */}
                <div className="absolute -inset-0.5 bg-gradient-to-r from-emerald/20 to-teal-500/20 rounded-2xl blur-lg opacity-75 group-hover/card:opacity-100 transition duration-500" />
                
                {/* Card Container */}
                <div className="relative rounded-2xl bg-card/85 backdrop-blur-xl border border-border/80 dark:border-border/30 shadow-card overflow-hidden">
                    {/* Top gradient accent line */}
                    <div className="h-1.5 w-full bg-gradient-to-r from-emerald-500 via-teal-400 to-primary" />

                    <div className="px-6 py-6 sm:px-8 sm:py-7 text-center">
                        <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald/10 to-teal-500/10 border border-emerald/20 shadow-inner mb-3.5">
                            <span className="material-symbols-outlined text-emerald text-[22px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                                mark_email_read
                            </span>
                        </div>
                        <h1 className="font-display text-xl sm:text-2xl font-black tracking-tight text-foreground mb-1.5">
                            Check your inbox
                        </h1>
                        <p className="text-muted-foreground text-xs sm:text-sm font-medium mb-1 leading-relaxed">
                            We sent a confirmation link to
                        </p>
                        <p className="font-bold text-foreground text-xs mb-4 break-all bg-muted/30 px-2.5 py-1 rounded-lg border border-border/50 inline-block">
                            {registeredEmail}
                        </p>
                        <p className="text-muted-foreground text-xs leading-relaxed mb-5">
                            Click the link in the email to activate your account. The link expires in 24 hours.
                            Check your spam folder if you don&apos;t see it.
                        </p>
                        <div className="flex flex-col gap-3">
                            <Link
                                href="/login"
                                className="w-full flex items-center justify-center gap-2 h-10 rounded-xl bg-primary hover:bg-primary-dark text-white font-bold text-xs shadow-lg shadow-primary/20 hover:shadow-xl hover:shadow-primary/30 transition-all duration-200 active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-primary/40"
                            >
                                Back to Sign In
                            </Link>
                        </div>
                    </div>
                    <div className="px-6 py-3 bg-muted/20 border-t border-border/80 dark:border-border/30 text-center">
                        <p className="text-xs text-muted-foreground">
                            Didn&apos;t get the email?{" "}
                            <button
                                type="button"
                                className="font-semibold text-primary hover:text-primary-dark transition-colors hover:underline"
                                onClick={() => setRegisteredEmail(null)}
                            >
                                Try again
                            </button>
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    // ── Registration form ──────────────────────────────────────────────────────
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
                                person_add
                            </span>
                        </div>
                        <h1 className="font-display text-xl sm:text-2xl font-black tracking-tight text-foreground mb-1.5">
                            Create your account
                        </h1>
                        <p className="text-muted-foreground text-xs sm:text-sm font-medium">
                            Start your training journey today.
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
                                <span className="font-semibold block mb-0.5 text-foreground/90">Registration error</span>
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
                        {/* Full Name */}
                        <div className="space-y-1">
                            <label className="block text-xs font-semibold text-foreground/80" htmlFor="fullname">
                                Full Name
                            </label>
                            <div className="relative group">
                                <input
                                    id="fullname"
                                    name="fullname"
                                    type="text"
                                    placeholder="John Doe"
                                    required
                                    disabled={isLoading}
                                    className="w-full h-10 pl-9 pr-3 rounded-xl border border-border/80 dark:border-border/30 bg-background/50 hover:bg-background/80 focus:bg-background text-foreground placeholder-muted-foreground/60 text-xs focus:border-primary focus:ring-4 focus:ring-primary/10 outline-none transition-all duration-200 disabled:opacity-50"
                                />
                                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-muted-foreground group-focus-within:text-primary transition-colors">
                                    <span className="material-symbols-outlined text-[16px]">person</span>
                                </div>
                            </div>
                        </div>

                        {/* Email */}
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
                                    className="w-full h-10 pl-9 pr-3 rounded-xl border border-border/80 dark:border-border/30 bg-background/50 hover:bg-background/80 focus:bg-background text-foreground placeholder-muted-foreground/60 text-xs focus:border-primary focus:ring-4 focus:ring-primary/10 outline-none transition-all duration-200 disabled:opacity-50"
                                />
                                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-muted-foreground group-focus-within:text-primary transition-colors">
                                    <span className="material-symbols-outlined text-[16px]">mail</span>
                                </div>
                            </div>
                        </div>

                        {/* Password */}
                        <div className="space-y-1">
                            <label className="block text-xs font-semibold text-foreground/80" htmlFor="password">
                                Password
                            </label>
                            <div className="relative group">
                                <input
                                    id="password"
                                    name="password"
                                    type={showPassword ? "text" : "password"}
                                    placeholder="At least 6 characters"
                                    required
                                    minLength={6}
                                    disabled={isLoading}
                                    className="w-full h-10 pl-9 pr-9 rounded-xl border border-border/80 dark:border-border/30 bg-background/50 hover:bg-background/80 focus:bg-background text-foreground placeholder-muted-foreground/60 text-xs focus:border-primary focus:ring-4 focus:ring-primary/10 outline-none transition-all duration-200 disabled:opacity-50"
                                />
                                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-muted-foreground group-focus-within:text-primary transition-colors">
                                    <span className="material-symbols-outlined text-[16px]">lock</span>
                                </div>
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute inset-y-0 right-0 flex items-center pr-3 text-muted-foreground hover:text-foreground transition-colors"
                                    tabIndex={-1}
                                >
                                    <span className="material-symbols-outlined text-[16px]">
                                        {showPassword ? "visibility_off" : "visibility"}
                                    </span>
                                </button>
                            </div>
                        </div>

                        {/* Submit */}
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
                                    Creating account...
                                </>
                            ) : (
                                <>
                                    Create Account
                                    <span className="material-symbols-outlined text-[16px] group-hover:translate-x-0.5 transition-transform">arrow_forward</span>
                                </>
                            )}
                        </button>

                        {/* Divider */}
                        <div className="flex items-center gap-2 py-0.5">
                            <div className="h-px flex-grow bg-border/80 dark:bg-border/30" />
                            <span className="text-muted-foreground text-[9px] font-bold uppercase tracking-wider">
                                or continue with
                            </span>
                            <div className="h-px flex-grow bg-border/80 dark:bg-border/30" />
                        </div>

                        {/* Google */}
                        <button
                            type="button"
                            onClick={() => googleLogin()}
                            disabled={isLoading}
                            className="w-full flex items-center justify-center gap-2.5 h-10 rounded-xl border border-border/80 dark:border-border/30 bg-background/50 hover:bg-muted/80 dark:hover:bg-muted/30 text-foreground text-xs font-semibold transition-all duration-200 hover:border-border dark:hover:border-border/60 active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-primary/20 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <svg className="h-5 w-5 flex-shrink-0" viewBox="0 0 24 24" aria-hidden="true">
                                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.84z" fill="#FBBC05" />
                                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                            </svg>
                            Sign up with Google
                        </button>

                        {/* Terms */}
                        <p className="text-xs text-muted-foreground text-center pt-0.5 leading-relaxed">
                            By creating an account, you agree to our{" "}
                            <Link href="#" className="text-primary hover:text-primary-dark font-medium transition-colors hover:underline">
                                Terms
                            </Link>{" "}
                            and{" "}
                            <Link href="#" className="text-primary hover:text-primary-dark font-medium transition-colors hover:underline">
                                Privacy Policy
                            </Link>
                            .
                        </p>
                    </form>
                </div>

                {/* Footer */}
                <div className="px-6 py-3 bg-muted/20 border-t border-border/80 dark:border-border/30 text-center">
                    <p className="text-xs text-muted-foreground">
                        Already have an account?{" "}
                        <Link href="/login" className="font-semibold text-primary hover:text-primary-dark hover:underline transition-colors">
                            Sign In
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}
