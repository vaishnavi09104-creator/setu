import type { TrustBadgeName } from "./types";

export const BADGE_STYLES: Record<TrustBadgeName, { bg: string; text: string; border: string; label: string }> = {
  "Verified Elite": {
    bg: "bg-emerald-50",
    text: "text-emerald-700",
    border: "border-emerald-200",
    label: "Verified Elite",
  },
  "Standard Audited": {
    bg: "bg-amber-50",
    text: "text-amber-700",
    border: "border-amber-200",
    label: "Standard Audited",
  },
  "Verification Incomplete": {
    bg: "bg-slate-100",
    text: "text-slate-600",
    border: "border-slate-300",
    label: "Verification Incomplete",
  },
  "High Risk — Review Required": {
    bg: "bg-rose-50",
    text: "text-rose-700",
    border: "border-rose-200",
    label: "High Risk — Review Required",
  },
  "Ineligible for CSR Funds": {
    bg: "bg-rose-50",
    text: "text-rose-900",
    border: "border-rose-300",
    label: "Ineligible for CSR Funds",
  },
};

export function badgeClass(badge: TrustBadgeName): string {
  const s = BADGE_STYLES[badge];
  return `${s.bg} ${s.text} ${s.border}`;
}

export const CONFIDENCE_STYLES: Record<string, string> = {
  high: "bg-emerald-100 text-emerald-700 border-emerald-200",
  medium: "bg-amber-100 text-amber-700 border-amber-200",
  low: "bg-rose-100 text-rose-700 border-rose-200",
};

// member colors for consortium coverage segments / budget donut
export const MEMBER_COLORS = ["#1D4ED8", "#059669", "#D97706"];

// choropleth palette for gap_score (demand layer)
export const GAP_COLORS = ["#FDE68A", "#FCA5A5", "#F87171", "#DC2626"];
export const ASPIRATIONAL_STYLE = { color: "#7C2D12", weight: 2, dashArray: "4 2" };

export const PILLAR_COLORS: Record<string, string> = {
  compliance: "#1D4ED8",
  financial: "#059669",
  operational: "#D97706",
  external: "#64748B",
};
