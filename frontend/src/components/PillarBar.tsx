"use client";

import { useState } from "react";
import type { TrustPillar, EvidenceItem } from "@/lib/types";
import { PILLAR_COLORS } from "@/lib/colors";
import { pct } from "@/lib/format";
import { ChevronDown } from "lucide-react";
import clsx from "clsx";

export function PillarBar({
  pillar,
  onEvidence,
}: {
  pillar: TrustPillar;
  onEvidence: (e: EvidenceItem) => void;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-lg border border-line bg-surface">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="flex w-full items-center gap-3 p-3 text-left"
      >
        <div className="w-24 shrink-0">
          <p className="text-sm font-medium text-ink">{pillar.label}</p>
          <p className="text-[10px] uppercase tracking-wide text-slate-500">weight {pct(pillar.weight)}</p>
        </div>
        <div className="flex-1">
          {pillar.no_evidence ? (
            <p className="text-xs font-medium text-rose-700">
              No evidence on file — contributes 0 to this pillar
            </p>
          ) : (
            <div className="flex items-center gap-2">
              <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full transition-all duration-200"
                  style={{ width: `${pillar.effective * 100}%`, backgroundColor: PILLAR_COLORS[pillar.key] }}
                />
              </div>
              <span className="tabular-nums text-xs text-muted">{pillar.effective.toFixed(2)}</span>
            </div>
          )}
          <p className="mt-1 tabular-nums text-[10px] text-slate-500">
            raw {pillar.raw.toFixed(2)} × freshness {pillar.freshness.toFixed(2)} → contributes {pillar.contribution.toFixed(1)} pts
          </p>
        </div>
        <ChevronDown
          className={clsx("h-4 w-4 shrink-0 text-slate-400 transition-transform duration-150", open && "rotate-180")}
          aria-hidden="true"
        />
      </button>
      {open && (
        <ul className="border-t border-line p-3 space-y-1.5">
          {pillar.evidence.map((ev) => (
            <li key={ev.evidence_id}>
              <button
                type="button"
                disabled={ev.no_evidence}
                onClick={() => onEvidence(ev)}
                className={clsx(
                  "w-full rounded-md border p-2 text-left text-xs transition-colors duration-150",
                  ev.no_evidence ? "border-dashed border-line bg-card text-muted" : "border-line bg-card hover:border-accent",
                )}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium text-ink">
                    {ev.doc_name}
                    {!ev.no_evidence && <span className="font-normal text-muted"> · page {ev.page}</span>}
                  </span>
                  {!ev.no_evidence && (
                    <span className="tabular-nums text-[10px] text-slate-500">conf {Math.round(ev.confidence * 100)}%</span>
                  )}
                </div>
                {!ev.no_evidence && <p className="mt-1 italic text-muted">&ldquo;{ev.snippet}&rdquo;</p>}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
