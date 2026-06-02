import React from "react";
import { Zap } from "lucide-react";
import { cn } from "@/lib/utils";

interface ConfirmationModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    title: string;
    description: string;
    confirmText?: string;
    cancelText?: string;
    variant?: "danger" | "primary" | "warning";
    icon?: React.ReactNode;
}

export function ConfirmationModal({
    isOpen,
    onClose,
    onConfirm,
    title,
    description,
    confirmText = "Confirm",
    cancelText = "Cancel",
    variant = "danger",
    icon,
}: ConfirmationModalProps) {
    if (!isOpen) return null;

    const variantStyles = {
        danger: {
            bg: "bg-rose-100 dark:bg-rose-900/30",
            text: "text-rose-600 dark:text-rose-400",
            button: "bg-rose-600 hover:bg-rose-700 focus:ring-rose-500 shadow-rose-500/20",
        },
        warning: {
            bg: "bg-amber-100 dark:bg-amber-900/30",
            text: "text-amber-600 dark:text-amber-400",
            button: "bg-amber-600 hover:bg-amber-700 focus:ring-amber-500 shadow-amber-500/20",
        },
        primary: {
            bg: "bg-primary/10 dark:bg-primary/20",
            text: "text-primary",
            button: "bg-primary hover:bg-primary-dark focus:ring-primary shadow-primary/20",
        },
    };

    const currentStyle = variantStyles[variant];

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-xl border border-gray-100 dark:border-gray-800 w-full max-w-sm p-6 overflow-hidden relative animate-in fade-in zoom-in-95 duration-200">
                <div className={cn("absolute top-0 left-0 w-full h-1", variant === 'danger' ? 'bg-rose-500' : variant === 'warning' ? 'bg-amber-500' : 'bg-primary')}></div>
                <div className="text-center">
                    <div className={cn("mx-auto flex items-center justify-center h-12 w-12 rounded-full mb-4", currentStyle.bg)}>
                        {icon || <Zap className={cn("h-6 w-6", currentStyle.text)} aria-hidden="true" />}
                    </div>
                    <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">{title}</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
                        {description}
                    </p>
                </div>
                <div className="flex gap-3 mt-4">
                    <button
                        type="button"
                        className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-xl font-medium text-sm hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-300 dark:focus:ring-gray-600 focus:ring-offset-2 dark:focus:ring-offset-gray-900"
                        onClick={onClose}
                    >
                        {cancelText}
                    </button>
                    <button
                        type="button"
                        className={cn("flex-1 px-4 py-2.5 text-white rounded-xl font-medium text-sm transition-colors shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-gray-900", currentStyle.button)}
                        onClick={onConfirm}
                    >
                        {confirmText}
                    </button>
                </div>
            </div>
        </div>
    );
}
