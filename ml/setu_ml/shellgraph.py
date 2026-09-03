"""setu_ml.shellgraph — connected-components shell-network detection (reference).

The OWNERSHIP of the shell-network endpoint is Task B (04-TASK-B-BACKEND-TRUST.md
B8). This module ships the *pure graph algorithm* + identifier normalisation
in the ML library so that:
  - it is unit-testable without any database or HTTP,
  - the backend can `from setu_ml.shellgraph import build_components` and stay
    thin, exactly like compute_trust.
Task B remains free to re-implement; if she does, this file costs nothing.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .types import ShellEdge, ShellNetworkComponent

GENERIC_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "yahoo.in", "outlook.com", "hotmail.com",
    "rediffmail.com", "protonmail.com",
}

_ADDR_NOISE = {
    "plot", "no", "near", "opp", "behind", "road", "street", "lane", "nagar",
    "colony", "village", "post", "ps", "dist", "tehsil", "block", "house",
    "flat", "floor", "wing", "building", "bldg", "the", "and", "at",
}

_PIN_RE = re.compile(r"\b(\d{6})\b")
_HONORIFIC_RE = re.compile(r"^(shri|smt|shrimati|dr|mr|mrs|ms|md|late)\.?\s+", re.I)
_PUNCT_RE = re.compile(r"[^\w\s]")
_PHONE_RE = re.compile(r"\d")


@dataclass
class NgoIdentifiers:
    """Normalised identifier set for one NGO — input to the graph builder."""

    ngo_id: str
    name: str = ""
    address_fingerprint: str | None = None
    phone_e164: str | None = None
    trustee_names: list[str] = field(default_factory=list)
    bank_ifsc: str | None = None
    bank_account_last4: str | None = None
    email_domain: str | None = None  # None when generic (gmail etc.)


def normalise_address(raw: str) -> str | None:
    """Lowercase, strip punctuation + noise words, anchor on the 6-digit PIN.
    Over-normalising creates false rings; under-normalising misses real ones."""
    if not raw:
        return None
    s = raw.lower()
    pin = _PIN_RE.search(s)
    s = _PUNCT_RE.sub(" ", s)
    toks = [t for t in s.split() if t not in _ADDR_NOISE and not t.isdigit()]
    if not toks:
        return pin.group(1) if pin else None
    fp = " ".join(toks[:6])  # first 6 meaningful tokens
    if pin:
        fp = f"{fp}|pin{pin.group(1)}"
    return fp or None


def normalise_phone(raw: str) -> str | None:
    """Digits only, strip +91 / leading 0, keep the last 10."""
    if not raw:
        return None
    digits = _PHONE_RE.findall(raw)
    d = "".join(digits)
    if len(d) < 10:
        return None
    return d[-10:]


def normalise_name(raw: str) -> str:
    """Lowercase, strip honorifics (repeatedly — 'Dr. Smt.' stacks), collapse whitespace."""
    if not raw:
        return ""
    s = raw.strip().lower()
    while True:
        new = _HONORIFIC_RE.sub("", s, count=1).strip()
        if new == s:
            break
        s = new
    s = _PUNCT_RE.sub(" ", s)
    return " ".join(s.split())


def _email_domain(raw: str | None) -> str | None:
    if not raw or "@" not in raw:
        return None
    dom = raw.split("@")[-1].strip().lower()
    return None if dom in GENERIC_EMAIL_DOMAINS else dom


def identifiers_from_fields(
    ngo_id: str,
    name: str,
    address: str | None,
    phone: str | None,
    trustees: list[str],
    bank_ifsc: str | None,
    bank_account_last4: str | None,
    email: str | None,
) -> NgoIdentifiers:
    return NgoIdentifiers(
        ngo_id=ngo_id,
        name=name,
        address_fingerprint=normalise_address(address),
        phone_e164=normalise_phone(phone),
        trustee_names=[normalise_name(t) for t in trustees if normalise_name(t)],
        bank_ifsc=(bank_ifsc or "").upper() or None,
        bank_account_last4=(bank_account_last4 or "").strip()[-4:] or None,
        email_domain=_email_domain(email),
    )


# --- graph + components --------------------------------------------------------

EDGE_TYPES = [
    "address_fingerprint",
    "phone_e164",
    "trustee_name",
    "bank_fingerprint",
    "email_domain",
]


def _bank_fp(i: NgoIdentifiers) -> str | None:
    if i.bank_ifsc and i.bank_account_last4:
        return f"{i.bank_ifsc}:{i.bank_account_last4}"
    return None


def _shared_types(a: NgoIdentifiers, b: NgoIdentifiers) -> list[str]:
    shared: list[str] = []
    if a.address_fingerprint and a.address_fingerprint == b.address_fingerprint:
        shared.append("address_fingerprint")
    if a.phone_e164 and a.phone_e164 == b.phone_e164:
        shared.append("phone_e164")
    if set(a.trustee_names) & set(b.trustee_names):
        shared.append("trustee_name")
    ba, bb = _bank_fp(a), _bank_fp(b)
    if ba and ba == bb:
        shared.append("bank_fingerprint")
    if a.email_domain and a.email_domain == b.email_domain:
        shared.append("email_domain")
    return shared


def build_components(ngos: list[NgoIdentifiers],
                     min_members: int = 2,
                     min_shared_types: int = 2) -> list[ShellNetworkComponent]:
    """Undirected graph over shared normalised identifiers; connected components
    flagged when ≥ min_members AND ≥ min_shared_types distinct identifier types
    shared across the component. One shared landline is a coincidence; a shared
    address AND trustee AND bank account is a pattern (§5.5).

    Note: the two-identifier rule is evaluated over the UNION of identifier
    types shared inside the component — how financial-crime teams read rings."""
    n = len(ngos)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[ry] = rx

    edges: list[ShellEdge] = []
    for i in range(n):
        for j in range(i + 1, n):
            shared = _shared_types(ngos[i], ngos[j])
            if shared:
                union(i, j)
                edges.append(ShellEdge(source=ngos[i].ngo_id, target=ngos[j].ngo_id,
                                       shared_types=shared))

    comps: dict[int, list[int]] = {}
    for i in range(n):
        comps.setdefault(find(i), []).append(i)

    out: list[ShellNetworkComponent] = []
    cid = 1
    for members_idx in comps.values():
        if len(members_idx) < min_members:
            continue
        # union of shared types across all intra-component edges
        type_union: set[str] = set()
        member_set = {ngos[i].ngo_id for i in members_idx}
        comp_edges = [e for e in edges
                      if e.source in member_set and e.target in member_set]
        for e in comp_edges:
            type_union |= set(e.shared_types)
        flagged = len(members_idx) >= min_members and len(type_union) >= min_shared_types
        out.append(ShellNetworkComponent(
            component_id=f"shl_{cid}",
            member_ngo_ids=[ngos[i].ngo_id for i in members_idx],
            shared_identifier_types=sorted(type_union),
            edges=comp_edges,
            flagged=flagged,
        ))
        cid += 1
    return out
