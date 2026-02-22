"use client";

import Link from "next/link";
import { Search, Bell, Plus } from "lucide-react";

export function TopBar() {
    return (
        <header className="h-20 bg-white dark:bg-gray-950 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between px-8 sticky top-0 z-20">
            <div className="flex-1 max-w-md">
                <div className="relative group">
                    <Search
                        size={18}
                        className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-primary transition-colors"
                    />
                    <input
                        type="text"
                        placeholder="Search sessions, reports, or skills..."
                        className="w-full pl-10 pr-4 py-2.5 bg-gray-50 dark:bg-gray-900 border-none rounded-xl text-sm focus:ring-2 focus:ring-primary/20 focus:bg-white dark:focus:bg-gray-950 transition-all placeholder-gray-400 dark:placeholder-gray-500 text-gray-700 dark:text-gray-300 outline-none"
                    />
                </div>
            </div>

            <div className="flex items-center gap-4">
                <button className="relative p-2.5 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-900 rounded-xl transition-all">
                    <Bell size={20} />
                    <span className="absolute top-2.5 right-2.5 size-2 bg-rose-500 rounded-full border-2 border-white dark:border-gray-950"></span>
                </button>
                <div className="h-8 w-px bg-gray-100 dark:bg-gray-800 mx-1"></div>
                <Link href="/dashboard/sessions/start">
                    <button className="bg-primary hover:bg-primary-dark text-white font-semibold py-2.5 px-6 rounded-xl shadow-lg shadow-primary/20 transition-all flex items-center gap-2 transform active:scale-95 text-sm">
                        <Plus size={18} />
                        Start Session
                    </button>
                </Link>
            </div>
        </header>
    );
}
