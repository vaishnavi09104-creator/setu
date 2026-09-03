"use client";

import { useEffect, useState } from "react";
import { subscribeNetState } from "@/lib/api";
import clsx from "clsx";

export function LatencyBadge() {
  const [state, setState] = useState<{ offline: boolean; lastLatencyMs: number | null; source: string | null }>({
    offline: false,
    lastLatencyMs: null,
    source: null,
  });

  useEffect(() => {
    const unsub = subscribeNetState(setState);
    return () => {
      unsub();
    };
  }, []);

  return (
    <div className="flex items-center gap-2" role="status" aria-live="polite">
      {state.offline ? (
        <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-300 bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-700">
          <span className="h-1.5 w-1.5 rounded-full bg-amber-500" aria-hidden="true" />
          offline — serving captured responses
        </span>
      ) : state.source === "live" ? (
        <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-700">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" aria-hidden="true" />
          live API
        </span>
      ) : null}
      {state.lastLatencyMs != null && (
        <span
          className={clsx(
            "tabular-nums inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium",
            state.source === "live" ? "border-line bg-card text-muted" : "border-line bg-card text-muted",
          )}
        >
          48 NGOs ranked in {Math.round(state.lastLatencyMs)} ms
        </span>
      )}
    </div>
  );
}
