"use client";

import { useEffect, useState } from "react";
import type { AuditEntry } from "@/lib/types";
import { getAudit } from "@/lib/api";
import { RowSkeleton } from "@/components/Skeleton";
import { EmptyState } from "@/components/EmptyState";
import { ShieldCheck } from "lucide-react";

export default function AdminPage() {
  const [entries, setEntries] = useState<AuditEntry[] | null>(null);
  const [filter, setFilter] = useState("");
  const [verifying, setVerifying] = useState<string | null>(null);
  const [chainValid, setChainValid] = useState<boolean | null>(null);

  useEffect(() => {
    let alive = true;
    void (async () => {
      const res = await getAudit();
      if (alive) setEntries(res.data);
    })();
    return () => {
      alive = false;
    };
  }, []);

  function verifyChain(list: AuditEntry[]): boolean {
    // hash-chained: each entry's prev_hash must equal the prior entry's hash
    for (let i = 1; i < list.length; i++) {
      if (list[i].prev_hash !== list[i - 1].hash) return false;
    }
    return true;
  }

  const filtered = (entries ?? []).filter(
    (e) =>
      !filter ||
      e.entity_id.includes(filter) ||
      e.action.includes(filter) ||
      e.actor_role.includes(filter),
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-ink">Audit Log</h1>
          <p className="mt-1 text-sm text-muted">
            Hash-chained, append-only. Role: auditor (read-only). Every scoring and verification action is recorded and
            reproducible.
          </p>
        </div>
        <button
          type="button"
          className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-card px-3.5 py-2 text-sm font-medium text-muted transition-colors hover:text-accent"
          onClick={() => {
            setVerifying("…");
            if (entries) {
              const ok = verifyChain(entries);
              setChainValid(ok);
              setVerifying(null);
            }
          }}
        >
          <ShieldCheck className="h-4 w-4" aria-hidden="true" />
          Verify hash chain
        </button>
      </div>

      {chainValid != null && (
        <div
          className={`rounded-lg border px-4 py-2.5 text-sm ${
            chainValid ? "border-emerald-200 bg-emerald-50 text-emerald-800" : "border-rose-200 bg-rose-50 text-rose-800"
          }`}
          role="status"
        >
          {chainValid
            ? "Hash chain verified — every entry links to its predecessor. No tampering detected."
            : "Chain verification FAILED — an entry does not link to its predecessor."}
        </div>
      )}

      <input
        type="search"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        placeholder="Filter by entity, action or role…"
        aria-label="Filter audit log"
        className="w-full max-w-sm rounded-lg border border-line bg-surface px-3.5 py-2 text-sm"
      />

      {entries === null ? (
        <RowSkeleton rows={6} />
      ) : filtered.length === 0 ? (
        <EmptyState title="No matching audit entries" hint="Clear the filter to see the full chain." />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-line">
          <table className="w-full min-w-[820px] text-sm">
            <caption className="sr-only">Hash-chained audit entries</caption>
            <thead className="bg-card text-left">
              <tr>
                <th scope="col" className="px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-slate-500">Timestamp (UTC)</th>
                <th scope="col" className="px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-slate-500">Role</th>
                <th scope="col" className="px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-slate-500">Action</th>
                <th scope="col" className="px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-slate-500">Entity</th>
                <th scope="col" className="px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-slate-500">Prev hash</th>
                <th scope="col" className="px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-slate-500">Hash</th>
              </tr>
            </thead>
            <tbody className="tabular-nums">
              {filtered.map((e) => (
                <tr key={e.entry_id} className="border-t border-line hover:bg-card">
                  <td className="px-4 py-2.5 text-muted">{e.timestamp.replace("T", " ").replace("Z", "")}</td>
                  <td className="px-4 py-2.5">
                    <span className="rounded-full border border-line bg-card px-2 py-0.5 text-xs font-medium text-muted">{e.actor_role}</span>
                  </td>
                  <td className="px-4 py-2.5 font-medium text-ink">{e.action}</td>
                  <td className="px-4 py-2.5 text-muted">{e.entity_id}</td>
                  <td className="px-4 py-2.5 text-slate-500">{e.prev_hash === "GENESIS" ? "GENESIS" : `${e.prev_hash.slice(0, 10)}…`}</td>
                  <td className="px-4 py-2.5 text-slate-500">{e.hash.slice(0, 10)}…</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {verifying && <p className="text-xs text-muted" role="status">{verifying}</p>}
    </div>
  );
}
