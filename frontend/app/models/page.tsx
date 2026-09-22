"use client";

import { useEffect, useState } from "react";
import { api, ModelMetric } from "@/lib/api";
import { MetricCard } from "@/components/MetricCard";
import { StatusBadge } from "@/components/StatusBadge";
import { formatNumber, formatPercent } from "@/lib/utils";
import { Cpu, Award, AlertCircle, RefreshCw, Layers } from "lucide-react";

export default function ModelsPage() {
  const [models, setModels] = useState<ModelMetric[]>([]);
  const [loading, setLoading] = useState(true);

  const loadModels = async () => {
    setLoading(true);
    try {
      const data = await api.getModelPerformance();
      setModels(data || []);
    } catch (err) {
      console.error("Failed to load model metrics", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadModels();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-terminal-border">
        <div>
          <h1 className="text-2xl font-bold font-mono text-terminal-text tracking-tight flex items-center gap-2">
            <Cpu className="h-6 w-6 text-gold-400" />
            MODEL BENCHMARKING & MANDATORY BASELINES
          </h1>
          <p className="text-xs font-mono text-terminal-muted mt-0.5">
            Every candidate model must beat 6 non-trivial naive baselines on out-of-sample Brier score & AUC-ROC
          </p>
        </div>

        <button
          onClick={loadModels}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded border border-terminal-border bg-terminal-panel text-xs font-mono text-terminal-muted hover:text-terminal-text"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh
        </button>
      </div>

      {/* Baseline Requirement Callout */}
      <div className="p-4 rounded-lg border border-gold-500/30 bg-gold-500/10 text-xs font-mono space-y-2">
        <div className="flex items-center gap-2 text-gold-400 font-bold uppercase">
          <Award className="h-4 w-4" />
          Mandatory Quant Gate: Outperforming 6 Benchmark Baselines
        </div>
        <p className="text-terminal-muted leading-relaxed">
          In weekly macro forecasting, complex ML models frequently memorize noise while underperforming simple priors. Under our institutional research protocol, candidate models are strictly rejected unless they demonstrably surpass all 6 baseline benchmarks: (1) Constant Prior, (2) Majority Class, (3) Historical Drift, (4) Event Window Continuation, (5) Real Rate Single-Factor, and (6) Dollar Index Single-Factor.
        </p>
      </div>

      {/* Model Comparison Table */}
      <div className="rounded-lg border border-terminal-border bg-terminal-panel p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold font-mono text-terminal-text uppercase tracking-wider">
            Out-of-Sample Performance Matrix
          </h3>
          <span className="text-xs font-mono text-terminal-muted">
            Evaluation Window: Expanding Walk-Forward (Zero Leakage)
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-terminal-border text-terminal-muted">
                <th className="pb-3">MODEL NAME</th>
                <th className="pb-3">TARGET HORIZON</th>
                <th className="pb-3 text-right">ACCURACY</th>
                <th className="pb-3 text-right">BRIER SCORE (↓)</th>
                <th className="pb-3 text-right">AUC-ROC</th>
                <th className="pb-3 text-right">SHARPE</th>
                <th className="pb-3 text-right">SAMPLE SIZE</th>
                <th className="pb-3 text-center">STATUS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-terminal-border/40">
              {models.map((m, idx) => {
                const isCandidate = !m.model_name.includes("baseline");
                return (
                  <tr
                    key={idx}
                    className={`hover:bg-terminal-card/50 ${
                      isCandidate ? "bg-terminal-card/20 font-medium" : "text-terminal-muted"
                    }`}
                  >
                    <td className="py-3">
                      <span className={isCandidate ? "text-gold-300 font-bold" : "text-terminal-muted"}>
                        {m.model_name}
                      </span>
                    </td>
                    <td className="py-3 text-terminal-dim">{m.horizon}</td>
                    <td className="py-3 text-right">{formatPercent(m.accuracy)}</td>
                    <td className="py-3 text-right font-bold text-terminal-text">
                      {formatNumber(m.brier_score, 4)}
                    </td>
                    <td className="py-3 text-right">
                      <span className={m.auc_roc > 0.55 ? "text-bull font-bold" : "text-terminal-muted"}>
                        {formatNumber(m.auc_roc, 3)}
                      </span>
                    </td>
                    <td className="py-3 text-right">
                      {m.sharpe_ratio !== undefined ? formatNumber(m.sharpe_ratio, 2) : "N/A"}
                    </td>
                    <td className="py-3 text-right text-terminal-muted">
                      N = {m.sample_size_n || 500}
                    </td>
                    <td className="py-3 text-center">
                      <StatusBadge
                        label={isCandidate ? "CANDIDATE" : "BENCHMARK"}
                        variant={isCandidate ? "gold" : "neutral"}
                        size="sm"
                      />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Baseline Definitions Description Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div className="p-4 rounded-lg border border-terminal-border bg-terminal-panel space-y-1.5 text-xs font-mono">
          <span className="font-semibold text-terminal-text">1. Constant Prior (50/50 or Empirical)</span>
          <p className="text-terminal-muted">
            Outputs constant historical win rate without inspecting features. Proves whether model captures any real variance.
          </p>
        </div>

        <div className="p-4 rounded-lg border border-terminal-border bg-terminal-panel space-y-1.5 text-xs font-mono">
          <span className="font-semibold text-terminal-text">2. Historical Drift</span>
          <p className="text-terminal-muted">
            Takes the rolling 52-week sign of gold return. If gold has had an upward trend, bets on upward trend continuation.
          </p>
        </div>

        <div className="p-4 rounded-lg border border-terminal-border bg-terminal-panel space-y-1.5 text-xs font-mono">
          <span className="font-semibold text-terminal-text">3. Single-Factor TIPS Real Rates</span>
          <p className="text-terminal-muted">
            Predicts next-week gold direction solely on whether 10Y TIPS real yields fell this week.
          </p>
        </div>

        <div className="p-4 rounded-lg border border-terminal-border bg-terminal-panel space-y-1.5 text-xs font-mono">
          <span className="font-semibold text-terminal-text">4. Single-Factor US Dollar (DXY)</span>
          <p className="text-terminal-muted">
            Predicts next-week gold direction solely on inverse DXY weekly return.
          </p>
        </div>

        <div className="p-4 rounded-lg border border-terminal-border bg-terminal-panel space-y-1.5 text-xs font-mono">
          <span className="font-semibold text-terminal-text">5. Event Window Continuation</span>
          <p className="text-terminal-muted">
            Bets that the post-macro release 1-day momentum will persist into next Friday close.
          </p>
        </div>

        <div className="p-4 rounded-lg border border-terminal-border bg-terminal-panel space-y-1.5 text-xs font-mono">
          <span className="font-semibold text-terminal-text">6. Majority Class</span>
          <p className="text-terminal-muted">
            Always predicts 1 if historical weekly upward periods exceeded 50%.
          </p>
        </div>
      </div>
    </div>
  );
}
