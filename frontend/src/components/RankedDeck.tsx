"use client";

import type { MatchResult } from "@/lib/types";
import { PartnerCard } from "./PartnerCard";
import { EmptyState } from "./EmptyState";
import { CardSkeleton } from "./Skeleton";
import { SearchX } from "lucide-react";

function ExcludedStrip({ count }: { count: number }) {
  return (
    <details className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm">
      <summary className="cursor-pointer font-medium text-rose-800">
        {count} organisations excluded — Form CSR-1 not filed
      </summary>
      <p className="mt-1.5 text-xs text-rose-700">
        Under the Companies (CSR Policy) Rules, an implementing agency without valid Form CSR-1 cannot legally receive CSR
        funds. SETU excludes these outright rather than ranking them low. Expand for the full list in the live backend view.
      </p>
    </details>
  );
}

export function RankedDeck({
  results,
  newIds,
  loading,
  excludedIneligibleCount,
  unmatchedWarning,
  onDossier,
  onCompare,
  comparedIds,
  ariaLive,
}: {
  results: MatchResult[];
  newIds?: Set<string>;
  loading?: boolean;
  excludedIneligibleCount: number;
  unmatchedWarning: string | null;
  onDossier: (ngoId: string) => void;
  onCompare: (ngoId: string) => void;
  comparedIds: Set<string>;
  ariaLive?: boolean;
}) {
  if (loading) {
    return (
      <div className="space-y-3" aria-label="Ranking partners">
        <CardSkeleton />
        <CardSkeleton />
        <CardSkeleton />
      </div>
    );
  }

  if (unmatchedWarning) {
    return (
      <div className="space-y-3">
        <div className="rounded-xl border border-amber-300 bg-amber-50 p-4">
          <h3 className="text-sm font-semibold text-amber-900">No strong match found</h3>
          <p className="mt-1 text-sm text-amber-800">{unmatchedWarning}</p>
          <p className="mt-2 text-xs text-amber-700">
            A suitable partner would need: multi-domain capability (skilling + clean energy), MP west-region field presence,
            and audited financials under 24 months old. The closest organisations are shown below at low confidence.
          </p>
        </div>
        {results.map((r, i) => (
          <div key={r.ngo_id} className="opacity-70">
            <PartnerCard
              result={r}
              rank={i + 1}
              onDossier={() => onDossier(r.ngo_id)}
              onCompare={() => onCompare(r.ngo_id)}
              compared={comparedIds.has(r.ngo_id)}
            />
          </div>
        ))}
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <EmptyState
        icon={<SearchX className="h-8 w-8" aria-hidden="true" />}
        title="No results for this engine"
        hint="Keyword search found no organisations using the mandate's exact words. Switch to semantic matching to see partners that describe the same work differently."
      />
    );
  }

  return (
    <div className="space-y-3" aria-live={ariaLive ? "polite" : undefined} aria-label="Ranked partner deck">
      {excludedIneligibleCount > 0 && <ExcludedStrip count={excludedIneligibleCount} />}
      {results.map((r, i) => (
        <PartnerCard
          key={`${r.ngo_id}-${i}`}
          result={r}
          rank={i + 1}
          isNew={newIds?.has(r.ngo_id)}
          onDossier={() => onDossier(r.ngo_id)}
          onCompare={() => onCompare(r.ngo_id)}
          compared={comparedIds.has(r.ngo_id)}
        />
      ))}
    </div>
  );
}
