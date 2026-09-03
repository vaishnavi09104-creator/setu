"use client";

import { useEffect, useState } from "react";
import { CounterfactualCoach } from "@/components/CounterfactualCoach";
import { getNgo } from "@/lib/api";
import type { NgoProfile } from "@/lib/types";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function NgoPage({ params }: { params: { id: string } }) {
  const id = params.id;
  const [profile, setProfile] = useState<NgoProfile | null>(null);
  useEffect(() => {
    let alive = true;
    void (async () => {
      const res = await getNgo(id);
      if (alive) setProfile(res.data);
    })();
    return () => {
      alive = false;
    };
  }, [id]);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link
          href="/"
          className="inline-flex items-center gap-1 text-sm text-muted transition-colors hover:text-accent"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Back to console
        </Link>
        <span className="text-xs uppercase tracking-wide text-slate-500">NGO self-service view · role: NGO</span>
      </div>

      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-ink">{profile?.name ?? id}</h1>
        <p className="mt-1 text-sm text-muted">
          Everything the corporate console sees about you, turned into a roadmap: what to upload, how many points it is
          worth, and the badge you would earn.
        </p>
      </div>

      <CounterfactualCoach ngoId={id} />
    </div>
  );
}
