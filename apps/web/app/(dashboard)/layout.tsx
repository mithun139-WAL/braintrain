"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopBar } from "@/components/layout/TopBar";
import { useAuthStore } from "@/lib/store/auth.store";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const router = useRouter();
    const { isAuthenticated, hasHydrated } = useAuthStore();
    const [isChecking, setIsChecking] = useState(true);

    useEffect(() => {
        if (!hasHydrated) return;

        if (!isAuthenticated) {
            router.push("/login");
        } else {
            setIsChecking(false);
        }
    }, [isAuthenticated, hasHydrated, router]);

    if (isChecking) {
        return (
            <div className="flex h-screen w-full items-center justify-center bg-background">
                <div className="flex flex-col items-center gap-4">
                    <div className="size-12 rounded-full border-4 border-primary border-t-transparent animate-spin"></div>
                    <p className="text-gray-500 font-medium animate-pulse">Authenticating...</p>
                </div>
            </div>
        );
    }
    return (
        <div className="flex h-screen w-full bg-background overflow-hidden font-sans">
            <Sidebar />
            <div className="flex-1 flex flex-col h-full overflow-hidden">
                <TopBar />
                <main className="flex-1 overflow-y-auto p-8 custom-scrollbar bg-slate-50/50">
                    <div className="max-w-7xl mx-auto">
                        {children}
                    </div>
                </main>
            </div>
        </div>
    );
}
