"""setu_ml.justify — three grounded bullets, never a template (Task A, item A5).

Each bullet must contain at least one specific number or place name from that
NGO's record. Generic sentences are worse than none; a judge reading three
identical justifications concludes the whole thing is cosmetic.
"""
from __future__ import annotations

import math

from .geo import district_jaccard, nearest_office_km, _norm
from .lexicon import DOMAIN_KEYWORDS
from .types import Domain, Mandate, NgoProfile


def format_inr(paise_free_rupees: float | int) -> str:
    """₹42.0L / ₹1.2Cr / ₹8,500. Indian conventions, used everywhere."""
    v = float(paise_free_rupees)
    if v >= 10_000_000:
        return f"₹{v/10_000_000:.1f}Cr"
    if v >= 100_000:
        return f"₹{v/100_000:.1f}L"
    return f"₹{int(round(v)):,}"


def _distinctive_phrase(ngo: NgoProfile, mandate_domains: list[Domain]) -> str:
    """Pull the most distinctive content phrase out of the proposal text:
    prefer a sentence containing a mandate-domain keyword that is NOT the
    generic domain word itself."""
    best = ""
    best_score = -1.0
    sentences = [s.strip(" .;") for s in ngo.proposal_text.split(".") if len(s.strip()) > 15]
    for s in sentences:
        sl = s.lower()
        score = 0.0
        for dom in mandate_domains:
            for kw in DOMAIN_KEYWORDS.get(dom, []):
                if kw in sl and len(kw) > 6:
                    score += 2.0
                elif kw in sl:
                    score += 0.5
        # slight preference for shorter, punchier sentences
        score -= max(0.0, (len(s) - 140) / 100.0)
        if score > best_score:
            best_score = score
            best = s
    if not best and sentences:
        best = sentences[0]
    if len(best) > 130:
        best = best[:127].rstrip() + "…"
    return best


def domain_synergy(mandate: Mandate, ngo: NgoProfile) -> str:
    """Name overlapping domains AND quote a distinctive phrase from proposal_text."""
    m_domains = set(mandate.domains)
    n_domains = {ngo.primary_domain, *ngo.secondary_domains}
    overlap = m_domains & n_domains
    overlap_names = ", ".join(d.value.replace("_", " ") for d in sorted(overlap, key=lambda x: x.value)) or "adjacent capability"
    phrase = _distinctive_phrase(ngo, mandate.domains)
    mand_names = ", ".join(d.value.replace("_", " ") for d in mandate.domains[:2]) or "the mandate"
    return (
        f"Mandate pillar{'s' if len(mandate.domains) != 1 else ''} [{mand_names}] align with this "
        f"organisation's documented work on {phrase}."
        if overlap
        else f"No direct pillar overlap, but adjacent capability: documented work on {phrase}."
    )


def scale_fit(mandate: Mandate, ngo: NgoProfile) -> str:
    """State the request as amount AND % of mandate; compare against
    max_grant_managed_inr. Surface it plainly when the request exceeds 1.5×
    the historical maximum — a genuine risk signal."""
    req = ngo.budget_request_inr
    mgm = ngo.financials.max_grant_managed_inr
    if mandate.budget_inr > 0:
        pct = req / mandate.budget_inr
        pct_txt = f" ({pct:.0%} of a {format_inr(mandate.budget_inr)} mandate)"
    else:
        pct_txt = ""
    base = (
        f"Requests {format_inr(req)}{pct_txt}; largest grant previously managed was "
        f"{format_inr(mgm)}"
    )
    if mgm and req > 1.5 * mgm:
        base += (
            " — this exceeds 1.5× demonstrated absorptive capacity, a genuine "
            "delivery risk that should be probed in diligence"
        )
    elif mgm:
        base += ", so this is within demonstrated absorptive capacity"
    return base + "."


def geographic_overlap(mandate: Mandate, ngo: NgoProfile) -> str:
    """Count overlapping districts, mention Aspirational Districts, give the
    real distance from the mandate centroid."""
    m_norm = {_norm(d.district) for d in mandate.districts}
    n_norm = {_norm(d.district) for d in ngo.districts_covered}
    inter = m_norm & n_norm
    n_asp = sum(
        1
        for d in ngo.districts_covered
        if _norm(d.district) in m_norm and d.is_aspirational
    )
    parts: list[str] = []
    if mandate.districts:
        parts.append(
            f"Covers {len(inter)} of {len(m_norm)} target district"
            f"{'s' if len(m_norm) != 1 else ''}"
            + (f" ({', '.join(sorted(inter))})" if inter else "")
        )
        if n_asp:
            parts.append(
                f"{n_asp} NITI Aayog Aspirational District{'s' if n_asp != 1 else ''}"
            )
        near = nearest_office_km(mandate, ngo)
        if near is not None:
            if math.isfinite(near) and near < 1:
                parts.append("field office inside the target area")
            else:
                parts.append(f"nearest field presence {near:.0f} km from the mandate centroid")
    else:
        jac = district_jaccard([], [d.district for d in ngo.districts_covered])
        parts.append(f"Operates across {len(n_norm)} districts from base {ngo.base_district}, {ngo.base_state}")
    return ", ".join(parts) + "."
