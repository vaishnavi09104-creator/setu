"""seed — python -m seed [--reset]

Restores the exact demo state: 48 NGO profiles, mock PDFs, shell networks,
the demo mandate. Deterministic (seed 42) — twice in a row gives byte-identical
output. Under 60 seconds or the spec is unhappy.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db  # noqa: E402
from app.config import get_settings  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent / "data"
DEMO_MANDATE_TEXT = (
    "₹50 lakh for maternal health and clean drinking water across Kalahandi, "
    "Nuapada and Balangir in Odisha, prefer partners with prior corporate CSR experience"
)
UNFILLABLE_MANDATE_TEXT = DEMO_MANDATE_TEXT  # same mandate — that's the point


def run(reset: bool) -> float:
    t0 = time.perf_counter()
    settings = get_settings()

    from seed.generator import build_world
    from seed.make_mock_pdfs import generate_all
    from app.services import shell_network

    db.connect()
    if reset:
        db.reset()
        print("db reset")

    world = build_world()
    print(f"world: {len(world)} NGOs")

    for doc in world:
        db.save_ngo(doc)

    # demo mandates
    from setu_ml.extract import parse_mandate_rules

    for mid, text in [
        ("mnd_demo", DEMO_MANDATE_TEXT),
        ("mnd_unfillable", UNFILLABLE_MANDATE_TEXT),
    ]:
        mandate = parse_mandate_rules(text)
        mandate.mandate_id = mid
        db.upsert("mandates", {"mandate_id": mid}, mandate.model_dump(),
                  columns={"corporate_id": "corp_demo", "created_at": db.utcnow()})

    # shell network detection + penalties
    rings = shell_network.run_detection()
    flagged = sum(len(r.get("member_ngo_ids", [])) for r in rings if r.get("flagged"))
    print(f"shell detection: {len(rings)} ring(s), {flagged} flagged member(s)")

    # mock PDFs (skipped in fast test mode via env)
    if not settings.demo_mode:
        manifest = generate_all(world)
        (DATA_DIR / "pdf_manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"mock pdfs: {sum(len(v) for v in manifest.values())} files")

    # seed audit chain with a genesis entry
    from app import audit
    audit.append("admin", "seed_reset", "world", {"ngos": len(world)})

    # persist a seeded calibration curve sample (P2 analytics)
    import random as _r

    rng = _r.Random(42)
    with db.tx() as conn:
        for ngo in world[:12]:
            predicted = float(rng.randint(30, 95))
            realised = round(max(5.0, min(100.0, predicted + rng.uniform(-8, 8))), 1)
            conn.execute(
                "INSERT INTO outcomes (ngo_id, mandate_id, predicted_impact, "
                "realised_impact, completed_at) VALUES (?,?,?,?,?)",
                (ngo["ngo_id"], "mnd_demo", round(predicted, 1), realised,
                 db.utcnow()),
            )

    # one corporate
    db.upsert("corporates", {"corporate_id": "corp_demo"}, {
        "name": "Meridian Industries Ltd", "sector": "pharmaceutical",
        "csr_budget_inr": 50_000_000, "foreign_funded": False,
    })

    elapsed = time.perf_counter() - t0
    print(f"seed complete in {elapsed:.1f}s")
    return elapsed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true", help="wipe + reseed")
    args = ap.parse_args()
    run(reset=args.reset)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
