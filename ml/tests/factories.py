"""Shared test fixtures: synthetic NGO factories + the seeded narrative cases."""
from __future__ import annotations

import pytest

from setu_ml.types import (
    ComplianceEvidence,
    DistrictRef,
    Domain,
    EvidenceRef,
    Mandate,
    NgoFinancials,
    NgoProfile,
    TrackRecord,
    TrustBadge,
)


def dref(district: str, state: str, lat: float, lng: float, aspir: bool = False) -> DistrictRef:
    return DistrictRef(district=district, state=state, lat=lat, lng=lng, is_aspirational=aspir)


ODISHA = {
    "Kalahandi": (19.91, 83.16, True),
    "Nuapada": (20.11, 82.54, True),
    "Balangir": (20.71, 83.48, True),
}
MAHARASHTRA = {
    "Gadchiroli": (20.10, 80.02, True),
    "Nagpur": (21.15, 79.09, False),
    "Pune": (18.52, 73.86, False),
}


def odisha_districts(*names: str) -> list[DistrictRef]:
    return [dref(n, "Odisha", *ODISHA[n]) for n in names]


def financials(**over) -> NgoFinancials:
    base = dict(
        admin_expense_inr=1_800_000,
        programme_expense_inr=8_200_000,
        total_expense_inr=10_000_000,
        beneficiaries_reached=8_000,
        max_grant_managed_inr=3_800_000,
        growth_rate_yoy=0.08,
        staff_count=24,
    )
    base.update(over)
    return NgoFinancials(**base)


def track_record(**over) -> TrackRecord:
    base = dict(
        projects_total=12,
        projects_completed=10,
        milestones_met=34,
        milestones_total=40,
        years_active=9,
        past_corporate_partners=["Tata Trusts", "L&T"],
    )
    base.update(over)
    return TrackRecord(**base)


def ngo(ngo_id: str, name: str, **over) -> NgoProfile:
    proposal = over.pop(
        "proposal_text",
        "We run community programmes across education and livelihoods with "
        "measurable outcomes and third-party evaluation.",
    )
    base = dict(
        ngo_id=ngo_id,
        name=name,
        primary_domain=Domain.EDUCATION,
        secondary_domains=[],
        districts_covered=odisha_districts("Kalahandi"),
        base_district="Kalahandi",
        base_state="Odisha",
        proposal_text=proposal,
        budget_request_inr=3_000_000,
        financials=financials(),
        track_record=track_record(),
        trust_score=75,
        trust_badge=TrustBadge.STANDARD,
        status="ACTIVE",
        freshness_days=90,
    )
    base.update(over)
    return NgoProfile(**base)


def ev(kind: str, age_days: int = 30, expired: bool = False,
       present: bool = True, doc: str = "doc_001") -> EvidenceRef:
    return EvidenceRef(
        doc_id=f"{doc}_{kind}",
        kind=kind,
        page=1,
        snippet=f"...{kind} evidence...",
        present=present,
        is_expired=expired,
        evidence_age_days=age_days if present else 0,
        confidence=0.95,
    )


def full_evidence(ngo_id: str = "ngo_x", **over) -> ComplianceEvidence:
    base = dict(
        ngo_id=ngo_id,
        csr1=ev("csr1"),
        reg_12a=ev("reg_12a"),
        reg_80g=ev("reg_80g"),
        darpan=ev("darpan"),
        audit_fy=ev("audit_fy"),
        third_party_audit=ev("third_party_audit"),
        impact_assessment=ev("impact_assessment"),
        peer_or_media_citation=ev("peer_or_media_citation"),
        site_visit_log=ev("site_visit_log"),
    )
    base.update(over)
    return ComplianceEvidence(**base)


DEMO_MANDATE_TEXT = (
    "₹50 lakh for maternal health and clean drinking water across Kalahandi, "
    "Nuapada and Balangir in Odisha, prefer partners with prior corporate CSR experience"
)


def make_demo_mandate() -> Mandate:
    from setu_ml.extract import parse_mandate_rules

    return parse_mandate_rules(DEMO_MANDATE_TEXT)


@pytest.fixture
def basic_ngo() -> NgoProfile:
    return ngo("ngo_001", "Ashadeep Gramin Vikas Samiti")
