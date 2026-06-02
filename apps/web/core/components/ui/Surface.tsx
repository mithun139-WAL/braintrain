import * as React from "react";
import { cn } from "@/lib/utils";

type SurfaceVariant = "default" | "subtle" | "hero" | "ghost";
type SurfacePadding = "none" | "sm" | "md" | "lg" | "xl";

interface SurfaceProps extends React.HTMLAttributes<HTMLDivElement> {
    variant?: SurfaceVariant;
    padding?: SurfacePadding;
}

const surfaceVariants: Record<SurfaceVariant, string> = {
    default:
        "rounded-3xl border border-border/80 bg-card/95 shadow-card supports-[backdrop-filter]:bg-card/90",
    subtle: "rounded-3xl border border-border-subtle bg-muted/40",
    hero: "rounded-[2rem] border border-border/70 bg-card/90 shadow-elevated",
    ghost: "",
};

const surfacePadding: Record<SurfacePadding, string> = {
    none: "",
    sm: "p-4",
    md: "p-6",
    lg: "p-8",
    xl: "p-10",
};

export function Surface({
    variant = "default",
    padding = "md",
    className,
    ...props
}: SurfaceProps) {
    return <div className={cn(surfaceVariants[variant], surfacePadding[padding], className)} {...props} />;
}
