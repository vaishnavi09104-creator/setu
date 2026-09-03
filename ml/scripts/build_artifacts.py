"""Build the committed ML artifacts after the seed corpus exists (Hour 12).

Usage (from backend/ after `seed --reset`, or from ml/ with any corpus):
    python -m scripts.build_artifacts --corpus path/to/ngos.json

Reads a JSON list of NgoProfile dicts, then:
  1. builds and saves ngo_embeddings.npy + manifest (nothing embeds at request time)
  2. fits calibration.json (LO=5th, HI=95th percentile over mandate×NGO pairs)
  3. rebuilds sdg_vectors.npy with engine metadata
Prints the calibration distribution + top-10 sanity check for eyeballing.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from setu_ml.calibrate import fit_semantic_calibration, sanity_check_top
from setu_ml.embeddings import build_ngo_index, save_index
from setu_ml.extract import parse_mandate_rules
from setu_ml.sdg import build_sdg_index
from setu_ml.types import Mandate, NgoProfile

DEMO_MANDATE_TEXT = (
    "₹50 lakh for maternal health and clean drinking water across Kalahandi, "
    "Nuapada and Balangir in Odisha, prefer partners with prior corporate CSR experience"
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, help="JSON list of NgoProfile dicts")
    ap.add_argument("--mandates", default=None,
                    help="optional JSON list of raw mandate strings for calibration")
    args = ap.parse_args()

    raw = json.loads(Path(args.corpus).read_text(encoding="utf-8"))
    ngos = [NgoProfile.model_validate(n) for n in raw]
    print(f"corpus: {len(ngos)} NGOs")

    # 1. index
    mat, ids = build_ngo_index(ngos)
    save_index(mat, ids)
    print(f"index saved: {mat.shape}")

    # 2. calibration — demo mandate + optional extra mandate strings
    mandate_texts = [DEMO_MANDATE_TEXT]
    if args.mandates:
        mandate_texts += json.loads(Path(args.mandates).read_text(encoding="utf-8"))
    mandates = [parse_mandate_rules(t) for t in mandate_texts]
    fit_semantic_calibration(mandates, ngos)

    # 3. SDG vectors with engine metadata
    build_sdg_index()
    print("sdg index rebuilt")

    # 4. eyeball aid
    demo = parse_mandate_rules(DEMO_MANDATE_TEXT)
    check = sanity_check_top(demo, ngos, (mat, ids))
    print(f"top-10 calibrated scores: {check['top_calibrated']}")
    print(f"sanity verdict: {check['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
