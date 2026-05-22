import Link from "next/link";
import { ReactNode } from "react";
import { Logo } from "@/components/ui/Logo";

export default function AuthLayout({ children }: { children: ReactNode }) {
    return (
        <div className="flex flex-col min-h-screen relative overflow-hidden">
            {/* Ambient background glows */}
            <div aria-hidden className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
                <div className="absolute top-[25%] left-1/2 -translate-x-1/2 -translate-y-1/2 w-[550px] h-[550px] bg-gradient-to-br from-primary/15 via-violet-500/5 to-transparent rounded-full blur-3xl opacity-80 dark:opacity-60" />
                <div className="absolute bottom-[20%] right-[10%] w-[350px] h-[350px] bg-sky-500/10 rounded-full blur-3xl opacity-40" />
            </div>

            <header className="w-full px-6 py-4 flex justify-between items-center z-10 md:absolute md:top-0 md:left-0">
                <Link href="/" className="transition-opacity hover:opacity-90">
                    <Logo
                        iconWrapperClassName="size-9 rounded-xl"
                        iconSize={18}
                        textClassName="text-lg font-bold"
                    />
                </Link>

                <Link
                    href="#"
                    className="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-primary transition-colors flex items-center gap-1"
                >
                    <span className="material-symbols-outlined text-lg">
                        help
                    </span>
                    <span className="hidden sm:inline">Help & Support</span>
                </Link>
            </header>

            <main className="flex-grow flex items-center justify-center p-4 md:py-20 z-10">
                {children}
            </main>

            <footer className="w-full py-4 text-center text-sm text-gray-500 dark:text-gray-400 z-10 md:absolute md:bottom-0 md:left-0">
                <div className="flex flex-col md:flex-row justify-center items-center gap-2 md:gap-8 min-h-[36px]">
                    <p className="text-xs">
                        © {new Date().getFullYear()} BrainTrain Inc. All rights reserved.
                    </p>
                    <div className="flex items-center gap-4 text-xs font-medium">
                        <Link className="hover:text-primary transition-colors" href="#">
                            Privacy Policy
                        </Link>
                        <Link className="hover:text-primary transition-colors" href="#">
                            Terms of Service
                        </Link>
                    </div>
                </div>
            </footer>
        </div>
    );
}
