"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSupport } from "./SupportProvider";

const LINKS = [
  { href: "/products", label: "Products" },
  { href: "/orders", label: "Track Order" },
  { href: "/support", label: "Support" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/about", label: "About" },
];

export function Nav() {
  const pathname = usePathname();
  const { openChat, openVoice } = useSupport();

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200/70 bg-white/80 backdrop-blur dark:border-slate-800 dark:bg-slate-950/80">
      <nav className="container-nova flex h-16 items-center justify-between gap-4">
        <Link href="/" className="flex items-center gap-2 font-bold">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-nova-600 text-white">N</span>
          <span className="text-lg">NovaStore</span>
        </Link>

        <div className="hidden items-center gap-1 md:flex">
          {LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={`rounded-lg px-3 py-2 text-sm font-medium transition ${
                pathname === l.href
                  ? "bg-nova-50 text-nova-700 dark:bg-nova-500/15 dark:text-nova-300"
                  : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              }`}
            >
              {l.label}
            </Link>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <button onClick={() => openChat()} className="btn-ghost !px-3 !py-2 text-xs sm:text-sm">
            Ask NovaCare
          </button>
          <button onClick={() => openVoice()} className="btn-primary !px-3 !py-2 text-xs sm:text-sm">
            <span className="hidden sm:inline">Call AI Support</span>
            <span className="sm:hidden">Call</span>
          </button>
        </div>
      </nav>
    </header>
  );
}
