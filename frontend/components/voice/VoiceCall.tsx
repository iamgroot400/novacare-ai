"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useSupport } from "@/components/SupportProvider";
import { VOICE_BASE } from "@/lib/api";
import { Waveform } from "./Waveform";

type CallState = "requesting" | "ready" | "recording" | "thinking" | "speaking" | "error";

export function VoiceCall({ onClose }: { onClose: () => void }) {
  const { convo, openChat } = useSupport();
  const [state, setState] = useState<CallState>("requesting");
  const [error, setError] = useState("");
  const [muted, setMuted] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [userText, setUserText] = useState("");
  const [aiText, setAiText] = useState("");
  const [fullDuplex, setFullDuplex] = useState<boolean | null>(null);

  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval>>();

  const stopEverything = useCallback(() => {
    recorderRef.current?.state === "recording" && recorderRef.current.stop();
    streamRef.current?.getTracks().forEach((t) => t.stop());
    if (timerRef.current) clearInterval(timerRef.current);
    audioRef.current?.pause();
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        streamRef.current = stream;
        setState("ready");
        timerRef.current = setInterval(() => setSeconds((s) => s + 1), 1000);
        try {
          const cfg = await fetch(`${VOICE_BASE}/api/voice/config`).then((r) => r.json());
          setFullDuplex(Boolean(cfg.full_duplex));
        } catch {
          setFullDuplex(false);
        }
      } catch (e) {
        setState("error");
        setError(
          "Microphone access was blocked. Enable it in your browser's site settings, then reopen the call. You can also keep chatting by text.",
        );
      }
    })();
    return stopEverything;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    streamRef.current?.getAudioTracks().forEach((t) => (t.enabled = !muted));
  }, [muted]);

  const startRecording = () => {
    if (!streamRef.current || muted || state === "thinking" || state === "speaking") return;
    chunksRef.current = [];
    const mime = MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : "";
    const rec = new MediaRecorder(streamRef.current, mime ? { mimeType: mime } : undefined);
    rec.ondataavailable = (e) => e.data.size && chunksRef.current.push(e.data);
    rec.onstop = () => void sendClip();
    recorderRef.current = rec;
    rec.start();
    setState("recording");
  };

  const stopRecording = () => {
    if (recorderRef.current?.state === "recording") recorderRef.current.stop();
  };

  const sendClip = async () => {
    const blob = new Blob(chunksRef.current, { type: "audio/webm" });
    if (blob.size < 1200) {
      setState("ready");
      return;
    }
    setState("thinking");
    setAiText("");
    try {
      const fd = new FormData();
      fd.append("audio", blob, "clip.webm");
      fd.append("conversation_id", convo.conversationId || "");
      const res = await fetch(`${VOICE_BASE}/api/voice/ptt`, { method: "POST", body: fd });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setUserText(data.transcript || "(couldn't hear that)");
      setAiText(data.reply || "");
      if (data.transcript) convo.appendLocal("user", data.transcript);
      if (data.reply) convo.appendLocal("assistant", data.reply);
      void convo.refresh();

      if (data.audio_base64) {
        const audio = new Audio(`data:${data.audio_mime || "audio/wav"};base64,${data.audio_base64}`);
        audioRef.current = audio;
        setState("speaking");
        audio.onended = () => setState("ready");
        await audio.play().catch(() => setState("ready"));
      } else {
        setState("ready");
      }
    } catch (e) {
      setState("error");
      setError(`Voice service error: ${(e as Error).message}. Try again or switch to text chat.`);
    }
  };

  const mmss = `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
  const statusLabel: Record<CallState, string> = {
    requesting: "Requesting microphone…",
    ready: "Connected — hold the button and speak",
    recording: "Listening…",
    thinking: "Processing voice…",
    speaking: "NovaCare is speaking…",
    error: "Call problem",
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur">
      <div className="card w-full max-w-md overflow-hidden">
        <div className="gradient-hero relative border-b border-slate-200 p-5 dark:border-slate-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="relative flex h-3 w-3">
                {(state === "recording" || state === "speaking") && (
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-nova-400 opacity-75" />
                )}
                <span className="relative inline-flex h-3 w-3 rounded-full bg-nova-500" />
              </span>
              <span className="text-sm font-semibold">Call AI Support</span>
            </div>
            <span className="font-mono text-sm text-slate-500">{mmss}</span>
          </div>
          <p className="mt-1 text-xs text-slate-500">{statusLabel[state]}</p>
          {fullDuplex === false && state !== "error" && (
            <p className="mt-1 text-[11px] text-amber-600 dark:text-amber-400">
              Full-duplex unavailable — using push-to-talk.
            </p>
          )}
        </div>

        <div className="p-5">
          <Waveform stream={streamRef.current} active={state === "recording" || state === "speaking"} />

          <div className="mt-4 space-y-3 text-sm">
            <div className="rounded-xl bg-slate-100 p-3 dark:bg-slate-800/60">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">You</p>
              <p className="min-h-[1.25rem] text-slate-700 dark:text-slate-200">{userText || "—"}</p>
            </div>
            <div className="rounded-xl bg-nova-50 p-3 dark:bg-nova-500/10">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-nova-500">NovaCare</p>
              <p className="min-h-[1.25rem] text-slate-700 dark:text-slate-100">{aiText || "—"}</p>
            </div>
          </div>

          {state === "error" && <p className="mt-3 text-xs text-rose-500">{error}</p>}

          <div className="mt-5 flex items-center justify-center gap-3">
            <button
              onClick={() => setMuted((m) => !m)}
              className={`btn-ghost !h-12 !w-12 !p-0 ${muted ? "!bg-rose-100 !text-rose-600 dark:!bg-rose-500/20" : ""}`}
              aria-label={muted ? "Unmute" : "Mute"}
              disabled={state === "requesting" || state === "error"}
            >
              {muted ? "🔇" : "🎙️"}
            </button>

            <button
              onMouseDown={startRecording}
              onMouseUp={stopRecording}
              onMouseLeave={stopRecording}
              onTouchStart={(e) => {
                e.preventDefault();
                startRecording();
              }}
              onTouchEnd={(e) => {
                e.preventDefault();
                stopRecording();
              }}
              disabled={["requesting", "thinking", "speaking", "error"].includes(state) || muted}
              className="btn-primary !h-16 !w-40 select-none text-sm"
            >
              {state === "recording" ? "Release to send" : "Hold to talk"}
            </button>

            <button
              onClick={() => {
                stopEverything();
                onClose();
              }}
              className="btn !h-12 !w-12 !p-0 bg-rose-600 text-white hover:bg-rose-700"
              aria-label="End call"
            >
              ✕
            </button>
          </div>

          <button
            onClick={() => {
              stopEverything();
              openChat();
            }}
            className="mt-4 w-full text-center text-xs font-medium text-nova-600 dark:text-nova-300"
          >
            Switch back to text chat (same conversation)
          </button>
        </div>
      </div>
    </div>
  );
}
