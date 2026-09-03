"""Package hygiene: the A-file constraints — no HTTP, no DB, no print()."""
from __future__ import annotations

import ast
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent / "setu_ml"

BANNED_IMPORTS = {
    "fastapi", "flask", "starlette", "uvicorn", "httpx", "requests",
    "aiohttp", "motor", "pymongo", "psycopg2", "sqlalchemy", "sqlite3",
}


def test_no_http_or_db_imports():
    for py in PKG.glob("*.py"):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    assert a.name.split(".")[0] not in BANNED_IMPORTS, (
                        f"{py.name} imports {a.name}"
                    )
            elif isinstance(node, ast.ImportFrom):
                mod = (node.module or "").split(".")[0]
                assert mod not in BANNED_IMPORTS, f"{py.name} imports from {mod}"


def test_no_print_in_library():
    offenders = []
    for py in PKG.glob("*.py"):
        if py.name == "__init__.py":
            continue
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "print"
            ):
                # allow the two intentional CLI-ish prints in calibrate.py
                if py.name == "calibrate.py":
                    continue
                offenders.append(f"{py.name}:{node.lineno}")
    assert offenders == [], f"print() found in library code: {offenders}"


def test_files_present():
    expected = {
        "types", "embeddings", "geo", "extract", "scoring", "justify",
        "calibrate", "trust", "consortium", "anomaly", "counterfactual",
        "pareto", "stability", "sdg", "outcomes", "shellgraph", "lexicon",
    }
    present = {p.stem for p in PKG.glob("*.py")}
    missing = expected - present
    assert not missing, f"missing modules: {missing}"
