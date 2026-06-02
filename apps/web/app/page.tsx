import { Header } from "@/components/landing/Header";
import { Hero } from "@/components/landing/Hero";
import { Features } from "@/components/landing/Features";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { Pricing } from "@/components/landing/Pricing";
import { CTA } from "@/components/landing/CTA";
import { Footer } from "@/components/landing/Footer";
import { LandingModal } from "@/components/landing/LandingModal";

export default function Home() {
    return (
        <div className="relative flex h-auto min-h-screen w-full flex-col overflow-x-hidden animate-fade-in">
            <Header />
            <main className="flex-grow pt-24">
                <Hero />
                <Features />
                <HowItWorks />
                <Pricing />
                <CTA />
            </main>
            <Footer />
            <LandingModal />
        </div>
    );
}

