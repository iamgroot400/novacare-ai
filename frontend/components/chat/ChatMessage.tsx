"use client";

import type { ChatMessage as Msg } from "@/lib/types";

export function ChatMessage({ message }: { message: Msg }) {
  if (message.role === "system") {
    return (
      <div className="mx-auto max-w-md rounded-lg bg-amber-50 px-3 py-2 text-center text-xs text-amber-800 dark:bg-amber-500/10 dark:text-amber-300">
        {message.content}
      </div>
    );
  }
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`animate-fade-up max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm leading-relaxed shadow-sm ${
          isUser
            ? "bg-nova-600 text-white"
            : "border border-slate-200 bg-white text-slate-800 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-100"
        }`}
      >
        {!isUser && (
          <span className="mb-1 block text-[11px] font-semibold uppercase tracking-wide text-nova-600 dark:text-nova-300">
            NovaCare
          </span>
        )}
        {message.content}
      </div>
    </div>
  );
}
