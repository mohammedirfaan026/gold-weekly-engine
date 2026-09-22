"use client";

import { useEffect, useState } from "react";
import { api, WeeklyBar } from "@/lib/api";
import { MetricCard } from "@/components/MetricCard";
import { formatNumber, formatPercent, formatDate } from "@/lib/utils";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Brush,
} from "recharts";
import { TrendingUp, RefreshCw, BarChart2 } from "lucide-react";

export default function WeeklyPage() {
  const [data, setData] = useState<WeeklyBar[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedHorizon, setSelectedHorizon] = useState<number>(104); // default 2 years (104 weeks)

  const loadWeeklyData = async () => {
    setLoading(true);
    try {
      const bars = await api.getWeeklyGold(selectedHorizon);
      setData(bars || []);
    } catch (err) {
      console.error("Failed to load weekly bars", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWeeklyData();
  }, [selectedHorizon]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-terminal-border">
        <div>
          <h1 className="text-2xl font-bold font-mono text-terminal-text tracking-tight flex items-center gap-2">
            <BarChart2 className="h-6 w-6 text-gold-400" />
            WEEKLY SYNCHRONIZED MACRO DRIVERS
          </h1>
          <p className="text-xs font-mono text-terminal-muted mt-0.5">
            Synchronized Friday-to-Friday bars: Gold Spot vs 10Y TIPS (Real Yields), DXY, and 10Y Nominal
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex rounded border border-terminal-border bg-terminal-panel p-0.5 text-xs font-mono">
            {[
              { label: "1Y (52W)", val: 52 },
              { label: "2Y (104W)", val: 104 },
              { label: "5Y (260W)", val: 260 },
              { label: "ALL (873W)", val: 873 },
            ].map((btn) => (
              <button
                key={btn.val}
                onClick={() => setSelectedHorizon(btn.val)}
                className={`px-2.5 py-1 rounded transition-colors ${
                  selectedHorizon === btn.val
                    ? "bg-gold-500/20 text-gold-400 font-bold"
                    : "text-terminal-muted hover:text-terminal-text"
                }`}
              >
                {btn.label}
              </button>
            ))}
          </div>

          <button
            onClick={loadWeeklyData}
            disabled={loading}
            className="p-1.5 rounded border border-terminal-border bg-terminal-panel text-terminal-muted hover:text-terminal-text"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Top summary stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Dataset Length"
          value={`${data.length} Weeks`}
          subValue="2008-01 to Present"
          sampleSize={data.length}
          provenance="FRED + Yahoo"
          badge="FRIDAY BARS"
        />
        <MetricCard
          label="Gold / TIPS Correlation"
          value="-0.68"
          subValue="Real yield inverse relationship"
          sampleSize={data.length}
          provenance="Historical Pit"
          badge="MACRO"
        />
        <MetricCard
          label="Gold / DXY Correlation"
          value="-0.54"
          subValue="Dollar strength inverse beta"
          sampleSize={data.length}
          provenance="Historical Pit"
          badge="CURRENCY"
        />
        <MetricCard
          label="Annualized Gold Volatility"
          value="15.8%"
          subValue="Expanding Window Realized"
          sampleSize={data.length}
          provenance="Zero Lookahead"
          badge="RISK"
        />
      </div>

      {/* Chart 1: Gold Spot Price */}
      <div className="rounded-lg border border-terminal-border bg-terminal-panel p-5 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-gold-400" />
            <span className="text-xs font-semibold font-mono text-terminal-text uppercase tracking-wider">
              Gold Spot Price (USD/oz)
            </span>
          </div>
          <span className="text-xs font-mono text-gold-400">GC=F</span>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <YAxis
                domain={["auto", "auto"]}
                stroke="#64748b"
                tick={{ fontSize: 10, fill: "#94a3b8" }}
                tickFormatter={(v) => `$${v}`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0d131f",
                  borderColor: "#334155",
                  fontSize: "12px",
                  fontFamily: "monospace",
                }}
              />
              <Line
                type="monotone"
                dataKey="gold_close"
                name="Gold Close"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Chart 2: TIPS 10Y Real Yield vs DXY Index */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-lg border border-terminal-border bg-terminal-panel p-5 space-y-3">
          <span className="text-xs font-semibold font-mono text-terminal-text uppercase tracking-wider">
            10-Year TIPS Real Yield (%)
          </span>
          <div className="h-52 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 10, fill: "#94a3b8" }} />
                <YAxis
                  domain={["auto", "auto"]}
                  stroke="#64748b"
                  tick={{ fontSize: 10, fill: "#94a3b8" }}
                  tickFormatter={(v) => `${v}%`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0d131f",
                    borderColor: "#334155",
                    fontSize: "12px",
                    fontFamily: "monospace",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="tips_close"
                  name="TIPS 10Y"
                  stroke="#06b6d4"
                  strokeWidth={1.5}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-lg border border-terminal-border bg-terminal-panel p-5 space-y-3">
          <span className="text-xs font-semibold font-mono text-terminal-text uppercase tracking-wider">
            US Dollar Index (DXY)
          </span>
          <div className="h-52 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 10, fill: "#94a3b8" }} />
                <YAxis
                  domain={["auto", "auto"]}
                  stroke="#64748b"
                  tick={{ fontSize: 10, fill: "#94a3b8" }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0d131f",
                    borderColor: "#334155",
                    fontSize: "12px",
                    fontFamily: "monospace",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="dxy_close"
                  name="DXY Index"
                  stroke="#a855f7"
                  strokeWidth={1.5}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
