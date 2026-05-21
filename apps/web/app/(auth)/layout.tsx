import Link from "next/link";
import { ReactNode } from "react";
import { Logo } from "@/components/ui/Logo";

export default function AuthLayout({ children }: { children: ReactNode }) {
    return (
        <div className="flex flex-col min-h-screen">
            <header className="w-full px-6 py-4 flex justify-between items-center border-b border-transparent">
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

            <main className="flex-grow flex items-center justify-center bg-background-light dark:bg-background-dark">
                {children}
            </main>

            <footer className="w-full py-6 text-center text-sm text-gray-500 dark:text-gray-400 bg-background-light dark:bg-background-dark">
                <div className="flex flex-col md:flex-row justify-center items-center gap-4 md:gap-8 min-h-[48px]">
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
