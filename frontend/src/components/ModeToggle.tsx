"use client";

import type { MatchEngine } from "@/lib/types";
import clsx from "clsx";

export function ModeToggle({
  mode,
  onChange,
  busy,
}: {
  mode: MatchEngine;
  onChange: (m: MatchEngine) => void;
  busy?: boolean;
}) {
  return (
    <div className="inline-flex items-center rounded-full border border-line bg-card p-1" role="group" aria-label="Matching engine">
      {(["keyword", "semantic"] as const).map((m) => (
        <button
          key={m}
          type="button"
          onClick={() => onChange(m)}
          disabled={busy}
          aria-pressed={mode === m}
          className={clsx(
            "rounded-full px-3.5 py-1 text-xs font-medium transition-colors duration-200",
            mode === m
              ? m === "semantic"
                ? "bg-accent text-white"
                : "bg-ink text-white"
              : "text-muted hover:text-ink",
          )}
        >
          {m === "keyword" ? "Keyword search" : "Semantic matching"}
        </button>
      ))}
    </div>
  );
}
