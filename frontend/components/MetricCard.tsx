import React from "react";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  change?: number;
  sampleSize?: number;
  provenance?: string;
  badge?: string;
  icon?: React.ReactNode;
  className?: string;
}

export function MetricCard({
  label,
  value,
  subValue,
  change,
  sampleSize,
  provenance,
  badge,
  icon,
  className,
}: MetricCardProps) {
  const isPositive = change !== undefined ? change > 0 : undefined;
  const isNegative = change !== undefined ? change < 0 : undefined;

  return (
    <div
      className={cn(
        "rounded-lg border border-terminal-border bg-terminal-panel p-4 flex flex-col justify-between hover:border-terminal-borderBright transition-colors",
        className
      )}
    >
      <div className="flex items-start justify-between">
        <span className="text-xs font-medium text-terminal-muted uppercase tracking-wider">
          {label}
        </span>
        <div className="flex items-center gap-1.5">
          {badge && (
            <span className="px-1.5 py-0.5 text-[10px] font-mono rounded bg-terminal-border text-terminal-muted">
              {badge}
            </span>
          )}
          {icon && <div className="text-terminal-dim">{icon}</div>}
        </div>
      </div>

      <div className="my-2">
        <div className="text-2xl font-bold font-mono text-terminal-text tracking-tight flex items-baseline gap-2">
          <span>{value}</span>
          {change !== undefined && (
            <span
              className={cn(
                "text-xs font-medium font-mono",
                isPositive && "text-bull",
                isNegative && "text-bear",
                !isPositive && !isNegative && "text-terminal-muted"
              )}
            >
              {isPositive ? "▲" : isNegative ? "▼" : "•"}{" "}
              {change > 0 ? `+${change.toFixed(2)}%` : `${change.toFixed(2)}%`}
            </span>
          )}
        </div>
        {subValue && (
          <p className="text-xs text-terminal-dim mt-0.5 font-mono">{subValue}</p>
        )}
      </div>

      <div className="flex items-center justify-between text-[11px] font-mono text-terminal-dim pt-2 border-t border-terminal-border/40">
        {sampleSize !== undefined ? (
          <span>Sample: <strong className="text-terminal-muted font-normal">N={sampleSize}</strong></span>
        ) : (
          <span>Verified PIT</span>
        )}
        {provenance && <span className="text-gold-500/80">{provenance}</span>}
      </div>
    </div>
  );
}
