"use client";

import { useEffect, useRef } from "react";
import type { AgentEvent } from "@/lib/types";

const ICONS: Record<string, string> = {
  intent_detected: "M12 2a10 10 0 100 20 10 10 0 000-20zm0 5v5l3 3",
  tool_started: "M4 12h16M4 6h16M4 18h16",
  tool_finished: "M20 6L9 17l-5-5",
  tool_error: "M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z",
  kb_search: "M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z",
  db_read: "M12 2C6.5 2 4 4 4 5v14c0 1 2.5 3 8 3s8-2 8-3V5c0-1-2.5-3-8-3z",
  db_write: "M12 2C6.5 2 4 4 4 5v14c0 1 2.5 3 8 3s8-2 8-3V5c0-1-2.5-3-8-3zM9 12l2 2 4-4",
  confirmation_requested: "M9 11l3 3L22 4M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11",
  confirmation_resolved: "M20 6L9 17l-5-5",
  escalation: "M12 2L2 22h20L12 2zm0 6v6m0 4h.01",
  status: "M12 8v4l3 3",
  message: "M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z",
};

const STATUS_COLOR: Record<string, string> = {
  running: "text-nova-600 dark:text-nova-300",
  success: "text-emerald-600 dark:text-emerald-400",
  error: "text-rose-600 dark:text-rose-400",
  warning: "text-orange-600 dark:text-orange-400",
  waiting: "text-amber-600 dark:text-amber-400",
  cancelled: "text-slate-400",
  info: "text-slate-500 dark:text-slate-400",
};

export function ActivityPanel({ events }: { events: AgentEvent[] }) {
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events.length]);

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-800">
        <h3 className="text-sm font-semibold">Agent Activity</h3>
        <span className="chip bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400">
          observable events only
        </span>
      </div>
      <div className="scroll-thin flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {events.length === 0 && (
          <p className="text-sm text-slate-400">
            Tool calls, knowledge-base searches and database operations will appear here as NovaCare works.
          </p>
        )}
        {events.map((e) => (
          <div key={e.id} className="animate-fade-up flex gap-3">
            <div className={`mt-0.5 shrink-0 ${STATUS_COLOR[e.status] || STATUS_COLOR.info}`}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d={ICONS[e.type] || ICONS.status} />
              </svg>
            </div>
            <div className="min-w-0">
              <p className="text-sm leading-snug text-slate-700 dark:text-slate-200">{e.display}</p>
              <p className="mt-0.5 text-[11px] uppercase tracking-wide text-slate-400">
                {e.tool ? `${e.tool} · ` : ""}
                {e.type.replace(/_/g, " ")}
              </p>
            </div>
          </div>
        ))}
        <div ref={endRef} />
      </div>
    </div>
  );
}
