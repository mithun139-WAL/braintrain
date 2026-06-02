"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuthStore } from "@/lib/store/auth.store";
import { useUiStore } from "@/lib/store/ui.store";
import { Logo } from "@/components/ui/Logo";

export function Header() {
    const { isAuthenticated, logout, hasHydrated } = useAuthStore();
    const { openModal } = useUiStore();
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    const isUserLoggedIn = mounted && hasHydrated && isAuthenticated;

    return (
        <header className="fixed top-0 z-50 w-full border-b border-slate-200/60 bg-white/80 backdrop-blur-md dark:border-slate-800/60 dark:bg-background-dark/80">
            <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 lg:px-12">
                <Link href="/" className="transition-opacity hover:opacity-90">
                    <Logo />
                </Link>
                
                <nav className="hidden md:flex items-center gap-10">
                    <button
                        onClick={() => openModal("demo")}
                        className="text-sm font-semibold text-slate-600 hover:text-primary transition-colors dark:text-slate-300"
                    >
                        Product
                    </button>
                    <a
                        className="text-sm font-semibold text-slate-600 hover:text-primary transition-colors dark:text-slate-300"
                        href="#features"
                    >
                        Features
                    </a>
                    <a
                        className="text-sm font-semibold text-slate-600 hover:text-primary transition-colors dark:text-slate-300"
                        href="#how-it-works"
                    >
                        How It Works
                    </a>
                    <a
                        className="text-sm font-semibold text-slate-600 hover:text-primary transition-colors dark:text-slate-300"
                        href="#pricing"
                    >
                        Pricing
                    </a>
                </nav>

                <div className="flex items-center gap-4">
                    {isUserLoggedIn ? (
                        <>
                            <Link
                                href="/dashboard"
                                className="flex items-center justify-center rounded-lg bg-primary px-6 py-2.5 text-sm font-bold text-white shadow-lg shadow-primary/20 hover:brightness-110 active:scale-95 transition-all"
                            >
                                Go to Dashboard
                            </Link>
                            <button
                                onClick={() => logout()}
                                className="text-sm font-bold text-slate-600 dark:text-slate-300 hover:text-primary dark:hover:text-primary transition-colors"
                            >
                                Sign Out
                            </button>
                        </>
                    ) : (
                        <>
                            <Link
                                href="/login"
                                className="hidden lg:block text-sm font-bold text-charcoal dark:text-white hover:opacity-70 transition-opacity"
                            >
                                Login
                            </Link>
                            <Link
                                href="/register"
                                className="flex items-center justify-center rounded-lg bg-primary px-6 py-2.5 text-sm font-bold text-white shadow-lg shadow-primary/20 hover:brightness-110 active:scale-95 transition-all"
                            >
                                Get Started
                            </Link>
                        </>
                    )}
                </div>
            </div>
        </header>
    );
}
