"""app.services.forensics — document tamper & consistency checks (B12).

Four checks, each {check, passed, detail, severity}. Named warnings, never
silent adjustments. "Inconsistency detected, flagged for human review" —
never "fraudulent": the restraint is itself a signal of seriousness.
"""
from __future__ import annotations

from typing import Any


def check_cross_document_identifiers(ngo_id: str, extracted_by_doc: dict[str, dict]) -> dict[str, Any]:
    """The PAN on the 12A must equal the PAN on the 80G and the audit report.
    A mismatch is the strongest single fraud signal in the system."""
    pans: dict[str, str] = {}
    for doc_id, ext in extracted_by_doc.items():
        pan = ext.get("pan")
        if pan:
            pans[doc_id] = pan
    unique = set(pans.values())
    passed = len(unique) <= 1
    return {
        "check": "cross_document_identifier_agreement",
        "passed": passed,
        "severity": "high" if not passed else "info",
        "detail": (
            f"PAN agrees across {len(pans)} documents."
            if passed else
            f"PAN mismatch across documents: {pans} — flagged for human review."
        ),
    }


def check_fy_consistency(claimed_fy: str | None, audit_fy: str | None) -> dict[str, Any]:
    passed = (claimed_fy is None) or (audit_fy is None) or (claimed_fy == audit_fy)
    return {
        "check": "financial_year_consistency",
        "passed": passed,
        "severity": "medium" if not passed else "info",
        "detail": (
            f"Claimed FY {claimed_fy} matches the audited FY {audit_fy}."
            if passed else
            f"Claimed FY {claimed_fy} does not match the audited FY {audit_fy}."
        ),
    }


def check_arithmetic_reconciliation(programme: int, admin: int, other: int,
                                    stated_total: int,
                                    tolerance_inr: int = 1000) -> dict[str, Any]:
    computed = programme + admin + other
    diff = abs(computed - stated_total)
    passed = diff <= tolerance_inr
    return {
        "check": "arithmetic_reconciliation",
        "passed": passed,
        "severity": "high" if not passed else "info",
        "detail": (
            f"Programme + admin + other = ₹{computed:,} reconciles with the stated "
            f"total ₹{stated_total:,} within ₹{tolerance_inr}."
            if passed else
            f"Programme + admin + other = ₹{computed:,} but the statement claims "
            f"₹{stated_total:,} — a gap of ₹{diff:,}. Real audited statements "
            "reconcile; flagged for human review."
        ),
    }


def check_pdf_metadata(metadata: dict[str, str] | None,
                       fy_end_year: int | None = None) -> dict[str, Any]:
    """Metadata plausibility — a SIGNAL, never a verdict; plenty of legitimate
    documents have odd metadata."""
    issues: list[str] = []
    meta = metadata or {}
    created = meta.get("creation_date", "")
    if fy_end_year and created[:4].isdigit():
        if int(created[:4]) < fy_end_year - 1:
            issues.append(f"CreationDate {created} precedes the claimed FY end {fy_end_year}")
    if not meta.get("producer"):
        issues.append("Producer missing")
    mod = meta.get("mod_date", "")
    if created and mod and mod < created:
        issues.append(f"ModDate {mod} precedes CreationDate {created}")
    return {
        "check": "pdf_metadata_plausibility",
        "passed": not issues,
        "severity": "low" if issues else "info",
        "detail": "; ".join(issues) if issues else "Metadata plausible.",
    }


def run_forensics(docs: list[dict[str, Any]]) -> dict[str, Any]:
    """Run all four over one NGO's documents → {checks: [], warnings_count}."""
    by_doc = {
        d["doc_id"]: d.get("extracted", {})
        for d in docs
        if d.get("extracted")
    }
    checks = [check_cross_document_identifiers("x", by_doc)]

    audits = [d for d in docs if d.get("kind") == "audited_financials"]
    for a in audits:
        ext = a.get("extracted", {})
        checks.append(check_fy_consistency(
            ext.get("claimed_fy"), ext.get("audit_fy")))
        checks.append(check_arithmetic_reconciliation(
            int(ext.get("programme_expense_inr", 0)),
            int(ext.get("admin_expense_inr", 0)),
            int(ext.get("other_expense_inr", 0)),
            int(ext.get("total_expense_inr", 0)),
        ))
        checks.append(check_pdf_metadata(
            ext.get("pdf_metadata"), ext.get("fy_end_year")))

    warnings = [c for c in checks if not c["passed"]]
    return {
        "checks": checks,
        "warnings_count": len(warnings),
        "warnings": [c["detail"] for c in warnings],
    }
