"use client";

import type { MatchWeights, RankStability } from "@/lib/types";
import { pct } from "@/lib/format";

export function WeightSliders({
  weights,
  onChange,
  rankStability,
  topName,
  disabled,
}: {
  weights: MatchWeights;
  onChange: (w: MatchWeights) => void;
  rankStability: RankStability;
  topName: string | null;
  disabled?: boolean;
}) {
  // normalise to sum 1 across the three sliders — trust gets the residual
  function setAndNormalise(changed: keyof MatchWeights, v: number) {
    const next = { ...weights, [changed]: v };
    const sum = next.semantic + next.trust + next.geo;
    const norm: MatchWeights = {
      semantic: next.semantic / sum,
      trust: next.trust / sum,
      geo: next.geo / sum,
    };
    onChange(norm);
  }

  const topId = Object.keys(rankStability)[0];
  const stability = topId ? rankStability[topId] : null;

  return (
    <section className="rounded-xl border border-line bg-card p-4" aria-label="Score weights and rank stability">
      <h3 className="text-sm font-semibold text-ink">Weights</h3>
      <div className="mt-3 space-y-3">
        {(
          [
            { key: "semantic", label: "Semantic fit" },
            { key: "trust", label: "Trust" },
            { key: "geo", label: "Geography" },
          ] as const
        ).map((s) => (
          <div key={s.key} className="flex items-center gap-3">
            <label className="w-24 text-xs font-medium text-muted" htmlFor={`slider-${s.key}`}>
              {s.label}
            </label>
            <input
              id={`slider-${s.key}`}
              type="range"
              min={0.05}
              max={0.9}
              step={0.05}
              value={weights[s.key]}
              disabled={disabled}
              onChange={(e) => setAndNormalise(s.key, Number(e.target.value))}
              className="flex-1 accent-[#1D4ED8]"
            />
            <span className="tabular-nums w-12 text-right text-xs text-ink">{pct(weights[s.key])}</span>
          </div>
        ))}
      </div>
      <p className="mt-2 text-[10px] text-slate-500">
        Normalised to sum to 100%. Weights re-run the match on release — a pharma and an infrastructure company genuinely
        should weight these differently.
      </p>

      {stability && topName && (
        <div className="mt-3 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2">
          <p className="text-xs font-semibold text-emerald-800">Rank stability — Dirichlet Monte Carlo, 500 perturbed weightings</p>
          <p className="mt-1 text-sm text-emerald-900">
            <strong className="tabular-nums">{topName}</strong> holds rank 1 in{" "}
            <strong className="tabular-nums">{pct(stability.p_top1)}</strong> of weightings and stays top-3 in{" "}
            <strong className="tabular-nums">{pct(stability.p_top3)}</strong>.
          </p>
        </div>
      )}
    </section>
  );
}
