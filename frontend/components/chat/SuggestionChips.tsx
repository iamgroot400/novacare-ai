"use client";

export const DEMO_QUESTIONS = [
  "Where is order NS-1077?",
  "Why is NS-1089 delayed?",
  "Can I return NS-1042?",
  "Can I return NS-1033?",
  "My NovaPods Pro keep disconnecting.",
  "Recommend headphones under Rs 7,000 with ANC.",
  "Recommend a keyboard under Rs 8,000.",
  "I want to speak to a human.",
];

export function SuggestionChips({
  onPick,
  compact = false,
}: {
  onPick: (q: string) => void;
  compact?: boolean;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {(compact ? DEMO_QUESTIONS.slice(0, 4) : DEMO_QUESTIONS).map((q) => (
        <button
          key={q}
          onClick={() => onPick(q)}
          className="chip border border-slate-300 bg-white text-slate-600 transition hover:border-nova-400 hover:text-nova-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:border-nova-500"
        >
          {q}
        </button>
      ))}
    </div>
  );
}
