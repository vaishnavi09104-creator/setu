"use client";

import { useEffect, useState } from "react";
import type { EvidenceItem } from "@/lib/types";
import { documentPageUrl } from "@/lib/api";
import { ChevronLeft, ChevronRight, Download, X } from "lucide-react";

// Evidence viewer: real rendered page image (backend) with SVG fallback beside a
// snippet callout. The callout beside a real page image is the robust choice.
export function EvidenceViewer({ item, onClose }: { item: EvidenceItem; onClose: () => void }) {
  const [page, setPage] = useState(item.page);
  const [imgError, setImgError] = useState(false);
  const fallbackSrc = `/evidence/${encodeURIComponent(item.doc_id)}_${page}.svg`;

  // preload adjacent pages
  useEffect(() => {
    const preload = (n: number) => {
      const img = new Image();
      img.src = `/evidence/${encodeURIComponent(item.doc_id)}_${n}.svg`;
    };
    preload(item.page + 1);
  }, [item.doc_id, item.page]);

  const src = imgError ? fallbackSrc : documentPageUrl(item.doc_id, page);

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-ink/40" role="dialog" aria-modal="true" aria-label="Evidence viewer">
      <div className="flex h-full w-full max-w-[720px] flex-col bg-surface shadow-2xl">
        <header className="flex items-center gap-3 border-b border-line px-4 py-3">
          <div className="min-w-0 flex-1">
            <h2 className="truncate text-sm font-semibold text-ink">{item.doc_name}</h2>
            <p className="text-xs text-muted">
              {item.kind.toUpperCase()} · page {page} · extraction confidence {Math.round(item.confidence * 100)}%
            </p>
          </div>
          <a
            href={fallbackSrc}
            download={`${item.doc_id}_${page}.svg`}
            className="inline-flex items-center gap-1 rounded-md border border-line px-2.5 py-1.5 text-xs font-medium text-muted hover:text-accent"
            aria-label="Download document page"
          >
            <Download className="h-3.5 w-3.5" aria-hidden="true" />
            Download
          </a>
          <button
            type="button"
            onClick={onClose}
            className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-line text-muted hover:text-ink"
            aria-label="Close evidence viewer"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </header>

        <div className="flex flex-1 gap-4 overflow-hidden p-4">
          <div className="flex-1 overflow-auto rounded-lg border border-line bg-card">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              key={src}
              src={src}
              alt={`Rendered page ${page} of ${item.doc_name}`}
              className="w-full"
              onError={() => setImgError(true)}
            />
          </div>
          <aside className="w-64 shrink-0 space-y-3 overflow-y-auto">
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-amber-700">Extracted snippet</p>
              <p className="mt-1.5 text-sm leading-relaxed text-amber-900">&ldquo;{item.snippet}&rdquo;</p>
              <p className="mt-2 text-[10px] text-amber-600 tabular-nums">
                char offsets [{item.char_offsets[0]}–{item.char_offsets[1]}]
              </p>
            </div>
            <p className="text-xs text-muted">
              This snippet is what the scoring engine read for the {item.kind} check. The highlighted region on the page
              is the engine&apos;s anchor.
            </p>
          </aside>
        </div>

        <footer className="flex items-center justify-between border-t border-line px-4 py-3">
          <button
            type="button"
            onClick={() => {
              setPage((p) => Math.max(1, p - 1));
              setImgError(false);
            }}
            disabled={page <= 1}
            className="inline-flex items-center gap-1 rounded-md border border-line px-3 py-1.5 text-xs font-medium text-muted enabled:hover:text-accent disabled:opacity-40"
          >
            <ChevronLeft className="h-3.5 w-3.5" aria-hidden="true" />
            Previous page
          </button>
          <span className="tabular-nums text-xs text-muted" aria-live="polite">
            page {page}
          </span>
          <button
            type="button"
            onClick={() => {
              setPage((p) => p + 1);
              setImgError(false);
            }}
            className="inline-flex items-center gap-1 rounded-md border border-line px-3 py-1.5 text-xs font-medium text-muted hover:text-accent"
          >
            Next page
            <ChevronRight className="h-3.5 w-3.5" aria-hidden="true" />
          </button>
        </footer>
      </div>
    </div>
  );
}
