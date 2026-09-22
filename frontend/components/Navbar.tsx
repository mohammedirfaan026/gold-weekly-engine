"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import {
  LayoutDashboard,
  TrendingUp,
  Zap,
  Filter,
  Calendar,
  Layers,
  Cpu,
  LineChart,
  ShieldCheck,
  Server,
} from "lucide-react";

const NAV_ITEMS = [
  { name: "Overview", href: "/", icon: LayoutDashboard },
  { name: "Weekly Macro", href: "/weekly", icon: TrendingUp },
  { name: "Reactions", href: "/reaction", icon: Zap },
  { name: "Conditional", href: "/conditional", icon: Filter },
  { name: "Events", href: "/explorer", icon: Calendar },
  { name: "Regimes", href: "/regimes", icon: Layers },
  { name: "Models", href: "/models", icon: Cpu },
  { name: "Backtests", href: "/backtests", icon: LineChart },
  { name: "Data Health", href: "/data-health", icon: ShieldCheck },
];

export function Navbar() {
  const pathname = usePathname();
  const [utcTime, setUtcTime] = useState<string>("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setUtcTime(now.toUTCString().replace("GMT", "UTC"));
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="border-b border-terminal-border bg-terminal-panel/90 backdrop-blur sticky top-0 z-50">
      {/* Top micro bar */}
      <div className="flex items-center justify-between px-4 py-1 border-b border-terminal-border/50 text-[11px] font-mono text-terminal-muted bg-terminal-bg/80">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 font-semibold text-gold-400">
            <span className="h-2 w-2 rounded-full bg-gold-400 animate-pulse" />
            GOLD RESEARCH TERMINAL v2.0
          </span>
          <span className="hidden sm:inline text-terminal-dim">|</span>
          <span className="hidden sm:flex items-center gap-1 text-terminal-dim">
            <Server className="h-3 w-3 text-emerald-400" />
            Oracle ARM64: 4 OCPU / 24GB ($0/mo)
          </span>
          <span className="hidden md:inline text-terminal-dim">|</span>
          <span className="hidden md:inline text-cyan-400">
            GCP Burst: Standby
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-emerald-400 flex items-center gap-1 font-semibold">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            SECURE TAILSCALE
          </span>
          <span className="text-terminal-dim">|</span>
          <span className="font-mono-nums">{utcTime || "SYNCING..."}</span>
        </div>
      </div>

      {/* Main navigation */}
      <nav className="flex items-center justify-between px-4 py-2 overflow-x-auto">
        <div className="flex items-center gap-1 min-w-max">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                  isActive
                    ? "bg-gold-500/15 text-gold-400 border border-gold-500/30"
                    : "text-terminal-muted hover:text-terminal-text hover:bg-terminal-card/80"
                }`}
              >
                <Icon className={`h-3.5 w-3.5 ${isActive ? "text-gold-400" : "text-terminal-dim"}`} />
                {item.name}
              </Link>
            );
          })}
        </div>
      </nav>
    </header>
  );
}
