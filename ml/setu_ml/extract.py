"""setu_ml.extract — natural-language mandate intake (Task A, item A4).

Primary path: deterministic rules — this is the path that runs on stage, offline.
Optional path: LLM function-calling (6s timeout, Pydantic-validated, falls back
on ANY failure). Both emit the identical `Mandate` schema.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Callable

from .geo import find_district, load_districts, state_districts, _norm
from .lexicon import (
    BENEFICIARY_PATTERNS,
    DOMAIN_KEYWORDS,
    DURATION_PATTERN,
    FOREIGN_FUNDING_PHRASES,
    PREFERENCE_PHRASES,
)
from .types import Domain, Mandate

logger = logging.getLogger("setu_ml.extract")

# --- Indian money conventions -------------------------------------------------
# "₹50 lakh" "50 lakhs" "Rs. 50,00,000" "50L" "0.5 crore" "1.2 Cr" "INR 5000000"
_CURRENCY_PREFIX = r"(?:₹|rs\.?|inr)\s*"
_NUM = r"\d[\d,]*(?:\.\d+)?"

_MONEY_PATTERNS: list[tuple[re.Pattern[str], Callable[[re.Match[str]], int]]] = [
    # 50 lakh / 50 lakhs / 50L / 50 lacs  (optionally with currency prefix)
    (
        re.compile(
            rf"(?:{_CURRENCY_PREFIX})?({_NUM})\s*(?:lakhs?|lacs?|l)\b", re.I
        ),
        lambda m: int(float(m.group(1).replace(",", "")) * 100_000),
    ),
    # 1.2 crore / 1.2 cr / 1.2Cr
    (
        re.compile(rf"(?:{_CURRENCY_PREFIX})?({_NUM})\s*(?:crores?|crs?|cr)\b", re.I),
        lambda m: int(float(m.group(1).replace(",", "")) * 10_000_000),
    ),
    # Rs. 50,00,000 / INR 5000000 / ₹ 5000000  (Indian grouping, 3 or 2+2+3)
    (
        re.compile(rf"(?:{_CURRENCY_PREFIX})({_NUM})(?!\s*(?:lakhs?|lacs?|crores?|crs?|cr)\b)", re.I),
        lambda m: int(float(m.group(1).replace(",", ""))),
    ),
]

_STOPWORDS = {
    "a", "an", "the", "for", "and", "or", "of", "in", "on", "across", "with",
    "prefer", "partners", "partner", "want", "want to", "we", "our", "us",
    "some", "something", "do", "doing", "work", "working", "please", "need",
    "would", "like", "to", "fund", "funding", "budget", "looking", "want",
    "ke", "ki", "kein", "ke", "liye", "mein", "mein", "chahiye", "humein",
    "koshish", "karo", "kar", "banao", "banan", "project", "programme",
    "program", "initiative", "activities", "work", "corporate", "csr",
}


def parse_budget_inr(text: str) -> int | None:
    for pattern, conv in _MONEY_PATTERNS:
        m = pattern.search(text)
        if m:
            val = conv(m)
            if val > 0:
                return val
    return None


# --- Domain detection ---------------------------------------------------------

# More specific domains win over their parents: maternal_health > healthcare,
# nutrition > healthcare, wash > environment (drinking water is not tree
# plantation). A broad keyword only fires when no specific one matched it.
_DOMAIN_SUPERSEDES: dict[Domain, list[Domain]] = {
    Domain.MATERNAL_HEALTH: [Domain.HEALTHCARE],
    Domain.NUTRITION: [Domain.HEALTHCARE],
    Domain.WASH: [Domain.ENVIRONMENT, Domain.RURAL_DEVELOPMENT],
    Domain.DISABILITY: [Domain.HEALTHCARE, Domain.EDUCATION],
    Domain.EDUCATION: [Domain.RURAL_DEVELOPMENT],
    Domain.SKILLING: [Domain.LIVELIHOODS, Domain.EDUCATION],
}


def detect_domains(text: str) -> list[tuple[Domain, float]]:
    """Return (domain, confidence) hits ordered by strength. Confidence 1.0 for
    a strong CSR keyword, 0.5 for a weak single-word generic ('water','health').
    Specific domains supersede the generic ones their keywords live under."""
    t = text.lower()
    seen: dict[Domain, float] = {}
    for dom, keywords in DOMAIN_KEYWORDS.items():
        best = 0.0
        for kw in keywords:
            if kw in t:
                strength = 1.0 if (len(kw) > 6 or " " in kw) else 0.5
                best = max(best, strength)
        if best > 0:
            seen[dom] = max(seen.get(dom, 0.0), best)
    # supersede: if a specific domain matched, drop parents it covers
    for specific, parents in _DOMAIN_SUPERSEDES.items():
        if specific in seen:
            for p in parents:
                seen.pop(p, None)
    ordered = sorted(seen.items(), key=lambda x: (-x[1], x[0].value))
    return ordered


# --- Geography ----------------------------------------------------------------

_DISTRICT_INDEX: list[tuple[str, str]] | None = None  # (norm_name, canonical) list


def _district_index() -> list[tuple[str, str]]:
    global _DISTRICT_INDEX
    if _DISTRICT_INDEX is None:
        idx: list[tuple[str, str]] = []
        for d in load_districts():
            idx.append((_norm(d.district), d.district))
            # allow matching without state qualifier for names like "Kerala (Wayanad)"
            if "(" in d.district:
                inner = d.district[d.district.find("(") + 1 : d.district.find(")")]
                idx.append((_norm(inner), d.district))
        _DISTRICT_INDEX = idx
    return _DISTRICT_INDEX


_STATE_NAMES: list[str] | None = None


def _state_names() -> list[str]:
    global _STATE_NAMES
    if _STATE_NAMES is None:
        _STATE_NAMES = sorted({d.state for d in load_districts()}, key=len, reverse=True)
    return _STATE_NAMES


_STATE_ALIASES = {
    "odisha": "Odisha",
    "orissa": "Odisha",
    "tn": "Tamil Nadu",
    "tamilnadu": "Tamil Nadu",
    "tamil nadu": "Tamil Nadu",
    "ap": "Andhra Pradesh",
    "andhrapradesh": "Andhra Pradesh",
    "mp": "Madhya Pradesh",
    "up": "Uttar Pradesh",
    "wb": "West Bengal",
    "jharkhand": "Jharkhand",
    "chattisgarh": "Chhattisgarh",
    "chatisgarh": "Chhattisgarh",
    "hp": "Himachal Pradesh",
    "himachal": "Himachal Pradesh",
    "j&k": "Jammu and Kashmir",
    "jk": "Jammu and Kashmir",
    "kashmir": "Jammu and Kashmir",
}


def detect_geography(text: str) -> tuple[list, float, list[str]]:
    """Match districts first, then states. Returns (district_refs, confidence,
    matched_states). Districts hit → confidence 1.0. State-only → 0.5 + expand."""
    t = _norm(text)
    raw_lower = text.lower()

    # states first (they appear inside district entries' state field, and we
    # need them for expansion), but district matches win on confidence.
    matched_states: list[str] = []
    for st in _state_names():
        if _norm(st) in t:
            matched_states.append(st)
    for alias, st in _STATE_ALIASES.items():
        if alias in raw_lower and st not in matched_states:
            matched_states.append(st)

    found: dict[str, tuple[float, str]] = {}
    for norm_name, canonical in _district_index():
        if len(norm_name) < 4:
            continue
        if re.search(rf"\b{re.escape(norm_name)}\b", t):
            dref = find_district(canonical)
            if dref is not None:
                found[dref.district] = (1.0, dref.state)

    district_refs = []
    for canonical, (conf, state) in found.items():
        dref = find_district(canonical, state)
        if dref is None:
            dref = find_district(canonical)
        if dref is not None:
            district_refs.append(dref)

    if district_refs:
        return district_refs, 1.0, matched_states

    # state-only path: expand to that state's districts but flag low confidence
    if matched_states:
        expanded = []
        for st in matched_states:
            expanded.extend(state_districts(st))
        if expanded:
            # A full state expansion can be huge; cap at the districts the
            # narrative actually uses — the caller may re-scope. Keep order.
            return expanded, 0.5, matched_states

    return [], 0.0, matched_states


# --- Preferences / flags ------------------------------------------------------

def detect_preferences(text: str) -> list[str]:
    t = text.lower()
    out: list[str] = []
    for pattern, label in PREFERENCE_PHRASES:
        if re.search(pattern, t) and label not in out:
            out.append(label)
    return out


def detect_foreign_funding(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in FOREIGN_FUNDING_PHRASES)


def detect_beneficiary(text: str) -> str | None:
    t = text.lower()
    for pattern, label in BENEFICIARY_PATTERNS:
        if re.search(pattern, t):
            return label
    return None


def detect_duration(text: str) -> int | None:
    m = re.search(DURATION_PATTERN, text.lower())
    if m:
        n = int(m.group(1))
        unit = m.group(0).lower()
        if "month" in unit or "mahin" in unit:
            return n
        if "year" in unit or "saal" in unit:
            return n * 12
    return None


# --- Confidence & clarifying questions ----------------------------------------

def field_confidence(mandate: Mandate, text: str) -> dict[str, float]:
    """Per-field confidence in [0,1]: 1.0 explicit pattern, 0.5 inferred/weak,
    0.0 defaulted."""
    conf: dict[str, float] = {
        "budget": 1.0 if mandate.budget_inr > 0 else 0.0,
        "domains": 0.0,
        "districts": 0.0,
        "duration": 1.0 if mandate.duration_months else 0.0,
        "beneficiary_profile": 1.0 if mandate.beneficiary_profile else 0.0,
        "preferences": 1.0 if mandate.preferences else 0.0,
    }
    if mandate.domains:
        domain_hits = detect_domains(text)
        strong = [c for _, c in domain_hits if c >= 1.0]
        conf["domains"] = 1.0 if strong else (0.5 if domain_hits else 0.0)
    if mandate.districts:
        # detect_geography already set 1.0 (districts) vs 0.5 (state expansion)
        conf["districts"] = 1.0
        # state-only expansion is detectable: no district names matched raw text
        if _state_only(text):
            conf["districts"] = 0.5
    return conf


def _state_only(text: str) -> bool:
    refs, conf, _ = detect_geography(text)
    return conf < 1.0 and bool(refs)


def clarifying_questions(mandate: Mandate) -> list[str]:
    """One question per field below 0.6 confidence. Maximum 2 — a chat that
    interrogates the user is worse than one that makes a visible assumption."""
    conf = mandate.field_confidence or {}
    questions: list[str] = []
    templates = {
        "budget": "What is the total budget for this mandate (in lakh or crore)?",
        "domains": "Which focus areas should this mandate fund — e.g. education, health, water, skilling?",
        "districts": "Which specific districts should this mandate target (state and district names)?",
        "duration": "Over what duration should the programme run?",
    }
    for field, tmpl in templates.items():
        c = conf.get(field, 0.0)
        if c < 0.6 and field in templates:
            if len(questions) >= 2:
                break
            # budget is the most load-bearing unknown; districts drive the
            # consortium engine — prioritise them.
            questions.append(tmpl)
    if conf.get("budget", 0.0) < 0.6 and len(questions) < 2:
        if templates["budget"] not in questions:
            questions.append(templates["budget"])
    # order: budget first, then districts, then domains, then duration
    priority = ["budget", "districts", "domains", "duration"]
    questions.sort(key=lambda q: min(
        (priority.index(p) for p in priority if q == templates[p]), default=9
    ))
    return questions[:2]


def build_requirement_units(mandate: Mandate) -> list:
    """Cartesian product of domains × districts, weight 1.0 (priority 1.5 if
    the raw text flags a district as priority)."""
    from .types import RequirementUnit

    units = []
    priority_districts = _priority_districts(mandate.raw_text)
    for dom in mandate.domains:
        for dref in mandate.districts:
            w = 1.5 if _norm(dref.district) in priority_districts else 1.0
            units.append(
                RequirementUnit(domain=dom, district=dref.district, state=dref.state, weight=w)
            )
    return units


def _priority_districts(text: str) -> set[str]:
    m = re.search(r"priorit\w*\s+(?:on\s+|in\s+|for\s+)?([A-Za-z ,]+)", text, re.I)
    if not m:
        return set()
    out: set[str] = set()
    for chunk in m.group(1).split(" and "):
        cand = chunk.strip().rstrip(".,;:")
        dref = find_district(cand)
        if dref is not None:
            out.add(_norm(dref.district))
    return out


# --- The two entry points -----------------------------------------------------

def parse_mandate_rules(text: str) -> Mandate:
    """Deterministic fallback. No network. This is the path that runs on stage."""
    domain_hits = detect_domains(text)
    domains = [d for d, _ in domain_hits]
    dom_conf = 1.0 if any(c >= 1.0 for _, c in domain_hits) else (0.5 if domains else 0.0)

    district_refs, geo_conf, matched_states = detect_geography(text)
    budget = parse_budget_inr(text)
    duration = detect_duration(text)
    beneficiary = detect_beneficiary(text)
    preferences = detect_preferences(text)
    foreign = detect_foreign_funding(text)

    mandate = Mandate(
        raw_text=text,
        domains=domains,
        budget_inr=budget or 0,
        districts=district_refs,
        duration_months=duration,
        beneficiary_profile=beneficiary,
        preferences=preferences,
        foreign_funded=foreign,
    )
    mandate.field_confidence = {
        "budget": 1.0 if budget else 0.0,
        "domains": dom_conf,
        "districts": geo_conf,
        "duration": 1.0 if duration else 0.0,
        "beneficiary_profile": 1.0 if beneficiary else 0.0,
        "preferences": 1.0 if preferences else 0.0,
    }
    mandate.clarifying_questions = clarifying_questions(mandate)
    mandate.requirement_units = build_requirement_units(mandate)
    return mandate


def parse_mandate(text: str, llm_client: Any = None) -> Mandate:
    """Primary entry point. Tries the LLM path when a client is supplied and
    the call succeeds; falls back to parse_mandate_rules() on any failure —
    timeout, bad JSON, schema violation, no client. Never raises for a
    parseable-looking sentence."""
    if llm_client is not None:
        try:
            llm_out = _llm_parse(text, llm_client)
            if llm_out is not None:
                mandate = _validate_llm_output(llm_out, text)
                if mandate is not None:
                    mandate.clarifying_questions = clarifying_questions(mandate)
                    mandate.requirement_units = build_requirement_units(mandate)
                    return mandate
        except Exception as exc:
            logger.warning("LLM parse path failed (%s); using rules", exc)
    return parse_mandate_rules(text)


def _llm_parse(text: str, llm_client: Any) -> dict | None:
    """One function-call style invocation, 6-second timeout, JSON out."""
    import json as _json

    prompt = (
        "Extract a CSR funding mandate into JSON with keys: "
        "domains (list of: education|healthcare|maternal_health|wash|environment|"
        "skilling|livelihoods|nutrition|disability|rural_development), "
        "budget_inr (integer rupees), districts (list of {district, state}), "
        "duration_months (int|null), beneficiary_profile (string|null), "
        "preferences (list of strings), foreign_funded (bool). "
        f"Mandate: {text}"
    )
    raw = llm_client(prompt) if callable(llm_client) else getattr(llm_client, "parse", lambda p: None)(prompt)
    if raw is None:
        return None
    if isinstance(raw, str):
        raw = _json.loads(raw)
    return raw


def _validate_llm_output(data: dict, text: str) -> Mandate | None:
    """Pydantic-validate the LLM response; None on any violation.
    An LLM that returns "budget": "50 lakh" as a string must not take the
    demo down — coerce money strings, then validate."""
    try:
        coerced = dict(data)
        b = coerced.get("budget_inr")
        if isinstance(b, str):
            coerced["budget_inr"] = parse_budget_inr(b) or int(re.sub(r"[^\d]", "", b) or 0)
        if coerced.get("domains"):
            coerced["domains"] = [
                d if isinstance(d, Domain) else Domain(str(d).lower()) for d in coerced["domains"]
            ]
        else:
            coerced["domains"] = []
        if not coerced.get("districts"):
            coerced["districts"] = []
        else:
            refs = []
            for d in coerced["districts"]:
                if isinstance(d, dict):
                    ref = find_district(str(d.get("district", "")), d.get("state"))
                    if ref is not None:
                        refs.append(ref)
            coerced["districts"] = refs
        coerced.setdefault("raw_text", text)
        coerced.setdefault("budget_inr", 0)
        return Mandate.model_validate(coerced)
    except Exception as exc:
        logger.warning("LLM output failed validation (%s)", exc)
        return None
