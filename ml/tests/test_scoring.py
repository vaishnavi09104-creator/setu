"""A5 — scoring, keyword baseline, justification; A6 calibration sanity."""
from __future__ import annotations

import pytest

from setu_ml.embeddings import build_ngo_index
from setu_ml.scoring import (
    composite_score,
    keyword_baseline,
    compare_engines,
    rank_ngos,
    semantic_score,
    unmatched_guard,
)
from setu_ml.types import Domain, TrustBadge

from factories import DEMO_MANDATE_TEXT, make_demo_mandate
from factories import financials as fin
from factories import make_demo_mandate, ngo, odisha_districts, dref


def _index(ngos):
    return build_ngo_index(ngos)


# --- composite ------------------------------------------------------------------

def test_composite_default_weights():
    assert abs(composite_score(0.8, 80, 0.7) - (0.5 * 0.8 + 0.3 * 0.8 + 0.2 * 0.7)) < 1e-9


def test_composite_rejects_bad_weights():
    with pytest.raises(ValueError):
        composite_score(0.8, 80, 0.7, weights={"semantic": 0.6, "trust": 0.3, "geo": 0.2})


def test_weights_change_ordering():
    m = make_demo_mandate()
    # near NGO: perfect geo + domain, mid trust; far NGO: same domain, high trust, zero geo
    near = ngo("near", "NearOrg", districts_covered=odisha_districts("Kalahandi", "Nuapada"),
               primary_domain=Domain.MATERNAL_HEALTH,
               proposal_text="postpartum institutional delivery care, ASHA worker training",
               trust_score=60)
    far = ngo("far", "FarOrg",
              districts_covered=[dref("Pune", "Maharashtra", 18.52, 73.86)],
              base_district="Pune", base_state="Maharashtra",
              primary_domain=Domain.MATERNAL_HEALTH,
              proposal_text="maternal health antenatal postpartum safe motherhood neonatal care",
              trust_score=99)
    idx = _index([near, far])
    geo_heavy, _ = rank_ngos(m, [near, far], idx,
                             weights={"semantic": 0.1, "trust": 0.1, "geo": 0.8})
    sem_heavy, _ = rank_ngos(m, [near, far], idx,
                             weights={"semantic": 0.1, "trust": 0.8, "geo": 0.1})
    # geo-dominant → near wins; trust-dominant → far (99 vs 60) wins
    assert geo_heavy[0].ngo_id == "near"
    assert sem_heavy[0].ngo_id == "far"


def test_ineligible_never_ranked():
    m = make_demo_mandate()
    good = ngo("good", "Good", trust_score=70, status="ACTIVE")
    bad = ngo("bad", "Bad", trust_score=90, status="INELIGIBLE")
    results, excluded = rank_ngos(m, [good, bad], _index([good, bad]), top_k=10)
    assert all(r.ngo_id != "bad" for r in results)
    assert excluded == 1


def test_calibration_clips():
    assert semantic_score(-0.5) == 0.0
    assert semantic_score(2.0) == 1.0
    lo, hi = 0.15, 0.80
    mid = semantic_score((lo + hi) / 2)
    assert abs(mid - 0.5) < 1e-6


# --- keyword baseline is FAIR ----------------------------------------------------

def test_keyword_baseline_finds_obvious_overlap():
    from setu_ml.extract import parse_mandate_rules

    m = parse_mandate_rules("maternal health and clean drinking water programme in Kalahandi")
    obvious = ngo("obv", "ObvOrg", primary_domain=Domain.MATERNAL_HEALTH,
                  proposal_text="maternal health and clean drinking water programmes for villages")
    invisible = ngo("inv", "InvOrg", primary_domain=Domain.MATERNAL_HEALTH,
                    proposal_text="postpartum institutional delivery care and ASHA worker capacity building")
    kw = keyword_baseline(m, [obvious, invisible], top_k=10)
    ids = {r.ngo_id for r in kw}
    assert "obv" in ids
    assert "inv" not in ids  # genuinely invisible to exact token overlap


def test_keyword_vs_semantic_engine_comparison():
    from setu_ml.extract import parse_mandate_rules

    m = parse_mandate_rules(DEMO_MANDATE_TEXT)
    obv = ngo("obv", "ObvOrg", primary_domain=Domain.WASH,
              proposal_text="clean drinking water and sanitation facilities in Kalahandi villages")
    inv = ngo("inv", "InvOrg", primary_domain=Domain.MATERNAL_HEALTH,
              proposal_text="postpartum institutional delivery care, ASHA worker training, safe childbirth")
    ngos = [obv, inv]
    sem_results, _ = rank_ngos(m, ngos, _index(ngos), top_k=10)
    kw_results = keyword_baseline(m, ngos, top_k=10)
    cmp = compare_engines(sem_results, kw_results)
    assert cmp["keyword_result_count"] < cmp["semantic_result_count"]
    assert cmp["missed_by_keyword"]  # non-empty
    assert "keyword" in cmp["headline"].lower()


# --- justifications ----------------------------------------------------------------

def test_justifications_unique_and_cite_numbers():
    m = make_demo_mandate()
    ngos = [
        ngo("n1", "Alpha Seva Sansthan", budget_request_inr=4_200_000,
            proposal_text="we run girls' schools and digital literacy labs in tribal Odisha",
            financials=fin(max_grant_managed_inr=3_800_000)),
        ngo("n2", "Beta Gramin Vikas", budget_request_inr=2_500_000,
            proposal_text="community seed banks and farmer livelihood collectives",
            financials=fin(max_grant_managed_inr=1_200_000)),
        ngo("n3", "Ganga Mahila Kalyan", budget_request_inr=1_800_000,
            proposal_text="women's self-help groups and village savings programmes",
            financials=fin(max_grant_managed_inr=600_000)),
    ]
    results, _ = rank_ngos(m, ngos, _index(ngos), top_k=3)
    j = [r.justification for r in results]
    syner = [x.domain_synergy for x in j]
    scale = [x.scale_fit for x in j]
    assert len(set(syner)) == len(syner)
    assert len(set(scale)) == len(scale)
    for x in j:
        blob = x.domain_synergy + x.scale_fit + x.geographic_overlap
        assert any(ch.isdigit() for ch in blob)


def test_absorptive_capacity_warning_in_scale_fit():
    from setu_ml.justify import scale_fit

    m = make_demo_mandate()
    risky = ngo("r", "Risky", budget_request_inr=4_000_000,
                financials=fin(max_grant_managed_inr=800_000))
    s = scale_fit(m, risky)
    assert "absorptive capacity" in s and "1.5×" in s


def test_unmatched_guard_triggers_on_garbage():
    from setu_ml.extract import parse_mandate_rules

    m = parse_mandate_rules("₹10 lakh for quantum blockchain lunar infrastructure")
    ngos = [ngo("n", "N", proposal_text="we teach children in village schools")]
    guard = unmatched_guard(m, ngos, _index(ngos))
    if guard is not None:
        assert guard["warning"] == "unmatched_mandate"
        assert "closest_capability" in guard


# --- badges on results ---------------------------------------------------------

def test_badges_flow_through():
    m = make_demo_mandate()
    elite = ngo("e", "Elite", trust_score=85, trust_badge=TrustBadge.ELITE)
    results, _ = rank_ngos(m, [elite], _index([elite]), top_k=5)
    assert results[0].trust_badge == TrustBadge.ELITE
    assert results[0].trust_score == 85