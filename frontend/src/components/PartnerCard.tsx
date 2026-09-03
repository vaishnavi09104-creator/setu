"use client";

import type { MatchResult } from "@/lib/types";
import { Badge } from "./Badge";
import { formatSmart, monthsAgo } from "@/lib/format";
import { ArrowUpRight, FileSearch, GitCompare, AlertTriangle } from "lucide-react";
import clsx from "clsx";

export function PartnerCard({
  result,
  rank,
  isNew,
  onDossier,
  onCompare,
  compared,
}: {
  result: MatchResult;
  rank: number;
  isNew?: boolean;
  onDossier: () => void;
  onCompare: () => void;
  compared: boolean;
}) {
  const r = result;
  const semW = 0.5, trustW = 0.3, geoW = 0.2;
  const sem = semW * r.semantic_score;
  const trust = trustW * (r.trust_score / 100);
  const geo = geoW * r.geo_score;

  return (
    <article
      className={clsx(
        "card-move relative rounded-xl border border-line bg-surface p-4 transition-shadow duration-150 hover:shadow-md",
        isNew && "border-l-4 border-l-accent",
      )}
      aria-labelledby={`card-${r.ngo_id}-name`}
    >
      {isNew && (
        <span className="absolute -top-2 left-4 rounded-full bg-accent px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-white">
          new
        </span>
      )}
      <div className="flex items-start gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-line bg-card text-sm font-semibold text-muted" aria-label={`Rank ${rank}`}>
          {rank}
        </div>
        <div className="min-w-0 flex-1">
          <h3 id={`card-${r.ngo_id}-name`} className="truncate text-sm font-semibold text-ink">
            {r.name}
          </h3>
          <p className="text-xs text-muted">
            {r.base_district}, {r.base_state} · covers {r.districts_covered.join(", ")}
          </p>
        </div>
        <Badge badge={r.trust_badge} />
      </div>

      <div className="mt-3 flex items-end justify-between gap-4">
        <div>
          <p className="tabular-nums text-3xl font-semibold leading-none text-ink">
            {(r.final_score * 100).toFixed(0)}
            <span className="ml-1 text-sm font-normal text-muted">/ 100</span>
          </p>
          <p className="mt-1 text-xs uppercase tracking-wide text-slate-500">composite score</p>
        </div>
        {/* three-segment contribution bar — weighting visible without a legend */}
        <div className="flex-1 max-w-[280px]">
          <div className="flex h-2.5 w-full overflow-hidden rounded-full" role="img" aria-label={`Contributions: semantic ${(sem * 100).toFixed(0)}, trust ${(trust * 100).toFixed(0)}, geo ${(geo * 100).toFixed(0)}`}>
            <div className="bg-accent" style={{ width: `${sem * 100}%` }} title="semantic" />
            <div className="bg-emerald-600" style={{ width: `${trust * 100}%` }} title="trust" />
            <div className="bg-amber-500" style={{ width: `${geo * 100}%` }} title="geographic" />
          </div>
          <div className="mt-1 flex justify-between text-[10px] text-slate-500 tabular-nums">
            <span>sem {r.semantic_score.toFixed(2)}</span>
            <span>trust {r.trust_score}</span>
            <span>geo {r.geo_score.toFixed(2)}</span>
          </div>
        </div>
      </div>

      <ul className="mt-3 space-y-1.5">
        <li className="flex gap-2 text-sm text-ink">
          <ArrowUpRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-accent" aria-hidden="true" />
          {r.justification.domain_synergy}
        </li>
        <li className="flex gap-2 text-sm text-muted">
          <ArrowUpRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-600" aria-hidden="true" />
          {r.justification.scale_fit}
        </li>
        <li className="flex gap-2 text-sm text-muted">
          <ArrowUpRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-500" aria-hidden="true" />
          {r.justification.geographic_overlap}
        </li>
      </ul>

      {r.flags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {r.flags.map((f) => (
            <span key={f} className="inline-flex items-center gap-1 rounded-full border border-rose-200 bg-rose-50 px-2 py-0.5 text-[10px] font-medium text-rose-700">
              <AlertTriangle className="h-3 w-3" aria-hidden="true" />
              {f.replace(/_/g, " ")}
            </span>
          ))}
        </div>
      )}

      <div className="mt-3 flex items-center justify-between border-t border-line pt-3">
        <dl className="flex gap-4 text-xs text-muted tabular-nums">
          <div>
            <dt className="uppercase tracking-wide text-slate-400">years</dt>
            <dd className="font-medium text-ink">{r.years_active ?? 8}</dd>
          </div>
          <div>
            <dt className="uppercase tracking-wide text-slate-400">beneficiaries</dt>
            <dd className="font-medium text-ink">{(r.beneficiaries_reached ?? 42000).toLocaleString("en-IN")}</dd>
          </div>
          <div>
            <dt className="uppercase tracking-wide text-slate-400">cost / beneficiary</dt>
            <dd className="font-medium text-ink">₹{r.cost_per_beneficiary_inr.toLocaleString("en-IN")}</dd>
          </div>
          <div>
            <dt className="uppercase tracking-wide text-slate-400">request</dt>
            <dd className="font-medium text-ink">{formatSmart(r.budget_request_inr)}</dd>
          </div>
          <div>
            <dt className="uppercase tracking-wide text-slate-400">verified</dt>
            <dd className="font-medium text-ink">{monthsAgo(r.freshness_days)}</dd>
          </div>
        </dl>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={onCompare}
            aria-pressed={compared}
            className={clsx(
              "inline-flex items-center gap-1 rounded-md border px-2.5 py-1.5 text-xs font-medium transition-colors duration-150",
              compared ? "border-accent bg-accent/10 text-accent" : "border-line text-muted hover:border-accent hover:text-accent",
            )}
          >
            <GitCompare className="h-3.5 w-3.5" aria-hidden="true" />
            {compared ? "In comparison" : "Compare"}
          </button>
          <button
            type="button"
            onClick={onDossier}
            className="inline-flex items-center gap-1 rounded-md bg-accent px-2.5 py-1.5 text-xs font-medium text-white transition-opacity duration-150 hover:opacity-90"
          >
            <FileSearch className="h-3.5 w-3.5" aria-hidden="true" />
            View dossier
          </button>
        </div>
      </div>
    </article>
  );
}
