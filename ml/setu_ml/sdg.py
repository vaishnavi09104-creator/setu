"""setu_ml.sdg — SDG auto-tagging (A11, P2 — first thing to cut if behind).

Goal-level descriptions (17), not target-level (169). Corporates must report
SDG alignment, so this is free reporting value.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .embeddings import MODEL_NAME, cosine_matrix, embed_texts

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "artifacts"
SDG_INDEX_PATH = ARTIFACTS_DIR / "sdg_vectors.npy"
SDG_META_PATH = ARTIFACTS_DIR / "sdg_vectors.meta.json"

SDG_DESCRIPTIONS: dict[int, str] = {
    1: "No poverty — end poverty in all its forms everywhere",
    2: "Zero hunger — end hunger, achieve food security and improved nutrition, promote sustainable agriculture",
    3: "Good health and well-being — ensure healthy lives and promote well-being for all at all ages",
    4: "Quality education — inclusive and equitable quality education for all",
    5: "Gender equality — empower all women and girls",
    6: "Clean water and sanitation — ensure availability and sustainable management of water and sanitation for all",
    7: "Affordable and clean energy — ensure access to affordable, reliable, sustainable modern energy",
    8: "Decent work and economic growth — full and productive employment, decent work for all",
    9: "Industry, innovation and infrastructure — build resilient infrastructure, inclusive industrialisation",
    10: "Reduced inequalities — reduce inequality within and among countries",
    11: "Sustainable cities and communities — make cities inclusive, safe, resilient, sustainable",
    12: "Responsible consumption and production — sustainable consumption and production patterns",
    13: "Climate action — take urgent action to combat climate change and its impacts",
    14: "Life below water — conserve and sustainably use oceans, seas and marine resources",
    15: "Life on land — protect, restore and promote sustainable use of terrestrial ecosystems, manage forests, halt biodiversity loss",
    16: "Peace, justice and strong institutions — inclusive societies, access to justice, accountable institutions",
    17: "Partnerships for the goals — revitalise global partnerships for sustainable development",
}

_cache: dict[str, object] = {}


def build_sdg_index() -> np.ndarray:
    """Embed all 17 goal descriptions once; persist to artifacts/ WITH engine
    metadata — a cached index from a different embedding engine silently
    produces plausible-looking garbage, which is far worse than a rebuild."""
    texts = [SDG_DESCRIPTIONS[i] for i in sorted(SDG_DESCRIPTIONS)]
    mat = embed_texts(texts)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    np.save(str(SDG_INDEX_PATH), mat)
    from .embeddings import get_model

    SDG_META_PATH.write_text(
        json.dumps({"engine": MODEL_NAME if get_model() is not None else "hashed-fallback"}),
        encoding="utf-8",
    )
    _cache.pop("vectors", None)
    return mat


def _sdg_index() -> np.ndarray:
    if "vectors" in _cache:
        return _cache["vectors"]  # type: ignore[return-value]
    from .embeddings import get_model

    engine = MODEL_NAME if get_model() is not None else "hashed-fallback"
    if SDG_INDEX_PATH.exists():
        if not SDG_META_PATH.exists():
            # legacy cache without engine metadata — rebuild, don't trust
            return build_sdg_index()
        meta = json.loads(SDG_META_PATH.read_text(encoding="utf-8"))
        if meta.get("engine") != engine:
            return build_sdg_index()  # engine switched — rebuild silently
        mat = np.load(SDG_INDEX_PATH).astype(np.float32)
    else:
        mat = build_sdg_index()
    _cache["vectors"] = mat
    return mat


def tag_sdgs(text: str, top_k: int = 3, threshold: float = 0.30,
             relative_floor: float = 0.35) -> list[dict]:
    """[{goal, name, confidence}] — absolute threshold OR relative-to-best rule.

    `threshold` is the absolute cosine floor (MiniLM scale). Because the hashed
    fallback engine produces systematically lower cosines, a tag also passes
    when it scores ≥ `relative_floor` × (best similarity) — engine-agnostic,
    so SDG tagging works identically on machines without torch. A weak
    'Life Below Water' tag for a school programme is still rejected because
    its ratio to the best (education) tag is far below the floor."""
    if not text.strip():
        return []
    q = embed_texts([text])
    sims = cosine_matrix(q, _sdg_index())[0]
    order = np.argsort(-sims)
    best = float(sims[order[0]]) if sims.size else 0.0
    out: list[dict] = []
    for i in order[:top_k]:
        conf = float(sims[i])
        passes_abs = conf >= threshold
        passes_rel = best > 0 and conf >= relative_floor * best
        if not (passes_abs or passes_rel):
            continue
        goal_no = int(i) + 1
        name = SDG_DESCRIPTIONS[goal_no].split("—")[0].strip()
        out.append({"goal": goal_no, "name": name, "confidence": round(conf, 3)})
    return out
