"use client";

import { Logo } from "@/components/ui/Logo";
import { useUiStore } from "@/lib/store/ui.store";

export function Footer() {
    const { openModal } = useUiStore();
    return (
        <footer className="border-t border-slate-200 bg-white py-12 dark:border-slate-800 dark:bg-background-dark">
            <div className="mx-auto max-w-7xl px-6 lg:px-12">
                <div className="grid grid-cols-2 gap-8 md:grid-cols-4 lg:grid-cols-5">
                    <div className="col-span-2">
                        <Logo
                            className="mb-6"
                            iconWrapperClassName="h-8 w-8 size-8 rounded-xl"
                            iconSize={16}
                            textClassName="text-lg"
                        />
                        <p className="max-w-xs text-sm text-slate-500 dark:text-slate-400">
                            The world&apos;s most advanced AI interview training
                            platform for elite professionals and
                            high-performance teams.
                        </p>
                    </div>
                    <div>
                        <h5 className="mb-4 text-sm font-bold uppercase tracking-widest text-charcoal dark:text-white">
                            Product
                        </h5>
                        <ul className="space-y-3 text-sm text-slate-500 dark:text-slate-400">
                            <li>
                                <a
                                    className="hover:text-primary transition-colors"
                                    href="#features"
                                >
                                    Features
                                </a>
                            </li>
                            <li>
                                <a
                                    className="hover:text-primary transition-colors"
                                    href="#how-it-works"
                                >
                                    How It Works
                                </a>
                            </li>
                            <li>
                                <a
                                    className="hover:text-primary transition-colors"
                                    href="#pricing"
                                >
                                    Pricing
                                </a>
                            </li>
                            <li>
                                <button
                                    onClick={() => openModal("api")}
                                    className="hover:text-primary transition-colors text-left"
                                >
                                    API
                                </button>
                            </li>
                        </ul>
                    </div>

                    <div>
                        <h5 className="mb-4 text-sm font-bold uppercase tracking-widest text-charcoal dark:text-white">
                            Company
                        </h5>
                        <ul className="space-y-3 text-sm text-slate-500 dark:text-slate-400 flex flex-col items-start">
                            <li>
                                <button
                                    onClick={() => openModal("about")}
                                    className="hover:text-primary transition-colors text-left"
                                >
                                    About Us
                                </button>
                            </li>
                            <li>
                                <button
                                    onClick={() => openModal("contact")}
                                    className="hover:text-primary transition-colors text-left"
                                >
                                    Contact
                                </button>
                            </li>
                            <li>
                                <button
                                    onClick={() => openModal("privacy")}
                                    className="hover:text-primary transition-colors text-left"
                                >
                                    Privacy
                                </button>
                            </li>
                        </ul>
                    </div>
                    <div>
                        <h5 className="mb-4 text-sm font-bold uppercase tracking-widest text-charcoal dark:text-white">
                            Resources
                        </h5>
                        <ul className="space-y-3 text-sm text-slate-500 dark:text-slate-400 flex flex-col items-start">
                            <li>
                                <button
                                    onClick={() => openModal("blog")}
                                    className="hover:text-primary transition-colors text-left"
                                >
                                    Blog
                                </button>
                            </li>
                            <li>
                                <button
                                    onClick={() => openModal("help")}
                                    className="hover:text-primary transition-colors text-left"
                                >
                                    Help Center
                                </button>
                            </li>
                            <li>
                                <button
                                    onClick={() => openModal("whitepapers")}
                                    className="hover:text-primary transition-colors text-left"
                                >
                                    Whitepapers
                                </button>
                            </li>
                            <li>
                                <button
                                    onClick={() => openModal("guides")}
                                    className="hover:text-primary transition-colors text-left"
                                >
                                    Guides
                                </button>
                            </li>
                        </ul>
                    </div>
                </div>
                <div className="mt-12 border-t border-slate-100 pt-8 dark:border-slate-800">
                    <p className="text-xs text-slate-400 dark:text-slate-500">
                        © 2024 BrainTrain Technologies Inc. All rights reserved.
                        Designed for high-performance.
                    </p>
                </div>
            </div>
        </footer>
    );
}
