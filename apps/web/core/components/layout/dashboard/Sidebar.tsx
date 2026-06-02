
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
            const email = profileResponse?.data?.email || "";
            const isAdmin = planType === "ADMIN" || email.toLowerCase().includes("admin") || email.endsWith("@braintrain.com");

            if (section.label === "Admin" && !isAdmin) {
                return {
                    ...section,
                    items: [],
                };
            }

            const filteredItems = section.items.filter((item) => {
                if (planType === "FREE") {
                    return !["Coach", "Topics", "Plan", "Knowledge"].includes(item.name);
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
                "flex h-full w-64 flex-shrink-0 flex-col border-r border-border/40 bg-card/50 backdrop-blur-xl",
                className
            )}
        >
            <div className="flex h-16 items-center gap-3 border-b border-border/40 px-6 flex-shrink-0">
                <Logo
                    showText={false}
                    iconWrapperClassName="size-8 rounded-xl bg-primary/10 text-primary flex-shrink-0"
                    iconSize={16}
                />
                <div className="min-w-0 flex-1">
                    <h1 className="text-foreground text-[15px] font-semibold leading-none tracking-tight">
                        BrainTrain
                    </h1>
                    <p className="mt-1.5 text-[11px] text-muted-foreground leading-none font-medium">
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

            <nav className="flex-1 overflow-y-auto px-4 py-6 flex flex-col gap-6 custom-scrollbar">
                {filteredNavigation.map((section) => (
                    <div key={section.label} className="flex flex-col gap-1">
                        <p className="px-3 text-[10px] font-bold uppercase tracking-wider text-muted-foreground/50 mb-1">
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
                                        "group flex items-center gap-3 rounded-xl px-3 py-2 text-[14px] font-medium transition-all duration-200",
                                        isActive
                                            ? "bg-primary/10 text-primary"
                                            : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
                                    )}
                                >
                                    <item.icon size={16} className={cn("shrink-0", isActive ? "text-primary" : "text-muted-foreground/70 group-hover:text-foreground")} />
                                    <span>{item.name}</span>
                                </Link>
                            );
                        })}
                    </div>
                ))}
            </nav>

            <div className="border-t border-border/40 p-5 bg-muted/10">
                <div className="space-y-1.5 mb-4">
                    <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground/50">
                        Next step
                    </p>
                    <p className="text-xs text-muted-foreground/90 leading-relaxed">
                        Run a practice session to update your coaching signal.
                    </p>
                </div>
                <Link
                    href={START_SESSION_HREF}
                    onClick={onNavigate}
                    className={cn(buttonStyles({ variant: "primary", size: "sm" }), "w-full rounded-md shadow-none")}
                >
                    <Sparkles className="mr-2 size-4" />
                    Start Practice
                </Link>
            </div>
        </aside>
    );
}

