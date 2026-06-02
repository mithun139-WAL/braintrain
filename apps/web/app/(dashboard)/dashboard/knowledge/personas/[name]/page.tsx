"use client";

import React, { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { PageHeader } from "@/core/components/ui/PageHeader";
import { Surface } from "@/core/components/ui/Surface";
import { buttonStyles } from "@/core/components/ui/button";
import { usePersona, usePersonaMutations } from "@/hooks/queries/useKnowledge";
import { ArrowLeft, Save, AlertCircle, Plus, X } from "lucide-react";
import { cn } from "@/lib/utils";

export default function EditPersonaPage() {
    const router = useRouter();
    const params = useParams();
    const personaName = params.name as string;
    const isNew = personaName === "new";

    const { data: persona, isLoading } = usePersona(isNew ? "" : personaName);
    const { createMutation, updateMutation } = usePersonaMutations();

    // Form states
    const [name, setName] = useState("");
    const [archetype, setArchetype] = useState("Professional Coach");
    const [pacingSpeed, setPacingSpeed] = useState(1.0);
    const [interruptionFrequency, setInterruptionFrequency] = useState(0.5);
    const [silenceTolerance, setSilenceTolerance] = useState(1.0);
    const [skepticismLevel, setSkepticismLevel] = useState(0.5);
    const [technicalDepth, setTechnicalDepth] = useState(0.5);
    const [followupAggressiveness, setFollowupAggressiveness] = useState(0.5);
    const [verbosityTolerance, setVerbosityTolerance] = useState(0.5);
    const [ambiguityTolerance, setAmbiguityTolerance] = useState(0.5);
    const [pressureIntensity, setPressureIntensity] = useState(0.5);
    const [conversationalWarmth, setConversationalWarmth] = useState(0.5);
    const [challengeEscalation, setChallengeEscalation] = useState("Standard");
    const [acknowledgmentPatterns, setAcknowledgmentPatterns] = useState<string[]>([]);
    const [newPattern, setNewPattern] = useState("");
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (persona && !isNew) {
            setName(persona.name);
            setArchetype(persona.archetype);
            setPacingSpeed(persona.pacingSpeed);
            setInterruptionFrequency(persona.interruptionFrequency);
            setSilenceTolerance(persona.silenceTolerance);
            setSkepticismLevel(persona.skepticismLevel);
            setTechnicalDepth(persona.technicalDepth);
            setFollowupAggressiveness(persona.followupAggressiveness);
            setVerbosityTolerance(persona.verbosityTolerance);
            setAmbiguityTolerance(persona.ambiguityTolerance);
            setPressureIntensity(persona.pressureIntensity);
            setConversationalWarmth(persona.conversationalWarmth);
            setChallengeEscalation(persona.challengeEscalation);
            setAcknowledgmentPatterns(persona.acknowledgmentPatterns || []);
        }
    }, [persona, isNew]);

    const handleAddPattern = (e?: React.FormEvent | React.KeyboardEvent) => {
        if (e) e.preventDefault();
        if (newPattern.trim()) {
            setAcknowledgmentPatterns([...acknowledgmentPatterns, newPattern.trim()]);
            setNewPattern("");
        }
    };

    const handleRemovePattern = (idx: number) => {
        setAcknowledgmentPatterns(acknowledgmentPatterns.filter((_, i) => i !== idx));
    };

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!name.trim()) {
            setError("Persona name is required.");
            return;
        }

        const payload = {
            name: name.trim(),
            archetype: archetype.trim(),
            pacingSpeed,
            interruptionFrequency,
            silenceTolerance,
            skepticismLevel,
            technicalDepth,
            followupAggressiveness,
            verbosityTolerance,
            ambiguityTolerance,
            pressureIntensity,
            conversationalWarmth,
            challengeEscalation,
            acknowledgmentPatterns,
            customPrompts: {},
        };

        try {
            if (isNew) {
                await createMutation.mutateAsync(payload);
            } else {
                await updateMutation.mutateAsync({ name: personaName, data: payload });
            }
            router.push("/dashboard/knowledge");
        } catch (err: any) {
            setError(err || "Failed to save persona configuration.");
        }
    };

    if (isLoading && !isNew) {
        return (
            <div className="py-12 flex flex-col items-center justify-center">
                <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mb-2" />
                <p className="text-xs text-muted-foreground">Loading persona configuration...</p>
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-6 pb-12">
            <div>
                <button
                    type="button"
                    onClick={() => router.push("/dashboard/knowledge")}
                    className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors mb-2"
                >
                    <ArrowLeft size={14} />
                    Back to Knowledge Base
                </button>
            </div>
            <PageHeader
                eyebrow="Admin Panel"
                title={isNew ? "Create Persona" : `Edit Persona: ${persona?.name}`}
                description="Configure the characteristic profile, tone adjustments, Socratic drilling depth, and acknowledgment patterns of the AI interviewer."
            />

            {error && (
                <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4 flex gap-3 text-xs text-red-500">
                    <AlertCircle size={16} className="shrink-0 mt-0.5" />
                    <span>{error}</span>
                </div>
            )}

            <form onSubmit={handleSave} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Core Config */}
                <div className="lg:col-span-2 space-y-6">
                    <Surface padding="lg" className="bg-card border border-border space-y-5">
                        <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground/80 mb-2 border-b border-border/40 pb-2">
                            Identity & Rules
                        </h3>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-1.5">
                                <label className="text-[11px] font-semibold text-muted-foreground">Persona Name</label>
                                <input
                                    type="text"
                                    disabled={!isNew}
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    placeholder="e.g. Skeptical Architect, Warm Coach"
                                    className="w-full rounded-lg border border-border/60 bg-muted/20 px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground/50 focus:border-primary/50 focus:outline-none disabled:opacity-50"
                                />
                            </div>
                            <div className="space-y-1.5">
                                <label className="text-[11px] font-semibold text-muted-foreground">Archetype Title</label>
                                <input
                                    type="text"
                                    value={archetype}
                                    onChange={(e) => setArchetype(e.target.value)}
                                    placeholder="e.g. Coder, Recruiter, CTO"
                                    className="w-full rounded-lg border border-border/60 bg-muted/20 px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground/50 focus:border-primary/50 focus:outline-none"
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-1.5">
                                <label className="text-[11px] font-semibold text-muted-foreground">Challenge Escalation Logic</label>
                                <select
                                    value={challengeEscalation}
                                    onChange={(e) => setChallengeEscalation(e.target.value)}
                                    className="w-full rounded-lg border border-border/60 bg-muted/20 px-3 py-2 text-xs text-foreground focus:border-primary/50 focus:outline-none"
                                >
                                    <option value="Standard">Standard Adaptation</option>
                                    <option value="TradeoffDrilling">Socratic Tradeoff Drilling</option>
                                    <option value="STARVerification">STAR Structure Verification</option>
                                    <option value="PressureEscalation">Aggressive Pressure Escalation</option>
                                </select>
                            </div>
                            <div className="space-y-1.5">
                                <label className="text-[11px] font-semibold text-muted-foreground">Silence Tolerance (Seconds)</label>
                                <input
                                    type="number"
                                    step="0.1"
                                    min="0.1"
                                    max="5.0"
                                    value={silenceTolerance}
                                    onChange={(e) => setSilenceTolerance(parseFloat(e.target.value))}
                                    className="w-full rounded-lg border border-border/60 bg-muted/20 px-3 py-2 text-xs text-foreground focus:border-primary/50 focus:outline-none"
                                />
                            </div>
                        </div>
                    </Surface>

                    {/* sliders surface */}
                    <Surface padding="lg" className="bg-card border border-border space-y-6">
                        <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground/80 mb-2 border-b border-border/40 pb-2">
                            Tone & Behavior Dimensions
                        </h3>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6">
                            <SliderField
                                label="Conversational Warmth"
                                description="High values make the agent polite; low values yield cold, clinical interviews."
                                min={0.0}
                                max={1.0}
                                step={0.05}
                                value={conversationalWarmth}
                                onChange={setConversationalWarmth}
                            />
                            <SliderField
                                label="Skepticism Level"
                                description="Likelihood of questioning assertions and drilling details."
                                min={0.0}
                                max={1.0}
                                step={0.05}
                                value={skepticismLevel}
                                onChange={setSkepticismLevel}
                            />
                            <SliderField
                                label="Technical Depth"
                                description="Forces deep-dive queries vs high-level conceptual questions."
                                min={0.0}
                                max={1.0}
                                step={0.05}
                                value={technicalDepth}
                                onChange={setTechnicalDepth}
                            />
                            <SliderField
                                label="Pressure Intensity"
                                description="Controls intensity of interruption and skepticism adaptively."
                                min={0.0}
                                max={1.0}
                                step={0.05}
                                value={pressureIntensity}
                                onChange={setPressureIntensity}
                            />
                            <SliderField
                                label="Interruption Frequency"
                                description="Probability of speaking over a verbose candidate."
                                min={0.0}
                                max={1.0}
                                step={0.05}
                                value={interruptionFrequency}
                                onChange={setInterruptionFrequency}
                            />
                            <SliderField
                                label="Pacing Speed"
                                description="Speech and delay multiplier (lower = slower)."
                                min={0.5}
                                max={1.5}
                                step={0.05}
                                value={pacingSpeed}
                                onChange={setPacingSpeed}
                            />
                            <SliderField
                                label="Verbosity Tolerance"
                                description="Maximum length candidate can talk before agent intercepts."
                                min={0.0}
                                max={1.0}
                                step={0.05}
                                value={verbosityTolerance}
                                onChange={setVerbosityTolerance}
                            />
                            <SliderField
                                label="Ambiguity Tolerance"
                                description="Controls threshold for asking for clarification."
                                min={0.0}
                                max={1.0}
                                step={0.05}
                                value={ambiguityTolerance}
                                onChange={setAmbiguityTolerance}
                            />
                        </div>
                    </Surface>
                </div>

                {/* Verbal Filler / Acknowledgment Patterns */}
                <div className="space-y-6">
                    <Surface padding="lg" className="bg-card border border-border flex flex-col justify-between h-full min-h-[400px]">
                        <div className="space-y-4">
                            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground/80 mb-2 border-b border-border/40 pb-2">
                                Verbal Fillers
                            </h3>
                            <p className="text-[10px] text-muted-foreground leading-relaxed">
                                Acknowledgment patterns (e.g. Socratic headers) the agent randomly pre-pends to its follow-up speech to simulate realistic turn-taking.
                            </p>

                            <div className="flex gap-2 pt-1">
                                <input
                                    type="text"
                                    placeholder="Add filler pattern..."
                                    value={newPattern}
                                    onChange={(e) => setNewPattern(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === "Enter") {
                                            handleAddPattern(e);
                                        }
                                    }}
                                    className="flex-1 rounded-lg border border-border/60 bg-muted/20 px-3 py-1.5 text-xs text-foreground placeholder:text-muted-foreground/50 focus:border-primary/50 focus:outline-none"
                                />
                                <button
                                    type="button"
                                    onClick={() => handleAddPattern()}
                                    className={cn(buttonStyles({ variant: "secondary", size: "sm" }), "px-3 rounded-lg")}
                                >
                                    <Plus size={14} />
                                </button>
                            </div>

                            <div className="flex flex-wrap gap-1.5 pt-2 max-h-[220px] overflow-y-auto custom-scrollbar">
                                {acknowledgmentPatterns.length === 0 ? (
                                    <span className="text-[10px] text-muted-foreground/60 italic">No verbal fillers configured.</span>
                                ) : (
                                    acknowledgmentPatterns.map((pattern, idx) => (
                                        <span
                                            key={idx}
                                            className="inline-flex items-center gap-1.5 rounded-lg bg-primary/10 border border-primary/20 px-2 py-1 text-xs text-primary font-medium"
                                        >
                                            {pattern}
                                            <button
                                                type="button"
                                                onClick={() => handleRemovePattern(idx)}
                                                className="hover:text-primary-dark transition-colors"
                                            >
                                                <X size={10} />
                                            </button>
                                        </span>
                                    ))
                                )}
                            </div>
                        </div>

                        <div className="border-t border-border/40 pt-4 mt-6 flex flex-col gap-2">
                            <button
                                type="button"
                                onClick={handleSave}
                                disabled={createMutation.isPending || updateMutation.isPending}
                                className={cn(buttonStyles(), "w-full justify-center")}
                            >
                                <Save size={16} className="mr-2" />
                                {createMutation.isPending || updateMutation.isPending ? "Saving..." : "Save Configuration"}
                            </button>
                            <button
                                type="button"
                                onClick={() => router.push("/dashboard/knowledge")}
                                className={cn(buttonStyles({ variant: "secondary" }), "w-full justify-center")}
                            >
                                Cancel
                            </button>
                        </div>
                    </Surface>
                </div>
            </form>
        </div>
    );
}

// Slider Field helper
interface SliderFieldProps {
    label: string;
    description: string;
    min: number;
    max: number;
    step: number;
    value: number;
    onChange: (val: number) => void;
}

function SliderField({ label, description, min, max, step, value, onChange }: SliderFieldProps) {
    return (
        <div className="space-y-1.5">
            <div className="flex items-center justify-between">
                <label className="text-[11px] font-bold text-foreground capitalize">{label}</label>
                <span className="text-xs font-semibold text-primary">{value.toFixed(2)}</span>
            </div>
            <p className="text-[10px] text-muted-foreground/90 leading-normal">{description}</p>
            <input
                type="range"
                min={min}
                max={max}
                step={step}
                value={value}
                onChange={(e) => onChange(parseFloat(e.target.value))}
                className="w-full accent-primary bg-muted/60 h-1 rounded-lg cursor-pointer appearance-none mt-2"
            />
        </div>
    );
}
