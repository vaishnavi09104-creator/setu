"""app.services.matching — /api/match pipeline (B10).

Order of operations, and it matters:
  filter INELIGIBLE *before* scoring (ranking an NGO you're about to hide
  changes the percentile calibration) → one matmul → geo → composite →
  consortium → pareto → rank-stability → keyword comparison.
"""
from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from setu_ml.consortium import find_consortiums
from setu_ml.pareto import pareto_front
from setu_ml.scoring import compare_engines, keyword_baseline, rank_ngos, unmatched_guard
from setu_ml.stability import rank_stability
from setu_ml.types import Mandate, MatchResult

from .. import db
from ..config import get_settings
from ..services.trust import ngo_profile_from_row

# In-memory index cache: rebuilt only when the corpus changes (X-Cache)
_INDEX_CACHE: dict[str, Any] = {"rows_hash": None, "index": None}


def _corpus_hash(rows: list[dict]) -> str:
    material = json.dumps([r["ngo_id"] for r in rows], sort_keys=True)
    return hashlib.sha256(material.encode()).hexdigest()


def get_index(rows: list[dict]):
    """Cache the embedding matrix in memory; recompute only on corpus change."""
    from setu_ml.embeddings import build_ngo_index

    ch = _corpus_hash(rows)
    if _INDEX_CACHE["rows_hash"] != ch or _INDEX_CACHE["index"] is None:
        profiles = [ngo_profile_from_row(r) for r in rows]
        _INDEX_CACHE["index"] = build_ngo_index(profiles)
        _INDEX_CACHE["rows_hash"] = ch
    return _INDEX_CACHE["index"]


def mandate_from_row(row: dict) -> Mandate:
    d = row["data"] if isinstance(row.get("data"), dict) else row
    return Mandate.model_validate(d)


def input_hash(payload: dict) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def run_match(mandate: Mandate, req) -> dict[str, Any]:
    t0 = time.perf_counter()
    settings = get_settings()

    all_rows = db.list_ngos()
    eligible_rows = [r for r in all_rows if r["data"].get("status") != "INELIGIBLE"]
    excluded = len(all_rows) - len(eligible_rows)

    profiles = [ngo_profile_from_row(r) for r in eligible_rows]
    index = get_index(eligible_rows)

    weights = None
    if req.weights is not None:
        weights = {"semantic": req.weights.semantic,
                   "trust": req.weights.trust,
                   "geo": req.weights.geo}

    results, _ = rank_ngos(mandate, profiles, index, weights=weights,
                           top_k=req.top_k, include_sdg=True)
    guard = unmatched_guard(mandate, profiles, index)

    mode = req.mode
    consortiums: list[dict[str, Any]] = []
    if mode in ("consortium", "both"):
        cons = find_consortiums(mandate, profiles, index, top_n=3, weights=weights)
        consortiums = [c.model_dump() for c in cons]

    pareto_ids = pareto_front(results) if req.include_pareto else []

    stability: dict[str, dict[str, float]] = {}
    if req.include_rank_stability:
        stability = rank_stability(mandate, profiles, index, n_samples=300)

    kw_comparison = None
    if req.use_keyword_baseline:
        kw_results = keyword_baseline(mandate, profiles, top_k=req.top_k)
        kw_comparison = compare_engines(results, kw_results)
        # keyword mode: results ARE the keyword ranking
        results = kw_results

    latency_ms = round((time.perf_counter() - t0) * 1000, 1)
    ih = input_hash({
        "mandate_id": mandate.mandate_id, "raw": mandate.raw_text,
        "weights": weights or "default", "top_k": req.top_k,
        "mode": mode, "kw": req.use_keyword_baseline,
    })

    # persist run for auditability (append-only log)
    with db.tx() as conn:
        conn.execute(
            "INSERT INTO matches (mandate_id, latency_ms, run_at, "
            "algorithm_version, input_hash, data) VALUES (?,?,?,?,?,?)",
            (mandate.mandate_id or "inline", latency_ms, db.utcnow(),
             settings.algorithm_version, ih,
             json.dumps({
                 "results": [r.model_dump() for r in results],
                 "consortiums": consortiums,
                 "pareto_front": pareto_ids,
             }, default=str)),
        )

    return {
        "algorithm_version": settings.algorithm_version,
        "input_hash": ih,
        "latency_ms": latency_ms,
        "mode_used": mode,
        "engine": "keyword" if req.use_keyword_baseline else "semantic",
        "excluded_ineligible_count": excluded,
        "unmatched_warning": guard,
        "results": [r.model_dump() for r in results],
        "consortiums": consortiums,
        "pareto_front": pareto_ids,
        "rank_stability": stability,
        "keyword_baseline_comparison": kw_comparison,
    }
