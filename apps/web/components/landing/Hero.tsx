import Link from "next/link";

export function Hero() {
    return (
        <section className="mx-auto max-w-7xl px-6 py-20 text-center lg:px-12 lg:py-32">
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-primary mb-8">
                <span className="relative flex h-2 w-2">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75"></span>
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-primary"></span>
                </span>
                AI-Powered Training
            </div>
            <h1 className="mx-auto max-w-4xl text-5xl font-black leading-[1.1] tracking-tight text-charcoal sm:text-7xl dark:text-white">
                Train Smarter. <br />
                <span className="text-primary">Perform Confidently.</span>
            </h1>
            <p className="mx-auto mt-8 max-w-2xl text-lg leading-relaxed text-slate-500 dark:text-slate-400">
                Master your interview skills with AI-driven feedback and
                personalized training paths tailored for elite professionals.
                Practice with the clinical precision required for high-stakes
                career moves.
            </p>
            <div className="mt-12 flex flex-col items-center justify-center gap-4 sm:flex-row">
                <Link href="/register" className="flex min-w-[200px] items-center justify-center rounded-xl bg-primary px-8 py-4 text-lg font-bold text-white shadow-xl shadow-primary/25 hover:brightness-105 transition-all">
                    Start Training Free
                </Link>
                <button className="flex min-w-[200px] items-center justify-center rounded-xl border border-slate-200 bg-white px-8 py-4 text-lg font-bold text-charcoal hover:bg-slate-50 transition-all dark:border-slate-700 dark:bg-transparent dark:text-white">
                    Book a Demo
                </button>
            </div>
            <div className="mt-20 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-slate-800 dark:bg-slate-900">
                <div
                    className="aspect-video w-full bg-slate-100 dark:bg-slate-800 bg-cover bg-center"
                    data-alt="Dashboard interface showing AI interview analysis charts and video playback"
                    style={{
                        backgroundImage:
                            'url("https://lh3.googleusercontent.com/aida-public/AB6AXuAKrxV5xeUji9MgM2W2DvPPV1JiBRbtFkqd6iR__BS_YGO8cY8Hj2iZifLhVkSUJH-v-y87Q98pzujMR7WaX646_ex4dTEjUlV7FHO_1CL8T1W8ebpmtKlepIPwa0sAjdPgkYGU1mM_W7zBsLpw88jMjbwGOe5kPMAiEmz0FKOVW1ROUkirHs0I4cMzbjvjxaFf6bUcRACTA7JjyH5ZckkxqFuGaYUGiLszXDAoP21jUAIt4vnw2BdsG06pPt6qDnzfO8-kpQm9JTQ")',
                    }}
                ></div>
            </div>
        </section>
    );
}
