export function HowItWorks() {
    return (
        <section id="how-it-works" className="bg-background-light py-24 dark:bg-background-dark">
            <div className="mx-auto max-w-7xl px-6 lg:px-12">
                <div className="mb-20">
                    <h2 className="text-3xl font-black tracking-tight text-charcoal sm:text-4xl dark:text-white">
                        How It Works
                    </h2>
                    <p className="mt-4 text-slate-500 dark:text-slate-400">
                        A streamlined three-step process to career excellence.
                    </p>
                </div>
                <div className="relative grid grid-cols-1 gap-12 md:grid-cols-3">
                    {/* Vertical line for mobile, horizontal for desktop */}
                    <div className="absolute left-6 top-0 hidden h-full w-px bg-slate-200 md:left-0 md:top-1/2 md:block md:h-px md:w-full dark:bg-slate-800"></div>
                    {/* Step 1 */}
                    <div className="relative flex flex-col items-start gap-6 md:items-center md:text-center">
                        <div className="z-10 flex h-12 w-12 items-center justify-center rounded-full bg-primary text-xl font-black text-white shadow-lg ring-8 ring-background-light dark:ring-background-dark">
                            1
                        </div>
                        <div>
                            <h4 className="text-xl font-bold text-charcoal dark:text-white">
                                Select Your Role
                            </h4>
                            <p className="mt-2 text-slate-500 dark:text-slate-400">
                                Choose from 500+ professional paths including
                                FAANG-level engineering, finance, and
                                management.
                            </p>
                        </div>
                    </div>
                    {/* Step 2 */}
                    <div className="relative flex flex-col items-start gap-6 md:items-center md:text-center">
                        <div className="z-10 flex h-12 w-12 items-center justify-center rounded-full bg-primary text-xl font-black text-white shadow-lg ring-8 ring-background-light dark:ring-background-dark">
                            2
                        </div>
                        <div>
                            <h4 className="text-xl font-bold text-charcoal dark:text-white">
                                Conduct Interview
                            </h4>
                            <p className="mt-2 text-slate-500 dark:text-slate-400">
                                Engage in a pressure-tested environment with our
                                adaptive AI that simulates real interviewer
                                behavior.
                            </p>
                        </div>
                    </div>
                    {/* Step 3 */}
                    <div className="relative flex flex-col items-start gap-6 md:items-center md:text-center">
                        <div className="z-10 flex h-12 w-12 items-center justify-center rounded-full bg-primary text-xl font-black text-white shadow-lg ring-8 ring-background-light dark:ring-background-dark">
                            3
                        </div>
                        <div>
                            <h4 className="text-xl font-bold text-charcoal dark:text-white">
                                Analyze Results
                            </h4>
                            <p className="mt-2 text-slate-500 dark:text-slate-400">
                                Review granular feedback on your performance and
                                follow your personalized roadmap to improvement.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
