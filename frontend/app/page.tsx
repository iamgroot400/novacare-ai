"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Product } from "@/lib/types";
import { ProductCard } from "@/components/ProductCard";
import { useSupport } from "@/components/SupportProvider";

const SECTIONS = ["Featured", "Audio", "Wearables", "Computing", "Accessories"];

export default function HomePage() {
  const { openChat, openVoice } = useSupport();
  const [products, setProducts] = useState<Product[]>([]);
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .products()
      .then(setProducts)
      .catch((e) => setErr(e.message));
  }, []);

  const byCategory = (c: string) =>
    c === "Featured"
      ? [...products].sort((a, b) => b.rating - a.rating).slice(0, 4)
      : products.filter((p) => p.category === c).slice(0, 4);

  return (
    <div>
      <section className="gradient-hero">
        <div className="container-nova grid gap-10 py-16 lg:grid-cols-2 lg:py-24">
          <div className="flex flex-col justify-center">
            <span className="chip w-fit bg-nova-100 text-nova-700 dark:bg-nova-500/15 dark:text-nova-300">
              Nepal-based electronics · fictional demo
            </span>
            <h1 className="mt-4 text-4xl font-extrabold tracking-tight sm:text-5xl lg:text-6xl">
              NovaStore
            </h1>
            <p className="mt-3 text-xl text-slate-600 dark:text-slate-300">Technology made simpler.</p>
            <p className="mt-4 max-w-md text-slate-500">
              Browse the catalogue, track an order, or talk to <strong>NovaCare AI</strong> — an
              agentic support agent that actually checks orders, policies and creates tickets, by
              chat or in-browser voice.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link href="/products" className="btn-primary">
                Shop Products
              </Link>
              <button onClick={() => openChat()} className="btn-ghost">
                Ask NovaCare
              </button>
              <button onClick={() => openVoice()} className="btn bg-slate-900 text-white hover:bg-slate-800 dark:bg-white dark:text-slate-900">
                🎙️ Call AI Support
              </button>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            {byCategory("Featured").map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </div>
      </section>

      <div className="container-nova space-y-14 py-14">
        {err && (
          <p className="rounded-xl bg-rose-50 p-4 text-sm text-rose-700 dark:bg-rose-500/10">
            Could not load products from the API ({err}). Is the backend running on{" "}
            {api.base}?
          </p>
        )}
        {SECTIONS.filter((s) => s !== "Featured").map((section) => {
          const items = byCategory(section);
          if (!items.length) return null;
          return (
            <section key={section}>
              <div className="mb-5 flex items-end justify-between">
                <h2 className="text-2xl font-bold">{section}</h2>
                <Link href={`/products?category=${section}`} className="text-sm font-medium text-nova-600">
                  View all →
                </Link>
              </div>
              <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
                {items.map((p) => (
                  <ProductCard key={p.id} product={p} />
                ))}
              </div>
            </section>
          );
        })}

        <section className="card grid gap-6 p-8 sm:grid-cols-3">
          {[
            ["Checks real records", "NovaCare queries the actual orders, products and tickets database — every activity line is a real tool call."],
            ["Confirms writes", "Returns and support tickets need your explicit approval before anything is created."],
            ["Chat or voice", "The same agent, same conversation — switch between typing and an in-browser voice call anytime."],
          ].map(([t, d]) => (
            <div key={t}>
              <h3 className="font-semibold text-nova-600">{t}</h3>
              <p className="mt-1 text-sm text-slate-500">{d}</p>
            </div>
          ))}
        </section>
      </div>
    </div>
  );
}
