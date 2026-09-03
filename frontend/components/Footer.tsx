export function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white py-8 text-sm dark:border-slate-800 dark:bg-slate-950">
      <div className="container-nova flex flex-col items-center justify-between gap-3 sm:flex-row">
        <p className="text-slate-500">
          © {new Date().getFullYear()} NovaStore (fictional). Built to demo NovaCare AI.
        </p>
        <p className="rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700 dark:bg-amber-500/10 dark:text-amber-300">
          Demo only — no real products, orders, or payments.
        </p>
      </div>
    </footer>
  );
}
