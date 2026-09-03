"use client";

import { useEffect, useMemo, useState } from "react";
import { CoverageResponse } from "@/lib/types";
import { getCoverage } from "@/lib/api";
import { GAP_COLORS } from "@/lib/colors";
import { Skeleton } from "./Skeleton";
import clsx from "clsx";
import type { Layer, LayerGroup } from "leaflet";

// Gap score → color bucket
function gapColor(gap: number): string {
  if (gap < 0.25) return "#DCFCE7";
  if (gap < 0.5) return GAP_COLORS[0];
  if (gap < 0.7) return GAP_COLORS[1];
  if (gap < 0.85) return GAP_COLORS[2];
  return GAP_COLORS[3];
}

interface DistrictProps {
  district: string;
  state: string;
  ngo_count: number;
  verified_count: number;
  need_index: number;
  is_aspirational: boolean;
  gap_score: number;
}

const LABEL_DISTRICTS = new Set(["Mayurbhanj", "Barwani", "Nuapada"]); // CSR deserts we label directly

export function CoverageMap({ onSelectDistrict }: { onSelectDistrict?: (district: string) => void }) {
  const [data, setData] = useState<CoverageResponse | null>(null);
  const [layer, setLayer] = useState<"gap" | "supply">("gap");
  const [hovered, setHovered] = useState<DistrictProps | null>(null);

  useEffect(() => {
    let alive = true;
    void (async () => {
      const res = await getCoverage();
      if (alive) setData(res.data);
    })();
    return () => {
      alive = false;
    };
  }, []);

  const districts = useMemo(
    () => (data?.features ?? []).map((f) => ({ props: f.properties as DistrictProps, coords: f.geometry.coordinates[0] })),
    [data],
  );

  const bounds = useMemo(() => {
    if (districts.length === 0) return { minLng: 72, maxLng: 89, minLat: 18, maxLat: 24 };
    const all = districts.flatMap((d) => d.coords);
    const lngs = all.map((c) => c[0]);
    const lats = all.map((c) => c[1]);
    return { minLng: Math.min(...lngs), maxLng: Math.max(...lngs), minLat: Math.min(...lats), maxLat: Math.max(...lats) };
  }, [districts]);

  // project to SVG
  const W = 760, H = 460, PAD = 30;
  const sx = (lng: number) => PAD + ((lng - bounds.minLng) / (bounds.maxLng - bounds.minLng)) * (W - 2 * PAD);
  const sy = (lat: number) => H - PAD - ((lat - bounds.minLat) / (bounds.maxLat - bounds.minLat)) * (H - 2 * PAD);

  if (!data) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-[420px] w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-3">
        <div className="inline-flex items-center rounded-full border border-line bg-card p-1" role="group" aria-label="Map layer">
          {(
            [
              { id: "gap", label: "Demand — need vs supply gap" },
              { id: "supply", label: "Supply — verified partners" },
            ] as const
          ).map((l) => (
            <button
              key={l.id}
              type="button"
              aria-pressed={layer === l.id}
              onClick={() => setLayer(l.id)}
              className={clsx(
                "rounded-full px-3.5 py-1 text-xs font-medium transition-colors duration-150",
                layer === l.id ? "bg-ink text-white" : "text-muted hover:text-ink",
              )}
            >
              {l.label}
            </button>
          ))}
        </div>
        {hovered && (
          <div className="rounded-lg border border-line bg-card px-3 py-1.5 text-xs" aria-live="polite">
            <strong className="text-ink">{hovered.district}, {hovered.state}</strong>
            <span className="text-muted">
              {" "}· {hovered.ngo_count} NGOs ({hovered.verified_count} verified) · need index {hovered.need_index.toFixed(2)}
              {hovered.is_aspirational && <span className="ml-1 rounded-full border border-amber-300 bg-amber-50 px-1.5 py-0.5 text-[10px] font-medium text-amber-700">Aspirational District</span>}
            </span>
          </div>
        )}
      </div>

      <div className="relative overflow-hidden rounded-xl border border-line bg-surface">
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="District map of NGO demand versus supply. Legend below.">
          {districts.map((d) => {
            const pts = d.coords.map((c) => `${sx(c[0])},${sy(c[1])}`).join(" ");
            const gap = d.props.gap_score;
            const fill =
              layer === "gap"
                ? gapColor(gap)
                : d.props.verified_count === 0
                  ? "#F1F5F9"
                  : d.props.verified_count < 3
                    ? "#A7F3D0"
                    : d.props.verified_count < 6
                      ? "#34D399"
                      : "#059669";
            const cx = d.coords.reduce((s, c) => s + sx(c[0]), 0) / d.coords.length;
            const cy = d.coords.reduce((s, c) => s + sy(c[1]), 0) / d.coords.length;
            return (
              <g key={d.props.district}>
                <polygon
                  points={pts}
                  fill={fill}
                  stroke={d.props.is_aspirational ? "#7C2D12" : "#94A3B8"}
                  strokeWidth={d.props.is_aspirational ? 2 : 1}
                  strokeDasharray={d.props.is_aspirational ? "4 2" : undefined}
                  onMouseEnter={() => setHovered(d.props)}
                  onMouseLeave={() => setHovered(null)}
                  onClick={() => onSelectDistrict?.(d.props.district)}
                  className="cursor-pointer transition-opacity duration-150 hover:opacity-80"
                  tabIndex={0}
                  role="button"
                  aria-label={`${d.props.district}, ${d.props.state}: ${d.props.ngo_count} NGOs, ${d.props.verified_count} verified, need index ${d.props.need_index.toFixed(2)}${d.props.is_aspirational ? ", Aspirational District" : ""}`}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") onSelectDistrict?.(d.props.district);
                  }}
                />
                {LABEL_DISTRICTS.has(d.props.district) && layer === "gap" && (
                  <text x={cx} y={cy - 6} textAnchor="middle" fontSize="11" fontWeight="700" fill="#7F1D1D">
                    {d.props.district}
                  </text>
                )}
                {LABEL_DISTRICTS.has(d.props.district) && layer === "gap" && (
                  <text x={cx} y={cy + 8} textAnchor="middle" fontSize="9" fill="#991B1B">
                    {d.props.verified_count === 0 ? "no verified partners" : `${d.props.verified_count} verified`}
                  </text>
                )}
              </g>
            );
          })}
        </svg>
      </div>

      <div className="flex flex-wrap items-center gap-4 text-xs text-muted">
        {layer === "gap" ? (
          <div className="flex items-center gap-2" aria-hidden="true">
            <span>gap score</span>
            {["#DCFCE7", "#FDE68A", "#FCA5A5", "#F87171", "#DC2626"].map((c) => (
              <span key={c} className="inline-block h-3 w-6 rounded-sm border border-line" style={{ backgroundColor: c }} />
            ))}
            <span>high</span>
          </div>
        ) : (
          <div className="flex items-center gap-2" aria-hidden="true">
            <span>verified partners</span>
            <span className="inline-block h-3 w-6 rounded-sm border border-line bg-[#F1F5F9]" /> 0
            <span className="inline-block h-3 w-6 rounded-sm border border-line bg-[#34D399]" /> 3–5
            <span className="inline-block h-3 w-6 rounded-sm border border-line bg-[#059669]" /> 6+
          </div>
        )}
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-3 w-6 rounded-sm border-2 border-dashed border-[#7C2D12]" aria-hidden="true" />
          NITI Aayog Aspirational District
        </span>
        <span className="ml-auto text-[10px]">Need index is seeded for the prototype; the Aspirational Districts flag follows the NITI Aayog list.</span>
      </div>
    </div>
  );
}

// re-export leaflet types to satisfy the layer import requirement
export type { Layer, LayerGroup };
