
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Brain, Sparkles, X } from "lucide-react";
import { cn } from "@/lib/utils";
import {
    dashboardNavigation,
    isDashboardItemActive,
    START_SESSION_HREF,
} from "@/core/components/layout/dashboard/navigation";
import { buttonStyles } from "@/core/components/ui/button";

interface SidebarProps {
    className?: string;
    onNavigate?: () => void;
    onClose?: () => void;
}

export function Sidebar({ className, onNavigate, onClose }: SidebarProps) {
    const pathname = usePathname();

    return (
        <aside
            className={cn(
                "flex h-full w-[18rem] flex-shrink-0 flex-col border-r border-border/80 bg-card/80 backdrop-blur-xl",
                className
            )}
        >
            <div className="flex items-center gap-3 border-b border-border/80 px-5 py-5 flex-shrink-0">
                <div className="flex items-center justify-center size-10 rounded-2xl bg-primary text-primary-foreground shadow-primary-sm flex-shrink-0">
                    <Brain size={18} />
                </div>
                <div className="min-w-0 flex-1">
                    <h1 className="text-foreground text-sm font-bold leading-none tracking-tight">
                        BrainTrain
                    </h1>
                    <p className="mt-1 text-[11px] font-medium text-muted-foreground leading-relaxed">
                        Your AI-native interview mentor.
                    </p>
                </div>
                {onClose ? (
                    <button
                        type="button"
                        onClick={onClose}
                        className="rounded-xl p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground xl:hidden"
                        aria-label="Close navigation"
                    >
                        <X size={16} />
                    </button>
                ) : null}
            </div>
            <nav className="flex-1 overflow-y-auto px-3 py-4 flex flex-col gap-6 custom-scrollbar">
                {dashboardNavigation.map((section) => (
                    <div key={section.label} className="flex flex-col gap-2">
                        <p className="px-3 text-[10px] font-semibold uppercase tracking-[0.22em] text-muted-foreground/70">
                            {section.label}
                        </p>
                        {section.items.map((item) => {
                            const isActive = isDashboardItemActive(item, pathname);

                            return (
                                <Link
                                    key={item.name}
                                    href={item.href}
                                        onClick={onNavigate}
                                        className={cn(
                                            "group rounded-3xl border px-3.5 py-3 transition-all duration-200",
                                            isActive
                                            ? "border-primary/20 bg-primary/10 shadow-card"
                                            : "border-transparent hover:border-border hover:bg-muted/40"
                                    )}
                                >
                                    <div className="flex items-start gap-3">
                                        <div
                                            className={cn(
                                                "flex size-9 flex-shrink-0 items-center justify-center rounded-2xl border transition-colors",
                                                isActive
                                                    ? "border-primary/20 bg-primary/10 text-primary"
                                                    : "border-border bg-card text-muted-foreground group-hover:text-foreground"
                                            )}
                                        >
                                            <item.icon size={17} />
                                        </div>
                                        <div className="min-w-0">
                                            <p className="text-sm font-semibold text-foreground">{item.name}</p>
                                            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                                                {item.description}
                                            </p>
                                        </div>
                                    </div>
                                </Link>
                            );
                        })}
                    </div>
                ))}
            </nav>
            <div className="border-t border-border/80 p-4">
                <div className="rounded-3xl border border-primary/20 bg-primary/5 p-4">
                    <div className="flex items-start gap-3">
                        <div className="mt-0.5 flex size-9 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                            <Sparkles size={16} />
                        </div>
                        <div className="space-y-1.5">
                            <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-primary/80">
                                Next Best Step
                            </p>
                            <p className="text-sm font-semibold text-foreground">
                                Run a focused practice session
                            </p>
                            <p className="text-xs leading-relaxed text-muted-foreground">
                                Capture a fresh readiness signal, then let the coach adapt your plan.
                            </p>
                        </div>
                    </div>
                    <Link
                        href={START_SESSION_HREF}
                        onClick={onNavigate}
                        className={cn(buttonStyles({ size: "md" }), "mt-4 w-full")}
                    >
                        Start Session
                    </Link>
                </div>
            </div>
        </aside>
    );
}
