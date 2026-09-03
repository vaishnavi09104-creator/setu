"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LatencyBadge } from "./LatencyBadge";
import clsx from "clsx";

const NAV = [
  { href: "/", label: "Console" },
  { href: "/map", label: "Demand vs Supply" },
  { href: "/ngo/ngo_007", label: "NGO View" },
  { href: "/admin", label: "Audit Log" },
];

export function Header() {
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-surface/95 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-7xl items-center gap-6 px-6">
        <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight text-ink">
          <span className="flex h-7 w-7 items-center justify-center rounded-md bg-accent text-sm font-bold text-white">S</span>
          SETU
        </Link>
        <nav className="flex items-center gap-1" aria-label="Main navigation">
          {NAV.map((item) => {
            const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href.split("/").slice(0, 2).join("/"));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  "rounded-md px-3 py-1.5 text-sm transition-colors duration-150",
                  active ? "bg-card font-medium text-accent" : "text-muted hover:bg-card hover:text-ink",
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="ml-auto flex items-center gap-3">
          <span className="hidden items-center gap-1.5 rounded-full border border-line bg-card px-2.5 py-0.5 text-xs font-medium text-muted md:inline-flex">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" aria-hidden="true" />
            setu-1.0.0
          </span>
          <LatencyBadge />
        </div>
      </div>
    </header>
  );
}
