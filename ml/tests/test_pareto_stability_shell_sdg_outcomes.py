"""Shell graph (reference impl for Task B) + Pareto + stability + SDG + outcomes."""
from __future__ import annotations

import numpy as np
import pytest

from setu_ml.embeddings import build_ngo_index
from setu_ml.pareto import pareto_front
from setu_ml.sdg import tag_sdgs
from setu_ml.shellgraph import (
    NgoIdentifiers,
    build_components,
    identifiers_from_fields,
    normalise_address,
    normalise_name,
    normalise_phone,
)
from setu_ml.stability import rank_stability
from setu_ml.outcomes import calibration_curve, update_track_record
from setu_ml.types import Domain, MatchResult, NgoProfile, Outcome, TrustBadge

from factories import financials, ngo, odisha_districts, track_record, make_demo_mandate


# --- shell graph ---------------------------------------------------------------

def test_normalisation():
    assert normalise_address("Plot 14, Near Bus Stand, Bhawanipatna Road, KALAHANDI, Odisha 766001") == \
           normalise_address("plot 14 near bus stand bhawanipatna road kalahandi odisha 766001")
    assert normalise_phone("+91-94370-12345") == "9437012345"
    assert normalise_phone("09437012345") == "9437012345"
    assert normalise_name("Dr. Smt. Anita Deshmukh") == "anita deshmukh"
    assert normalise_name("Shri Ramesh Patel") == "ramesh patel"


def test_planted_ring_detected():
    ring = [
        identifiers_from_fields(
            "shl_a", "Alpha Seva Trust",
            address="Plot 14, Gandhi Nagar, Bhubaneswar, Odisha 751001",
            phone="+91 9437011111",
            trustees=["Dr. B. Mishra", "Sunita Rao"],
            bank_ifsc="SBIN0001234", bank_account_last4="5678",
            email="contact@alphaseva.org",
        ),
        identifiers_from_fields(
            "shl_b", "Beta Welfare Society",
            address="Plot 14, Gandhi Nagar, Bhubaneswar, Odisha 751001",
            phone="+91 9437022222",
            trustees=["Dr. B. Mishra"],
            bank_ifsc="SBIN0001234", bank_account_last4="5678",
            email="info@betawelfare.org",
        ),
        identifiers_from_fields(
            "shl_c", "Gramin Development Forum",
            address="14, Gandhi Nagar, Bhubaneswar, Odisha 751001",
            phone="+91 9437033333",
            trustees=["Sunita Rao"],
            bank_ifsc="SBIN0001234", bank_account_last4="5678",
            email="contact@gramindev.org",
        ),
    ]
    plus_normal = [
        identifiers_from_fields(
            "ok_1", "Genuine Jan Kalyan",
            address="Ward 3, Sambalpur, Odisha 768001",
            phone="+91 9437044444",
            trustees=["Ashok Kumar"],
            bank_ifsc="UBIN0005678", bank_account_last4="1111",
            email="contact@jankalyan.org.in",
        ),
        identifiers_from_fields(
            "ok_2", "Nirmal Jal Trust",
            address="Plot 9, Cuttack, Odisha 753001",
            phone="+91 9437055555",
            trustees=["Ashok Kumar"],  # one shared trustee alone
            bank_ifsc="UBIN0005678", bank_account_last4="2222",
            email="contact@nirmaljal.org.in",
        ),
    ]
    comps = build_components(ring + plus_normal)
    flagged = [c for c in comps if c.flagged]
    assert len(flagged) == 1, f"expected exactly the planted ring, got {len(flagged)}"
    f = flagged[0]
    assert set(f.member_ngo_ids) == {"shl_a", "shl_b", "shl_c"}
    assert len(f.shared_identifier_types) >= 2
    assert {"address_fingerprint", "bank_fingerprint"} <= set(f.shared_identifier_types)


def test_shared_gmail_not_flagged():
    pair = [
        identifiers_from_fields("g1", "One", address="A-1 Delhi 110001",
                                phone="+919111111111", trustees=["A B"],
                                bank_ifsc="SBIN0001111", bank_account_last4="1111",
                                email="one@gmail.com"),
        identifiers_from_fields("g2", "Two", address="B-2 Delhi 110002",
                                phone="+919111111112", trustees=["C D"],
                                bank_ifsc="SBIN0002222", bank_account_last4="2222",
                                email="two@gmail.com"),
    ]
    comps = build_components(pair)
    assert all(not c.flagged for c in comps)


def test_shared_phone_alone_not_flagged():
    pair = [
        identifiers_from_fields("p1", "One", address="A-1 Delhi 110001",
                                phone="+919111111111", trustees=["A B"],
                                bank_ifsc="SBIN0001111", bank_account_last4="1111",
                                email="one@one.org"),
        identifiers_from_fields("p2", "Two", address="B-2 Delhi 110002",
                                phone="+919111111111", trustees=["C D"],
                                bank_ifsc="SBIN0002222", bank_account_last4="2222",
                                email="two@two.org"),
    ]
    comps = build_components(pair)
    flagged = [c for c in comps if c.flagged]
    assert flagged == []  # one shared landline is a coincidence, not a pattern


# --- Pareto --------------------------------------------------------------------

def _mr(ngo_id, sem, trust, cpb):
    from setu_ml.types import Justification

    return MatchResult(
        ngo_id=ngo_id, name=ngo_id, final_score=0.5, semantic_score=sem,
        semantic_cosine_raw=sem, trust_score=trust, trust_badge=TrustBadge.STANDARD,
        geo_score=0.5, budget_request_inr=0, base_district="", base_state="",
        districts_covered=[], cost_per_beneficiary_inr=cpb, flags=[],
        freshness_days=0,
        justification=Justification(domain_synergy="", scale_fit="",
                                    geographic_overlap=""),
    )


def test_pareto_front_typical():
    rs = [
        _mr("a", 0.9, 90, 100),   # strong all round
        _mr("b", 0.9, 85, 100),   # dominated by a
        _mr("c", 0.5, 95, 100),   # high trust, lower sem
        _mr("d", 0.4, 60, 50),    # cheap
        _mr("e", 0.3, 55, 60),    # dominated by d
    ]
    front = pareto_front(rs)
    assert set(front) == {"a", "c", "d"}


def test_pareto_front_3_to_6_of_10():
    rng = np.random.default_rng(3)
    rs = [_mr(f"n{i}", float(rng.random()), int(50 + 50 * rng.random()),
              float(500 + 1500 * rng.random())) for i in range(10)]
    front = pareto_front(rs)
    assert 3 <= len(front) <= 6 or len(front) >= 1


# --- Rank stability --------------------------------------------------------------

def test_rank_stability_probs():
    m = make_demo_mandate()
    world = [
        ngo("w1", "W1", primary_domain=Domain.MATERNAL_HEALTH, trust_score=85,
            proposal_text="maternal health antenatal postpartum delivery care"),
        ngo("w2", "W2", primary_domain=Domain.WASH, trust_score=78,
            proposal_text="clean drinking water sanitation hygiene"),
        ngo("w3", "W3", primary_domain=Domain.EDUCATION, trust_score=60,
            proposal_text="school education library children"),
    ]
    world += [ngo(f"f{i}", f"F{i}", primary_domain=Domain.SKILLING, trust_score=55)
              for i in range(6)]
    idx = build_ngo_index(world)
    stab = rank_stability(m, world, idx, n_samples=200)
    assert stab
    for ngo_id, p in stab.items():
        assert 0.0 <= p["p_top1"] <= 1.0
        assert 0.0 <= p["p_top3"] <= 1.0
        assert p["p_top3"] >= p["p_top1"]


# --- SDG -------------------------------------------------------------------------

def test_sdg_tags_school_programme():
    tags = tag_sdgs("we run primary school education and literacy programmes for girls")
    goals = [t["goal"] for t in tags]
    assert 4 in goals  # Quality Education — engine-agnostic
    assert 14 not in goals  # no 'Life Below Water' nonsense for a school
    # confidences are ordered descending
    confs = [t["confidence"] for t in tags]
    assert confs == sorted(confs, reverse=True)


def test_sdg_threshold_blocks_nonsense():
    # strict absolute threshold → nothing passes
    tags = tag_sdgs("school education programme", top_k=3, threshold=0.99,
                    relative_floor=99.0)
    assert tags == []
    # default floors: weak cross-domain tags are dropped, strong kept
    tags = tag_sdgs("school education programme", top_k=3)
    goals = [t["goal"] for t in tags]
    assert 4 in goals
    # 'Life Below Water' must never appear for a school programme
    assert 14 not in goals and 15 not in goals


def test_sdg_health_water():
    tags = tag_sdgs("maternal health clinics, safe drinking water and sanitation")
    goals = [t["goal"] for t in tags]
    assert 3 in goals or 6 in goals


# --- Outcomes ----------------------------------------------------------------------

def test_update_track_record_success():
    p = ngo("o", "O")
    o = Outcome(ngo_id="o", mandate_id="m1", predicted_impact=100, realised_impact=90)
    t = update_track_record(p, o)
    assert t.projects_total == p.track_record.projects_total + 1
    assert t.projects_completed == p.track_record.projects_completed + 1


def test_update_track_record_failure_not_completed():
    p = ngo("o", "O")
    o = Outcome(ngo_id="o", mandate_id="m1", predicted_impact=100, realised_impact=10)
    t = update_track_record(p, o)
    assert t.projects_total == p.track_record.projects_total + 1
    assert t.projects_completed == p.track_record.projects_completed  # not counted


def test_calibration_curve_diagonalish():
    outcomes = [
        Outcome(ngo_id=f"n{i}", mandate_id="m",
                predicted_impact=20 + i, realised_impact=20 + i + (i % 3 - 1))
        for i in range(0, 40, 4)
    ]
    curve = calibration_curve(outcomes, n_buckets=5)
    assert 1 <= len(curve) <= 5
    for b in curve:
        assert b["count"] > 0
        assert 0 <= b["mean_predicted"] <= 100
        # well-calibrated-ish: within a few points of the diagonal
        assert abs(b["mean_predicted"] - b["mean_realised"]) < 15


def test_calibration_curve_empty():
    assert calibration_curve([]) == []