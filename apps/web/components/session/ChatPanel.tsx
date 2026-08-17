import React, { useState, useRef, useEffect } from "react";
import { Send, Image as ImageIcon, Loader2 } from "lucide-react";
import { type ChatMessage } from "@/hooks/useSessionDataChannel";
import { CodeBlock } from "./CodeBlock";

interface ChatPanelProps {
    messages: ChatMessage[];
    onSend: (content: string, file?: File) => Promise<void>;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({ messages, onSend }) => {
    const [input, setInput] = useState("");
    const [file, setFile] = useState<File | null>(null);
    const [sending, setSending] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() && !file) return;

        setSending(true);
        try {
            await onSend(input, file || undefined);
            setInput("");
            setFile(null);
        } catch (err) {
            console.error("Failed to send message:", err);
        } finally {
            setSending(false);
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    // Render message content with markdown-like code block extraction
    const renderContent = (content: string) => {
        const parts = content.split(/(```[\s\S]*?```)/g);
        return parts.map((part, index) => {
            if (part.startsWith("```")) {
                const match = part.match(/```(\w*)\n([\s\S]*?)```/);
                const lang = match ? match[1] : "";
                const code = match ? match[2] : part.slice(3, -3);
                return <CodeBlock key={index} code={code.trim()} language={lang} />;
            }
            return (
                <p key={index} className="whitespace-pre-wrap leading-relaxed">
                    {part}
                </p>
            );
        });
    };

    return (
        <div className="flex flex-col h-full bg-slate-900 border-l border-slate-800">
            {/* Header */}
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
                <h3 className="font-semibold text-sm text-slate-200">Session Transcript & Chat</h3>
                <span className="text-[10px] bg-primary/10 text-primary-light px-2 py-0.5 rounded-full font-medium">
                    Live Session
                </span>
            </div>

            {/* Message list */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {messages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-center p-8">
                        <div className="size-12 rounded-2xl bg-slate-800/50 border border-slate-700/50 flex items-center justify-center text-slate-500 mb-3 animate-pulse">
                            💬
                        </div>
                        <h4 className="text-slate-300 font-medium text-sm mb-1">No Chat History</h4>
                        <p className="text-xs text-slate-500 max-w-[240px]">
                            Once the interview starts, the transcripts and challenges will appear here.
                        </p>
                    </div>
                ) : (
                    messages.map((msg) => {
                        const isAI = msg.role === "interviewer";
                        return (
                            <div
                                key={msg.id}
                                className={`flex flex-col ${isAI ? "items-start" : "items-end"}`}
                            >
                                <span className="text-[10px] text-slate-500 mb-1 font-medium px-1">
                                    {isAI ? "AI Interviewer" : "You"}
                                </span>
                                <div
                                    className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${
                                        isAI
                                            ? "bg-slate-800/80 text-slate-200 border border-slate-750"
                                            : "bg-primary text-white"
                                    }`}
                                >
                                    {renderContent(msg.content)}
                                </div>
                            </div>
                        );
                    })
                )}
                <div ref={bottomRef} />
            </div>

            {/* Input Form */}
            <form onSubmit={handleSend} className="p-4 border-t border-slate-800 bg-slate-950/40">
                {file && (
                    <div className="mb-2 px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg flex items-center justify-between text-xs text-slate-300">
                        <span className="truncate max-w-[200px]">{file.name}</span>
                        <button
                            type="button"
                            onClick={() => setFile(null)}
                            className="text-red-400 hover:text-red-300 ml-2"
                        >
                            Remove
                        </button>
                    </div>
                )}
                <div className="flex items-end gap-2 bg-slate-800/60 border border-slate-700/85 rounded-xl p-2 focus-within:border-primary transition-colors">
                    <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        className="p-2 text-slate-400 hover:text-slate-200 rounded-lg hover:bg-slate-750 transition-colors"
                        title="Upload diagram image"
                    >
                        <ImageIcon size={18} />
                    </button>
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*"
                        onChange={handleFileChange}
                        className="hidden"
                    />
                    <textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === "Enter" && !e.shiftKey) {
                                e.preventDefault();
                                handleSend(e);
                            }
                        }}
                        placeholder="Type code or describe your solution... (Press Enter to Send)"
                        rows={1}
                        className="flex-1 bg-transparent border-0 outline-none focus:ring-0 text-slate-200 text-sm py-1.5 resize-none max-h-32 min-h-[36px]"
                    />
                    <button
                        type="submit"
                        disabled={sending || (!input.trim() && !file)}
                        className="p-2.5 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:bg-slate-800 disabled:text-slate-600 transition-colors flex-shrink-0"
                    >
                        {sending ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
                    </button>
                </div>
            </form>
        </div>
    );
};
