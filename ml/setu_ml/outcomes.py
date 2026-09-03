"""setu_ml.outcomes — the feedback loop (A12, P2). §5.10.

Claim ONLY what this does and nothing more: realised outcomes update the
track-record pillar directly, and the calibration is reported honestly.
Never say "the model retrains" — with a synthetic dataset that claim
collapses under one follow-up question.
"""
from __future__ import annotations

from .types import NgoProfile, Outcome, TrackRecord


def update_track_record(ngo: NgoProfile, outcome: Outcome) -> TrackRecord:
    """Increment projects_total and, if realised_impact ≥ 50% of predicted,
    projects_completed. This is the real feedback: a completed project
    genuinely moves the O pillar through the Laplace-smoothed formula."""
    t = ngo.track_record.model_copy(deep=True)
    t.projects_total += 1
    success = outcome.realised_impact >= 0.5 * max(outcome.predicted_impact, 1e-9)
    if success:
        t.projects_completed += 1
        if t.milestones_total > t.milestones_met:
            t.milestones_met += 1
    return t


def calibration_curve(outcomes: list[Outcome], n_buckets: int = 5) -> list[dict]:
    """Bucket by predicted-impact bucket; mean predicted vs mean realised per
    bucket, with counts. A well-calibrated system sits on the diagonal."""
    if not outcomes:
        return []
    preds = sorted(o.predicted_impact for o in outcomes)
    # equal-count bucket edges
    edges = [preds[min(int(i * len(preds) / n_buckets), len(preds) - 1)]
             for i in range(n_buckets + 1)]
    edges = sorted(set(edges))
    if len(edges) < 2:
        return [{
            "bucket": 0,
            "mean_predicted": round(sum(o.predicted_impact for o in outcomes) / len(outcomes), 3),
            "mean_realised": round(sum(o.realised_impact for o in outcomes) / len(outcomes), 3),
            "count": len(outcomes),
        }]
    buckets: list[dict] = []
    for b in range(len(edges) - 1):
        lo, hi = edges[b], edges[b + 1]
        sel = [o for o in outcomes
               if (lo <= o.predicted_impact < hi)
               or (b == len(edges) - 2 and o.predicted_impact == hi)]
        if not sel:
            continue
        buckets.append({
            "bucket": b,
            "mean_predicted": round(sum(o.predicted_impact for o in sel) / len(sel), 3),
            "mean_realised": round(sum(o.realised_impact for o in sel) / len(sel), 3),
            "count": len(sel),
        })
    return buckets
