// Hand-transcribed from ml/setu_ml/types.py + §6 API contract.
// Field names are snake_case on the wire — do NOT camelCase.

export type TrustBadgeName =
  | "Verified Elite"
  | "Standard Audited"
  | "Verification Incomplete"
  | "High Risk — Review Required"
  | "Ineligible for CSR Funds";

export type MatchEngine = "semantic" | "keyword";

export interface ParsedMandate {
  mandate_id?: string;
  budget_inr: number | null;
  domains: string[];
  districts: string[];
  state: string | null;
  languages?: string[];
  foreign_funded: boolean;
  prefers_csr_experience: boolean;
  confidence: Record<string, "high" | "medium" | "low">;
  clarifying_questions: string[];
  raw_text: string;
}

export interface Justification {
  domain_synergy: string;
  scale_fit: string;
  geographic_overlap: string;
}

export interface EvidenceSummary {
  csr1: boolean;
  reg_12a: boolean;
  reg_80g: boolean;
  darpan: boolean;
  audit_fy: string | null;
}

export interface MatchResult {
  ngo_id: string;
  name: string;
  final_score: number;
  semantic_score: number;
  semantic_cosine_raw: number;
  trust_score: number;
  trust_badge: TrustBadgeName;
  geo_score: number;
  budget_request_inr: number;
  base_district: string;
  base_state: string;
  districts_covered: string[];
  cost_per_beneficiary_inr: number;
  flags: string[];
  freshness_days: number;
  years_active?: number;
  beneficiaries_reached?: number;
  admin_ratio?: number;
  justification: Justification;
  evidence_summary: EvidenceSummary;
}

export interface ConsortiumMember {
  ngo_id: string;
  name: string;
  trust_score: number;
  covers: { domain: string; districts: string[] }[];
  unique_units: number;
  budget_share_inr: number;
  share_pct: number;
  absorptive_cap_inr: number;
  capped: boolean;
}

export interface Consortium {
  consortium_id: string;
  members: ConsortiumMember[];
  coverage: number;
  redundancy: number;
  trust_weighted: number;
  coordination_cost: number;
  score: number;
  beats_best_single_by: number;
  unallocated_inr: number;
  rationale: string;
}

export interface RankStability {
  [ngoId: string]: { p_top1: number; p_top3: number };
}

export interface KeywordBaselineComparison {
  keyword_result_count: number;
  semantic_result_count: number;
  missed_by_keyword: string[];
  headline: string;
}

export interface MatchResponse {
  algorithm_version: string;
  input_hash: string;
  latency_ms: number;
  mode_used: "single" | "consortium" | "both";
  engine: MatchEngine;
  excluded_ineligible_count: number;
  unmatched_warning: string | null;
  results: MatchResult[];
  consortiums: Consortium[];
  pareto_front: string[];
  rank_stability: RankStability;
  keyword_baseline_comparison: KeywordBaselineComparison | null;
}

export interface MatchWeights {
  semantic: number;
  trust: number;
  geo: number;
}

export interface MatchRequest {
  mandate_id?: string;
  mandate_inline?: ParsedMandate | null;
  top_k?: number;
  mode?: "single" | "consortium" | "both";
  weights?: MatchWeights;
  use_keyword_baseline?: boolean;
  include_pareto?: boolean;
  include_rank_stability?: boolean;
  foreign_funded?: boolean;
}

export interface EvidenceItem {
  evidence_id: string;
  doc_id: string;
  doc_name: string;
  kind: string;
  page: number;
  snippet: string;
  char_offsets: [number, number];
  confidence: number;
  age_days: number;
  no_evidence?: boolean;
}

export interface TrustPillar {
  key: "compliance" | "financial" | "operational" | "external";
  label: string;
  weight: number;
  raw: number;
  freshness: number;
  effective: number;
  contribution: number;
  no_evidence: boolean;
  evidence: EvidenceItem[];
}

export interface TrustDossier {
  ngo_id: string;
  name: string;
  trust_score: number;
  badge: TrustBadgeName;
  pillars: TrustPillar[];
  anomaly_penalty: number;
  shell_penalty: number;
  flagged_metrics?: { metric: string; z_score: number; direction: string }[];
  last_verified_days_ago: number;
  algorithm_version: string;
  input_hash: string;
}

export interface CounterfactualAction {
  action_id: string;
  label: string;
  delta: number;
  effort: "low" | "medium" | "high";
  effort_class: "actionable" | "structural";
  explanation: string;
  threshold_crossed?: string | null;
}

export interface CounterfactualResponse {
  ngo_id: string;
  name: string;
  current: number;
  achievable_ceiling: number;
  actions: CounterfactualAction[];
  combined_projection?: number | null;
  algorithm_version: string;
}

export interface NetworkMember {
  ngo_id: string;
  name: string;
  base_district: string;
}

export interface NetworkResponse {
  flagged: boolean;
  members: NetworkMember[];
  shared_identifier_types: string[];
  explanation: string;
}

export interface NgoProfile {
  ngo_id: string;
  name: string;
  base_district: string;
  base_state: string;
  primary_domain: string;
  trust_score: number;
  trust_badge: TrustBadgeName;
  years_active: number;
  beneficiaries_reached: number;
  cost_per_beneficiary_inr: number;
  admin_ratio: number;
  lat: number;
  lng: number;
  domains: string[];
  districts_covered: string[];
}

export interface CoverageFeature {
  type: "Feature";
  geometry: { type: "Polygon"; coordinates: number[][][] };
  properties: {
    district: string;
    state: string;
    ngo_count: number;
    verified_count: number;
    need_index: number;
    is_aspirational: boolean;
    gap_score: number;
  };
}

export interface CoverageResponse {
  type: "FeatureCollection";
  features: CoverageFeature[];
}

export interface AuditEntry {
  entry_id: string;
  timestamp: string;
  actor_role: string;
  action: string;
  entity_id: string;
  payload_digest: string;
  prev_hash: string;
  hash: string;
}

export interface HealthResponse {
  status: string;
  algorithm_version: string;
  demo_mode: boolean;
  ngo_count: number;
  index_ready: boolean;
  model_loaded: boolean;
}

export interface DocumentUploadResponse {
  doc_id: string;
  kind_detected: string;
  extracted: Record<string, unknown>;
  page_count: number;
  warnings: string[];
}

export type BadgeLevel = "high" | "medium" | "low";
