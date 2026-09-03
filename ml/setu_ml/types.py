"""setu_ml.types — the shared vocabulary (Task A, item A1).

Field-naming contract (00-PROJECT-CONTEXT.md §6):
  - snake_case everywhere
  - money: paise-free integer rupees with an `_inr` suffix
  - scores in [0,1] EXCEPT trust_score which is 0–100
  - timestamps ISO-8601 UTC with a Z

This module is dependency-light (pydantic only) so the backend installs it
even when torch/sentence-transformers are unavailable (demo mode).
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

ALGORITHM_VERSION = "setu-1.0.0"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Domain(str, Enum):
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    MATERNAL_HEALTH = "maternal_health"
    WASH = "wash"  # water, sanitation, hygiene
    ENVIRONMENT = "environment"
    SKILLING = "skilling"
    LIVELIHOODS = "livelihoods"
    NUTRITION = "nutrition"
    DISABILITY = "disability"
    RURAL_DEVELOPMENT = "rural_development"


class TrustBadge(str, Enum):
    ELITE = "Verified Elite"
    STANDARD = "Standard Audited"
    INCOMPLETE = "Verification Incomplete"
    HIGH_RISK = "High Risk — Review Required"
    INELIGIBLE = "Ineligible for CSR Funds"


class DistrictRef(BaseModel):
    district: str
    state: str
    lat: float
    lng: float
    is_aspirational: bool = False


class RequirementUnit(BaseModel):
    """One cell of the mandate: a domain in a district. The atom of coverage."""

    domain: Domain
    district: str
    state: str
    weight: float = 1.0


class Mandate(BaseModel):
    mandate_id: str | None = None
    raw_text: str
    domains: list[Domain] = Field(default_factory=list)
    budget_inr: int = 0
    districts: list[DistrictRef] = Field(default_factory=list)
    duration_months: int | None = None
    beneficiary_profile: str | None = None
    preferences: list[str] = Field(default_factory=list)
    foreign_funded: bool = False
    field_confidence: dict[str, float] = Field(default_factory=dict)
    clarifying_questions: list[str] = Field(default_factory=list)
    requirement_units: list[RequirementUnit] = Field(default_factory=list)

    # §5.8 / A4 helper — kept on the model so backend and ML agree by construction.
    def build_requirement_units(self) -> list[RequirementUnit]:
        units: list[RequirementUnit] = []
        for dom in self.domains:
            for dref in self.districts:
                units.append(
                    RequirementUnit(
                        domain=dom,
                        district=dref.district,
                        state=dref.state,
                        weight=1.0,
                    )
                )
        return units


class NgoFinancials(BaseModel):
    admin_expense_inr: int
    programme_expense_inr: int
    total_expense_inr: int
    beneficiaries_reached: int
    max_grant_managed_inr: int
    growth_rate_yoy: float | None = None
    staff_count: int | None = None

    @property
    def admin_ratio(self) -> float:
        return self.admin_expense_inr / max(self.total_expense_inr, 1)

    @property
    def cost_per_beneficiary_inr(self) -> float:
        return self.programme_expense_inr / max(self.beneficiaries_reached, 1)


class TrackRecord(BaseModel):
    projects_total: int
    projects_completed: int
    milestones_met: int
    milestones_total: int
    years_active: int
    past_corporate_partners: list[str] = Field(default_factory=list)


class EvidenceRef(BaseModel):
    """One anchored piece of evidence: {doc_id, page, snippet, offsets, confidence}."""

    doc_id: str
    kind: str  # csr1 | reg_12a | reg_80g | darpan | fcra | audit | impact | citation | site_visit
    page: int = 1
    snippet: str = ""
    char_start: int = 0
    char_end: int = 0
    confidence: float = 1.0
    present: bool = True
    valid_from: str | None = None
    valid_to: str | None = None
    is_expired: bool = False
    evidence_age_days: int = 0
    extraction_note: str | None = None


class ComplianceEvidence(BaseModel):
    """Aggregated artefact-level evidence for one NGO — `compute_trust` input."""

    ngo_id: str = ""
    csr1: EvidenceRef | None = None
    reg_12a: EvidenceRef | None = None
    reg_80g: EvidenceRef | None = None
    darpan: EvidenceRef | None = None
    fcra: EvidenceRef | None = None
    audit_fy: EvidenceRef | None = None
    third_party_audit: EvidenceRef | None = None
    impact_assessment: EvidenceRef | None = None
    peer_or_media_citation: EvidenceRef | None = None
    site_visit_log: EvidenceRef | None = None

    def items(self) -> dict[str, EvidenceRef | None]:
        return {
            "csr1": self.csr1,
            "reg_12a": self.reg_12a,
            "reg_80g": self.reg_80g,
            "darpan": self.darpan,
            "fcra": self.fcra,
            "audit_fy": self.audit_fy,
            "third_party_audit": self.third_party_audit,
            "impact_assessment": self.impact_assessment,
            "peer_or_media_citation": self.peer_or_media_citation,
            "site_visit_log": self.site_visit_log,
        }

    def with_override(self, key: str, ref: EvidenceRef) -> "ComplianceEvidence":
        """A *pure* copy with one evidence item replaced — this is how the
        counterfactual engine builds hypothetical evidence sets without
        mutating shared state (A9 round-trip guarantee)."""
        data = self.model_copy(deep=True).model_dump()
        data[key] = ref.model_dump()
        return ComplianceEvidence.model_validate(data)


class PillarBreakdown(BaseModel):
    pillar: Literal["compliance", "financial", "operational", "external"]
    raw: float
    effective: float
    freshness: float
    freshness_days: int
    half_life_days: int
    weight: float
    contribution: float  # 100 * weight * effective
    evidence: list[EvidenceRef] = Field(default_factory=list)
    no_evidence: bool = False
    notes: list[str] = Field(default_factory=list)


class AnomalyFlag(BaseModel):
    metric: str
    direction: Literal["above", "below"]
    z_score: float
    value: float
    cohort_median: float
    cohort_size: int
    flag_text: str


class AnomalyReport(BaseModel):
    ngo_id: str
    cohort_key: tuple[str, str, str]
    cohort_size: int
    insufficient_cohort: bool
    penalty: float
    flags: list[AnomalyFlag] = Field(default_factory=list)


class ShellNetworkInfo(BaseModel):
    flagged: bool
    component_id: str | None = None
    shared_identifier_types: list[str] = Field(default_factory=list)
    member_ngo_ids: list[str] = Field(default_factory=list)


class TrustBreakdown(BaseModel):
    ngo_id: str
    score: float  # 0–100
    badge: TrustBadge
    is_ineligible: bool
    pillars: list[PillarBreakdown]
    anomaly_penalty: float = 0.0
    shell_penalty: float = 0.0
    shell_network: ShellNetworkInfo | None = None
    anomaly_flags: list[str] = Field(default_factory=list)
    algorithm_version: str = ALGORITHM_VERSION
    input_hash: str
    computed_at: datetime = Field(default_factory=utc_now)


class NgoProfile(BaseModel):
    ngo_id: str
    name: str
    primary_domain: Domain
    secondary_domains: list[Domain] = Field(default_factory=list)
    districts_covered: list[DistrictRef] = Field(default_factory=list)
    base_district: str
    base_state: str
    proposal_text: str
    budget_request_inr: int
    financials: NgoFinancials
    track_record: TrackRecord
    # Trust is computed by the backend's trust service (pure function); ML consumes it.
    trust_score: int = 0
    trust_badge: TrustBadge = TrustBadge.INCOMPLETE
    status: Literal["ACTIVE", "INELIGIBLE", "FLAGGED"] = "ACTIVE"
    freshness_days: int = 0


class Justification(BaseModel):
    domain_synergy: str
    scale_fit: str
    geographic_overlap: str


class MatchResult(BaseModel):
    ngo_id: str
    name: str
    final_score: float
    semantic_score: float  # calibrated, for display
    semantic_cosine_raw: float  # raw, for ranking and honesty
    trust_score: int
    trust_badge: TrustBadge
    geo_score: float
    budget_request_inr: int
    base_district: str
    base_state: str
    districts_covered: list[str]
    cost_per_beneficiary_inr: float
    flags: list[str] = Field(default_factory=list)
    freshness_days: int = 0
    justification: Justification
    sdg_tags: list[dict[str, Any]] = Field(default_factory=list)


class ConsortiumMember(BaseModel):
    ngo_id: str
    name: str
    trust_score: int
    covers: list[RequirementUnit]
    unique_units: int
    budget_share_inr: int
    share_pct: float
    absorptive_cap_inr: int
    capped: bool


class Consortium(BaseModel):
    consortium_id: str
    members: list[ConsortiumMember]
    coverage: float
    redundancy: float
    trust_weighted: float
    coordination_cost: float
    score: float
    beats_best_single_by: float
    unallocated_inr: int
    rationale: str
    best_single_coverage: float
    n_units: int


class CounterfactualAction(BaseModel):
    label: str
    delta_points: float
    resulting_score: float
    resulting_badge: TrustBadge
    effort: Literal["upload", "obtain_registration", "structural"]
    evidence_required: str
    evidence_key: str  # key in ComplianceEvidence
    sentence: str  # the exact line the UI renders
    actionable: bool = True


class CounterfactualReport(BaseModel):
    ngo_id: str
    current_score: float
    current_badge: TrustBadge
    achievable_ceiling: float
    actions: list[CounterfactualAction]


class Outcome(BaseModel):
    ngo_id: str
    mandate_id: str
    predicted_impact: float
    realised_impact: float
    completed_at: datetime = Field(default_factory=utc_now)


class ShellEdge(BaseModel):
    source: str
    target: str
    shared_types: list[str]


class ShellNetworkComponent(BaseModel):
    component_id: str
    member_ngo_ids: list[str]
    shared_identifier_types: list[str]
    edges: list[ShellEdge]
    flagged: bool


DEFAULT_WEIGHTS: dict[str, float] = {"semantic": 0.50, "trust": 0.30, "geo": 0.20}

# §5.9 — never suggest these; suggesting them is insulting and destroys trust.
NEVER_SUGGEST: frozenset[str] = frozenset(
    {
        "change_historical_completion_rate",
        "change_years_active",
        "change_past_beneficiary_counts",
    }
)
