"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { DashboardData } from "@/lib/types";
import { statusLabel, timeAgo } from "@/lib/format";

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    const load = () => api.dashboard().then(setData).catch((e) => setErr(e.message));
    load();
    const t = setInterval(load, 8000);
    return () => clearInterval(t);
  }, []);

  if (err) return <div className="container-nova py-16 text-rose-600">Could not load dashboard: {err}</div>;
  if (!data) return <div className="container-nova py-16 text-slate-400">Loading…</div>;

  const t = data.totals;
  const cards = [
    ["Conversations", t.conversations],
    ["AI-resolved", t.ai_resolved],
    ["Escalations", t.escalations],
    ["Tickets created by AI", t.tickets_created_by_ai],
    ["Return requests by AI", t.returns_created_by_ai],
    ["Voice sessions", t.voice_sessions],
    ["Avg response", t.avg_response_seconds != null ? `${t.avg_response_seconds}s` : "—"],
  ] as const;

  return (
    <div className="container-nova py-10">
      <div className="flex items-center gap-3">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <span className="chip bg-amber-100 text-amber-700 dark:bg-amber-500/15">Demo Analytics</span>
      </div>
      <p className="mt-1 text-sm text-slate-500">{data.disclaimer}</p>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map(([label, value]) => (
          <div key={label} className="card p-4">
            <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
            <p className="mt-1 text-2xl font-bold">{value}</p>
          </div>
        ))}
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-3">
        <BarCard title="Orders by status" data={data.orders_by_status} />
        <BarCard title="Tickets by status" data={data.tickets_by_status} />
        <BarCard title="Returns by status" data={data.returns_by_status} />
      </div>

      <div className="card mt-8 overflow-hidden">
        <h2 className="border-b border-slate-200 px-5 py-3 font-semibold dark:border-slate-800">Recent activity</h2>
        <div className="divide-y divide-slate-100 dark:divide-slate-800">
          {data.recent_activity.length === 0 && (
            <p className="px-5 py-4 text-sm text-slate-400">No conversations yet — open NovaCare and ask something.</p>
          )}
          {data.recent_activity.map((r) => (
            <div key={r.conversation_id} className="flex items-center justify-between gap-4 px-5 py-3 text-sm">
              <div className="min-w-0">
                <p className="truncate">
                  {r.order_id && <span className="mr-2 font-mono text-nova-600">{r.order_id}</span>}
                  {r.summary}
                </p>
                <p className="text-xs text-slate-400">
                  {r.channel} · {timeAgo(r.updated_at)}
                </p>
              </div>
              <span className="chip shrink-0 bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                {r.outcome}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function BarCard({ title, data }: { title: string; data: Record<string, number> }) {
  const entries = Object.entries(data);
  const max = Math.max(1, ...entries.map(([, v]) => v));
  return (
    <div className="card p-5">
      <h3 className="text-sm font-semibold">{title}</h3>
      <div className="mt-3 space-y-2">
        {entries.length === 0 && <p className="text-xs text-slate-400">No data</p>}
        {entries.map(([k, v]) => (
          <div key={k}>
            <div className="flex justify-between text-xs text-slate-500">
              <span>{statusLabel(k)}</span>
              <span>{v}</span>
            </div>
            <div className="mt-1 h-2 rounded-full bg-slate-100 dark:bg-slate-800">
              <div className="h-2 rounded-full bg-nova-500" style={{ width: `${(v / max) * 100}%` }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
