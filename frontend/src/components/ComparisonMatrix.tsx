"use client";

import type { MatchResult } from "@/lib/types";
import { Badge } from "./Badge";
import { X, GitCompare } from "lucide-react";

export function ComparisonMatrix({
  ngos,
  onRemove,
}: {
  ngos: MatchResult[];
  onRemove: (ngoId: string) => void;
}) {
  if (ngos.length === 0) return null;

  const rows: { label: string; get: (r: MatchResult) => string; best?: (r: MatchResult) => number; raw?: (r: MatchResult) => number }[] = [
    { label: "Composite score", get: (r) => (r.final_score * 100).toFixed(0), best: (r) => r.final_score },
    { label: "Semantic fit", get: (r) => r.semantic_score.toFixed(2), best: (r) => r.semantic_score },
    { label: "Trust score", get: (r) => `${r.trust_score}/100`, best: (r) => r.trust_score },
    { label: "Geographic fit", get: (r) => r.geo_score.toFixed(2), best: (r) => r.geo_score },
    { label: "Cost / beneficiary", get: (r) => `₹${r.cost_per_beneficiary_inr.toLocaleString("en-IN")}`, best: (r) => -r.cost_per_beneficiary_inr },
    { label: "Admin ratio", get: (r) => `${((r.admin_ratio ?? 0.12) * 100).toFixed(0)}%` },
    { label: "Evidence freshness", get: (r) => `${r.freshness_days} days` },
    { label: "Districts covered", get: (r) => r.districts_covered.join(", ") },
    { label: "Flags", get: (r) => (r.flags.length ? r.flags.join(", ").replace(/_/g, " ") : "none") },
  ];

  return (
    <section className="rounded-xl border border-line bg-card p-4" aria-label="Comparison matrix">
      <div className="flex items-center gap-2">
        <GitCompare className="h-4 w-4 text-accent" aria-hidden="true" />
        <h3 className="text-sm font-semibold text-ink">Side-by-side — the spreadsheet a CSR team builds by hand over two weeks</h3>
      </div>
      <div className="mt-3 overflow-x-auto">
        <table className="w-full min-w-[520px] text-sm">
          <caption className="sr-only">Comparison of shortlisted organisations across trust pillars, fit and cost</caption>
          <thead>
            <tr>
              <th scope="col" className="w-40" />
              {ngos.map((r) => (
                <th key={r.ngo_id} scope="col" className="p-2 text-left align-top">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="font-semibold text-ink">{r.name}</p>
                      <div className="mt-1">
                        <Badge badge={r.trust_badge} />
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => onRemove(r.ngo_id)}
                      className="rounded p-1 text-slate-400 hover:text-rose-600"
                      aria-label={`Remove ${r.name} from comparison`}
                    >
                      <X className="h-3.5 w-3.5" aria-hidden="true" />
                    </button>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const isBestRow = ngos.length > 1 && row.best != null;
              let bestIdx = -1;
              if (isBestRow) {
                const vals = ngos.map((r) => row.best!(r));
                bestIdx = vals.indexOf(Math.max(...vals));
              }
              return (
                <tr key={row.label} className="border-t border-line">
                  <th scope="row" className="p-2 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
                    {row.label}
                  </th>
                  {ngos.map((r, i) => (
                    <td
                      key={r.ngo_id}
                      className={`p-2 tabular-nums ${i === bestIdx ? "rounded bg-emerald-50 font-semibold text-emerald-800" : "text-ink"}`}
                    >
                      {row.get(r)}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
        {ngos.length < 2 && (
          <p className="mt-2 text-xs text-muted">Add another partner from the deck (up to three) to compare rows.</p>
        )}
      </div>
    </section>
  );
}
