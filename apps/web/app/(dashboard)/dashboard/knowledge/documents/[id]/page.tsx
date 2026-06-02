"use client";

import React, { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { PageHeader } from "@/core/components/ui/PageHeader";
import { Surface } from "@/core/components/ui/Surface";
import { buttonStyles } from "@/core/components/ui/button";
import { useDocument, useDocumentMutations } from "@/hooks/queries/useKnowledge";
import { ArrowLeft, Save, AlertCircle, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

export default function EditDocumentPage() {
    const router = useRouter();
    const params = useParams();
    const docId = params.id as string;
    const isNew = docId === "new";

    const { data: document, isLoading } = useDocument(isNew ? "" : docId);
    const { createMutation, updateMutation } = useDocumentMutations();

    // Form states
    const [title, setTitle] = useState("");
    const [source, setSource] = useState("");
    const [sourceType, setSourceType] = useState("markdown");
    const [domain, setDomain] = useState("interview_experience");
    const [topic, setTopic] = useState("");
    const [difficulty, setDifficulty] = useState("MEDIUM");
    const [content, setContent] = useState("");
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (document && !isNew) {
            setTitle(document.title);
            setSource(document.source);
            setSourceType(document.sourceType);
            setDomain(document.domain);
            setTopic(document.topic);
            setDifficulty(document.difficulty);
            setContent(document.content);
        }
    }, [document, isNew]);

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!title.trim()) {
            setError("Document title is required.");
            return;
        }
        if (!topic.trim()) {
            setError("Topic is required (e.g. react, aws, system_design).");
            return;
        }
        if (!content.trim()) {
            setError("Document content cannot be empty.");
            return;
        }

        const payload = {
            title: title.trim(),
            source: source.trim() || "dashboard_upload",
            sourceType,
            domain,
            topic: topic.trim().toLowerCase(),
            difficulty,
            content: content.trim(),
            metaData: {},
        };

        try {
            if (isNew) {
                await createMutation.mutateAsync(payload);
            } else {
                await updateMutation.mutateAsync({ id: docId, data: payload });
            }
            router.push("/dashboard/knowledge");
        } catch (err: any) {
            setError(err || "Failed to save document to knowledge base.");
        }
    };

    if (isLoading && !isNew) {
        return (
            <div className="py-12 flex flex-col items-center justify-center">
                <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mb-2" />
                <p className="text-xs text-muted-foreground">Loading knowledge document...</p>
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
                title={isNew ? "Ingest Knowledge Document" : "Edit Knowledge Document"}
                description="Import guides, code reviews, rubrics, or real transcripts. Documents are automatically chunked and embedded into pgvector in real-time."
            />

            {error && (
                <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4 flex gap-3 text-xs text-red-500">
                    <AlertCircle size={16} className="shrink-0 mt-0.5" />
                    <span>{error}</span>
                </div>
            )}

            <form onSubmit={handleSave} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Editor Content */}
                <div className="lg:col-span-2 space-y-4">
                    <Surface padding="lg" className="bg-card border border-border flex flex-col h-[520px]">
                        <div className="flex items-center justify-between border-b border-border/40 pb-2 mb-4 shrink-0">
                            <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground/80">
                                Document Content (Markdown or Text)
                            </label>
                            <span className="text-[10px] text-muted-foreground bg-muted/60 px-2 py-0.5 rounded">
                                Characters: {content.length}
                            </span>
                        </div>
                        
                        <textarea
                            value={content}
                            onChange={(e) => setContent(e.target.value)}
                            placeholder="# Enter document headers, logs, or templates here..."
                            className="flex-1 w-full bg-muted/20 border border-border/50 rounded-lg p-4 text-xs font-mono text-foreground placeholder:text-muted-foreground/40 focus:border-primary/50 focus:outline-none resize-none overflow-y-auto"
                        />
                    </Surface>
                </div>

                {/* Metadata & Actions */}
                <div className="space-y-6">
                    <Surface padding="lg" className="bg-card border border-border flex flex-col justify-between h-full min-h-[520px]">
                        <div className="space-y-4">
                            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground/80 mb-2 border-b border-border/40 pb-2">
                                Settings & Meta
                            </h3>

                            <div className="space-y-1.5">
                                <label className="text-[11px] font-semibold text-muted-foreground">Document Title</label>
                                <input
                                    type="text"
                                    value={title}
                                    onChange={(e) => setTitle(e.target.value)}
                                    placeholder="e.g. Google System Design Guide"
                                    className="w-full rounded-lg border border-border/60 bg-muted/20 px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground/50 focus:border-primary/50 focus:outline-none"
                                />
                            </div>

                            <div className="space-y-1.5">
                                <label className="text-[11px] font-semibold text-muted-foreground">Knowledge Domain</label>
                                <select
                                    value={domain}
                                    onChange={(e) => setDomain(e.target.value)}
                                    className="w-full rounded-lg border border-border/60 bg-muted/20 px-3 py-2 text-xs text-foreground focus:border-primary/50 focus:outline-none"
                                >
                                    <option value="interview_experience">Interview Experience / Transcript</option>
                                    <option value="company_rubric">Company Rubrics & Principles</option>
                                    <option value="system_design">System Design Architectures</option>
                                    <option value="behavioral">Behavioral STAR Primers</option>
                                    <option value="frontend">Frontend / Performance Guides</option>
                                    <option value="backend">Backend / Databases Guides</option>
                                </select>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-1.5">
                                    <label className="text-[11px] font-semibold text-muted-foreground">Topic Tag</label>
                                    <input
                                        type="text"
                                        value={topic}
                                        onChange={(e) => setTopic(e.target.value)}
                                        placeholder="e.g. react, aws"
                                        className="w-full rounded-lg border border-border/60 bg-muted/20 px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground/50 focus:border-primary/50 focus:outline-none"
                                    />
                                </div>
                                <div className="space-y-1.5">
                                    <label className="text-[11px] font-semibold text-muted-foreground">Difficulty</label>
                                    <select
                                        value={difficulty}
                                        onChange={(e) => setDifficulty(e.target.value)}
                                        className="w-full rounded-lg border border-border/60 bg-muted/20 px-3 py-2 text-xs text-foreground focus:border-primary/50 focus:outline-none"
                                    >
                                        <option value="EASY">EASY (Foundational)</option>
                                        <option value="MEDIUM">MEDIUM (Applied)</option>
                                        <option value="HARD">HARD (System level)</option>
                                    </select>
                                </div>
                            </div>

                            <div className="space-y-1.5">
                                <label className="text-[11px] font-semibold text-muted-foreground">Source Reference (URL or Path)</label>
                                <input
                                    type="text"
                                    value={source}
                                    onChange={(e) => setSource(e.target.value)}
                                    placeholder="e.g. github.com/user/project"
                                    className="w-full rounded-lg border border-border/60 bg-muted/20 px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground/50 focus:border-primary/50 focus:outline-none"
                                />
                            </div>

                            <div className="space-y-1.5">
                                <label className="text-[11px] font-semibold text-muted-foreground">Source Type</label>
                                <select
                                    value={sourceType}
                                    onChange={(e) => setSourceType(e.target.value)}
                                    className="w-full rounded-lg border border-border/60 bg-muted/20 px-3 py-2 text-xs text-foreground focus:border-primary/50 focus:outline-none"
                                >
                                    <option value="markdown">Markdown (.md)</option>
                                    <option value="pdf">PDF File</option>
                                    <option value="json">JSON Metadata</option>
                                    <option value="txt">Plain Text (.txt)</option>
                                </select>
                            </div>
                        </div>

                        <div className="border-t border-border/40 pt-4 mt-6 flex flex-col gap-2">
                            <button
                                type="submit"
                                disabled={createMutation.isPending || updateMutation.isPending}
                                className={cn(buttonStyles(), "w-full justify-center")}
                            >
                                <Sparkles size={16} className="mr-2 animate-pulse" />
                                {createMutation.isPending || updateMutation.isPending ? "Indexing Chunks..." : "Ingest & Index"}
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
