"use client";

import { useState } from "react";
import { CoverageMap } from "@/components/CoverageMap";
import { PartnerCard } from "@/components/PartnerCard";
import { EmptyState } from "@/components/EmptyState";
import { FIXTURE_MATCH_SEMANTIC } from "@/lib/fixtures";
import { MapPin } from "lucide-react";

export default function MapPage() {
  const [district, setDistrict] = useState<string | null>(null);

  const results = district
    ? FIXTURE_MATCH_SEMANTIC.results.filter((r) => r.districts_covered.includes(district))
    : null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-ink">Demand vs Supply</h1>
        <p className="mt-1 text-sm text-muted">
          Where the money is needed and where verified partners actually are. The story is the districts that are dark on
          demand and empty on supply.
        </p>
      </div>

      <CoverageMap onSelectDistrict={(d) => setDistrict((cur) => (cur === d ? null : d))} />

      {district && (
        <section aria-label={`Partners in ${district}`}>
          <h2 className="text-sm font-semibold text-ink">
            Partners covering {district}
            <span className="ml-2 text-xs font-normal text-muted">click a district again to clear the filter</span>
          </h2>
          <div className="mt-3 space-y-3">
            {results && results.length > 0 ? (
              results.map((r, i) => (
                <PartnerCard key={r.ngo_id} result={r} rank={i + 1} onDossier={() => void 0} onCompare={() => void 0} compared={false} />
              ))
            ) : (
              <EmptyState
                icon={<MapPin className="h-8 w-8" aria-hidden="true" />}
                title={`No ranked partners cover ${district}`}
                hint="This is the CSR desert pattern the map is built to surface — high need, zero verified supply."
              />
            )}
          </div>
        </section>
      )}
    </div>
  );
}
