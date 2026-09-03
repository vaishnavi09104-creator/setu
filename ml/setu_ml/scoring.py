"""setu_ml.scoring — the composite score and the main rank entry (A5). §5.1, §5.6.

Calibration: we rank on RAW cosine but DISPLAY the calibrated value
(affine map through LO/HI fitted on the corpus). Both are returned.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

import numpy as np

from .embeddings import cosine_matrix, embed_texts
from .geo import geo_score
from .justify import domain_synergy, geographic_overlap, scale_fit, format_inr
from .types import (
    DEFAULT_WEIGHTS,
    Justification,
    Mandate,
    MatchResult,
    NgoProfile,
    TrustBadge,
)

logger = logging.getLogger("setu_ml.scoring")

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "artifacts"
CALIBRATION_PATH = ARTIFACTS_DIR / "calibration.json"

# §5.1 starting guesses; fitted on the real seed corpus by calibrate.py (A6)
CALIBRATION_LO = 0.15
CALIBRATION_HI = 0.80

# Unmatched guard (§5.1): below this best raw cosine, return honest failure.
UNMATCHED_THRESHOLD = 0.28


def _load_calibration() -> tuple[float, float]:
    if CALIBRATION_PATH.exists():
        try:
            import json

            data = json.loads(CALIBRATION_PATH.read_text(encoding="utf-8"))
            return float(data["LO"]), float(data["HI"])
        except Exception as exc:  # pragma: no cover
            logger.warning("calibration.json unreadable (%s); using defaults", exc)
    return CALIBRATION_LO, CALIBRATION_HI


def semantic_score(cosine_raw: float) -> float:
    """§5.1 affine calibration, clipped to [0,1]."""
    lo, hi = _load_calibration()
    if hi <= lo:
        return 0.0
    return max(0.0, min(1.0, (cosine_raw - lo) / (hi - lo)))


def composite_score(
    sem: float,
    trust_0_100: int | float,
    geo: float,
    weights: dict[str, float] | None = None,
) -> float:
    """§5.6. Default {'semantic':0.50,'trust':0.30,'geo':0.20}.
    Weights must sum to 1.0 ± 1e-6 — silently renormalising makes the
    rank-stability numbers meaningless, so raise instead."""
    w = weights or DEFAULT_WEIGHTS
    total = sum(w.get(k, 0.0) for k in ("semantic", "trust", "geo"))
    if abs(total - 1.0) > 1e-6:
        raise ValueError(
            f"weights must sum to 1.0 ± 1e-6 (got {total:.6f}: {w}) — "
            "renormalising silently would corrupt the rank-stability story"
        )
    return (
        w["semantic"] * sem
        + w["trust"] * (max(0.0, min(100.0, float(trust_0_100))) / 100.0)
        + w["geo"] * geo
    )


# --- The fair keyword baseline -------------------------------------------------

_STOP = {
    "a", "an", "the", "for", "and", "or", "of", "in", "on", "across", "with",
    "prefer", "partners", "partner", "we", "our", "want", "to", "fund",
    "funding", "budget", "looking", "csr", "corporate", "experience",
    "prior", "clean", "drinking", "water", "maternal", "health", "and",
    "girls", "ki", "ke", "liye", "mein", "chahiye", "humein", "rural",
    "districts", "district", "prior",
}

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    out = set()
    for t in _TOKEN_RE.findall(text.lower()):
        # light stemming: strip plural 's'
        t2 = t[:-1] if (len(t) > 3 and t.endswith("s") and not t.endswith("ss")) else t
        out.add(t2)
    return out


def _keyword_score(mandate_tokens: set[str], ngo: NgoProfile) -> float:
    """What a competent developer would write without embeddings: exact token
    overlap over proposal text, score = |overlap| / |mandate_tokens|.
    NOTE: we deliberately do NOT add the NGO's structured domain fields to
    the searchable text — the baseline embeds/reads the PROPOSAL, which is the
    honest 'what would search see' comparison."""
    doc = f"{ngo.name} {ngo.proposal_text}"
    doc_toks = _tokens(doc)
    overlap = mandate_tokens & doc_toks
    if not mandate_tokens:
        return 0.0
    return len(overlap) / len(mandate_tokens)


def keyword_baseline(mandate: Mandate, ngos: list[NgoProfile], top_k: int = 10) -> list[MatchResult]:
    """The naive matcher that makes the A/B toggle honest (FR-B5).
    Keeps anything with score > 0, sorted by score."""
    mtoks = _tokens(mandate.raw_text) - _STOP
    results: list[MatchResult] = []
    for ngo in ngos:
        if ngo.status == "INELIGIBLE":
            continue
        s = _keyword_score(mtoks, ngo)
        if s <= 0:
            continue
        g = geo_score(mandate, ngo)
        results.append(
            MatchResult(
                ngo_id=ngo.ngo_id,
                name=ngo.name,
                final_score=s,  # naive scorer has no composite — its own score
                semantic_score=0.0,
                semantic_cosine_raw=0.0,
                trust_score=ngo.trust_score,
                trust_badge=ngo.trust_badge,
                geo_score=g,
                budget_request_inr=ngo.budget_request_inr,
                base_district=ngo.base_district,
                base_state=ngo.base_state,
                districts_covered=[d.district for d in ngo.districts_covered],
                cost_per_beneficiary_inr=ngo.financials.cost_per_beneficiary_inr,
                flags=[],
                freshness_days=ngo.freshness_days,
                justification=Justification(
                    domain_synergy="Keyword token overlap only — no semantic model ran.",
                    scale_fit=scale_fit(mandate, ngo),
                    geographic_overlap=geographic_overlap(mandate, ngo),
                ),
            )
        )
    results.sort(key=lambda r: -r.final_score)
    return results[:top_k]


def compare_engines(semantic: list[MatchResult], keyword: list[MatchResult]) -> dict:
    """keyword_result_count, semantic_result_count, missed_by_keyword (in
    semantic top-5 but absent from keyword results) and a headline computed
    from the data — never hardcoded."""
    sem_ids = [r.ngo_id for r in semantic]
    kw_ids = {r.ngo_id for r in keyword}
    missed = [i for i in sem_ids[:5] if i not in kw_ids]
    counts = (len(keyword), len(semantic))
    if missed and counts[0] < counts[1]:
        headline = (
            f"Keyword search would have missed your best-scoring partner."
            if sem_ids and sem_ids[0] in missed
            else f"Keyword search missed {len(missed)} of the top {min(5, len(sem_ids))} partners."
        )
    elif counts[0] == 0 and counts[1] > 0:
        headline = "Keyword search returned nothing; semantic matching found partners."
    else:
        headline = "Keyword and semantic results largely agree for this mandate."
    return {
        "keyword_result_count": counts[0],
        "semantic_result_count": counts[1],
        "missed_by_keyword": missed,
        "headline": headline,
    }


# --- The main rank entry ------------------------------------------------------

def rank_ngos(
    mandate: Mandate,
    ngos: list[NgoProfile],
    index: tuple[np.ndarray, list[str]],
    weights: dict | None = None,
    top_k: int = 10,
    include_justifications: bool = True,
    include_sdg: bool = False,
) -> tuple[list[MatchResult], int]:
    """The main entry point the backend calls. Order of operations matters:
      1. FILTER OUT status == "INELIGIBLE"  ← before scoring, not after
      2. one matrix multiply for all cosine similarities
      3. geo_score per surviving candidate
      4. composite, sort descending, take top_k
      5. justifications for survivors only
    Returns (results, excluded_ineligible_count).
    """
    eligible = [n for n in ngos if n.status != "INELIGIBLE"]
    excluded = len(ngos) - len(eligible)

    if not eligible:
        return [], excluded

    matrix, ids = index
    id_pos = {ngo_id: i for i, ngo_id in enumerate(ids)}

    # mandate query embedding
    q_text = mandate.raw_text
    q = embed_texts([q_text])  # (1, 384) normalised
    sub_rows: list[int] = []
    sub_ngos: list[NgoProfile] = []
    for n in eligible:
        pos = id_pos.get(n.ngo_id)
        if pos is None:
            # not in the committed index — embed on the fly (rare path)
            logger.debug("ngo %s missing from index; embedding on the fly", n.ngo_id)
            from .embeddings import ngo_embedding_text

            vec = embed_texts([ngo_embedding_text(n)])
            matrix = np.vstack([matrix, vec])
            ids = ids + [n.ngo_id]
            id_pos[n.ngo_id] = len(ids) - 1
            pos = len(ids) - 1
        sub_rows.append(pos)
        sub_ngos.append(n)

    corpus = matrix[sub_rows] if sub_rows else matrix[:0]
    sims = cosine_matrix(q, corpus)[0]  # (n_eligible,)

    w = weights or DEFAULT_WEIGHTS
    scored: list[tuple[float, NgoProfile, float, float]] = []
    for sim, ngo in zip(sims, sub_ngos):
        sem = semantic_score(float(sim))
        g = geo_score(mandate, ngo)
        fs = composite_score(sem, ngo.trust_score, g, w)
        scored.append((fs, ngo, float(sim), sem))

    scored.sort(key=lambda x: -x[0])
    top = scored[:top_k]

    results: list[MatchResult] = []
    for fs, ngo, raw, sem in top:
        just = (
            Justification(
                domain_synergy=domain_synergy(mandate, ngo),
                scale_fit=scale_fit(mandate, ngo),
                geographic_overlap=geographic_overlap(mandate, ngo),
            )
            if include_justifications
            else Justification(domain_synergy="", scale_fit="", geographic_overlap="")
        )
        sdg_tags = []
        if include_sdg:
            from .sdg import tag_sdgs

            sdg_tags = tag_sdgs(ngo.proposal_text)
        results.append(
            MatchResult(
                ngo_id=ngo.ngo_id,
                name=ngo.name,
                final_score=fs,
                semantic_score=sem,
                semantic_cosine_raw=raw,
                trust_score=ngo.trust_score,
                trust_badge=ngo.trust_badge,
                geo_score=geo_score(mandate, ngo),
                budget_request_inr=ngo.budget_request_inr,
                base_district=ngo.base_district,
                base_state=ngo.base_state,
                districts_covered=[d.district for d in ngo.districts_covered],
                cost_per_beneficiary_inr=ngo.financials.cost_per_beneficiary_inr,
                flags=list(_flags_for(ngo)),
                freshness_days=ngo.freshness_days,
                justification=just,
                sdg_tags=sdg_tags,
            )
        )
    return results, excluded


def unmatched_guard(mandate: Mandate, ngos: list[NgoProfile],
                    index: tuple[np.ndarray, list[str]]) -> dict | None:
    """§5.1 guard: if best raw cosine < 0.28 across the whole network, do NOT
    return a ranked list as if it were fine. Return the honest warning with
    the closest adjacent capability."""
    eligible = [n for n in ngos if n.status != "INELIGIBLE"]
    if not eligible:
        return {"warning": "no_eligible_ngos", "closest_capability": None}
    matrix, ids = index
    id_pos = {i: k for k, i in enumerate(ids)}
    rows = [id_pos[n.ngo_id] for n in eligible if n.ngo_id in id_pos]
    if not rows:
        return None
    q = embed_texts([mandate.raw_text])
    sims = cosine_matrix(q, matrix[rows])[0]
    best = float(np.max(sims))
    if best >= UNMATCHED_THRESHOLD:
        return None
    best_ngo = eligible[int(np.argmax(sims))]
    return {
        "warning": "unmatched_mandate",
        "best_raw_cosine": round(best, 3),
        "closest_capability": best_ngo.primary_domain.value,
        "message": (
            "No strong match found. The closest organisations are shown with low "
            "confidence — a suitable partner would need to cover this capability."
        ),
    }


def _flags_for(ngo: NgoProfile) -> list[str]:
    flags: list[str] = []
    if ngo.trust_badge == TrustBadge.HIGH_RISK:
        flags.append("high_risk_review")
    if ngo.status == "FLAGGED":
        flags.append("network_flagged")
    return flags
