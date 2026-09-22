"use client";

import { useState } from "react";
import { api, BacktestResult } from "@/lib/api";
import { MetricCard } from "@/components/MetricCard";
import { StatusBadge } from "@/components/StatusBadge";
import { formatNumber, formatPercent, formatDate } from "@/lib/utils";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  AreaChart,
  Area,
} from "recharts";
import {
  LineChart as ChartIcon,
  Play,
  RotateCcw,
  CheckCircle2,
  Sliders,
  DollarSign,
  TrendingDown,
} from "lucide-react";

export default function BacktestsPage() {
  const [strategy, setStrategy] = useState<string>("macro_regime_trend");
  const [startDate, setStartDate] = useState<string>("2018-01-01");
  const [endDate, setEndDate] = useState<string>("2024-12-31");
  const [initialCapital, setInitialCapital] = useState<number>(100000);
  const [slippageBps, setSlippageBps] = useState<number>(5.0);
  const [commissionPerTrade, setCommissionPerTrade] = useState<number>(2.5);

  const [loading, setLoading] = useState<boolean>(false);
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);
  const [results, setResults] = useState<BacktestResult | null>(null);
  const [statusMessage, setStatusMessage] = useState<string>("");

  const handleLaunchBacktest = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setStatusMessage("Submitting backtest to background worker...");
    setResults(null);

    try {
      const launch = await api.runBacktest({
        strategy_name: strategy,
        start_date: startDate,
        end_date: endDate,
        initial_capital: initialCapital,
        slippage_bps: slippageBps,
        commission_per_trade: commissionPerTrade,
      });

      setCurrentRunId(launch.run_id);
      setStatusMessage("Running point-in-time simulation...");

      // Poll until completed
      let attempts = 0;
      const pollInterval = setInterval(async () => {
        attempts++;
        try {
          const status = await api.getBacktestStatus(launch.run_id);
          if (status.status === "completed") {
            clearInterval(pollInterval);
            const res = await api.getBacktestResult(launch.run_id);
            setResults(res);
            setLoading(false);
            setStatusMessage("Backtest completed successfully.");
          } else if (status.status === "failed") {
            clearInterval(pollInterval);
            setLoading(false);
            setStatusMessage("Backtest simulation failed.");
          } else if (attempts > 30) {
            clearInterval(pollInterval);
            setLoading(false);
            setStatusMessage("Backtest timed out.");
          }
        } catch (err) {
          clearInterval(pollInterval);
          setLoading(false);
          setStatusMessage("Error polling status.");
        }
      }, 1000);
    } catch (err: any) {
      setLoading(false);
      setStatusMessage(`Failed: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-terminal-border">
        <div>
          <h1 className="text-2xl font-bold font-mono text-terminal-text tracking-tight flex items-center gap-2">
            <ChartIcon className="h-6 w-6 text-gold-400" />
            POINT-IN-TIME BACKTEST LAB
          </h1>
          <p className="text-xs font-mono text-terminal-muted mt-0.5">
            Friday-to-Friday rebalanced simulation with realistic slippage, commission, and zero lookahead
          </p>
        </div>
      </div>

      {/* Backtest Parameter Configuration */}
      <form
        onSubmit={handleLaunchBacktest}
        className="rounded-lg border border-terminal-border bg-terminal-panel p-5 space-y-4"
      >
        <div className="flex items-center gap-2 text-xs font-mono text-gold-400 font-semibold uppercase">
          <Sliders className="h-4 w-4" /> Simulation Parameters
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 text-xs font-mono">
          <div>
            <label className="block text-terminal-muted mb-1 font-medium">STRATEGY</label>
            <select
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
              className="w-full px-3 py-1.5 rounded border border-terminal-border bg-terminal-card text-terminal-text focus:outline-none focus:border-gold-500"
            >
              <option value="macro_regime_trend">Macro Regime Trend</option>
              <option value="tips_real_rate_momentum">TIPS Real Rate Momentum</option>
              <option value="event_reversal_filter">Event Shock + Reversal</option>
              <option value="buy_and_hold">Gold Benchmark (B&H)</option>
            </select>
          </div>

          <div>
            <label className="block text-terminal-muted mb-1 font-medium">START DATE</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-1.5 rounded border border-terminal-border bg-terminal-card text-terminal-text focus:outline-none focus:border-gold-500"
            />
          </div>

          <div>
            <label className="block text-terminal-muted mb-1 font-medium">END DATE</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-1.5 rounded border border-terminal-border bg-terminal-card text-terminal-text focus:outline-none focus:border-gold-500"
            />
          </div>

          <div>
            <label className="block text-terminal-muted mb-1 font-medium">INITIAL CAPITAL ($)</label>
            <input
              type="number"
              value={initialCapital}
              onChange={(e) => setInitialCapital(Number(e.target.value))}
              className="w-full px-3 py-1.5 rounded border border-terminal-border bg-terminal-card text-terminal-text focus:outline-none focus:border-gold-500"
            />
          </div>

          <div>
            <label className="block text-terminal-muted mb-1 font-medium">SLIPPAGE (BPS)</label>
            <input
              type="number"
              step="0.5"
              value={slippageBps}
              onChange={(e) => setSlippageBps(Number(e.target.value))}
              className="w-full px-3 py-1.5 rounded border border-terminal-border bg-terminal-card text-terminal-text focus:outline-none focus:border-gold-500"
            />
          </div>

          <div>
            <label className="block text-terminal-muted mb-1 font-medium">COMMISSION ($/TRADE)</label>
            <input
              type="number"
              step="0.5"
              value={commissionPerTrade}
              onChange={(e) => setCommissionPerTrade(Number(e.target.value))}
              className="w-full px-3 py-1.5 rounded border border-terminal-border bg-terminal-card text-terminal-text focus:outline-none focus:border-gold-500"
            />
          </div>
        </div>

        <div className="flex items-center justify-between pt-3 border-t border-terminal-border/60">
          <span className="text-xs font-mono text-terminal-dim">
            Execution Invariant: Positions enter/exit strictly on Friday weekly close prices
          </span>
          <button
            type="submit"
            disabled={loading}
            className="flex items-center gap-2 px-5 py-2 rounded bg-gold-500 hover:bg-gold-400 text-black font-semibold text-xs font-mono transition-colors shadow-sm disabled:opacity-50"
          >
            <Play className="h-4 w-4 fill-black" />
            {loading ? "Running Backtest..." : "Run Backtest Simulation"}
          </button>
        </div>
      </form>

      {statusMessage && (
        <div className="p-3 rounded border border-terminal-border bg-terminal-panel text-xs font-mono text-gold-400">
          {statusMessage}
        </div>
      )}

      {/* Backtest Results */}
      {results && (
        <div className="space-y-6">
          {/* Key Portfolio Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
            <div className="p-3 rounded border border-terminal-border bg-terminal-panel">
              <span className="text-[10px] font-mono text-terminal-muted uppercase block">ANNUALIZED</span>
              <span className="text-base font-bold font-mono text-bull">
                {formatPercent(results.annualized_return)}
              </span>
            </div>

            <div className="p-3 rounded border border-terminal-border bg-terminal-panel">
              <span className="text-[10px] font-mono text-terminal-muted uppercase block">SHARPE RATIO</span>
              <span className="text-base font-bold font-mono text-terminal-text">
                {formatNumber(results.sharpe_ratio, 2)}
              </span>
            </div>

            <div className="p-3 rounded border border-terminal-border bg-terminal-panel">
              <span className="text-[10px] font-mono text-terminal-muted uppercase block">SORTINO RATIO</span>
              <span className="text-base font-bold font-mono text-terminal-text">
                {formatNumber(results.sortino_ratio, 2)}
              </span>
            </div>

            <div className="p-3 rounded border border-terminal-border bg-terminal-panel">
              <span className="text-[10px] font-mono text-terminal-muted uppercase block">MAX DRAWDOWN</span>
              <span className="text-base font-bold font-mono text-bear">
                {formatPercent(results.max_drawdown)}
              </span>
            </div>

            <div className="p-3 rounded border border-terminal-border bg-terminal-panel">
              <span className="text-[10px] font-mono text-terminal-muted uppercase block">WIN RATE</span>
              <span className="text-base font-bold font-mono text-gold-400">
                {formatPercent(results.win_rate)}
              </span>
            </div>

            <div className="p-3 rounded border border-terminal-border bg-terminal-panel">
              <span className="text-[10px] font-mono text-terminal-muted uppercase block">TOTAL TRADES</span>
              <span className="text-base font-bold font-mono text-terminal-text">
                {results.total_trades}
              </span>
            </div>

            <div className="p-3 rounded border border-terminal-border bg-terminal-panel">
              <span className="text-[10px] font-mono text-terminal-muted uppercase block">PROFIT FACTOR</span>
              <span className="text-base font-bold font-mono text-terminal-text">
                {formatNumber(results.profit_factor, 2)}
              </span>
            </div>

            <div className="p-3 rounded border border-terminal-border bg-terminal-panel">
              <span className="text-[10px] font-mono text-terminal-muted uppercase block">CALMAR RATIO</span>
              <span className="text-base font-bold font-mono text-terminal-text">
                {formatNumber(results.calmar_ratio, 2)}
              </span>
            </div>
          </div>

          {/* Equity Curve Chart */}
          <div className="rounded-lg border border-terminal-border bg-terminal-panel p-5 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold font-mono text-terminal-text uppercase tracking-wider">
                Cumulative Portfolio Value vs Gold Benchmark ($)
              </span>
              <span className="text-xs font-mono text-terminal-dim">
                Initial: ${formatNumber(initialCapital, 0)}
              </span>
            </div>

            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={results.equity_curve}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 10, fill: "#94a3b8" }} />
                  <YAxis
                    domain={["auto", "auto"]}
                    stroke="#64748b"
                    tick={{ fontSize: 10, fill: "#94a3b8" }}
                    tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0d131f",
                      borderColor: "#334155",
                      fontSize: "12px",
                      fontFamily: "monospace",
                    }}
                    formatter={(val: any) => [`$${formatNumber(val, 2)}`, ""]}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="portfolio_value"
                    name="Strategy (Net of Fees)"
                    stroke="#10b981"
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="benchmark_value"
                    name="Gold Buy & Hold"
                    stroke="#f59e0b"
                    strokeWidth={1.5}
                    strokeDasharray="4 4"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Drawdown Curve */}
          <div className="rounded-lg border border-terminal-border bg-terminal-panel p-5 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold font-mono text-terminal-text uppercase tracking-wider flex items-center gap-1.5 text-bear">
                <TrendingDown className="h-4 w-4" /> Strategy Drawdown (%)
              </span>
              <span className="text-xs font-mono text-terminal-dim">
                Max DD: {formatPercent(results.max_drawdown)}
              </span>
            </div>

            <div className="h-40 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={results.equity_curve}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 10, fill: "#94a3b8" }} />
                  <YAxis
                    domain={["auto", 0]}
                    stroke="#64748b"
                    tick={{ fontSize: 10, fill: "#94a3b8" }}
                    tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0d131f",
                      borderColor: "#334155",
                      fontSize: "12px",
                      fontFamily: "monospace",
                    }}
                    formatter={(val: any) => [formatPercent(val), "Drawdown"]}
                  />
                  <Area
                    type="monotone"
                    dataKey="drawdown_pct"
                    name="Drawdown"
                    stroke="#f43f5e"
                    fill="#f43f5e"
                    fillOpacity={0.2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
