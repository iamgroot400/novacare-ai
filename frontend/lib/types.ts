export interface Product {
  id: string;
  name: string;
  category: string;
  price_npr: number;
  stock: number;
  in_stock: boolean;
  warranty_months: number;
  rating: number;
  features: string[];
  description: string;
  warranty_note?: string;
}

export interface Order {
  id: string;
  customer_id: string;
  product_id: string;
  product_name?: string | null;
  quantity: number;
  total_npr: number;
  status: string;
  ordered_at?: string | null;
  shipped_at?: string | null;
  delivered_at?: string | null;
  estimated_delivery?: string | null;
  current_location?: string | null;
  delay_reason?: string | null;
  payment_method: string;
  is_demo?: boolean;
}

export interface Ticket {
  id: string;
  customer_id?: string | null;
  order_id?: string | null;
  subject: string;
  description: string;
  priority: string;
  status: string;
  created_at: string;
  resolution?: string;
}

export interface ChatMessage {
  id: number | string;
  role: "user" | "assistant" | "system";
  content: string;
  channel?: string;
  created_at?: string;
}

export interface AgentEvent {
  id: number;
  type: string;
  tool?: string | null;
  display: string;
  status: string;
  meta?: Record<string, unknown>;
  created_at: string;
}

export interface PendingAction {
  tool: string;
  display: string;
  summary: string;
  args: Record<string, unknown>;
}

export interface Conversation {
  id: string;
  channel: string;
  status: string;
  customer_id?: string | null;
  created_at: string;
  updated_at: string;
  context: Record<string, unknown>;
  messages: ChatMessage[];
  events: AgentEvent[];
  pending_action?: PendingAction | null;
}

export interface AppConfig {
  demo_date: string;
  ice_servers: RTCIceServer[];
  voice_url: string;
  model: string;
}

export interface DashboardData {
  label: string;
  disclaimer: string;
  totals: {
    conversations: number;
    ai_resolved: number;
    escalations: number;
    tickets_created_by_ai: number;
    returns_created_by_ai: number;
    voice_sessions: number;
    avg_response_seconds: number | null;
  };
  tickets_by_status: Record<string, number>;
  returns_by_status: Record<string, number>;
  orders_by_status: Record<string, number>;
  recent_activity: {
    conversation_id: string;
    order_id?: string | null;
    channel: string;
    summary: string;
    outcome: string;
    updated_at: string | null;
  }[];
}
