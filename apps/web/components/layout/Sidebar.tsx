"use client";

import { useState, useRef, useEffect } from "react";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    LayoutDashboard,
    BookOpen,
    BarChart3,
    TrendingUp,
    Settings,
    Brain,
    User,
    ChevronDown,
    ChevronUp,
    Zap,
    LogOut
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/store/auth.store";
import { useRouter } from "next/navigation";
import { identityApi } from "@/lib/api/identity.api";
import { ConfirmationModal } from "@/components/ui/ConfirmationModal";
import { useGetProfile } from "@/hooks/queries/useGetProfile";

const navItems = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Practice Sessions", href: "/dashboard/sessions", icon: BookOpen },
    { name: "Reports", href: "/dashboard/reports", icon: BarChart3 },
    { name: "Performance Trends", href: "/dashboard/trends", icon: TrendingUp },
];

export function Sidebar() {
    const pathname = usePathname();
    const router = useRouter();
    const { user: authUser, logout: clearStore } = useAuthStore();
    const { data: profileResponse } = useGetProfile();

    const user = profileResponse?.data || authUser;

    const [isLogoutModalOpen, setIsLogoutModalOpen] = useState(false);
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsDropdownOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, []);

    const handleLogout = async () => {
        try {
            await identityApi.logout();
        } catch (error) {
            console.error("Logout error:", error);
        } finally {
            clearStore();
            localStorage.removeItem("braintrain-auth-storage"); // Explicitly clear local storage
            router.push("/login");
        }
    };

    return (
        <>
            <aside className="w-64 flex-shrink-0 bg-white dark:bg-gray-950 border-r border-gray-100 dark:border-gray-800 flex flex-col justify-between h-full z-10 shadow-premium">
                <div className="flex flex-col gap-8 p-6">
                    <div className="flex items-center gap-3 px-2">
                        <div className="flex items-center justify-center size-10 rounded-xl bg-primary text-white shadow-lg shadow-primary/30">
                            <Brain size={24} />
                        </div>
                        <div>
                            <h1 className="text-gray-900 dark:text-gray-100 text-lg font-bold leading-tight tracking-tight">BrainTrain</h1>
                            <p className="text-gray-500 dark:text-gray-400 text-[10px] font-medium uppercase tracking-wider">Interview Prep AI</p>
                        </div>
                    </div>

                    <nav className="flex flex-col gap-1.5 mt-2">
                        {navItems.map((item) => {
                            const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
                            return (
                                <Link
                                    key={item.name}
                                    href={item.href}
                                    className={cn(
                                        "flex items-center gap-3 px-4 py-3 rounded-xl transition-all group",
                                        isActive
                                            ? "bg-primary/10 dark:bg-primary/20 text-primary border border-primary/10 dark:border-primary/20"
                                            : "text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-900 hover:text-gray-900 dark:hover:text-gray-100"
                                    )}
                                >
                                    <item.icon
                                        size={20}
                                        className={cn(
                                            "transition-transform",
                                            !isActive && "group-hover:scale-110"
                                        )}
                                    />
                                    <span className={cn("text-sm transition-all", isActive ? "font-semibold" : "font-medium")}>
                                        {item.name}
                                    </span>
                                </Link>
                            );
                        })}
                    </nav>
                </div>

                <div className="p-6 border-t border-gray-50 dark:border-gray-800 relative" ref={dropdownRef}>
                    {isDropdownOpen && (
                        <div className="absolute bottom-full left-6 right-6 mb-2 bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl shadow-lg shadow-black/5 dark:shadow-black/20 overflow-hidden z-20 animate-in fade-in slide-in-from-bottom-2 duration-200">
                            <Link
                                href="/dashboard/settings"
                                onClick={() => setIsDropdownOpen(false)}
                                className="w-full flex items-center gap-3 px-4 py-3 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors border-b border-gray-50 dark:border-gray-800"
                            >
                                <Settings size={18} />
                                Profile Settings
                            </Link>
                            <button
                                className="w-full flex items-center gap-3 px-4 py-3 text-sm font-medium text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-500/10 transition-colors text-left"
                                onClick={() => {
                                    setIsDropdownOpen(false);
                                    setIsLogoutModalOpen(true);
                                }}
                            >
                                <LogOut size={18} />
                                Sign out
                            </button>
                        </div>
                    )}
                    <div
                        className="flex items-center gap-3 p-2 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-900 cursor-pointer transition-colors group"
                        onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                        title="Profile options"
                    >
                        <div className="size-10 rounded-full bg-primary/10 dark:bg-primary/20 flex items-center justify-center text-primary ring-2 ring-white dark:ring-gray-950 shadow-sm overflow-hidden">
                            {user?.avatarUrl ? (
                                <img src={user.avatarUrl} alt={user.displayName || "User"} className="h-full w-full object-cover" />
                            ) : (
                                <span className="text-xs font-bold uppercase">
                                    {(user?.displayName || user?.email || "U")[0]}
                                </span>
                            )}
                        </div>
                        <div className="flex flex-col overflow-hidden">
                            <p className="text-xs font-bold text-gray-900 dark:text-gray-100 truncate group-hover:text-primary transition-colors leading-none mb-1">
                                {user?.displayName || "User"}
                            </p>
                            <p className="text-[10px] text-gray-500 dark:text-gray-400 truncate">
                                {user?.email || "user@example.com"}
                            </p>
                        </div>
                        {isDropdownOpen ? (
                            <ChevronUp size={14} className="ml-auto text-gray-400 dark:text-gray-500 group-hover:text-gray-600 dark:group-hover:text-gray-300 transition-colors" />
                        ) : (
                            <ChevronDown size={14} className="ml-auto text-gray-400 dark:text-gray-500 group-hover:text-gray-600 dark:group-hover:text-gray-300 transition-colors" />
                        )}
                    </div>
                </div>
            </aside>

            <ConfirmationModal
                isOpen={isLogoutModalOpen}
                onClose={() => setIsLogoutModalOpen(false)}
                onConfirm={handleLogout}
                title="Sign Out"
                description="Are you sure you want to sign out of your account?"
                confirmText="Sign Out"
                variant="danger"
            />
        </>
    );
}
