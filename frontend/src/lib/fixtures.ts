// Captured fixture responses — committed so the demo survives a dead backend.
// Shapes mirror §6 of the frozen API contract exactly.

import type {
  ParsedMandate, MatchResponse, TrustDossier, CounterfactualResponse,
  NetworkResponse, CoverageResponse, AuditEntry, HealthResponse, MatchResult,
  Consortium, NgoProfile,
} from "./types";

export const FIXTURE_HEALTH: HealthResponse = {
  status: "ok",
  algorithm_version: "setu-1.0.0",
  demo_mode: true,
  ngo_count: 48,
  index_ready: true,
  model_loaded: true,
};

const DEMO_TEXT =
  "₹50 lakh for maternal health and clean drinking water across Kalahandi, Nuapada and Balangir in Odisha, prefer partners with prior corporate CSR experience";

export const FIXTURE_PARSE_DEMO: ParsedMandate = {
  budget_inr: 5000000,
  domains: ["maternal_health", "clean_water"],
  districts: ["Kalahandi", "Nuapada", "Balangir"],
  state: "Odisha",
  foreign_funded: false,
  prefers_csr_experience: true,
  confidence: {
    budget_inr: "high",
    domains: "high",
    districts: "high",
    state: "high",
    prefers_csr_experience: "medium",
    foreign_funded: "high",
  },
  clarifying_questions: [
    "Is a preference for prior CSR-experienced partners a hard requirement, or should newer organisations also be considered?",
  ],
  raw_text: DEMO_TEXT,
};

export const FIXTURE_PARSE_HINGLISH: ParsedMandate = {
  budget_inr: 4000000,
  domains: ["girls_education"],
  districts: [],
  state: "Maharashtra",
  foreign_funded: false,
  prefers_csr_experience: false,
  confidence: {
    budget_inr: "high",
    domains: "high",
    districts: "low",
    state: "medium",
    prefers_csr_experience: "high",
    foreign_funded: "high",
  },
  clarifying_questions: [
    "Which districts in Maharashtra should the mandate target? Rural statewide, or a specific region?",
  ],
  raw_text: "humein rural Maharashtra mein girls ki education ke liye partner chahiye, budget 40 lakh",
};

export const FIXTURE_PARSE_UNFILLABLE: ParsedMandate = {
  budget_inr: 3500000,
  domains: ["disability_inclusion", "clean_energy", "skilling"],
  districts: ["Khandwa", "Barwani"],
  state: "Madhya Pradesh",
  foreign_funded: false,
  prefers_csr_experience: true,
  confidence: {
    budget_inr: "medium",
    domains: "high",
    districts: "high",
    state: "high",
    prefers_csr_experience: "low",
    foreign_funded: "high",
  },
  clarifying_questions: [
    "The mandate spans three domains across two districts. Can the budget be split across a partner consortium?",
  ],
  raw_text: "₹35 lakh for disability-inclusive skilling and clean energy access in Khandwa and Barwani, Madhya Pradesh",
};

const NGO_NAMES: Record<string, string> = {
  ngo_014: "Ashadeep Gramin Vikas Samiti",
  ngo_007: "Aarogya Sakhi Foundation",
  ngo_022: "Jal Shakti Mahila Mandal",
  ngo_031: "Kalahandi Shiksha Avam Gramin Vikas Sanstha",
  ngo_005: "Nirmal Jal Pariyojana",
  ngo_040: "Maa Bhoomi Trust",
  ngo_009: "Saksham Yuva Foundation",
  ngo_017: "Gramin Aarogya Seva Trust",
  ngo_028: "Balangir Mahila Swavalamban Sangh",
};

function result(
  id: string, score: number, sem: number, cos: number, trust: number,
  badge: MatchResult["trust_badge"], geo: number, budget: number,
  district: string, districts: string[], cpb: number, flags: string[],
  fresh: number, dom: string, scale: string, geoJ: string, missedByKeyword = false,
): MatchResult {
  return {
    ngo_id: id,
    name: NGO_NAMES[id] ?? id,
    final_score: score,
    semantic_score: sem,
    semantic_cosine_raw: cos,
    trust_score: trust,
    trust_badge: badge,
    geo_score: geo,
    budget_request_inr: budget,
    base_district: district,
    base_state: "Odisha",
    districts_covered: districts,
    cost_per_beneficiary_inr: cpb,
    flags,
    freshness_days: fresh,
    years_active: 8,
    beneficiaries_reached: 42000,
    admin_ratio: 0.12,
    justification: {
      domain_synergy: dom,
      scale_fit: scale,
      geographic_overlap: geoJ,
    },
    evidence_summary: { csr1: true, reg_12a: true, reg_80g: true, darpan: true, audit_fy: "2024-25" },
    // custom marker consumed by the UI banner logic
    ...({ missed_by_keyword: missedByKeyword } as object),
  } as MatchResult;
}

const SEMANTIC_RESULTS: MatchResult[] = [
  result(
    "ngo_014", 0.871, 0.88, 0.687, 84, "Verified Elite", 0.79, 4200000,
    "Kalahandi", ["Kalahandi", "Nuapada"], 1180, [], 96,
    "Mandate pillar 'maternal healthcare' aligns with the NGO's documented work on postpartum institutional delivery care and ASHA-worker training.",
    "Requests ₹42.0L against a ₹50.0L mandate (84%); largest grant previously managed was ₹38.0L, so this is within demonstrated absorptive capacity.",
    "Covers 2 of the 3 target districts, including 1 NITI Aayog Aspirational District. Nearest field office is 34 km from the mandate centroid.",
    true,
  ),
  result(
    "ngo_007", 0.812, 0.81, 0.621, 78, "Standard Audited", 0.72, 1700000,
    "Kalahandi", ["Kalahandi"], 1420, [], 141,
    "Describes its maternal-health work as 'postpartum institutional delivery care' — semantically equivalent to the mandate's phrasing, invisible to keyword search.",
    "Requests ₹17.0L (34% of mandate); has managed grants up to ₹21.0L previously.",
    "Covers Kalahandi district only; field staff embedded at the Bhawanipatna block office.",
    true,
  ),
  result(
    "ngo_022", 0.784, 0.74, 0.583, 81, "Verified Elite", 0.88, 1800000,
    "Balangir", ["Balangir", "Nuapada"], 980, [], 60,
    "Runs women-led community water quality monitoring across nine panchayats — directly matches the clean drinking water pillar.",
    "Requests ₹18.0L (36% of mandate); largest previous grant ₹24.0L.",
    "Covers Balangir and Nuapada — the two districts the top-ranked partner does not reach.",
    true,
  ),
  result(
    "ngo_031", 0.741, 0.69, 0.542, 66, "Standard Audited", 0.84, 900000,
    "Nuapada", ["Nuapada"], 1310, [], 210,
    "Girls' education and health-nutrition programming in aspirational-district schools intersects the maternal-health pillar via Aanganwadi worker training.",
    "Requests ₹9.0L (18% of mandate).",
    "Single-district footprint in Nuapada with 3 field supervisors.",
    false,
  ),
  result(
    "ngo_005", 0.703, 0.66, 0.519, 73, "Standard Audited", 0.77, 600000,
    "Kalahandi", ["Kalahandi", "Balangir"], 890, [], 175,
    "Handpump repair and drinking-water source restoration crews active in two of the mandate districts.",
    "Requests ₹6.0L (12% of mandate); absorptive cap ₹12.0L.",
    "Covers Kalahandi and Balangir blocks near the mandate centroid.",
    false,
  ),
  result(
    "ngo_028", 0.664, 0.62, 0.493, 58, "Verification Incomplete", 0.71, 400000,
    "Balangir", ["Balangir"], 1150, ["audit_fy2023_missing"], 240,
    "Women's livelihood and maternal-nutrition kitchen gardens in Balangir.",
    "Requests ₹4.0L (8% of mandate) — small but within demonstrated capacity.",
    "Single-district footprint in Balangir.",
    false,
  ),
  result(
    "ngo_017", 0.628, 0.55, 0.437, 52, "Verification Incomplete", 0.65, 350000,
    "Nuapada", ["Nuapada"], 1260, ["80g_expired"], 300,
    "Mobile health camps covering maternal checkups in remote Nuapada villages.",
    "Requests ₹3.5L (7% of mandate).",
    "Covers Nuapada district; camp route reaches 22 villages.",
    false,
  ),
  result(
    "ngo_009", 0.588, 0.51, 0.406, 47, "High Risk — Review Required", 0.62, 1500000,
    "Kalahandi", ["Kalahandi"], 640, ["admin_ratio_anomaly"], 420,
    "Multi-domain implementer claiming maternal health, water and skilling coverage.",
    "Requests ₹15.0L (30% of mandate) — no prior grant above ₹6.0L on record.",
    "Claims all three districts; field presence verified in only one.",
    false,
  ),
  result(
    "ngo_040", 0.512, 0.44, 0.356, 38, "High Risk — Review Required", 0.58, 2000000,
    "Balangir", ["Balangir"], 410, ["shell_network_flag"], 500,
    "Registered for rural development; proposal text mirrors mandate wording closely.",
    "Requests ₹20.0L (40% of mandate) with no audited financials since FY22.",
    "Lists a Balangir address shared with two other registered entities.",
    false,
  ),
];

// Keyword baseline returns only organisations using the mandate's exact words.
// It loves the SEO-optimised paper NGOs — that's the whole point of the A/B.
const KEYWORD_RESULTS: MatchResult[] = [
  SEMANTIC_RESULTS[0], // ngo_014 — legit, exact words
  SEMANTIC_RESULTS[4], // ngo_005 — legit, "drinking water"
  SEMANTIC_RESULTS[7], // ngo_009 — high risk, "maternal health, water and skilling"
  SEMANTIC_RESULTS[8], // ngo_040 — shell network, "rural development" + mirrors mandate
].map((r) => ({ ...r }));

const DEMO_CONSORTIUM: Consortium = {
  consortium_id: "cns_1",
  members: [
    {
      ngo_id: "ngo_014",
      name: NGO_NAMES.ngo_014,
      trust_score: 84,
      covers: [
        { domain: "maternal_health", districts: ["Kalahandi", "Nuapada"] },
        { domain: "clean_water", districts: ["Kalahandi"] },
      ],
      unique_units: 4,
      budget_share_inr: 3250000,
      share_pct: 65,
      absorptive_cap_inr: 5700000,
      capped: false,
    },
    {
      ngo_id: "ngo_022",
      name: NGO_NAMES.ngo_022,
      trust_score: 81,
      covers: [
        { domain: "clean_water", districts: ["Balangir", "Nuapada"] },
        { domain: "maternal_health", districts: ["Balangir"] },
      ],
      unique_units: 2,
      budget_share_inr: 1750000,
      share_pct: 35,
      absorptive_cap_inr: 3600000,
      capped: false,
    },
  ],
  coverage: 1.0,
  redundancy: 0.08,
  trust_weighted: 0.79,
  coordination_cost: 0.05,
  score: 0.842,
  beats_best_single_by: 0.31,
  unallocated_inr: 0,
  rationale:
    "No single partner covers both maternal health and clean water across all three districts. This pair reaches full coverage with 8% overlap.",
};

function matchResponse(engine: "semantic" | "keyword", latency: number): MatchResponse {
  const results = engine === "semantic" ? SEMANTIC_RESULTS : KEYWORD_RESULTS;
  return {
    algorithm_version: "setu-1.0.0",
    input_hash: "sha256:9f2c41ab77e0d3c1b84a5512ff09a7c3ee8d120b7fa6c1e4d2a9b8f7e6d5c4a3",
    latency_ms: latency,
    mode_used: "both",
    engine,
    excluded_ineligible_count: 4,
    unmatched_warning: null,
    results,
    consortiums: engine === "semantic" ? [DEMO_CONSORTIUM] : [],
    pareto_front: ["ngo_014", "ngo_022", "ngo_007"],
    rank_stability: {
      ngo_014: { p_top1: 0.71, p_top3: 0.94 },
      ngo_007: { p_top1: 0.18, p_top3: 0.88 },
      ngo_022: { p_top1: 0.09, p_top3: 0.79 },
    },
    keyword_baseline_comparison:
      engine === "semantic"
        ? {
            keyword_result_count: 4,
            semantic_result_count: 9,
            missed_by_keyword: ["ngo_014", "ngo_022", "ngo_007"],
            headline: "Keyword search would have missed your best-scoring partner.",
          }
        : null,
  };
}

export const FIXTURE_MATCH_SEMANTIC = matchResponse("semantic", 214);
export const FIXTURE_MATCH_KEYWORD = matchResponse("keyword", 38);

export const FIXTURE_MATCH_UNFILLABLE: MatchResponse = {
  algorithm_version: "setu-1.0.0",
  input_hash: "sha256:1a7b3c9e02d4f6a8b0c2d4e6f8a0b2c4d6e8f0a2b4c6d8e0f2a4b6c8d0e2f4a6",
  latency_ms: 268,
  mode_used: "both",
  engine: "semantic",
  excluded_ineligible_count: 3,
  unmatched_warning:
    "No single NGO in the current network covers disability-inclusive skilling with clean energy access across Khandwa and Barwani. The closest capability is 'rural skilling' (2 organisations, both single-district).",
  results: SEMANTIC_RESULTS.slice(3, 6),
  consortiums: [],
  pareto_front: ["ngo_031"],
  rank_stability: {},
  keyword_baseline_comparison: null,
};

export const FIXTURE_TRUST: Record<string, TrustDossier> = {
  ngo_014: {
    ngo_id: "ngo_014",
    name: NGO_NAMES.ngo_014,
    trust_score: 84,
    badge: "Verified Elite",
    last_verified_days_ago: 96,
    pillars: [
      {
        key: "compliance",
        label: "Compliance",
        weight: 0.3,
        raw: 1.0,
        freshness: 0.83,
        effective: 0.932,
        contribution: 27.96,
        no_evidence: false,
        evidence: [
          {
            evidence_id: "ev_csr1",
            doc_id: "doc_csr1_014",
            doc_name: "Form CSR-1 Registration",
            kind: "csr1",
            page: 1,
            snippet:
              "…the entity Ashadeep Gramin Vikas Samiti is registered with the Ministry of Corporate Affairs under Form CSR-1, registration number CSR-00024187, valid from 14-03-2022…",
            char_offsets: [60, 92],
            confidence: 0.96,
            age_days: 96,
          },
          {
            evidence_id: "ev_80g",
            doc_id: "doc_80g_014",
            doc_name: "80G Renewal Certificate",
            kind: "80g",
            page: 1,
            snippet:
              "…certificate number AA/8G/2024/1147 granted under section 80G of the Income Tax Act, 1961, valid up to 31-03-2027…",
            char_offsets: [18, 56],
            confidence: 0.93,
            age_days: 96,
          },
        ],
      },
      {
        key: "financial",
        label: "Financial",
        weight: 0.3,
        raw: 0.86,
        freshness: 0.84,
        effective: 0.802,
        contribution: 24.05,
        no_evidence: false,
        evidence: [
          {
            evidence_id: "ev_audit",
            doc_id: "doc_audit_014",
            doc_name: "Audited Financial Statement FY2024-25",
            kind: "audit",
            page: 4,
            snippet:
              "…total expenditure ₹2,84,00,000 of which administrative overhead ₹34,08,000 (12.0%); programme expense ₹2,49,92,000…",
            char_offsets: [24, 61],
            confidence: 0.97,
            age_days: 120,
          },
        ],
      },
      {
        key: "operational",
        label: "Operational",
        weight: 0.25,
        raw: 0.78,
        freshness: 0.9,
        effective: 0.744,
        contribution: 18.6,
        no_evidence: false,
        evidence: [
          {
            evidence_id: "ev_ar",
            doc_id: "doc_ar_014",
            doc_name: "Annual Report 2024-25",
            kind: "annual_report",
            page: 12,
            snippet:
              "…42 completed projects against 47 sanctioned since 2016; milestone compliance 91% across 240 reported milestones…",
            char_offsets: [3, 46],
            confidence: 0.9,
            age_days: 140,
          },
        ],
      },
      {
        key: "external",
        label: "External",
        weight: 0.15,
        raw: 0.7,
        freshness: 0.81,
        effective: 0.613,
        contribution: 9.2,
        no_evidence: false,
        evidence: [
          {
            evidence_id: "ev_impact",
            doc_id: "doc_impact_014",
            doc_name: "Third-Party Impact Assessment — maternal health programme",
            kind: "impact_assessment",
            page: 2,
            snippet:
              "…independent assessment by Sigma Development Analytics confirmed 11,240 safe-delivery referrals against a target of 10,000…",
            char_offsets: [48, 91],
            confidence: 0.88,
            age_days: 210,
          },
        ],
      },
    ],
    anomaly_penalty: 0,
    shell_penalty: 0,
    algorithm_version: "setu-1.0.0",
    input_hash: "sha256:3f8a1c6e9b2d4f0a7c3e5b1d9f8a2c4e6b0d8f2a4c6e8b0d2f4a6c8e0b2d4f6",
  },
  ngo_040: {
    ngo_id: "ngo_040",
    name: NGO_NAMES.ngo_040,
    trust_score: 38,
    badge: "High Risk — Review Required",
    last_verified_days_ago: 500,
    pillars: [
      {
        key: "compliance",
        label: "Compliance",
        weight: 0.3,
        raw: 0.55,
        freshness: 0.29,
        effective: 0.319,
        contribution: 9.58,
        no_evidence: false,
        evidence: [
          {
            evidence_id: "ev_csr1_040",
            doc_id: "doc_csr1_040",
            doc_name: "Form CSR-1 Registration",
            kind: "csr1",
            page: 1,
            snippet: "…registered under Form CSR-1, number CSR-00031542, valid from 09-11-2021…",
            char_offsets: [30, 58],
            confidence: 0.74,
            age_days: 500,
          },
        ],
      },
      {
        key: "financial",
        label: "Financial",
        weight: 0.3,
        raw: 0.0,
        freshness: 0.0,
        effective: 0.0,
        contribution: 0.0,
        no_evidence: true,
        evidence: [
          {
            evidence_id: "ev_audit_040",
            doc_id: "doc_audit_040",
            doc_name: "No audited financial statement on file",
            kind: "audit",
            page: 1,
            snippet: "No audit report on file — contributes 0 to this pillar.",
            char_offsets: [0, 20],
            confidence: 0.0,
            age_days: 1000,
            no_evidence: true,
          },
        ],
      },
      {
        key: "operational",
        label: "Operational",
        weight: 0.25,
        raw: 0.42,
        freshness: 0.35,
        effective: 0.273,
        contribution: 6.82,
        no_evidence: false,
        evidence: [
          {
            evidence_id: "ev_ar_040",
            doc_id: "doc_ar_040",
            doc_name: "Annual Report 2022-23",
            kind: "annual_report",
            page: 3,
            snippet: "…9 projects completed of 15 sanctioned; milestone reporting irregular after FY22…",
            char_offsets: [3, 31],
            confidence: 0.61,
            age_days: 640,
          },
        ],
      },
      {
        key: "external",
        label: "External",
        weight: 0.15,
        raw: 0.1,
        freshness: 0.2,
        effective: 0.052,
        contribution: 0.78,
        no_evidence: true,
        evidence: [
          {
            evidence_id: "ev_ext_040",
            doc_id: "doc_ext_040",
            doc_name: "No third-party verification on file",
            kind: "impact_assessment",
            page: 1,
            snippet: "No impact assessment or third-party audit on file — contributes 0 to this pillar.",
            char_offsets: [0, 20],
            confidence: 0.0,
            age_days: 1000,
            no_evidence: true,
          },
        ],
      },
    ],
    anomaly_penalty: 0,
    shell_penalty: 20,
    algorithm_version: "setu-1.0.0",
    input_hash: "sha256:7d2e4f6a8c0b2d4e6f8a0c2b4d6e8f0a2c4e6b8d0f2a4c6e8b0d2f4a6c8e0d2f4a6",
  },
};

export const FIXTURE_COUNTERFACTUAL: Record<string, CounterfactualResponse> = {
  ngo_007: {
    ngo_id: "ngo_007",
    name: NGO_NAMES.ngo_007,
    current: 61,
    achievable_ceiling: 80,
    combined_projection: 80,
    actions: [
      {
        action_id: "act_audit",
        label: "Upload FY2024-25 audited financial statement",
        delta: 12,
        effort: "low",
        effort_class: "actionable",
        explanation:
          "Your last audited statement is 26 months old. A current audit refreshes the Financial pillar at full weight.",
        threshold_crossed: null,
      },
      {
        action_id: "act_80g",
        label: "Renew 80G certificate (expired Mar 2025)",
        delta: 7,
        effort: "medium",
        effort_class: "actionable",
        explanation:
          "An expired 80G scores half-weight in Compliance. Renewal restores the full 0.20 share of the pillar.",
        threshold_crossed: "Standard Audited → Verified Elite",
      },
      {
        action_id: "act_impact",
        label: "Commission third-party impact assessment",
        delta: 5,
        effort: "medium",
        effort_class: "actionable",
        explanation: "Adds the 0.40 External Verification component you currently lack entirely.",
        threshold_crossed: null,
      },
      {
        action_id: "act_tenure",
        label: "Reach 10 years of operating history",
        delta: 2,
        effort: "high",
        effort_class: "structural",
        explanation: "Tenure contributes 15% of the Operational pillar; yours is at 7 years.",
        threshold_crossed: null,
      },
    ],
    algorithm_version: "setu-1.0.0",
  },
};

export const FIXTURE_NETWORK: Record<string, NetworkResponse> = {
  ngo_040: {
    flagged: true,
    members: [
      { ngo_id: "ngo_040", name: NGO_NAMES.ngo_040, base_district: "Balangir" },
      { ngo_id: "ngo_041", name: "Seva Balangir Rural Development Society", base_district: "Balangir" },
      { ngo_id: "ngo_042", name: "Kosal Kalyan Trust", base_district: "Balangir" },
    ],
    shared_identifier_types: ["same address", "same trustee", "same bank account"],
    explanation:
      "These three organisations share a registered address, a trustee name, and a bank account. All three are capped at trust 40 and excluded from recommendation pending human review.",
  },
  ngo_014: {
    flagged: false,
    members: [{ ngo_id: "ngo_014", name: NGO_NAMES.ngo_014, base_district: "Kalahandi" }],
    shared_identifier_types: [],
    explanation: "No linked-entity network detected for this organisation.",
  },
};

export const FIXTURE_NGOS: Record<string, NgoProfile> = Object.fromEntries(
  SEMANTIC_RESULTS.map((r) => [
    r.ngo_id,
    {
      ngo_id: r.ngo_id,
      name: r.name,
      base_district: r.base_district,
      base_state: r.base_state,
      primary_domain: r.ngo_id === "ngo_022" || r.ngo_id === "ngo_005" ? "clean_water" : "maternal_health",
      trust_score: r.trust_score,
      trust_badge: r.trust_badge,
      years_active: 8,
      beneficiaries_reached: 42000,
      cost_per_beneficiary_inr: r.cost_per_beneficiary_inr,
      admin_ratio: 0.12,
      lat: 19.9,
      lng: 83.2,
      domains: ["maternal_health"],
      districts_covered: r.districts_covered,
    } as NgoProfile,
  ]),
);

// Simplified polygons around the demo districts (centroid boxes ~0.5°) —
// the real districts.geojson is bundled in public/geo/ for the map.
export const FIXTURE_COVERAGE: CoverageResponse = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      geometry: { type: "Polygon", coordinates: [[[82.9, 19.7], [83.6, 19.7], [83.6, 20.3], [82.9, 20.3], [82.9, 19.7]]] },
      properties: { district: "Kalahandi", state: "Odisha", ngo_count: 5, verified_count: 2, need_index: 0.82, is_aspirational: true, gap_score: 0.74 },
    },
    {
      type: "Feature",
      geometry: { type: "Polygon", coordinates: [[[82.4, 19.9], [83.1, 19.9], [83.1, 20.6], [82.4, 20.6], [82.4, 19.9]]] },
      properties: { district: "Nuapada", state: "Odisha", ngo_count: 3, verified_count: 1, need_index: 0.88, is_aspirational: true, gap_score: 0.81 },
    },
    {
      type: "Feature",
      geometry: { type: "Polygon", coordinates: [[[82.8, 20.4], [83.7, 20.4], [83.7, 21.1], [82.8, 21.1], [82.8, 20.4]]] },
      properties: { district: "Balangir", state: "Odisha", ngo_count: 6, verified_count: 2, need_index: 0.79, is_aspirational: true, gap_score: 0.69 },
    },
    {
      type: "Feature",
      geometry: { type: "Polygon", coordinates: [[[85.0, 20.2], [85.8, 20.2], [85.8, 20.9], [85.0, 20.9], [85.0, 20.2]]] },
      properties: { district: "Cuttack", state: "Odisha", ngo_count: 21, verified_count: 9, need_index: 0.31, is_aspirational: false, gap_score: 0.08 },
    },
    {
      type: "Feature",
      geometry: { type: "Polygon", coordinates: [[[86.6, 20.2], [87.4, 20.2], [87.4, 21.0], [86.6, 21.0], [86.6, 20.2]]] },
      properties: { district: "Mayurbhanj", state: "Odisha", ngo_count: 4, verified_count: 0, need_index: 0.85, is_aspirational: true, gap_score: 0.86 },
    },
    {
      type: "Feature",
      geometry: { type: "Polygon", coordinates: [[[73.0, 19.6], [73.9, 19.6], [73.9, 20.3], [73.0, 20.3], [73.0, 19.6]]] },
      properties: { district: "Palghar", state: "Maharashtra", ngo_count: 9, verified_count: 3, need_index: 0.72, is_aspirational: true, gap_score: 0.52 },
    },
    {
      type: "Feature",
      geometry: { type: "Polygon", coordinates: [[[75.6, 19.6], [76.4, 19.6], [76.4, 20.3], [75.6, 20.3], [75.6, 19.6]]] },
      properties: { district: "Nashik", state: "Maharashtra", ngo_count: 17, verified_count: 8, need_index: 0.44, is_aspirational: false, gap_score: 0.11 },
    },
    {
      type: "Feature",
      geometry: { type: "Polygon", coordinates: [[[75.0, 21.5], [76.0, 21.5], [76.0, 22.4], [75.0, 22.4], [75.0, 21.5]]] },
      properties: { district: "Khandwa", state: "Madhya Pradesh", ngo_count: 3, verified_count: 1, need_index: 0.77, is_aspirational: true, gap_score: 0.71 },
    },
    {
      type: "Feature",
      geometry: { type: "Polygon", coordinates: [[[74.4, 21.5], [75.4, 21.5], [75.4, 22.3], [74.4, 22.3], [74.4, 21.5]]] },
      properties: { district: "Barwani", state: "Madhya Pradesh", ngo_count: 2, verified_count: 0, need_index: 0.9, is_aspirational: true, gap_score: 0.9 },
    },
    {
      type: "Feature",
      geometry: { type: "Polygon", coordinates: [[[77.2, 21.6], [78.2, 21.6], [78.2, 22.5], [77.2, 22.5], [77.2, 21.6]]] },
      properties: { district: "Narsinghpur", state: "Madhya Pradesh", ngo_count: 8, verified_count: 4, need_index: 0.36, is_aspirational: false, gap_score: 0.1 },
    },
  ],
};

export const FIXTURE_AUDIT: AuditEntry[] = [
  { entry_id: "aud_001", timestamp: "2026-09-03T09:41:02Z", actor_role: "corporate", action: "mandate.parse", entity_id: "mnd_01", payload_digest: "pd_9f2c41ab", prev_hash: "GENESIS", hash: "0001a7f3c9e2b4d6" },
  { entry_id: "aud_002", timestamp: "2026-09-03T09:41:14Z", actor_role: "corporate", action: "mandate.create", entity_id: "mnd_01", payload_digest: "pd_4b8e1d0a", prev_hash: "0001a7f3c9e2b4d6", hash: "0002be418c7a" },
  { entry_id: "aud_003", timestamp: "2026-09-03T09:41:19Z", actor_role: "corporate", action: "match.run", entity_id: "mnd_01", payload_digest: "pd_77c2e5f1", prev_hash: "0002be418c7a", hash: "0003d95f0e3a" },
  { entry_id: "aud_004", timestamp: "2026-09-03T09:43:47Z", actor_role: "corporate", action: "trust.view", entity_id: "ngo_014", payload_digest: "pd_1a4b9d02", prev_hash: "0003d95f0e3a", hash: "0004e6b21f8c" },
  { entry_id: "aud_005", timestamp: "2026-09-03T09:47:30Z", actor_role: "ngo", action: "counterfactual.view", entity_id: "ngo_007", payload_digest: "pd_5c8f3b7a", prev_hash: "0004e6b21f8c", hash: "0005f0a93c6d" },
  { entry_id: "aud_006", timestamp: "2026-09-03T09:52:11Z", actor_role: "auditor", action: "network.flag", entity_id: "ngo_040", payload_digest: "pd_2e6d4a9c", prev_hash: "0005f0a93c6d", hash: "0006a1b74e9f" },
];

export const FIXTURE_PRESETS = [
  { label: "Demo mandate", text: DEMO_TEXT },
  {
    label: "Unfillable mandate",
    text: "₹35 lakh for disability-inclusive skilling and clean energy access in Khandwa and Barwani, Madhya Pradesh",
  },
  {
    label: "Hinglish mandate",
    text: "humein rural Maharashtra mein girls ki education ke liye partner chahiye, budget 40 lakh",
  },
];

// Unused-but-handy guard for fixtures dir existence via TS
export const FIXTURE_DIR_NOTE = "fixtures are also stored under src/fixtures for the bundler";
