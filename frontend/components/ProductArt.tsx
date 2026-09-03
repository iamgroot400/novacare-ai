"use client";

/** Deterministic local SVG illustration per product — no external images. */
export function ProductArt({
  id,
  category,
  className = "",
}: {
  id: string;
  category: string;
  className?: string;
}) {
  const seed = [...id].reduce((a, c) => a + c.charCodeAt(0), 0);
  const hue = (seed * 37) % 360;
  const c1 = `hsl(${hue} 85% 62%)`;
  const c2 = `hsl(${(hue + 40) % 360} 80% 48%)`;

  const shapes: Record<string, JSX.Element> = {
    Audio: (
      <>
        <rect x="58" y="44" width="24" height="44" rx="12" fill="url(#g)" />
        <rect x="118" y="44" width="24" height="44" rx="12" fill="url(#g)" />
        <path d="M60 52c0-22 80-22 80 0" stroke={c2} strokeWidth="8" fill="none" strokeLinecap="round" />
      </>
    ),
    Wearables: (
      <>
        <rect x="74" y="34" width="52" height="72" rx="16" fill="url(#g)" />
        <rect x="86" y="20" width="28" height="18" rx="6" fill={c2} />
        <rect x="86" y="102" width="28" height="18" rx="6" fill={c2} />
        <circle cx="100" cy="70" r="14" fill="#fff" opacity="0.85" />
      </>
    ),
    Computing: (
      <>
        <rect x="46" y="42" width="108" height="64" rx="8" fill="url(#g)" />
        <rect x="58" y="54" width="84" height="30" rx="4" fill="#fff" opacity="0.8" />
        <rect x="70" y="106" width="60" height="8" rx="4" fill={c2} />
      </>
    ),
    Accessories: (
      <>
        <rect x="70" y="40" width="60" height="60" rx="14" fill="url(#g)" />
        <path d="M100 40v-14M86 100l-8 14M114 100l8 14" stroke={c2} strokeWidth="8" strokeLinecap="round" />
      </>
    ),
  };

  return (
    <svg viewBox="0 0 200 140" className={className} role="img" aria-label={`${category} product illustration`}>
      <defs>
        <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor={c1} />
          <stop offset="1" stopColor={c2} />
        </linearGradient>
      </defs>
      <rect width="200" height="140" rx="16" fill={`hsl(${hue} 60% 96%)`} />
      {shapes[category] || shapes.Accessories}
    </svg>
  );
}
