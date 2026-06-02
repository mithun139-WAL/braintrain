"use client";

import { useState } from "react";
import { X, Plus, Brain, Info } from "lucide-react";
import { CreateTopicDto } from "@braintrain/shared";

interface CreateTopicModalProps {
    isOpen: boolean;
    onClose: () => void;
    onCreate: (data: CreateTopicDto) => void;
    isSubmitting?: boolean;
}

export function CreateTopicModal({ isOpen, onClose, onCreate, isSubmitting }: CreateTopicModalProps) {
    const [name, setName] = useState("");
    const [description, setDescription] = useState("");

    if (!isOpen) return null;

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!name.trim()) return;
        onCreate({ name: name.trim(), description: description.trim() });
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-white dark:bg-gray-950 w-full max-w-md rounded-2xl shadow-2xl border border-gray-100 dark:border-gray-800 overflow-hidden animate-in zoom-in-95 duration-200">
                <div className="p-6 border-b border-gray-50 dark:border-gray-800 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="size-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
                            <Plus size={20} />
                        </div>
                        <div>
                            <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">Create New Topic</h2>
                            <p className="text-xs text-gray-500 dark:text-gray-400">Add a custom practice domain</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 rounded-lg text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors"
                    >
                        <X size={20} />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-6 flex flex-col gap-5">
                    <div className="flex flex-col gap-2">
                        <label className="text-xs font-bold text-gray-700 dark:text-gray-300 uppercase tracking-widest">
                            Topic Name
                        </label>
                        <input
                            type="text"
                            placeholder="e.g. System Design - Microservices"
                            className="w-full px-4 py-3 rounded-xl bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 focus:border-primary focus:ring-2 focus:ring-primary/10 transition-all outline-none text-sm font-medium text-gray-900 dark:text-gray-100"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            required
                        />
                    </div>

                    <div className="flex flex-col gap-2">
                        <label className="text-xs font-bold text-gray-700 dark:text-gray-300 uppercase tracking-widest">
                            Description
                        </label>
                        <textarea
                            placeholder="Briefly describe what this topic covers..."
                            rows={3}
                            className="w-full px-4 py-3 rounded-xl bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 focus:border-primary focus:ring-2 focus:ring-primary/10 transition-all outline-none text-sm font-medium text-gray-900 dark:text-gray-100 resize-none"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                        />
                    </div>

                    <div className="flex items-start gap-3 p-4 bg-primary/5 dark:bg-primary/10 rounded-xl border border-primary/10">
                        <Info size={16} className="text-primary mt-0.5 shrink-0" />
                        <p className="text-[11px] text-primary/80 dark:text-primary/70 leading-relaxed font-medium">
                            Custom topics allow the AI to tailor interview questions specifically to the domain you want to practice.
                        </p>
                    </div>

                    <div className="flex gap-3 pt-2">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 h-11 rounded-xl border border-gray-100 dark:border-gray-800 text-sm font-bold text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-900 transition-all"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={isSubmitting || !name.trim()}
                            className="flex-1 h-11 rounded-xl bg-primary text-white text-sm font-bold shadow-lg shadow-primary/20 hover:bg-primary-dark transition-all active:scale-95 disabled:opacity-50 disabled:active:scale-100"
                        >
                            {isSubmitting ? "Creating..." : "Create Topic"}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
