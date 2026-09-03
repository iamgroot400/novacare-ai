"use client";

import type { PendingAction } from "@/lib/types";

export function ApprovalCard({
  action,
  onApprove,
  onReject,
  busy,
}: {
  action: PendingAction;
  onApprove: () => void;
  onReject: () => void;
  busy: boolean;
}) {
  const reason = (action.args?.reason as string) || (action.args?.description as string) || "";
  return (
    <div className="animate-fade-up mx-auto w-full max-w-md rounded-2xl border-2 border-nova-300 bg-nova-50 p-4 dark:border-nova-500/40 dark:bg-nova-500/10">
      <div className="mb-1 flex items-center gap-2 text-nova-700 dark:text-nova-300">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
        </svg>
        <span className="text-xs font-bold uppercase tracking-wide">Confirmation required</span>
      </div>
      <p className="text-sm font-medium text-slate-800 dark:text-slate-100">{action.summary}</p>
      {reason && (
        <p className="mt-2 rounded-lg bg-white/70 px-3 py-2 text-xs text-slate-600 dark:bg-slate-900/50 dark:text-slate-300">
          <span className="font-semibold">Details: </span>
          {reason}
        </p>
      )}
      <div className="mt-3 flex gap-2">
        <button className="btn-primary flex-1" onClick={onApprove} disabled={busy}>
          Confirm
        </button>
        <button className="btn-ghost flex-1" onClick={onReject} disabled={busy}>
          Cancel
        </button>
      </div>
      <p className="mt-2 text-center text-[11px] text-slate-400">
        Nothing is written to the database until you press Confirm.
      </p>
    </div>
  );
}
