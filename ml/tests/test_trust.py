"""trust.py — the pure §5.2 reference. Includes the 61→80 narrative case."""
from __future__ import annotations

import pytest

from setu_ml.trust import (
    apply_freshness,
    assign_badge,
    compute_trust,
    freshness,
    input_hash,
    pillar_compliance,
    pillar_financial,
)
from setu_ml.types import (
    ComplianceEvidence,
    Domain,
    EvidenceRef,
    NgoProfile,
    TrustBadge,
)

from factories import ev, financials, full_evidence, ngo, track_record


def test_freshness_half_life():
    assert abs(freshness(365, 365) - 0.5) < 1e-9
    assert freshness(0, 365) == 1.0
    assert 0.49 < freshness(540, 540) < 0.51


def test_freshness_floor_never_annihilates():
    assert apply_freshness(1.0, 0.0) == 0.60  # stale-but-real: 0.60 floor


def test_compliance_weights_full():
    ev = full_evidence("ngo_x")
    c, refs, notes = pillar_compliance(ev, foreign_funded=False)
    # all five domestic artefacts present & valid → 1.0
    assert abs(c - 1.0) < 1e-9
    assert len(refs) == 4  # fcra excluded → renormalised (csr1, 12a, 80g, darpan)


def test_fcra_renormalisation_domestic_not_punished():
    domestic_no_fcra = full_evidence("a", fcra=None)
    foreigner_with_fcra = full_evidence("b", fcra=ev("fcra"))
    c_dom, _, _ = pillar_compliance(domestic_no_fcra, foreign_funded=False)
    c_for, _, _ = pillar_compliance(foreigner_with_fcra, foreign_funded=True)
    assert abs(c_dom - 1.0) < 1e-9  # renormalised over 0.90
    assert abs(c_for - 1.0) < 1e-9


def test_missing_12a_lowers_compliance():
    with12a = full_evidence("a")
    without = full_evidence("b", reg_12a=None)
    c1, _, _ = pillar_compliance(with12a, False)
    c0, _, _ = pillar_compliance(without, False)
    assert c1 > c0
    assert abs((c1 - c0) - 0.2 / 0.9) < 0.01  # 12A is 0.20 of renormalised 0.90


def test_expired_80g_half_weight():
    fresh = full_evidence("a")
    expired = full_evidence("b", reg_80g=ev("reg_80g", expired=True))
    c1, _, _ = pillar_compliance(fresh, False)
    c0, _, _ = pillar_compliance(expired, False)
    assert abs((c1 - c0) - 0.5 * 0.2 / 0.9) < 0.01


def test_financial_ladder():
    def mk(ratio):
        admin = int(10_000_000 * ratio)
        return ngo("x", "X", financials=financials(
            admin_expense_inr=admin,
            programme_expense_inr=10_000_000 - admin,
            total_expense_inr=10_000_000,
        ))

    assert pillar_financial(mk(0.05))[0] == 1.0
    assert pillar_financial(mk(0.10))[0] == 1.0
    assert abs(pillar_financial(mk(0.175))[0] - 0.75) < 1e-9  # midpoint of 0.10→0.25
    assert abs(pillar_financial(mk(0.25))[0] - 0.50) < 1e-9
    assert abs(pillar_financial(mk(0.375))[0] - 0.25) < 1e-9  # midpoint of 0.25→0.50
    assert pillar_financial(mk(0.50))[0] == 0.0
    assert pillar_financial(mk(0.80))[0] == 0.0


def test_laplace_smoothing_operational():
    one_for_one = ngo("o", "O", track_record=track_record(
        projects_total=1, projects_completed=1))
    veteran = ngo("v", "V", track_record=track_record(
        projects_total=30, projects_completed=27))
    b = compute_trust(one_for_one, full_evidence("o"))
    v = compute_trust(veteran, full_evidence("v"))
    # veteran's operational pillar must beat the one-for-one NGO
    op = {p.pillar: p for p in b.pillars}["operational"]
    vp = {p.pillar: p for p in v.pillars}["operational"]
    assert vp.raw > op.raw
    assert op.raw < 1.0  # 1/1 does NOT score 100%


def test_csr1_hard_gate():
    no_csr1 = full_evidence("a", csr1=None)
    p = ngo("a", "A")
    b = compute_trust(p, no_csr1)
    assert b.is_ineligible is True
    assert b.badge == TrustBadge.INELIGIBLE


def test_badge_thresholds():
    assert assign_badge(85, False, False) == TrustBadge.ELITE
    assert assign_badge(80, False, False) == TrustBadge.ELITE
    assert assign_badge(79, False, False) == TrustBadge.STANDARD
    assert assign_badge(60, False, False) == TrustBadge.STANDARD
    assert assign_badge(59, False, False) == TrustBadge.INCOMPLETE
    assert assign_badge(40, False, False) == TrustBadge.INCOMPLETE
    assert assign_badge(39, False, False) == TrustBadge.HIGH_RISK
    assert assign_badge(90, False, True) == TrustBadge.HIGH_RISK
    assert assign_badge(90, True, False) == TrustBadge.INELIGIBLE


def test_shell_cap_at_40():
    from setu_ml.types import ShellNetworkInfo

    p = ngo("a", "A")
    b = compute_trust(p, full_evidence("a"),
                      shell_network=ShellNetworkInfo(flagged=True))
    assert b.shell_penalty == 20.0
    assert b.score <= 40.0
    assert b.badge == TrustBadge.HIGH_RISK


def test_anomaly_penalty_applied():
    from setu_ml.types import AnomalyFlag, AnomalyReport

    p = ngo("a", "A")
    anomaly = AnomalyReport(
        ngo_id="a", cohort_key=("wash", "10L-50L", "east"), cohort_size=8,
        insufficient_cohort=False, penalty=8.0,
        flags=[AnomalyFlag(metric="admin_ratio", direction="above", z_score=3.4,
                           value=0.41, cohort_median=0.14, cohort_size=8,
                           flag_text="administrative overhead 3.4σ above cohort")],
    )
    b = compute_trust(p, full_evidence("a"), anomaly=anomaly)
    clean = compute_trust(p, full_evidence("a"))
    assert abs((clean.score - b.score) - 8.0) < 1e-9
    assert any("3.4σ" in f for f in b.anomaly_flags)


def test_determinism_and_input_hash():
    p = ngo("a", "A")
    ev1 = full_evidence("a")
    b1 = compute_trust(p, ev1)
    b2 = compute_trust(p, full_evidence("a"))
    assert b1.input_hash == b2.input_hash
    assert abs(b1.score - b2.score) < 1e-9
    # hash changes when evidence changes
    b3 = compute_trust(p, full_evidence("a", reg_12a=None))
    assert b3.input_hash != b1.input_hash


def test_freshness_visible_in_pillars():
    p = ngo("a", "A")
    fresh = compute_trust(p, full_evidence("a"))
    stale = compute_trust(p, full_evidence("a", csr1=ev("csr1", age_days=730)))
    assert fresh.score > stale.score


# --- THE 61→80 NARRATIVE CASE ---------------------------------------------------
# The seeded coached NGO (06-PITCH-AND-DEMO-RUNBOOK.md): everything decent,
# but CSR-1 expired and audit stale → lands exactly 61 (Standard Audited).
# Uploading the renewal packet (fresh CSR-1 + FY audit + 80G + 12A refresh)
# moves it to exactly 80 and the badge flips to Verified Elite.

def _coached_profile() -> NgoProfile:
    return ngo(
        "ngo_061",
        "Sarthak Seva Evam Shiksha Sansthan",
        primary_domain=Domain.EDUCATION,
        secondary_domains=[Domain.SKILLING],
        budget_request_inr=2_400_000,
        financials=financials(
            admin_expense_inr=1_500_000,      # r = 15% → ladder ≈ 0.83
            programme_expense_inr=8_500_000,
            total_expense_inr=10_000_000,
            beneficiaries_reached=7_400,
            max_grant_managed_inr=2_200_000,
        ),
        track_record=track_record(
            projects_total=12, projects_completed=10,
            milestones_met=32, milestones_total=40, years_active=9,
        ),
        trust_score=61,
    )


def _coached_evidence_before() -> ComplianceEvidence:
    return ComplianceEvidence(
        ngo_id="ngo_061",
        csr1=ev("csr1", age_days=500, expired=True),  # ← the demo gap
        reg_12a=ev("reg_12a", age_days=200),
        reg_80g=ev("reg_80g", age_days=300),
        darpan=ev("darpan", age_days=150),
        audit_fy=ev("audit_fy", age_days=540),        # stale
        third_party_audit=ev("third_party_audit", age_days=400),
        impact_assessment=ev("impact_assessment", age_days=400),
        peer_or_media_citation=None,
        site_visit_log=None,
    )


def test_coached_ngo_lands_61_then_80():
    p = _coached_profile()
    ev_before = _coached_evidence_before()

    # Variant A (missing CSR-1 entirely): ineligible, excluded — the hard gate.
    missing = ev_before.with_override(
        "csr1", EvidenceRef(doc_id="none", kind="csr1", page=1, snippet="",
                            present=False)
    )
    assert compute_trust(p, missing).is_ineligible is True

    # Variant B (the actual demo): expired CSR-1 + stale audit → exactly 61
    before = compute_trust(p, ev_before)
    assert 60 <= before.score <= 62, f"expected 61±1, got {before.score}"
    assert before.badge == TrustBadge.STANDARD

    # after: the renewal packet — fresh CSR-1, fresh FY audit, refreshed
    # 80G and 12A (all four travel together in a real renewal)
    ev_after = ev_before.with_override("csr1", ev("csr1", age_days=10))
    ev_after = ev_after.with_override("audit_fy", ev("audit_fy", age_days=30))
    ev_after = ev_after.with_override("reg_80g", ev("reg_80g", age_days=150))
    ev_after = ev_after.with_override("reg_12a", ev("reg_12a", age_days=90))
    after = compute_trust(p, ev_after)
    assert 79 <= after.score <= 81, f"expected 80±1, got {after.score}"
    assert after.badge == TrustBadge.ELITE
