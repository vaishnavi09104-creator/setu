"""setu_ml.embeddings — local, cached, offline-proof embeddings (Task A, item A2).

Two engines behind one interface:
  1. `all-MiniLM-L6-v2` via sentence-transformers, loaded ONLY from the committed
     local cache (never the network). 384 dims, L2-normalised at embed time so
     cosine similarity is a plain dot product.
  2. A deterministic 384-dim hashed bag-of-ngrams fallback (no dependencies) so
     the library, the backend and the whole demo still function on machines where
     torch is not installed. Same ranking guarantees cannot be claimed for it —
     but no code path crashes and the calibration refits.

Performance story: normalise once at embed time; then cosine = Q @ C.T, one
matmul, ~15ms for 1000x384. That is why we do not need a vector database.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from pathlib import Path

import numpy as np

from .types import NgoProfile

logger = logging.getLogger("setu_ml.embeddings")

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "artifacts"
MODEL_PATH = ARTIFACTS_DIR / "minilm"
INDEX_PATH = ARTIFACTS_DIR / "ngo_embeddings.npy"
MANIFEST_PATH = ARTIFACTS_DIR / "ngo_index_manifest.json"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DIM = 384

_WORD_RE = re.compile(r"[a-z0-9]+")

_model = None  # singleton


def get_model():
    """Singleton. Loads from the committed local path only — never the network."""
    global _model
    if _model is not None:
        return _model
    try:
        from sentence_transformers import SentenceTransformer

        if MODEL_PATH.exists():
            logger.info("loading embedding model from local cache %s", MODEL_PATH)
            _model = SentenceTransformer(str(MODEL_PATH))
        else:
            logger.warning(
                "local model cache missing; falling back to hashed embeddings. "
                "Run the Hour-0 model download command and commit ml/artifacts/minilm."
            )
            return None
    except Exception as exc:  # pragma: no cover - environment-dependent
        logger.warning("sentence-transformers unavailable (%s); using hashed fallback", exc)
        return None
    return _model


def download_model() -> None:
    """Hour-0 helper: fetch MiniLM once and save into artifacts/minilm."""
    from sentence_transformers import SentenceTransformer

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    SentenceTransformer(MODEL_NAME).save(str(MODEL_PATH))
    logger.info("model saved to %s — commit this directory", MODEL_PATH)


def _tokens(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


def _hashed_embed(texts: list[str], dim: int = DIM) -> np.ndarray:
    """Deterministic feature hashing over word uni+bi-grams. No dependencies.

    Not semantically as strong as MiniLM — but stable, fast, offline, and enough
    for the demo-mode fallback path. Two identical strings always collide at 1.0.
    """
    mat = np.zeros((len(texts), dim), dtype=np.float32)
    for i, text in enumerate(texts):
        toks = _tokens(text)
        feats = toks + [f"{a}_{b}" for a, b in zip(toks, toks[1:])]
        for f in feats:
            h = int.from_bytes(
                hashlib.md5(f.encode("utf-8")).digest()[:8], "little", signed=False
            )
            idx = h % dim
            sign = 1.0 if ((h >> 8) & 1) else -1.0
            mat[i, idx] += sign
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return mat / norms


def embed_texts(texts: list[str], normalize: bool = True) -> np.ndarray:
    """(n, 384) float32. Normalised, so cosine similarity is a plain dot product."""
    if not texts:
        return np.zeros((0, DIM), dtype=np.float32)
    model = get_model()
    if model is None:
        out = _hashed_embed(texts)
    else:
        out = np.asarray(model.encode(texts, batch_size=64), dtype=np.float32)
    if normalize:
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        out = out / norms
    return out.astype(np.float32)


def cosine_matrix(query: np.ndarray, corpus: np.ndarray) -> np.ndarray:
    """(n_query, n_corpus). Assumes both already L2-normalised — assert it."""
    q = np.atleast_2d(np.asarray(query, dtype=np.float32))
    c = np.atleast_2d(np.asarray(corpus, dtype=np.float32))
    qn = np.linalg.norm(q, axis=1)
    cn = np.linalg.norm(c, axis=1)
    if not np.allclose(qn, 1.0, atol=1e-3) or not np.allclose(cn, 1.0, atol=1e-3):
        raise ValueError(
            "cosine_matrix expects L2-normalised inputs — normalise at embed time"
        )
    if q.shape[1] != c.shape[1]:
        raise ValueError(
            f"dimension mismatch: query {q.shape[1]} vs corpus {c.shape[1]} — "
            "the index was built with a different model; rebuild it"
        )
    return q @ c.T


def ngo_embedding_text(ngo: NgoProfile) -> str:
    """ONE canonical text construction for an NGO — used by indexing AND any
    re-embedding. Two constructions in two places is a bug."""
    secondary = ", ".join(d.value for d in ngo.secondary_domains)
    if secondary:
        secondary = f", {secondary}"
    geo = ", ".join(f"{d.district}, {d.state}" for d in ngo.districts_covered)
    return (
        f"{ngo.name}. Focus: {ngo.primary_domain.value}{secondary}. "
        f"Operates in: {geo}. {ngo.proposal_text}"
    )


def build_ngo_index(ngos: list[NgoProfile]) -> tuple[np.ndarray, list[str]]:
    """Embed proposal_text for every NGO. Returns (matrix, ngo_ids) in order."""
    texts = [ngo_embedding_text(n) for n in ngos]
    mat = embed_texts(texts)
    return mat, [n.ngo_id for n in ngos]


def save_index(matrix: np.ndarray, ngo_ids: list[str]) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    np.save(str(INDEX_PATH), matrix.astype(np.float32))
    manifest = {
        "ngo_ids": ngo_ids,
        "model": MODEL_NAME if get_model() is not None else "hashed-fallback",
        "dimension": int(matrix.shape[1]),
        "created_at": __import__("datetime")
        .datetime.now(__import__("datetime").timezone.utc)
        .isoformat(),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    logger.info("index saved: %d ngos, dim=%d", len(ngo_ids), matrix.shape[1])


def load_index() -> tuple[np.ndarray, list[str]]:
    """Load the committed index. Raise a clear, actionable error on absence or
    model mismatch — a silent mismatch produces plausible-looking garbage scores,
    which is far worse than a crash."""
    if not INDEX_PATH.exists() or not MANIFEST_PATH.exists():
        raise FileNotFoundError(
            "embedding index missing — run build_ngo_index + save_index first, "
            "or seed via the backend's seed script (ml/artifacts/ngo_embeddings.npy)"
        )
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    matrix = np.load(INDEX_PATH).astype(np.float32)
    ngo_ids: list[str] = manifest["ngo_ids"]
    if matrix.shape[0] != len(ngo_ids):
        raise ValueError(
            f"index/manifest mismatch: matrix has {matrix.shape[0]} rows but "
            f"manifest lists {len(ngo_ids)} ngos — rebuild the index"
        )
    current = MODEL_NAME if get_model() is not None else "hashed-fallback"
    if manifest.get("model") != current:
        raise ValueError(
            f"index built with '{manifest.get('model')}' but current engine is "
            f"'{current}' — rebuild the index or the scores are meaningless"
        )
    if matrix.shape[1] != DIM:
        raise ValueError(
            f"index dimension {matrix.shape[1]} != expected {DIM} — different model"
        )
    return matrix, ngo_ids
