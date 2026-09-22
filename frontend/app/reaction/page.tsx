"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { api, ReactionDetail, MacroEvent } from "@/lib/api";
import { MetricCard } from "@/components/MetricCard";
import { StatusBadge } from "@/components/StatusBadge";
import { formatNumber, formatPercent, formatPctDirect, formatDate } from "@/lib/utils";
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
import { Zap, Clock, ShieldAlert, ArrowLeft, ArrowRight, Layers } from "lucide-react";

function ReactionContent() {
  const searchParams = useSearchParams();
  const eventIdParam = searchParams.get("event_id");
  const [eventId, setEventId] = useState<number>(eventIdParam ? parseInt(eventIdParam) : 1);
  const [reaction, setReaction] = useState<ReactionDetail | null>(null);
  const [comparables, setComparables] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [allEvents, setAllEvents] = useState<MacroEvent[]>([]);

  useEffect(() => {
    api.getEvents({ limit: 50 }).then((res) => {
      setAllEvents(res || []);
      if (!eventIdParam && res && res.length > 0) {
        setEventId(res[0].event_id);
      }
    });
  }, [eventIdParam]);

  useEffect(() => {
    if (!eventId) return;
    setLoading(true);
    Promise.all([
      api.getEventReaction(eventId).catch(() => null),
      api.getEventComparables(eventId).catch(() => null),
    ])
      .then(([rData, cData]) => {
        setReaction(rData);
        setComparables(cData);
      })
      .finally(() => setLoading(false));
  }, [eventId]);

  const horizonData = reaction?.horizons
    ? Object.entries(reaction.horizons).map(([key, h]) => ({
        horizon: key,
        return_pct: h.return_pct !== undefined ? Number((h.return_pct * 100).toFixed(3)) : 0,
        bps: h.bps !== undefined ? Number(h.bps.toFixed(1)) : 0,
        price: h.price,
        hasData: h.price !== undefined && h.price !== null,
        timestamp: h.timestamp,
      }))
    : [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-terminal-border">
        <div>
          <h1 className="text-2xl font-bold font-mono text-terminal-text tracking-tight flex items-center gap-2">
            <Zap className="h-6 w-6 text-gold-400" />
            INDEPENDENT HORIZON REACTION ENGINE
          </h1>
          <p className="text-xs font-mono text-terminal-muted mt-0.5">
            Strict non-reused horizon observation: Pre-Release (t_pre), 5m, 1h, 4h, 1d, and Next Friday Close
          </p>
        </div>

        {/* Event selector dropdown */}
        <div className="flex items-center gap-2">
          <select
            value={eventId}
            onChange={(e) => setEventId(parseInt(e.target.value))}
            className="px-3 py-1.5 rounded border border-terminal-border bg-terminal-panel text-xs font-mono text-terminal-text focus:outline-none focus:border-gold-500"
          >
            {allEvents.map((evt) => (
              <option key={evt.event_id} value={evt.event_id}>
                {formatDate(evt.timestamp_utc)} - {evt.event_name} ({evt.event_type})
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading && (
        <div className="p-8 text-center text-xs font-mono text-terminal-muted">
          Loading reaction dynamics and independent horizon bars...
        </div>
      )}

      {reaction && !loading && (
        <>
          {/* Reaction Header Card */}
          <div className="rounded-lg border border-terminal-border bg-terminal-panel p-5 space-y-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-lg font-bold font-mono text-terminal-text">
                    {reaction.event_name}
                  </span>
                  <StatusBadge
                    label={reaction.event_type}
                    variant="gold"
                  />
                  <StatusBadge
                    label={reaction.is_synthetic ? "SYNTHETIC" : "REAL PIT VINTAGE"}
                    variant={reaction.is_synthetic ? "danger" : "success"}
                  />
                </div>
                <div className="flex items-center gap-4 text-xs font-mono text-terminal-dim mt-1">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5 text-terminal-muted" />
                    Release: {reaction.timestamp_utc}
                  </span>
                  <span>•</span>
                  <span>Pre-Release Anchor (t-1): ${formatNumber(reaction.ref_pre, 2)}</span>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded border border-terminal-border bg-terminal-card text-center">
                  <span className="text-[10px] font-mono text-terminal-muted block">SURPRISE (Z)</span>
                  <span
                    className={`text-base font-mono font-bold ${
                      (reaction.surprise_std || 0) > 0.5
                        ? "text-bull"
                        : (reaction.surprise_std || 0) < -0.5
                        ? "text-bear"
                        : "text-terminal-text"
                    }`}
                  >
                    {reaction.surprise_std !== undefined
                      ? `${reaction.surprise_std > 0 ? "+" : ""}${reaction.surprise_std.toFixed(2)}σ`
                      : "N/A"}
                  </span>
                </div>

                <div className="p-2.5 rounded border border-terminal-border bg-terminal-card text-center">
                  <span className="text-[10px] font-mono text-terminal-muted block">NEXT FRIDAY MOVE</span>
                  <span
                    className={`text-base font-mono font-bold ${
                      (reaction.horizons?.next_friday?.return_pct || 0) > 0
                        ? "text-bull"
                        : (reaction.horizons?.next_friday?.return_pct || 0) < 0
                        ? "text-bear"
                        : "text-terminal-text"
                    }`}
                  >
                    {reaction.horizons?.next_friday?.return_pct !== undefined
                      ? formatPercent(reaction.horizons.next_friday.return_pct)
                      : "N/A"}
                  </span>
                </div>
              </div>
            </div>

            {/* Active Regimes during Event */}
            <div className="pt-3 border-t border-terminal-border/60 flex flex-wrap items-center gap-3 text-xs font-mono">
              <span className="text-terminal-muted flex items-center gap-1">
                <Layers className="h-3.5 w-3.5 text-terminal-dim" /> Regime State:
              </span>
              {Object.entries(reaction.regimes || {}).map(([regimeKey, regimeVal]) => (
                <span key={regimeKey} className="px-2 py-0.5 rounded bg-terminal-card border border-terminal-border text-terminal-text">
                  <strong className="text-terminal-dim font-normal">{regimeKey}:</strong> {regimeVal}
                </span>
              ))}
            </div>
          </div>

          {/* Horizon Response Chart */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 rounded-lg border border-terminal-border bg-terminal-panel p-5 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold font-mono text-terminal-text uppercase tracking-wider">
                  Horizon Return Profile (Basis Points from t_pre)
                </h3>
                <span className="text-xs font-mono text-terminal-dim">
                  Strictly Disjoint Timestamps (t_pre &lt; t_1 &lt; t_2)
                </span>
              </div>

              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={horizonData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="horizon" stroke="#64748b" tick={{ fontSize: 11, fill: "#94a3b8" }} />
                    <YAxis stroke="#64748b" tick={{ fontSize: 11, fill: "#94a3b8" }} tickFormatter={(v) => `${v} bps`} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#0d131f",
                        borderColor: "#334155",
                        fontSize: "12px",
                        fontFamily: "monospace",
                      }}
                      formatter={(val: any, name: any) => [`${val} bps`, "Move"]}
                    />
                    <ReferenceLine y={0} stroke="#475569" />
                    <Bar dataKey="bps" name="Basis Points">
                      {horizonData.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={
                            !entry.hasData
                              ? "#334155"
                              : entry.bps >= 0
                              ? "#10b981"
                              : "#f43f5e"
                          }
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <p className="text-[11px] font-mono text-terminal-dim">
                * Note: If intraday tick/1m bars were unavailable at event execution time, intraday horizons (5m, 1h, 4h) display null rather than repeating daily close.
              </p>
            </div>

            {/* Horizon Data Table */}
            <div className="rounded-lg border border-terminal-border bg-terminal-panel p-5 space-y-3">
              <h3 className="text-sm font-semibold font-mono text-terminal-text uppercase tracking-wider">
                Observation Detail
              </h3>
              <div className="space-y-2">
                {horizonData.map((h) => (
                  <div
                    key={h.horizon}
                    className="p-2.5 rounded border border-terminal-border/60 bg-terminal-card flex items-center justify-between text-xs font-mono"
                  >
                    <div>
                      <span className="font-semibold text-terminal-text block">{h.horizon}</span>
                      <span className="text-[10px] text-terminal-dim">
                        {h.timestamp ? formatDate(h.timestamp) : "No Intraday Bar"}
                      </span>
                    </div>
                    <div className="text-right">
                      {h.hasData ? (
                        <>
                          <div className={h.bps >= 0 ? "text-bull font-bold" : "text-bear font-bold"}>
                            {h.bps > 0 ? `+${h.bps}` : h.bps} bps
                          </div>
                          <div className="text-[10px] text-terminal-muted">
                            ${formatNumber(h.price, 2)}
                          </div>
                        </>
                      ) : (
                        <span className="text-terminal-dim">N/A</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Historical Comparables */}
          {comparables && comparables.comparables && (
            <div className="rounded-lg border border-terminal-border bg-terminal-panel p-5 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold font-mono text-terminal-text uppercase tracking-wider">
                  Historical Comparables ({reaction.event_name})
                </h3>
                <span className="text-xs font-mono text-gold-400">
                  Sample Size: N={comparables.sample_size_n || comparables.comparables.length}
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead>
                    <tr className="border-b border-terminal-border text-terminal-muted">
                      <th className="pb-2">RELEASE DATE</th>
                      <th className="pb-2">EVENT TYPE</th>
                      <th className="pb-2 text-right">ACTUAL</th>
                      <th className="pb-2 text-right">SURPRISE</th>
                      <th className="pb-2 text-right">1-DAY RETURN</th>
                      <th className="pb-2 text-right">NEXT FRI RETURN</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-terminal-border/40">
                    {comparables.comparables.map((c: any, i: number) => (
                      <tr key={i} className="hover:bg-terminal-card/40">
                        <td className="py-2 text-terminal-dim">{formatDate(c.timestamp_utc)}</td>
                        <td className="py-2 text-terminal-text">{c.event_type}</td>
                        <td className="py-2 text-right text-terminal-text">{formatNumber(c.actual_value, 2)}</td>
                        <td className="py-2 text-right">
                          <span className={(c.surprise_std || 0) > 0 ? "text-bull" : "text-bear"}>
                            {c.surprise_std ? `${c.surprise_std > 0 ? "+" : ""}${c.surprise_std.toFixed(2)}σ` : "-"}
                          </span>
                        </td>
                        <td className="py-2 text-right">
                          {c.return_1d !== undefined ? (
                            <span className={c.return_1d > 0 ? "text-bull" : "text-bear"}>
                              {formatPercent(c.return_1d)}
                            </span>
                          ) : (
                            <span className="text-terminal-dim">N/A</span>
                          )}
                        </td>
                        <td className="py-2 text-right">
                          {c.return_next_friday !== undefined ? (
                            <span className={c.return_next_friday > 0 ? "text-bull font-bold" : "text-bear font-bold"}>
                              {formatPercent(c.return_next_friday)}
                            </span>
                          ) : (
                            <span className="text-terminal-dim">N/A</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default function ReactionPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs font-mono text-terminal-muted">Loading...</div>}>
      <ReactionContent />
    </Suspense>
  );
}
