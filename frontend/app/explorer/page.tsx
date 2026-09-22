"use client";

import { useEffect, useState } from "react";
import { api, MacroEvent } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { formatNumber, formatDate } from "@/lib/utils";
import Link from "next/link";
import {
  Calendar,
  Search,
  ChevronLeft,
  ChevronRight,
  Filter,
  ArrowUpRight,
  ShieldCheck,
  AlertCircle,
} from "lucide-react";

export default function ExplorerPage() {
  const [events, setEvents] = useState<MacroEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [page, setPage] = useState<number>(0);
  const pageSize = 25;

  const loadEvents = async () => {
    setLoading(true);
    try {
      const params: any = {
        limit: pageSize,
        offset: page * pageSize,
      };
      if (filterType !== "ALL") params.event_type = filterType;
      const data = await api.getEvents(params);
      setEvents(data || []);
    } catch (err) {
      console.error("Failed to load events", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
  }, [page, filterType]);

  const filtered = events.filter((e) =>
    searchQuery === ""
      ? true
      : e.event_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        e.timestamp_utc.includes(searchQuery)
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-terminal-border">
        <div>
          <h1 className="text-2xl font-bold font-mono text-terminal-text tracking-tight flex items-center gap-2">
            <Calendar className="h-6 w-6 text-gold-400" />
            MACRO EVENT EXPLORER
          </h1>
          <p className="text-xs font-mono text-terminal-muted mt-0.5">
            Full audit catalog of 1,428 scheduled macro releases with real-time vintage tracking
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-terminal-muted">
            Total Catalog: <strong className="text-gold-400">1,428 releases</strong>
          </span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="rounded-lg border border-terminal-border bg-terminal-panel p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2 w-full md:w-auto">
          <div className="relative flex-1 md:w-64">
            <Search className="h-4 w-4 absolute left-3 top-2.5 text-terminal-muted" />
            <input
              type="text"
              placeholder="Search event name or date..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs font-mono rounded border border-terminal-border bg-terminal-card text-terminal-text focus:outline-none focus:border-gold-500"
            />
          </div>

          <div className="flex items-center gap-1.5">
            <Filter className="h-4 w-4 text-terminal-muted" />
            <select
              value={filterType}
              onChange={(e) => {
                setFilterType(e.target.value);
                setPage(0);
              }}
              className="px-3 py-1.5 text-xs font-mono rounded border border-terminal-border bg-terminal-card text-terminal-text focus:outline-none focus:border-gold-500"
            >
              <option value="ALL">All Types</option>
              <option value="CPI">CPI</option>
              <option value="NFP">NFP</option>
              <option value="FOMC">FOMC</option>
              <option value="PMI">PMI</option>
              <option value="GDP">GDP</option>
            </select>
          </div>
        </div>

        {/* Pagination controls */}
        <div className="flex items-center gap-2 self-end md:self-auto text-xs font-mono">
          <span className="text-terminal-muted">
            Page {page + 1}
          </span>
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            className="p-1 rounded border border-terminal-border bg-terminal-card text-terminal-muted disabled:opacity-40"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={events.length < pageSize}
            className="p-1 rounded border border-terminal-border bg-terminal-card text-terminal-muted disabled:opacity-40"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Events Table */}
      <div className="rounded-lg border border-terminal-border bg-terminal-panel p-5 space-y-4">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-terminal-border text-terminal-muted">
                <th className="pb-2.5 font-medium">TIMESTAMP (UTC)</th>
                <th className="pb-2.5 font-medium">EVENT NAME</th>
                <th className="pb-2.5 font-medium">TYPE</th>
                <th className="pb-2.5 font-medium text-right">ACTUAL</th>
                <th className="pb-2.5 font-medium text-right">CONSENSUS</th>
                <th className="pb-2.5 font-medium text-right">SURPRISE (Z)</th>
                <th className="pb-2.5 font-medium text-center">VINTAGE</th>
                <th className="pb-2.5 font-medium text-center">SYNTHETIC?</th>
                <th className="pb-2.5 font-medium text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-terminal-border/40">
              {filtered.map((evt) => (
                <tr key={evt.event_id} className="hover:bg-terminal-card/50 transition-colors">
                  <td className="py-2.5 text-terminal-dim">{formatDate(evt.timestamp_utc)}</td>
                  <td className="py-2.5 font-medium text-terminal-text">{evt.event_name}</td>
                  <td className="py-2.5">
                    <span className="px-2 py-0.5 rounded bg-terminal-card text-terminal-muted border border-terminal-border text-[10px]">
                      {evt.event_type}
                    </span>
                  </td>
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
                  <td className="py-2.5 text-center">
                    {evt.is_synthetic ? (
                      <StatusBadge label="SYNTHETIC" variant="danger" size="sm" />
                    ) : (
                      <span className="text-emerald-400 text-[10px]">REAL</span>
                    )}
                  </td>
                  <td className="py-2.5 text-right">
                    <Link
                      href={`/reaction?event_id=${evt.event_id}`}
                      className="text-gold-400 hover:text-gold-300 underline inline-flex items-center gap-0.5"
                    >
                      Reaction <ArrowUpRight className="h-3 w-3" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
