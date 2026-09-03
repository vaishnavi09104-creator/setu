import { BADGE_STYLES } from "@/lib/colors";
import type { TrustBadgeName } from "@/lib/types";
import clsx from "clsx";

export function Badge({ badge, size = "sm" }: { badge: TrustBadgeName; size?: "sm" | "md" }) {
  const s = BADGE_STYLES[badge];
  const ineligible = badge === "Ineligible for CSR Funds";
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full border font-medium",
        size === "sm" ? "px-2.5 py-0.5 text-xs" : "px-3.5 py-1 text-sm",
        s.bg, s.text, s.border,
        ineligible && "line-through decoration-rose-400 decoration-2"
      )}
    >
      {s.label}
    </span>
  );
}
