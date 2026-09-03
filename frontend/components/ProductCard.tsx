"use client";

import Link from "next/link";
import type { Product } from "@/lib/types";
import { npr } from "@/lib/format";
import { ProductArt } from "./ProductArt";
import { useSupport } from "./SupportProvider";

export function ProductCard({ product }: { product: Product }) {
  const { openChat } = useSupport();
  return (
    <div className="card group flex flex-col overflow-hidden transition hover:-translate-y-0.5 hover:shadow-lg">
      <Link href={`/products/${product.id}`} className="block">
        <ProductArt id={product.id} category={product.category} className="h-40 w-full" />
      </Link>
      <div className="flex flex-1 flex-col gap-2 p-4">
        <div className="flex items-start justify-between gap-2">
          <div>
            <span className="chip bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400">
              {product.category}
            </span>
          </div>
          <span className="flex items-center gap-1 text-xs font-medium text-amber-500">
            ★ {product.rating.toFixed(1)}
          </span>
        </div>
        <Link href={`/products/${product.id}`} className="font-semibold hover:text-nova-600">
          {product.name}
        </Link>
        <p className="line-clamp-2 text-xs text-slate-500">{product.description}</p>
        <div className="flex flex-wrap gap-1">
          {product.features.slice(0, 3).map((f) => (
            <span key={f} className="chip bg-nova-50 text-nova-700 dark:bg-nova-500/10 dark:text-nova-300">
              {f}
            </span>
          ))}
        </div>
        <div className="mt-auto flex items-center justify-between pt-2">
          <span className="text-lg font-bold">{npr(product.price_npr)}</span>
          <span
            className={`chip ${
              product.in_stock
                ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300"
                : "bg-rose-100 text-rose-700 dark:bg-rose-500/15 dark:text-rose-300"
            }`}
          >
            {product.in_stock ? `In stock (${product.stock})` : "Out of stock"}
          </span>
        </div>
        <div className="flex gap-2 pt-1">
          <Link href={`/products/${product.id}`} className="btn-ghost flex-1 !py-2 text-xs">
            Details
          </Link>
          <button
            onClick={() => openChat({ prompt: `Tell me about the ${product.name} (${product.id}).`, autoSend: true })}
            className="btn-primary flex-1 !py-2 text-xs"
          >
            Ask NovaCare
          </button>
        </div>
      </div>
    </div>
  );
}
