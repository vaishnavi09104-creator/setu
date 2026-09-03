"""setu_ml.pareto — the non-dominated frontier (A10, P2). §5.7.

Non-dominated over (semantic_score, trust_score, −cost_per_beneficiary).
A dominates B if A ≥ B on all three and > on at least one. O(n²) is fine
at n=10. Typically 3–6 survive.
"""
from __future__ import annotations

from .types import MatchResult


def _key(r: MatchResult) -> tuple[float, float, float]:
    # cost: LOWER is better → negate
    return (r.semantic_score, r.trust_score, -r.cost_per_beneficiary_inr)


def pareto_front(results: list[MatchResult]) -> list[str]:
    """Return ngo_ids of the non-dominated set, preserving input order."""
    out: list[str] = []
    for i, a in enumerate(results):
        ka = _key(a)
        dominated = False
        for j, b in enumerate(results):
            if i == j:
                continue
            kb = _key(b)
            if (
                kb[0] >= ka[0]
                and kb[1] >= ka[1]
                and kb[2] >= ka[2]
                and (kb[0] > ka[0] or kb[1] > ka[1] or kb[2] > ka[2])
            ):
                dominated = True
                break
        if not dominated:
            out.append(a.ngo_id)
    return out
