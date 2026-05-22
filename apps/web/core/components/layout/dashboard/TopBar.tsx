"use client";

import Link from "next/link";
import { Menu, Moon, Sun, LogOut, Settings } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { resolveDashboardContext } from "@/core/components/layout/dashboard/navigation";
import { useAuthStore } from "@/lib/store/auth.store";
import { useUiStore } from "@/lib/store/ui.store";
import { cn } from "@/lib/utils";
import { ConfirmationModal } from "@/components/ui/ConfirmationModal";

export function TopBar() {
    const { resolvedTheme, setTheme } = useTheme();
    const pathname = usePathname();
    const router = useRouter();
    const user = useAuthStore((state) => state.user);
    const logout = useAuthStore((state) => state.logout);
    const toggleSidebar = useUiStore((state) => state.toggleSidebar);
    const [mounted, setMounted] = useState(false);
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    const [isLogoutDialogOpen, setIsLogoutDialogOpen] = useState(false);

    useEffect(() => setMounted(true), []);

    useEffect(() => {
        if (!isDropdownOpen) return;
        const handleClickOutside = (event: MouseEvent) => {
            const target = event.target as HTMLElement;
            if (!target.closest("#user-menu-button") && !target.closest("#user-menu-dropdown")) {
                setIsDropdownOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [isDropdownOpen]);

    const context = resolveDashboardContext(pathname);
    const displayName = user?.displayName || user?.email?.split("@")[0] || "You";
    const initials = displayName
        .split(/\s+/)
        .filter(Boolean)
        .slice(0, 2)
        .map((part) => part[0]?.toUpperCase())
        .join("") || "BT";

    const today = new Intl.DateTimeFormat("en-US", {
        weekday: "long",
        month: "short",
        day: "numeric",
    }).format(new Date());

    return (
        <>
            <header className="sticky top-0 z-30 border-b border-border/80 bg-background/80 backdrop-blur-xl">
                <div className="mx-auto flex h-16 w-full max-w-shell items-center gap-3 px-4 sm:px-6 lg:px-8 xl:px-10">
                    <button
                        type="button"
                        onClick={toggleSidebar}
                        className="inline-flex items-center justify-center rounded-xl border border-border bg-card p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground xl:hidden"
                        aria-label="Open navigation"
                    >
                        <Menu size={18} />
                    </button>

                    <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                            <span className="inline-flex rounded-full border border-border bg-card px-2.5 py-1 text-[10px] text-foreground">
                                {context.eyebrow}
                            </span>
                            <span className="hidden md:block">{today}</span>
                        </div>
                        <p className="truncate text-sm font-semibold text-foreground">{context.description}</p>
                    </div>

                    <div className="ml-auto flex items-center gap-2">
                        <div className="relative">
                            <button
                                id="user-menu-button"
                                type="button"
                                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                                className="hidden min-w-0 items-center gap-3 rounded-full border border-border bg-card px-2.5 py-1.5 shadow-card transition-colors hover:bg-muted/60 sm:flex text-left outline-none focus:border-primary/30"
                            >
                                <span className="flex size-8 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
                                    {initials}
                                </span>
                                <div className="min-w-0">
                                    <p className="truncate text-sm font-semibold text-foreground">{displayName}</p>
                                    <p className="truncate text-xs text-muted-foreground">{context.title}</p>
                                </div>
                            </button>

                            {/* Dropdown Menu */}
                            {isDropdownOpen && (
                                <div
                                    id="user-menu-dropdown"
                                    className="absolute right-0 mt-2 w-48 rounded-2xl border border-border bg-card p-1.5 shadow-xl animate-in fade-in slide-in-from-top-2 duration-150 z-50"
                                >
                                    <Link
                                        href="/dashboard/settings"
                                        onClick={() => setIsDropdownOpen(false)}
                                        className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-sm font-semibold text-foreground hover:bg-muted/60 transition-colors"
                                    >
                                        <Settings size={15} className="text-muted-foreground" />
                                        Settings
                                    </Link>
                                    <button
                                        type="button"
                                        onClick={() => {
                                            setIsDropdownOpen(false);
                                            setIsLogoutDialogOpen(true);
                                        }}
                                        className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-sm font-semibold text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/20 transition-colors"
                                    >
                                        <LogOut size={15} />
                                        Logout
                                    </button>
                                </div>
                            )}
                        </div>

                        {mounted && (
                            <button
                                type="button"
                                onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
                                className={cn(
                                    "rounded-xl border border-border bg-card p-2 text-muted-foreground shadow-card transition-colors hover:bg-muted hover:text-foreground",
                                    "sm:rounded-full"
                                )}
                                aria-label="Toggle theme"
                            >
                                {resolvedTheme === "dark" ? (
                                    <Sun size={17} />
                                ) : (
                                    <Moon size={17} />
                                )}
                            </button>
                        )}
                    </div>
                </div>
            </header>

            <ConfirmationModal
                isOpen={isLogoutDialogOpen}
                onClose={() => setIsLogoutDialogOpen(false)}
                onConfirm={() => {
                    setIsLogoutDialogOpen(false);
                    logout();
                }}
                title="Confirm Logout"
                description="Are you sure you want to log out of your session? You will need to sign in again to access your dashboard."
                confirmText="Log Out"
                variant="danger"
                icon={<LogOut className="h-6 w-6 text-rose-600 dark:text-rose-400" />}
            />
        </>
    );
}
