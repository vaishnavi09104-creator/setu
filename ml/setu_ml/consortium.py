"""setu_ml.consortium — the weighted set-cover consortium engine (A7 ★). §5.8.

The single most differentiating thing in the project: CSR matching reframed
from "sort a list" to "solve a constrained weighted set-cover".

  Coverage(K)   = Σ weight(u) covered by ≥1 member / Σ weight(u)
  Redundancy(K) = Σ weight(u)·(members(u)−1) / Σ weight(u)·members(u)
  TrustW(K)     = Σ (budget_share_i × T_i)/100   — BUDGET-weighted, not plain mean
  CoordCost(K)  = 0.05 × (|K|−1)
  S = 0.45·Coverage + 0.30·TrustW + 0.15·(1−Redundancy) − CoordCost

Hard constraints (reject the set when any fails):
  1. |K| ≤ 3
  2. every member T_i ≥ 55 (a weak link poisons the whole consortium)
  3. every member covers ≥1 unit no one else covers (no passengers)
  4. Coverage(K) > best single coverage + 0.10 (else recommend the single NGO)

Solver: exhaustive over the top-12 shortlist, |K| ∈ {2,3} → 286 sets.
That is optimal *within the shortlist*, in milliseconds — and you can say so.
"""
from __future__ import annotations

import logging
from itertools import combinations

from .geo import _norm
from .justify import format_inr
from .scoring import rank_ngos
from .types import (
    Consortium,
    ConsortiumMember,
    Mandate,
    NgoProfile,
    RequirementUnit,
)

logger = logging.getLogger("setu_ml.consortium")

MIN_TRUST_FLOOR = 55
MAX_MEMBERS = 3
SHORTLIST = 12
COVERAGE_EPS = 0.10
ABSORPTIVE_MULTIPLIER = 1.5
MIN_ABSORPTIVE_CAP_INR = 200_000


# --- unit coverage ------------------------------------------------------------

def _unit_key(u: RequirementUnit) -> tuple[str, str]:
    return (_norm(u.district), u.domain.value)


def covered_units(ngo: NgoProfile, units: list[RequirementUnit]) -> list[RequirementUnit]:
    """A unit is covered if the NGO's domains include unit.domain AND its
    districts_covered include unit.district. BOTH conditions — an education
    NGO in the right district does not cover a WASH unit there. This
    strictness is what makes coverage gaps real and the consortium necessary."""
    dom = {ngo.primary_domain.value, *(d.value for d in ngo.secondary_domains)}
    dists = {_norm(d.district) for d in ngo.districts_covered}
    return [u for u in units if u.domain.value in dom and _norm(u.district) in dists]


def coverage(members: list[NgoProfile], units: list[RequirementUnit]) -> float:
    """Weighted fraction of units covered by at least one member."""
    if not units:
        return 0.0
    total = sum(u.weight for u in units)
    covered_w = 0.0
    covered_keys: set[tuple[str, str]] = set()
    for m in members:
        covered_keys |= {_unit_key(u) for u in covered_units(m, units)}
    for u in units:
        if _unit_key(u) in covered_keys:
            covered_w += u.weight
    return covered_w / total


def redundancy(members: list[NgoProfile], units: list[RequirementUnit]) -> float:
    """§5.8 overlap fraction. Two members covering the same unit is duplicated
    spend. In [0,1]; a disjoint set scores 0."""
    if not units:
        return 0.0
    keys = [_unit_key(u) for u in units]
    per_unit_key_counts: dict[tuple[str, str], int] = {k: 0 for k in keys}
    for m in members:
        for cu in covered_units(m, units):
            k = _unit_key(cu)
            if k in per_unit_key_counts:
                per_unit_key_counts[k] += 1
    num = 0.0
    den = 0.0
    for u, k in zip(units, keys):
        c = per_unit_key_counts[k]
        if c > 0:
            num += u.weight * (c - 1)
            den += u.weight * c
    return (num / den) if den > 0 else 0.0


def unique_units(member: NgoProfile, others: list[NgoProfile],
                 units: list[RequirementUnit]) -> int:
    """Units this member covers that NO other member covers. Zero = passenger."""
    mine = {_unit_key(u) for u in covered_units(member, units)}
    others_cov: set[tuple[str, str]] = set()
    for o in others:
        others_cov |= {_unit_key(u) for u in covered_units(o, units)}
    return len(mine - others_cov)


def absorptive_cap(ngo: NgoProfile) -> int:
    """int(1.5 × max_grant_managed_inr), floored at ₹2,00,000 so a first-time
    NGO isn't capped to nothing."""
    cap = int(ABSORPTIVE_MULTIPLIER * max(0, ngo.financials.max_grant_managed_inr))
    return max(cap, MIN_ABSORPTIVE_CAP_INR)


# --- budget split -------------------------------------------------------------

def split_budget(members: list[NgoProfile], units: list[RequirementUnit],
                 mandate_budget_inr: int) -> tuple[list[int], int, list[bool]]:
    """Proportional to covered weight, capped by absorptive_cap, residual
    redistributed to members with headroom.

    Assert sum(shares) + unallocated == mandate_budget EXACTLY in integer
    rupees — an off-by-₹1 assertion failure on stage is a bad way to find
    out you used floats for money.

    Returns (shares, unallocated, capped_flags).
    """
    if not members:
        return [], int(mandate_budget_inr), []
    covered_w = [sum(u.weight for u in covered_units(m, units)) for m in members]
    total_w = sum(covered_w)
    caps = [absorptive_cap(m) for m in members]
    shares = [0] * len(members)
    capped = [False] * len(members)
    if total_w <= 0:
        # no unit coverage at all: equal split, still capacity-capped
        raw = [mandate_budget_inr / len(members)] * len(members)
    else:
        raw = [w / total_w * mandate_budget_inr for w in covered_w]

    # initial assignment with caps
    assigned_total = 0
    for i, r in enumerate(raw):
        s = int(r)
        if s > caps[i]:
            s = caps[i]
            capped[i] = True
        shares[i] = s
        assigned_total += s

    residual = mandate_budget_inr - assigned_total
    # redistribute residual to members with headroom, iterating
    for _ in range(len(members) * 4):
        if residual <= 0:
            break
        with_room = [i for i in range(len(members)) if caps[i] - shares[i] > 0]
        if not with_room:
            break
        per = residual / len(with_room)
        moved = 0
        for i in with_room:
            add = min(int(per), caps[i] - shares[i])
            if add > 0:
                shares[i] += add
                moved += add
        residual -= moved
        if moved == 0:
            break

    # any remainder (₹1–2 rounding) goes to the largest share with headroom
    if residual > 0:
        for i in sorted(range(len(members)), key=lambda j: -shares[j]):
            room = caps[i] - shares[i]
            if room >= residual:
                shares[i] += residual
                residual = 0
                break
            elif room > 0:
                shares[i] += room
                residual -= room

    total = sum(shares) + residual
    assert total == int(mandate_budget_inr), (
        f"budget not conserved: shares {total - residual} + unallocated {residual} "
        f"!= {mandate_budget_inr}"
    )
    return shares, int(residual), capped


# --- scoring ------------------------------------------------------------------

def _trust_weighted(members: list[NgoProfile], shares: list[int]) -> float:
    den = sum(shares)
    if den <= 0:
        return sum(m.trust_score for m in members) / max(len(members), 1) / 100.0
    return sum(s * m.trust_score for s, m in zip(shares, members)) / den / 100.0


def score_consortium(members: list[NgoProfile], units: list[RequirementUnit],
                     shares: list[int]) -> float:
    """§5.8 composite for a candidate set."""
    cov = coverage(members, units)
    red = redundancy(members, units)
    tw = _trust_weighted(members, shares)
    cc = 0.05 * (len(members) - 1)
    return 0.45 * cov + 0.30 * tw + 0.15 * (1.0 - red) - cc


def is_valid(members: list[NgoProfile], units: list[RequirementUnit],
             mandate_budget_inr: int = 0,
             best_single_coverage: float = 0.0) -> tuple[bool, str]:
    """All four hard constraints from §5.8. (False, human-readable reason)."""
    if not members:
        return False, "empty set"
    if len(members) > MAX_MEMBERS:
        return False, f"more than {MAX_MEMBERS} members — a CSR team will not manage more grantees"
    for m in members:
        if m.trust_score < MIN_TRUST_FLOOR:
            return False, (
                f"member {m.name} has trust {m.trust_score} below the floor of "
                f"{MIN_TRUST_FLOOR} — a weak link poisons the whole consortium"
            )
    for i, m in enumerate(members):
        others = [o for j, o in enumerate(members) if j != i]
        if unique_units(m, others, units) == 0:
            return False, (
                f"member {m.name} is a passenger — every unit it covers is also "
                "covered by another member"
            )
    cov = coverage(members, units)
    if cov <= best_single_coverage + COVERAGE_EPS:
        return False, (
            f"coverage {cov:.0%} does not beat the best single NGO "
            f"({best_single_coverage:.0%}) by more than 10 points — recommend "
            "the single partner instead"
        )
    return True, "ok"


# --- rationale -----------------------------------------------------------------

def _uncovered_description(units: list[RequirementUnit], members: list[NgoProfile]) -> str:
    cov_keys: set[tuple[str, str]] = set()
    for m in members:
        cov_keys |= {_unit_key(u) for u in covered_units(m, units)}
    missing = [u for u in units if _unit_key(u) not in cov_keys]
    if not missing:
        return "every requirement"
    doms = sorted({u.domain.value.replace("_", " ") for u in missing})
    return f"{doms[0] if len(doms)==1 else ' and '.join(doms[:2])} in {len({u.district for u in missing})} district(s)"


def build_rationale(members: list[NgoProfile], units: list[RequirementUnit],
                    shares: list[int], capped: list[bool], cov: float, red: float,
                    best_single: float) -> str:
    base = (
        f"No single partner covers {_uncovered_description(units, members)}. "
        f"This {len(members)}-partner combination reaches {cov:.0%} coverage with "
        f"{red:.0%} overlap, against {best_single:.0%} for the best single NGO."
    )
    capped_members = [members[i].name for i in range(len(members)) if capped[i]]
    if capped_members:
        base += (
            f" {'/'.join(capped_members)} share{'' if len(capped_members)==1 else 's'} "
            "capped at absorptive capacity (1.5× the largest grant previously managed)."
        )
    return base


# --- the engine ---------------------------------------------------------------

def find_consortiums(
    mandate: Mandate,
    ngos: list[NgoProfile],
    index,
    top_n: int = 3,
    weights: dict | None = None,
) -> list[Consortium]:
    """1. Rank all NGOs individually (A5); take top 12 by final_score.
    2. Compute best single-NGO coverage — the baseline to beat.
    3. Enumerate ALL pairs and triples: C(12,2)+C(12,3) = 286 sets.
    4. Filter through is_valid(); score the survivors.
    5. Return top_n by score, with rationale text. Optimal over the shortlist.
    """
    eligible = [n for n in ngos if n.status != "INELIGIBLE"]
    units = mandate.requirement_units or mandate.build_requirement_units()
    if not units:
        return []

    results, _ = rank_ngos(mandate, eligible, index, weights=weights, top_k=SHORTLIST,
                          include_justifications=False)
    shortlist_ids = [r.ngo_id for r in results]
    by_id = {n.ngo_id: n for n in eligible}
    shortlist = [by_id[i] for i in shortlist_ids if i in by_id]
    if len(shortlist) < 2:
        return []

    best_single_cov = max((coverage([n], units) for n in shortlist), default=0.0)

    candidates: list[tuple[float, Consortium]] = []
    counter = 1
    for k in (2, 3):
        for combo in combinations(shortlist, k):
            ok, reason = is_valid(list(combo), units,
                                  mandate.budget_inr, best_single_cov)
            if not ok:
                continue
            shares, unallocated, capped = split_budget(
                list(combo), units, mandate.budget_inr
            )
            score = score_consortium(list(combo), units, shares)
            cov = coverage(list(combo), units)
            red = redundancy(list(combo), units)
            tw = _trust_weighted(list(combo), shares)

            members = []
            for i, m in enumerate(combo):
                my_units = covered_units(m, units)
                others = [o for j, o in enumerate(combo) if j != i]
                uniq = unique_units(m, others, units)
                members.append(
                    ConsortiumMember(
                        ngo_id=m.ngo_id,
                        name=m.name,
                        trust_score=m.trust_score,
                        covers=my_units,
                        unique_units=uniq,
                        budget_share_inr=shares[i],
                        share_pct=(shares[i] / mandate.budget_inr * 100) if mandate.budget_inr else 0.0,
                        absorptive_cap_inr=absorptive_cap(m),
                        capped=capped[i],
                    )
                )

            rationale = build_rationale(list(combo), units, shares, capped, cov, red,
                                       best_single_cov)
            cns = Consortium(
                consortium_id=f"cns_{counter}",
                members=members,
                coverage=cov,
                redundancy=red,
                trust_weighted=tw,
                coordination_cost=0.05 * (k - 1),
                score=score,
                beats_best_single_by=cov - best_single_cov,
                unallocated_inr=unallocated,
                rationale=rationale,
                best_single_coverage=best_single_cov,
                n_units=len(units),
            )
            candidates.append((score, cns))
            counter += 1

    candidates.sort(key=lambda x: -x[0])
    out = []
    for rank_i, (score, cns) in enumerate(candidates[:top_n], start=1):
        cns.consortium_id = f"cns_{rank_i}"
        out.append(cns)
    if not candidates:
        logger.info("no valid consortium for this mandate (best single %.0f%%)",
                    best_single_cov * 100)
    return out
