"use client";
 
import React, { useState } from "react";
import Link from "next/link";
import { PageHeader } from "@/core/components/ui/PageHeader";
import { Surface } from "@/core/components/ui/Surface";
import { buttonStyles } from "@/core/components/ui/button";
import { useGetProfile } from "@/hooks/queries/useGetProfile";
import { 
    usePersonas, 
    useDocuments, 
    usePersonaMutations, 
    useDocumentMutations, 
    useJobAnalysisMutation,
    useOptimizationHistory,
    useOptimizeProfileMutation,
    useDeleteOptimizationMutation
} from "@/hooks/queries/useKnowledge";
import { 
    Users, 
    FileText, 
    Plus, 
    Trash2, 
    Edit, 
    Sliders, 
    BookOpen, 
    AlertCircle, 
    Search,
    Brain,
    Building2,
    Compass,
    Sparkles,
    Briefcase,
    CheckCircle2,
    Copy,
    Check,
    Upload,
    History,
    ArrowRight,
    TrendingUp,
    FileCheck,
    ShieldAlert
} from "lucide-react";
import { cn } from "@/lib/utils";
 
export default function KnowledgeBaseDashboard() {
    const [activeTab, setActiveTab] = useState<"personas" | "documents" | "analyzer" | "optimizer">("personas");
    const [searchQuery, setSearchQuery] = useState("");
 
    // Profile RBAC check
    const { data: profileResponse } = useGetProfile();
    const planType = profileResponse?.data?.planType || "FREE";
    const email = profileResponse?.data?.email || "";
    const isAdmin = planType === "ADMIN" || email.toLowerCase().includes("admin") || email.endsWith("@braintrain.com");

    const { data: personas, isLoading: loadingPersonas } = usePersonas();
    const { data: documents, isLoading: loadingDocs } = useDocuments();
    
    const { deleteMutation: deletePersona } = usePersonaMutations();
    const { deleteMutation: deleteDocument } = useDocumentMutations();

    // Job Analyzer state
    const [roleTitle, setRoleTitle] = useState("");
    const [jobDescription, setJobDescription] = useState("");
    const [analysisResult, setAnalysisResult] = useState<any | null>(null);
    const [analysisError, setAnalysisError] = useState<string | null>(null);
    const analyzeJobMutation = useJobAnalysisMutation();

    // Career Optimizer state
    const [currentRole, setCurrentRole] = useState("");
    const [targetRole, setTargetRole] = useState("");
    const [resumeFile, setResumeFile] = useState<File | null>(null);
    const [linkedinFile, setLinkedinFile] = useState<File | null>(null);
    const [naukriFile, setNaukriFile] = useState<File | null>(null);
    
    const [selectedOptId, setSelectedOptId] = useState<string | null>(null);
    const [copiedId, setCopiedId] = useState<string | null>(null);
    const [optSubTab, setOptSubTab] = useState<"linkedin-headline" | "linkedin-about" | "resume-summary" | "naukri" | "skills">("linkedin-headline");
    const [aboutTab, setAboutTab] = useState<"professional" | "story" | "recruiter">("professional");

    const { data: optHistory, isLoading: loadingHistory } = useOptimizationHistory();
    const optimizeMutation = useOptimizeProfileMutation();
    const deleteOptMutation = useDeleteOptimizationMutation();

    // Copy helper
    const copyToClipboard = (text: string, id: string) => {
        navigator.clipboard.writeText(text);
        setCopiedId(id);
        setTimeout(() => setCopiedId(null), 2000);
    };

    const handleAnalyzeJob = async (e: React.FormEvent) => {
        e.preventDefault();
        setAnalysisError(null);
        setAnalysisResult(null);

        if (!roleTitle.trim()) {
            setAnalysisError("Role title is required.");
            return;
        }
        if (!jobDescription.trim()) {
            setAnalysisError("Job description is required.");
            return;
        }

        try {
            const res = await analyzeJobMutation.mutateAsync({
                roleTitle: roleTitle.trim(),
                jobDescription: jobDescription.trim()
            });
            setAnalysisResult(res);
        } catch (err: any) {
            setAnalysisError(err || "Failed to analyze job role.");
        }
    };

    const handleOptimizeProfile = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!currentRole.trim()) return;
        if (!targetRole.trim()) return;

        try {
            const res = await optimizeMutation.mutateAsync({
                currentRole: currentRole.trim(),
                targetRole: targetRole.trim(),
                resume: resumeFile,
                linkedinPdf: linkedinFile,
                naukriPdf: naukriFile
            });
            setSelectedOptId(res.id);
        } catch (err) {
            console.error("Optimization failed:", err);
        }
    };

    const handleDeletePersona = async (name: string) => {
        if (confirm(`Are you sure you want to delete the persona "${name}"?`)) {
            await deletePersona.mutateAsync(name);
        }
    };

    const handleDeleteDocument = async (id: string, title: string) => {
        if (confirm(`Are you sure you want to delete the document "${title}"?`)) {
            await deleteDocument.mutateAsync(id);
        }
    };

    const handleDeleteOptimization = async (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        if (confirm("Are you sure you want to delete this optimization report?")) {
            await deleteOptMutation.mutateAsync(id);
            if (selectedOptId === id) {
                setSelectedOptId(null);
            }
        }
    };

    const filteredPersonas = personas?.filter(p => 
        p.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
        p.archetype.toLowerCase().includes(searchQuery.toLowerCase())
    ) || [];

    const filteredDocs = documents?.filter(d => 
        d.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
        d.topic.toLowerCase().includes(searchQuery.toLowerCase()) || 
        d.domain.toLowerCase().includes(searchQuery.toLowerCase())
    ) || [];

    const activeOptimization = optHistory?.find(o => o.id === selectedOptId);

    return (
        <div className="flex flex-col gap-6 pb-12">
            <PageHeader
                eyebrow={isAdmin ? "Admin Panel" : "Knowledge Workspace"}
                title="Knowledge Hub & Optimizer"
                description="Access dynamic interviewer profiles, indexed RAG documents, and AI-powered profile transition optimization tools."
                actions={
                    <div className="flex gap-2">
                        {activeTab === "personas" && isAdmin && (
                            <Link href="/dashboard/knowledge/personas/new" className={buttonStyles()}>
                                <Plus size={16} />
                                New Persona
                            </Link>
                        )}
                        {activeTab === "documents" && isAdmin && (
                            <Link href="/dashboard/knowledge/documents/new" className={buttonStyles()}>
                                <Plus size={16} />
                                Ingest Experience/Doc
                            </Link>
                        )}
                    </div>
                }
            />

            {/* Tabs */}
            <div className="flex items-center justify-between border-b border-border/40 pb-px">
                <div className="flex gap-4 overflow-x-auto scrollbar-none">
                    <button
                        onClick={() => { setActiveTab("personas"); setSearchQuery(""); }}
                        className={cn(
                            "flex items-center gap-2 border-b-2 px-1 py-3 text-sm font-semibold transition-all whitespace-nowrap",
                            activeTab === "personas"
                                ? "border-primary text-primary"
                                : "border-transparent text-muted-foreground hover:text-foreground"
                        )}
                    >
                        <Users size={16} />
                        Interviewer Personas ({personas?.length ?? 0})
                    </button>
                    <button
                        onClick={() => { setActiveTab("documents"); setSearchQuery(""); }}
                        className={cn(
                            "flex items-center gap-2 border-b-2 px-1 py-3 text-sm font-semibold transition-all whitespace-nowrap",
                            activeTab === "documents"
                                ? "border-primary text-primary"
                                : "border-transparent text-muted-foreground hover:text-foreground"
                        )}
                    >
                        <FileText size={16} />
                        RAG Knowledge Documents ({documents?.length ?? 0})
                    </button>
                    <button
                        onClick={() => { setActiveTab("analyzer"); setSearchQuery(""); }}
                        className={cn(
                            "flex items-center gap-2 border-b-2 px-1 py-3 text-sm font-semibold transition-all whitespace-nowrap",
                            activeTab === "analyzer"
                                ? "border-primary text-primary"
                                : "border-transparent text-muted-foreground hover:text-foreground"
                        )}
                    >
                        <Sliders size={16} />
                        Job Role Analyzer
                    </button>
                    <button
                        onClick={() => { setActiveTab("optimizer"); setSearchQuery(""); }}
                        className={cn(
                            "flex items-center gap-2 border-b-2 px-1 py-3 text-sm font-semibold transition-all whitespace-nowrap",
                            activeTab === "optimizer"
                                ? "border-primary text-primary"
                                : "border-transparent text-muted-foreground hover:text-foreground"
                        )}
                    >
                        <Sparkles size={16} />
                        AI Career Optimizer
                    </button>
                </div>

                {activeTab !== "analyzer" && activeTab !== "optimizer" && (
                    <div className="relative w-72 hidden md:block">
                        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground/70" />
                        <input
                            type="text"
                            placeholder={activeTab === "personas" ? "Search personas..." : "Search documents..."}
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full rounded-lg border border-border/60 bg-muted/30 py-1.5 pl-9 pr-4 text-xs text-foreground placeholder:text-muted-foreground/60 focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/50"
                        />
                    </div>
                )}
            </div>

            {/* TAB CONTENT: PERSONAS */}
            {activeTab === "personas" && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {loadingPersonas ? (
                        Array.from({ length: 4 }).map((_, i) => (
                            <div key={i} className="h-48 rounded-xl bg-card border border-border animate-pulse" />
                        ))
                    ) : filteredPersonas.length === 0 ? (
                        <div className="col-span-2 py-12 flex flex-col items-center justify-center text-center">
                            <Sliders className="size-8 text-muted-foreground/40 mb-3" />
                            <p className="text-sm font-medium text-muted-foreground">No personas found.</p>
                            {isAdmin && (
                                <Link href="/dashboard/knowledge/personas/new" className="mt-2 text-xs font-semibold text-primary hover:underline">
                                    Create your first dynamic persona
                                </Link>
                            )}
                        </div>
                    ) : (
                        filteredPersonas.map((persona) => (
                            <Surface key={persona.name} padding="md" className="flex flex-col justify-between bg-card border border-border/60">
                                <div className="space-y-3">
                                    <div className="flex items-start justify-between">
                                        <div>
                                            <h3 className="text-sm font-semibold text-foreground">{persona.name}</h3>
                                            <p className="text-[11px] font-medium text-primary mt-0.5">{persona.archetype}</p>
                                        </div>
                                        {isAdmin && (
                                            <div className="flex gap-1.5">
                                                <Link
                                                    href={`/dashboard/knowledge/personas/${persona.name}`}
                                                    className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                                                    title="Edit Persona"
                                                >
                                                    <Edit size={14} />
                                                </Link>
                                                <button
                                                    onClick={() => handleDeletePersona(persona.name)}
                                                    className="rounded-lg p-1.5 text-muted-foreground hover:bg-red-500/10 hover:text-red-500 transition-colors"
                                                    title="Delete Persona"
                                                >
                                                    <Trash2 size={14} />
                                                </button>
                                            </div>
                                        )}
                                    </div>

                                    {/* Characteristics grid */}
                                    <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 pt-1 text-[11px]">
                                        <CharacteristicPill label="Warmth" value={persona.conversationalWarmth} />
                                        <CharacteristicPill label="Skepticism" value={persona.skepticismLevel} />
                                        <CharacteristicPill label="Tech Depth" value={persona.technicalDepth} />
                                        <CharacteristicPill label="Pressure" value={persona.pressureIntensity} />
                                        <CharacteristicPill label="Pacing" value={persona.pacingSpeed} />
                                        <CharacteristicPill label="Interruption" value={persona.interruptionFrequency} />
                                    </div>
                                </div>

                                <div className="border-t border-border/40 mt-4 pt-3 flex items-center justify-between text-[10px] text-muted-foreground">
                                    <span>Escalation: <strong className="text-foreground">{persona.challengeEscalation}</strong></span>
                                    <span>Phrases: <strong className="text-foreground">{persona.acknowledgmentPatterns?.length ?? 0}</strong></span>
                                </div>
                            </Surface>
                        ))
                    )}
                </div>
            )}

            {/* TAB CONTENT: DOCUMENTS */}
            {activeTab === "documents" && (
                <div className="flex flex-col gap-4">
                    {loadingDocs ? (
                        Array.from({ length: 3 }).map((_, i) => (
                            <div key={i} className="h-24 rounded-xl bg-card border border-border animate-pulse" />
                        ))
                    ) : filteredDocs.length === 0 ? (
                        <div className="py-12 flex flex-col items-center justify-center text-center">
                            <BookOpen className="size-8 text-muted-foreground/40 mb-3" />
                            <p className="text-sm font-medium text-muted-foreground">No documents indexed.</p>
                            {isAdmin && (
                                <Link href="/dashboard/knowledge/documents/new" className="mt-2 text-xs font-semibold text-primary hover:underline">
                                    Ingest a new interview experience guide
                                </Link>
                            )}
                        </div>
                    ) : (
                        <div className="overflow-hidden border border-border/40 rounded-xl bg-card">
                            <div className="overflow-x-auto">
                                <table className="w-full text-left border-collapse">
                                    <thead>
                                        <tr className="border-b border-border/40 bg-muted/20 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                                            <th className="px-5 py-3">Document Title</th>
                                            <th className="px-5 py-3">Domain</th>
                                            <th className="px-5 py-3">Topic</th>
                                            <th className="px-5 py-3">Difficulty</th>
                                            <th className="px-5 py-3">Chunks</th>
                                            <th className="px-5 py-3 text-right">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-border/30 text-xs">
                                        {filteredDocs.map((doc) => (
                                            <tr key={doc.id} className="hover:bg-muted/10 transition-colors">
                                                <td className="px-5 py-4">
                                                    <div className="font-semibold text-foreground">{doc.title}</div>
                                                    <div className="text-[10px] text-muted-foreground mt-0.5 max-w-sm truncate" title={doc.source}>
                                                        Source: {doc.source}
                                                    </div>
                                                </td>
                                                <td className="px-5 py-4">
                                                    <span className={cn(
                                                        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold",
                                                        doc.domain === "interview_experience" ? "bg-amber-500/10 text-amber-500" :
                                                        doc.domain === "company_rubric" ? "bg-purple-500/10 text-purple-500" :
                                                        doc.domain === "system_design" ? "bg-sky-500/10 text-sky-500" : "bg-primary/10 text-primary"
                                                    )}>
                                                        {doc.domain === "interview_experience" && <Brain size={10} />}
                                                        {doc.domain === "company_rubric" && <Building2 size={10} />}
                                                        {doc.domain === "system_design" && <Compass size={10} />}
                                                        {doc.domain.replace("_", " ")}
                                                    </span>
                                                </td>
                                                <td className="px-5 py-4 font-medium text-foreground">{doc.topic}</td>
                                                <td className="px-5 py-4">
                                                    <span className={cn(
                                                        "text-[10px] font-bold uppercase",
                                                        doc.difficulty === "HARD" ? "text-red-500" :
                                                        doc.difficulty === "MEDIUM" ? "text-primary" : "text-emerald-500"
                                                    )}>
                                                        {doc.difficulty}
                                                    </span>
                                                </td>
                                                <td className="px-5 py-4">
                                                    <div className="font-semibold text-foreground">{doc.chunkCount ?? 0} Chunks</div>
                                                    <div className="text-[10px] text-muted-foreground">~{doc.tokenCount ?? 0} Tokens</div>
                                                </td>
                                                <td className="px-5 py-4 text-right">
                                                    <div className="flex justify-end gap-1.5">
                                                        {isAdmin ? (
                                                            <>
                                                                <Link
                                                                    href={`/dashboard/knowledge/documents/${doc.id}`}
                                                                    className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                                                                    title="Edit Document"
                                                                >
                                                                    <Edit size={13} />
                                                                </Link>
                                                                <button
                                                                    onClick={() => handleDeleteDocument(doc.id!, doc.title)}
                                                                    className="rounded-lg p-1.5 text-muted-foreground hover:bg-red-500/10 hover:text-red-500 transition-colors"
                                                                    title="Delete Document"
                                                                >
                                                                    <Trash2 size={13} />
                                                                </button>
                                                            </>
                                                        ) : (
                                                            <span className="text-[10px] text-muted-foreground italic">Read-only</span>
                                                        )}
                                                    </div>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* TAB CONTENT: ANALYZER */}
            {activeTab === "analyzer" && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Left: Input Form */}
                    <div className="lg:col-span-1 space-y-6">
                        <Surface padding="lg" className="bg-card border border-border/60 space-y-4">
                            <div className="flex items-center gap-2 border-b border-border/40 pb-3">
                                <Sparkles size={16} className="text-primary" />
                                <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground/80">
                                    Analyze Role & Skills
                                </h3>
                            </div>
                            <p className="text-[10px] text-muted-foreground leading-relaxed">
                                Paste a job title and job description to extract the standard industry skills required, as well as unique, specific requirements unique to this listing.
                            </p>

                            <form onSubmit={handleAnalyzeJob} className="space-y-4 pt-2">
                                <div className="space-y-1.5">
                                    <label className="text-[11px] font-semibold text-muted-foreground">Job Title</label>
                                    <input
                                        type="text"
                                        placeholder="e.g. Senior Backend Engineer (Go)"
                                        value={roleTitle}
                                        onChange={(e) => setRoleTitle(e.target.value)}
                                        className="w-full rounded-lg border border-border/60 bg-muted/20 px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground/50 focus:border-primary/50 focus:outline-none"
                                    />
                                </div>
                                <div className="space-y-1.5">
                                    <label className="text-[11px] font-semibold text-muted-foreground">Job Description</label>
                                    <textarea
                                        rows={10}
                                        placeholder="Paste full job description here..."
                                        value={jobDescription}
                                        onChange={(e) => setJobDescription(e.target.value)}
                                        className="w-full rounded-lg border border-border/60 bg-muted/20 px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground/50 focus:border-primary/50 focus:outline-none resize-none custom-scrollbar"
                                    />
                                </div>

                                {analysisError && (
                                    <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-3 flex gap-2 text-[10px] text-red-500">
                                        <AlertCircle size={14} className="shrink-0 mt-0.5" />
                                        <span>{analysisError}</span>
                                    </div>
                                )}

                                <button
                                    type="submit"
                                    disabled={analyzeJobMutation.isPending}
                                    className={cn(buttonStyles(), "w-full justify-center")}
                                >
                                    {analyzeJobMutation.isPending ? (
                                        <>
                                            <div className="w-3.5 h-3.5 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin mr-2" />
                                            Analyzing Job...
                                        </>
                                    ) : (
                                        <>
                                            <Sparkles size={14} className="mr-2" />
                                            Analyze Role
                                        </>
                                    )}
                                </button>
                            </form>
                        </Surface>
                    </div>

                    {/* Right: Results Comparison */}
                    <div className="lg:col-span-2">
                        {analyzeJobMutation.isPending ? (
                            <Surface padding="lg" className="bg-card border border-border/60 flex flex-col items-center justify-center min-h-[400px] text-center">
                                <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mb-3" />
                                <h4 className="text-xs font-semibold text-foreground">AI is Analyzing & Comparing Roles</h4>
                                <p className="text-[10px] text-muted-foreground max-w-xs mt-1 leading-normal">
                                    Checking database for matching roles and querying the model to extract and categorize skills...
                                </p>
                            </Surface>
                        ) : !analysisResult ? (
                            <Surface padding="lg" className="bg-card border border-border/60 flex flex-col items-center justify-center min-h-[400px] text-center text-muted-foreground/60">
                                <Briefcase className="size-10 mb-3 text-muted-foreground/30" />
                                <h4 className="text-xs font-semibold">Ready for Analysis</h4>
                                <p className="text-[10px] max-w-xs mt-1 leading-normal">
                                    Fill in the title and description on the left to begin the role and skill comparison.
                                </p>
                            </Surface>
                        ) : (
                            <div className="space-y-6">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    {/* Common Core Skills */}
                                    <Surface padding="lg" className="bg-card border border-border/60 space-y-4">
                                        <div className="flex items-center gap-2 border-b border-border/40 pb-3">
                                            <CheckCircle2 size={16} className="text-emerald-500" />
                                            <div>
                                                <h3 className="text-xs font-bold uppercase tracking-wider text-foreground">
                                                    Common Core Skills
                                                </h3>
                                                <p className="text-[9px] text-muted-foreground mt-0.5">
                                                    Standard expectations across similar roles
                                                </p>
                                            </div>
                                        </div>

                                        <div className="space-y-2 max-h-[300px] overflow-y-auto custom-scrollbar pr-1">
                                            {analysisResult.commonSkills.length === 0 ? (
                                                <p className="text-[10px] text-muted-foreground italic">No common skills extracted.</p>
                                            ) : (
                                                analysisResult.commonSkills.map((skill: string, index: number) => (
                                                    <div
                                                        key={index}
                                                        className="flex items-center gap-2 rounded-lg bg-emerald-500/5 border border-emerald-500/10 px-3 py-2 text-xs text-foreground font-medium"
                                                    >
                                                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                                                        {skill}
                                                    </div>
                                                ))
                                            )}
                                        </div>
                                    </Surface>

                                    {/* Role-Specific Unique Skills */}
                                    <Surface padding="lg" className="bg-card border border-border/60 space-y-4">
                                        <div className="flex items-center gap-2 border-b border-border/40 pb-3">
                                            <Sparkles size={16} className="text-primary" />
                                            <div>
                                                <h3 className="text-xs font-bold uppercase tracking-wider text-foreground">
                                                    Unique / Specific Skills
                                                </h3>
                                                <p className="text-[9px] text-muted-foreground mt-0.5">
                                                    Tailored custom requirements for this description
                                                </p>
                                            </div>
                                        </div>

                                        <div className="space-y-2 max-h-[300px] overflow-y-auto custom-scrollbar pr-1">
                                            {analysisResult.uniqueSkills.length === 0 ? (
                                                <p className="text-[10px] text-muted-foreground italic">No unique/specific skills extracted.</p>
                                            ) : (
                                                analysisResult.uniqueSkills.map((skill: string, index: number) => (
                                                    <div
                                                        key={index}
                                                        className="flex items-center gap-2 rounded-lg bg-primary/5 border border-primary/10 px-3 py-2 text-xs text-foreground font-medium"
                                                    >
                                                        <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                                                        {skill}
                                                    </div>
                                                ))
                                            )}
                                        </div>
                                    </Surface>
                                </div>

                                {/* Similar Roles Matched */}
                                <Surface padding="lg" className="bg-card border border-border/60 space-y-3">
                                    <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground/80 border-b border-border/40 pb-2">
                                        Similar Database Roles Compared ({analysisResult.similarRolesCompared.length})
                                    </h4>
                                    {analysisResult.similarRolesCompared.length === 0 ? (
                                        <p className="text-[10px] text-muted-foreground italic">
                                            No other interview journey profiles found in database to compare against.
                                        </p>
                                    ) : (
                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                                            {analysisResult.similarRolesCompared.map((role: any) => (
                                                <div
                                                    key={role.id}
                                                    className="flex flex-col justify-center rounded-lg border border-border/60 bg-muted/20 px-3 py-2.5"
                                                >
                                                    <span className="text-xs font-semibold text-foreground truncate">
                                                        {role.roleTitle}
                                                    </span>
                                                    {role.companyName && (
                                                        <span className="text-[10px] text-muted-foreground font-medium mt-0.5">
                                                            Company: {role.companyName}
                                                        </span>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </Surface>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* TAB CONTENT: CAREER OPTIMIZER */}
            {activeTab === "optimizer" && (
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                    {/* History Sidebar */}
                    <div className="lg:col-span-1 space-y-4">
                        <Surface padding="md" className="bg-card border border-border/60 space-y-3">
                            <div className="flex items-center justify-between border-b border-border/40 pb-2.5">
                                <div className="flex items-center gap-1.5">
                                    <History size={14} className="text-primary" />
                                    <span className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
                                        Optimization Runs
                                    </span>
                                </div>
                                <button
                                    onClick={() => setSelectedOptId(null)}
                                    className="text-[10px] font-semibold text-primary hover:underline"
                                >
                                    New +
                                </button>
                            </div>

                            {loadingHistory ? (
                                <div className="space-y-2 py-4">
                                    <div className="h-10 bg-muted/20 animate-pulse rounded-lg" />
                                    <div className="h-10 bg-muted/20 animate-pulse rounded-lg" />
                                </div>
                            ) : optHistory?.length === 0 ? (
                                <div className="py-6 text-center text-[10px] text-muted-foreground">
                                    No past runs found. Complete your first optimizer run.
                                </div>
                            ) : (
                                <div className="space-y-1.5 max-h-[350px] overflow-y-auto pr-0.5 custom-scrollbar">
                                    {optHistory?.map((opt) => (
                                        <div
                                            key={opt.id}
                                            onClick={() => setSelectedOptId(opt.id)}
                                            className={cn(
                                                "group flex items-center justify-between rounded-lg px-2.5 py-2 text-[11px] cursor-pointer border transition-all",
                                                selectedOptId === opt.id
                                                    ? "bg-primary/10 border-primary/30 text-primary font-medium"
                                                    : "bg-muted/10 border-transparent hover:bg-muted/30 text-muted-foreground hover:text-foreground"
                                            )}
                                        >
                                            <div className="min-w-0 flex-1 pr-2">
                                                <div className="font-semibold truncate">
                                                    {opt.targetRole}
                                                </div>
                                                <div className="text-[9px] text-muted-foreground mt-0.5 flex items-center gap-1">
                                                    <span>from {opt.currentRole}</span>
                                                </div>
                                            </div>
                                            <button
                                                onClick={(e) => handleDeleteOptimization(opt.id, e)}
                                                className="opacity-0 group-hover:opacity-100 hover:text-red-500 p-0.5 rounded transition-all"
                                                title="Delete Run"
                                            >
                                                <Trash2 size={12} />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </Surface>
                    </div>

                    {/* Main Area */}
                    <div className="lg:col-span-3">
                        {!selectedOptId ? (
                            /* OPTIMIZER SUBMIT FORM */
                            <Surface padding="lg" className="bg-card border border-border/60 max-w-2xl mx-auto space-y-6">
                                <div className="border-b border-border/40 pb-4 space-y-1">
                                    <div className="flex items-center gap-2">
                                        <Sparkles size={18} className="text-primary" />
                                        <h3 className="text-sm font-semibold text-foreground">
                                            AI Career Transition Agent
                                        </h3>
                                    </div>
                                    <p className="text-xs text-muted-foreground leading-relaxed">
                                        Upload your professional credentials to identify gaps and generate rewritten positioning content for your target career pivot.
                                    </p>
                                </div>

                                <form onSubmit={handleOptimizeProfile} className="space-y-6">
                                    {/* Role Selectors */}
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div className="space-y-1.5">
                                            <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                                                Current Role
                                            </label>
                                            <input
                                                type="text"
                                                required
                                                placeholder="e.g. Full Stack Developer"
                                                value={currentRole}
                                                onChange={(e) => setCurrentRole(e.target.value)}
                                                className="w-full rounded-lg border border-border/60 bg-muted/20 px-3 py-2 text-xs text-foreground focus:border-primary/50 focus:outline-none"
                                            />
                                        </div>
                                        <div className="space-y-1.5">
                                            <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                                                Target Role
                                            </label>
                                            <input
                                                type="text"
                                                required
                                                placeholder="e.g. Applied AI Engineer"
                                                value={targetRole}
                                                onChange={(e) => setTargetRole(e.target.value)}
                                                className="w-full rounded-lg border border-border/60 bg-muted/20 px-3 py-2 text-xs text-foreground focus:border-primary/50 focus:outline-none"
                                            />
                                        </div>
                                    </div>

                                    {/* Drop File Upload Zone */}
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                        <FileUploader
                                            label="Resume (PDF/DOCX)"
                                            file={resumeFile}
                                            onChange={setResumeFile}
                                        />
                                        <FileUploader
                                            label="LinkedIn (PDF)"
                                            file={linkedinFile}
                                            onChange={setLinkedinFile}
                                        />
                                        <FileUploader
                                            label="Naukri Export"
                                            file={naukriFile}
                                            onChange={setNaukriFile}
                                        />
                                    </div>

                                    <div className="border-t border-border/40 pt-4 flex justify-end">
                                        <button
                                            type="submit"
                                            disabled={optimizeMutation.isPending}
                                            className={cn(buttonStyles(), "px-6")}
                                        >
                                            {optimizeMutation.isPending ? (
                                                <>
                                                    <div className="w-3.5 h-3.5 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin mr-2" />
                                                    Evaluating Profile...
                                                </>
                                            ) : (
                                                <>
                                                    <Sparkles size={14} className="mr-2" />
                                                    Optimize Career Pivot
                                                </>
                                            )}
                                        </button>
                                    </div>
                                </form>
                            </Surface>
                        ) : activeOptimization ? (
                            /* RESULTS AND OPTIMIZATION DETAIL VIEW */
                            <div className="space-y-6">
                                {/* Header Summary */}
                                <div className="flex items-center justify-between border-b border-border/40 pb-4">
                                    <div>
                                        <h3 className="text-sm font-bold text-foreground">
                                            Transition Plan
                                        </h3>
                                        <p className="text-xs text-muted-foreground flex items-center gap-1.5 mt-0.5">
                                            <span>{activeOptimization.currentRole}</span>
                                            <ArrowRight size={12} className="text-muted-foreground/60" />
                                            <span className="font-semibold text-primary">{activeOptimization.targetRole}</span>
                                        </p>
                                    </div>
                                    <button
                                        onClick={() => setSelectedOptId(null)}
                                        className={cn(buttonStyles({ variant: "outline", size: "sm" }))}
                                    >
                                        New Analysis
                                    </button>
                                </div>

                                {/* Metrics Cards */}
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    <MetricCard
                                        title="Career Score"
                                        value={activeOptimization.analysisResult?.scores?.careerScore ?? 0}
                                        description="Overall credentials match"
                                    />
                                    <MetricCard
                                        title="Role Alignment"
                                        value={activeOptimization.analysisResult?.scores?.roleAlignmentScore ?? 0}
                                        description="Skill correlation percentage"
                                    />
                                    <MetricCard
                                        title="Market Readiness"
                                        value={activeOptimization.analysisResult?.scores?.marketReadinessScore ?? 0}
                                        description="ATS standard score"
                                    />
                                    <MetricCard
                                        title="Recruiter Visibility"
                                        value={activeOptimization.analysisResult?.scores?.recruiterVisibilityScore ?? 0}
                                        description="Search density rating"
                                    />
                                </div>

                                {/* Gap Analysis & Roadmap Grid */}
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    {/* Gap Analysis */}
                                    <Surface padding="lg" className="bg-card border border-border/60 space-y-4">
                                        <h4 className="text-xs font-bold uppercase tracking-wider text-foreground border-b border-border/40 pb-2 flex items-center gap-2">
                                            <AlertCircle size={14} className="text-amber-500" />
                                            Profile Gaps Identified
                                        </h4>
                                        <div className="space-y-4 max-h-[350px] overflow-y-auto custom-scrollbar pr-1 text-xs">
                                            <GapListSection
                                                title="Missing Skills"
                                                items={activeOptimization.analysisResult?.gapAnalysis?.missingSkills}
                                            />
                                            <GapListSection
                                                title="Missing Keywords"
                                                items={activeOptimization.analysisResult?.gapAnalysis?.missingKeywords}
                                            />
                                            <GapListSection
                                                title="Weak Positioning"
                                                items={activeOptimization.analysisResult?.gapAnalysis?.weakPositioning}
                                            />
                                            <GapListSection
                                                title="Missing Projects / Proof"
                                                items={(activeOptimization.analysisResult?.gapAnalysis?.missingProjects ?? []).concat(
                                                    activeOptimization.analysisResult?.gapAnalysis?.missingProof ?? []
                                                )}
                                            />
                                        </div>
                                    </Surface>

                                    {/* Roadmap */}
                                    <Surface padding="lg" className="bg-card border border-border/60 space-y-4">
                                        <h4 className="text-xs font-bold uppercase tracking-wider text-foreground border-b border-border/40 pb-2 flex items-center gap-2">
                                            <TrendingUp size={14} className="text-primary" />
                                            Transition Roadmap
                                        </h4>
                                        <div className="space-y-4 text-xs">
                                            <RoadmapSection
                                                priority="HIGH"
                                                items={activeOptimization.analysisResult?.roadmap?.high}
                                                colorClass="bg-red-500/10 text-red-500 border-red-500/20"
                                            />
                                            <RoadmapSection
                                                priority="MEDIUM"
                                                items={activeOptimization.analysisResult?.roadmap?.medium}
                                                colorClass="bg-primary/10 text-primary border-primary/20"
                                            />
                                            <RoadmapSection
                                                priority="LOW"
                                                items={activeOptimization.analysisResult?.roadmap?.low}
                                                colorClass="bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
                                            />
                                        </div>
                                    </Surface>
                                </div>

                                {/* Generated Section Output Modules */}
                                <Surface padding="lg" className="bg-card border border-border/60 space-y-4">
                                    <h4 className="text-xs font-bold uppercase tracking-wider text-foreground border-b border-border/40 pb-2">
                                        AI Recommended Rewrites & Content
                                    </h4>

                                    {/* Subtabs for Outputs */}
                                    <div className="flex border-b border-border/20 overflow-x-auto scrollbar-none gap-2">
                                        <button
                                            onClick={() => setOptSubTab("linkedin-headline")}
                                            className={cn(
                                                "px-3 py-1.5 text-[11px] font-semibold transition-all border-b-2 whitespace-nowrap",
                                                optSubTab === "linkedin-headline" ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"
                                            )}
                                        >
                                            LinkedIn Headline
                                        </button>
                                        <button
                                            onClick={() => setOptSubTab("linkedin-about")}
                                            className={cn(
                                                "px-3 py-1.5 text-[11px] font-semibold transition-all border-b-2 whitespace-nowrap",
                                                optSubTab === "linkedin-about" ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"
                                            )}
                                        >
                                            LinkedIn About
                                        </button>
                                        <button
                                            onClick={() => setOptSubTab("resume-summary")}
                                            className={cn(
                                                "px-3 py-1.5 text-[11px] font-semibold transition-all border-b-2 whitespace-nowrap",
                                                optSubTab === "resume-summary" ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"
                                            )}
                                        >
                                            Resume Summary
                                        </button>
                                        <button
                                            onClick={() => setOptSubTab("naukri")}
                                            className={cn(
                                                "px-3 py-1.5 text-[11px] font-semibold transition-all border-b-2 whitespace-nowrap",
                                                optSubTab === "naukri" ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"
                                            )}
                                        >
                                            Naukri Profile
                                        </button>
                                        <button
                                            onClick={() => setOptSubTab("skills")}
                                            className={cn(
                                                "px-3 py-1.5 text-[11px] font-semibold transition-all border-b-2 whitespace-nowrap",
                                                optSubTab === "skills" ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"
                                            )}
                                        >
                                            Skills suggestions
                                        </button>
                                    </div>

                                    {/* Outputs Content View */}
                                    <div className="pt-2 text-xs">
                                        {/* LinkedIn Headlines */}
                                        {optSubTab === "linkedin-headline" && (
                                            <div className="space-y-3">
                                                <p className="text-[10px] text-muted-foreground mb-1 leading-normal">
                                                    Choose from these 5 search-visibility optimized headlines matching your pivot:
                                                </p>
                                                {activeOptimization.analysisResult?.generatedContent?.linkedinHeadlines?.map((hl: string, idx: number) => {
                                                    const copyId = `headline-${idx}`;
                                                    return (
                                                        <div key={idx} className="flex items-start justify-between bg-muted/10 border border-border/40 rounded-xl px-4 py-3 gap-4">
                                                            <div className="font-medium text-foreground pr-2 leading-relaxed">
                                                                {hl}
                                                            </div>
                                                            <button
                                                                onClick={() => copyToClipboard(hl, copyId)}
                                                                className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors shrink-0"
                                                                title="Copy Headline"
                                                            >
                                                                {copiedId === copyId ? <Check size={14} className="text-emerald-500" /> : <Copy size={14} />}
                                                            </button>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        )}

                                        {/* LinkedIn About summaries */}
                                        {optSubTab === "linkedin-about" && (
                                            <div className="space-y-4">
                                                {/* Mini sub-tabs for versions */}
                                                <div className="flex gap-2">
                                                    {(["professional", "story", "recruiter"] as const).map((ver) => (
                                                        <button
                                                            key={ver}
                                                            onClick={() => setAboutTab(ver)}
                                                            className={cn(
                                                                "rounded-full px-3 py-1 text-[10px] font-semibold border transition-all uppercase tracking-wider",
                                                                aboutTab === ver
                                                                    ? "bg-primary/10 border-primary/20 text-primary"
                                                                    : "bg-muted/10 border-border/40 text-muted-foreground hover:text-foreground"
                                                            )}
                                                        >
                                                            {ver === "professional" ? "Professional Style" : ver === "story" ? "Personal Story" : "Recruiter Optimized"}
                                                        </button>
                                                    ))}
                                                </div>

                                                {/* Render selected version */}
                                                {(() => {
                                                    const text = activeOptimization.analysisResult?.generatedContent?.linkedinAbout?.[aboutTab] || "";
                                                    const copyId = `about-${aboutTab}`;
                                                    return (
                                                        <div className="relative bg-muted/10 border border-border/40 rounded-xl p-4 min-h-[120px]">
                                                            <button
                                                                onClick={() => copyToClipboard(text, copyId)}
                                                                className="absolute right-3 top-3 rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                                                                title="Copy Text"
                                                            >
                                                                {copiedId === copyId ? <Check size={14} className="text-emerald-500" /> : <Copy size={14} />}
                                                            </button>
                                                            <pre className="text-xs font-sans text-foreground whitespace-pre-wrap leading-relaxed pr-8">
                                                                {text || "No generated content available."}
                                                            </pre>
                                                        </div>
                                                    );
                                                })()}
                                            </div>
                                        )}

                                        {/* Resume Summary */}
                                        {optSubTab === "resume-summary" && (
                                            <div className="space-y-2">
                                                <p className="text-[10px] text-muted-foreground leading-normal mb-1">
                                                    An ATS-friendly resume summary optimized to emphasize key transition domains and match parsing keywords:
                                                </p>
                                                {(() => {
                                                    const text = activeOptimization.analysisResult?.generatedContent?.resumeSummary || "";
                                                    const copyId = "resume-summary";
                                                    return (
                                                        <div className="relative bg-muted/10 border border-border/40 rounded-xl p-4 min-h-[80px]">
                                                            <button
                                                                onClick={() => copyToClipboard(text, copyId)}
                                                                className="absolute right-3 top-3 rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                                                                title="Copy Summary"
                                                            >
                                                                {copiedId === copyId ? <Check size={14} className="text-emerald-500" /> : <Copy size={14} />}
                                                            </button>
                                                            <pre className="text-xs font-sans text-foreground whitespace-pre-wrap leading-relaxed pr-8">
                                                                {text || "No summary generated."}
                                                            </pre>
                                                        </div>
                                                    );
                                                })()}
                                            </div>
                                        )}

                                        {/* Naukri Summary */}
                                        {optSubTab === "naukri" && (
                                            <div className="space-y-4">
                                                {/* Headline */}
                                                <div className="space-y-1.5">
                                                    <div className="flex items-center justify-between">
                                                        <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                                                            Naukri Headline
                                                        </span>
                                                        <button
                                                            onClick={() => copyToClipboard(activeOptimization.analysisResult?.generatedContent?.naukriHeadline || "", "naukri-hl")}
                                                            className="text-muted-foreground hover:text-foreground p-0.5 rounded transition-all"
                                                        >
                                                            {copiedId === "naukri-hl" ? (
                                                                <span className="text-[9px] text-emerald-500 font-semibold">Copied</span>
                                                            ) : (
                                                                <Copy size={12} />
                                                            )}
                                                        </button>
                                                    </div>
                                                    <div className="bg-muted/10 border border-border/40 rounded-lg p-3 font-medium text-foreground">
                                                        {activeOptimization.analysisResult?.generatedContent?.naukriHeadline || "No headline generated."}
                                                    </div>
                                                </div>

                                                {/* Summary */}
                                                <div className="space-y-1.5">
                                                    <div className="flex items-center justify-between">
                                                        <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                                                            Naukri Profile Summary
                                                        </span>
                                                        <button
                                                            onClick={() => copyToClipboard(activeOptimization.analysisResult?.generatedContent?.naukriSummary || "", "naukri-sum")}
                                                            className="text-muted-foreground hover:text-foreground p-0.5 rounded transition-all"
                                                        >
                                                            {copiedId === "naukri-sum" ? (
                                                                <span className="text-[9px] text-emerald-500 font-semibold">Copied</span>
                                                            ) : (
                                                                <Copy size={12} />
                                                            )}
                                                        </button>
                                                    </div>
                                                    <div className="bg-muted/10 border border-border/40 rounded-lg p-3 font-sans text-foreground leading-relaxed">
                                                        {activeOptimization.analysisResult?.generatedContent?.naukriSummary || "No summary generated."}
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        {/* Skills suggestions */}
                                        {optSubTab === "skills" && (
                                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                                {/* Already Present */}
                                                <div className="space-y-2">
                                                    <div className="text-[10px] font-bold text-emerald-500 uppercase tracking-wider flex items-center gap-1.5">
                                                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                                                        Already Present ({activeOptimization.analysisResult?.generatedContent?.skillsSuggestions?.alreadyPresent?.length ?? 0})
                                                    </div>
                                                    <div className="flex flex-wrap gap-1.5">
                                                        {activeOptimization.analysisResult?.generatedContent?.skillsSuggestions?.alreadyPresent?.map((skill: string) => (
                                                            <span key={skill} className="rounded-full bg-emerald-500/5 border border-emerald-500/20 px-2 py-0.5 text-[10px] text-foreground font-semibold">
                                                                {skill}
                                                            </span>
                                                        )) || <span className="text-[10px] text-muted-foreground italic">None matching</span>}
                                                    </div>
                                                </div>

                                                {/* Missing Skills */}
                                                <div className="space-y-2">
                                                    <div className="text-[10px] font-bold text-red-500 uppercase tracking-wider flex items-center gap-1.5">
                                                        <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                                                        Missing (Required) ({activeOptimization.analysisResult?.generatedContent?.skillsSuggestions?.missingSkills?.length ?? 0})
                                                    </div>
                                                    <div className="flex flex-wrap gap-1.5">
                                                        {activeOptimization.analysisResult?.generatedContent?.skillsSuggestions?.missingSkills?.map((skill: string) => (
                                                            <span key={skill} className="rounded-full bg-red-500/5 border border-red-500/20 px-2 py-0.5 text-[10px] text-foreground font-semibold">
                                                                {skill}
                                                            </span>
                                                        )) || <span className="text-[10px] text-muted-foreground italic">None matching</span>}
                                                    </div>
                                                </div>

                                                {/* Recommended Skills */}
                                                <div className="space-y-2">
                                                    <div className="text-[10px] font-bold text-primary uppercase tracking-wider flex items-center gap-1.5">
                                                        <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                                                        Recommended (Preferred) ({activeOptimization.analysisResult?.generatedContent?.skillsSuggestions?.recommendedSkills?.length ?? 0})
                                                    </div>
                                                    <div className="flex flex-wrap gap-1.5">
                                                        {activeOptimization.analysisResult?.generatedContent?.skillsSuggestions?.recommendedSkills?.map((skill: string) => (
                                                            <span key={skill} className="rounded-full bg-primary/5 border border-primary/20 px-2 py-0.5 text-[10px] text-foreground font-semibold">
                                                                {skill}
                                                            </span>
                                                        )) || <span className="text-[10px] text-muted-foreground italic">None matching</span>}
                                                    </div>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </Surface>
                            </div>
                        ) : (
                            <div className="py-20 text-center text-xs text-muted-foreground">
                                Select an optimization report from the sidebar or click "New" to start.
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

// Characteristic Pill Helper
function CharacteristicPill({ label, value }: { label: string; value: number }) {
    return (
        <div className="flex items-center justify-between py-1 border-b border-border/10">
            <span className="text-muted-foreground">{label}</span>
            <div className="flex items-center gap-2">
                <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                    <div className="h-full bg-primary" style={{ width: `${value * 100}%` }} />
                </div>
                <span className="font-semibold text-foreground w-6 text-right">{(value).toFixed(1)}</span>
            </div>
        </div>
    );
}

// Metric Card Helper
function MetricCard({ title, value, description }: { title: string; value: number; description: string }) {
    return (
        <Surface padding="md" className="bg-card border border-border/60 flex flex-col justify-between">
            <div>
                <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                    {title}
                </span>
                <div className="text-2xl font-bold text-foreground mt-1">
                    {value}%
                </div>
            </div>
            <span className="text-[9px] text-muted-foreground mt-3 block leading-tight">
                {description}
            </span>
        </Surface>
    );
}

// File Uploader component Helper
function FileUploader({
    label,
    file,
    onChange
}: {
    label: string;
    file: File | null;
    onChange: (f: File | null) => void;
}) {
    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            onChange(e.target.files[0]);
        }
    };

    return (
        <div className="relative border border-dashed border-border/80 rounded-xl p-4 bg-muted/5 hover:bg-muted/10 transition-colors flex flex-col items-center justify-center text-center">
            {file ? (
                <div className="space-y-2 w-full">
                    <FileCheck className="size-8 text-primary mx-auto" />
                    <div className="text-xs font-semibold text-foreground truncate px-2" title={file.name}>
                        {file.name}
                    </div>
                    <button
                        type="button"
                        onClick={() => onChange(null)}
                        className="text-[10px] text-red-500 font-semibold hover:underline"
                    >
                        Remove file
                    </button>
                </div>
            ) : (
                <label className="cursor-pointer space-y-1.5 py-2 w-full block">
                    <Upload className="size-8 text-muted-foreground/60 mx-auto" />
                    <div className="text-xs font-semibold text-foreground">
                        {label}
                    </div>
                    <div className="text-[9px] text-muted-foreground">
                        Click or drag PDF to upload
                    </div>
                    <input
                        type="file"
                        accept=".pdf,.docx,.txt"
                        onChange={handleFileChange}
                        className="hidden"
                    />
                </label>
            )}
        </div>
    );
}

// Gap Analysis list helper
function GapListSection({ title, items }: { title: string; items?: string[] }) {
    if (!items || items.length === 0) return null;
    return (
        <div className="space-y-1.5">
            <div className="font-bold text-foreground text-[10px] uppercase tracking-wider">
                {title}
            </div>
            <ul className="space-y-1 pl-3.5 list-disc text-muted-foreground">
                {items.map((item, idx) => (
                    <li key={idx} className="leading-relaxed">
                        {item}
                    </li>
                ))}
            </ul>
        </div>
    );
}

// Roadmap section helper
function RoadmapSection({ priority, items, colorClass }: { priority: string; items?: string[]; colorClass: string }) {
    if (!items || items.length === 0) return null;
    return (
        <div className="space-y-2">
            <div className={cn("inline-flex rounded px-1.5 py-0.5 text-[9px] font-bold border uppercase tracking-wider", colorClass)}>
                {priority} Priority
            </div>
            <ul className="space-y-1.5 pl-3 list-decimal text-muted-foreground text-xs">
                {items.map((item, idx) => (
                    <li key={idx} className="leading-relaxed">
                        {item}
                    </li>
                ))}
            </ul>
        </div>
    );
}
