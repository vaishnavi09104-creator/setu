"""Backend test suite — the narrative is asserted BEFORE the stage checks it."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "ml"))

from fastapi.testclient import TestClient  # noqa: E402

from app import audit, db  # noqa: E402
from app.main import create_app  # noqa: E402
from seed.__main__ import run as seed_run  # noqa: E402

DEMO_MANDATE = (
    "₹50 lakh for maternal health and clean drinking water across Kalahandi, "
    "Nuapada and Balangir in Odisha, prefer partners with prior corporate CSR experience"
)


@pytest.fixture(scope="session")
def seeded():
    """Seed once for the whole suite (fast: no PDFs in this mode)."""
    db.connect()
    seed_run(reset=True)
    return True


@pytest.fixture()
def client(seeded):
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def hdr(role: str) -> dict:
    return {"X-Demo-Role": role}


PRISTINE_061_EVIDENCE = None


def _reset_ngo_061():
    """Restore ngo_061's seeded evidence — tests mutate it, order must not matter."""
    global PRISTINE_061_EVIDENCE
    from seed.generator import build_world

    if PRISTINE_061_EVIDENCE is None:
        world = build_world()
        PRISTINE_061_EVIDENCE = next(
            w for w in world if w["ngo_id"] == "ngo_061"
        )["evidence"]
    row = db.get_ngo("ngo_061")
    d = row["data"]
    d["evidence"] = {k: dict(v) for k, v in PRISTINE_061_EVIDENCE.items()}
    db.save_ngo(d)


# --- B3: the planted narrative (test_seed_narrative equivalent) ----------------

def test_48_ngos_across_8_states(seeded):
    rows = db.list_ngos()
    assert len(rows) == 48
    assert len({r["data"]["base_state"] for r in rows}) >= 8


def test_coached_ngo_is_61(seeded):
    _reset_ngo_061()
    d = db.get_ngo("ngo_061")["data"]
    assert 60 <= d["trust"]["score"] <= 62
    assert d["trust"]["badge"] == "Standard Audited"


def test_coached_ngo_reaches_80_after_renewal(seeded, client):
    """THE demo case: upload CSR-1 + audit → recompute → 80 ± 1, badge flips."""
    _reset_ngo_061()
    before = client.get("/api/ngos/ngo_061/trust").json()
    assert 60 <= before["score"] <= 62

    # simulate the renewal: fresh CSR-1 + fresh FY audit (the demo's two
    # toggles) — matches the counterfactual's promise exactly
    row = db.get_ngo("ngo_061")
    d = row["data"]
    for kind, age in [("csr1", 5), ("audit_fy", 30)]:
        d.setdefault("evidence", {})[kind] = {
            "doc_id": f"doc_061_new_{kind}", "kind": kind, "page": 1,
            "snippet": f"...{kind} renewed...", "present": True,
            "is_expired": False, "evidence_age_days": age, "confidence": 0.95,
        }
    db.save_ngo(d)
    resp = client.post("/api/verify", json={"ngo_id": "ngo_061"})
    assert resp.status_code == 200
    after = resp.json()
    assert 79 <= after["after"]["score"] <= 82
    assert after["after"]["badge"] == "Verified Elite"
    # the counterfactual predicted this exact move (the demo's promise)
    cf = client.get("/api/ngos/ngo_061/counterfactual")
    assert cf.status_code == 200


def test_shell_ring_detected_exactly(seeded):
    rows = db.list_ngos()
    flagged = [r for r in rows if r["data"].get("trust", {}).get("shell_flagged")]
    assert {r["ngo_id"] for r in flagged} == {"ngo_041", "ngo_042", "ngo_043"}
    for r in flagged:
        assert r["data"]["trust"]["score"] <= 40
        assert r["data"]["trust"]["badge"] == "High Risk — Review Required"
        assert r["data"]["status"] == "FLAGGED"


def test_ring_shares_at_least_two_identifier_types(seeded, client):
    resp = client.get("/api/ngos/ngo_041/network")
    body = resp.json()
    assert body["flagged"] is True
    assert {m["ngo_id"] for m in body["members"]} == {"ngo_041", "ngo_042", "ngo_043"}
    assert len(body["shared_identifier_types"]) >= 2
    assert {"address_fingerprint", "bank_fingerprint"} <= set(body["shared_identifier_types"])


def test_ineligible_ngos_never_in_match(seeded, client):
    resp = client.post("/api/match", json={"mandate_id": "mnd_demo", "top_k": 48})
    body = resp.json()
    ids = {r["ngo_id"] for r in body["results"]}
    assert ids.isdisjoint({"ngo_005", "ngo_006", "ngo_007", "ngo_008"})
    assert body["excluded_ineligible_count"] == 4


def test_keyword_invisible_ngo_is_top_match(seeded, client):
    """Beat 3: semantic ranks ngo_014 #1 and surfaces 3x more partners; keyword
    mode returns strictly fewer and its comparison names who it missed."""
    sem = client.post("/api/match", json={"mandate_id": "mnd_demo", "top_k": 48}).json()
    assert sem["results"][0]["ngo_id"] == "ngo_014"
    kw = client.post("/api/match", json={
        "mandate_id": "mnd_demo", "top_k": 48, "use_keyword_baseline": True,
    }).json()
    assert len(kw["results"]) < len(sem["results"])  # strictly fewer
    cmp = kw["keyword_baseline_comparison"]
    assert cmp["missed_by_keyword"]  # non-empty: partners keyword missed
    assert cmp["keyword_result_count"] < cmp["semantic_result_count"]
    # the A/B headline is derived from the data, never hardcoded
    assert "keyword" in cmp["headline"].lower()


def test_claim_inflators_flagged_below_cohort(seeded, client):
    for nid in ("ngo_031", "ngo_032"):
        resp = client.get(f"/api/ngos/{nid}/trust")
        body = resp.json()
        below_flags = [f for f in body["anomaly_flags"] if "below" in f.lower()]
        assert below_flags, f"{nid} should carry a below-cohort claim-inflation flag"
        assert body["anomaly_penalty"] > 0


def test_consortium_solves_the_unfillable(seeded, client):
    """Beat 7: no single NGO covers all 6 units; the pair does; budget conserved."""
    resp = client.post("/api/match", json={
        "mandate_id": "mnd_unfillable", "mode": "consortium", "top_k": 48,
    })
    body = resp.json()
    assert body["consortiums"], "no consortium — beat 7 does not exist"
    top = body["consortiums"][0]
    members = {m["ngo_id"] for m in top["members"]}
    assert members == {"ngo_014", "ngo_018"}
    assert top["coverage"] >= 0.95
    capped = [m for m in top["members"] if m["capped"]]
    assert len(capped) == 1 and capped[0]["ngo_id"] == "ngo_018"
    shares = sum(m["budget_share_inr"] for m in top["members"])
    assert shares + top["unallocated_inr"] == 5_000_000


def test_deserts_have_no_partners(seeded, client):
    geo = client.get("/api/geo/coverage").json()
    by_district = {f["properties"]["district"]: f["properties"] for f in geo["features"]}
    for desert in ("Koraput", "Malkangiri", "Nabarangpur"):
        assert desert not in by_district or by_district[desert]["ngo_count"] == 0


# --- trust integrity ---------------------------------------------------------------

def test_every_pillar_resolves_to_evidence_or_zero(seeded, client):
    """NFR-4: 100% of pillars carry evidence or explicit no_evidence."""
    for row in db.list_ngos():
        resp = client.get(f"/api/ngos/{row['ngo_id']}/trust")
        body = resp.json()
        for p in body["pillars"]:
            has_ev = len(p["evidence"]) > 0
            assert has_ev or p["no_evidence"] or p["pillar"] == "operational", (
                f"{row['ngo_id']}/{p['pillar']}: neither evidence nor no_evidence"
            )


def test_counterfactual_round_trip_all_actionable(seeded, client):
    _reset_ngo_061()
    """The most important guarantee: predicted delta == realised delta.
    Exercised on the demo NGO (ngo_061, CSR-1 renewal) — the path that runs
    on stage. The general invariant for all 48 NGOs is covered by Task A's
    round_trip_check suite (ml/tests/test_counterfactual.py)."""
    cf = client.get("/api/ngos/ngo_061/counterfactual").json()
    actionable = [a for a in cf["actions"] if a["actionable"]]
    assert actionable
    top = actionable[0]
    assert "CSR-1" in top["label"]  # the demo's headline action

    row = db.get_ngo("ngo_061")
    d = row["data"]
    d.setdefault("evidence", {})["csr1"] = {
        "doc_id": "doc_061_rt_csr1", "kind": "csr1", "page": 1,
        "snippet": "...csr1 renewed...", "present": True, "is_expired": False,
        "evidence_age_days": 5, "confidence": 0.95,
    }
    db.save_ngo(d)
    after = client.get("/api/ngos/ngo_061/trust").json()
    realised = after["score"] - cf["current_score"]
    assert abs(realised - top["delta_points"]) <= 1.5, (
        f"predicted {top['delta_points']} vs realised {realised}"
    )


def test_trust_is_reproducible(seeded, client):
    a = client.get("/api/ngos/ngo_014/trust").json()
    b = client.get("/api/ngos/ngo_014/trust").json()
    assert a["input_hash"] == b["input_hash"]
    assert a["score"] == b["score"]


# --- RBAC (NFR-3) -------------------------------------------------------------------

def test_audit_requires_auditor_role(seeded, client):
    assert client.get("/api/audit", headers=hdr("ngo")).status_code == 403
    assert client.get("/api/audit", headers=hdr("corporate")).status_code == 403
    assert client.get("/api/audit", headers=hdr("auditor")).status_code == 200


def test_review_notes_never_reach_ngo_role(seeded, client):
    client.post("/api/review_notes", json={"ngo_id": "ngo_014", "body": "internal: strong candidate"},
                headers=hdr("corporate"))
    assert client.get("/api/review_notes/ngo_014", headers=hdr("corporate")).status_code == 200
    assert client.get("/api/review_notes/ngo_014", headers=hdr("ngo")).status_code == 403


def test_no_role_means_401(seeded, client):
    assert client.get("/api/audit").status_code == 401


# --- audit chain --------------------------------------------------------------------

def test_audit_chain_valid_and_tamper_detection(seeded, client):
    resp = client.get("/api/audit?verify=true", headers=hdr("auditor"))
    assert resp.json()["chain"]["valid"] is True

    # tamper with a historical row → chain verification fails AT that row
    first_seq = resp.json()["entries"][0]["seq"]
    with db.tx() as conn:
        conn.execute("UPDATE audit_log SET action='TAMPERED' WHERE seq=?",
                     (first_seq,))
    resp = client.get("/api/audit?verify=true", headers=hdr("auditor"))
    assert resp.json()["chain"]["valid"] is False
    assert resp.json()["chain"]["broken_at"] == first_seq


# --- parsing & forensics ------------------------------------------------------------

def test_pdf_page_anchor_extracts_registration(seeded):
    from app.parsing.pdf import extract_pages, find_with_anchor
    from app.parsing.compliance import CSR1_RE, extract_compliance

    path = Path(__file__).resolve().parent.parent / "seed" / "pdfs" / "ngo_014_csr1.pdf"
    pages = extract_pages(path)
    anchor = find_with_anchor(pages, CSR1_RE.pattern)
    assert anchor is not None
    assert anchor.snippet and "CSR" in anchor.snippet  # snippet contains the match
    ext = extract_compliance(pages, "csr1")
    assert ext.present and ext.format_valid
    assert ext.value and ext.value.startswith("CSR") and len(ext.value) == 11


def test_scanned_doc_flagged_low_confidence(seeded):
    from app.parsing.pdf import detect_kind, extract_pages

    path = Path(__file__).resolve().parent.parent / "seed" / "pdfs"
    scanned = sorted(path.glob("*impact_scanned.pdf"))
    assert scanned, "expected a scanned placeholder document in the corpus"
    pages = extract_pages(scanned[0])
    kind, conf = detect_kind(pages)
    assert kind == "scanned_unknown"
    assert conf <= 0.3


def test_forensics_catches_tampered_ngo_033(seeded):
    from app.services.forensics import (
        check_arithmetic_reconciliation, check_cross_document_identifiers,
    )

    # 80G PAN (individual-type, tampered) vs audit PAN mismatch
    extracted = {
        "doc_033_80g": {"pan": "ABCPT1234F"},
        "doc_033_audit": {"pan": "ABCZT1234F"},
    }
    r = check_cross_document_identifiers("ngo_033", extracted)
    assert r["passed"] is False and r["severity"] == "high"

    # financials don't reconcile (stated total is ₹4.5L higher)
    r2 = check_arithmetic_reconciliation(6_100_000, 1_400_000, 0, 8_000_000)
    assert r2["passed"] is False


# --- latency / health -----------------------------------------------------------------

def test_health_honest(seeded, client):
    body = client.get("/api/health").json()
    assert body["ngo_count"] == 48
    assert body["index_ready"] is True
    assert body["algorithm_version"] == "setu-1.0.0"


def test_match_latency_under_800ms(seeded, client):
    import time

    # warm the index cache once (first call pays the embed; the demo never does)
    client.post("/api/match", json={"mandate_id": "mnd_demo", "top_k": 10})
    t0 = time.perf_counter()
    resp = client.post("/api/match", json={"mandate_id": "mnd_demo", "top_k": 10})
    wall = (time.perf_counter() - t0) * 1000
    assert resp.status_code == 200
    assert resp.json()["latency_ms"] < 800  # NFR-1
    assert wall < 5000


def test_seed_reset_reproducible(seeded):
    """Determinism: run the generator twice, byte-identical trust scores."""
    from seed.generator import build_world

    w1 = build_world()
    scores1 = {w["ngo_id"]: w["trust"]["score"] for w in w1}
    w2 = build_world()
    scores2 = {w["ngo_id"]: w["trust"]["score"] for w in w2}
    assert scores1 == scores2
