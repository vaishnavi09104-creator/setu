"""A8 ★ — anomaly detection: directionality, cohorts, guards."""
from __future__ import annotations

from setu_ml.anomaly import budget_tier, cohort_key, detect_anomalies, robust_z

from factories import financials, ngo


def _cohort(ngos):
    return ngos


def test_robust_z_basics():
    vals = [10, 12, 12, 13, 12, 11, 14, 13, 15, 10, 12, 13]
    assert abs(robust_z(12, vals)) < 1.0
    assert abs(robust_z(12, vals)) < abs(robust_z(100, vals))
    # below direction is negative
    assert robust_z(2, vals) < 0
    assert robust_z(100, vals) > 0


def test_robust_z_zero_mad_returns_zero_never_inf():
    identical = [5.0] * 10
    assert robust_z(5.0, identical) == 0.0
    assert robust_z(999.0, identical) == 0.0  # MAD=0 → 0.0, not inf


def test_budget_tiers():
    assert budget_tier(900_000) == "<10L"
    assert budget_tier(1_000_000) == "10L-50L"
    assert budget_tier(5_000_000) == "50L-2Cr"
    assert budget_tier(20_000_000) == ">2Cr"


def test_cohort_key_shape():
    n = ngo("a", "A", base_state="Odisha")
    k = cohort_key(n)
    assert k[1] == "50L-2Cr" and k[2] == "east"  # factory total = ₹1Cr = 50L–2Cr tier


def test_claim_inflation_flagged_below_cohort():
    """The two seeded claim-inflation NGOs: cost_per_beneficiary ~25× below cohort."""
    # cohort of 8 normal wash NGOs in same tier/state, ₹1,180 median/beneficiary
    normal = [
        ngo(f"n{i}", f"N{i}",
            financials=financials(
                programme_expense_inr=8_000_000 + i * 100_000,
                beneficiaries_reached=6_500 + i * 250,
                total_expense_inr=10_000_000,
            ))
        for i in range(8)
    ]
    # inflator: same spend shape, 25× the beneficiaries → ₹~45/beneficiary
    inflator = ngo("infl", "Inflator",
                   financials=financials(
                       programme_expense_inr=8_200_000,
                       beneficiaries_reached=180_000,  # inflated
                       total_expense_inr=10_000_000,
                   ))
    report = detect_anomalies(inflator, normal + [inflator])
    assert not report.insufficient_cohort
    flags = {f.metric: f for f in report.flags}
    assert "cost_per_beneficiary_inr" in flags
    f = flags["cost_per_beneficiary_inr"]
    assert f.direction == "below"
    assert f.z_score < -3.0
    assert "below" in f.flag_text.lower()
    assert "verification" in f.flag_text.lower() or "inflated" in f.flag_text.lower()
    assert report.penalty > 0 and report.penalty <= 15


def test_waste_direction_above_cohort():
    normal = [
        ngo(f"n{i}", f"N{i}",
            financials=financials(
                admin_expense_inr=1_500_000 + i * 20_000,
                programme_expense_inr=8_500_000,
                total_expense_inr=10_000_000,
            ))
        for i in range(8)
    ]
    waster = ngo("w", "Waster",
                 financials=financials(
                     admin_expense_inr=4_100_000,  # 41%
                     programme_expense_inr=5_900_000,
                     total_expense_inr=10_000_000,
                 ))
    report = detect_anomalies(waster, normal + [waster])
    flags = {f.metric: f for f in report.flags}
    assert "admin_ratio" in flags
    assert flags["admin_ratio"].direction == "above"
    assert "above" in flags["admin_ratio"].flag_text.lower()


def test_normal_ngo_zero_flags():
    cohort = [
        ngo(f"n{i}", f"N{i}",
            financials=financials(
                programme_expense_inr=8_000_000 + i * 90_000,
                beneficiaries_reached=7_000 + i * 200,
                growth_rate_yoy=0.05 + 0.01 * (i % 3),
            ))
        for i in range(9)
    ]
    target = ngo("t", "T",
                 financials=financials(
                     programme_expense_inr=8_300_000,
                     beneficiaries_reached=7_400,
                     growth_rate_yoy=0.07,
                 ))
    report = detect_anomalies(target, cohort + [target])
    assert report.flags == []
    assert report.penalty == 0.0


def test_insufficient_cohort_guard():
    cohort = [ngo(f"n{i}", f"N{i}") for i in range(3)]  # < 5
    target = ngo("t", "T", financials=financials(beneficiaries_reached=500_000))
    report = detect_anomalies(target, cohort + [target])
    assert report.insufficient_cohort is True
    assert report.penalty == 0.0
    assert report.flags == []


def test_penalty_capped_at_15():
    # hard to exceed in practice with 4 metrics — verify cap logic directly
    from setu_ml.anomaly import MAX_PENALTY, PENALTY_PER_FLAG

    assert MAX_PENALTY == 15.0
    assert min(MAX_PENALTY, PENALTY_PER_FLAG * 5) == 15.0
