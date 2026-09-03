"""setu_ml.calibrate — fit the semantic calibration on the real corpus (A6).

LO = 5th percentile (noise floor), HI = 95th percentile (realistic ceiling —
NOT max, which is one lucky pair). The result is committed as
ml/artifacts/calibration.json and loaded by scoring.semantic_score.

Sanity target after fitting: demo-mandate top match ~0.85–0.92 calibrated,
tenth match ~0.45–0.60. If everything reads 95% or everything reads 40%,
the calibration is not doing its job.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .embeddings import cosine_matrix, embed_texts, ngo_embedding_text, get_model
from .types import Mandate, NgoProfile

logger = logging.getLogger("setu_ml.calibrate")

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "artifacts"
CALIBRATION_PATH = ARTIFACTS_DIR / "calibration.json"

DEFAULT_LO = 0.15
DEFAULT_HI = 0.80


def fit_semantic_calibration(
    mandates: list[Mandate],
    ngos: list[NgoProfile],
    lo_pct: float = 5.0,
    hi_pct: float = 95.0,
) -> dict:
    """Compute cosine for every mandate × NGO pair, take the percentile window,
    write calibration.json. Returns the written dict."""
    if not mandates or not ngos:
        raise ValueError("need at least one mandate and one NGO to fit calibration")

    corpus = np.stack([embed_texts([ngo_embedding_text(n)])[0] for n in ngos])
    q = embed_texts([m.raw_text for m in mandates])
    sims = cosine_matrix(q, corpus).ravel()

    lo = float(np.percentile(sims, lo_pct))
    hi = float(np.percentile(sims, hi_pct))
    if hi <= lo + 1e-4:
        logger.warning("degenerate percentile window; falling back to defaults")
        lo, hi = DEFAULT_LO, DEFAULT_HI

    table = {
        f"p{p}": round(float(np.percentile(sims, p)), 4)
        for p in (1, 5, 10, 25, 50, 75, 90, 95, 99)
    }
    payload = {
        "LO": lo,
        "HI": hi,
        "lo_pct": lo_pct,
        "hi_pct": hi_pct,
        "percentile_table": table,
        "n_pairs": int(sims.size),
        "model": "sentence-transformers/all-MiniLM-L6-v2" if get_model() is not None else "hashed-fallback",
        "fitted_at": datetime.now(timezone.utc).isoformat(),
    }
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    CALIBRATION_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # eyeball aid — distribution across pairs
    logger.info("calibration fitted: LO=%.3f HI=%.3f over %d pairs", lo, hi, sims.size)
    logger.info("distribution: %s", table)
    print(f"calibration: LO={lo:.3f} HI={hi:.3f} over {sims.size} pairs")
    print(f"percentiles: {table}")
    return payload


def load_calibration() -> dict:
    if CALIBRATION_PATH.exists():
        return json.loads(CALIBRATION_PATH.read_text(encoding="utf-8"))
    return {"LO": DEFAULT_LO, "HI": DEFAULT_HI, "default": True}


def sanity_check_top(mandate: Mandate, ngos: list[NgoProfile], index) -> dict:
    """Eyeball aid for Hour 12: calibrated scores of the demo mandate's top 10.
    Warn when the spread is useless."""
    from .scoring import rank_ngos

    results, _ = rank_ngos(mandate, ngos, index, top_k=10)
    cals = [r.semantic_score for r in results]
    out = {
        "top_calibrated": [round(c, 3) for c in cals],
        "spread": round((max(cals) - min(cals)), 3) if cals else 0.0,
    }
    if cals:
        if all(c > 0.90 for c in cals):
            out["verdict"] = "TOO HIGH — widen the percentile window and refit"
        elif all(c < 0.40 for c in cals):
            out["verdict"] = "TOO LOW — narrow the window and refit"
        elif (max(cals) - min(cals)) < 0.10:
            out["verdict"] = "BUNCHED — distribution not discriminating"
        else:
            out["verdict"] = "sensible"
    return out
