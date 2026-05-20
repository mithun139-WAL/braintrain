import { cn } from "@/lib/utils";

type ButtonVariant = "primary" | "secondary" | "ghost";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonStylesOptions {
    variant?: ButtonVariant;
    size?: ButtonSize;
    fullWidth?: boolean;
}

const variantStyles: Record<ButtonVariant, string> = {
    primary:
        "bg-primary text-primary-foreground shadow-primary-sm hover:bg-primary-dark active:translate-y-px",
    secondary:
        "border border-border bg-card text-foreground shadow-card hover:bg-muted/70 hover:border-border",
    ghost:
        "text-muted-foreground hover:bg-muted hover:text-foreground",
};

const sizeStyles: Record<ButtonSize, string> = {
    sm: "h-9 px-4 rounded-xl text-sm",
    md: "h-11 px-5 rounded-2xl text-sm",
    lg: "h-12 px-6 rounded-2xl text-sm",
};

export function buttonStyles({
    variant = "primary",
    size = "md",
    fullWidth = false,
}: ButtonStylesOptions = {}) {
    return cn(
        "inline-flex items-center justify-center gap-2 font-semibold transition-all duration-200",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background",
        "disabled:pointer-events-none disabled:opacity-50",
        variantStyles[variant],
        sizeStyles[size],
        fullWidth && "w-full"
    );
}
