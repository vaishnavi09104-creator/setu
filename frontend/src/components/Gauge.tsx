"use client";

// Animated arc gauge, 0–100. `ceiling` draws a faint outer arc (achievable ceiling).
export function Gauge({
  value,
  ceiling,
  size = 160,
  label,
  color = "#1D4ED8",
  animate = true,
  ariaLabel,
}: {
  value: number;
  ceiling?: number;
  size?: number;
  label?: string;
  color?: string;
  animate?: boolean;
  ariaLabel?: string;
}) {
  const stroke = 12;
  const r = (size - stroke) / 2 - (ceiling != null ? 6 : 0);
  const c = 2 * Math.PI * r;
  const frac = Math.max(0, Math.min(100, value)) / 100;
  const dash = animate ? c * frac : c * frac;

  return (
    <div className="relative inline-flex items-center justify-center" role="img" aria-label={ariaLabel ?? `Trust score ${Math.round(value)} of 100`}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#E2E8F0" strokeWidth={stroke} />
        {ceiling != null && ceiling > value && (
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r + 6}
            fill="none"
            stroke="#94A3B8"
            strokeWidth={3}
            strokeDasharray={`${(2 * Math.PI * (r + 6) * Math.min(ceiling, 100)) / 100} ${2 * Math.PI * (r + 6)}`}
            strokeLinecap="round"
            opacity={0.5}
          />
        )}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeDasharray={`${dash} ${c}`}
          strokeLinecap="round"
          style={animate ? { transition: "stroke-dasharray 500ms ease-out" } : undefined}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="tabular-nums text-3xl font-semibold text-ink">{Math.round(value)}</span>
        {label && <span className="text-xs uppercase tracking-wide text-slate-500">{label}</span>}
      </div>
    </div>
  );
}
