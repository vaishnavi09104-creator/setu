"""app.services.mock — contract-shaped stub responses (B2, ship by Hour 8).

One JSON file per endpoint under seed/data/mock_responses/, loaded verbatim
when USE_MOCK_DATA=true. The examples in 00-PROJECT-CONTEXT.md §6 were written
to be exactly this shape.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

MOCK_DIR = Path(__file__).resolve().parent.parent.parent / "seed" / "data" / "mock_responses"


@lru_cache
def _load(name: str) -> dict | list:
    path = MOCK_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"mock response '{name}' missing — add seed/data/mock_responses/{name}.json"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def mock_response(name: str) -> dict | list:
    """Used when settings.use_mock_data is true."""
    return _load(name)
