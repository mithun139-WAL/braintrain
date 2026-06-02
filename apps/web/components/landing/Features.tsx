import { Mic, Zap, Smile, TrendingUp } from "lucide-react";

export function Features() {
    return (
        <section id="features" className="bg-white py-24 dark:bg-background-dark/50">
            <div className="mx-auto max-w-7xl px-6 lg:px-12">
                <div className="mb-16 text-center">
                    <h2 className="text-3xl font-black tracking-tight text-charcoal sm:text-4xl dark:text-white">
                        Premium Features for Elite Professionals
                    </h2>
                    <p className="mt-4 text-slate-500 dark:text-slate-400">
                        Our platform provides the clinical precision needed to
                        excel in any scenario.
                    </p>
                </div>
                <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
                    {/* Card 1 */}
                    <div className="group relative rounded-2xl border border-slate-100 bg-background-light p-8 transition-all hover:border-primary/20 hover:shadow-xl hover:shadow-primary/5 dark:border-slate-800 dark:bg-slate-900/50">
                        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-white text-primary shadow-sm group-hover:bg-primary group-hover:text-white transition-all dark:bg-slate-800">
                            <Mic className="size-6" />
                        </div>
                        <h3 className="text-lg font-bold text-charcoal dark:text-white">
                            AI Mock Interviews
                        </h3>
                        <p className="mt-2 text-sm leading-relaxed text-slate-500 dark:text-slate-400">
                            Practice with industry-specific AI personas designed
                            by real recruiters.
                        </p>
                    </div>
                    {/* Card 2 */}
                    <div className="group relative rounded-2xl border border-slate-100 bg-background-light p-8 transition-all hover:border-primary/20 hover:shadow-xl hover:shadow-primary/5 dark:border-slate-800 dark:bg-slate-900/50">
                        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-white text-primary shadow-sm group-hover:bg-primary group-hover:text-white transition-all dark:bg-slate-800">
                            <Zap className="size-6" />
                        </div>
                        <h3 className="text-lg font-bold text-charcoal dark:text-white">
                            Real-time Feedback
                        </h3>
                        <p className="mt-2 text-sm leading-relaxed text-slate-500 dark:text-slate-400">
                            Get instant AI-powered corrections on tone, pacing,
                            and content quality.
                        </p>
                    </div>
                    {/* Card 3 */}
                    <div className="group relative rounded-2xl border border-slate-100 bg-background-light p-8 transition-all hover:border-primary/20 hover:shadow-xl hover:shadow-primary/5 dark:border-slate-800 dark:bg-slate-900/50">
                        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-white text-primary shadow-sm group-hover:bg-primary group-hover:text-white transition-all dark:bg-slate-800">
                            <Smile className="size-6" />
                        </div>
                        <h3 className="text-lg font-bold text-charcoal dark:text-white">
                            Behavioral Analysis
                        </h3>
                        <p className="mt-2 text-sm leading-relaxed text-slate-500 dark:text-slate-400">
                            Deep dive into non-verbal communication cues and
                            micro-expressions.
                        </p>
                    </div>
                    {/* Card 4 */}
                    <div className="group relative rounded-2xl border border-slate-100 bg-background-light p-8 transition-all hover:border-primary/20 hover:shadow-xl hover:shadow-primary/5 dark:border-slate-800 dark:bg-slate-900/50">
                        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-white text-primary shadow-sm group-hover:bg-primary group-hover:text-white transition-all dark:bg-slate-800">
                            <TrendingUp className="size-6" />
                        </div>
                        <h3 className="text-lg font-bold text-charcoal dark:text-white">
                            Progress Tracking
                        </h3>
                        <p className="mt-2 text-sm leading-relaxed text-slate-500 dark:text-slate-400">
                            Monitor your improvement with data-driven charts and
                            historical benchmarks.
                        </p>
                    </div>
                </div>
            </div>
        </section>
    );
}
