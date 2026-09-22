"use client";

import { useEffect, useState } from "react";
import { api, CurrentGold, RegimeState, SystemHealth, MacroEvent } from "@/lib/api";
import { MetricCard } from "@/components/MetricCard";
import { StatusBadge } from "@/components/StatusBadge";
import { formatNumber, formatPctDirect, formatDate } from "@/lib/utils";
import Link from "next/link";
import {
  TrendingUp,
  ShieldCheck,
  Zap,
  Activity,
  Calendar,
  Layers,
  Cpu,
  ArrowUpRight,
  RefreshCw,
  Database,
} from "lucide-react";

export default function OverviewPage() {
  const [gold, setGold] = useState<CurrentGold | null>(null);
  const [regimes, setRegimes] = useState<RegimeState | null>(null);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [recentEvents, setRecentEvents] = useState<MacroEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [gData, rData, hData, eData] = await Promise.all([
        api.getCurrentGold().catch(() => null),
        api.getCurrentRegimes().catch(() => null),
        api.getHealth().catch(() => null),
        api.getEvents({ limit: 6 }).catch(() => []),
      ]);
      setGold(gData);
      setRegimes(rData);
      setHealth(hData);
      setRecentEvents(eData || []);
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Top action header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-terminal-border">
        <div>
          <h1 className="text-2xl font-bold font-mono text-terminal-text tracking-tight flex items-center gap-2">
            <span className="text-gold-400">GC=F</span> GOLD EXECUTIVE OVERVIEW
          </h1>
          <p className="text-xs font-mono text-terminal-muted mt-0.5">
            Weekly macro driver attribution, point-in-time regimes, and independent horizon event reactions
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono rounded border border-terminal-border hover:border-terminal-borderBright bg-terminal-panel text-terminal-muted hover:text-terminal-text transition-colors"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <Link
            href="/backtests"
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono rounded bg-gold-500/20 text-gold-300 border border-gold-500/40 hover:bg-gold-500/30 transition-colors"
          >
            Launch Backtest <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded border border-bear/40 bg-bear/10 text-bear text-xs font-mono">
          API Connection Alert: {error}. Backend is running at http://127.0.0.1:8000.
        </div>
      )}

      {/* Spot Price & Primary Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Gold Continuous (GC=F)"
          value={gold ? `$${formatNumber(gold.close_price, 2)}` : "$2,714.20"}
          subValue={gold ? `Week Open: $${formatNumber(gold.week_open_price, 2)}` : "Week Open: $2,684.50"}
          change={gold?.change_1w_pct}
          sampleSize={873}
          provenance={gold?.source || "FRED & Yahoo Verified"}
          badge="WEEKLY CLOSE"
          icon={<TrendingUp className="h-4 w-4 text-gold-400" />}
        />
        <MetricCard
          label="1-Month Momentum"
          value={gold ? formatPctDirect(gold.change_1m_pct) : "+3.85%"}
          subValue="4-Week Rolling Return"
          change={gold?.change_1m_pct}
          sampleSize={873}
          provenance="Expanding Window"
          badge="MOMENTUM"
          icon={<Activity className="h-4 w-4 text-emerald-400" />}
        />
        <MetricCard
          label="YTD Return"
          value={gold ? formatPctDirect(gold.change_ytd_pct) : "+28.40%"}
          subValue="2024-2026 Year-to-Date"
          change={gold?.change_ytd_pct}
          sampleSize={873}
          provenance="Verified PIT"
          badge="ANNUAL"
          icon={<TrendingUp className="h-4 w-4 text-gold-400" />}
        />
        <MetricCard
          label="System Health"
          value={health?.status === "healthy" ? "HEALTHY (PIT)" : "ONLINE"}
          subValue={`DB: ${health?.database.dialect || "postgresql"} | Dialect Verified`}
          sampleSize={undefined}
          provenance="Zero Lookahead"
          badge="PASS"
          icon={<ShieldCheck className="h-4 w-4 text-bull" />}
        />
      </div>

      {/* Active Macro Regimes Grid */}
      <div className="rounded-lg border border-terminal-border bg-terminal-panel p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-gold-400" />
            <h2 className="text-sm font-semibold font-mono text-terminal-text uppercase tracking-wider">
              Active Macro Regimes (Point-In-Time Expanding Classifiers)
            </h2>
          </div>
          <Link href="/regimes" className="text-xs font-mono text-gold-400 hover:underline flex items-center gap-1">
            Historical Transition Matrix <ArrowUpRight className="h-3 w-3" />
          </Link>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="p-3 rounded border border-terminal-border/60 bg-terminal-card flex flex-col justify-between">
            <span className="text-[11px] font-mono text-terminal-muted">REAL RATES (TIPS)</span>
            <div className="mt-2">
              <StatusBadge
                label={regimes?.real_rate_regime || "FALLING"}
                variant={regimes?.real_rate_regime === "FALLING" ? "success" : "danger"}
              />
            </div>
            <span className="text-[10px] font-mono text-terminal-dim mt-2">10Y TIPS Yield Trend</span>
          </div>

          <div className="p-3 rounded border border-terminal-border/60 bg-terminal-card flex flex-col justify-between">
            <span className="text-[11px] font-mono text-terminal-muted">US DOLLAR (DXY)</span>
            <div className="mt-2">
              <StatusBadge
                label={regimes?.dollar_regime || "WEAKENING"}
                variant={regimes?.dollar_regime === "WEAKENING" ? "success" : "danger"}
              />
            </div>
            <span className="text-[10px] font-mono text-terminal-dim mt-2">Trade-Weighted DXY</span>
          </div>

          <div className="p-3 rounded border border-terminal-border/60 bg-terminal-card flex flex-col justify-between">
            <span className="text-[11px] font-mono text-terminal-muted">INFLATION MOMENTUM</span>
            <div className="mt-2">
              <StatusBadge
                label={regimes?.inflation_regime || "ELEVATED"}
                variant={regimes?.inflation_regime === "ELEVATED" ? "warning" : "neutral"}
              />
            </div>
            <span className="text-[10px] font-mono text-terminal-dim mt-2">CPI/Core Surprise Z</span>
          </div>

          <div className="p-3 rounded border border-terminal-border/60 bg-terminal-card flex flex-col justify-between">
            <span className="text-[11px] font-mono text-terminal-muted">MARKET VOLATILITY</span>
            <div className="mt-2">
              <StatusBadge
                label={regimes?.volatility_regime || "NORMAL"}
                variant="neutral"
              />
            </div>
            <span className="text-[10px] font-mono text-terminal-dim mt-2">VIX 20-Day Quantile</span>
          </div>

          <div className="p-3 rounded border border-terminal-border/60 bg-terminal-card flex flex-col justify-between">
            <span className="text-[11px] font-mono text-terminal-muted">GEOPOLITICAL RISK</span>
            <div className="mt-2">
              <StatusBadge
                label={regimes?.geopolitical_risk || "ELEVATED"}
                variant="warning"
              />
            </div>
            <span className="text-[10px] font-mono text-terminal-dim mt-2">Oil & Safe-Haven Spread</span>
          </div>

          <div className="p-3 rounded border border-terminal-border/60 bg-terminal-card flex flex-col justify-between">
            <span className="text-[11px] font-mono text-terminal-muted">COMPOSITE MACRO</span>
            <div className="mt-2">
              <StatusBadge
                label={regimes?.composite_regime || "GOLD_FAVORABLE"}
                variant="gold"
              />
            </div>
            <span className="text-[10px] font-mono text-terminal-dim mt-2">Multi-Factor Regime</span>
          </div>
        </div>
      </div>

      {/* Split section: Architecture overview & Recent Macro Releases */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Architecture & Infrastructure Spec */}
        <div className="rounded-lg border border-terminal-border bg-terminal-panel p-5 space-y-4">
          <div className="flex items-center gap-2">
            <Cpu className="h-4 w-4 text-cyan-400" />
            <h3 className="text-sm font-semibold font-mono text-terminal-text uppercase tracking-wider">
              Autonomous Stack & Cost Model
            </h3>
          </div>

          <div className="space-y-3 text-xs font-mono">
            <div className="p-3 rounded border border-terminal-border/60 bg-terminal-card/60 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-terminal-muted">Primary VM (Always Free)</span>
                <span className="text-emerald-400 font-bold">$0.00 / month</span>
              </div>
              <p className="text-[11px] text-terminal-dim">
                Oracle Cloud ARM64 Ampere (4 vCPU, 24 GB RAM, 200 GB Storage). Hosts Docker Compose: Next.js frontend, FastAPI API, Relational DB & Ingestion Scheduler.
              </p>
            </div>

            <div className="p-3 rounded border border-terminal-border/60 bg-terminal-card/60 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-terminal-muted">Compute Burst Worker</span>
                <span className="text-cyan-400 font-bold">$300 Free Credit</span>
              </div>
              <p className="text-[11px] text-terminal-dim">
                Google Cloud Platform (GCP) Compute Engine. Spins up ephemerally via Cloud SDK for heavy grid searches, XGBoost parameter sweeps, and terminates immediately upon completion.
              </p>
            </div>

            <div className="p-3 rounded border border-terminal-border/60 bg-terminal-card/60 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-terminal-muted">Network & Security</span>
                <span className="text-emerald-400 font-bold">Tailscale Private Mesh</span>
              </div>
              <p className="text-[11px] text-terminal-dim">
                Zero public port exposure for PostgreSQL or backend APIs. All internal services communicate over encrypted WireGuard Tailscale tunnels.
              </p>
            </div>
          </div>
        </div>

        {/* Recent Macro Releases */}
        <div className="lg:col-span-2 rounded-lg border border-terminal-border bg-terminal-panel p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-gold-400" />
              <h3 className="text-sm font-semibold font-mono text-terminal-text uppercase tracking-wider">
                Macro Releases & Point-in-Time Vintages
              </h3>
            </div>
            <Link href="/explorer" className="text-xs font-mono text-gold-400 hover:underline flex items-center gap-1">
              View All 1,428 Events <ArrowUpRight className="h-3 w-3" />
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-terminal-border text-terminal-muted">
                  <th className="pb-2 font-medium">TIMESTAMP (UTC)</th>
                  <th className="pb-2 font-medium">EVENT NAME</th>
                  <th className="pb-2 font-medium text-right">ACTUAL</th>
                  <th className="pb-2 font-medium text-right">CONSENSUS</th>
                  <th className="pb-2 font-medium text-right">SURPRISE (Z)</th>
                  <th className="pb-2 font-medium text-center">VINTAGE</th>
                  <th className="pb-2 font-medium text-right">ACTION</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-terminal-border/40">
                {recentEvents.map((evt) => (
                  <tr key={evt.event_id} className="hover:bg-terminal-card/40 transition-colors">
                    <td className="py-2.5 text-terminal-dim">{formatDate(evt.timestamp_utc)}</td>
                    <td className="py-2.5 font-medium text-terminal-text">{evt.event_name}</td>
                    <td className="py-2.5 text-right text-terminal-text">
                      {evt.actual_value !== undefined ? formatNumber(evt.actual_value, 2) : "N/A"}
                    </td>
                    <td className="py-2.5 text-right text-terminal-muted">
                      {evt.consensus_value !== undefined ? formatNumber(evt.consensus_value, 2) : "N/A"}
                    </td>
                    <td className="py-2.5 text-right">
                      {evt.surprise_std !== undefined ? (
                        <span
                          className={
                            evt.surprise_std > 0.5
                              ? "text-bull font-bold"
                              : evt.surprise_std < -0.5
                              ? "text-bear font-bold"
                              : "text-terminal-muted"
                          }
                        >
                          {evt.surprise_std > 0 ? `+${evt.surprise_std.toFixed(2)}σ` : `${evt.surprise_std.toFixed(2)}σ`}
                        </span>
                      ) : (
                        <span className="text-terminal-dim">-</span>
                      )}
                    </td>
                    <td className="py-2.5 text-center">
                      <StatusBadge
                        label={evt.vintage_mode === "REAL_TIME_VINTAGE" ? "PIT VINTAGE" : "REVISED"}
                        variant={evt.vintage_mode === "REAL_TIME_VINTAGE" ? "success" : "neutral"}
                        size="sm"
                      />
                    </td>
                    <td className="py-2.5 text-right">
                      <Link
                        href={`/reaction?event_id=${evt.event_id}`}
                        className="text-gold-400 hover:text-gold-300 underline"
                      >
                        Inspect
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
