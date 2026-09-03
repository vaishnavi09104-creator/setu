"use client";

import { useEffect, useState } from "react";
import type { TrustDossier as TrustDossierData, EvidenceItem, NetworkResponse } from "@/lib/types";
import { getTrust, getNetwork } from "@/lib/api";
import { Badge } from "./Badge";
import { Gauge } from "./Gauge";
import { PillarBar } from "./PillarBar";
import { EvidenceViewer } from "./EvidenceViewer";
import { ShellNetworkGraph } from "./ShellNetworkGraph";
import { Skeleton } from "./Skeleton";
import { monthsAgo, shortId } from "@/lib/format";
import { X } from "lucide-react";

function PenaltyRow({ label, points }: { label: string; points: number }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-rose-200 bg-rose-50 px-3 py-2">
      <span className="text-sm font-medium text-rose-800">{label}</span>
      <span className="tabular-nums text-sm font-semibold text-rose-700">−{points}</span>
    </div>
  );
}

export function TrustDossier({ ngoId, onClose }: { ngoId: string; onClose: () => void }) {
  const [dossier, setDossier] = useState<TrustDossierData | null>(null);
  const [network, setNetwork] = useState<NetworkResponse | null>(null);
  const [evidence, setEvidence] = useState<EvidenceItem | null>(null);

  useEffect(() => {
    let alive = true;
    setDossier(null);
    void (async () => {
      const [t, n] = await Promise.all([getTrust(ngoId), getNetwork(ngoId)]);
      if (!alive) return;
      setDossier(t.data);
      setNetwork(n.data);
    })();
    return () => {
      alive = false;
    };
  }, [ngoId]);

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-ink/30" role="dialog" aria-modal="true" aria-label="Trust dossier">
      <div className="h-full w-full max-w-[560px] overflow-y-auto bg-surface shadow-2xl">
        <header className="sticky top-0 z-10 flex items-start gap-3 border-b border-line bg-surface px-5 py-4">
          <div className="flex-1">
            {dossier ? (
              <>
                <h2 className="text-lg font-semibold text-ink">{dossier.name}</h2>
                <div className="mt-1.5 flex items-center gap-2">
                  <Badge badge={dossier.badge} size="md" />
                  <span className="text-xs text-muted">last verified {monthsAgo(dossier.last_verified_days_ago)}</span>
                </div>
              </>
            ) : (
              <>
                <Skeleton className="h-6 w-56" />
                <Skeleton className="mt-2 h-5 w-40" />
              </>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-line text-muted hover:text-ink"
            aria-label="Close dossier"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </header>

        <div className="space-y-4 p-5">
          {dossier ? (
            <>
              <div className="flex justify-center">
                <Gauge
                  value={dossier.trust_score}
                  label="trust score"
                  ariaLabel={`Trust score ${dossier.trust_score} of 100 for ${dossier.name}`}
                  color={dossier.trust_score >= 80 ? "#059669" : dossier.trust_score >= 60 ? "#D97706" : "#E11D48"}
                />
              </div>

              <div className="space-y-2">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Pillars — click to see evidence</p>
                {dossier.pillars.map((p) => (
                  <PillarBar key={p.key} pillar={p} onEvidence={setEvidence} />
                ))}
              </div>

              {(dossier.anomaly_penalty > 0 || dossier.shell_penalty > 0) && (
                <div className="space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Penalties — applied separately</p>
                  {dossier.anomaly_penalty > 0 && <PenaltyRow label="Cohort anomaly flags" points={dossier.anomaly_penalty} />}
                  {dossier.shell_penalty > 0 && <PenaltyRow label="Shell network" points={dossier.shell_penalty} />}
                </div>
              )}

              {network?.flagged && <ShellNetworkGraph network={network} />}

              <footer className="border-t border-line pt-3 text-xs text-slate-500 tabular-nums">
                algorithm {dossier.algorithm_version} · input {shortId(dossier.input_hash)} — any score reproduces
                byte-identically from these.
              </footer>
            </>
          ) : (
            <div className="space-y-3">
              <Skeleton className="mx-auto h-40 w-40 rounded-full" />
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          )}
        </div>
      </div>

      {evidence && <EvidenceViewer item={evidence} onClose={() => setEvidence(null)} />}
    </div>
  );
}
