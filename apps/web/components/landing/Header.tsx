import Link from "next/link";

export function Header() {
    return (
        <header className="fixed top-0 z-50 w-full border-b border-slate-200/60 bg-white/80 backdrop-blur-md dark:border-slate-800/60 dark:bg-background-dark/80">
            <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 lg:px-12">
                <div className="flex items-center gap-2">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-white">
                        <span className="material-symbols-outlined !text-2xl font-bold">
                            psychology_alt
                        </span>
                    </div>
                    <span className="text-xl font-extrabold tracking-tight text-charcoal dark:text-white">
                        BrainTrain
                    </span>
                </div>
                <nav className="hidden md:flex items-center gap-10">
                    <a
                        className="text-sm font-semibold text-slate-600 hover:text-primary transition-colors dark:text-slate-300"
                        href="#"
                    >
                        Product
                    </a>
                    <a
                        className="text-sm font-semibold text-slate-600 hover:text-primary transition-colors dark:text-slate-300"
                        href="#"
                    >
                        Features
                    </a>
                    <a
                        className="text-sm font-semibold text-slate-600 hover:text-primary transition-colors dark:text-slate-300"
                        href="#"
                    >
                        Enterprise
                    </a>
                    <a
                        className="text-sm font-semibold text-slate-600 hover:text-primary transition-colors dark:text-slate-300"
                        href="#"
                    >
                        Pricing
                    </a>
                </nav>
                <div className="flex items-center gap-4">
                    <Link href="/login" className="hidden lg:block text-sm font-bold text-charcoal dark:text-white hover:opacity-70 transition-opacity">
                        Login
                    </Link>
                    <Link href="/register" className="flex items-center justify-center rounded-lg bg-primary px-6 py-2.5 text-sm font-bold text-white shadow-lg shadow-primary/20 hover:brightness-110 active:scale-95 transition-all">
                        Get Started
                    </Link>
                </div>
            </div>
        </header>
    );
}
