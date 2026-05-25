
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Sparkles, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Logo } from "@/components/ui/Logo";
import {
    dashboardNavigation,
    isDashboardItemActive,
    START_SESSION_HREF,
} from "@/core/components/layout/dashboard/navigation";
import { buttonStyles } from "@/core/components/ui/button";
import { useGetProfile } from "@/hooks/queries/useGetProfile";

interface SidebarProps {
    className?: string;
    onNavigate?: () => void;
    onClose?: () => void;
}

export function Sidebar({ className, onNavigate, onClose }: SidebarProps) {
    const pathname = usePathname();
    const { data: profileResponse } = useGetProfile();
    const planType = profileResponse?.data?.planType || "FREE";

    const filteredNavigation = dashboardNavigation
        .map((section) => {
            const filteredItems = section.items.filter((item) => {
                if (planType === "FREE") {
                    return !["Coach", "Topics", "Plan"].includes(item.name);
                }
                return true;
            });
            return {
                ...section,
                items: filteredItems,
            };
        })
        .filter((section) => section.items.length > 0);

    return (
        <aside
            className={cn(
                "flex h-full w-60 flex-shrink-0 flex-col border-r border-border/60 bg-card/45 backdrop-blur-md",
                className
            )}
        >
            <div className="flex items-center gap-2.5 border-b border-border/60 px-4.5 py-4 flex-shrink-0">
                <Logo
                    showText={false}
                    iconWrapperClassName="size-8 rounded-lg bg-primary/10 text-primary flex-shrink-0"
                    iconSize={15}
                />
                <div className="min-w-0 flex-1">
                    <h1 className="text-foreground text-sm font-semibold leading-none tracking-tight">
                        BrainTrain
                    </h1>
                    <p className="mt-1 text-[10px] text-muted-foreground leading-none">
                        AI Interview Mentor
                    </p>
                </div>

                {onClose ? (
                    <button
                        type="button"
                        onClick={onClose}
                        className="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground xl:hidden"
                        aria-label="Close navigation"
                    >
                        <X size={15} />
                    </button>
                ) : null}
            </div>
            <nav className="flex-1 overflow-y-auto px-2 py-4 flex flex-col gap-4 custom-scrollbar">
                {filteredNavigation.map((section) => (
                    <div key={section.label} className="flex flex-col gap-0.5">
                        <p className="px-3 py-1 text-[9px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/45">
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
                                        "group flex items-center gap-2.5 rounded-lg px-3 py-1.5 text-[13px] font-medium transition-colors",
                                        isActive
                                            ? "bg-primary/8 text-primary"
                                            : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                                    )}
                                >
                                    <item.icon size={14} className={cn("shrink-0", isActive ? "text-primary" : "text-muted-foreground/60 group-hover:text-foreground")} />
                                    <span>{item.name}</span>
                                </Link>
                            );
                        })}
                    </div>
                ))}
            </nav>
            <div className="border-t border-border/60 p-3 space-y-2.5">
                <div className="px-3 space-y-1">
                    <p className="text-[9px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/45">
                        Next step
                    </p>
                    <p className="text-[11px] text-muted-foreground leading-normal">
                        Run a practice session to update your coaching signal.
                    </p>
                </div>
                <Link
                    href={START_SESSION_HREF}
                    onClick={onNavigate}
                    className={cn(buttonStyles({ variant: "primary", size: "sm" }), "w-full rounded-md shadow-none")}
                >
                    Start Practice
                </Link>
            </div>
        </aside>
    );
}

