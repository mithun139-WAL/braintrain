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
        "bg-primary text-primary-foreground shadow-[0_0_16px_rgba(var(--primary-rgb,99,102,241),0.35)] hover:brightness-110 active:translate-y-px active:shadow-none",
    secondary:
        "border border-border/80 bg-muted/40 text-foreground shadow-sm hover:bg-muted hover:border-primary/40 hover:text-primary active:translate-y-px",
    ghost:
        "text-muted-foreground hover:bg-muted/60 hover:text-foreground active:translate-y-px",
};

const sizeStyles: Record<ButtonSize, string> = {
    sm: "h-9 px-4 rounded-xl text-[13px]",
    md: "h-10 px-5 rounded-xl text-[13px]",
    lg: "h-12 px-6 rounded-2xl text-sm",
};

export function buttonStyles({
    variant = "primary",
    size = "md",
    fullWidth = false,
}: ButtonStylesOptions = {}) {
    return cn(
        "inline-flex items-center justify-center gap-2 font-semibold whitespace-nowrap cursor-pointer transition-all duration-200",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background",
        "disabled:pointer-events-none disabled:opacity-40",
        variantStyles[variant],
        sizeStyles[size],
        fullWidth && "w-full"
    );
}
