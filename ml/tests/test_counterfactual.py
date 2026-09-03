"""A9 ★ — counterfactual: the round-trip guarantee, NEVER_SUGGEST, ceiling."""
from __future__ import annotations

import pytest

from setu_ml.counterfactual import (
    achievable_ceiling,
    generate_counterfactual,
    round_trip_check,
)
from setu_ml.trust import compute_trust
from setu_ml.types import Domain, NEVER_SUGGEST, TrustBadge

from factories import ev, financials, full_evidence, ngo, track_record


def fn(profile, evidence):
    return compute_trust(profile, evidence)


# --- the round-trip: predicted == realised -------------------------------------

def test_round_trip_all_paths():
    p = ngo("a", "A")
    evidence_variants = [
        full_evidence("a"),
        full_evidence("a", reg_12a=None),
        full_evidence("a", audit_fy=None, impact_assessment=None,
                      third_party_audit=None, peer_or_media_citation=None,
                      site_visit_log=None),
        full_evidence("a", reg_80g=ev("reg_80g", expired=True)),
    ]
    for ev_set in evidence_variants:
        result = round_trip_check(p, ev_set, fn)
        if "skipped" in result:
            continue
        assert result["match"], (
            f"predicted {result['predicted_delta']} vs realised "
            f"{result['realised_delta']} on {result['action']}"
        )


def test_round_trip_delta_within_half_point():
    p = ngo("a", "A")
    evset = full_evidence("a", reg_12a=None, impact_assessment=None)
    check = round_trip_check(p, evset, fn)
    assert abs(check["predicted_delta"] - check["realised_delta"]) <= 0.5


# --- ranking & classification -----------------------------------------------------

def test_actions_ranked_by_delta_over_effort():
    p = ngo("a", "A")
    base = full_evidence("a", csr1=None, reg_12a=None, impact_assessment=None,
                          third_party_audit=None, site_visit_log=None,
                          peer_or_media_citation=None)
    current = fn(p, base)
    report = generate_counterfactual(p, current, fn, base)
    actionable = [a for a in report.actions if a.actionable]
    assert actionable
    # sorted by delta/effort descending among actionable
    scores = [a.delta_points / {"upload": 1, "obtain_registration": 5, "structural": 10}[a.effort]
              for a in actionable]
    assert scores == sorted(scores, reverse=True)


def test_badge_change_mentioned_only_when_it_changes():
    p = ngo("a", "A")
    base = full_evidence("a", csr1=None, reg_12a=None, impact_assessment=None,
                          third_party_audit=None, site_visit_log=None,
                          peer_or_media_citation=None, audit_fy=None)
    current = fn(p, base)
    report = generate_counterfactual(p, current, fn, base)
    for a in report.actions:
        if a.resulting_badge == current.badge:
            assert "badge from" not in a.sentence
        else:
            assert "badge from" in a.sentence


def test_never_suggest_never_returned():
    p = ngo("a", "A")
    base = full_evidence("a")
    current = fn(p, base)
    report = generate_counterfactual(p, current, fn, base)
    for a in report.actions:
        assert a.label not in {
            "Change your historical completion rate",
            "Change years active",
            "Change past beneficiary counts",
        }
        assert a.evidence_key not in NEVER_SUGGEST


def test_ceiling_at_least_current_and_below_100():
    p = ngo("a", "A")
    base = full_evidence("a", reg_12a=None, impact_assessment=None)
    current = fn(p, base)
    ceiling = achievable_ceiling(p, current, fn, base)
    assert ceiling >= current.score
    assert ceiling <= 100.0


def test_ceiling_is_honest_not_100():
    """An NGO with a mediocre track record must not be promised 100."""
    p = ngo("a", "A",
            track_record=track_record(projects_total=4, projects_completed=1,
                                      milestones_met=5, milestones_total=20,
                                      years_active=2))
    base = full_evidence("a", impact_assessment=None, third_party_audit=None)
    current = fn(p, base)
    ceiling = achievable_ceiling(p, current, fn, base)
    assert ceiling < 95.0  # operational pillar limits the honest maximum


def test_elite_ngo_gets_empty_actions_not_invented():
    """Already-Verified-Elite with complete fresh evidence → empty list, graceful."""
    p = ngo("a", "A",
            financials=financials(admin_expense_inr=600_000,
                                 programme_expense_inr=9_400_000),
            track_record=track_record(projects_total=20, projects_completed=19,
                                      milestones_met=58, milestones_total=60,
                                      years_active=12))
    base = full_evidence("a")
    current = fn(p, base)
    assert current.badge == TrustBadge.ELITE
    report = generate_counterfactual(p, current, fn, base)
    actionable = [a for a in report.actions if a.actionable]
    assert actionable == []  # nothing left to upload; no invented suggestions


def test_structural_items_labelled():
    p = ngo("a", "A",
            financials=financials(admin_expense_inr=4_500_000,
                                  programme_expense_inr=5_500_000),
            track_record=track_record(projects_total=2, projects_completed=0,
                                      milestones_met=2, milestones_total=10,
                                      years_active=1))
    base = full_evidence("a", reg_12a=None, impact_assessment=None,
                          third_party_audit=None, audit_fy=None,
                          peer_or_media_citation=None, site_visit_log=None)
    current = fn(p, base)
    report = generate_counterfactual(p, current, fn, base, top_n=10)
    structural = [a for a in report.actions if not a.actionable]
    assert structural
    for a in structural:
        assert a.effort == "structural"
        assert "Longer-term" in a.sentence
    # actionable items come before structural in ranking
    actionable = [a for a in report.actions if a.actionable]
    first_structural_idx = report.actions.index(structural[0])
    for a in actionable:
        assert report.actions.index(a) < first_structural_idx


def test_sentence_format():
    p = ngo("a", "A")
    base = full_evidence("a", csr1=None, reg_12a=None)
    current = fn(p, base)
    report = generate_counterfactual(p, current, fn, base)
    assert report.actions
    a = report.actions[0]
    assert a.sentence.startswith(f"+{a.delta_points:.0f} points")
    assert "→" in a.sentence
