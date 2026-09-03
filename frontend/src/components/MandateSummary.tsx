"use client";

import { useEffect, useState } from "react";
import type { ParsedMandate } from "@/lib/types";
import { CONFIDENCE_STYLES } from "@/lib/colors";
import { formatSmart } from "@/lib/format";
import { CheckCircle2, Pencil, HelpCircle } from "lucide-react";
import clsx from "clsx";

const FIELD_DEFS: { key: string; label: string; fmt: (m: ParsedMandate) => string | null }[] = [
  { key: "budget_inr", label: "Budget", fmt: (m) => (m.budget_inr ? formatSmart(m.budget_inr) : null) },
  { key: "domains", label: "Domains", fmt: (m) => (m.domains.length ? m.domains.map(title).join(", ") : null) },
  { key: "districts", label: "Districts", fmt: (m) => (m.districts.length ? m.districts.join(", ") : "state-wide") },
  { key: "state", label: "State", fmt: (m) => m.state },
  {
    key: "prefers_csr_experience",
    label: "CSR experience",
    fmt: (m) => (m.prefers_csr_experience ? "prior corporate CSR experience preferred" : "no preference"),
  },
  { key: "foreign_funded", label: "Funding", fmt: (m) => (m.foreign_funded ? "foreign-sourced (FCRA needed)" : "domestic") },
];

function title(s: string) {
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function Field({
  def,
  m,
  appearIndex,
  onEdit,
}: {
  def: (typeof FIELD_DEFS)[number];
  m: ParsedMandate;
  appearIndex: number;
  onEdit: () => void;
}) {
  const value = def.fmt(m);
  const conf = m.confidence[def.key] ?? "medium";
  const low = conf === "low";
  return (
    <button
      type="button"
      onClick={onEdit}
      className={clsx(
        "field-in w-full rounded-lg border border-line bg-surface p-3 text-left transition-colors duration-150 hover:border-accent",
        low && "border-l-4 border-l-amber-500",
      )}
      style={{ animationDelay: `${appearIndex * 70}ms` }}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-wide text-slate-500">{def.label}</span>
        <div className="flex items-center gap-1.5">
          <span className={clsx("rounded-full border px-2 py-0.5 text-[10px] font-medium", CONFIDENCE_STYLES[conf])}>{conf}</span>
          <Pencil className="h-3 w-3 text-slate-400" aria-label="Edit field" />
        </div>
      </div>
      <p className={clsx("mt-1 text-sm font-medium text-ink", low && "italic text-muted")}>{value ?? "not specified"}</p>
    </button>
  );
}

// inline editor for a single field — simple text replace for the prototype
function FieldEditor({
  def,
  m,
  onDone,
}: {
  def: (typeof FIELD_DEFS)[number];
  m: ParsedMandate;
  onDone: (next: ParsedMandate) => void;
}) {
  const [v, setV] = useState(def.fmt(m) ?? "");
  return (
    <form
      className="rounded-lg border border-accent bg-surface p-3"
      onSubmit={(e) => {
        e.preventDefault();
        onDone({
          ...m,
          districts: def.key === "districts" ? v.split(",").map((s) => s.trim()).filter(Boolean) : m.districts,
          domains: def.key === "domains" ? v.toLowerCase().split(",").map((s) => s.trim().replace(/ /g, "_")).filter(Boolean) : m.domains,
          state: def.key === "state" ? v : m.state,
          budget_inr: def.key === "budget_inr" ? Number(v.replace(/[^\d]/g, "")) || m.budget_inr : m.budget_inr,
        });
      }}
    >
      <label className="text-xs uppercase tracking-wide text-slate-500" htmlFor={`edit-${def.key}`}>
        Edit {def.label}
      </label>
      <div className="mt-1 flex gap-2">
        <input
          id={`edit-${def.key}`}
          className="flex-1 rounded-md border border-line px-2 py-1.5 text-sm"
          value={v}
          onChange={(e) => setV(e.target.value)}
          autoFocus
        />
        <button type="submit" className="rounded-md bg-accent px-3 text-xs font-medium text-white" aria-label={`Save ${def.label}`}>
          Save
        </button>
      </div>
    </form>
  );
}

export function MandateSummary({ mandate }: { mandate: ParsedMandate | null }) {
  const [editing, setEditing] = useState<string | null>(null);
  const [rev, setRev] = useState(0);

  // reset stagger animation whenever a new mandate arrives
  useEffect(() => {
    setEditing(null);
  }, [mandate]);

  if (!mandate) {
    return (
      <div className="flex h-[560px] flex-col items-center justify-center rounded-xl border border-dashed border-line bg-card text-center">
        <HelpCircle className="mb-3 h-8 w-8 text-slate-300" aria-hidden="true" />
        <p className="text-sm font-medium text-muted">Structured mandate appears here</p>
        <p className="mt-1 max-w-xs text-sm text-muted">
          Type a sentence on the left or tap a preset — budget, domains, districts and preferences extract with per-field confidence.
        </p>
      </div>
    );
  }

  return (
    <div className="flex h-[560px] flex-col rounded-xl border border-line bg-card">
      <div className="flex items-center gap-2 border-b border-line px-4 py-3">
        <CheckCircle2 className="h-4 w-4 text-emerald-600" aria-hidden="true" />
        <h2 className="text-sm font-semibold text-ink">Structured mandate</h2>
        <span className="ml-auto rounded-full bg-surface px-2 py-0.5 text-[10px] font-medium text-muted">rev {rev + 1}</span>
      </div>
      <div className="flex-1 overflow-y-auto p-3">
        <div className="grid grid-cols-2 gap-2">
          {FIELD_DEFS.map((def, i) =>
            editing === def.key ? (
              <FieldEditor
                key={`${def.key}-${rev}`}
                def={def}
                m={mandate}
                onDone={(next) => {
                  setRev((r) => r + 1);
                  setEditing(null);
                  // re-render with the edited mandate — parent keeps its own copy via callback
                  mandateEdited = next;
                  window.dispatchEvent(new CustomEvent("mandate-edited", { detail: next }));
                }}
              />
            ) : (
              <Field
                key={`${def.key}-${rev}`}
                def={def}
                m={mandate}
                appearIndex={i}
                onEdit={() => setEditing(def.key)}
              />
            ),
          )}
        </div>

        {mandate.clarifying_questions.length > 0 && (
          <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3">
            <p className="text-xs font-medium uppercase tracking-wide text-amber-700">Clarifying questions</p>
            {mandate.clarifying_questions.map((q, i) => (
              <p key={i} className="mt-1.5 text-sm text-amber-900">
                {q}
              </p>
            ))}
            <div className="mt-2 flex flex-wrap gap-1.5">
              <button
                type="button"
                className="rounded-full border border-amber-300 bg-surface px-3 py-1 text-xs font-medium text-amber-800 hover:bg-amber-100"
                onClick={() => window.dispatchEvent(new CustomEvent("mandate-edited", { detail: mandate }))}
              >
                It&apos;s a preference, not a hard filter
              </button>
              <button
                type="button"
                className="rounded-full border border-amber-300 bg-surface px-3 py-1 text-xs font-medium text-amber-800 hover:bg-amber-100"
                onClick={() => window.dispatchEvent(new CustomEvent("mandate-edited", { detail: mandate }))}
              >
                Hard requirement
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// module-level hand-off for edited mandates (kept simple for the prototype)
let mandateEdited: ParsedMandate | null = null;
export function takeEditedMandate(): ParsedMandate | null {
  const m = mandateEdited;
  mandateEdited = null;
  return m;
}
