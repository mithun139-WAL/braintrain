import * as React from "react";
import { cn } from "@/lib/utils";

interface PageHeaderProps {
    eyebrow?: string;
    title: string;
    description?: string;
    meta?: React.ReactNode;
    actions?: React.ReactNode;
    className?: string;
}

export function PageHeader({
    eyebrow,
    title,
    description,
    meta,
    actions,
    className,
}: PageHeaderProps) {
    return (
        <header className={cn("flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between", className)}>
            <div className="min-w-0 flex-1 space-y-3">
                {eyebrow ? (
                    <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-primary/80">
                        {eyebrow}
                    </p>
                ) : null}
                <div className="space-y-2">
                    <h1 className="font-display text-display-md text-foreground">{title}</h1>
                    {description ? (
                        <p className="max-w-reading text-body-md text-muted-foreground">{description}</p>
                    ) : null}
                </div>
                {meta ? <div className="flex flex-wrap gap-2">{meta}</div> : null}
            </div>
            {actions ? <div className="flex flex-wrap items-center gap-3">{actions}</div> : null}
        </header>
    );
}
