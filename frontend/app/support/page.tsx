"use client";

import { SupportWidget } from "@/components/chat/SupportWidget";

export default function SupportPage() {
  return (
    <div className="container-nova py-6">
      <div className="mb-4">
        <h1 className="text-2xl font-bold">NovaCare AI</h1>
        <p className="text-sm text-slate-500">
          One agent, two interfaces. Watch the Agent Activity panel — every line is a real tool call,
          knowledge-base search or database operation, never hidden reasoning.
        </p>
      </div>
      <div className="card h-[calc(100vh-13rem)] min-h-[560px] overflow-hidden">
        <SupportWidget variant="page" />
      </div>
    </div>
  );
}
