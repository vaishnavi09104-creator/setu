"""app.services.shell_network — linked-entity detection (B8 ★).

The graph algorithm + identifier normalisation live in setu_ml.shellgraph
(pure, unit-tested). This service: loads identifiers from SQLite, runs the
components, persists rings, applies penalties (trust cap 40, badge High
Risk, status FLAGGED). That division keeps the detection testable without
a database and this file thin.
"""
from __future__ import annotations

from typing import Any

from setu_ml.shellgraph import build_components, identifiers_from_fields
from setu_ml.types import TrustBadge

from .. import db
from ..config import get_settings


def _identifiers_from_row(row: dict):
    d = row["data"] if isinstance(row.get("data"), dict) else row
    idf = d.get("identifiers", {})
    return identifiers_from_fields(
        ngo_id=d["ngo_id"],
        name=d.get("name", ""),
        address=idf.get("address"),
        phone=idf.get("phone"),
        trustees=idf.get("trustees", []),
        bank_ifsc=idf.get("bank_ifsc"),
        bank_account_last4=idf.get("bank_account_last4"),
        email=idf.get("email"),
    )


def run_detection() -> list[dict[str, Any]]:
    """Scan the full seeded set, persist rings + penalties. Returns rings."""
    rows = db.list_ngos()
    idents = [_identifiers_from_row(r) for r in rows]
    components = build_components(idents)

    row_by_id = {r["ngo_id"]: r for r in rows}
    rings: list[dict[str, Any]] = []
    flagged_ids: set[str] = set()

    for comp in components:
        doc = comp.model_dump()
        db.upsert("shell_networks", {"component_id": comp.component_id}, doc)
        if comp.flagged:
            flagged_ids.update(comp.member_ngo_ids)
            rings.append(doc)

    # penalties: trust capped at 40, badge High Risk, status FLAGGED
    for ngo_id in flagged_ids:
        row = row_by_id.get(ngo_id)
        if not row:
            continue
        d = dict(row["data"])
        trust = d.setdefault("trust", {})
        current = float(trust.get("score", 40) or 40)
        trust["score"] = int(min(current, 40))
        trust["badge"] = TrustBadge.HIGH_RISK.value
        trust["shell_flagged"] = True
        d["status"] = "FLAGGED"
        db.save_ngo(d)

    return rings


def network_payload(ngo_id: str) -> dict[str, Any]:
    """/api/ngos/{id}/network response — the ring this NGO belongs to."""
    row = db.get_ngo(ngo_id)
    if row is None:
        return {
            "flagged": False, "component_id": None,
            "members": [], "shared_identifier_types": [], "edges": [],
        }
    comp = db.get_one(
        "shell_networks",
        "json_extract(data, '$.member_ngo_ids') LIKE ?",
        (f'%"{ngo_id}"%',),
    )
    if comp is None:
        return {
            "flagged": False, "component_id": None,
            "members": [], "shared_identifier_types": [], "edges": [],
        }
    data = comp["data"]
    members = []
    for mid in data.get("member_ngo_ids", []):
        mrow = db.get_ngo(mid)
        if mrow:
            mtrust = mrow["data"].get("trust", {})
            members.append({
                "ngo_id": mid,
                "name": mrow["data"].get("name", mid),
                "trust_score": int(mtrust.get("score", 0) or 0),
            })
    return {
        "flagged": bool(data.get("flagged", False)),
        "component_id": data.get("component_id"),
        "members": members,
        "shared_identifier_types": data.get("shared_identifier_types", []),
        "edges": data.get("edges", []),
    }
