"use client";

import React, { useState, useEffect, useRef } from "react";
import { useUiStore } from "@/lib/store/ui.store";
import {
    X,
    Play,
    Pause,
    RotateCcw,
    Check,
    Copy,
    ChevronDown,
    ChevronUp,
    Search,
    Mail,
    Briefcase,
    FileText,
    Send,
    Terminal,
    ArrowRight,
    Lock,
    Shield,
    Activity,
    FileDown,
    Sparkles,
    CheckCircle2,
    Users,
    AlertCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ── TYPES & INTERFACES ──────────────────────────────────────────────────────

type ModalType =
    | "demo"
    | "api"
    | "about"
    | "contact"
    | "privacy"
    | "blog"
    | "help"
    | "whitepapers"
    | "guides";

interface DialogueLine {
    speaker: "interviewer" | "user" | "coach";
    text: string;
    metrics?: {
        clarity: number;
        depth: number;
        pace: number;
    };
}

// Mock database values
const DEMO_DIALOGUE: DialogueLine[] = [
    {
        speaker: "interviewer",
        text: "Welcome to your technical session. To begin, could you explain the differences between SQL and NoSQL databases, and when you would choose one over the other?",
    },
    {
        speaker: "user",
        text: "Sure. SQL databases are relational and table-based, while NoSQL databases are non-relational and can be document-based, key-value, or graph. I would choose SQL when ACID compliance is critical, and NoSQL for high throughput or flexible schemas.",
        metrics: { clarity: 82, depth: 75, pace: 130 },
    },
    {
        speaker: "coach",
        text: "Strong explanation! Mentioning ACID compliance is a great talking point. To improve, you could briefly mention horizontal scaling limits on traditional SQL setups.",
    },
    {
        speaker: "interviewer",
        text: "Excellent. Let's dig deeper. How does a database index work under the hood, and what are the performance trade-offs of using too many indexes?",
    },
    {
        speaker: "user",
        text: "Indexes speed up read queries by creating lookup structures like B-Trees. However, they slow down write operations (INSERT, UPDATE, DELETE) because the index needs to be rebuilt, and they consume additional disk space.",
        metrics: { clarity: 91, depth: 88, pace: 122 },
    },
    {
        speaker: "coach",
        text: "Perfect. Spot on with B-Trees and write overhead trade-offs. Your pacing was also excellent here, staying around 120 words per minute.",
    },
    {
        speaker: "interviewer",
        text: "Great. Let's do a behavioral question. Tell me about a time you had a conflict with a colleague and how you resolved it.",
    },
    {
        speaker: "user",
        text: "In my last project, a teammate wanted to use a NoSQL database while I favored SQL. I set up a brief sync where we listed our trade-offs and did a small prototype. We realized NoSQL met our speed requirements better, so we aligned on it.",
        metrics: { clarity: 88, depth: 82, pace: 140 },
    },
    {
        speaker: "coach",
        text: "Excellent use of the STAR method. You clearly showed how you proactively collaborated to reach alignment. Next time, try to elaborate slightly on the long-term impact of that alignment.",
    },
];

const API_LANGUAGES = ["cURL", "JavaScript", "Python"];
const API_CODE = {
    cURL: `curl -X POST https://api.braintrain.ai/v1/sessions \\
  -H "Authorization: Bearer $BT_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "topicId": "sys-design-01",
    "difficulty": "medium",
    "interviewMode": "panel"
  }'`,
    JavaScript: `const startSession = async () => {
  const res = await fetch("https://api.braintrain.ai/v1/sessions", {
    method: "POST",
    headers: {
      "Authorization": "Bearer " + process.env.BT_API_KEY,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      topicId: "sys-design-01",
      difficulty: "medium",
      interviewMode: "panel"
    })
  });
  return res.json();
};`,
    Python: `import os
import requests

api_key = os.getenv("BT_API_KEY")
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
payload = {
    "topicId": "sys-design-01",
    "difficulty": "medium",
    "interviewMode": "panel"
}

response = requests.post(
    "https://api.braintrain.ai/v1/sessions",
    headers=headers,
    json=payload
)
session_data = response.json()`,
};

const BLOG_POSTS = [
    {
        title: "Mastering the STAR Method for Executive Roles",
        excerpt: "Learn how to frame complex engineering decisions to impress director-level panels.",
        readTime: "5 min read",
        tag: "Behavioral",
    },
    {
        title: "5 Coding Patterns You Must Know in 2026",
        excerpt: "A deep dive into sliding window, fast/slow pointers, and dynamic programming.",
        readTime: "7 min read",
        tag: "Technical",
    },
    {
        title: "The Psychology of Interview Stress & How to Beat It",
        excerpt: "How cognitive reframing and mock practice under pressure can reset your nervous system.",
        readTime: "4 min read",
        tag: "Mindset",
    },
];

const HELP_FAQS = [
    {
        q: "How does the AI evaluate my response?",
        a: "Our AI model analyzes a combination of semantic depth (technical accuracy), speech clarity (structure and fillers), and confidence delivery metrics (pace, pause patterns). It provides granular feedback based on real hiring manager criteria.",
    },
    {
        q: "Is my session recording data private?",
        a: "Absolutely. We encrypt all voice and text data in transit and at rest. We never sell your data or use your session logs for training general models without explicit enterprise consent.",
    },
    {
        q: "Can I cancel or change plans anytime?",
        a: "Yes. You can manage your subscription directly from your settings. Upgrades take effect immediately, while downgrades apply at the end of the current billing cycle.",
    },
];

// ── COMPONENT ───────────────────────────────────────────────────────────────

export function LandingModal() {
    const { activeModal, closeModal } = useUiStore();
    const [activeTab, setActiveTab] = useState<string>("cURL");
    const [copied, setCopied] = useState<boolean>(false);
    const [faqOpen, setFaqOpen] = useState<number | null>(null);

    // Demo state
    const [demoPlaying, setDemoPlaying] = useState<boolean>(false);
    const [demoStep, setDemoStep] = useState<number>(0);
    const [demoMetrics, setDemoMetrics] = useState({ clarity: 80, depth: 75, pace: 130 });
    const timerRef = useRef<NodeJS.Timeout | null>(null);

    // Contact Form state
    const [contactSubmitted, setContactSubmitted] = useState<boolean>(false);
    const [contactName, setContactName] = useState("");
    const [contactEmail, setContactEmail] = useState("");
    const [contactMsg, setContactMsg] = useState("");

    // Whitepapers state
    const [downloadingId, setDownloadingId] = useState<string | null>(null);
    const [downloadProgress, setDownloadProgress] = useState<number>(0);

    // Reset states on modal close/change
    useEffect(() => {
        if (!activeModal) {
            setDemoPlaying(false);
            setDemoStep(0);
            setDemoMetrics({ clarity: 80, depth: 75, pace: 130 });
            setContactSubmitted(false);
            setContactName("");
            setContactEmail("");
            setContactMsg("");
            setDownloadingId(null);
            setDownloadProgress(0);
        }
        if (activeModal === "demo") {
            setDemoPlaying(true);
        }
    }, [activeModal]);

    // Demo play loop
    useEffect(() => {
        if (demoPlaying) {
            timerRef.current = setInterval(() => {
                setDemoStep((prev) => {
                    const next = (prev + 1) % DEMO_DIALOGUE.length;
                    // Update metrics if current step has them
                    const line = DEMO_DIALOGUE[next];
                    if (line.metrics) {
                        setDemoMetrics(line.metrics);
                    }
                    return next;
                });
            }, 5500);
        } else {
            if (timerRef.current) clearInterval(timerRef.current);
        }

        return () => {
            if (timerRef.current) clearInterval(timerRef.current);
        };
    }, [demoPlaying]);

    if (!activeModal) return null;

    const modalType = activeModal as ModalType;

    const handleCopy = (text: string) => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const handleDownload = (id: string) => {
        setDownloadingId(id);
        setDownloadProgress(0);
        const interval = setInterval(() => {
            setDownloadProgress((prev) => {
                if (prev >= 100) {
                    clearInterval(interval);
                    setTimeout(() => {
                        setDownloadingId(null);
                    }, 500);
                    return 100;
                }
                return prev + 20;
            });
        }, 150);
    };

    const renderContent = () => {
        switch (modalType) {
            case "demo":
                return (
                    <div className="space-y-6">
                        <div className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
                            <div>
                                <h3 className="text-xl font-extrabold text-charcoal dark:text-white">
                                    Interactive AI Interview Demo
                                </h3>
                                <p className="text-xs text-slate-500 dark:text-slate-400">
                                    Watch how BrainTrain scores responses and coaches you in real time
                                </p>
                            </div>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={() => setDemoPlaying(!demoPlaying)}
                                    className="flex items-center justify-center size-8 rounded-lg bg-primary/10 text-primary hover:bg-primary/20 transition-colors"
                                >
                                    {demoPlaying ? <Pause size={15} /> : <Play size={15} className="ml-0.5" />}
                                </button>
                                <button
                                    onClick={() => {
                                        setDemoStep(0);
                                        setDemoMetrics({ clarity: 80, depth: 75, pace: 130 });
                                    }}
                                    className="flex items-center justify-center size-8 rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700 transition-colors"
                                    title="Restart Demo"
                                >
                                    <RotateCcw size={15} />
                                </button>
                            </div>
                        </div>

                        {/* Simulator Layout */}
                        <div className="grid grid-cols-1 md:grid-cols-[1.5fr_1fr] gap-6">
                            {/* Live Chat feed */}
                            <div className="flex flex-col h-[340px] bg-slate-50 dark:bg-slate-950 rounded-2xl border border-slate-100 dark:border-slate-900 p-4 overflow-y-auto space-y-4">
                                {DEMO_DIALOGUE.slice(0, demoStep + 1).map((line, idx) => {
                                    const isInterviewer = line.speaker === "interviewer";
                                    const isCoach = line.speaker === "coach";
                                    return (
                                        <div
                                            key={idx}
                                            className={cn(
                                                "flex flex-col max-w-[85%] rounded-2xl p-3 text-sm animate-in fade-in slide-in-from-bottom-2 duration-300",
                                                isInterviewer
                                                    ? "bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 text-charcoal dark:text-white self-start"
                                                    : isCoach
                                                    ? "bg-amber-500/10 border border-amber-500/20 text-amber-800 dark:text-amber-300 self-center max-w-[95%] text-xs"
                                                    : "bg-primary text-white self-end"
                                            )}
                                        >
                                            <span className="text-[10px] font-bold uppercase tracking-wider mb-1 opacity-60">
                                                {isInterviewer ? "AI Panel" : isCoach ? "AI Coach Feedback" : "You (Candidate)"}
                                            </span>
                                            <p className="leading-relaxed">{line.text}</p>
                                        </div>
                                    );
                                })}
                            </div>

                            {/* Live Metrics sidebar */}
                            <div className="flex flex-col justify-between border border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900/50 rounded-2xl p-4">
                                <div className="space-y-4">
                                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                                        Live Speech Metrics
                                    </h4>

                                    <div className="space-y-3">
                                        <div>
                                            <div className="flex justify-between text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                                                <span>Speech Clarity</span>
                                                <span className="text-primary">{demoMetrics.clarity}%</span>
                                            </div>
                                            <div className="h-1.5 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-primary transition-all duration-700"
                                                    style={{ width: `${demoMetrics.clarity}%` }}
                                                />
                                            </div>
                                        </div>

                                        <div>
                                            <div className="flex justify-between text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                                                <span>Technical Depth</span>
                                                <span className="text-emerald-500">{demoMetrics.depth}%</span>
                                            </div>
                                            <div className="h-1.5 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-emerald-500 transition-all duration-700"
                                                    style={{ width: `${demoMetrics.depth}%` }}
                                                />
                                            </div>
                                        </div>

                                        <div>
                                            <div className="flex justify-between text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                                                <span>Pacing (wpm)</span>
                                                <span className="text-sky-500">{demoMetrics.pace}</span>
                                            </div>
                                            <div className="h-1.5 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-sky-500 transition-all duration-700"
                                                    style={{ width: `${Math.min(100, (demoMetrics.pace / 200) * 100)}%` }}
                                                />
                                            </div>
                                            <span className="text-[9px] text-slate-400 dark:text-slate-500 mt-1 block">
                                                Target: 110-150 words/min
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                <div className="pt-4 border-t border-slate-100 dark:border-slate-800/80">
                                    <div className="rounded-xl bg-slate-50 dark:bg-slate-950 p-3 border border-slate-100 dark:border-slate-900 text-center">
                                        <span className="block text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest">
                                            Status
                                        </span>
                                        <span className="text-xs font-bold text-slate-700 dark:text-slate-300 animate-pulse flex items-center justify-center gap-1.5 mt-1">
                                            <span className="size-2 rounded-full bg-primary animate-ping" />
                                            {demoPlaying ? "AI Interview is live" : "Demo paused"}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                );

            case "api":
                return (
                    <div className="space-y-6">
                        <div className="border-b border-slate-100 pb-4 dark:border-slate-800">
                            <h3 className="text-xl font-extrabold text-charcoal dark:text-white flex items-center gap-2">
                                <Terminal size={22} className="text-primary" />
                                Developer API access
                            </h3>
                            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                                Integrate AI-powered interview pipelines directly into your workflows.
                            </p>
                        </div>

                        {/* Tabs */}
                        <div className="flex border-b border-slate-100 dark:border-slate-800">
                            {API_LANGUAGES.map((lang) => (
                                <button
                                    key={lang}
                                    onClick={() => setActiveTab(lang)}
                                    className={cn(
                                        "px-4 py-2 text-xs font-bold transition-all border-b-2",
                                        activeTab === lang
                                            ? "border-primary text-primary"
                                            : "border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-white"
                                    )}
                                >
                                    {lang}
                                </button>
                            ))}
                        </div>

                        {/* Code editor mockup */}
                        <div className="relative rounded-xl overflow-hidden bg-slate-900 border border-slate-800 text-slate-300 p-4 font-mono text-xs shadow-inner">
                            <button
                                onClick={() => handleCopy(API_CODE[activeTab as keyof typeof API_CODE])}
                                className="absolute right-3 top-3 flex items-center gap-1 rounded bg-slate-800 border border-slate-700 hover:bg-slate-700 text-slate-400 hover:text-white px-2 py-1 text-[10px] transition-colors"
                            >
                                {copied ? <Check size={11} className="text-emerald-500" /> : <Copy size={11} />}
                                {copied ? "Copied!" : "Copy Code"}
                            </button>
                            <pre className="overflow-x-auto pt-4 leading-relaxed whitespace-pre">
                                {API_CODE[activeTab as keyof typeof API_CODE]}
                            </pre>
                        </div>

                        <div className="rounded-xl border border-slate-100 dark:border-slate-800 p-4 bg-slate-50 dark:bg-slate-900/30 flex gap-3">
                            <Lock size={20} className="text-primary shrink-0 mt-0.5" />
                            <div>
                                <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300">
                                    Looking for an Enterprise Sandbox API Key?
                                </h4>
                                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                                    Full API access is available for enterprise plan subscribers. Contact support or generate your credential within the Developer Console settings.
                                </p>
                            </div>
                        </div>
                    </div>
                );

            case "about":
                return (
                    <div className="space-y-6">
                        <div className="border-b border-slate-100 pb-4 dark:border-slate-800">
                            <h3 className="text-xl font-extrabold text-charcoal dark:text-white">
                                About BrainTrain
                            </h3>
                            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                                Empowering candidates worldwide to land life-changing career opportunities.
                            </p>
                        </div>

                        <div className="space-y-4 text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                            <p>
                                BrainTrain was founded in 2024 by a group of former tech recruiters, engineers, and AI research scientists. Having conducted thousands of interviews combined, we realized that the primary barrier for talented candidates wasn&apos;t their technical skill level, but their performance under actual interview pressure.
                            </p>
                            <p>
                                By utilizing high-fidelity generative AI personas, real-time speech transcription metrics, and structured behavioral analytics, we offer the same clinical precision of elite human coaching at a fraction of the cost.
                            </p>
                        </div>

                        <div className="grid grid-cols-3 gap-4 pt-4 border-t border-slate-100 dark:border-slate-800">
                            <div className="text-center p-3 rounded-xl bg-slate-50 dark:bg-slate-900/50">
                                <span className="block text-2xl font-black text-primary">50k+</span>
                                <span className="text-[10px] text-slate-400 dark:text-slate-500 font-bold uppercase tracking-wider mt-1 block">
                                    Users Assisted
                                </span>
                            </div>
                            <div className="text-center p-3 rounded-xl bg-slate-50 dark:bg-slate-900/50">
                                <span className="block text-2xl font-black text-emerald-500">1.5M+</span>
                                <span className="text-[10px] text-slate-400 dark:text-slate-500 font-bold uppercase tracking-wider mt-1 block">
                                    Minutes Practiced
                                </span>
                            </div>
                            <div className="text-center p-3 rounded-xl bg-slate-50 dark:bg-slate-900/50">
                                <span className="block text-2xl font-black text-sky-500">92.4%</span>
                                <span className="text-[10px] text-slate-400 dark:text-slate-500 font-bold uppercase tracking-wider mt-1 block">
                                    Placement Success
                                </span>
                            </div>
                        </div>
                    </div>
                );

            case "contact":
                return (
                    <div className="space-y-6">
                        <div className="border-b border-slate-100 pb-4 dark:border-slate-800">
                            <h3 className="text-xl font-extrabold text-charcoal dark:text-white">
                                Contact Support & Sales
                            </h3>
                            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                                Drop us a line. We typically reply within a few hours.
                            </p>
                        </div>

                        {contactSubmitted ? (
                            <div className="text-center py-10 space-y-4">
                                <div className="mx-auto size-12 rounded-full bg-emerald-100 dark:bg-emerald-950/30 flex items-center justify-center text-emerald-500">
                                    <CheckCircle2 size={24} />
                                </div>
                                <div>
                                    <h4 className="text-base font-extrabold text-charcoal dark:text-white">
                                        Message Dispatched!
                                    </h4>
                                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                                        We have received your message and will follow up shortly.
                                    </p>
                                </div>
                                <button
                                    onClick={() => setContactSubmitted(false)}
                                    className="px-6 py-2 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 rounded-lg text-xs font-bold hover:bg-slate-200 transition-all"
                                >
                                    Send Another Message
                                </button>
                            </div>
                        ) : (
                            <form
                                onSubmit={(e) => {
                                    e.preventDefault();
                                    setContactSubmitted(true);
                                }}
                                className="space-y-4"
                            >
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-1">
                                        <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                                            Your Name
                                        </label>
                                        <input
                                            type="text"
                                            required
                                            value={contactName}
                                            onChange={(e) => setContactName(e.target.value)}
                                            className="w-full text-xs p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 focus:border-primary outline-none text-charcoal dark:text-white"
                                        />
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                                            Email Address
                                        </label>
                                        <input
                                            type="email"
                                            required
                                            value={contactEmail}
                                            onChange={(e) => setContactEmail(e.target.value)}
                                            className="w-full text-xs p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 focus:border-primary outline-none text-charcoal dark:text-white"
                                        />
                                    </div>
                                </div>

                                <div className="space-y-1">
                                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                                        Your Message
                                    </label>
                                    <textarea
                                        required
                                        rows={4}
                                        value={contactMsg}
                                        onChange={(e) => setContactMsg(e.target.value)}
                                        className="w-full text-xs p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 focus:border-primary outline-none text-charcoal dark:text-white resize-none"
                                        placeholder="How can we help?"
                                    />
                                </div>

                                <button
                                    type="submit"
                                    className="w-full py-3 rounded-lg bg-primary hover:bg-primary-dark text-white font-bold text-xs transition-colors flex items-center justify-center gap-2"
                                >
                                    <Send size={14} />
                                    Send Message
                                </button>
                            </form>
                        )}
                    </div>
                );

            case "privacy":
                return (
                    <div className="space-y-6">
                        <div className="border-b border-slate-100 pb-4 dark:border-slate-800">
                            <h3 className="text-xl font-extrabold text-charcoal dark:text-white">
                                Privacy & Security Principles
                            </h3>
                            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                                Your records, transcripts, and evaluation data are safe with us.
                            </p>
                        </div>

                        <div className="space-y-4">
                            <div className="flex gap-3">
                                <div className="size-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary shrink-0">
                                    <Lock size={16} />
                                </div>
                                <div>
                                    <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300">
                                        End-to-End Encryption
                                    </h4>
                                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                                        We encrypt all session transcripts and audio evaluations in transit and at rest. Access is strictly constrained by user session tokens.
                                    </p>
                                </div>
                            </div>

                            <div className="flex gap-3">
                                <div className="size-8 rounded-lg bg-emerald-100 dark:bg-emerald-950/30 flex items-center justify-center text-emerald-500 shrink-0">
                                    <Shield size={16} />
                                </div>
                                <div>
                                    <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300">
                                        Zero Data Selling Policy
                                    </h4>
                                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                                        We will never monetize, lease, or distribute your private transcripts, resume details, or metrics reports to third-party ad brokers or recruiters.
                                    </p>
                                </div>
                            </div>

                            <div className="flex gap-3">
                                <div className="size-8 rounded-lg bg-sky-100 dark:bg-sky-950/30 flex items-center justify-center text-sky-500 shrink-0">
                                    <Users size={16} />
                                </div>
                                <div>
                                    <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300">
                                        EU-US Data Privacy Framework
                                    </h4>
                                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                                        Our cloud systems align with the strictest GDPR guidelines. You maintain total, permanent control to purge your profile data on demand.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                );

            case "blog":
                return (
                    <div className="space-y-6">
                        <div className="border-b border-slate-100 pb-4 dark:border-slate-800">
                            <h3 className="text-xl font-extrabold text-charcoal dark:text-white">
                                BrainTrain Blog
                            </h3>
                            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                                Expert insights on landing top-tier software engineering roles.
                            </p>
                        </div>

                        <div className="space-y-4">
                            {BLOG_POSTS.map((post) => (
                                <div
                                    key={post.title}
                                    className="p-4 rounded-xl border border-slate-100 hover:border-primary/20 bg-white dark:border-slate-850 dark:bg-slate-900/50 hover:shadow-md transition-all group cursor-pointer"
                                >
                                    <div className="flex justify-between items-start mb-2">
                                        <span className="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-[10px] font-bold">
                                            {post.tag}
                                        </span>
                                        <span className="text-[10px] text-slate-400 dark:text-slate-500">
                                            {post.readTime}
                                        </span>
                                    </div>
                                    <h4 className="text-sm font-bold text-slate-700 dark:text-slate-300 group-hover:text-primary transition-colors">
                                        {post.title}
                                    </h4>
                                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                                        {post.excerpt}
                                    </p>
                                </div>
                            ))}
                        </div>
                    </div>
                );

            case "help":
                return (
                    <div className="space-y-6">
                        <div className="border-b border-slate-100 pb-4 dark:border-slate-800">
                            <h3 className="text-xl font-extrabold text-charcoal dark:text-white">
                                Help Center & FAQ
                            </h3>
                            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                                Everything you need to get up and running.
                            </p>
                        </div>

                        <div className="space-y-3">
                            {HELP_FAQS.map((faq, idx) => (
                                <div
                                    key={idx}
                                    className="border border-slate-150 dark:border-slate-800 rounded-xl overflow-hidden"
                                >
                                    <button
                                        onClick={() => setFaqOpen(faqOpen === idx ? null : idx)}
                                        className="w-full flex justify-between items-center p-4 bg-slate-50 dark:bg-slate-900/50 hover:bg-slate-100 dark:hover:bg-slate-800/50 text-left transition-colors"
                                    >
                                        <span className="text-xs font-bold text-slate-700 dark:text-slate-300">
                                            {faq.q}
                                        </span>
                                        {faqOpen === idx ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
                                    </button>
                                    {faqOpen === idx && (
                                        <div className="p-4 bg-white dark:bg-slate-950 text-xs text-slate-500 dark:text-slate-400 leading-relaxed border-t border-slate-100 dark:border-slate-850 animate-in fade-in duration-250">
                                            {faq.a}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                );

            case "whitepapers":
                return (
                    <div className="space-y-6">
                        <div className="border-b border-slate-100 pb-4 dark:border-slate-800">
                            <h3 className="text-xl font-extrabold text-charcoal dark:text-white">
                                Executive Whitepapers
                            </h3>
                            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                                Peer-reviewed research on AI assessment precision.
                            </p>
                        </div>

                        <div className="space-y-4">
                            {[
                                {
                                    id: "wp-1",
                                    title: "Validating Generative Evaluation Models in Technical Hiring",
                                    desc: "Statistical analysis of AI scoring variance compared to human panels.",
                                    size: "2.4 MB PDF",
                                },
                                {
                                    id: "wp-2",
                                    title: "Cognitive Stress Mitigation in Simulated Interview Scenarios",
                                    desc: "How practice loops reduce heart rate volatility during high-pressure panels.",
                                    size: "1.8 MB PDF",
                                },
                            ].map((paper) => (
                                <div
                                    key={paper.id}
                                    className="p-4 rounded-xl border border-slate-100 bg-white dark:border-slate-850 dark:bg-slate-900/50 flex justify-between items-center"
                                >
                                    <div className="max-w-[70%]">
                                        <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300">
                                            {paper.title}
                                        </h4>
                                        <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 leading-relaxed">
                                            {paper.desc}
                                        </p>
                                        <span className="text-[9px] font-bold text-primary mt-1 block">
                                            {paper.size}
                                        </span>
                                    </div>
                                    <button
                                        onClick={() => handleDownload(paper.id)}
                                        disabled={downloadingId !== null}
                                        className="px-4 py-2 bg-primary text-white rounded-lg text-xs font-bold hover:bg-primary-dark transition-all disabled:bg-slate-100 disabled:text-slate-400 flex items-center gap-1.5 min-w-[110px] justify-center"
                                    >
                                        {downloadingId === paper.id ? (
                                            <div className="w-full flex flex-col items-center">
                                                <span className="text-[9px] mb-0.5">Downloading</span>
                                                <div className="w-full h-1 bg-white/30 rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-white transition-all duration-150"
                                                        style={{ width: `${downloadProgress}%` }}
                                                    />
                                                </div>
                                            </div>
                                        ) : (
                                            <>
                                                <FileDown size={14} />
                                                Download
                                            </>
                                        )}
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                );

            case "guides":
                return (
                    <div className="space-y-6">
                        <div className="border-b border-slate-100 pb-4 dark:border-slate-800">
                            <h3 className="text-xl font-extrabold text-charcoal dark:text-white">
                                Candidate Training Guides
                            </h3>
                            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                                Complete preparation checklists for various job roles.
                            </p>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            {[
                                {
                                    id: "guide-se",
                                    title: "Staff Engineer Guide",
                                    desc: "Architectural blueprint, system design, staff behavioral scripts.",
                                    lessons: "12 sections",
                                },
                                {
                                    id: "guide-pm",
                                    title: "Product Manager Blueprint",
                                    desc: "Product strategy, estimation math, metrics & prioritization.",
                                    lessons: "9 sections",
                                },
                            ].map((guide) => (
                                <div
                                    key={guide.id}
                                    className="p-4 rounded-xl border border-slate-150 dark:border-slate-800 bg-white dark:bg-slate-900/30 flex flex-col justify-between h-[140px]"
                                >
                                    <div>
                                        <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300">
                                            {guide.title}
                                        </h4>
                                        <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                                            {guide.desc}
                                        </p>
                                    </div>
                                    <div className="flex justify-between items-center border-t border-slate-100 dark:border-slate-850 pt-2 mt-2">
                                        <span className="text-[10px] text-slate-400 dark:text-slate-500 font-medium">
                                            {guide.lessons}
                                        </span>
                                        <button
                                            onClick={() => handleDownload(guide.id)}
                                            disabled={downloadingId !== null}
                                            className="text-xs font-bold text-primary hover:text-primary-dark transition-colors flex items-center gap-0.5"
                                        >
                                            {downloadingId === guide.id ? "Downloading..." : "Get PDF"}
                                            <ArrowRight size={12} />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                );

            default:
                return null;
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <div
                onClick={closeModal}
                className="absolute inset-0 bg-black/60 backdrop-blur-sm cursor-pointer"
            />

            {/* Modal Card */}
            <div className="relative w-full max-w-2xl bg-white dark:bg-slate-900 rounded-[2rem] shadow-2xl border border-slate-100 dark:border-slate-800 p-6 md:p-8 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                {/* Glow accent */}
                <div className="absolute top-0 right-0 w-44 h-44 bg-primary/10 rounded-full blur-2xl pointer-events-none" />

                {/* Close Button */}
                <button
                    onClick={closeModal}
                    className="absolute right-5 top-5 p-2 rounded-full text-slate-400 hover:text-slate-800 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                >
                    <X size={20} />
                </button>

                {/* Inner Content */}
                <div className="relative z-10">{renderContent()}</div>
            </div>
        </div>
    );
}
