export function Footer() {
    return (
        <footer className="border-t border-slate-200 bg-white py-12 dark:border-slate-800 dark:bg-background-dark">
            <div className="mx-auto max-w-7xl px-6 lg:px-12">
                <div className="grid grid-cols-2 gap-8 md:grid-cols-4 lg:grid-cols-5">
                    <div className="col-span-2">
                        <div className="flex items-center gap-2 mb-6">
                            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-white">
                                <span className="material-symbols-outlined !text-xl font-bold">
                                    psychology_alt
                                </span>
                            </div>
                            <span className="text-lg font-extrabold tracking-tight text-charcoal dark:text-white">
                                BrainTrain
                            </span>
                        </div>
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
                                    href="#"
                                >
                                    Features
                                </a>
                            </li>
                            <li>
                                <a
                                    className="hover:text-primary transition-colors"
                                    href="#"
                                >
                                    Enterprise
                                </a>
                            </li>
                            <li>
                                <a
                                    className="hover:text-primary transition-colors"
                                    href="#"
                                >
                                    Pricing
                                </a>
                            </li>
                            <li>
                                <a
                                    className="hover:text-primary transition-colors"
                                    href="#"
                                >
                                    API
                                </a>
                            </li>
                        </ul>
                    </div>
                    <div>
                        <h5 className="mb-4 text-sm font-bold uppercase tracking-widest text-charcoal dark:text-white">
                            Company
                        </h5>
                        <ul className="space-y-3 text-sm text-slate-500 dark:text-slate-400">
                            <li>
                                <a
                                    className="hover:text-primary transition-colors"
                                    href="#"
                                >
                                    About Us
                                </a>
                            </li>
                            <li>
                                <a
                                    className="hover:text-primary transition-colors"
                                    href="#"
                                >
                                    Careers
                                </a>
                            </li>
                            <li>
                                <a
                                    className="hover:text-primary transition-colors"
                                    href="#"
                                >
                                    Contact
                                </a>
                            </li>
                            <li>
                                <a
                                    className="hover:text-primary transition-colors"
                                    href="#"
                                >
                                    Privacy
                                </a>
                            </li>
                        </ul>
                    </div>
                    <div>
                        <h5 className="mb-4 text-sm font-bold uppercase tracking-widest text-charcoal dark:text-white">
                            Resources
                        </h5>
                        <ul className="space-y-3 text-sm text-slate-500 dark:text-slate-400">
                            <li>
                                <a
                                    className="hover:text-primary transition-colors"
                                    href="#"
                                >
                                    Blog
                                </a>
                            </li>
                            <li>
                                <a
                                    className="hover:text-primary transition-colors"
                                    href="#"
                                >
                                    Help Center
                                </a>
                            </li>
                            <li>
                                <a
                                    className="hover:text-primary transition-colors"
                                    href="#"
                                >
                                    Whitepapers
                                </a>
                            </li>
                            <li>
                                <a
                                    className="hover:text-primary transition-colors"
                                    href="#"
                                >
                                    Guides
                                </a>
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
