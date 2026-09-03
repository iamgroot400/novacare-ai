import type {
  AppConfig,
  Conversation,
  DashboardData,
  Order,
  Product,
  Ticket,
} from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";
export const VOICE_BASE =
  process.env.NEXT_PUBLIC_VOICE_URL?.replace(/\/$/, "") || "http://localhost:8080";

async function j<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  base: API_BASE,
  voiceBase: VOICE_BASE,

  async config(): Promise<AppConfig> {
    return j(await fetch(`${API_BASE}/api/config`, { cache: "no-store" }));
  },
  async products(params?: { category?: string; q?: string; max_price?: number }): Promise<Product[]> {
    const qs = new URLSearchParams();
    if (params?.category) qs.set("category", params.category);
    if (params?.q) qs.set("q", params.q);
    if (params?.max_price) qs.set("max_price", String(params.max_price));
    return j(await fetch(`${API_BASE}/api/products?${qs}`, { cache: "no-store" }));
  },
  async product(id: string): Promise<Product> {
    return j(await fetch(`${API_BASE}/api/products/${id}`, { cache: "no-store" }));
  },
  async buyDemo(productId: string): Promise<Order> {
    return j(
      await fetch(`${API_BASE}/api/orders/demo`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ product_id: productId }),
      }),
    );
  },
  async order(id: string): Promise<Order> {
    return j(await fetch(`${API_BASE}/api/orders/${encodeURIComponent(id)}`, { cache: "no-store" }));
  },
  async ticket(id: string): Promise<Ticket> {
    return j(await fetch(`${API_BASE}/api/tickets/${encodeURIComponent(id)}`, { cache: "no-store" }));
  },
  async dashboard(): Promise<DashboardData> {
    return j(await fetch(`${API_BASE}/api/dashboard`, { cache: "no-store" }));
  },
  async createConversation(channel: "chat" | "voice" = "chat", context: Record<string, unknown> = {}): Promise<Conversation> {
    return j(
      await fetch(`${API_BASE}/api/conversations`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ channel, context }),
      }),
    );
  },
  async getConversation(id: string): Promise<Conversation> {
    return j(await fetch(`${API_BASE}/api/conversations/${id}`, { cache: "no-store" }));
  },
  async sendMessage(id: string, content: string, channel: "chat" | "voice" = "chat") {
    return j<{ reply: string; pending_action: unknown; conversation: Conversation }>(
      await fetch(`${API_BASE}/api/conversations/${id}/message`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ content, channel }),
      }),
    );
  },
  async approve(id: string) {
    return j<{ ok: boolean; reply: string; conversation: Conversation }>(
      await fetch(`${API_BASE}/api/conversations/${id}/approve`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({}),
      }),
    );
  },
  async reject(id: string) {
    return j<{ ok: boolean; reply: string; conversation: Conversation }>(
      await fetch(`${API_BASE}/api/conversations/${id}/reject`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({}),
      }),
    );
  },
};

export function wsUrl(conversationId: string): string {
  const base = API_BASE.replace(/^http/, "ws");
  return `${base}/api/conversations/${conversationId}/ws`;
}
