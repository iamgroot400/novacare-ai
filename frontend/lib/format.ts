export function npr(value: number): string {
  return `NPR ${value.toLocaleString("en-IN")}`;
}

export function statusLabel(s: string): string {
  return s
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export const STATUS_STYLES: Record<string, string> = {
  delivered: "bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300",
  in_transit: "bg-sky-100 text-sky-800 dark:bg-sky-500/15 dark:text-sky-300",
  shipped: "bg-sky-100 text-sky-800 dark:bg-sky-500/15 dark:text-sky-300",
  processing: "bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300",
  delayed: "bg-orange-100 text-orange-800 dark:bg-orange-500/15 dark:text-orange-300",
  cancelled: "bg-rose-100 text-rose-800 dark:bg-rose-500/15 dark:text-rose-300",
  return_requested: "bg-purple-100 text-purple-800 dark:bg-purple-500/15 dark:text-purple-300",
};

export function statusStyle(s: string): string {
  return STATUS_STYLES[s] || "bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-200";
}

export function timeAgo(iso?: string | null): string {
  if (!iso) return "";
  const d = new Date(iso).getTime();
  const diff = Date.now() - d;
  const mins = Math.round(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.round(hrs / 24)}d ago`;
}
