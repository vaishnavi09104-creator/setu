"use client";

import type { NetworkResponse } from "@/lib/types";
import { ShieldAlert } from "lucide-react";

// Hand-drawn SVG — three nodes on a circle, labelled edges. No graph library.
export function ShellNetworkGraph({ network }: { network: NetworkResponse }) {
  const n = network.members.length;
  const cx = 150, cy = 140, r = 95;
  const nodes = network.members.map((m, i) => {
    const a = (2 * Math.PI * i) / n - Math.PI / 2;
    return { ...m, x: cx + r * Math.cos(a), y: cy + r * Math.sin(a) };
  });
  const mid = { x: cx, y: cy };
  const edgeLabels = network.shared_identifier_types;

  return (
    <section className="rounded-xl border border-rose-300 bg-rose-50 p-4" aria-label="Linked-entity network detected">
      <div className="flex items-center gap-2">
        <ShieldAlert className="h-5 w-5 text-rose-700" aria-hidden="true" />
        <h3 className="text-sm font-semibold text-rose-900">Linked-entity network detected</h3>
      </div>

      <div className="mt-3 flex flex-col items-center gap-4 sm:flex-row">
        <svg
          viewBox="0 0 300 280"
          className="w-[300px] shrink-0"
          role="img"
          aria-label={`Graph of ${n} organisations sharing: ${edgeLabels.join(", ")}`}
        >
          {/* edges to hub */}
          {nodes.map((node) => (
            <line key={`e-${node.ngo_id}`} x1={node.x} y1={node.y} x2={mid.x} y2={mid.y} stroke="#E11D48" strokeWidth="1.5" />
          ))}
          {/* edge labels around the hub */}
          {edgeLabels.map((lbl, i) => {
            const a = (2 * Math.PI * i) / edgeLabels.length - Math.PI / 2;
            const lx = mid.x + 46 * Math.cos(a);
            const ly = mid.y + 46 * Math.sin(a);
            return (
              <text key={lbl} x={lx} y={ly} textAnchor="middle" dominantBaseline="middle" fontSize="9" fill="#9F1239" fontWeight="600">
                {lbl}
              </text>
            );
          })}
          {/* hub */}
          <circle cx={mid.x} cy={mid.y} r={14} fill="#E11D48" />
          <text x={mid.x} y={mid.y} textAnchor="middle" dominantBaseline="middle" fontSize="8" fill="#fff" fontWeight="700">
            SHARED
          </text>
          {/* member nodes */}
          {nodes.map((node) => (
            <g key={node.ngo_id}>
              <circle cx={node.x} cy={node.y} r={30} fill="#FFFFFF" stroke="#E11D48" strokeWidth="2" />
              <text x={node.x} y={node.y - 4} textAnchor="middle" fontSize="8.5" fill="#9F1239" fontWeight="600">
                {node.name.length > 22 ? node.name.slice(0, 20) + "…" : node.name}
              </text>
              <text x={node.x} y={node.y + 8} textAnchor="middle" fontSize="7.5" fill="#64748B">
                {node.base_district}
              </text>
            </g>
          ))}
        </svg>

        <p className="text-sm leading-relaxed text-rose-900">{network.explanation}</p>
      </div>

      <p className="mt-3 border-t border-rose-200 pt-2 text-xs font-medium text-rose-700">
        Flagged for human review — not a fraud determination.
      </p>
    </section>
  );
}
