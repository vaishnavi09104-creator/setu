"""setu_ml.trust — PURE reference implementation of the trust index, §5.2.

This module exists so that the counterfactual engine (A9) and the backend's
trust service call the SAME arithmetic. 00-PROJECT-CONTEXT.md §5.2 is the
single source of truth; this file implements it exactly:

  T_base = 100 × (0.30·C + 0.30·F + 0.25·O + 0.15·E)
  T      = clip(T_base − anomaly_penalty − shell_penalty, 0, 100)
  pillar_effective = pillar_raw × (0.60 + 0.40 × freshness)
  freshness = 0.5^(evidence_age_days / half_life_days)

PURE: no database, no I/O, no global state, deterministic given its inputs.
The backend may import this directly or re-expose it — the contract is that
`compute_trust` is the only place this arithmetic exists.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone

from .types import (
    ALGORITHM_VERSION,
    AnomalyReport,
    ComplianceEvidence,
    EvidenceRef,
    NgoProfile,
    PillarBreakdown,
    ShellNetworkInfo,
    TrustBadge,
    TrustBreakdown,
)

# Pillar weights (§5.2)
W_COMPLIANCE = 0.30
W_FINANCIAL = 0.30
W_OPERATIONAL = 0.25
W_EXTERNAL = 0.15

# Freshness half-lives, documented per §5.2 (days)
HALF_LIVES = {
    "compliance": 365,
    "financial": 540,
    "operational": 730,
    "external": 540,
}

# Compliance artefact weights within pillar C
C_WEIGHTS = {
    "csr1": 0.40,
    "reg_12a": 0.20,
    "reg_80g": 0.20,
    "darpan": 0.10,
    "fcra": 0.10,
}

# Artefacts counted for freshness of the compliance pillar
C_FRESHNESS_KEYS = ["csr1", "reg_12a", "reg_80g", "darpan", "fcra"]

FRESHNESS_FLOOR = 0.60  # pillar_raw * (0.60 + 0.40*f) — stale ≠ annihilated


def freshness(evidence_age_days: int, half_life_days: int) -> float:
    """0.5 ** (age / half_life)"""
    if half_life_days <= 0:
        return 1.0
    return 0.5 ** (max(0, evidence_age_days) / half_life_days)


def apply_freshness(pillar_raw: float, fresh: float) -> float:
    """pillar_raw * (0.60 + 0.40 * fresh) — the floor is deliberate."""
    return pillar_raw * (FRESHNESS_FLOOR + 0.40 * fresh)


def _evidence_age(ref: EvidenceRef | None, default: int = 0) -> int:
    return max(0, ref.evidence_age_days if ref else default)


def _fmt_inr_short(x: float) -> str:
    if x >= 10_000_000:
        return f"₹{x/10_000_000:.1f}Cr"
    if x >= 100_000:
        return f"₹{x/100_000:.1f}L"
    return f"₹{int(x):,}"


# --- Pillar C: compliance -----------------------------------------------------

def pillar_compliance(
    evidence: ComplianceEvidence, foreign_funded: bool = False
) -> tuple[float, list[EvidenceRef], list[str]]:
    """Weighted presence AND format validity, FCRA renormalisation included.

    CSR-1 absent/invalid is handled OUTSIDE scoring (hard gate → INELIGIBLE);
    here it simply contributes 0 to C, keeping the function total."""
    notes: list[str] = []
    items = evidence.items()
    weights = dict(C_WEIGHTS)

    if not foreign_funded:
        # FCRA dropped; renormalise remaining 0.90 so domestic NGOs are not
        # punished for lacking a registration they may not need.
        total = sum(v for k, v in weights.items() if k != "fcra")
        weights = {k: (v / total if k != "fcra" else 0.0) for k, v in weights.items()}
        notes.append("FCRA excluded (domestic mandate): C renormalised over 0.90")
    else:
        notes.append("FCRA counted (foreign-funded mandate)")

    score = 0.0
    refs: list[EvidenceRef] = []
    for key, w in weights.items():
        if w == 0.0:
            continue
        ref = items.get(key)
        if ref is None or not ref.present:
            continue  # contributes 0
        mult = 1.0
        if ref.is_expired:
            if key == "reg_80g":
                mult = 0.5  # expired 80G scores half — it's renewable
                notes.append("80G expired: contributes 0.5× weight (renewable)")
            elif key == "csr1":
                mult = 0.0  # invalid handled by hard gate anyway
        score += w * mult
        refs.append(ref)
    return min(1.0, score), refs, notes


def _compliance_age(evidence: ComplianceEvidence) -> int:
    """Freshness age of pillar C = age of the OLDEST counted artefact (the
    weakest link governs compliance freshness)."""
    ages = [
        _evidence_age(evidence.items().get(k))
        for k in C_FRESHNESS_KEYS
        if evidence.items().get(k) is not None and evidence.items().get(k).present  # type: ignore[union-attr]
    ]
    return max(ages) if ages else 0


# --- Pillar F: financial ------------------------------------------------------

def pillar_financial(profile: NgoProfile) -> tuple[float, list[EvidenceRef], list[str]]:
    """Admin-overhead ratio ladder (§5.2). Evidence refs supplied by the
    backend's audit artefact; the ladder itself is arithmetic."""
    f = profile.financials
    r = f.admin_ratio
    if r <= 0.10:
        s = 1.0
    elif r <= 0.25:
        s = 1.00 - 0.50 * (r - 0.10) / 0.15
    elif r <= 0.50:
        s = 0.50 - 0.50 * (r - 0.25) / 0.25
    else:
        s = 0.0
    notes = [f"Admin ratio {r:.1%} → ladder score {s:.2f}"]
    return max(0.0, min(1.0, s)), [], notes


# --- Pillar O: operational (Laplace-smoothed) ---------------------------------

def pillar_operational(profile: NgoProfile) -> tuple[float, list[EvidenceRef], list[str]]:
    t = profile.track_record
    completion = (t.projects_completed + 1) / (t.projects_total + 2)
    milestone = t.milestones_met / max(t.milestones_total, 1)
    tenure = min(t.years_active / 10, 1)
    o = 0.60 * completion + 0.25 * milestone + 0.15 * tenure
    notes = [
        f"Completion (Laplace) {completion:.2f} · milestones {milestone:.2f} · tenure {tenure:.2f}"
    ]
    return max(0.0, min(1.0, o)), [], notes


# --- Pillar E: external -------------------------------------------------------

E_WEIGHTS = {
    "third_party_audit": 0.40,
    "impact_assessment": 0.30,
    "peer_or_media_citation": 0.20,
    "site_visit_log": 0.10,
}


def pillar_external(evidence: ComplianceEvidence) -> tuple[float, list[EvidenceRef], list[str]]:
    score = 0.0
    refs: list[EvidenceRef] = []
    for key, w in E_WEIGHTS.items():
        ref = evidence.items().get(key)
        if ref is not None and ref.present:
            score += w
            refs.append(ref)
    notes = [f"External items present: {sum(1 for r in refs)}"]
    return min(1.0, score), refs, notes


# --- Badge --------------------------------------------------------------------

def assign_badge(
    score: float, is_ineligible: bool, has_shell_flag: bool
) -> TrustBadge:
    if is_ineligible:
        return TrustBadge.INELIGIBLE
    if score < 40 or has_shell_flag:
        return TrustBadge.HIGH_RISK
    if score < 60:
        return TrustBadge.INCOMPLETE
    if score < 80:
        return TrustBadge.STANDARD
    return TrustBadge.ELITE


# --- Input hash (reproducibility, FR-C11) --------------------------------------

def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def input_hash(profile: NgoProfile, evidence: ComplianceEvidence,
               anomaly: AnomalyReport | None, shell_flag: bool) -> str:
    payload = {
        "ngo": {
            "ngo_id": profile.ngo_id,
            "financials": profile.financials.model_dump(),
            "track_record": profile.track_record.model_dump(),
        },
        "evidence": {k: (v.model_dump() if v else None) for k, v in evidence.items().items()},
        "anomaly": anomaly.model_dump() if anomaly else None,
        "shell": shell_flag,
    }
    return "sha256:" + hashlib.sha256(_canonical(payload).encode()).hexdigest()


# --- The pure function --------------------------------------------------------

def compute_trust(
    profile: NgoProfile,
    evidence: ComplianceEvidence,
    anomaly: AnomalyReport | None = None,
    shell_network: ShellNetworkInfo | None = None,
    foreign_funded: bool = False,
    now: datetime | None = None,
) -> TrustBreakdown:
    """PURE. No database. No I/O. No global state. Deterministic given inputs.

    The counterfactual engine calls THIS with a hypothetically augmented
    evidence set — the only way predicted and realised deltas can be
    guaranteed to agree.
    """
    now = now or datetime.now(timezone.utc)
    shell_flag = bool(shell_network and shell_network.flagged)

    # --- hard gate: CSR-1 ---
    csr1 = evidence.csr1
    is_ineligible = csr1 is None or not csr1.present

    pillars: list[PillarBreakdown] = []

    # C
    c_raw, c_refs, c_notes = pillar_compliance(evidence, foreign_funded)
    c_age = _compliance_age(evidence)
    c_fresh = freshness(c_age, HALF_LIVES["compliance"])
    c_eff = apply_freshness(c_raw, c_fresh)
    pillars.append(PillarBreakdown(
        pillar="compliance", raw=c_raw, effective=c_eff, freshness=c_fresh,
        freshness_days=c_age, half_life_days=HALF_LIVES["compliance"],
        weight=W_COMPLIANCE, contribution=100 * W_COMPLIANCE * c_eff,
        evidence=c_refs, no_evidence=(c_raw == 0), notes=c_notes,
    ))

    # F
    f_raw, f_refs, f_notes = pillar_financial(profile)
    audit_age = _evidence_age(evidence.audit_fy)
    f_fresh = freshness(audit_age, HALF_LIVES["financial"])
    f_eff = apply_freshness(f_raw, f_fresh)
    if evidence.audit_fy is not None and evidence.audit_fy.present:
        f_refs = [evidence.audit_fy]
    pillars.append(PillarBreakdown(
        pillar="financial", raw=f_raw, effective=f_eff, freshness=f_fresh,
        freshness_days=audit_age, half_life_days=HALF_LIVES["financial"],
        weight=W_FINANCIAL, contribution=100 * W_FINANCIAL * f_eff,
        evidence=f_refs, no_evidence=(f_raw == 0 and not f_refs), notes=f_notes,
    ))

    # O
    o_raw, o_refs, o_notes = pillar_operational(profile)
    o_age = 0  # track record is lived history, not a document: fresh by nature
    o_fresh = 1.0
    o_eff = o_raw  # no decay on lived history
    pillars.append(PillarBreakdown(
        pillar="operational", raw=o_raw, effective=o_eff, freshness=o_fresh,
        freshness_days=o_age, half_life_days=HALF_LIVES["operational"],
        weight=W_OPERATIONAL, contribution=100 * W_OPERATIONAL * o_eff,
        evidence=o_refs, no_evidence=False, notes=o_notes,
    ))

    # E
    e_raw, e_refs, e_notes = pillar_external(evidence)
    e_ages = [_evidence_age(r) for r in e_refs] or [0]
    e_age = max(e_ages)
    e_fresh = freshness(e_age, HALF_LIVES["external"])
    e_eff = apply_freshness(e_raw, e_fresh)
    pillars.append(PillarBreakdown(
        pillar="external", raw=e_raw, effective=e_eff, freshness=e_fresh,
        freshness_days=e_age, half_life_days=HALF_LIVES["external"],
        weight=W_EXTERNAL, contribution=100 * W_EXTERNAL * e_eff,
        evidence=e_refs, no_evidence=(e_raw == 0), notes=e_notes,
    ))

    t_base = 100 * (
        W_COMPLIANCE * c_eff + W_FINANCIAL * f_eff
        + W_OPERATIONAL * o_eff + W_EXTERNAL * e_eff
    )

    anomaly_penalty = float(anomaly.penalty) if anomaly else 0.0
    shell_penalty = 20.0 if shell_flag else 0.0

    t = max(0.0, min(100.0, t_base - anomaly_penalty - shell_penalty))

    # Shell cap: trust hard-capped at 40 (§5.5)
    if shell_flag:
        t = min(t, 40.0)

    badge = assign_badge(t, is_ineligible, shell_flag)

    return TrustBreakdown(
        ngo_id=profile.ngo_id,
        score=t,
        badge=badge,
        is_ineligible=is_ineligible,
        pillars=pillars,
        anomaly_penalty=anomaly_penalty,
        shell_penalty=shell_penalty,
        shell_network=shell_network,
        anomaly_flags=[f.flag_text for f in anomaly.flags] if anomaly else [],
        algorithm_version=ALGORITHM_VERSION,
        input_hash=input_hash(profile, evidence, anomaly, shell_flag),
        computed_at=now,
    )
