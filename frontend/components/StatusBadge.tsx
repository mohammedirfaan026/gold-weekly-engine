import React from "react";
import { cn } from "@/lib/utils";

interface StatusBadgeProps {
  label: string;
  variant?: "success" | "warning" | "danger" | "info" | "neutral" | "gold";
  size?: "sm" | "md";
  className?: string;
}

export function StatusBadge({
  label,
  variant = "neutral",
  size = "sm",
  className,
}: StatusBadgeProps) {
  const variantStyles = {
    success: "bg-bull/10 text-bull border-bull/30",
    warning: "bg-amber-500/10 text-amber-400 border-amber-500/30",
    danger: "bg-bear/10 text-bear border-bear/30",
    info: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30",
    neutral: "bg-terminal-border text-terminal-muted border-terminal-borderBright",
    gold: "bg-gold-500/15 text-gold-400 border-gold-500/40",
  };

  const sizeStyles = {
    sm: "px-2 py-0.5 text-[10px]",
    md: "px-2.5 py-1 text-xs",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 font-mono uppercase tracking-wider rounded border font-medium",
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
    >
      {label}
    </span>
  );
}
