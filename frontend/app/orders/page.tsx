"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import type { Order } from "@/lib/types";
import { npr, statusLabel, statusStyle } from "@/lib/format";
import { useSupport } from "@/components/SupportProvider";

const TIMELINE = ["processing", "shipped", "in_transit", "delivered"];

function OrdersInner() {
  const params = useSearchParams();
  const { openChat } = useSupport();
  const [id, setId] = useState(params.get("id") || "");
  const [order, setOrder] = useState<Order | null>(null);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  const lookup = async (value?: string) => {
    const target = (value ?? id).trim().toUpperCase();
    if (!target) return;
    setLoading(true);
    setErr("");
    setOrder(null);
    try {
      setOrder(await api.order(target));
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (params.get("id")) lookup(params.get("id")!);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const stageIndex = order ? TIMELINE.indexOf(order.status === "delayed" ? "in_transit" : order.status) : -1;

  return (
    <div className="container-nova max-w-2xl py-10">
      <h1 className="text-3xl font-bold">Track your order</h1>
      <p className="mt-1 text-sm text-slate-500">
        Enter an order ID (try <button className="font-mono text-nova-600" onClick={() => { setId("NS-1077"); lookup("NS-1077"); }}>NS-1077</button>,
        {" "}
        <button className="font-mono text-nova-600" onClick={() => { setId("NS-1089"); lookup("NS-1089"); }}>NS-1089</button>).
      </p>

      <div className="mt-5 flex gap-2">
        <input
          value={id}
          onChange={(e) => setId(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && lookup()}
          placeholder="NS-1077"
          className="flex-1 rounded-xl border border-slate-300 bg-white px-4 py-2.5 font-mono text-sm outline-none focus:border-nova-400 dark:border-slate-700 dark:bg-slate-900"
        />
        <button onClick={() => lookup()} className="btn-primary" disabled={loading}>
          {loading ? "…" : "Track"}
        </button>
      </div>

      {err && (
        <p className="mt-5 rounded-xl bg-rose-50 p-4 text-sm text-rose-700 dark:bg-rose-500/10">
          {err.includes("not found") ? `No order matches "${id}" in the demo system.` : err}
        </p>
      )}

      {order && (
        <div className="card mt-6 p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="font-mono text-lg font-bold">{order.id}</p>
              <p className="text-sm text-slate-500">
                {order.product_name} · qty {order.quantity} · {npr(order.total_npr)}
              </p>
            </div>
            <span className={`chip ${statusStyle(order.status)}`}>{statusLabel(order.status)}</span>
          </div>

          {order.is_demo && (
            <p className="mt-2 chip bg-amber-100 text-amber-700 dark:bg-amber-500/15">Synthetic demo order</p>
          )}

          <div className="mt-6">
            <div className="flex justify-between">
              {TIMELINE.map((stage, i) => (
                <div key={stage} className="flex flex-1 flex-col items-center text-center">
                  <div
                    className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold ${
                      i <= stageIndex
                        ? "bg-nova-600 text-white"
                        : "bg-slate-200 text-slate-400 dark:bg-slate-800"
                    }`}
                  >
                    {i + 1}
                  </div>
                  <span className="mt-1 text-[11px] text-slate-500">{statusLabel(stage)}</span>
                </div>
              ))}
            </div>
            {order.status === "cancelled" && (
              <p className="mt-3 text-center text-sm text-rose-600">This order was cancelled.</p>
            )}
          </div>

          <dl className="mt-6 grid grid-cols-2 gap-3 text-sm">
            <Row label="Ordered" value={order.ordered_at} />
            <Row label="Shipped" value={order.shipped_at} />
            <Row label="Delivered" value={order.delivered_at} />
            <Row label="Est. delivery" value={order.estimated_delivery} />
            <Row label="Location" value={order.current_location} />
            <Row label="Payment" value={order.payment_method} />
          </dl>

          {order.delay_reason && (
            <p className="mt-3 rounded-lg bg-orange-50 px-3 py-2 text-sm text-orange-700 dark:bg-orange-500/10">
              Delay: {order.delay_reason}
            </p>
          )}

          <button
            onClick={() =>
              openChat({
                prompt: `About my order ${order.id}: `,
                orderId: order.id,
                autoSend: false,
              })
            }
            className="btn-ghost mt-5 w-full"
          >
            Ask NovaCare about this order
          </button>
        </div>
      )}
    </div>
  );
}

function Row({ label, value }: { label: string; value?: string | null }) {
  if (!value) return null;
  return (
    <div className="rounded-lg border border-slate-200 px-3 py-2 dark:border-slate-800">
      <dt className="text-xs text-slate-400">{label}</dt>
      <dd className="font-medium">{value}</dd>
    </div>
  );
}

export default function OrdersPage() {
  return (
    <Suspense fallback={<div className="container-nova py-10 text-slate-400">Loading…</div>}>
      <OrdersInner />
    </Suspense>
  );
}
