import Link from "next/link";

export function CTA() {
    return (
        <section className="mx-auto max-w-7xl px-6 py-24 lg:px-12">
            <div className="relative overflow-hidden rounded-[2.5rem] bg-charcoal px-8 py-20 text-center dark:bg-slate-900">
                <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-primary/20 blur-3xl"></div>
                <div className="absolute -bottom-20 -left-20 h-64 w-64 rounded-full bg-primary/10 blur-3xl"></div>
                <div className="relative z-10 mx-auto max-w-3xl">
                    <h2 className="text-4xl font-black text-white sm:text-5xl">
                        Ready to land your dream role?
                    </h2>
                    <p className="mt-6 text-lg text-slate-400">
                        Join 50,000+ professionals who have used BrainTrain to
                        accelerate their career growth.
                    </p>
                    <div className="mt-10">
                        <Link href="/register" className="inline-block rounded-xl bg-primary px-10 py-5 text-xl font-bold text-white shadow-xl shadow-primary/20 hover:scale-105 transition-transform active:scale-95">
                            Start Your Training Journey
                        </Link>
                        <p className="mt-6 text-sm text-slate-500">
                            No credit card required. Free forever basic plan.
                        </p>
                    </div>
                </div>
            </div>
        </section>
    );
}
