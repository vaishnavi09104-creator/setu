"""setu_ml — SETU matching & trust intelligence library.

A PURE Python library: no HTTP, no database, no global mutable state.
The backend imports it directly (`pip install -e ../ml`).

Module map (Task A items):
  types           A1  shared vocabulary (Pydantic models)
  embeddings      A2  local cached embeddings + NGO index
  geo             A3  haversine, district Jaccard, geo_score
  extract         A4  mandate NLU (rules primary, LLM optional, Hinglish)
  scoring         A5  composite score, rank entry, fair keyword baseline
  justify         A5  three grounded justification bullets
  calibrate       A6  percentile calibration fitting on the corpus
  trust           ref pure §5.2 trust implementation (shared by counterfactual)
  consortium      A7  weighted set-cover consortium engine  ★ headline
  anomaly         A8  cohort-relative robust anomaly detection ★ headline
  counterfactual  A9  the coaching engine (round-trip guaranteed)  ★ headline
  pareto          A10 non-dominated frontier
  stability       A10 rank-stability Monte Carlo (Dirichlet)
  sdg             A11 SDG auto-tagging
  outcomes        A12 feedback loop + calibration curve
  shellgraph      ref pure shell-network graph algorithm (Task B owns the service)
  lexicon         domain keywords shared by extract & justify
"""
from .types import (  # noqa: F401
    ALGORITHM_VERSION,
    AnomalyFlag,
    AnomalyReport,
    ComplianceEvidence,
    Consortium,
    ConsortiumMember,
    CounterfactualAction,
    CounterfactualReport,
    DEFAULT_WEIGHTS,
    Domain,
    DistrictRef,
    EvidenceRef,
    Justification,
    Mandate,
    MatchResult,
    NgoFinancials,
    NgoProfile,
    Outcome,
    PillarBreakdown,
    RequirementUnit,
    ShellEdge,
    ShellNetworkComponent,
    ShellNetworkInfo,
    TrackRecord,
    TrustBadge,
    TrustBreakdown,
    NEVER_SUGGEST,
)

__version__ = ALGORITHM_VERSION
