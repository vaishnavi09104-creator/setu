"""app.models — request/response models mirroring §6 EXACTLY.

snake_case on the wire; money integer rupees with `_inr`; scores [0,1] except
trust_score 0–100; ISO-8601 UTC timestamps. Task C builds against these keys.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    code: str
    message: str
    detail: dict[str, Any] = Field(default_factory=dict)


class ErrorEnvelope(BaseModel):
    error: ErrorBody


class HealthResponse(BaseModel):
    status: str
    algorithm_version: str
    demo_mode: bool
    ngo_count: int
    index_ready: bool
    model_loaded: bool


class ParseMandateRequest(BaseModel):
    text: str


class ParsedMandateResponse(BaseModel):
    mandate_id: str | None = None
    raw_text: str
    domains: list[str]
    budget_inr: int
    districts: list[dict[str, Any]]
    duration_months: int | None = None
    beneficiary_profile: str | None = None
    preferences: list[str]
    foreign_funded: bool
    field_confidence: dict[str, float]
    clarifying_questions: list[str]
    requirement_units: list[dict[str, Any]]
    confidence_note: str = (
        "Confidence chips: 1.0 explicit pattern · 0.5 inferred · 0.0 defaulted."
    )


class CreateMandateRequest(BaseModel):
    corporate_id: str = "corp_demo"
    raw_text: str
    parsed: dict[str, Any] | None = None


class MandateCreatedResponse(BaseModel):
    mandate_id: str


class WeightModel(BaseModel):
    semantic: float = 0.50
    trust: float = 0.30
    geo: float = 0.20


class MatchRequest(BaseModel):
    mandate_id: str | None = None
    mandate_inline: str | None = None
    top_k: int = 10
    mode: Literal["single", "consortium", "both"] = "both"
    weights: WeightModel | None = None
    use_keyword_baseline: bool = False
    include_pareto: bool = True
    include_rank_stability: bool = True
    foreign_funded: bool = False


class JustificationModel(BaseModel):
    domain_synergy: str
    scale_fit: str
    geographic_overlap: str


class MatchResultModel(BaseModel):
    ngo_id: str
    name: str
    final_score: float
    semantic_score: float
    semantic_cosine_raw: float
    trust_score: int
    trust_badge: str
    geo_score: float
    budget_request_inr: int
    base_district: str
    base_state: str
    districts_covered: list[str]
    cost_per_beneficiary_inr: float
    flags: list[str]
    freshness_days: int
    justification: JustificationModel
    evidence_summary: dict[str, Any] = Field(default_factory=dict)
    sdg_tags: list[dict[str, Any]] = Field(default_factory=list)


class ConsortiumMemberModel(BaseModel):
    ngo_id: str
    name: str
    trust_score: int
    covers: list[dict[str, Any]]
    unique_units: int
    budget_share_inr: int
    share_pct: float
    absorptive_cap_inr: int
    capped: bool


class ConsortiumModel(BaseModel):
    consortium_id: str
    members: list[ConsortiumMemberModel]
    coverage: float
    redundancy: float
    trust_weighted: float
    coordination_cost: float
    score: float
    beats_best_single_by: float
    unallocated_inr: int
    rationale: str
    best_single_coverage: float = 0.0
    n_units: int = 0


class MatchResponse(BaseModel):
    algorithm_version: str
    input_hash: str
    latency_ms: float
    mode_used: str
    engine: str
    excluded_ineligible_count: int
    unmatched_warning: dict[str, Any] | None = None
    results: list[MatchResultModel]
    consortiums: list[ConsortiumModel] = Field(default_factory=list)
    pareto_front: list[str] = Field(default_factory=list)
    rank_stability: dict[str, dict[str, float]] = Field(default_factory=dict)
    keyword_baseline_comparison: dict[str, Any] | None = None


class EvidenceRefModel(BaseModel):
    doc_id: str
    kind: str
    page: int
    snippet: str
    char_start: int = 0
    char_end: int = 0
    confidence: float = 1.0


class PillarModel(BaseModel):
    pillar: str
    label: str
    weight: float
    raw: float
    effective: float
    freshness: float
    freshness_days: int
    half_life_days: int
    contribution: float
    evidence: list[EvidenceRefModel]
    no_evidence: bool = False
    notes: list[str] = Field(default_factory=list)


class TrustDossierResponse(BaseModel):
    ngo_id: str
    score: float
    badge: str
    is_ineligible: bool
    anomaly_penalty: float
    shell_penalty: float
    pillars: list[PillarModel]
    anomaly_flags: list[str]
    shell_network: dict[str, Any] | None = None
    last_verified_months_ago: int | None = None
    algorithm_version: str
    input_hash: str
    computed_at: str


class CounterfactualActionModel(BaseModel):
    label: str
    delta_points: float
    resulting_score: float
    resulting_badge: str
    effort: str
    evidence_required: str
    sentence: str
    actionable: bool = True


class CounterfactualResponse(BaseModel):
    ngo_id: str
    current_score: float
    current_badge: str
    achievable_ceiling: float
    actions: list[CounterfactualActionModel]


class NetworkResponse(BaseModel):
    flagged: bool
    component_id: str | None = None
    members: list[dict[str, Any]]
    shared_identifier_types: list[str]
    edges: list[dict[str, Any]]


class UploadResponse(BaseModel):
    doc_id: str
    kind_detected: str
    page_count: int
    extracted: dict[str, Any]
    warnings: list[str]
    forensics: dict[str, Any]
    extraction_confidence: float


class VerifyRequest(BaseModel):
    ngo_id: str


class VerifyResponse(BaseModel):
    ngo_id: str
    before: dict[str, Any]
    after: dict[str, Any]
    delta_points: float
    notes: list[str]


class GeoCoverageFeature(BaseModel):
    type: str = "Feature"
    properties: dict[str, Any]


class GeoCoverageResponse(BaseModel):
    type: str = "FeatureCollection"
    features: list[GeoCoverageFeature]


class RfpRequest(BaseModel):
    mandate_id: str
    ngo_ids: list[str]
    message: str = ""


class RfpResponse(BaseModel):
    rfp_id: str
    status: str
    recipients: list[str]


class OutcomeRequest(BaseModel):
    ngo_id: str
    mandate_id: str
    predicted_impact: float
    realised_impact: float


class CalibrationBucket(BaseModel):
    bucket: int
    mean_predicted: float
    mean_realised: float
    count: int


class AuditResponse(BaseModel):
    entries: list[dict[str, Any]]
    chain: dict[str, Any] | None = None


class ReviewNoteIn(BaseModel):
    ngo_id: str
    body: str


class ReviewNote(BaseModel):
    id: int
    corporate_id: str
    author: str
    ngo_id: str
    body: str
    created_at: str
