"""setu_ml.geo — distance and district overlap (Task A, item A3). §5.3."""
from __future__ import annotations

import math
import re

from .types import DistrictRef, Mandate, NgoProfile

EARTH_RADIUS_KM = 6371.0

# Normalise Indian district names through ONE helper. Names arrive with
# inconsistent casing, spacing and transliteration variants; if Jaccard
# silently returns 0 because of a trailing space, geo scores are quietly
# wrong everywhere and nothing crashes to tell you.
_NOISE_WORDS = {
    "district", "distt", "dist", "dt", "(pr)", "rural", "urban",
}


def _norm(name: str) -> str:
    s = (name or "").lower().strip()
    # token-level noise removal (NOT substring — 'district' contains 'dist')
    toks = [t for t in re.split(r"[\s,()]+", s) if t and t not in _NOISE_WORDS]
    s = " ".join(toks)
    s = "".join(ch if ch.isalnum() else " " for ch in s)
    return " ".join(s.split())


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance. Earth radius 6371.0 km."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(min(1.0, a)))


def district_jaccard(mandate_districts: list[str], ngo_districts: list[str]) -> float:
    """Case- and whitespace-normalised set Jaccard. Empty mandate list → 0.0."""
    if not mandate_districts or not ngo_districts:
        return 0.0
    m = {_norm(d) for d in mandate_districts}
    n = {_norm(d) for d in ngo_districts}
    union = m | n
    if not union:
        return 0.0
    return len(m & n) / len(union)


def min_distance_km(mandate: Mandate, ngo: NgoProfile) -> float:
    """Minimum haversine over all (mandate district, NGO district) pairs.
    Returns inf if either side has no coordinates."""
    if not mandate.districts or not ngo.districts_covered:
        return float("inf")
    best = float("inf")
    for md in mandate.districts:
        for nd in ngo.districts_covered:
            d = haversine_km(md.lat, md.lng, nd.lat, nd.lng)
            if d < best:
                best = d
    return best


def geo_score(mandate: Mandate, ngo: NgoProfile) -> float:
    """§5.3:  0.60 * district_jaccard + 0.40 * exp(-min_km / 150.0), clamped [0,1].

    If the mandate names only a state, the Jaccard runs over that state's
    districts present in the NGO's footprint (mandate extraction handles the
    expansion; here we just consume the district lists).
    """
    m_names = [d.district for d in mandate.districts]
    n_names = [d.district for d in ngo.districts_covered]
    jac = district_jaccard(m_names, n_names)
    mind = min_distance_km(mandate, ngo)
    decay = math.exp(-mind / 150.0) if math.isfinite(mind) else 0.0
    return min(1.0, max(0.0, 0.60 * jac + 0.40 * decay))


def centroid(districts: list[DistrictRef]) -> tuple[float, float]:
    """Mean lat/lng. Used in justification text ('34 km from the mandate centroid')."""
    if not districts:
        return (0.0, 0.0)
    lat = sum(d.lat for d in districts) / len(districts)
    lng = sum(d.lng for d in districts) / len(districts)
    return (lat, lng)


def nearest_office_km(mandate: Mandate, ngo: NgoProfile) -> float | None:
    """Distance from the mandate centroid to the NGO's nearest district office.
    Returns None when coordinates are missing (justification falls back)."""
    if not ngo.districts_covered:
        return None
    clat, clng = centroid(mandate.districts) if mandate.districts else (None, None)
    if clat is None:
        return None
    ds = [haversine_km(clat, clng, d.lat, d.lng) for d in ngo.districts_covered]
    return min(ds)


def load_districts() -> list[DistrictRef]:
    """Load the committed district gazetteer."""
    import json
    from pathlib import Path

    path = Path(__file__).resolve().parent.parent / "artifacts" / "districts_india.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return [DistrictRef.model_validate(d) for d in data["districts"]]


def find_district(name: str, state: str | None = None) -> DistrictRef | None:
    """Case-insensitive lookup with normalisation, optional state filter."""
    target = _norm(name)
    for d in load_districts():
        if _norm(d.district) == target and (state is None or _norm(d.state) == _norm(state)):
            return d
    return None


def state_districts(state: str) -> list[DistrictRef]:
    """All districts of a state — used when a mandate names only the state."""
    st = _norm(state)
    return [d for d in load_districts() if _norm(d.state) == st]
