"use client";

import { useEffect, useRef, useState } from "react";
import { useSupport } from "@/components/SupportProvider";
import { ActivityPanel } from "@/components/agent-activity/ActivityPanel";
import { ChatMessage } from "./ChatMessage";
import { ApprovalCard } from "./ApprovalCard";
import { SuggestionChips } from "./SuggestionChips";

export function SupportWidget({
  variant = "page",
  onClose,
}: {
  variant?: "page" | "drawer";
  onClose?: () => void;
}) {
  const { convo, openVoice, pendingPrompt, consumePrompt } = useSupport();
  const [input, setInput] = useState("");
  const [showActivity, setShowActivity] = useState(variant === "page");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (pendingPrompt) {
      setInput(pendingPrompt);
      consumePrompt();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingPrompt]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [convo.messages.length, convo.busy, convo.pending]);

  const submit = (text?: string) => {
    const value = (text ?? input).trim();
    if (!value || convo.busy) return;
    convo.send(value);
    setInput("");
  };

  const online = convo.connection === "online";

  return (
    <div className="flex h-full flex-col bg-slate-50 dark:bg-slate-950">
      {/* header */}
      <header className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center gap-2.5">
          <span className="relative flex h-2.5 w-2.5">
            <span
              className={`absolute inline-flex h-full w-full rounded-full ${
                online ? "animate-ping bg-emerald-400" : "bg-slate-300"
              } opacity-75`}
            />
            <span
              className={`relative inline-flex h-2.5 w-2.5 rounded-full ${
                online ? "bg-emerald-500" : "bg-slate-400"
              }`}
            />
          </span>
          <div>
            <p className="text-sm font-semibold leading-none">NovaCare AI</p>
            <p className="text-[11px] text-slate-400">
              {online ? "Online" : convo.connection === "connecting" ? "Connecting…" : "Reconnecting…"}
              {convo.conversationId ? ` · ${convo.conversationId.slice(0, 12)}` : ""}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <button className="btn-ghost !px-2.5 !py-1.5 text-xs" onClick={() => openVoice()}>
            Call AI Support
          </button>
          {variant === "drawer" && onClose && (
            <button
              onClick={onClose}
              aria-label="Close support"
              className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </header>

      <div className={`flex min-h-0 flex-1 ${variant === "page" ? "lg:gap-4 lg:p-4" : ""}`}>
        {/* conversation column */}
        <section className={`flex min-h-0 flex-1 flex-col ${variant === "page" ? "lg:card lg:overflow-hidden" : ""}`}>
          <div ref={scrollRef} className="scroll-thin flex-1 space-y-3 overflow-y-auto px-4 py-4">
            {convo.messages.length === 0 && (
              <div className="mx-auto max-w-md space-y-3 pt-6 text-center">
                <p className="text-sm text-slate-500">
                  Hi, I&apos;m NovaCare. Ask about an order, a return, a product, or a device that
                  isn&apos;t working. Try one of these:
                </p>
                <SuggestionChips onPick={(q) => submit(q)} />
              </div>
            )}
            {convo.messages.map((m) => (
              <ChatMessage key={m.id} message={m} />
            ))}
            {convo.pending && (
              <ApprovalCard
                action={convo.pending}
                busy={convo.busy}
                onApprove={convo.approve}
                onReject={convo.reject}
              />
            )}
            {convo.busy && (
              <div className="flex items-center gap-1.5 px-1 text-slate-400">
                <span className="h-2 w-2 animate-bounce rounded-full bg-nova-400 [animation-delay:-0.2s]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-nova-400 [animation-delay:-0.1s]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-nova-400" />
              </div>
            )}
          </div>

          {convo.messages.length > 0 && (
            <div className="border-t border-slate-200 px-4 py-2 dark:border-slate-800">
              <SuggestionChips compact onPick={(q) => submit(q)} />
            </div>
          )}

          {/* input */}
          <div className="border-t border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-end gap-2">
              <button
                onClick={() => openVoice()}
                aria-label="Start voice call"
                className="btn-ghost !p-2.5"
                title="Switch to voice"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z" />
                  <path d="M19 10v2a7 7 0 01-14 0v-2M12 19v4M8 23h8" />
                </svg>
              </button>
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    submit();
                  }
                }}
                rows={1}
                maxLength={2000}
                placeholder="Message NovaCare…"
                className="max-h-32 flex-1 resize-none rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-nova-400 focus:ring-2 focus:ring-nova-100 dark:border-slate-700 dark:bg-slate-950 dark:focus:ring-nova-900"
              />
              <button className="btn-primary !p-2.5" onClick={() => submit()} disabled={convo.busy || !input.trim()} aria-label="Send">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
                </svg>
              </button>
            </div>
            {variant !== "page" && (
              <button
                onClick={() => setShowActivity((s) => !s)}
                className="mt-2 text-xs font-medium text-nova-600 dark:text-nova-300"
              >
                {showActivity ? "Hide" : "Show"} agent activity ({convo.events.length})
              </button>
            )}
          </div>
        </section>

        {/* activity column */}
        {(variant === "page" || showActivity) && (
          <aside
            className={
              variant === "page"
                ? "hidden w-80 shrink-0 lg:block lg:card lg:overflow-hidden"
                : "border-t border-slate-200 dark:border-slate-800"
            }
          >
            <div className={variant === "page" ? "h-full" : "max-h-64 overflow-hidden"}>
              <ActivityPanel events={convo.events} />
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}
