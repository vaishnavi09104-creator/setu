"""A7 ★ — consortium engine: the seven hand-constructed cases."""
from __future__ import annotations

import random

import pytest

from setu_ml.consortium import (
    absorptive_cap,
    coverage,
    find_consortiums,
    is_valid,
    redundancy,
    split_budget,
    unique_units,
)
from setu_ml.embeddings import build_ngo_index
from setu_ml.extract import parse_mandate_rules
from setu_ml.types import Domain, RequirementUnit

from factories import DEMO_MANDATE_TEXT, financials, ngo, odisha_districts


def units_from(domains: list[str], districts: list[str]) -> list[RequirementUnit]:
    return [
        RequirementUnit(domain=Domain(d), district=dist, state="Odisha")
        for d in domains
        for dist in districts
    ]


MAT_WASH_UNITS = units_from(["maternal_health", "wash"],
                            ["Kalahandi", "Nuapada", "Balangir"])  # 6 units


# --- Case 1: known-optimal pair -------------------------------------------------

def _case1_ngos():
    u = MAT_WASH_UNITS[:6]
    # X: maternal in K+N · Y: wash in K+B+Nu · Z: maternal K + wash K
    x = ngo("x", "X Org", primary_domain=Domain.MATERNAL_HEALTH,
            districts_covered=odisha_districts("Kalahandi", "Nuapada"), trust_score=80)
    y = ngo("y", "Y Org", primary_domain=Domain.WASH,
            districts_covered=odisha_districts("Kalahandi", "Nuapada", "Balangir"), trust_score=80)
    z = ngo("z", "Z Org", primary_domain=Domain.WASH,
            secondary_domains=[Domain.MATERNAL_HEALTH],
            districts_covered=odisha_districts("Kalahandi", "Nuapada", "Balangir"), trust_score=80)
    return u, x, y, z


def test_known_optimal_pair():
    u, x, y, z = _case1_ngos()
    # X∪Y or X∪Z must cover all 6; both valid; ranking picks the higher scorer
    cy = coverage([x, y], u)
    cz = coverage([x, z], u)
    assert cy == 1.0 or cz == 1.0
    assert is_valid([x, y], u, best_single_coverage=0.5)[0] or \
           is_valid([x, z], u, best_single_coverage=0.5)[0]


# --- Case 2: single wins → no consortium ------------------------------------------

def test_single_wins_rejects_pointless_pair():
    u = units_from(["maternal_health"], ["Kalahandi", "Nuapada"])
    super_ngo = ngo("s", "SuperOrg", primary_domain=Domain.MATERNAL_HEALTH,
                    districts_covered=odisha_districts("Kalahandi", "Nuapada"),
                    trust_score=85)
    other = ngo("o", "OtherOrg", primary_domain=Domain.MATERNAL_HEALTH,
                districts_covered=odisha_districts("Kalahandi"), trust_score=80)
    best_single = coverage([super_ngo], u)  # 1.0 — full coverage alone
    # a pair whose coverage (1.0) does not exceed best_single + 0.10
    ok, reason = is_valid([super_ngo, other], u, best_single_coverage=best_single)
    assert not ok
    # either the passenger rule or the coverage rule rejects it — both are
    # correct outcomes of "the single NGO should win"
    assert "passenger" in reason or "10 points" in reason or "single" in reason


# --- Case 3: passenger rejected ----------------------------------------------------

def test_passenger_rejected():
    u = units_from(["wash"], ["Kalahandi", "Nuapada", "Balangir"])
    big = ngo("b", "BigOrg", primary_domain=Domain.WASH,
              districts_covered=odisha_districts("Kalahandi", "Nuapada", "Balangir"),
              trust_score=80)
    subset = ngo("s", "SubsetOrg", primary_domain=Domain.WASH,
                 districts_covered=odisha_districts("Kalahandi"), trust_score=80)
    assert unique_units(subset, [big], u) == 0
    ok, reason = is_valid([big, subset], u, best_single_coverage=0.5)
    assert not ok
    assert "passenger" in reason


# --- Case 4: trust floor -----------------------------------------------------------

def test_trust_floor_rejects_weak_link():
    u = units_from(["maternal_health", "wash"], ["Kalahandi", "Nuapada"])
    a = ngo("a", "A", primary_domain=Domain.MATERNAL_HEALTH,
            districts_covered=odisha_districts("Kalahandi"), trust_score=84)
    weak = ngo("w", "W", primary_domain=Domain.WASH,
               districts_covered=odisha_districts("Nuapada"), trust_score=40)
    ok, reason = is_valid([a, weak], u, best_single_coverage=0.25)
    assert not ok
    assert "trust" in reason.lower()


# --- Case 5: budget conservation over 50 random runs ---------------------------------

def test_budget_conservation_50_runs():
    rng = random.Random(7)
    u = units_from(["maternal_health", "wash"], ["Kalahandi", "Nuapada", "Balangir"])
    for _ in range(50):
        n = rng.randint(2, 3)
        members = [
            ngo(f"m{i}", f"M{i}", primary_domain=Domain.MATERNAL_HEALTH,
                districts_covered=odisha_districts("Kalahandi", "Nuapada"),
                trust_score=70,
                financials=financials(max_grant_managed_inr=rng.randint(2, 80) * 100_000))
            for i in range(n)
        ]
        budget = rng.randint(2_000_000, 80_000_000)
        shares, unallocated, _ = split_budget(members, u, budget)
        assert sum(shares) + unallocated == budget


def test_budget_exact_no_rounding_leak():
    u = units_from(["wash"], ["Kalahandi", "Nuapada"])
    a = ngo("a", "A", primary_domain=Domain.WASH,
            districts_covered=odisha_districts("Kalahandi"), trust_score=80)
    b = ngo("b", "B", primary_domain=Domain.WASH,
            districts_covered=odisha_districts("Nuapada"), trust_score=80)
    shares, unalloc, _ = split_budget([a, b], u, 5_000_001)  # odd number
    assert sum(shares) + unalloc == 5_000_001


# --- Case 6: capacity cap bites -------------------------------------------------------

def test_capacity_cap_bites():
    u = units_from(["maternal_health", "wash"], ["Kalahandi", "Nuapada"])
    big = ngo("big", "BigOrg", primary_domain=Domain.MATERNAL_HEALTH,
              districts_covered=odisha_districts("Kalahandi"),
              trust_score=85,
              financials=financials(max_grant_managed_inr=40_000_000))
    tiny = ngo("tiny", "TinyOrg", primary_domain=Domain.WASH,
               districts_covered=odisha_districts("Nuapada"),
               trust_score=85,
               financials=financials(max_grant_managed_inr=800_000))
    assert absorptive_cap(tiny) == 1_200_000  # 1.5×₹8L
    shares, unalloc, capped = split_budget([big, tiny], u, 50_000_000)
    assert capped[1] is True
    assert shares[1] <= 1_200_000
    assert sum(shares) + unalloc == 50_000_000
    assert unalloc == 50_000_000 - sum(shares)  # residual honestly reported


def test_absorptive_cap_floor():
    newborn = ngo("nb", "NewOrg", primary_domain=Domain.EDUCATION,
                  financials=financials(max_grant_managed_inr=0))
    assert absorptive_cap(newborn) == 200_000


# --- Case 7: the demo case — unfillable mandate solved by a pair ------------------------

def _demo_world():
    """Two complementary partners cover all 6 units; best single ≤ 3 of 6."""
    maternal_partner = ngo(
        "mp", "Ashadeep Maternal Care Trust",
        primary_domain=Domain.MATERNAL_HEALTH,
        secondary_domains=[],
        districts_covered=odisha_districts("Kalahandi", "Nuapada", "Balangir"),
        trust_score=84,
        proposal_text="postpartum institutional delivery care and ASHA worker training",
    )
    wash_partner = ngo(
        "wp", "Jal Seva WASH Foundation",
        primary_domain=Domain.WASH,
        secondary_domains=[],
        districts_covered=odisha_districts("Kalahandi", "Nuapada", "Balangir"),
        trust_score=78,
        financials=financials(max_grant_managed_inr=800_000),  # capped member
        proposal_text="clean drinking water, sanitation and hygiene in tribal districts",
    )
    filler = [
        ngo(f"f{i}", f"Filler {i}", primary_domain=Domain.EDUCATION,
            districts_covered=odisha_districts("Kalahandi"), trust_score=70,
            proposal_text="remedial education and library programmes for rural children")
        for i in range(6)
    ]
    mandate = parse_mandate_rules(DEMO_MANDATE_TEXT)
    return mandate, [maternal_partner, wash_partner, *filler]


def test_demo_case_best_single_below_70_and_consortium_reaches_95():
    mandate, world = _demo_world()
    u = mandate.requirement_units
    assert len(u) == 6
    mp = next(n for n in world if n.ngo_id == "mp")
    wp = next(n for n in world if n.ngo_id == "wp")
    best_single = max(coverage([n], u) for n in world)
    assert best_single < 0.70, f"best single covers {best_single:.0%} — seed broken"
    assert coverage([mp, wp], u) == 1.0
    assert redundancy([mp, wp], u) == 0.0  # disjoint domains → no overlap
    idx = build_ngo_index(world)
    consortia = find_consortiums(mandate, world, idx, top_n=3)
    assert consortia, "no consortium found — demo beat 7 does not exist"
    top = consortia[0]
    assert top.coverage >= 0.95
    assert {m.ngo_id for m in top.members} == {"mp", "wp"}
    assert sum(m.budget_share_inr for m in top.members) + top.unallocated_inr == 5_000_000
    capped = [m for m in top.members if m.capped]
    assert len(capped) == 1 and capped[0].ngo_id == "wp"
    assert "absorptive capacity" in top.rationale


def test_three_member_loses_on_coordination_cost():
    """A 3-member split exists but coordination cost makes the pair score higher."""
    mandate, world = _demo_world()
    idx = build_ngo_index(world)
    top = find_consortiums(mandate, world, idx, top_n=3)[0]
    assert len(top.members) == 2
    assert top.coordination_cost == 0.05
