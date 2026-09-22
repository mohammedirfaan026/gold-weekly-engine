"use client";

import { useEffect, useState } from "react";
import { api, RegimeState } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { formatDate } from "@/lib/utils";
import {
  Layers,
  BookOpen,
  History,
  TrendingDown,
  TrendingUp,
  RefreshCw,
  GitCommit,
} from "lucide-react";

export default function RegimesPage() {
  const [current, setCurrent] = useState<RegimeState | null>(null);
  const [history, setHistory] = useState<RegimeState[]>([]);
  const [definitions, setDefinitions] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const [cData, hData, dData] = await Promise.all([
        api.getCurrentRegimes().catch(() => null),
        api.getRegimeHistory(30).catch(() => []),
        api.getRegimeDefinitions().catch(() => null),
      ]);
      setCurrent(cData);
      setHistory(hData || []);
      setDefinitions(dData);
    } catch (err) {
      console.error("Failed to load regimes data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-terminal-border">
        <div>
          <h1 className="text-2xl font-bold font-mono text-terminal-text tracking-tight flex items-center gap-2">
            <Layers className="h-6 w-6 text-gold-400" />
            POINT-IN-TIME REGIME ENGINE
          </h1>
          <p className="text-xs font-mono text-terminal-muted mt-0.5">
            Classifiers using strictly expanding backward-only quantiles with zero lookahead
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded border border-terminal-border bg-terminal-panel text-xs font-mono text-terminal-muted hover:text-terminal-text"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh
        </button>
      </div>

      {/* Active State Banner */}
      <div className="rounded-lg border border-terminal-border bg-terminal-panel p-5 space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono text-terminal-muted uppercase tracking-wider">
            Current Historical Classification (As of {formatDate(current?.timestamp)})
          </span>
          <span className="text-xs font-mono text-gold-400 font-semibold">
            Strict Expanding Window PIT
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-xs font-mono">
          <div className="p-3 rounded border border-terminal-border bg-terminal-card space-y-1">
            <span className="text-terminal-muted block text-[10px]">REAL RATES</span>
            <StatusBadge
              label={current?.real_rate_regime || "FALLING"}
              variant={current?.real_rate_regime === "FALLING" ? "success" : "danger"}
            />
            <span className="text-[10px] text-terminal-dim block pt-1">Bullish Gold Bias</span>
          </div>

          <div className="p-3 rounded border border-terminal-border bg-terminal-card space-y-1">
            <span className="text-terminal-muted block text-[10px]">US DOLLAR (DXY)</span>
            <StatusBadge
              label={current?.dollar_regime || "WEAKENING"}
              variant={current?.dollar_regime === "WEAKENING" ? "success" : "danger"}
            />
            <span className="text-[10px] text-terminal-dim block pt-1">Dollar Weakness</span>
          </div>

          <div className="p-3 rounded border border-terminal-border bg-terminal-card space-y-1">
            <span className="text-terminal-muted block text-[10px]">INFLATION</span>
            <StatusBadge
              label={current?.inflation_regime || "ELEVATED"}
              variant="warning"
            />
            <span className="text-[10px] text-terminal-dim block pt-1">CPI Momentum</span>
          </div>

          <div className="p-3 rounded border border-terminal-border bg-terminal-card space-y-1">
            <span className="text-terminal-muted block text-[10px]">VOLATILITY (VIX)</span>
            <StatusBadge
              label={current?.volatility_regime || "NORMAL"}
              variant="neutral"
            />
            <span className="text-[10px] text-terminal-dim block pt-1">20-Day Quantile</span>
          </div>

          <div className="p-3 rounded border border-terminal-border bg-terminal-card space-y-1">
            <span className="text-terminal-muted block text-[10px]">GEOPOLITICS</span>
            <StatusBadge
              label={current?.geopolitical_risk || "ELEVATED"}
              variant="warning"
            />
            <span className="text-[10px] text-terminal-dim block pt-1">Safe-Haven Demand</span>
          </div>

          <div className="p-3 rounded border border-gold-500/40 bg-gold-500/10 space-y-1">
            <span className="text-gold-400 block text-[10px]">COMPOSITE REGIME</span>
            <StatusBadge
              label={current?.composite_regime || "GOLD_FAVORABLE"}
              variant="gold"
            />
            <span className="text-[10px] text-gold-300 block pt-1">High Probability Up</span>
          </div>
        </div>
      </div>

      {/* Regime Definitions and Formula Documentation */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-lg border border-terminal-border bg-terminal-panel p-5 space-y-4">
          <div className="flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-gold-400" />
            <h3 className="text-sm font-semibold font-mono text-terminal-text uppercase tracking-wider">
              Mathematical Regime Definitions
            </h3>
          </div>

          <div className="space-y-3 text-xs font-mono">
            <div className="p-3 rounded border border-terminal-border/60 bg-terminal-card space-y-1">
              <span className="font-semibold text-terminal-text">1. Real Rate Regime (TIPS 10Y)</span>
              <p className="text-terminal-muted">
                Evaluates difference between current yield and 20-week rolling average:
                <code className="block mt-1 text-cyan-400 bg-terminal-bg p-1.5 rounded">
                  Yield_diff = TIPS_t - SMA_20(TIPS)
                </code>
                If Yield_diff &lt; -0.05%, classified as <strong>FALLING</strong> (Strong tailwind for Gold).
              </p>
            </div>

            <div className="p-3 rounded border border-terminal-border/60 bg-terminal-card space-y-1">
              <span className="font-semibold text-terminal-text">2. Dollar Regime (DXY 4-Week Delta)</span>
              <p className="text-terminal-muted">
                Classifies multi-week momentum of trade-weighted US Dollar:
                <code className="block mt-1 text-cyan-400 bg-terminal-bg p-1.5 rounded">
                  DXY_return_4w = (DXY_t / DXY_(t-4w)) - 1.0
                </code>
                If return &lt; -0.5%, classified as <strong>WEAKENING</strong>.
              </p>
            </div>

            <div className="p-3 rounded border border-terminal-border/60 bg-terminal-card space-y-1">
              <span className="font-semibold text-terminal-text">3. Volatility Quantiles (Zero Lookahead)</span>
              <p className="text-terminal-muted">
                Strictly uses backward-only expanding quantiles:
                <code className="block mt-1 text-cyan-400 bg-terminal-bg p-1.5 rounded">
                  q_low = series[:t].quantile(0.25), q_high = series[:t].quantile(0.75)
                </code>
                Eliminates future peak leakage during historical backtesting.
              </p>
            </div>
          </div>
        </div>

        {/* Historical Regime Transitions */}
        <div className="rounded-lg border border-terminal-border bg-terminal-panel p-5 space-y-4">
          <div className="flex items-center gap-2">
            <History className="h-4 w-4 text-emerald-400" />
            <h3 className="text-sm font-semibold font-mono text-terminal-text uppercase tracking-wider">
              Recent Regime Chronology
            </h3>
          </div>

          <div className="overflow-x-auto max-h-[350px] overflow-y-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="sticky top-0 bg-terminal-panel">
                <tr className="border-b border-terminal-border text-terminal-muted">
                  <th className="pb-2">DATE</th>
                  <th className="pb-2">REAL RATES</th>
                  <th className="pb-2">DOLLAR</th>
                  <th className="pb-2">INFLATION</th>
                  <th className="pb-2">COMPOSITE</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-terminal-border/40">
                {history.map((h, i) => (
                  <tr key={i} className="hover:bg-terminal-card/40">
                    <td className="py-2 text-terminal-dim">{formatDate(h.timestamp)}</td>
                    <td className="py-2">
                      <span className={h.real_rate_regime === "FALLING" ? "text-bull" : "text-bear"}>
                        {h.real_rate_regime}
                      </span>
                    </td>
                    <td className="py-2">
                      <span className={h.dollar_regime === "WEAKENING" ? "text-bull" : "text-bear"}>
                        {h.dollar_regime}
                      </span>
                    </td>
                    <td className="py-2 text-terminal-muted">{h.inflation_regime}</td>
                    <td className="py-2 font-bold text-gold-400">{h.composite_regime}</td>
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
