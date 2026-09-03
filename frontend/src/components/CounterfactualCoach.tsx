"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { CounterfactualResponse, CounterfactualAction } from "@/lib/types";
import { getCounterfactual } from "@/lib/api";
import { Badge } from "./Badge";
import { Gauge } from "./Gauge";
import { Skeleton } from "./Skeleton";
import type { TrustBadgeName } from "@/lib/types";
import clsx from "clsx";

function badgeFor(score: number): TrustBadgeName {
  if (score >= 80) return "Verified Elite";
  if (score >= 60) return "Standard Audited";
  if (score >= 40) return "Verification Incomplete";
  return "High Risk — Review Required";
}

export function CounterfactualCoach({ ngoId }: { ngoId: string }) {
  const [data, setData] = useState<CounterfactualResponse | null>(null);
  const [on, setOn] = useState<Set<string>>(new Set());
  const [flipKey, setFlipKey] = useState(0);
  const prevBadge = useRef<TrustBadgeName | null>(null);

  useEffect(() => {
    let alive = true;
    setData(null);
    setOn(new Set());
    void (async () => {
      const res = await getCounterfactual(ngoId);
      if (alive) setData(res.data);
    })();
    return () => {
      alive = false;
    };
  }, [ngoId]);

  const projected = useMemo(() => {
    if (!data) return 0;
    const total = data.current + Array.from(on).reduce((s, id) => s + (data.actions.find((a) => a.action_id === id)?.delta ?? 0), 0);
    return Math.min(total, data.achievable_ceiling);
  }, [data, on]);

  const currentBadge = data ? badgeFor(projected) : null;
  useEffect(() => {
    if (currentBadge && prevBadge.current && currentBadge !== prevBadge.current) {
      setFlipKey((k) => k + 1); // trigger the badge-pulse animation
    }
    if (currentBadge) prevBadge.current = currentBadge;
  }, [currentBadge]);

  if (!data) {
    return (
      <div className="space-y-4">
        <Skeleton className="mx-auto h-44 w-44 rounded-full" />
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-12 w-full" />
      </div>
    );
  }

  const actionable = data.actions.filter((a) => a.effort_class === "actionable");
  const structural = data.actions.filter((a) => a.effort_class === "structural");
  const badge = badgeFor(projected);

  function toggle(a: CounterfactualAction) {
    setOn((prev) => {
      const next = new Set(prev);
      if (next.has(a.action_id)) next.delete(a.action_id);
      else next.add(a.action_id);
      return next;
    });
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <section className="rounded-xl border border-line bg-card p-6 text-center">
        <Gauge
          value={projected}
          ceiling={data.achievable_ceiling}
          size={200}
          label="trust score"
          color={projected >= 80 ? "#059669" : projected >= 60 ? "#D97706" : "#E11D48"}
          ariaLabel={`Trust score ${projected} of 100, achievable ceiling ${data.achievable_ceiling}`}
        />
        <div className="mt-3 flex items-center justify-center gap-3">
          <div key={flipKey} className="badge-pulse inline-block">
            <Badge badge={badge} size="md" />
          </div>
          {on.size > 0 && (
            <p className="text-sm text-muted">
              {data.current} → <span className="tabular-nums font-semibold text-ink">{projected}</span>
              {data.combined_projection != null && projected < data.achievable_ceiling && (
                <span className="text-xs"> · API projection</span>
              )}
            </p>
          )}
        </div>
        <p className="mt-2 text-xs text-slate-500">
          Faint outer arc = achievable ceiling ({data.achievable_ceiling}) — the realistic maximum with every actionable
          document supplied.
        </p>
      </section>

      <section aria-label="Improvement actions">
        <h3 className="text-sm font-semibold text-ink">Actionable now — toggle to simulate</h3>
        <ul className="mt-2 space-y-2">
          {actionable.map((a) => (
            <li key={a.action_id}>
              <label
                className={clsx(
                  "flex cursor-pointer items-start gap-3 rounded-lg border p-3 transition-colors duration-150",
                  on.has(a.action_id) ? "border-accent bg-accent/5" : "border-line bg-surface hover:border-accent/50",
                )}
              >
                <input
                  type="checkbox"
                  checked={on.has(a.action_id)}
                  onChange={() => toggle(a)}
                  className="mt-1 h-4 w-4 accent-[#1D4ED8]"
                />
                <span className="flex-1">
                  <span className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-medium text-ink">{a.label}</span>
                    <span className="tabular-nums rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-700">
                      +{a.delta} points
                    </span>
                    <span className="text-xs text-muted">effort: {a.effort}</span>
                  </span>
                  <span className="mt-1 block text-xs text-muted">{a.explanation}</span>
                  {a.threshold_crossed && (
                    <span className="mt-1 block text-xs font-medium text-accent">Crosses a badge threshold: {a.threshold_crossed}</span>
                  )}
                </span>
              </label>
            </li>
          ))}
        </ul>

        {structural.length > 0 && (
          <>
            <h3 className="mt-5 text-sm font-semibold text-muted">Structural — takes time, shown for planning</h3>
            <ul className="mt-2 space-y-2">
              {structural.map((a) => (
                <li key={a.action_id} className="rounded-lg border border-dashed border-line bg-card p-3 opacity-70">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-medium text-muted">{a.label}</span>
                    <span className="tabular-nums rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
                      +{a.delta} points
                    </span>
                    <span className="text-xs text-slate-500">structural</span>
                  </div>
                  <p className="mt-1 text-xs text-slate-500">{a.explanation}</p>
                </li>
              ))}
            </ul>
          </>
        )}
        <p className="mt-4 text-xs text-slate-500">
          Deltas are the engine&apos;s predictions (algorithm {data.algorithm_version}), not frontend arithmetic — predicted
          equals realised is asserted in the backend test suite.
        </p>
      </section>
    </div>
  );
}
