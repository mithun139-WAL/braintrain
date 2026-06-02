import { Rocket } from "lucide-react";
import { Surface } from "@/core/components/ui/Surface";

export function PromoCard() {
    return (
        <Surface
            variant="hero"
            padding="xl"
            className="relative overflow-hidden border-primary/20 bg-[linear-gradient(135deg,hsl(var(--primary)/0.16),hsl(var(--background-dark)))] text-white"
        >
            <div className="absolute right-[-4rem] top-[-4rem] h-40 w-40 rounded-full bg-white/10 blur-3xl" />
            <div className="relative space-y-4">
                <div className="flex size-12 items-center justify-center rounded-2xl border border-white/15 bg-white/10">
                    <Rocket size={20} />
                </div>
                <div className="space-y-2">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-white/70">Coming Soon</p>
                    <h3 className="font-display text-title-lg text-white">AI avatar interviews</h3>
                    <p className="text-body-sm text-white/75">
                        A richer mock-interview format with more lifelike presence, pacing pressure, and conversational variation is on the roadmap.
                    </p>
                </div>
                <div className="inline-flex items-center rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/85">
                    Beta queue
                </div>
            </div>
        </Surface>
    );
}
