"use client";

import { useRouter } from "next/navigation";
import { VoiceCall } from "@/components/voice/VoiceCall";

export default function SupportPage() {
  const router = useRouter();
  return (
    <div className="container-nova py-6">
      <div className="mb-2 text-center">
        <h1 className="text-2xl font-bold">Talk to NovaCare</h1>
        <p className="text-sm text-slate-500">
          A live voice call with our AI agent. Just speak — you can interrupt at any time.
        </p>
      </div>
      <VoiceCall inline onClose={() => router.push("/")} />
    </div>
  );
}
