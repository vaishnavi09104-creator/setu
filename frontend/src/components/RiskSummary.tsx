"use client";

import type { MatchResult, ParsedMandate } from "@/lib/types";
import { formatSmart } from "@/lib/format";
import { ShieldAlert } from "lucide-react";

// "₹ at risk": mandate budget that would route to ineligible/high-risk orgs that a
// KEYWORD ranking would have placed in the top 5. 45 minutes, closing line of the pitch.
export function RiskSummary({
  mandate,
  keywordTop5,
  semanticResults,
}: {
  mandate: ParsedMandate | null;
  keywordTop5: MatchResult[];
  semanticResults: MatchResult[];
}) {
  if (!mandate?.budget_inr || keywordTop5.length === 0) return null;

  const budget = mandate.budget_inr;
  // ineligible/high-risk orgs a keyword process would have shortlisted
  const badKeywordPicks = keywordTop5.filter(
    (r) => r.trust_badge === "High Risk — Review Required" || r.trust_badge === "Ineligible for CSR Funds",
  );
  // how much of the budget those picks would have absorbed, judged by their own requests
  const atRisk = badKeywordPicks.reduce((s, r) => s + Math.min(r.budget_request_inr, budget - s), 0);

  if (atRisk <= 0) return null;

  const verifiedShare = semanticResults
    .filter((r) => r.trust_badge === "Verified Elite" || r.trust_badge === "Standard Audited")
    .slice(0, 3)
    .reduce((s, r) => s + r.budget_request_inr, 0);

  return (
    <section
      className="flex flex-wrap items-center gap-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3"
      aria-label="Rupees at risk"
    >
      <ShieldAlert className="h-5 w-5 shrink-0 text-rose-700" aria-hidden="true" />
      <p className="flex-1 text-sm text-rose-900">
        <strong className="tabular-nums font-semibold">{formatSmart(atRisk)}</strong> of this mandate would be routed to
        organisations that are ineligible or high-risk under a keyword-based process. Semantic matching routes{" "}
        {formatSmart(verifiedShare)} to verified or audited partners instead.
      </p>
      <span className="text-[10px] uppercase tracking-wide text-rose-600">seeded prototype figures</span>
    </section>
  );
}
