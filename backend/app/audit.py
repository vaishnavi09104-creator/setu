"""app.audit — hash-chained append-only audit log.

Fifteen lines of real code that sound extremely serious and ARE genuinely
correct for a compliance product: every entry's hash covers the previous
entry's hash AND the payload's own hash, so tampering with any historical
row breaks the chain at that point.
"""
from __future__ import annotations

import hashlib
import json

from . import db

GENESIS = "0" * 64


def _payload_hash(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload or {}, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def _hash(prev: str, actor: str, action: str, entity_id: str,
          payload_hash: str, at: str) -> str:
    material = f"{prev}{actor}{action}{entity_id}{at}{payload_hash}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def append(actor_role: str, action: str, entity_id: str, payload: dict) -> dict:
    at = db.utcnow()
    ph = _payload_hash(payload)
    with db.tx() as conn:
        row = conn.execute("SELECT this_hash FROM audit_log ORDER BY seq DESC LIMIT 1").fetchone()
        prev = row["this_hash"] if row else GENESIS
        this = _hash(prev, actor_role, action, entity_id, ph, at)
        cur = conn.execute(
            "INSERT INTO audit_log (actor_role, action, entity_id, payload_hash, "
            "prev_hash, this_hash, at) VALUES (?,?,?,?,?,?,?)",
            (actor_role, action, entity_id, ph, prev, this, at),
        )
        seq = cur.lastrowid
    return {"seq": seq, "actor_role": actor_role, "action": action,
            "entity_id": entity_id, "this_hash": this, "at": at}


def entries(entity_id: str | None = None) -> list[dict]:
    if entity_id:
        rows = db.list_rows("audit_log", "entity_id=?", (entity_id,), order="seq")
    else:
        rows = db.list_rows("audit_log", order="seq")
    for r in rows:
        r.pop("payload_hash", None)
    return rows


def verify_chain() -> dict:
    """Walk the chain; a tampered row makes verification fail AT that row."""
    rows = db.list_rows("audit_log", order="seq")
    prev = GENESIS
    for r in rows:
        expected = _hash(prev, r["actor_role"], r["action"], r["entity_id"],
                          r["payload_hash"], r["at"])
        if r["prev_hash"] != prev or r["this_hash"] != expected:
            return {
                "valid": False,
                "entries_checked": len(rows),
                "broken_at": r.get("seq"),
                "reason": "hash mismatch — chain tampered",
            }
        prev = r["this_hash"]
    return {"valid": True, "entries_checked": len(rows), "broken_at": None}
