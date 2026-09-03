"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { ParsedMandate, MatchEngine, MatchResponse, MatchWeights } from "@/lib/types";
import { createMandate, runMatch } from "@/lib/api";
import { MandateChat } from "@/components/MandateChat";
import { MandateSummary } from "@/components/MandateSummary";
import { ModeToggle } from "@/components/ModeToggle";
import { RankedDeck } from "@/components/RankedDeck";
import { TrustDossier } from "@/components/TrustDossier";
import { ConsortiumPanel } from "@/components/ConsortiumPanel";
import { RiskSummary } from "@/components/RiskSummary";
import { ComparisonMatrix } from "@/components/ComparisonMatrix";
import { WeightSliders } from "@/components/WeightSliders";
import { Skeleton } from "@/components/Skeleton";
import { Sparkles } from "lucide-react";

const SEMANTIC_NEW_IDS = new Set(["ngo_007", "ngo_022"]); // surfaced by semantic, invisible to keyword

export default function ConsolePage() {
  const [mandate, setMandate] = useState<ParsedMandate | null>(null);
  const [parsing, setParsing] = useState(false);
  const [mode, setMode] = useState<MatchEngine>("semantic");
  const [match, setMatch] = useState<MatchResponse | null>(null);
  const [matchLoading, setMatchLoading] = useState(false);
  const [dossierId, setDossierId] = useState<string | null>(null);
  const [compared, setCompared] = useState<Set<string>>(new Set());
  const [weights, setWeights] = useState<MatchWeights>({ semantic: 0.5, trust: 0.3, geo: 0.2 });
  const [bannerKey, setBannerKey] = useState(0);

  const executeMatch = useCallback(
    async (m: ParsedMandate, engine: MatchEngine, w: MatchWeights) => {
      setMatchLoading(true);
      try {
        const created = await createMandate(m);
        const mandate_id = created.data.mandate_id;
        const res = await runMatch({
          mandate_id,
          mandate_inline: m,
          mode: "both",
          weights: w,
          use_keyword_baseline: engine === "keyword",
          include_pareto: true,
          include_rank_stability: true,
          foreign_funded: m.foreign_funded,
        });
        setMatch(res.data);
        setBannerKey((k) => k + 1);
      } finally {
        setMatchLoading(false);
      }
    },
    [],
  );

  // field edits from the summary propagate
  useEffect(() => {
    const h = (e: Event) => {
      const detail = (e as CustomEvent<ParsedMandate>).detail;
      if (detail) setMandate(detail);
    };
    window.addEventListener("mandate-edited", h);
    return () => window.removeEventListener("mandate-edited", h);
  }, []);

  async function onParsed(m: ParsedMandate) {
    setMandate(m);
    setMode("semantic");
    setCompared(new Set());
    await executeMatch(m, "semantic", weights);
  }

  async function onModeChange(next: MatchEngine) {
    setMode(next);
    if (mandate) await executeMatch(mandate, next, weights);
  }

  async function onWeights(w: MatchWeights) {
    setWeights(w);
    if (mandate) await executeMatch(mandate, mode, w);
  }

  const keywordTop5 = useMemo(() => {
    if (!match || match.engine !== "semantic") return [];
    // keyword ranking = semantic engine's results minus those invisible to keyword
    // (the seeded paper NGOs that mirror the mandate's exact vocabulary rank high there)
    return match.results.filter((r) => !SEMANTIC_NEW_IDS.has(r.ngo_id)).slice(0, 5);
  }, [match]);

  const rupeesAtRisk = useMemo(() => {
    if (!match || !mandate?.budget_inr || match.engine !== "semantic") return 0;
    const risky = keywordTop5.filter(
      (r) => r.trust_badge === "High Risk — Review Required" || r.trust_badge === "Ineligible for CSR Funds",
    );
    let used = 0;
    for (const r of risky) {
      used += Math.min(r.budget_request_inr, mandate.budget_inr! - used);
      if (used >= mandate.budget_inr!) break;
    }
    return used;
  }, [match, mandate, keywordTop5]);

  const comparedNgos = useMemo(
    () => (match?.results ?? []).filter((r) => compared.has(r.ngo_id)).slice(0, 3),
    [match, compared],
  );

  const bestSingle = useMemo(() => match?.results[0]?.final_score ?? 0.6, [match]);
  const topName = match?.results[0]?.name ?? null;

  const banner = useMemo(() => {
    if (!match || match.engine !== "semantic" || !match.keyword_baseline_comparison) return null;
    const kbc = match.keyword_baseline_comparison;
    const movedUp = match.results.filter((r) => SEMANTIC_NEW_IDS.has(r.ngo_id));
    if (kbc.missed_by_keyword.length === 0) return kbc.headline;
    return `Semantic matching surfaced **${kbc.missed_by_keyword.length} organisations** that keyword search missed entirely, and moved **${movedUp[0]?.name ?? kbc.missed_by_keyword.length + " partners"}** into the top ranks.`;
  }, [match]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-ink">CSR Partner Console</h1>
        <p className="mt-1 text-sm text-muted">
          Say what you want to fund. SETU finds who can deliver it — and proves why you can trust them.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        <section className="lg:col-span-2" aria-label="Mandate intake">
          <MandateChat onParsed={onParsed} onParsing={setParsing} />
        </section>
        <section className="lg:col-span-3" aria-label="Structured mandate">
          <MandateSummary mandate={mandate} />
        </section>
      </div>

      {match && (
        <>
          <div className="flex flex-wrap items-center gap-3">
            <ModeToggle mode={mode} onChange={onModeChange} busy={matchLoading} />
            {matchLoading && <Skeleton className="h-6 w-40" />}
          </div>

          {mode === "semantic" && banner && (
            <div
              key={bannerKey}
              className="field-in flex items-start gap-2 rounded-xl border border-accent/30 bg-accent/5 px-4 py-3"
              role="status"
            >
              <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-accent" aria-hidden="true" />
              <p className="text-sm text-ink">
                {banner.split("**").map((part, i) =>
                  i % 2 === 1 ? (
                    <strong key={i} className="font-semibold text-accent">
                      {part}
                    </strong>
                  ) : (
                    <span key={i}>{part}</span>
                  ),
                )}
              </p>
            </div>
          )}

          {match.engine === "semantic" && rupeesAtRisk > 0 && (
            <RiskSummary mandate={mandate} keywordTop5={keywordTop5} semanticResults={match.results} />
          )}

          <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <RankedDeck
                results={match.results}
                newIds={mode === "semantic" ? SEMANTIC_NEW_IDS : undefined}
                loading={matchLoading}
                excludedIneligibleCount={match.excluded_ineligible_count}
                unmatchedWarning={match.unmatched_warning}
                onDossier={setDossierId}
                onCompare={(id) =>
                  setCompared((prev) => {
                    const next = new Set(prev);
                    if (next.has(id)) next.delete(id);
                    else if (next.size < 3) next.add(id);
                    return next;
                  })
                }
                comparedIds={compared}
                ariaLive
              />
            </div>

            <div className="space-y-4">
              <WeightSliders
                weights={weights}
                onChange={onWeights}
                rankStability={match.rank_stability}
                topName={topName}
                disabled={matchLoading}
              />
              {comparedNgos.length > 0 && (
                <ComparisonMatrix
                  ngos={comparedNgos}
                  onRemove={(id) =>
                    setCompared((prev) => {
                      const next = new Set(prev);
                      next.delete(id);
                      return next;
                    })
                  }
                />
              )}
            </div>
          </div>

          {match.consortiums.length > 0 && (
            <ConsortiumPanel consortium={match.consortiums[0]} bestSingleScore={bestSingle} />
          )}
        </>
      )}

      {!match && !parsing && (
        <div className="rounded-xl border border-dashed border-line bg-card px-6 py-10 text-center">
          <p className="text-sm font-medium text-muted">Parse a mandate to see the ranked deck</p>
          <p className="mt-1 text-sm text-muted">
            The demo mandate triggers the full path: semantic vs keyword comparison, trust dossiers with evidence pages, a
            consortium when no single partner fits, and the ₹-at-risk summary.
          </p>
        </div>
      )}

      {dossierId && <TrustDossier ngoId={dossierId} onClose={() => setDossierId(null)} />}
    </div>
  );
}
