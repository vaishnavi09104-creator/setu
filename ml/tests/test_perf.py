"""Performance bounds (NFR-1): rank over 1,000 synthetic NGOs < 150 ms.
Marked `perf` — run with `pytest -m perf` in the perf environment."""
from __future__ import annotations

import random
import time

import pytest

from setu_ml.embeddings import build_ngo_index
from setu_ml.scoring import rank_ngos

from factories import DEMO_MANDATE_TEXT, dref, financials, ngo, odisha_districts
from setu_ml.extract import parse_mandate_rules

pytestmark = pytest.mark.perf

STATES = [
    ("Kalahandi", "Odisha"), ("Nuapada", "Odisha"), ("Balangir", "Odisha"),
    ("Pune", "Maharashtra"), ("Nagpur", "Maharashtra"), ("Raipur", "Chhattisgarh"),
    ("Bhopal", "Madhya Pradesh"), ("Ranchi", "Jharkhand"), ("Gaya", "Bihar"),
]


def _make_world(n: int = 1000) -> list:
    rng = random.Random(42)
    world = []
    for i in range(n):
        dname, dstate = STATES[i % len(STATES)]
        world.append(
            ngo(
                f"perf_{i}",
                f"Perf NGO {i}",
                districts_covered=odisha_districts(dname) if dstate == "Odisha"
                else [dref(dname, dstate, 20 + (i % 5), 80 + (i % 9))],
                base_district=dname,
                base_state=dstate,
                budget_request_inr=1_000_000 + (i * 37) % 9_000_000,
                trust_score=40 + (i * 13) % 55,
                financials=financials(
                    programme_expense_inr=5_000_000 + (i * 91) % 5_000_000,
                    beneficiaries_reached=3_000 + (i * 53) % 20_000,
                ),
                proposal_text=(
                    f"Organisation {i} runs community programmes in {dname} with "
                    f"{rng.choice(['education', 'health', 'water', 'skilling'])} focus"
                ),
            )
        )
    return world


def test_rank_1000_ngos_under_150ms():
    world = _make_world(1000)
    mandate = parse_mandate_rules(DEMO_MANDATE_TEXT)
    t0 = time.perf_counter()
    index = build_ngo_index(world)
    build_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    results, excluded = rank_ngos(mandate, world, index, top_k=10)
    rank_ms = (time.perf_counter() - t0) * 1000

    assert len(results) == 10
    print(f"\nindex build: {build_ms:.0f} ms · rank: {rank_ms:.0f} ms (n=1000)")
    assert rank_ms < 150, f"rank took {rank_ms:.0f} ms — over the 150 ms bound"
