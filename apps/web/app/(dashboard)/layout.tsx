
"use client";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Sidebar } from "@/core/components/layout/dashboard/Sidebar";
import { TopBar } from "@/core/components/layout/dashboard/TopBar";
import { useAuthStore } from "@/lib/store/auth.store";
import { useUiStore } from "@/lib/store/ui.store";
import { cn } from "@/lib/utils";
import { useGetProfile } from "@/hooks/queries/useGetProfile";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const router = useRouter();
    const pathname = usePathname();
    const { isAuthenticated, hasHydrated } = useAuthStore();
    const isSidebarOpen = useUiStore((state) => state.isSidebarOpen);
    const closeSidebar = useUiStore((state) => state.closeSidebar);
    const [isChecking, setIsChecking] = useState(true);

    const { data: profileResponse, isLoading: isProfileLoading } = useGetProfile();
    const user = profileResponse?.data;
    const isFree = user?.planType === "FREE";
    const isForbiddenPath =
        pathname.startsWith("/dashboard/coach") ||
        pathname.startsWith("/dashboard/training") ||
        pathname.startsWith("/dashboard/topics");

    const isRedirecting = isForbiddenPath && (isProfileLoading || (user && isFree));

    useEffect(() => {
        if (!hasHydrated) return;

        if (!isAuthenticated) {
            router.replace("/login");
            return;
        }

        setIsChecking(false);

        if (!isProfileLoading && isFree && isForbiddenPath) {
            router.replace("/dashboard");
        }
    }, [isAuthenticated, hasHydrated, isProfileLoading, isFree, isForbiddenPath, router]);

    useEffect(() => {
        closeSidebar();
    }, [pathname, closeSidebar]);

    if (isChecking || isRedirecting) {
        return (
            <div className="flex min-h-dvh w-full items-center justify-center bg-background text-foreground">
                <div className="flex flex-col items-center gap-4">
                    <div className="size-12 rounded-full border-4 border-primary border-t-transparent animate-spin"></div>
                    <p className="text-muted-foreground font-medium animate-pulse">
                        {isChecking ? "Authenticating..." : "Redirecting..."}
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="h-dvh overflow-hidden bg-background text-foreground">
            <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
                <div className="absolute left-[8%] top-[-6rem] h-[24rem] w-[24rem] rounded-full bg-primary/10 blur-3xl" />
                <div className="absolute right-[-4rem] top-[18%] h-[22rem] w-[22rem] rounded-full bg-sky/10 blur-3xl" />
                <div className="absolute bottom-[-8rem] left-[25%] h-[26rem] w-[26rem] rounded-full bg-violet/8 blur-3xl" />
            </div>

            <div className="flex h-full w-full">
                <Sidebar className="hidden xl:flex" />

                <div
                    className={cn(
                        "fixed inset-0 z-40 bg-background/70 backdrop-blur-sm transition-opacity xl:hidden",
                        isSidebarOpen ? "opacity-100" : "pointer-events-none opacity-0"
                    )}
                    onClick={closeSidebar}
                    aria-hidden="true"
                />

                <Sidebar
                    className={cn(
                        "fixed inset-y-0 left-0 z-50 xl:hidden transition-transform duration-200",
                        isSidebarOpen ? "translate-x-0" : "-translate-x-full"
                    )}
                    onNavigate={closeSidebar}
                    onClose={closeSidebar}
                />

                <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
                <TopBar />
                    <main className="flex-1 overflow-y-auto custom-scrollbar">
                        <div className="mx-auto flex w-full max-w-shell flex-col px-4 pb-12 pt-6 sm:px-6 lg:px-8 xl:px-10">
                        {children}
                        </div>
                    </main>
                    </div>
            </div>
        </div>
    );
}
