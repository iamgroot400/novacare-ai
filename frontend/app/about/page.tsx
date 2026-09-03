"use client";

import Link from "next/link";
import { useSupport } from "@/components/SupportProvider";

export default function AboutPage() {
  const { openChat, openVoice } = useSupport();
  return (
    <div className="container-nova max-w-3xl py-12">
      <h1 className="text-3xl font-bold">About this demo</h1>
      <p className="mt-3 text-slate-600 dark:text-slate-300">
        <strong>NovaStore</strong> is a fictional Nepal-based electronics retailer. It exists only to
        showcase <strong>NovaCare AI</strong> — an agentic customer-support agent that does real work,
        not just text generation.
      </p>

      <h2 className="mt-8 text-xl font-semibold">What NovaCare actually does</h2>
      <ul className="mt-3 list-disc space-y-1.5 pl-5 text-sm text-slate-600 dark:text-slate-300">
        <li>Looks up real order records, product inventory and support tickets in a database.</li>
        <li>Searches company policy and troubleshooting docs with local RAG (ChromaDB + local embeddings).</li>
        <li>Checks return eligibility against a fixed 14-day rule and the demo date 2026-09-03.</li>
        <li>Creates return requests and support tickets — but only after you confirm.</li>
        <li>Escalates to a human when you ask, or when it shouldn&apos;t guess.</li>
        <li>Remembers the conversation across both chat and an in-browser voice call.</li>
      </ul>

      <h2 className="mt-8 text-xl font-semibold">Open-source stack</h2>
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
        Next.js · FastAPI · LangGraph · Ollama (qwen3:4b) · ChromaDB · SQLite · Pipecat with
        Faster-Whisper STT and Kokoro TTS. No paid AI APIs. Runs with <code>docker compose up</code>.
      </p>

      <div className="mt-8 flex gap-3">
        <button onClick={() => openChat()} className="btn-primary">Ask NovaCare</button>
        <button onClick={() => openVoice()} className="btn-ghost">Call AI Support</button>
        <Link href="/dashboard" className="btn-ghost">See the dashboard</Link>
      </div>

      <p className="mt-8 rounded-xl bg-amber-50 p-4 text-xs text-amber-700 dark:bg-amber-500/10">
        Everything here is synthetic. No real people, orders, or money are involved. Refund lifecycles
        are simulated and never touch a real payment system.
      </p>
    </div>
  );
}
