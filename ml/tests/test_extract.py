"""A4 — mandate extraction: rules, confidence, clarifying questions, Hinglish."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from setu_ml.extract import (
    build_requirement_units,
    clarifying_questions,
    detect_domains,
    parse_budget_inr,
    parse_mandate,
    parse_mandate_rules,
)
from setu_ml.types import Domain, Mandate

FIXTURES = Path(__file__).parent / "fixtures"
CASES = json.loads((FIXTURES / "mandates.json").read_text(encoding="utf-8"))["mandates"]
BY_ID = {c["id"]: c for c in CASES}


def parse(cid: str) -> Mandate:
    return parse_mandate_rules(BY_ID[cid]["text"])


# --- budget, all Indian conventions -------------------------------------------

@pytest.mark.parametrize("text,expected", [
    ("₹50 lakh", 5_000_000),
    ("50 lakhs", 5_000_000),
    ("Rs. 50,00,000", 5_000_000),
    ("50L", 5_000_000),
    ("0.5 crore", 5_000_000),
    ("1.2 Cr", 12_000_000),
    ("INR 5000000", 5_000_000),
    ("₹1.5 crore", 15_000_000),
    ("50 lacs", 5_000_000),
])
def test_budget_conventions(text, expected):
    assert parse_budget_inr(text) == expected


def test_budget_none_when_absent():
    assert parse_budget_inr("we want to help children") is None


# --- domains -------------------------------------------------------------------

def test_maternal_health_keywords():
    doms = detect_domains("postpartum institutional delivery care and ASHA worker training")
    assert Domain.MATERNAL_HEALTH in [d for d, _ in doms]


def test_wash_health_pair():
    doms = [d for d, _ in detect_domains("clean drinking water and sanitation programme")]
    assert Domain.WASH in doms


def test_hinglish_domain():
    doms = [d for d, _ in detect_domains("girls ki education ke liye")]
    assert Domain.EDUCATION in doms


# --- the 12 canned mandates ------------------------------------------------------

def test_at_least_10_of_12_extract_budget():
    ok = sum(1 for c in CASES if parse(c["id"]).budget_inr == c["expect"]["budget_inr"])
    assert ok >= 10


def test_at_least_10_of_12_extract_domain_and_geo():
    ok = 0
    for c in CASES:
        m = parse(c["id"])
        has_dom = len(m.domains) >= 1
        has_geo = len(m.districts) >= 1
        if has_dom and has_geo:
            ok += 1
    assert ok >= 10


def test_demo_mandate_exact():
    m = parse("demo")
    assert m.budget_inr == 5_000_000
    assert {d.district for d in m.districts} == {"Kalahandi", "Nuapada", "Balangir"}
    assert Domain.MATERNAL_HEALTH in m.domains
    assert Domain.WASH in m.domains
    assert len(m.requirement_units) == 2 * 3  # 2 domains × 3 districts
    assert all(u.weight == 1.0 for u in m.requirement_units)
    assert m.field_confidence["budget"] == 1.0
    assert m.field_confidence["districts"] == 1.0
    assert "Prior corporate CSR experience" in m.preferences


def test_state_only_lowers_confidence_and_asks():
    m = parse("state_only")
    assert m.field_confidence["districts"] < 1.0
    assert len(m.districts) > 0  # expanded
    assert m.clarifying_questions  # a clarifying question is raised


def test_state_only_is_state_of_maharashtra():
    m = parse("state_only")
    assert all(d.state == "Maharashtra" for d in m.districts)


def test_crore_budget():
    assert parse("crore_budget").budget_inr == 15_000_000


def test_duration_extracted():
    assert parse("multi_domain_multi_district").duration_months == 24


def test_preferences_and_fcra_flag():
    m = parse("preferences")
    assert m.foreign_funded is True
    assert any("women-led" in p.lower() for p in m.preferences)


def test_vague_is_honest():
    m = parse("vague")
    assert m.budget_inr == 0
    assert m.field_confidence["budget"] == 0.0
    assert m.clarifying_questions  # not confidently wrong — asks instead


def test_hinglish_mandates():
    m = parse("hinglish")
    assert m.budget_inr == 4_000_000
    assert len(m.domains) >= 1
    m2 = parse("hinglish_odisha")
    assert m2.budget_inr == 5_000_000
    assert Domain.MATERNAL_HEALTH in m2.domains


def test_requirement_unit_count():
    m = parse("multi_domain_multi_district")
    assert len(build_requirement_units(m)) == len(m.domains) * len(m.districts)


def test_clarifying_questions_max_two():
    m = parse("vague")
    assert len(m.clarifying_questions) <= 2


# --- LLM path: falls back on any failure, never raises --------------------------

def test_parse_mandate_llm_none_client():
    m = parse_mandate("₹50 lakh for maternal health in Kalahandi", llm_client=None)
    assert m.budget_inr == 5_000_000


def test_parse_mandate_llm_raises_falls_back():
    class Exploding:
        def __call__(self, prompt):
            raise TimeoutError("6s timeout")

    m = parse_mandate("₹50 lakh for maternal health in Kalahandi", llm_client=Exploding())
    assert m.budget_inr == 5_000_000


def test_parse_mandate_llm_bad_json_falls_back():
    class BadJSON:
        def __call__(self, prompt):
            return "{not json"

    m = parse_mandate("50 lakh for WASH in Nuapada", llm_client=BadJSON())
    assert m.budget_inr == 5_000_000


def test_parse_mandate_llm_valid_output_used():
    class Good:
        def __call__(self, prompt):
            return {
                "domains": ["maternal_health"],
                "budget_inr": 5_000_000,
                "districts": [{"district": "Kalahandi", "state": "Odisha"}],
                "duration_months": None,
                "beneficiary_profile": None,
                "preferences": [],
                "foreign_funded": False,
            }

    m = parse_mandate("anything at all", llm_client=Good())
    assert m.budget_inr == 5_000_000
    assert Domain.MATERNAL_HEALTH in m.domains


def test_parse_mandate_llm_string_budget_coerced():
    class Sloppy:
        def __call__(self, prompt):
            return {"domains": ["wash"], "budget_inr": "50 lakh",
                    "districts": [{"district": "Nuapada", "state": "Odisha"}]}

    m = parse_mandate("whatever", llm_client=Sloppy())
    assert m.budget_inr == 5_000_000  # coerced, did not crash
