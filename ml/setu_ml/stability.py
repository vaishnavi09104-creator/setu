"""setu_ml.stability — rank-stability Monte Carlo (A10, P2). §5.6.

Answers "why 0.5/0.3/0.2?" with a measurement instead of an opinion: sample
weights from Dirichlet(alpha = concentration × [0.5, 0.3, 0.2]), re-rank
under each sample, report p_top1 / p_top3 for the base top 5.

1000 samples × 1000 NGOs = one 1000×1000 matmul reused — cache the cosine
matrix ONCE outside the loop; recomputing embeddings inside turns
1 second into 20 minutes.
"""
from __future__ import annotations

import logging

import numpy as np

from .embeddings import cosine_matrix, embed_texts
from .geo import geo_score
from .types import Mandate, NgoProfile

logger = logging.getLogger("setu_ml.stability")

BASE_WEIGHTS = np.array([0.50, 0.30, 0.20])


def rank_stability(
    mandate: Mandate,
    ngos: list[NgoProfile],
    index,
    n_samples: int = 1000,
    concentration: float = 50.0,
    top_report: int = 5,
) -> dict[str, dict[str, float]]:
    """{ngo_id: {p_top1, p_top3}} for the base top-5. Probabilities in [0,1],
    p_top3 ≥ p_top1 by construction."""
    eligible = [n for n in ngos if n.status != "INELIGIBLE"]
    if not eligible:
        return {}

    matrix, ids = index
    id_pos = {ngo_id: i for i, ngo_id in enumerate(ids)}
    rows = [id_pos[n.ngo_id] for n in eligible if n.ngo_id in id_pos]
    keep = [n for n in eligible if n.ngo_id in id_pos]
    if not keep:
        return {}

    # ONE cached query + matmul for all samples
    q = embed_texts([mandate.raw_text])
    sem_raw = cosine_matrix(q, matrix[rows])[0]               # (n,)
    trust = np.array([n.trust_score for n in keep], dtype=float)  # (n,)
    geo = np.array([geo_score(mandate, n) for n in keep], dtype=float)

    # base ranking
    base_scores = BASE_WEIGHTS[0] * sem_raw + BASE_WEIGHTS[1] * (trust / 100) + BASE_WEIGHTS[2] * geo
    base_order = np.argsort(-base_scores)
    focus_ids = [keep[i].ngo_id for i in base_order[:top_report]]

    alpha = concentration * BASE_WEIGHTS
    rng = np.random.default_rng(42)  # deterministic — results reproducible
    samples = rng.dirichlet(alpha, size=n_samples)  # (n_samples, 3)

    # vectorised: (n_samples,3) @ (3,n) → (n_samples, n)
    all_scores = samples @ np.vstack([sem_raw, trust / 100.0, geo])
    orders = np.argsort(-all_scores, axis=1)  # top row per sample

    top1 = orders[:, 0]
    top3 = orders[:, :3]

    out: dict[str, dict[str, float]] = {}
    for fid in focus_ids:
        pos = next(i for i, n in enumerate(keep) if n.ngo_id == fid)
        p1 = float(np.mean(top1 == pos))
        p3 = float(np.mean(np.any(top3 == pos, axis=1)))
        out[fid] = {"p_top1": round(p1, 3), "p_top3": round(max(p1, p3), 3)}
    return out
