"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
} from "react";
import { useConversation } from "@/lib/useConversation";
import { SupportWidget } from "@/components/chat/SupportWidget";
import { VoiceCall } from "@/components/voice/VoiceCall";

interface OpenOptions {
  prompt?: string;
  orderId?: string;
  productId?: string;
  autoSend?: boolean;
}

interface SupportCtx {
  convo: ReturnType<typeof useConversation>;
  openChat: (opts?: OpenOptions) => void;
  openVoice: (opts?: OpenOptions) => void;
  closeAll: () => void;
  drawerOpen: boolean;
  voiceOpen: boolean;
  pendingPrompt: string;
  consumePrompt: () => string;
}

const Ctx = createContext<SupportCtx | null>(null);

export function useSupport(): SupportCtx {
  const v = useContext(Ctx);
  if (!v) throw new Error("useSupport must be used inside <SupportProvider>");
  return v;
}

export function SupportProvider({ children }: { children: React.ReactNode }) {
  const convo = useConversation();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [voiceOpen, setVoiceOpen] = useState(false);
  const promptRef = useRef<string>("");
  const [pendingPrompt, setPendingPrompt] = useState("");

  const applyContext = useCallback(
    (opts?: OpenOptions) => {
      if (opts?.prompt) {
        promptRef.current = opts.prompt;
        setPendingPrompt(opts.prompt);
        if (opts.autoSend && convo.conversationId) {
          convo.send(opts.prompt);
          promptRef.current = "";
          setPendingPrompt("");
        }
      }
    },
    [convo],
  );

  const openChat = useCallback(
    (opts?: OpenOptions) => {
      setVoiceOpen(false);
      setDrawerOpen(true);
      applyContext(opts);
    },
    [applyContext],
  );

  const openVoice = useCallback(
    (opts?: OpenOptions) => {
      setDrawerOpen(false);
      setVoiceOpen(true);
      applyContext(opts);
    },
    [applyContext],
  );

  const closeAll = useCallback(() => {
    setDrawerOpen(false);
    setVoiceOpen(false);
  }, []);

  const consumePrompt = useCallback(() => {
    const p = promptRef.current;
    promptRef.current = "";
    setPendingPrompt("");
    return p;
  }, []);

  const value = useMemo(
    () => ({
      convo,
      openChat,
      openVoice,
      closeAll,
      drawerOpen,
      voiceOpen,
      pendingPrompt,
      consumePrompt,
    }),
    [convo, openChat, openVoice, closeAll, drawerOpen, voiceOpen, pendingPrompt, consumePrompt],
  );

  return (
    <Ctx.Provider value={value}>
      {children}

      {/* Slide-over chat drawer */}
      <div
        className={`fixed inset-0 z-40 transition ${drawerOpen ? "pointer-events-auto" : "pointer-events-none"}`}
        aria-hidden={!drawerOpen}
      >
        <div
          className={`absolute inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity ${
            drawerOpen ? "opacity-100" : "opacity-0"
          }`}
          onClick={closeAll}
        />
        <div
          className={`absolute right-0 top-0 h-full w-full max-w-xl transform bg-slate-50 shadow-2xl transition-transform dark:bg-slate-950 ${
            drawerOpen ? "translate-x-0" : "translate-x-full"
          }`}
          role="dialog"
          aria-label="NovaCare support chat"
        >
          {drawerOpen && <SupportWidget variant="drawer" onClose={closeAll} />}
        </div>
      </div>

      {voiceOpen && <VoiceCall onClose={closeAll} />}

      {/* Persistent launcher button (hidden on the /support route via CSS target) */}
      <button
        onClick={() => (drawerOpen ? closeAll() : openChat())}
        className="fixed bottom-5 right-5 z-30 flex h-14 w-14 items-center justify-center rounded-full bg-nova-600 text-white shadow-soft transition hover:bg-nova-700 data-[hide=true]:hidden"
        aria-label="Open NovaCare support"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
        </svg>
      </button>
    </Ctx.Provider>
  );
}
