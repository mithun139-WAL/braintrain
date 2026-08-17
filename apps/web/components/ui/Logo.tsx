import { Brain } from "lucide-react";
import { cn } from "@/lib/utils";

interface LogoProps {
    className?: string;
    iconClassName?: string;
    iconWrapperClassName?: string;
    iconSize?: number;
    showText?: boolean;
    textClassName?: string;
}

export function Logo({
    className,
    iconClassName,
    iconWrapperClassName,
    iconSize = 18,
    showText = true,
    textClassName,
}: LogoProps) {
    return (
        <div className={cn("flex items-center gap-2", className)}>
            <div
                className={cn(
                    "flex items-center justify-center rounded-2xl bg-primary text-white shadow-lg shadow-primary/20 flex-shrink-0",
                    iconWrapperClassName || "size-10"
                )}
            >
                <Brain className={cn(iconClassName)} size={iconSize} />
            </div>
            {showText && (
                <span
                    className={cn(
                        "font-extrabold tracking-tight text-foreground dark:text-white",
                        textClassName || "text-xl"
                    )}
                >
                    BrainTrain
                </span>
            )}
        </div>
    );
}
