"""app.services.trust — evidence assembly + the ONE trust function.

Design rule (04-TASK-B §B7, non-negotiable): `compute_trust` is PURE and is
the ONLY place trust arithmetic exists. We import it from setu_ml (Task A
shipped it as the shared reference implementation) and this file's job is
purely: load evidence from SQLite → build ComplianceEvidence → call it →
persist pillars to compliance_audit. One function, two callers (scoring and
counterfactual) — that is what stops the on-stage contradiction.
"""
from __future__ import annotations

from typing import Any

from setu_ml.trust import compute_trust as _compute_trust
from setu_ml.types import (
    AnomalyReport,
    ComplianceEvidence,
    EvidenceRef,
    NgoProfile,
    ShellNetworkInfo,
    TrustBadge,
    TrustBreakdown,
)

from .. import db

# The imported pure function is the single source of trust arithmetic.
compute_trust = _compute_trust

PILLAR_LABELS = {
    "compliance": "Compliance",
    "financial": "Financial Discipline",
    "operational": "Operational Track Record",
    "external": "External Verification",
}

FRESHNESS_MONTHS_DIV = 30


def ngo_profile_from_row(row: dict) -> NgoProfile:
    """SQLite row (with nested `data`) → setu_ml NgoProfile for compute_trust."""
    d = row["data"] if isinstance(row.get("data"), dict) else row
    trust = d.get("trust", {})
    return NgoProfile(
        ngo_id=d["ngo_id"],
        name=d.get("name", ""),
        primary_domain=d.get("primary_domain", "education"),
        secondary_domains=d.get("secondary_domains", []),
        districts_covered=d.get("districts_covered", []),
        base_district=d.get("base_district", ""),
        base_state=d.get("base_state", ""),
        proposal_text=d.get("proposal_text", ""),
        budget_request_inr=d.get("budget_request_inr", 0),
        financials=d.get("financials"),
        track_record=d.get("track_record"),
        trust_score=int(trust.get("score", 0) or 0),
        trust_badge=TrustBadge(trust.get("badge", "Verification Incomplete"))
        if trust.get("badge") else TrustBadge.INCOMPLETE,
        status=d.get("status", "ACTIVE"),
        freshness_days=int(trust.get("freshness_days", 0) or 0),
    )


def evidence_from_row(row: dict) -> ComplianceEvidence:
    """SQLite NGO document → ComplianceEvidence with anchored refs."""
    d = row["data"] if isinstance(row.get("data"), dict) else row
    ev = d.get("evidence", {})  # seeded/derived evidence map
    out = ComplianceEvidence(ngo_id=d.get("ngo_id", ""))
    for key, ref in ev.items():
        if isinstance(ref, dict):
            setattr(out, key, EvidenceRef.model_validate(ref))
    return out


def anomaly_for(ngo_row: dict, all_rows: list[dict]) -> AnomalyReport | None:
    """Detect anomalies within the seeded cohort using setu_ml (A8)."""
    from setu_ml.anomaly import detect_anomalies

    if not all_rows:
        return None
    me = ngo_profile_from_row(ngo_row)
    others = [ngo_profile_from_row(r) for r in all_rows]
    return detect_anomalies(me, others)


def shell_info_for(ngo_id: str) -> ShellNetworkInfo | None:
    comp = db.get_one("shell_networks", "1=1 AND json_extract(data, '$.member_ngo_ids') LIKE ?",
                      (f'%"{ngo_id}"%',))
    if comp is None:
        return None
    data = comp["data"]
    if ngo_id not in data.get("member_ngo_ids", []):
        return None
    return ShellNetworkInfo(
        flagged=data.get("flagged", False),
        component_id=data.get("component_id"),
        shared_identifier_types=data.get("shared_identifier_types", []),
        member_ngo_ids=data.get("member_ngo_ids", []),
    )


def compute_for_ngo(row: dict, all_rows: list[dict],
                    foreign_funded: bool = False) -> TrustBreakdown:
    """Full pipeline for one NGO: evidence + anomaly + shell → compute_trust."""
    profile = ngo_profile_from_row(row)
    evidence = evidence_from_row(row)
    anomaly = anomaly_for(row, all_rows)
    shell = shell_info_for(row["ngo_id"])
    return _compute_trust(
        profile, evidence,
        anomaly=anomaly,
        shell_network=shell,
        foreign_funded=foreign_funded,
    )


def dossier_json(b: TrustBreakdown) -> dict[str, Any]:
    """TrustBreakdown → §6 /api/ngos/{id}/trust response shape."""
    pillars = []
    for p in b.pillars:
        pillars.append({
            "pillar": p.pillar,
            "label": PILLAR_LABELS.get(p.pillar, p.pillar),
            "weight": p.weight,
            "raw": round(p.raw, 4),
            "effective": round(p.effective, 4),
            "freshness": round(p.freshness, 4),
            "freshness_days": p.freshness_days,
            "half_life_days": p.half_life_days,
            "contribution": round(p.contribution, 2),
            "evidence": [e.model_dump() for e in p.evidence],
            "no_evidence": p.no_evidence,
            "notes": p.notes,
        })
    freshest = min(
        (p.freshness_days for p in b.pillars if p.freshness_days > 0), default=0
    )
    return {
        "ngo_id": b.ngo_id,
        "score": round(b.score, 1),
        "badge": b.badge.value,
        "is_ineligible": b.is_ineligible,
        "anomaly_penalty": b.anomaly_penalty,
        "shell_penalty": b.shell_penalty,
        "pillars": pillars,
        "anomaly_flags": b.anomaly_flags,
        "shell_network": b.shell_network.model_dump() if b.shell_network else None,
        "last_verified_months_ago": round(freshest / FRESHNESS_MONTHS_DIV) or None,
        "algorithm_version": b.algorithm_version,
        "input_hash": b.input_hash,
        "computed_at": b.computed_at.isoformat(),
    }


def persist_breakdown(b: TrustBreakdown) -> None:
    """Store per-pillar evidence ledger in compliance_audit (FR-C4)."""
    for p in b.pillars:
        doc = {
            "ngo_id": b.ngo_id,
            "pillar": p.pillar,
            "raw": p.raw,
            "effective": p.effective,
            "freshness_days": p.freshness_days,
            "evidence": [e.model_dump() for e in p.evidence],
            "no_evidence": p.no_evidence,
            "contribution": p.contribution,
        }
        db.upsert(
            "compliance_audit",
            {"ngo_id": b.ngo_id, "pillar": p.pillar},
            doc,
            columns={
                "computed_at": b.computed_at.isoformat(),
                "algorithm_version": b.algorithm_version,
                "input_hash": b.input_hash,
            },
        )
