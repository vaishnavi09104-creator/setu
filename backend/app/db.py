"""app.db — SQLite persistence layer (replaces MongoDB per team decision).

Pattern: SQLite as a document store — indexed scalar columns for the fields
we filter on, a `data` JSON column for the full nested document. Zero server
process, byte-portable, offline-proof: exactly what a demo laptop wants.

Concurrency: one shared connection guarded by an RLock (SQLite ops here are
sub-millisecond; FastAPI's threadpool makes a per-request connection unsafe
with WAL off, so serialise — plenty for the demo and for the benchmarks).
"""
from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .config import get_settings

_CONN: sqlite3.Connection | None = None
_LOCK = threading.RLock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS ngo_profiles (
    ngo_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    primary_domain TEXT NOT NULL,
    base_state TEXT NOT NULL,
    trust_score INTEGER NOT NULL DEFAULT 0,
    trust_badge TEXT NOT NULL DEFAULT 'Verification Incomplete',
    data TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ngo_status ON ngo_profiles(status);
CREATE INDEX IF NOT EXISTS idx_ngo_domain ON ngo_profiles(primary_domain);
CREATE INDEX IF NOT EXISTS idx_ngo_state ON ngo_profiles(base_state);
CREATE INDEX IF NOT EXISTS idx_ngo_trust ON ngo_profiles(trust_score);

CREATE TABLE IF NOT EXISTS corporates (
    corporate_id TEXT PRIMARY KEY, data TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS mandates (
    mandate_id TEXT PRIMARY KEY,
    corporate_id TEXT,
    created_at TEXT NOT NULL,
    data TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    doc_id TEXT PRIMARY KEY,
    ngo_id TEXT,
    kind TEXT NOT NULL,
    page_count INTEGER NOT NULL DEFAULT 1,
    file_path TEXT,
    extraction_confidence REAL NOT NULL DEFAULT 1.0,
    uploaded_at TEXT NOT NULL,
    extracted TEXT NOT NULL DEFAULT '{}',
    forensics TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_doc_ngo ON documents(ngo_id);

CREATE TABLE IF NOT EXISTS compliance_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ngo_id TEXT NOT NULL,
    pillar TEXT NOT NULL,
    computed_at TEXT NOT NULL,
    algorithm_version TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    data TEXT NOT NULL,
    UNIQUE (ngo_id, pillar)
);
CREATE INDEX IF NOT EXISTS idx_audit_ngo ON compliance_audit(ngo_id);

CREATE TABLE IF NOT EXISTS shell_networks (
    component_id TEXT PRIMARY KEY, data TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mandate_id TEXT NOT NULL,
    latency_ms REAL NOT NULL,
    run_at TEXT NOT NULL,
    algorithm_version TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    data TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ngo_id TEXT NOT NULL,
    mandate_id TEXT,
    predicted_impact REAL NOT NULL,
    realised_impact REAL NOT NULL,
    completed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_role TEXT NOT NULL,
    action TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    this_hash TEXT NOT NULL,
    at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS review_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    corporate_id TEXT NOT NULL,
    author TEXT NOT NULL,
    ngo_id TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS counterfactuals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ngo_id TEXT NOT NULL,
    algorithm_version TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    data TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rfps (
    rfp_id TEXT PRIMARY KEY,
    mandate_id TEXT,
    ngo_ids TEXT NOT NULL,
    message TEXT,
    status TEXT NOT NULL DEFAULT 'sent',
    created_at TEXT NOT NULL
);
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect() -> sqlite3.Connection:
    global _CONN
    if _CONN is None:
        with _LOCK:
            if _CONN is None:
                path = Path(get_settings().database_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                _CONN = sqlite3.connect(str(path), check_same_thread=False)
                _CONN.row_factory = sqlite3.Row
                _CONN.execute("PRAGMA journal_mode=WAL")
                _CONN.execute("PRAGMA foreign_keys=ON")
                _CONN.executescript(SCHEMA)
                _CONN.commit()
    return _CONN


@contextmanager
def tx() -> Iterator[sqlite3.Connection]:
    """Serialised write transaction."""
    with _LOCK:
        conn = connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def _j(obj: Any) -> str:
    return json.dumps(obj, default=str, separators=(",", ":"), sort_keys=True)


def _r(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    d = dict(row)
    for k in ("data", "extracted", "forensics"):
        if k in d and isinstance(d[k], str):
            try:
                d[k] = json.loads(d[k])
            except json.JSONDecodeError:
                pass
    return d


# --- generic helpers -----------------------------------------------------------

def upsert(table: str, keys: dict, doc: dict, columns: dict | None = None) -> None:
    cols = columns or {}
    fields = {**{k: v for k, v in keys.items()}, **cols, "data": _j(doc)}
    all_cols = ", ".join(fields)
    placeholders = ", ".join("?" for _ in fields)
    updates = ", ".join(f"{c}=excluded.{c}" for c in fields if c not in keys)
    sql = (
        f"INSERT INTO {table} ({all_cols}) VALUES ({placeholders}) "
        f"ON CONFLICT DO UPDATE SET {updates}" if updates
        else f"INSERT OR REPLACE INTO {table} ({all_cols}) VALUES ({placeholders})"
    )
    with tx() as conn:
        conn.execute(sql, tuple(fields.values()))


def get_one(table: str, where: str, params: tuple = ()) -> dict | None:
    conn = connect()
    row = conn.execute(f"SELECT * FROM {table} WHERE {where} LIMIT 1", params).fetchone()
    return _r(row)


def list_rows(table: str, where: str = "1=1", params: tuple = (),
              order: str = "", limit: int | None = None) -> list[dict]:
    conn = connect()
    sql = f"SELECT * FROM {table} WHERE {where}"
    if order:
        sql += f" ORDER BY {order}"
    if limit:
        sql += f" LIMIT {int(limit)}"
    return [_r(r) for r in conn.execute(sql, params).fetchall()]  # type: ignore[misc]


def delete_all(tables: list[str]) -> None:
    with tx() as conn:
        for t in tables:
            conn.execute(f"DELETE FROM {t}")


# --- ngo_profiles ---------------------------------------------------------------

def save_ngo(profile: dict, columns: dict | None = None) -> None:
    cols = {
        "name": profile.get("name", ""),
        "status": profile.get("status", "ACTIVE"),
        "primary_domain": profile.get("primary_domain", ""),
        "base_state": profile.get("base_state", ""),
        "trust_score": int(profile.get("trust", {}).get("score", 0) or 0),
        "trust_badge": profile.get("trust", {}).get("badge", "Verification Incomplete"),
        **(columns or {}),
    }
    upsert("ngo_profiles", {"ngo_id": profile["ngo_id"]}, profile, cols)


def get_ngo(ngo_id: str) -> dict | None:
    return get_one("ngo_profiles", "ngo_id=?", (ngo_id,))


def list_ngos(where: str = "1=1", params: tuple = ()) -> list[dict]:
    return list_rows("ngo_profiles", where, params, order="name")


def reset() -> None:
    """Drop all rows (seed --reset), including AUTOINCREMENT counters so
    sequences restart at 1 — determinism, twice in a row."""
    with tx() as conn:
        for t in [
            "ngo_profiles", "corporates", "mandates", "documents",
            "compliance_audit", "shell_networks", "matches", "outcomes",
            "audit_log", "review_notes", "counterfactuals", "rfps",
        ]:
            conn.execute(f"DELETE FROM {t}")
        conn.execute(
            "DELETE FROM sqlite_sequence WHERE name IN "
            "('audit_log','outcomes','matches','review_notes','counterfactuals','compliance_audit')"
        )
