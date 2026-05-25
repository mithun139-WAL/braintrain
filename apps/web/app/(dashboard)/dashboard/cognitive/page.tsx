"use client";

import React, { useState, useMemo, useEffect } from "react";
import Link from "next/link";
import {
    Brain,
    Calendar,
    Activity,
    MessageSquare,
    TrendingUp,
    ShieldAlert,
    HelpCircle,
    RotateCcw,
    Zap,
    Loader2
} from "lucide-react";
import { PageHeader } from "@/core/components/ui/PageHeader";
import { Surface } from "@/core/components/ui/Surface";
import { buttonStyles } from "@/core/components/ui/button";
import { StatCard } from "@/components/dashboard/StatCard";
import { useCognitiveAnalytics } from "@/hooks/queries/useAnalytics";
import { cn } from "@/lib/utils";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer
} from "recharts";

// --- Node coordinate layout generator ---
interface GraphNode {
    id: string;
    name: string;
    type: string;
    mastery: number;
    isFragile: boolean;
    isWeak: boolean;
    x: number;
    y: number;
}

interface GraphLink {
    source: string;
    target: string;
    type: string;
    strength: number;
}

export default function CognitivePage() {
    const { data: response, isLoading, error } = useCognitiveAnalytics();
    const cognitiveData = response?.data;

    const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

    // --- Interactive Graph Simulation ---
    const [graphNodes, setGraphNodes] = useState<GraphNode[]>([]);
    const [graphLinks, setGraphLinks] = useState<GraphLink[]>([]);

    const rawNodes = cognitiveData?.nodes || [];
    const rawEdges = cognitiveData?.edges || [];

    useEffect(() => {
        if (rawNodes.length === 0) return;

        // Initialize positions in a circle layout
        const initialNodes: GraphNode[] = rawNodes.map((n, i) => {
            const angle = (i / rawNodes.length) * 2 * Math.PI;
            const radius = 130;
            return {
                id: n.id,
                name: n.conceptName,
                type: n.conceptType,
                mastery: n.masteryLevel,
                isFragile: n.isFragile,
                isWeak: n.isWeakRecall,
                x: 250 + radius * Math.cos(angle),
                y: 200 + radius * Math.sin(angle)
            };
        });

        const initialLinks: GraphLink[] = rawEdges.map(e => ({
            source: e.sourceNodeId,
            target: e.targetNodeId,
            type: e.relationshipType,
            strength: e.strength
        }));

        // Run basic relaxation layout iterations (Force-directed layout)
        let nodes = [...initialNodes];
        for (let iter = 0; iter < 60; iter++) {
            // Gravity to center
            nodes = nodes.map(node => {
                const dx = 250 - node.x;
                const dy = 200 - node.y;
                return {
                    ...node,
                    x: node.x + dx * 0.05,
                    y: node.y + dy * 0.05
                };
            });

            // Repulsion between nodes
            for (let i = 0; i < nodes.length; i++) {
                for (let j = i + 1; j < nodes.length; j++) {
                    const dx = nodes[j].x - nodes[i].x;
                    const dy = nodes[j].y - nodes[i].y;
                    const dist = Math.sqrt(dx * dx + dy * dy) || 1.0;
                    if (dist < 80) {
                        const force = (80 - dist) * 0.15;
                        const fx = (dx / dist) * force;
                        const fy = (dy / dist) * force;
                        nodes[i].x -= fx;
                        nodes[i].y -= fy;
                        nodes[j].x += fx;
                        nodes[j].y += fy;
                    }
                }
            }

            // Attraction along links
            initialLinks.forEach(link => {
                const sNode = nodes.find(n => n.id === link.source);
                const tNode = nodes.find(n => n.id === link.target);
                if (sNode && tNode) {
                    const dx = tNode.x - sNode.x;
                    const dy = tNode.y - sNode.y;
                    const dist = Math.sqrt(dx * dx + dy * dy) || 1.0;
                    const desiredDist = 100;
                    const force = (dist - desiredDist) * 0.08 * link.strength;
                    const fx = (dx / dist) * force;
                    const fy = (dy / dist) * force;
                    sNode.x += fx;
                    sNode.y += fy;
                    tNode.x -= fx;
                    tNode.y -= fy;
                }
            });
        }

        setGraphNodes(nodes);
        setGraphLinks(initialLinks);

        // Auto select first node
        if (nodes.length > 0) {
            setSelectedNode(nodes[0]);
        }
    }, [rawNodes.length, rawEdges.length]);

    // Trajectory formatting
    const trajectoryData = useMemo(() => {
        if (!cognitiveData?.trajectory) return [];
        const t = cognitiveData.trajectory;
        const length = t.confidence?.length || 0;
        return Array.from({ length }).map((_, i) => ({
            session: `Session ${i + 1}`,
            confidence: t.confidence?.[i],
            communication: t.communication?.[i],
            recall: t.recall_stability?.[i],
            strategic: t.strategic_thinking?.[i]
        }));
    }, [cognitiveData?.trajectory]);

    // Full Node stats representation
    const selectedNodeDetails = useMemo(() => {
        if (!selectedNode || !cognitiveData) return null;
        return cognitiveData.nodes.find(n => n.id === selectedNode.id);
    }, [selectedNode, cognitiveData]);

    if (isLoading) {
        return (
            <div className="flex h-screen items-center justify-center">
                <Loader2 className="animate-spin text-primary" size={40} />
            </div>
        );
    }

    if (error || !cognitiveData) {
        return (
            <div className="flex min-h-[300px] flex-col items-center justify-center gap-4 text-center">
                <Brain size={36} className="text-ruby" />
                <h3 className="text-lg font-bold text-foreground">Failed to load cognitive graph</h3>
                <p className="text-muted-foreground text-sm">Please retry or run another session.</p>
            </div>
        );
    }

    return (
        <div className="flex w-full flex-col gap-8 pb-12">
            <PageHeader
                eyebrow="Intelligence Center"
                title="Cognitive Performance Map"
                description="Obsidian-style knowledge tracking, stress-resistant recall stability, structural communication analyses, and meta-cognitive timelines."
                meta={
                    <>
                        <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 text-sm text-foreground shadow-card">
                            <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">Mastery</span>
                            <span className="font-semibold text-foreground">{cognitiveData.mindState?.memoryRecallStrength || 50}%</span>
                        </div>
                        <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 text-sm text-foreground shadow-card">
                            <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">Strategic</span>
                            <span className="font-semibold text-foreground">{cognitiveData.mindState?.strategicThinking || 50}%</span>
                        </div>
                    </>
                }
                actions={
                    <>
                        <Link href="/dashboard/training" className={buttonStyles({ variant: "secondary" })}>
                            View Reps Plan
                        </Link>
                        <Link href="/dashboard/sessions/start" className={buttonStyles()}>
                            <Zap size={16} />
                            Start Practice Session
                        </Link>
                    </>
                }
            />

            {/* --- Apple Health Stats --- */}
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
                <StatCard
                    label="Recall Pacing / Latency"
                    value={cognitiveData.nodes.length > 0
                        ? (cognitiveData.nodes.reduce((sum, n) => sum + n.recallLatency, 0) / cognitiveData.nodes.length).toFixed(1)
                        : "1.5"}
                    unit="s"
                    trend={0}
                    icon={Activity}
                    iconColor="text-sky-500"
                    iconBg="bg-sky-500/10"
                    accentColor="bg-sky-500"
                />
                <StatCard
                    label="Executive Presence"
                    value={Math.round(cognitiveData.mindState?.executivePresence || 50)}
                    unit="%"
                    trend={0}
                    icon={TrendingUp}
                    iconColor="text-emerald"
                    iconBg="bg-emerald/10"
                    accentColor="bg-emerald"
                />
                <StatCard
                    label="Speaking Consistency"
                    value={Math.round(cognitiveData.mindState?.speakingConsistency || 50)}
                    unit="%"
                    trend={0}
                    icon={MessageSquare}
                    iconColor="text-primary"
                    iconBg="bg-primary/10"
                    accentColor="bg-primary"
                />
                <StatCard
                    label="Fragile Concepts"
                    value={cognitiveData.nodes.filter(n => n.isFragile).length}
                    unit="topics"
                    trend={0}
                    icon={ShieldAlert}
                    iconColor="text-ruby"
                    iconBg="bg-ruby/10"
                    accentColor="bg-ruby"
                />
            </div>

            {/* --- Obsidian Graph & Concept Inspection --- */}
            <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
                <Surface padding="none" className="lg:col-span-2 relative overflow-hidden bg-card border border-border rounded-3xl h-[450px]">
                    <div className="absolute top-4 left-5 z-10">
                        <h3 className="text-sm font-semibold text-foreground">Candidate Cognitive Knowledge Map</h3>
                        <p className="text-xs text-muted-foreground">Obsidian-style conceptual representation. Hover or click nodes to inspect.</p>
                    </div>

                    <svg className="w-full h-full bg-[#030307]">
                        <defs>
                            <marker id="arrow" viewBox="0 0 10 10" refX="24" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                                <path d="M 0 0 L 10 5 L 0 10 z" fill="#1e1e24" />
                            </marker>
                        </defs>

                        {/* Link lines */}
                        {graphLinks.map((link, idx) => {
                            const source = graphNodes.find(n => n.id === link.source);
                            const target = graphNodes.find(n => n.id === link.target);
                            if (!source || !target) return null;
                            return (
                                <line
                                    key={idx}
                                    x1={source.x}
                                    y1={source.y}
                                    x2={target.x}
                                    y2={target.y}
                                    stroke={link.type === "prerequisite" ? "hsl(var(--primary))" : "#2a2a35"}
                                    strokeWidth={link.strength * 2.5}
                                    strokeDasharray={link.type === "confusion_overlap" ? "4 4" : "0"}
                                    markerEnd="url(#arrow)"
                                    opacity={0.65}
                                />
                            );
                        })}

                        {/* Nodes */}
                        {graphNodes.map(node => (
                            <g
                                key={node.id}
                                transform={`translate(${node.x}, ${node.y})`}
                                className="cursor-pointer group"
                                onClick={() => setSelectedNode(node)}
                            >
                                <circle
                                    r={selectedNode?.id === node.id ? 10 : 7}
                                    className={cn(
                                        "transition-all duration-300",
                                        node.isFragile
                                            ? "fill-ruby shadow-lg shadow-ruby/50 animate-pulse"
                                            : node.isWeak
                                            ? "fill-gold shadow-lg shadow-gold/30"
                                            : "fill-emerald"
                                    )}
                                />
                                <text
                                    y={-14}
                                    textAnchor="middle"
                                    className="text-[10px] font-medium fill-muted-foreground group-hover:fill-foreground select-none transition-colors"
                                >
                                    {node.name}
                                </text>
                            </g>
                        ))}
                    </svg>
                </Surface>

                <Surface padding="lg" className="flex flex-col border border-border rounded-3xl bg-card">
                    {selectedNodeDetails ? (
                        <div className="flex-1 space-y-5">
                            <div>
                                <span className={cn(
                                    "px-2.5 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider",
                                    selectedNodeDetails.conceptType === "technology" ? "bg-sky-500/10 text-sky-500" :
                                    selectedNodeDetails.conceptType === "framework" ? "bg-primary/10 text-primary" :
                                    "bg-emerald/10 text-emerald"
                                )}>
                                    {selectedNodeDetails.conceptType}
                                </span>
                                <h3 className="font-display text-title-lg text-foreground mt-2">{selectedNodeDetails.conceptName}</h3>
                            </div>

                            <div className="grid grid-cols-2 gap-4 border-t border-border/50 pt-4">
                                <InspectValue label="Mastery level" value={`${selectedNodeDetails.masteryLevel}%`} />
                                <InspectValue label="Recall stability" value={`${selectedNodeDetails.pressureRecallStability}%`} />
                                <InspectValue label="Recall latency" value={`${selectedNodeDetails.recallLatency}s`} />
                                <InspectValue label="Retention strength" value={`${selectedNodeDetails.retentionStrength}%`} />
                                <InspectValue label="Familiarity" value={`${selectedNodeDetails.familiarityScore}%`} />
                                <InspectValue label="Exposures" value={selectedNodeDetails.exposureCount} />
                            </div>

                            <div className="border-t border-border/50 pt-4 space-y-2">
                                <p className="text-xs font-semibold text-foreground/80">Coaching Status</p>
                                {selectedNodeDetails.isFragile ? (
                                    <div className="flex items-start gap-2 rounded-2xl bg-ruby/5 border border-ruby/20 p-3">
                                        <ShieldAlert size={14} className="text-ruby mt-0.5" />
                                        <p className="text-[11px] text-ruby leading-normal">
                                            <strong>FRAGILE UNDER PRESSURE:</strong> Candidate answered correctly once, but failed second time or shows volatility under stress.
                                        </p>
                                    </div>
                                ) : selectedNodeDetails.isWeakRecall ? (
                                    <div className="flex items-start gap-2 rounded-2xl bg-gold/5 border border-gold/20 p-3">
                                        <RotateCcw size={14} className="text-gold mt-0.5" />
                                        <p className="text-[11px] text-gold leading-normal">
                                            <strong>DECAYING RETENTION:</strong> Recall pathway is fading. Spaced repetition is recommended.
                                        </p>
                                    </div>
                                ) : (
                                    <div className="flex items-start gap-2 rounded-2xl bg-emerald/5 border border-emerald/20 p-3">
                                        <Brain size={14} className="text-emerald mt-0.5" />
                                        <p className="text-[11px] text-emerald leading-normal">
                                            <strong>STABLE MEMORY:</strong> Concept is highly recallable and stable under load.
                                        </p>
                                    </div>
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="flex-1 flex flex-col items-center justify-center text-center text-muted-foreground text-xs">
                            Select a node in the Obsidian graph to inspect memory metrics.
                        </div>
                    )}
                </Surface>
            </div>

            {/* --- Trajectory and Spaced Repetition Drills --- */}
            <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
                <Surface padding="lg" className="lg:col-span-2 flex flex-col border border-border rounded-3xl bg-card">
                    <div className="pb-6">
                        <h3 className="font-display text-title-md text-foreground">Longitudinal Trajectory Chart</h3>
                        <p className="mt-1 text-body-sm text-muted-foreground">
                            Candidate growth velocities across metrics, tracking stress-resistant memory, strategic pathing, and presence.
                        </p>
                    </div>
                    <div className="h-[300px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={trajectoryData}>
                                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                                <XAxis dataKey="session" className="text-[10px] fill-muted-foreground" />
                                <YAxis domain={[30, 100]} className="text-[10px] fill-muted-foreground" />
                                <Tooltip
                                    contentStyle={{
                                        borderRadius: "12px",
                                        background: "hsl(var(--card))",
                                        border: "1px solid hsl(var(--border))",
                                        color: "hsl(var(--foreground))"
                                    }}
                                />
                                <Legend />
                                <Line type="monotone" dataKey="confidence" stroke="hsl(var(--primary))" strokeWidth={2} name="Confidence" />
                                <Line type="monotone" dataKey="communication" stroke="#0ea5e9" strokeWidth={2} name="Communication" />
                                <Line type="monotone" dataKey="recall" stroke="#f59e0b" strokeWidth={2} name="Recall Stability" />
                                <Line type="monotone" dataKey="strategic" stroke="#10b981" strokeWidth={2} name="Strategic Thinking" />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </Surface>

                <Surface padding="lg" className="flex flex-col border border-border rounded-3xl bg-card h-[380px] overflow-hidden">
                    <div className="pb-4 border-b border-border/50">
                        <h3 className="font-display text-title-md text-foreground">Spaced Repetition Drills</h3>
                        <p className="mt-1 text-body-sm text-muted-foreground">Next adaptive reinforcement tasks.</p>
                    </div>
                    <div className="flex-1 overflow-y-auto pt-4 space-y-4 pr-1">
                        {cognitiveData.drills.length === 0 ? (
                            <div className="text-center py-8 text-xs text-muted-foreground">
                                No drills scheduled. All pathways are reinforced!
                            </div>
                        ) : (
                            cognitiveData.drills.map((drill, idx) => (
                                <div key={idx} className="rounded-2xl border border-border-subtle bg-muted/40 p-4 space-y-2">
                                    <div className="flex items-center justify-between">
                                        <span className="text-[10px] font-bold uppercase tracking-wider text-primary bg-primary/10 px-2 py-0.5 rounded">
                                            {drill.drillType.replace("_", " ")}
                                        </span>
                                        <span className={cn(
                                            "text-[10px] font-semibold px-2 py-0.5 rounded",
                                            drill.recommendedDifficulty === "HIGH" ? "bg-ruby/10 text-ruby" : "bg-gold/10 text-gold"
                                        )}>
                                            {drill.recommendedDifficulty} Difficulty
                                        </span>
                                    </div>
                                    <p className="text-xs font-semibold text-foreground">{drill.conceptName}</p>
                                    <p className="text-[11px] text-muted-foreground leading-relaxed">{drill.instruction}</p>
                                </div>
                            ))
                        )}
                    </div>
                </Surface>
            </div>

            {/* --- Meta-Cognitive Coach Guidelines --- */}
            <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
                <Surface padding="lg" className="border border-border rounded-3xl bg-card">
                    <div className="pb-4 border-b border-border/50">
                        <h3 className="font-display text-title-md text-foreground">Cognitive Recovery Protocol</h3>
                        <p className="mt-1 text-body-sm text-muted-foreground">Mental anchor plans for recall failures under stress.</p>
                    </div>
                    <div className="pt-4 space-y-4">
                        {cognitiveData.recoveryExercises.length === 0 ? (
                            <p className="text-xs text-muted-foreground">No custom recovery triggers needed.</p>
                        ) : (
                            cognitiveData.recoveryExercises.map((ex, idx) => (
                                <div key={idx} className="flex gap-3 items-start">
                                    <div className="size-6 rounded-full bg-primary/10 text-primary flex items-center justify-center flex-shrink-0 mt-0.5 text-xs font-bold">
                                        {idx + 1}
                                    </div>
                                    <div className="space-y-1">
                                        <p className="text-xs font-bold text-foreground">Stall trigger on: {ex.conceptName}</p>
                                        <p className="text-xs text-muted-foreground leading-relaxed">{ex.exercise}</p>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </Surface>

                <Surface padding="lg" className="border border-border rounded-3xl bg-card">
                    <div className="pb-4 border-b border-border/50">
                        <h3 className="font-display text-title-md text-foreground">Meta-Cognitive Strategic Frameworks</h3>
                        <p className="mt-1 text-body-sm text-muted-foreground">Rubrics and heuristics to structure complexity during interviews.</p>
                    </div>
                    <div className="pt-4 space-y-4 overflow-y-auto max-h-[250px]">
                        <FrameworkCard
                            domain="Backend System Design"
                            rules={[
                                "Define bottlenecks and scale limits first.",
                                "Map trade-offs between SQL (consistency) vs NoSQL (availability).",
                                "Never jump to implementation details before client-server boundaries are set."
                            ]}
                        />
                        <FrameworkCard
                            domain="Communication & Storytelling (PREP)"
                            rules={[
                                "Open answers with a direct thesis statement.",
                                "Justify reasons clearly and detail a single structured scenario.",
                                "Summarize back to the point instead of trailing off."
                            ]}
                        />
                    </div>
                </Surface>
            </div>
        </div>
    );
}

function InspectValue({ label, value }: { label: string; value: string | number }) {
    return (
        <div className="rounded-2xl border border-border bg-card/50 p-3 text-center">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">{label}</p>
            <p className="mt-1 text-sm font-bold text-foreground">{value}</p>
        </div>
    );
}

function FrameworkCard({ domain, rules }: { domain: string; rules: string[] }) {
    return (
        <div className="rounded-2xl border border-border bg-muted/20 p-4 space-y-2">
            <p className="text-xs font-bold text-primary">{domain}</p>
            <ul className="list-disc pl-4 space-y-1 text-[11px] text-muted-foreground leading-normal">
                {rules.map((rule, idx) => (
                    <li key={idx}>{rule}</li>
                ))}
            </ul>
        </div>
    );
}
