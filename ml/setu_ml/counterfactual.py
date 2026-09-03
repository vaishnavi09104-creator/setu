"""setu_ml.counterfactual — the coaching engine (A9 ★). §5.9.

Demo beat 8 and the emotional high point: "we don't reject NGOs into a
black box, we hand them the roadmap."

THE ONE THING THAT MUST NOT GO WRONG: the predicted delta has to equal what
actually happens when the document is uploaded. So BOTH the prediction and
the recomputation call the SAME trust function. This module never re-derives
the arithmetic — it re-runs the caller's `compute_trust_fn` with a
hypothetically augmented evidence set.
"""
from __future__ import annotations

import logging
from typing import Callable

from .trust import assign_badge
from .types import (
    NEVER_SUGGEST,
    ComplianceEvidence,
    CounterfactualAction,
    CounterfactualReport,
    EvidenceRef,
    NgoProfile,
    TrustBadge,
    TrustBreakdown,
)

logger = logging.getLogger("setu_ml.counterfactual")

ComputeTrust = Callable[[NgoProfile, ComplianceEvidence], TrustBreakdown]

# effort scale for Δ/effort ranking (§5.9)
EFFORT = {"upload": 1, "obtain_registration": 5, "structural": 10}


def _fresh_ref(kind: str, note: str | None = None) -> EvidenceRef:
    return EvidenceRef(
        doc_id=f"hypothetical_{kind}",
        kind=kind,
        page=1,
        snippet="(prospective upload — not yet on file)",
        present=True,
        evidence_age_days=0,
        confidence=1.0,
        extraction_note=note,
    )


# candidate actions: (evidence_key, label, effort, actionable, evidence_required)
_CANDIDATE_ACTIONS: list[dict] = [
    {
        "key": "csr1",
        "label": "Upload your CSR-1 registration certificate",
        "effort": "upload",
        "actionable": True,
        "requires": "Form CSR-1 filed with MCA (mandatory to receive CSR funds)",
        "never": False,
    },
    {
        "key": "reg_80g",
        "label": "Upload your renewed 80G certificate",
        "effort": "upload",
        "actionable": True,
        "requires": "80G renewal from the Income Tax Department",
        "never": False,
        "stale_only": True,
    },
    {
        "key": "audit_fy",
        "label": "Upload the latest audited financial statement",
        "effort": "upload",
        "actionable": True,
        "requires": "Audited FY financials from a practicing chartered accountant",
        "never": False,
        "stale_only": True,
    },
    {
        "key": "third_party_audit",
        "label": "Obtain a third-party audit report",
        "effort": "obtain_registration",
        "actionable": True,
        "requires": "Independent statutory audit documentation",
        "never": False,
    },
    {
        "key": "impact_assessment",
        "label": "Commission an impact assessment",
        "effort": "obtain_registration",
        "actionable": True,
        "requires": "Independent evaluation of a completed project",
        "never": False,
    },
    {
        "key": "site_visit_log",
        "label": "Publish a site-visit log",
        "effort": "upload",
        "actionable": True,
        "requires": "Dated, geotagged site-visit records",
        "never": False,
    },
    {
        "key": "peer_or_media_citation",
        "label": "Collect peer or media citations of your work",
        "effort": "upload",
        "actionable": True,
        "requires": "Publicly verifiable third-party references",
        "never": False,
    },
    {
        "key": "reg_12a",
        "label": "Obtain 12A registration",
        "effort": "obtain_registration",
        "actionable": True,
        "requires": "Income Tax 12A registration (exemption on own income)",
        "never": False,
    },
    {
        "key": "_structural_overhead",
        "label": "Reduce administrative overhead ratio",
        "effort": "structural",
        "actionable": False,
        "requires": "Multi-year financial restructuring — programme spend ↑, admin ↓",
        "never": False,
        "structural": True,
    },
    {
        "key": "_structural_projects",
        "label": "Complete more funded projects to build the track record",
        "effort": "structural",
        "actionable": False,
        "requires": "Deliver and document more projects over time",
        "never": False,
        "structural": True,
    },
]

# NEVER-SUGGEST enforcement: history cannot change, and suggesting it does is
# insulting and destroys the tool's credibility with the exact user it serves.
_HYPOTHETICAL_STRUCTURAL: dict[str, dict] = {
    a["key"]: a for a in _CANDIDATE_ACTIONS if a.get("structural")
}


def generate_counterfactual(
    ngo: NgoProfile,
    current_breakdown: TrustBreakdown,
    compute_trust_fn: ComputeTrust,
    evidence: ComplianceEvidence | None = None,
    top_n: int = 3,
) -> CounterfactualReport:
    """For each candidate evidence item missing or stale:
       1. build a hypothetical evidence set with that item present and fresh
       2. call compute_trust_fn on it
       3. delta = hypothetical.score − current.score
    Classify, filter, rank by Δ/effort, return top_n plus the ceiling."""
    if evidence is None:
        # derive the evidence set from the current breakdown's pillar evidence
        evidence = _evidence_from_breakdown(current_breakdown)

    current = current_breakdown.score
    actions: list[CounterfactualAction] = []

    for cand in _CANDIDATE_ACTIONS:
        key = cand["key"]
        if cand.get("never") or key in NEVER_SUGGEST:
            continue  # never suggest — enforced, and tested

        if cand.get("structural"):
            # structural items: compute delta via the structural levers
            delta = _structural_delta(ngo, current_breakdown, compute_trust_fn, cand)
            if delta <= 0.05:
                continue
            resulting = current + delta
            actions.append(_mk_action(cand, delta, resulting, current, current_breakdown.badge, structural=True))
            continue

        existing = evidence.items().get(key)
        needs_it = existing is None or not existing.present
        stale = (existing is not None and existing.present and existing.is_expired) or (
            existing is not None and existing.present and existing.evidence_age_days > 540
        )
        if cand.get("stale_only"):
            # only suggest refresh when the current one is expired or stale
            if not (needs_it or stale):
                continue
        if not (needs_it or stale):
            continue

        hypothetical = evidence.with_override(key, _fresh_ref(key))
        try:
            hyp_breakdown = compute_trust_fn(ngo, hypothetical)
        except Exception as exc:  # pragma: no cover
            logger.warning("counterfactual compute failed for %s/%s: %s", ngo.ngo_id, key, exc)
            continue
        delta = hyp_breakdown.score - current
        if delta <= 0.05:
            continue
        actions.append(
            _mk_action(cand, delta, hyp_breakdown.score, current, current_breakdown.badge,
                       structural=False, new_badge=assign_badge(
                           hyp_breakdown.score,
                           hyp_breakdown.is_ineligible,
                           bool(hyp_breakdown.shell_penalty),
                       ))
        )

    # rank by Δ/effort, actionable first
    actions.sort(key=lambda a: (not a.actionable, -(a.delta_points / EFFORT[a.effort])))

    ceiling = achievable_ceiling(ngo, current_breakdown, compute_trust_fn, evidence)
    return CounterfactualReport(
        ngo_id=ngo.ngo_id,
        current_score=current,
        current_badge=current_breakdown.badge,
        achievable_ceiling=ceiling,
        actions=actions[:top_n],
    )


def _mk_action(cand: dict, delta: float, resulting: float, current: float,
               current_badge: TrustBadge, structural: bool,
               new_badge: TrustBadge | None = None) -> CounterfactualAction:
    resulting = max(0.0, min(100.0, resulting))
    badge_out = new_badge if new_badge is not None else assign_badge(resulting, False, False)
    badge_change = badge_out != current_badge
    sentence = f"+{delta:.0f} points — {cand['label']}. Your score would move from {current:.0f} → {resulting:.0f}"
    if badge_change:
        sentence += f" and your badge from '{current_badge.value}' to '{badge_out.value}'."
    else:
        sentence += "."
    if structural:
        sentence += " (Longer-term change — shown as a roadmap item, not a quick upload.)"
    return CounterfactualAction(
        label=cand["label"],
        delta_points=round(delta, 1),
        resulting_score=round(resulting, 1),
        resulting_badge=badge_out,
        effort=cand["effort"],  # type: ignore[arg-type]
        evidence_required=cand["requires"],
        evidence_key=cand["key"],
        sentence=sentence,
        actionable=not structural,
    )


def _structural_delta(ngo, current_breakdown, compute_trust_fn, cand) -> float:
    """Structural items get honest indicative deltas — measured against the
    same trust function with a materially better profile."""
    better = ngo.model_copy(deep=True)
    if cand["key"] == "_structural_overhead":
        f = better.financials
        target_admin = max(100_000, int(f.total_expense_inr * 0.08))
        if f.admin_expense_inr <= target_admin:
            return 0.0
        better.financials.admin_expense_inr = target_admin
    elif cand["key"] == "_structural_projects":
        t = better.track_record
        if t.projects_total >= 8 and (t.projects_completed / max(t.projects_total, 1)) >= 0.85:
            return 0.0
        better.track_record.projects_total = t.projects_total + 3
        better.track_record.projects_completed = t.projects_completed + 3
    else:
        return 0.0
    # structural changes carry no freshness change; reuse current evidence
    ev = _evidence_from_breakdown(current_breakdown)
    try:
        return compute_trust_fn(better, ev).score - current_breakdown.score
    except Exception:  # pragma: no cover
        return 0.0


def achievable_ceiling(ngo, current_breakdown, compute_trust_fn,
                       evidence: ComplianceEvidence | None = None) -> float:
    """Score with ALL 'upload'-effort items supplied. The honest maximum —
    not 100, which would be a lie for an NGO whose track record limits it."""
    if evidence is None:
        evidence = _evidence_from_breakdown(current_breakdown)
    best = current_breakdown.score
    for cand in _CANDIDATE_ACTIONS:
        if cand.get("structural") or cand.get("never"):
            continue
        if cand["key"] in NEVER_SUGGEST:
            continue
        key = cand["key"]
        if key.startswith("_"):
            continue
        hyp = evidence.with_override(key, _fresh_ref(key))
        try:
            s = compute_trust_fn(ngo, hyp).score
            best = max(best, s)
        except Exception:  # pragma: no cover
            continue
    return round(max(best, current_breakdown.score), 1)


def _evidence_from_breakdown(b: TrustBreakdown) -> ComplianceEvidence:
    """Rebuild a ComplianceEvidence from pillar evidence refs (backend normally
    passes the real set; this is the fallback derivation)."""
    ev = ComplianceEvidence(ngo_id=b.ngo_id)
    for p in b.pillars:
        for ref in p.evidence:
            if hasattr(ev, ref.kind):
                try:
                    setattr(ev, ref.kind, ref)
                except Exception:
                    continue
    return ev


def round_trip_check(ngo: NgoProfile, evidence: ComplianceEvidence,
                     compute_trust_fn: ComputeTrust) -> dict:
    """The most important test in the lane: predicted delta == realised delta.
    Adds the top actionable item, recomputes, compares."""
    current = compute_trust_fn(ngo, evidence)
    report = generate_counterfactual(ngo, current, compute_trust_fn, evidence)
    actionable = [a for a in report.actions if a.actionable]
    if not actionable:
        return {"ngo_id": ngo.ngo_id, "skipped": "no actionable items"}
    top = actionable[0]
    realised = compute_trust_fn(
        ngo, evidence.with_override(top.evidence_key, _fresh_ref(top.evidence_key))
    ).score
    predicted = top.resulting_score
    return {
        "ngo_id": ngo.ngo_id,
        "action": top.label,
        "predicted_delta": round(predicted - report.current_score, 1),
        "realised_delta": round(realised - current.score, 1),
        "match": abs((realised - current.score) - (predicted - report.current_score)) <= 0.5,
    }
