"""A1/A2/A3 — types, embeddings engine, geo."""
from __future__ import annotations

import math

import numpy as np
import pytest

from setu_ml.embeddings import (
    cosine_matrix,
    embed_texts,
    ngo_embedding_text,
    build_ngo_index,
)
from setu_ml.geo import (
    centroid,
    district_jaccard,
    find_district,
    geo_score,
    haversine_km,
    min_distance_km,
    state_districts,
    _norm,
)
from setu_ml.types import Domain, Mandate

from factories import make_demo_mandate, ngo, odisha_districts, dref


# --- A2 embeddings -----------------------------------------------------------

def test_identical_text_cosine_one():
    a = embed_texts(["ashagram runs maternal health clinics in tribal odisha"])
    b = embed_texts(["ashagram runs maternal health clinics in tribal odisha"])
    sim = float(a[0] @ b[0])
    assert sim > 0.999


def test_related_scores_higher_than_unrelated():
    maternal = embed_texts(["postpartum institutional delivery care and ASHA worker training"])
    m_mandate = embed_texts(["postpartum delivery care training for ASHA workers"])
    forest = embed_texts(["reforestation and biodiversity conservation of western ghats"])
    sim_mm = float(m_mandate[0] @ maternal[0])
    sim_mf = float(m_mandate[0] @ forest[0])
    assert sim_mm > sim_mf
    assert sim_mm > 0.05  # some real overlap in-domain
    assert sim_mf < 0.02  # and near-zero cross-domain


def test_matrix_shape_and_norm():
    mat = embed_texts(["one two three", "four five six", "seven eight"])
    assert mat.shape == (3, 384)
    assert mat.dtype == np.float32
    assert np.allclose(np.linalg.norm(mat, axis=1), 1.0, atol=1e-3)


def test_cosine_matrix_rejects_unnormalised():
    with pytest.raises(ValueError):
        cosine_matrix(np.array([[2.0, 0, 0, 0]]), np.array([[1.0, 0, 0, 0]]))


def test_cosine_matrix_rejects_dim_mismatch():
    with pytest.raises(ValueError):
        cosine_matrix(np.ones((1, 384), dtype=np.float32),
                      np.ones((2, 300), dtype=np.float32))


def test_ngo_embedding_text_contains_key_facts():
    n = ngo("ngo_1", "Test Org",
            proposal_text="we do things",
            districts_covered=odisha_districts("Kalahandi"),
            primary_domain=Domain.WASH)
    t = ngo_embedding_text(n)
    assert "Test Org" in t and "Kalahandi" in t and "wash" in t and "we do things" in t


def test_build_ngo_index_order():
    ngos = [ngo("ngo_a", "A"), ngo("ngo_b", "B"), ngo("ngo_c", "C")]
    mat, ids = build_ngo_index(ngos)
    assert ids == ["ngo_a", "ngo_b", "ngo_c"]
    assert mat.shape[0] == 3


def test_load_index_missing_raises():
    from setu_ml.embeddings import load_index

    # no index committed in test env → clear actionable error
    import setu_ml.embeddings as emb

    if not emb.INDEX_PATH.exists():
        with pytest.raises(FileNotFoundError):
            load_index()
    else:
        pytest.skip("index present in this env — covered by seed tests")


# --- A3 geo -------------------------------------------------------------------

def test_haversine_delhi_mumbai():
    d = haversine_km(28.61, 77.21, 19.08, 72.88)
    assert 1100 <= d <= 1300


def test_jaccard_identical_and_disjoint():
    assert district_jaccard(["Kalahandi", "Nuapada"], ["kalahandi ", "Nuapada"]) == 1.0
    assert district_jaccard(["Kalahandi"], ["Pune"]) == 0.0
    assert district_jaccard([], ["Pune"]) == 0.0


def test_jaccard_partial():
    j = district_jaccard(["Kalahandi", "Nuapada", "Balangir"], ["Kalahandi"])
    assert abs(j - 1 / 3) < 1e-9


def test_norm_handles_noise():
    assert _norm("Kalahandi District ") == _norm("kalahandi")
    assert _norm("  Raigarh ") == "raigarh"


def test_geo_score_in_range_and_preference():
    m = make_demo_mandate()
    near = ngo("ngo_near", "NearOrg", districts_covered=odisha_districts("Kalahandi", "Nuapada"),
               primary_domain=Domain.MATERNAL_HEALTH)
    far = ngo("ngo_far", "FarOrg", districts_covered=[dref("Pune", "Maharashtra", 18.52, 73.86)],
              base_district="Pune", base_state="Maharashtra",
              primary_domain=Domain.EDUCATION)
    g_near = geo_score(m, near)
    g_far = geo_score(m, far)
    assert 0.0 <= g_near <= 1.0 and 0.0 <= g_far <= 1.0
    assert g_near > g_far


def test_min_distance_inf_on_empty():
    m = Mandate(raw_text="x", domains=[], budget_inr=0, districts=[])
    n = ngo("ngo_x", "X")
    assert math.isinf(min_distance_km(m, n))


def test_centroid():
    c = centroid(odisha_districts("Kalahandi", "Nuapada"))
    assert 19.9 < c[0] < 20.2 and 82.5 < c[1] < 83.3


def test_find_district_and_state_expansion():
    d = find_district("KALAHANDI ")
    assert d is not None and d.state == "Odisha" and d.is_aspirational
    assert len(state_districts("odisha")) > 10
    assert find_district("NotARealPlace") is None
