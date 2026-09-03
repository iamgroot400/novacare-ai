"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import type { Product } from "@/lib/types";
import { ProductCard } from "@/components/ProductCard";

const CATEGORIES = ["All", "Audio", "Wearables", "Computing", "Accessories"];

function ProductsInner() {
  const params = useSearchParams();
  const [products, setProducts] = useState<Product[]>([]);
  const [q, setQ] = useState("");
  const [cat, setCat] = useState(params.get("category") || "All");
  const [maxPrice, setMaxPrice] = useState<number | "">("");
  const [err, setErr] = useState("");

  useEffect(() => {
    api.products().then(setProducts).catch((e) => setErr(e.message));
  }, []);

  const filtered = useMemo(() => {
    return products.filter((p) => {
      if (cat !== "All" && p.category !== cat) return false;
      if (maxPrice !== "" && p.price_npr > Number(maxPrice)) return false;
      if (q) {
        const hay = `${p.name} ${p.description} ${p.features.join(" ")}`.toLowerCase();
        if (!hay.includes(q.toLowerCase())) return false;
      }
      return true;
    });
  }, [products, cat, maxPrice, q]);

  return (
    <div className="container-nova py-10">
      <h1 className="text-3xl font-bold">All products</h1>
      <p className="mt-1 text-sm text-slate-500">{products.length} Nova-branded products in the demo catalogue.</p>

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search products…"
          className="w-full max-w-xs rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-nova-400 dark:border-slate-700 dark:bg-slate-900"
        />
        <div className="flex flex-wrap gap-1.5">
          {CATEGORIES.map((c) => (
            <button
              key={c}
              onClick={() => setCat(c)}
              className={`chip ${
                cat === c
                  ? "bg-nova-600 text-white"
                  : "border border-slate-300 bg-white text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
              }`}
            >
              {c}
            </button>
          ))}
        </div>
        <select
          value={maxPrice}
          onChange={(e) => setMaxPrice(e.target.value ? Number(e.target.value) : "")}
          className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
        >
          <option value="">Any price</option>
          <option value="3000">Under NPR 3,000</option>
          <option value="5000">Under NPR 5,000</option>
          <option value="8000">Under NPR 8,000</option>
          <option value="12000">Under NPR 12,000</option>
        </select>
      </div>

      {err && <p className="mt-6 text-sm text-rose-600">Could not load products: {err}</p>}

      <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {filtered.map((p) => (
          <ProductCard key={p.id} product={p} />
        ))}
      </div>
      {!filtered.length && !err && <p className="mt-10 text-center text-slate-400">No products match those filters.</p>}
    </div>
  );
}

export default function ProductsPage() {
  return (
    <Suspense fallback={<div className="container-nova py-10 text-slate-400">Loading…</div>}>
      <ProductsInner />
    </Suspense>
  );
}
