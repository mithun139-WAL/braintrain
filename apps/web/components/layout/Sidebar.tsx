"use client";

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
    Zap
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/store/auth.store";
import { useRouter } from "next/navigation";
import { identityApi } from "@/lib/api/identity.api";

const navItems = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Practice Sessions", href: "/dashboard/sessions", icon: BookOpen },
    { name: "Reports", href: "/dashboard/reports", icon: BarChart3 },
    { name: "Performance Trends", href: "/dashboard/analytics", icon: TrendingUp },
    { name: "Settings", href: "/dashboard/settings", icon: Settings },
];

export function Sidebar() {
    const pathname = usePathname();
    const router = useRouter();
    const { user, logout: clearStore } = useAuthStore();

    const handleLogout = async () => {
        try {
            await identityApi.logout();
        } catch (error) {
            console.error("Logout error:", error);
        } finally {
            clearStore();
            router.push("/login");
        }
    };

    return (
        <aside className="w-64 flex-shrink-0 bg-white border-r border-gray-100 flex flex-col justify-between h-full z-10 shadow-premium">
            <div className="flex flex-col gap-8 p-6">
                <div className="flex items-center gap-3 px-2">
                    <div className="flex items-center justify-center size-10 rounded-xl bg-primary text-white shadow-lg shadow-primary/30">
                        <Brain size={24} />
                    </div>
                    <div>
                        <h1 className="text-gray-900 text-lg font-bold leading-tight tracking-tight">BrainTrain</h1>
                        <p className="text-gray-500 text-[10px] font-medium uppercase tracking-wider">Interview Prep AI</p>
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
                                        ? "bg-primary/10 text-primary border border-primary/10"
                                        : "text-gray-500 hover:bg-gray-50 hover:text-gray-900"
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

            <div className="flex flex-col gap-6">
                <div className="px-6">
                    <div className="bg-gray-900 rounded-2xl p-4 text-white relative overflow-hidden group cursor-pointer border border-gray-800">
                        <div className="absolute top-0 right-0 w-16 h-16 bg-primary rounded-full blur-2xl opacity-20 -mr-4 -mt-4 transition-opacity group-hover:opacity-30"></div>
                        <div className="flex items-center gap-2 mb-1">
                            <Zap size={14} className="text-primary fill-primary" />
                            <h4 className="font-bold text-sm relative z-10">Pro Plan</h4>
                        </div>
                        <p className="text-[11px] text-gray-400 mb-3 relative z-10">Get unlimited AI mock interviews and deep analytics.</p>
                        <button className="w-full py-2 bg-white text-gray-900 text-xs font-bold rounded-lg hover:bg-gray-100 transition-colors relative z-10">
                            Upgrade Now
                        </button>
                    </div>
                </div>

                <div className="p-6 border-t border-gray-50">
                    <div
                        className="flex items-center gap-3 p-2 rounded-xl hover:bg-gray-50 cursor-pointer transition-colors group"
                        onClick={handleLogout}
                        title="Click to logout"
                    >
                        <div className="size-10 rounded-full bg-indigo-100 flex items-center justify-center text-primary ring-2 ring-white shadow-sm overflow-hidden">
                            <User size={20} />
                        </div>
                        <div className="flex flex-col overflow-hidden">
                            <p className="text-sm font-bold text-gray-900 truncate group-hover:text-primary transition-colors leading-none mb-1">
                                {user?.name || "User"}
                            </p>
                            <p className="text-[10px] text-gray-500 truncate">
                                {user?.email || "user@example.com"}
                            </p>
                        </div>
                        <ChevronDown size={16} className="ml-auto text-gray-400 group-hover:text-gray-600 transition-colors" />
                    </div>
                </div>
            </div>
        </aside>
    );
}
