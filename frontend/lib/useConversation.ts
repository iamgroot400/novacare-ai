"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, wsUrl } from "./api";
import type { AgentEvent, ChatMessage, Conversation, PendingAction } from "./types";

type ConnState = "connecting" | "online" | "offline";

interface UseConversation {
  conversationId: string | null;
  messages: ChatMessage[];
  events: AgentEvent[];
  pending: PendingAction | null;
  busy: boolean;
  connection: ConnState;
  send: (text: string, channel?: "chat" | "voice") => Promise<void>;
  approve: () => Promise<void>;
  reject: () => Promise<void>;
  ingestExternal: (conv: Conversation) => void;
  refresh: () => Promise<void>;
  appendLocal: (role: "user" | "assistant", content: string) => void;
  reset: () => void;
}

export function useConversation(initialContext: Record<string, unknown> = {}): UseConversation {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [pending, setPending] = useState<PendingAction | null>(null);
  const [busy, setBusy] = useState(false);
  const [connection, setConnection] = useState<ConnState>("connecting");

  const wsRef = useRef<WebSocket | null>(null);
  const ctxRef = useRef(initialContext);
  const seenEvents = useRef<Set<number>>(new Set());

  const applyConversation = useCallback((conv: Conversation) => {
    setMessages(conv.messages);
    conv.events.forEach((e) => seenEvents.current.add(e.id));
    setEvents(conv.events);
    setPending(conv.pending_action ?? null);
  }, []);

  const addEvent = useCallback((e: AgentEvent) => {
    if (e.id && seenEvents.current.has(e.id)) return;
    if (e.id) seenEvents.current.add(e.id);
    setEvents((prev) => [...prev, e]);
  }, []);

  // create conversation + open websocket
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const conv = await api.createConversation("chat", ctxRef.current);
        if (cancelled) return;
        setConversationId(conv.id);
        applyConversation(conv);
        openSocket(conv.id);
      } catch {
        setConnection("offline");
      }
    })();
    return () => {
      cancelled = true;
      wsRef.current?.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const openSocket = useCallback(
    (id: string) => {
      try {
        const ws = new WebSocket(wsUrl(id));
        wsRef.current = ws;
        setConnection("connecting");
        ws.onopen = () => setConnection("online");
        ws.onclose = () => setConnection("offline");
        ws.onerror = () => setConnection("offline");
        ws.onmessage = (evt) => {
          const data = JSON.parse(evt.data);
          if (data.kind === "event") {
            addEvent(data as AgentEvent);
          } else if (data.kind === "assistant") {
            setBusy(false);
            setMessages((prev) => [
              ...prev,
              { id: `a-${Date.now()}`, role: "assistant", content: data.content },
            ]);
            setPending((data.pending_action as PendingAction) ?? null);
          } else if (data.kind === "error") {
            setBusy(false);
          }
        };
      } catch {
        setConnection("offline");
      }
    },
    [addEvent],
  );

  const send = useCallback(
    async (text: string, channel: "chat" | "voice" = "chat") => {
      if (!conversationId || !text.trim()) return;
      setBusy(true);
      setPending(null);
      setMessages((prev) => [...prev, { id: `u-${Date.now()}`, role: "user", content: text }]);

      const ws = wsRef.current;
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ kind: "message", content: text, channel }));
        return;
      }
      // REST fallback
      try {
        const res = await api.sendMessage(conversationId, text, channel);
        applyConversation(res.conversation);
      } catch (e) {
        setMessages((prev) => [
          ...prev,
          {
            id: `e-${Date.now()}`,
            role: "system",
            content: `Could not reach NovaCare: ${(e as Error).message}`,
          },
        ]);
      } finally {
        setBusy(false);
      }
    },
    [conversationId, applyConversation],
  );

  const approve = useCallback(async () => {
    if (!conversationId) return;
    setBusy(true);
    try {
      const res = await api.approve(conversationId);
      applyConversation(res.conversation);
    } finally {
      setBusy(false);
    }
  }, [conversationId, applyConversation]);

  const reject = useCallback(async () => {
    if (!conversationId) return;
    setBusy(true);
    try {
      const res = await api.reject(conversationId);
      applyConversation(res.conversation);
    } finally {
      setBusy(false);
    }
  }, [conversationId, applyConversation]);

  const ingestExternal = useCallback(
    (conv: Conversation) => {
      applyConversation(conv);
    },
    [applyConversation],
  );

  const refresh = useCallback(async () => {
    if (!conversationId) return;
    try {
      const conv = await api.getConversation(conversationId);
      applyConversation(conv);
    } catch {
      /* ignore */
    }
  }, [conversationId, applyConversation]);

  const appendLocal = useCallback((role: "user" | "assistant", content: string) => {
    setMessages((prev) => [...prev, { id: `${role[0]}-${Date.now()}-${Math.random()}`, role, content }]);
  }, []);

  const reset = useCallback(() => {
    wsRef.current?.close();
    seenEvents.current.clear();
    setMessages([]);
    setEvents([]);
    setPending(null);
    setConversationId(null);
    api.createConversation("chat", ctxRef.current).then((conv) => {
      setConversationId(conv.id);
      applyConversation(conv);
      openSocket(conv.id);
    });
  }, [applyConversation, openSocket]);

  return {
    conversationId,
    messages,
    events,
    pending,
    busy,
    connection,
    send,
    approve,
    reject,
    ingestExternal,
    refresh,
    appendLocal,
    reset,
  };
}
