"""setu_ml.anomaly — cohort-relative robust fraud statistics (A8 ★). §5.4.

Global outlier detection is WRONG for this problem: a large urban NGO and a
rural micro-NGO have legitimately different cost structures. Bucket first,
compare within cohort, using robust statistics (median/MAD — a fraudster's
own value drags the mean, so never mean/σ).

The interesting direction is BELOW-cohort cost-per-beneficiary: implausibly
cheap outcomes usually mean inflated beneficiary counts — claim inflation.
"""
from __future__ import annotations

import logging
from typing import Literal

from .types import AnomalyFlag, AnomalyReport, NgoProfile

logger = logging.getLogger("setu_ml.anomaly")

MIN_COHORT = 5
Z_THRESHOLD = 3.0
MAX_PENALTY = 15.0
PENALTY_PER_FLAG = 5.0

# Coarse region buckets — a proxy for cost-of-operations, which is exactly
# what it is. Keep the mapping in the module.
STATE_GROUPS: dict[str, str] = {
    # north
    "delhi": "north", "haryana": "north", "himachal pradesh": "north",
    "jammu and kashmir": "north", "ladakh": "north", "punjab": "north",
    "chandigarh": "north", "rajasthan": "north", "uttarakhand": "north",
    "uttar pradesh": "north",
    # south
    "andhra pradesh": "south", "karnataka": "south", "kerala": "south",
    "tamil nadu": "south", "telangana": "south", "puducherry": "south",
    "lakshadweep": "south", "andaman and nicobar islands": "south",
    # east
    "odisha": "east", "west bengal": "east", "jharkhand": "east",
    "bihar": "east", "assam": "east", "sikkim": "east",
    # west
    "maharashtra": "west", "gujarat": "west", "goa": "west",
    "dadra and nagar haveli and daman and diu": "west",
    # central
    "madhya pradesh": "central", "chhattisgarh": "central",
    # northeast
    "arunachal pradesh": "northeast", "manipur": "northeast", "meghalaya": "northeast",
    "mizoram": "northeast", "nagaland": "northeast", "tripura": "northeast",
}
DEFAULT_GROUP = "central"


def budget_tier(total_expense_inr: int) -> Literal["<10L", "10L-50L", "50L-2Cr", ">2Cr"]:
    if total_expense_inr < 1_000_000:
        return "<10L"
    if total_expense_inr < 5_000_000:
        return "10L-50L"
    if total_expense_inr < 20_000_000:
        return "50L-2Cr"
    return ">2Cr"


def cohort_key(ngo: NgoProfile) -> tuple[str, str, str]:
    """(primary_domain, budget_tier, state_group)."""
    return (
        ngo.primary_domain.value,
        budget_tier(ngo.financials.total_expense_inr),
        STATE_GROUPS.get(ngo.base_state.strip().lower(), DEFAULT_GROUP),
    )


def _median(xs: list[float]) -> float:
    xs = sorted(xs)
    n = len(xs)
    if n == 0:
        return 0.0
    if n % 2:
        return xs[n // 2]
    return (xs[n // 2 - 1] + xs[n // 2]) / 2.0


def robust_z(x: float, values: list[float]) -> float:
    """0.6745 * (x − median) / MAD.

    MAD == 0 (all cohort values identical) returns 0.0, never inf — this
    WILL happen with synthetic data and an inf z-score propagating into a
    trust score is a demo-breaking bug that is invisible until it isn't."""
    if not values:
        return 0.0
    med = _median(values)
    mad = _median([abs(v - med) for v in values])
    if mad == 0:
        return 0.0
    return 0.6745 * (x - med) / mad


# metric definitions: (name, extractor, direction, meaning)
def _metrics_for(ngo: NgoProfile) -> dict[str, float | None]:
    f = ngo.financials
    out: dict[str, float | None] = {
        "admin_ratio": f.admin_ratio,
        "cost_per_beneficiary_inr": f.cost_per_beneficiary_inr,
    }
    if f.staff_count and f.staff_count > 0:
        out["beneficiaries_per_staff"] = f.beneficiaries_reached / f.staff_count
    else:
        out["beneficiaries_per_staff"] = None
    out["growth_rate_yoy"] = f.growth_rate_yoy
    return out


_FLAG_TEXTS = {
    "admin_ratio": {
        "above": (
            "Administrative overhead is {sigma:.1f}σ above comparable organisations "
            "({value:.0%} vs cohort median {median:.0%})."
        ),
        "below": (
            "Administrative overhead is {sigma:.1f}σ below the cohort median "
            "({value:.0%} vs {median:.0%}) — unusually lean; worth a look but not a fraud signal."
        ),
    },
    "cost_per_beneficiary_inr": {
        "below": (
            "Reports ₹{value:,.0f} per beneficiary against a cohort median of "
            "₹{median:,.0f} — {sigma:.1f}σ BELOW peers. Implausibly cheap outcomes "
            "usually mean inflated beneficiary counts; requires verification."
        ),
        "above": (
            "Reports ₹{value:,.0f} per beneficiary against a cohort median of "
            "₹{median:,.0f} — {sigma:.1f}σ above peers."
        ),
    },
    "beneficiaries_per_staff": {
        "above": (
            "Claims {value:,.0f} beneficiaries per staff member, {sigma:.1f}σ "
            "above peers ({median:,.0f}) — operationally implausible reach for the headcount."
        ),
        "below": None,
    },
    "growth_rate_yoy": {
        "above": (
            "Expenditure grew {value:.0%} year-on-year, {sigma:.1f}σ above peers "
            "— sudden unexplained scale-up."
        ),
        "below": None,
    },
}


def detect_anomalies(ngo: NgoProfile, all_ngos: list[NgoProfile]) -> AnomalyReport:
    """Cohort must have ≥ 5 members, else insufficient_cohort with penalty 0 —
    never penalise on thin data. Flag |z| > 3.0. penalty = min(15, 5·n_flags)."""
    key = cohort_key(ngo)
    cohort = [n for n in all_ngos if cohort_key(n) == key]

    if len(cohort) < MIN_COHORT:
        return AnomalyReport(
            ngo_id=ngo.ngo_id,
            cohort_key=key,
            cohort_size=len(cohort),
            insufficient_cohort=True,
            penalty=0.0,
            flags=[],
        )

    my = _metrics_for(ngo)
    flags: list[AnomalyFlag] = []
    for metric, my_val in my.items():
        if my_val is None:
            continue
        cohort_vals = []
        for n in cohort:
            v = _metrics_for(n).get(metric)
            if v is not None:
                cohort_vals.append(float(v))
        if len(cohort_vals) < MIN_COHORT:
            continue
        z = robust_z(float(my_val), cohort_vals)
        if abs(z) <= Z_THRESHOLD:
            continue
        direction: Literal["above", "below"] = "above" if z > 0 else "below"
        texts = _FLAG_TEXTS.get(metric, {})
        tmpl = texts.get(direction)
        if tmpl is None:
            # only the interesting direction is flagged for this metric
            continue
        med = _median(cohort_vals)
        flag_text = tmpl.format(
            sigma=abs(z), value=my_val, median=med,
        )
        flags.append(
            AnomalyFlag(
                metric=metric,
                direction=direction,
                z_score=round(z, 2),
                value=round(float(my_val), 2),
                cohort_median=round(med, 2),
                cohort_size=len(cohort_vals),
                flag_text=flag_text,
            )
        )

    penalty = min(MAX_PENALTY, PENALTY_PER_FLAG * len(flags))
    return AnomalyReport(
        ngo_id=ngo.ngo_id,
        cohort_key=key,
        cohort_size=len(cohort),
        insufficient_cohort=False,
        penalty=penalty,
        flags=flags,
    )
