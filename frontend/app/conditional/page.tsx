"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { MetricCard } from "@/components/MetricCard";
import { StatusBadge } from "@/components/StatusBadge";
import { formatNumber, formatPercent, formatDate } from "@/lib/utils";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
  ReferenceLine,
} from "recharts";
import { Filter, Search, AlertTriangle, CheckCircle2, ChevronRight } from "lucide-react";

export default function ConditionalPage() {
  const [eventType, setEventType] = useState<string>("CPI");
  const [surpriseDir, setSurpriseDir] = useState<string>("POSITIVE");
  const [realRateRegime, setRealRateRegime] = useState<string>("ALL");
  const [dollarRegime, setDollarRegime] = useState<string>("ALL");
  const [loading, setLoading] = useState<boolean>(false);
  const [results, setResults] = useState<any>(null);

  const handleRunQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload: any = {
        event_type: eventType,
      };
      if (surpriseDir === "POSITIVE") payload.min_surprise = 0.2;
      if (surpriseDir === "NEGATIVE") payload.max_surprise = -0.2;
      if (realRateRegime !== "ALL") payload.real_rate_regime = realRateRegime;
      if (dollarRegime !== "ALL") payload.dollar_regime = dollarRegime;

      const res = await api.queryConditional(payload);
      setResults(res);
    } catch (err) {
      console.error("Conditional query error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-terminal-border">
        <div>
          <h1 className="text-2xl font-bold font-mono text-terminal-text tracking-tight flex items-center gap-2">
            <Filter className="h-6 w-6 text-gold-400" />
            CONDITIONAL MACRO REACTION ENGINE
          </h1>
          <p className="text-xs font-mono text-terminal-muted mt-0.5">
            Evaluate empirical probability distributions conditioned on surprise magnitude and regime states
          </p>
        </div>
      </div>

      {/* Query Filter Controls */}
      <form
        onSubmit={handleRunQuery}
        className="rounded-lg border border-terminal-border bg-terminal-panel p-5 space-y-4"
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
          <div>
            <label className="block text-terminal-muted mb-1.5 font-medium">MACRO EVENT TYPE</label>
            <select
              value={eventType}
              onChange={(e) => setEventType(e.target.value)}
              className="w-full px-3 py-2 rounded border border-terminal-border bg-terminal-card text-terminal-text focus:outline-none focus:border-gold-500"
            >
              <option value="CPI">CPI (Inflation)</option>
              <option value="NFP">NFP (Non-Farm Payrolls)</option>
              <option value="FOMC">FOMC Rate Decision</option>
              <option value="PMI">ISM / PMI Manufacturing</option>
              <option value="GDP">GDP Growth</option>
            </select>
          </div>

          <div>
            <label className="block text-terminal-muted mb-1.5 font-medium">SURPRISE DIRECTION</label>
            <select
              value={surpriseDir}
              onChange={(e) => setSurpriseDir(e.target.value)}
              className="w-full px-3 py-2 rounded border border-terminal-border bg-terminal-card text-terminal-text focus:outline-none focus:border-gold-500"
            >
              <option value="POSITIVE">Positive Surprise (&gt; +0.20σ)</option>
              <option value="NEGATIVE">Negative Surprise (&lt; -0.20σ)</option>
              <option value="ALL">Any Surprise (All)</option>
            </select>
          </div>

          <div>
            <label className="block text-terminal-muted mb-1.5 font-medium">REAL RATE REGIME</label>
            <select
              value={realRateRegime}
              onChange={(e) => setRealRateRegime(e.target.value)}
              className="w-full px-3 py-2 rounded border border-terminal-border bg-terminal-card text-terminal-text focus:outline-none focus:border-gold-500"
            >
              <option value="ALL">All Regimes</option>
              <option value="FALLING">Falling Real Rates (Bullish Gold)</option>
              <option value="RISING">Rising Real Rates (Bearish Gold)</option>
              <option value="NEUTRAL">Neutral / Stable Rates</option>
            </select>
          </div>

          <div>
            <label className="block text-terminal-muted mb-1.5 font-medium">DOLLAR REGIME (DXY)</label>
            <select
              value={dollarRegime}
              onChange={(e) => setDollarRegime(e.target.value)}
              className="w-full px-3 py-2 rounded border border-terminal-border bg-terminal-card text-terminal-text focus:outline-none focus:border-gold-500"
            >
              <option value="ALL">All Regimes</option>
              <option value="WEAKENING">Weakening Dollar</option>
              <option value="STRENGTHENING">Strengthening Dollar</option>
            </select>
          </div>
        </div>

        <div className="flex items-center justify-between pt-3 border-t border-terminal-border/60">
          <span className="text-xs font-mono text-terminal-dim">
            Point-in-Time Verified: Filters applied strictly using historical expanding window
          </span>
          <button
            type="submit"
            disabled={loading}
            className="flex items-center gap-2 px-5 py-2 rounded bg-gold-500 hover:bg-gold-400 text-black font-semibold text-xs font-mono transition-colors shadow-sm"
          >
            <Search className="h-4 w-4" />
            {loading ? "Querying..." : "Execute Conditional Study"}
          </button>
        </div>
      </form>

      {/* Query Results */}
      {results && (
        <div className="space-y-6">
          {/* Sample Size Caution Alert if N < 20 */}
          {results.sample_size < 20 && (
            <div className="p-3.5 rounded border border-amber-500/40 bg-amber-500/10 text-amber-300 text-xs font-mono flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 flex-shrink-0 text-amber-400" />
              <span>
                <strong>Small Sample Warning:</strong> This conditional query returned N={results.sample_size} events. Statistical significance may be low. Treat empirical probabilities with caution.
              </span>
            </div>
          )}

          {/* Key Empirical Metrics */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              label="Sample Size"
              value={`N = ${results.sample_size}`}
              subValue="Matched historical occurrences"
              sampleSize={results.sample_size}
              provenance="Database Verified"
              badge="SAMPLE"
            />
            <MetricCard
              label="Win Rate (Next Fri > 0)"
              value={formatPercent(results.win_rate)}
              subValue={`${results.win_rate >= 0.5 ? "Bullish" : "Bearish"} Skew`}
              change={results.win_rate ? (results.win_rate - 0.5) * 100 : 0}
              sampleSize={results.sample_size}
              provenance="Empirical"
              badge="PROBABILITY"
            />
            <MetricCard
              label="Median Return"
              value={formatPercent(results.median_return)}
              subValue={`Mean: ${formatPercent(results.mean_return)}`}
              sampleSize={results.sample_size}
              provenance="Next Friday"
              badge="RETURN"
            />
            <MetricCard
              label="Interquartile Range"
              value={`${formatPercent(results.p25)} to ${formatPercent(results.p75)}`}
              subValue={`Std Dev: ${formatPercent(results.std_dev)}`}
              sampleSize={results.sample_size}
              provenance="Dispersion"
              badge="RISK"
            />
          </div>

          {/* Matching Events Table */}
          {results.matching_events && results.matching_events.length > 0 && (
            <div className="rounded-lg border border-terminal-border bg-terminal-panel p-5 space-y-4">
              <h3 className="text-sm font-semibold font-mono text-terminal-text uppercase tracking-wider">
                Matched Releases (Chronological)
              </h3>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead>
                    <tr className="border-b border-terminal-border text-terminal-muted">
                      <th className="pb-2">DATE (UTC)</th>
                      <th className="pb-2">EVENT</th>
                      <th className="pb-2 text-right">ACTUAL</th>
                      <th className="pb-2 text-right">CONSENSUS</th>
                      <th className="pb-2 text-right">SURPRISE (Z)</th>
                      <th className="pb-2 text-right">NEXT FRI RETURN</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-terminal-border/40">
                    {results.matching_events.map((evt: any, i: number) => (
                      <tr key={i} className="hover:bg-terminal-card/40">
                        <td className="py-2.5 text-terminal-dim">{formatDate(evt.timestamp_utc)}</td>
                        <td className="py-2.5 text-terminal-text">{evt.event_name}</td>
                        <td className="py-2.5 text-right text-terminal-text">{formatNumber(evt.actual_value, 2)}</td>
                        <td className="py-2.5 text-right text-terminal-muted">{formatNumber(evt.consensus_value, 2)}</td>
                        <td className="py-2.5 text-right">
                          <span className={evt.surprise_std > 0 ? "text-bull" : "text-bear"}>
                            {evt.surprise_std > 0 ? `+${evt.surprise_std.toFixed(2)}σ` : `${evt.surprise_std.toFixed(2)}σ`}
                          </span>
                        </td>
                        <td className="py-2.5 text-right">
                          <span className={evt.next_friday_return >= 0 ? "text-bull font-bold" : "text-bear font-bold"}>
                            {formatPercent(evt.next_friday_return)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
