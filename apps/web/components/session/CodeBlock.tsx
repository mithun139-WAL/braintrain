import React, { useState } from "react";
import { Check, Copy } from "lucide-react";

interface CodeBlockProps {
    code: string;
    language?: string;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({ code, language }) => {
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(code);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="relative my-4 rounded-lg bg-slate-900 font-mono text-xs text-slate-100 overflow-hidden border border-slate-800">
            <div className="flex items-center justify-between px-4 py-2 bg-slate-950 border-b border-slate-850 text-[10px] text-slate-400 font-sans font-medium uppercase tracking-wider">
                <span>{language || "code"}</span>
                <button
                    onClick={handleCopy}
                    className="flex items-center gap-1 hover:text-slate-200 transition-colors"
                >
                    {copied ? (
                        <>
                            <Check size={12} className="text-green-400" />
                            <span>Copied</span>
                        </>
                    ) : (
                        <>
                            <Copy size={12} />
                            <span>Copy</span>
                        </>
                    )}
                </button>
            </div>
            <pre className="p-4 overflow-x-auto whitespace-pre leading-relaxed">
                <code>{code}</code>
            </pre>
        </div>
    );
};
