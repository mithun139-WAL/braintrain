import Link from "next/link";
import { ArrowRight, Zap, Star } from "lucide-react";

const SOCIAL_PROOF = [
    { initials: "JS", color: "bg-violet-600" },
    { initials: "AK", color: "bg-sky-600"    },
    { initials: "MR", color: "bg-emerald-600" },
    { initials: "PL", color: "bg-amber-600"   },
];

export function Hero() {
    return (
        <section className="relative mx-auto max-w-7xl px-6 py-24 text-center lg:px-12 lg:py-36 overflow-hidden">

            {/* Ambient background glows */}
            <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[500px] bg-primary opacity-[0.08] rounded-full blur-3xl" />
                <div className="absolute bottom-0 left-1/4 w-[400px] h-[300px] bg-violet-500 opacity-[0.05] rounded-full blur-3xl" />
            </div>

            {/* Badge */}
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/25 bg-primary/8 px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-primary mb-10">
                <span className="relative flex h-2 w-2 flex-shrink-0">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75" />
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-primary" />
                </span>
                AI-Powered Interview Training
            </div>

            {/* Headline */}
            <h1 className="mx-auto max-w-4xl text-5xl font-black leading-[1.08] tracking-tight text-gray-900 sm:text-6xl lg:text-7xl dark:text-white">
                Stop fearing{" "}
                <span className="relative inline-block">
                    interviews.
                    <span
                        aria-hidden
                        className="absolute left-0 bottom-1 w-full h-[6px] bg-primary/20 rounded-full -z-10"
                    />
                </span>
                <br />
                <span className="text-primary">Start owning them.</span>
            </h1>

            {/* Sub-headline */}
            <p className="mx-auto mt-8 max-w-2xl text-lg leading-relaxed text-slate-500 dark:text-slate-400">
                Most candidates fail not because they lack skill — but because they&apos;ve never
                practiced under pressure. BrainTrain puts you through real interview conditions
                with an AI coach that knows exactly where you need to improve.
            </p>

            {/* CTAs */}
            <div className="mt-12 flex flex-col items-center justify-center gap-4 sm:flex-row">
                <Link
                    href="/register"
                    className="group flex min-w-[210px] items-center justify-center gap-2 rounded-xl bg-primary px-8 py-4 text-base font-bold text-white shadow-xl shadow-primary/25 hover:brightness-105 transition-all active:scale-95"
                >
                    <Zap size={17} className="fill-white" />
                    Start Training Free
                    <ArrowRight size={15} className="text-white/60 group-hover:translate-x-0.5 transition-transform" />
                </Link>
                <button className="flex min-w-[210px] items-center justify-center rounded-xl border border-slate-200 bg-white px-8 py-4 text-base font-bold text-gray-900 hover:bg-slate-50 transition-all dark:border-slate-700 dark:bg-transparent dark:text-white">
                    Watch a Demo
                </button>
            </div>

            {/* Social proof */}
            <div className="mt-10 flex items-center justify-center gap-3">
                <div className="flex -space-x-2">
                    {SOCIAL_PROOF.map(({ initials, color }) => (
                        <div
                            key={initials}
                            className={`size-8 rounded-full ${color} border-2 border-white dark:border-gray-950 flex items-center justify-center text-[10px] font-bold text-white flex-shrink-0`}
                        >
                            {initials}
                        </div>
                    ))}
                </div>
                <div className="flex flex-col items-start">
                    <div className="flex text-amber-400">
                        {Array.from({ length: 5 }).map((_, i) => (
                            <Star key={i} size={12} className="fill-amber-400" />
                        ))}
                    </div>
                    <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                        Trusted by 1,200+ engineers
                    </span>
                </div>
            </div>

            {/* App screenshot */}
            <div className="mt-20 overflow-hidden rounded-2xl border border-slate-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-2xl shadow-black/10 dark:shadow-black/40 ring-1 ring-black/5">
                <div
                    className="aspect-video w-full bg-gray-100 dark:bg-gray-800"
                    role="img"
                    aria-label="BrainTrain dashboard — AI interview analysis with score cards and live coaching"
                    style={{
                        backgroundImage:
                            "url('https://lh3.googleusercontent.com/aida-public/AB6AXuAKrxV5xeUji9MgM2W2DvPPV1JiBRbtFkqd6iR__BS_YGO8cY8Hj2iZifLhVkSUJH-v-y87Q98pzujMR7WaX646_ex4dTEjUlV7FHO_1CL8T1W8ebpmtKlepIPwa0sAjdPgkYGU1mM_W7zBsLpw88jMjbwGOe5kPMAiEmz0FKOVW1ROUkirHs0I4cMzbjvjxaFf6bUcRACTA7JjyH5ZckkxqFuGaYUGiLszXDAoP21jUAIt4vnw2BdsG06pPt6qDnzfO8-kpQm9JTQ')",
                        backgroundSize:     "cover",
                        backgroundPosition: "center",
                    }}
                />
            </div>
        </section>
    );
}
