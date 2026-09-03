"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Product } from "@/lib/types";
import { npr } from "@/lib/format";
import { ProductArt } from "@/components/ProductArt";
import { useSupport } from "@/components/SupportProvider";

export default function ProductDetail({ params }: { params: { id: string } }) {
  const { id } = params;
  const { openChat } = useSupport();
  const [product, setProduct] = useState<Product | null>(null);
  const [err, setErr] = useState("");
  const [demoMsg, setDemoMsg] = useState("");

  useEffect(() => {
    api.product(id).then(setProduct).catch((e) => setErr(e.message));
  }, [id]);

  const buyDemo = async () => {
    if (!product) return;
    try {
      const order = await api.buyDemo(product.id);
      setDemoMsg(
        `Demo order ${order.id} created (synthetic, no payment). Track it on the Orders page or ask NovaCare about it.`,
      );
    } catch (e) {
      setDemoMsg(`Could not create demo order: ${(e as Error).message}`);
    }
  };

  if (err)
    return (
      <div className="container-nova py-16">
        <p className="text-rose-600">Product not found: {err}</p>
        <Link href="/products" className="text-nova-600">← Back to products</Link>
      </div>
    );
  if (!product) return <div className="container-nova py-16 text-slate-400">Loading…</div>;

  return (
    <div className="container-nova py-10">
      <Link href="/products" className="text-sm text-nova-600">← All products</Link>
      <div className="mt-4 grid gap-8 lg:grid-cols-2">
        <div className="card overflow-hidden">
          <ProductArt id={product.id} category={product.category} className="h-72 w-full" />
        </div>
        <div>
          <span className="chip bg-slate-100 text-slate-500 dark:bg-slate-800">{product.category}</span>
          <h1 className="mt-2 text-3xl font-bold">{product.name}</h1>
          <p className="mt-1 flex items-center gap-2 text-amber-500">★ {product.rating.toFixed(1)}
            <span className="text-slate-400">·</span>
            <span className={product.in_stock ? "text-emerald-600" : "text-rose-600"}>
              {product.in_stock ? `In stock (${product.stock})` : "Out of stock"}
            </span>
          </p>
          <p className="mt-4 text-slate-600 dark:text-slate-300">{product.description}</p>

          <div className="mt-5 grid grid-cols-2 gap-3 text-sm">
            <Info label="Price" value={npr(product.price_npr)} />
            <Info label="Warranty" value={`${product.warranty_months} months`} />
          </div>

          <div className="mt-5">
            <h3 className="text-sm font-semibold text-slate-500">Features</h3>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {product.features.map((f) => (
                <span key={f} className="chip bg-nova-50 text-nova-700 dark:bg-nova-500/10 dark:text-nova-300">
                  {f}
                </span>
              ))}
            </div>
          </div>

          <div className="mt-7 flex flex-wrap gap-3">
            <button
              onClick={() =>
                openChat({ prompt: `I'm looking at the ${product.name} (${product.id}). ${""}`, autoSend: false })
              }
              className="btn-ghost"
            >
              Ask NovaCare about this product
            </button>
            <button onClick={buyDemo} className="btn-primary">Buy Demo</button>
          </div>
          {demoMsg && <p className="mt-3 text-xs text-emerald-600">{demoMsg}</p>}
          <p className="mt-2 text-xs text-slate-400">
            &quot;Buy Demo&quot; creates a clearly-labelled synthetic order. No payment is processed.
          </p>
        </div>
      </div>
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200 p-3 dark:border-slate-800">
      <p className="text-xs text-slate-400">{label}</p>
      <p className="font-semibold">{value}</p>
    </div>
  );
}
