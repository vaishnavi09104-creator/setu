const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const FORCE_FIXTURES = process.env.NEXT_PUBLIC_USE_FIXTURES === "true";

export type ApiSource = "live" | "fixture";
export interface ApiResult<T> {
  data: T;
  source: ApiSource;
  latencyMs: number;
}

export class ApiError extends Error {
  constructor(public path: string, public status?: number) {
    super(`API call failed: ${path}`);
    this.name = "ApiError";
  }
}

type Listener = (state: { offline: boolean; lastLatencyMs: number | null; source: ApiSource | null }) => void;
const listeners = new Set<Listener>();
let netState = { offline: false, lastLatencyMs: null as number | null, source: null as ApiSource | null };

export function subscribeNetState(l: Listener): () => void {
  listeners.add(l);
  l(netState);
  return () => listeners.delete(l);
}
function setNetState(patch: Partial<typeof netState>) {
  netState = { ...netState, ...patch };
  listeners.forEach((l) => l(netState));
}

async function call<T>(
  path: string,
  fixture: () => T,
  init?: RequestInit,
): Promise<ApiResult<T>> {
  const t0 = performance.now();
  const finishFixture = (label: string): ApiResult<T> => {
    const r = { data: fixture(), source: "fixture" as const, latencyMs: Math.round(performance.now() - t0) };
    if (label === "force") setNetState({ source: "fixture" });
    return r;
  };
  if (FORCE_FIXTURES) return finishFixture("force");
  try {
    const res = await fetch(`${BASE}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
      signal: AbortSignal.timeout(8000),
    });
    if (!res.ok) throw new ApiError(path, res.status);
    const data = (await res.json()) as T;
    setNetState({ offline: false, source: "live" });
    return { data, source: "live", latencyMs: performance.now() - t0 };
  } catch {
    // silent, automatic, invisible — fall back to captured responses
    const r = finishFixture("fallback");
    setNetState({ offline: true, source: "fixture", lastLatencyMs: null });
    return r;
  }
}

/* ---------------- typed endpoint functions (the only API surface) ---------------- */

import type {
  ParsedMandate, MatchResponse, MatchRequest, TrustDossier, CounterfactualResponse,
  NetworkResponse, CoverageResponse, AuditEntry, HealthResponse, NgoProfile,
  DocumentUploadResponse,
} from "./types";
import {
  FIXTURE_HEALTH, FIXTURE_PARSE_DEMO, FIXTURE_PARSE_HINGLISH, FIXTURE_PARSE_UNFILLABLE,
  FIXTURE_MATCH_SEMANTIC, FIXTURE_MATCH_KEYWORD, FIXTURE_MATCH_UNFILLABLE, FIXTURE_TRUST,
  FIXTURE_COUNTERFACTUAL, FIXTURE_NETWORK, FIXTURE_COVERAGE, FIXTURE_AUDIT, FIXTURE_NGOS,
} from "./fixtures";

function parseFixtureFor(text: string): ParsedMandate {
  const t = text.toLowerCase();
  if (t.includes("maharashtra") || t.includes("hinglish")) return FIXTURE_PARSE_HINGLISH;
  if (t.includes("disability") || t.includes("khandwa")) return FIXTURE_PARSE_UNFILLABLE;
  return FIXTURE_PARSE_DEMO;
}

export async function health(): Promise<ApiResult<HealthResponse>> {
  return call<HealthResponse>("/api/health", () => FIXTURE_HEALTH);
}

export async function parseMandate(text: string): Promise<ApiResult<ParsedMandate>> {
  const res = await call<ParsedMandate>(
    "/api/mandates/parse",
    () => parseFixtureFor(text),
    { method: "POST", body: JSON.stringify({ text }) },
  );
  return res;
}

let mandateSeq = 0;
export async function createMandate(m: ParsedMandate): Promise<ApiResult<{ mandate_id: string }>> {
  mandateSeq += 1;
  return call<{ mandate_id: string }>(
    "/api/mandates",
    () => ({ mandate_id: `mnd_demo_${mandateSeq.toString().padStart(2, "0")}` }),
    { method: "POST", body: JSON.stringify(m) },
  );
}

export async function runMatch(req: MatchRequest): Promise<ApiResult<MatchResponse>> {
  const useKeyword = req.use_keyword_baseline === true;
  const unfillable =
    req.mandate_inline?.domains.includes("disability_inclusion") ||
    req.mandate_id === "mnd_unfillable";
  const fixture = () => {
    if (unfillable) return FIXTURE_MATCH_UNFILLABLE;
    return useKeyword ? FIXTURE_MATCH_KEYWORD : FIXTURE_MATCH_SEMANTIC;
  };
  const res = await call<MatchResponse>("/api/match", fixture, {
    method: "POST",
    body: JSON.stringify(req),
  });
  setNetState({ lastLatencyMs: res.data.latency_ms });
  return res;
}

export async function getNgo(id: string): Promise<ApiResult<NgoProfile>> {
  return call<NgoProfile>(`/api/ngos/${id}`, () => {
    const p = FIXTURE_NGOS[id];
    if (p) return p;
    throw new ApiError(`/api/ngos/${id}`, 404);
  });
}

export async function getTrust(id: string): Promise<ApiResult<TrustDossier>> {
  return call<TrustDossier>(`/api/ngos/${id}/trust`, () => {
    const d = FIXTURE_TRUST[id];
    if (!d) {
      const base = FIXTURE_TRUST.ngo_014;
      return { ...base, ngo_id: id, name: id };
    }
    return d;
  });
}

export async function getCounterfactual(id: string): Promise<ApiResult<CounterfactualResponse>> {
  return call<CounterfactualResponse>(`/api/ngos/${id}/counterfactual`, () => {
    const c = FIXTURE_COUNTERFACTUAL[id];
    if (!c) {
      // generic fallback so the coach always renders
      return {
        ...FIXTURE_COUNTERFACTUAL.ngo_007,
        ngo_id: id,
        name: id,
      };
    }
    return c;
  });
}

export async function getNetwork(id: string): Promise<ApiResult<NetworkResponse>> {
  return call<NetworkResponse>(`/api/ngos/${id}/network`, () => {
    const n = FIXTURE_NETWORK[id];
    return n ?? FIXTURE_NETWORK.ngo_014;
  });
}

export async function getCoverage(state?: string, domain?: string): Promise<ApiResult<CoverageResponse>> {
  const qs = new URLSearchParams();
  if (state) qs.set("state", state);
  if (domain) qs.set("domain", domain);
  const q = qs.toString();
  return call<CoverageResponse>(`/api/geo/coverage${q ? `?${q}` : ""}`, () => FIXTURE_COVERAGE);
}

export async function uploadDocument(file: File): Promise<ApiResult<DocumentUploadResponse>> {
  // multipart — no fixture path for the binary itself; fixtures return a canned parse
  const fd = new FormData();
  fd.append("file", file);
  const t0 = performance.now();
  try {
    const res = await fetch(`${BASE}/api/documents/upload`, { method: "POST", body: fd, signal: AbortSignal.timeout(8000) });
    if (!res.ok) throw new ApiError("/api/documents/upload", res.status);
    setNetState({ offline: false, source: "live" });
    return { data: await res.json(), source: "live", latencyMs: performance.now() - t0 };
  } catch {
    return {
      data: {
        doc_id: "doc_fixtures_upload",
        kind_detected: "audit",
        extracted: { note: "offline demo: canned extraction from fixtures" },
        page_count: 6,
        warnings: ["offline mode: parsed from captured fixture response"],
      },
      source: "fixture",
      latencyMs: performance.now() - t0,
    };
  }
}

export function documentPageUrl(docId: string, page: number): string {
  return `${BASE}/api/documents/${docId}/pages/${page}.png`;
}

// Fixture page image: a locally generated SVG placeholder so evidence drill-down
// works with the backend dead. Uses data URI in <img> src.
export function documentPageUrlWithFallback(docId: string, page: number): { live: string; fallback: string } {
  return {
    live: documentPageUrl(docId, page),
    fallback: `/evidence/${encodeURIComponent(docId)}_${page}.svg`,
  };
}

export async function getAudit(entityId?: string): Promise<ApiResult<AuditEntry[]>> {
  const q = entityId ? `?entity_id=${encodeURIComponent(entityId)}` : "";
  return call<AuditEntry[]>(`/api/audit${q}`, () =>
    entityId ? FIXTURE_AUDIT.filter((a) => a.entity_id === entityId) : FIXTURE_AUDIT,
  );
}
