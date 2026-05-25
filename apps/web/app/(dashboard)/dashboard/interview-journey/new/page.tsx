"use client";

import { useState, useCallback } from "react";
import { PageHeader } from "@/core/components/ui/PageHeader";
import { Surface } from "@/core/components/ui/Surface";
import { buttonStyles } from "@/core/components/ui/button";
import { cn } from "@/lib/utils";
import { useCreateJourney, useUploadResume } from "@/hooks/mutations/useCreateJourney";
import { Upload, FileText, ArrowLeft, ArrowRight, Building2 } from "lucide-react";
import Link from "next/link";

type Step = "resume" | "details" | "review";

export default function NewJourneyPage() {
    const [step, setStep] = useState<Step>("resume");
    const [resumeText, setResumeText] = useState("");
    const [resumeFileName, setResumeFileName] = useState("");
    const [roleTitle, setRoleTitle] = useState("");
    const [companyName, setCompanyName] = useState("");
    const [jobDescription, setJobDescription] = useState("");

    const createJourney = useCreateJourney();
    const uploadResume = useUploadResume();

    const handleFileUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setResumeFileName(file.name);

        if (file.name.endsWith(".txt")) {
            const text = await file.text();
            setResumeText(text);
            return;
        }

        try {
            const result = await uploadResume.mutateAsync(file);
            if (result.data) {
                setResumeText(result.data.resumeText);
            }
        } catch {
            const text = await file.text();
            setResumeText(text);
        }
    }, [uploadResume]);

    const handlePasteResume = useCallback(() => {
        const text = prompt("Paste your resume text:");
        if (text) {
            setResumeText(text);
            setResumeFileName("pasted-resume.txt");
        }
    }, []);

    const handleCreate = useCallback(async () => {
        if (!resumeText || !roleTitle || !jobDescription) return;

        await createJourney.mutateAsync({
            roleTitle,
            jobDescription,
            resumeText,
            companyName: companyName || undefined,
        });
    }, [resumeText, roleTitle, jobDescription, companyName, createJourney]);

    return (
        <div className="flex flex-col gap-8 pb-12 max-w-2xl mx-auto">
            <PageHeader
                eyebrow="New Interview Journey"
                title="Create a hiring simulation"
                description="Upload a resume and paste a job description to generate a realistic interview pipeline."
                actions={
                    <Link href="/dashboard/interview-journey" className={buttonStyles({ variant: "ghost", size: "sm" })}>
                        <ArrowLeft size={14} />
                        Back
                    </Link>
                }
            />

            {/* Steps indicator */}
            <div className="flex items-center gap-2 text-sm">
                {(["resume", "details", "review"] as const).map((s, i) => (
                    <div key={s} className="flex items-center gap-2">
                        <div className={cn(
                            "size-7 rounded-full flex items-center justify-center text-xs font-semibold",
                            step === s
                                ? "bg-primary text-primary-foreground"
                                : "bg-muted text-muted-foreground"
                        )}>
                            {i + 1}
                        </div>
                        <span className={cn(
                            "capitalize",
                            step === s ? "text-foreground font-medium" : "text-muted-foreground"
                        )}>
                            {s === "resume" ? "Upload Resume" : s === "details" ? "Job Details" : "Review"}
                        </span>
                        {i < 2 && <ArrowRight size={12} className="text-muted-foreground/40" />}
                    </div>
                ))}
            </div>

            {step === "resume" && (
                <Surface variant="default" padding="lg" className="space-y-6">
                    <div>
                        <h3 className="font-semibold text-foreground mb-1">Upload Resume</h3>
                        <p className="text-sm text-muted-foreground">PDF, DOCX, or plain text</p>
                    </div>

                    <label className={cn(
                        "flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed border-border p-8 cursor-pointer",
                        "hover:border-primary/50 hover:bg-muted/30 transition-all",
                        resumeText && "border-emerald-500/50 bg-emerald-500/5"
                    )}>
                        <div className={cn(
                            "size-12 rounded-full flex items-center justify-center",
                            resumeText ? "bg-emerald-500/10 text-emerald-500" : "bg-muted text-muted-foreground"
                        )}>
                            {resumeText ? <FileText size={22} /> : <Upload size={22} />}
                        </div>
                        {resumeText ? (
                            <div className="text-center">
                                <p className="text-sm font-medium text-foreground">Resume loaded</p>
                                <p className="text-xs text-muted-foreground mt-0.5">{resumeFileName || "pasted text"}</p>
                            </div>
                        ) : (
                            <div className="text-center">
                                <p className="text-sm font-medium text-foreground">Click to upload</p>
                                <p className="text-xs text-muted-foreground mt-0.5">or drag and drop</p>
                            </div>
                        )}
                        <input
                            type="file"
                            accept=".pdf,.docx,.txt"
                            onChange={handleFileUpload}
                            className="hidden"
                        />
                    </label>

                    <div className="text-center">
                        <button
                            type="button"
                            onClick={handlePasteResume}
                            className="text-sm text-primary hover:text-primary-dark transition-colors"
                        >
                            Or paste resume text instead
                        </button>
                    </div>

                    {resumeText && (
                        <div className="max-h-40 overflow-y-auto rounded-lg bg-muted/50 p-3 text-xs text-muted-foreground">
                            {resumeText.slice(0, 1000)}{resumeText.length > 1000 ? "..." : ""}
                        </div>
                    )}

                    <div className="flex justify-end">
                        <button
                            type="button"
                            onClick={() => setStep("details")}
                            disabled={!resumeText}
                            className={buttonStyles()}
                        >
                            Next
                            <ArrowRight size={14} />
                        </button>
                    </div>
                </Surface>
            )}

            {step === "details" && (
                <Surface variant="default" padding="lg" className="space-y-6">
                    <div>
                        <h3 className="font-semibold text-foreground mb-1">Job Details</h3>
                        <p className="text-sm text-muted-foreground">Paste the job description you're preparing for</p>
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-medium text-foreground">Role Title</label>
                        <input
                            type="text"
                            value={roleTitle}
                            onChange={(e) => setRoleTitle(e.target.value)}
                            placeholder="e.g. Senior Frontend Engineer"
                            className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/30"
                        />
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-medium text-foreground flex items-center gap-1.5">
                            <Building2 size={14} className="text-muted-foreground" />
                            Company Name (optional)
                        </label>
                        <input
                            type="text"
                            value={companyName}
                            onChange={(e) => setCompanyName(e.target.value)}
                            placeholder="e.g. Acme Corp"
                            className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/30"
                        />
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-medium text-foreground">Job Description</label>
                        <textarea
                            value={jobDescription}
                            onChange={(e) => setJobDescription(e.target.value)}
                            placeholder="Paste the full job description here..."
                            rows={10}
                            className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/30 resize-vertical"
                        />
                    </div>

                    <div className="flex justify-between">
                        <button
                            type="button"
                            onClick={() => setStep("resume")}
                            className={buttonStyles({ variant: "ghost" })}
                        >
                            <ArrowLeft size={14} />
                            Back
                        </button>
                        <button
                            type="button"
                            onClick={() => setStep("review")}
                            disabled={!roleTitle || !jobDescription}
                            className={buttonStyles()}
                        >
                            Next
                            <ArrowRight size={14} />
                        </button>
                    </div>
                </Surface>
            )}

            {step === "review" && (
                <Surface variant="default" padding="lg" className="space-y-6">
                    <div>
                        <h3 className="font-semibold text-foreground mb-1">Review & Create</h3>
                        <p className="text-sm text-muted-foreground">Verify your details before creating the journey</p>
                    </div>

                    <div className="space-y-3 rounded-lg bg-muted/30 p-4">
                        <div className="flex justify-between text-sm">
                            <span className="text-muted-foreground">Role</span>
                            <span className="font-medium text-foreground">{roleTitle}</span>
                        </div>
                        {companyName && (
                            <div className="flex justify-between text-sm">
                                <span className="text-muted-foreground">Company</span>
                                <span className="font-medium text-foreground">{companyName}</span>
                            </div>
                        )}
                        <div className="flex justify-between text-sm">
                            <span className="text-muted-foreground">Resume</span>
                            <span className="font-medium text-foreground">
                                {resumeText.length} characters
                            </span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span className="text-muted-foreground">Job Description</span>
                            <span className="font-medium text-foreground">
                                {jobDescription.length} characters
                            </span>
                        </div>
                    </div>

                    <div className="flex justify-between">
                        <button
                            type="button"
                            onClick={() => setStep("details")}
                            className={buttonStyles({ variant: "ghost" })}
                        >
                            <ArrowLeft size={14} />
                            Back
                        </button>
                        <button
                            type="button"
                            onClick={handleCreate}
                            disabled={createJourney.isPending}
                            className={buttonStyles()}
                        >
                            {createJourney.isPending ? "Creating..." : "Create Journey"}
                        </button>
                    </div>
                </Surface>
            )}
        </div>
    );
}
