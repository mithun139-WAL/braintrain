"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { useUiStore } from "@/lib/store/ui.store";

export function Hero() {
    const { openModal } = useUiStore();
    return (
        <section className="relative mx-auto max-w-4xl px-6 py-20 text-center lg:px-8 lg:py-32">
            {/* Headline */}
            <h1 className="text-display-xl font-semibold tracking-tight text-foreground sm:text-display-2xl">
                Practice interviews like they’re real.
            </h1>

            {/* Subtext */}
            <p className="mx-auto mt-6 max-w-xl text-body-md text-muted-foreground leading-relaxed">
                Build confidence through realistic AI-powered interview simulations. 
                Experience realistic scenarios, compose your thoughts, and improve without pressure.
            </p>

            {/* CTAs */}
            <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
                <Link
                    href="/register"
                    className="flex h-11 items-center justify-center gap-1.5 rounded-lg bg-primary px-6 text-[13px] font-semibold text-white shadow-sm hover:brightness-105 transition-all"
                >
                    Start Practice
                    <ArrowRight size={14} className="text-white/80" />
                </Link>
                <button
                    onClick={() => openModal("demo")}
                    className="flex h-11 items-center justify-center rounded-lg border border-border bg-card px-6 text-[13px] font-semibold text-foreground hover:bg-muted/50 transition-all dark:bg-transparent"
                >
                    See How It Works
                </button>
            </div>

            {/* Subtle product preview */}
            <div className="mt-16 overflow-hidden rounded-xl border border-border bg-card/50 p-2 shadow-sm">
                <div className="rounded-lg border border-border/60 bg-background overflow-hidden aspect-video flex flex-col">
                    {/* Simplified mock UI header */}
                    <div className="border-b border-border/60 px-4 py-2.5 flex items-center justify-between bg-muted/20">
                        <div className="flex items-center gap-1.5">
                            <span className="size-2 rounded-full bg-border" />
                            <span className="size-2 rounded-full bg-border" />
                            <span className="size-2 rounded-full bg-border" />
                        </div>
                        <span className="text-[10px] font-medium text-muted-foreground tracking-wide uppercase">Mock Preparation Room</span>
                        <div className="w-12" />
                    </div>
                    {/* Simulated calm interview environment */}
                    <div className="flex-1 flex flex-col items-center justify-center p-6 bg-background">
                        <div className="max-w-md w-full text-center space-y-4">
                            <div className="size-16 rounded-full bg-primary/10 text-primary flex items-center justify-center mx-auto">
                                <span className="text-lg font-bold">AI</span>
                            </div>
                            <p className="text-xs text-muted-foreground italic">
                                "Tell me about a time you had to resolve a high-pressure technical challenge under tight constraints."
                            </p>
                            <div className="flex justify-center gap-2">
                                <span className="h-1.5 w-1.5 rounded-full bg-primary/40 animate-pulse" />
                                <span className="h-1.5 w-1.5 rounded-full bg-primary/40 animate-pulse [animation-delay:0.2s]" />
                                <span className="h-1.5 w-1.5 rounded-full bg-primary/40 animate-pulse [animation-delay:0.4s]" />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
