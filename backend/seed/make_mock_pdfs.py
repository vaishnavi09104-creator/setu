"""seed.make_mock_pdfs — realistic compliance artefact PDFs (B4).

One per NGO per artefact type, into seed/pdfs/. Requirements:
  - registration numbers on a PREDICTABLE page (recorded in the generator)
  - numbers agree with the NGO's financials object — except the tampered one
  - three layout variants + one image-only page (no text layer)
"""
from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

PDF_DIR = Path(__file__).resolve().parent / "pdfs"
rng = random.Random(42)

styles = getSampleStyleSheet()
H = ParagraphStyle("h", parent=styles["Title"], fontSize=13,
                   textColor=colors.HexColor("#0F172A"))
B = ParagraphStyle("b", parent=styles["BodyText"], fontSize=9, leading=12)
BOLD = ParagraphStyle("bd", parent=styles["BodyText"], fontSize=9, leading=12,
                      fontName="Helvetica-Bold")
SMALL = ParagraphStyle("s", parent=styles["BodyText"], fontSize=7.5,
                       textColor=colors.HexColor("#475569"))

LAYOUT_TITLES = [
    "MINISTRY OF CORPORATE AFFAIRS",
    "GOVERNMENT OF INDIA",
    "OFFICE OF THE REGISTRAR",
]
FY = "2024-25"


def _pan(ngo_id: str, entity: str = "T") -> str:
    rng_local = random.Random(ngo_id)
    letters = "".join(rng_local.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(3))
    digits = "".join(rng_local.choice("0123456789") for _ in range(4))
    last = rng_local.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    return f"{letters}{entity[0]}{digits}{last}"


def _csr_number(ngo_id: str) -> str:
    rng_local = random.Random(ngo_id + "csr")
    return "CSR" + "".join(rng_local.choice("0123456789") for _ in range(8))


def _doc(path: Path, title: str, flowables: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(path), pagesize=A4, title=title)
    doc.build(flowables)


def build_csr1(ngo: dict, path: Path, variant: int = 0) -> None:
    num = _csr_number(ngo["ngo_id"])
    pan = _pan(ngo["ngo_id"])
    flow = [
        Paragraph(LAYOUT_TITLES[variant % 3], H),
        Paragraph("FORM CSR-1 — REGISTRATION OF IMPLEMENTING AGENCY", BOLD),
        Spacer(1, 12),
        Paragraph(f"Registration Number: <b>{num}</b>", B),
        Paragraph(f"Registered Entity: {ngo['name']}", B),
        Paragraph(f"PAN: {pan}", B),
        Paragraph("Date of Registration: 12/04/2023", B),
        Paragraph("Validity: Per Section 135 read with CSR Policy Rules.", B),
        Spacer(1, 24),
        Paragraph("Authorised Signatory — Registrar, CSR Division", B),
    ]
    _doc(path, "CSR-1 Registration", flow)


def build_12a(ngo: dict, path: Path, variant: int = 0) -> None:
    pan = _pan(ngo["ngo_id"])
    flow = [
        Paragraph(LAYOUT_TITLES[(variant + 1) % 3], H),
        Paragraph("INCOME TAX DEPARTMENT — ORDER UNDER SECTION 12A", BOLD),
        Spacer(1, 10),
        Paragraph(f"Registration Number: 12A/{rng.randint(2000, 2024)}/{rng.randint(10000, 99999)}", B),
        Paragraph(f"Entity: {ngo['name']}", B),
        Paragraph(f"PAN: {pan}", B),
        Paragraph("Effective Date: 01/04/2019", B),
        Paragraph("Validity: from 01/04/2019 to 31/03/2029", B),
    ]
    _doc(path, "12A Registration", flow)


def build_80g(ngo: dict, path: Path, variant: int = 0, expired: bool = False,
              tamper_pan: str | None = None) -> None:
    pan = tamper_pan or _pan(ngo["ngo_id"])
    if expired:
        vfrom, vto = "01/04/2021", "31/03/2025"
    else:
        vfrom, vto = "01/04/2023", "31/03/2028"
    flow = [
        Paragraph(LAYOUT_TITLES[(variant + 2) % 3], H),
        Paragraph("INCOME TAX DEPARTMENT — ORDER UNDER SECTION 80G", BOLD),
        Spacer(1, 10),
        Paragraph(f"Registration Number: 80G/{rng.randint(2000, 2026)}/{rng.randint(10000, 99999)}", B),
        Paragraph(f"Entity: {ngo['name']}", B),
        Paragraph(f"PAN: {pan}", B),
        Paragraph(f"Validity: from {vfrom} to {vto}", B),
    ]
    _doc(path, "80G Registration", flow)


def build_darpan(ngo: dict, path: Path, variant: int = 0) -> None:
    uid = f"OD/{rng.randint(2015, 2024)}/{rng.randint(1000000, 9999999)}"
    flow = [
        Paragraph("NITI AAYOG — NGO-DARPAN PORTAL", H),
        Paragraph("UNIQUE IDENTITY CERTIFICATE", BOLD),
        Spacer(1, 10),
        Paragraph(f"Unique ID: {uid}", B),
        Paragraph(f"Organisation: {ngo['name']}", B),
        Paragraph(f"State: {ngo['base_state']}", B),
        Paragraph(f"Sector: {ngo['primary_domain']}", B),
    ]
    _doc(path, "Darpan ID", flow)


def build_audit(ngo: dict, path: Path, variant: int = 0,
                reconcile: bool = True) -> None:
    f = ngo.get("financials", {})
    prog = f.get("programme_expense_inr", 0)
    admin = f.get("admin_expense_inr", 0)
    total = f.get("total_expense_inr", 0)
    stated = total if reconcile else total + 450_000  # tampered: off by ₹4.5L
    rows = [
        ["Particulars", f"FY {FY} (₹)"],
        ["Total Income", f"{stated + 250_000:,}"],
        ["Programme Expenditure", f"{prog:,}"],
        ["Administrative Expenditure", f"{admin:,}"],
        ["Total Expenditure", f"{stated:,}"],
    ]
    t = Table(rows, colWidths=[110, 80])
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E2E8F0")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    flow = [
        Paragraph(f"AUDITED FINANCIAL STATEMENT — FY {FY}", H),
        Paragraph(f"{ngo['name']}", BOLD),
        Paragraph(f"PAN: {_pan(ngo['ngo_id'])}", B),
        Paragraph("Auditor: M/s Rao &amp; Associates, Chartered Accountants", SMALL),
        Spacer(1, 8),
        t,
        Spacer(1, 6),
        Paragraph("Notes: figures reconcile to the audited ledger.", SMALL),
    ]
    _doc(path, f"Audit FY{FY}", flow)


def build_scanned_placeholder(ngo: dict, path: Path) -> None:
    """Image-only page with NO extractable text layer — FR-A7's real test.
    Text is simulated with vector strokes (drawings), not glyphs, so
    page.get_text() returns nothing."""
    import pymupdf

    path.parent.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    # header bar + lines simulating a scanned certificate layout
    page.draw_rect(pymupdf.Rect(40, 150, 555, 190), color=(0.1, 0.2, 0.5), width=2)
    for y in range(240, 700, 40):
        page.draw_line(pymupdf.Point(60, y), pymupdf.Point(535, y),
                       color=(0.3, 0.3, 0.3), width=1)
    # seal circle
    page.draw_circle(pymupdf.Point(470, 640), 40, color=(0.6, 0.1, 0.1), width=2)
    doc.save(str(path))
    doc.close()


def generate_all(world: list[dict]) -> dict[str, Any]:
    """One artefact set per NGO; returns {ngo_id: {kind: {path, page}}}."""
    manifest: dict[str, Any] = {}
    for i, ngo in enumerate(world):
        nid = ngo["ngo_id"]
        variant = i % 3
        reg_page = 1
        files: dict[str, dict] = {}

        f = PDF_DIR / f"{nid}_csr1.pdf"
        build_csr1(ngo, f, variant)
        files["csr1"] = {"path": str(f), "page": reg_page}

        f = PDF_DIR / f"{nid}_12a.pdf"
        build_12a(ngo, f, variant)
        files["reg_12a"] = {"path": str(f), "page": reg_page}

        expired_80g = nid in ("ngo_033", "ngo_034", "ngo_061")
        f = PDF_DIR / f"{nid}_80g.pdf"
        # ngo_033 is the TAMPERED doc: 80G PAN disagrees with the audit's
        if nid == "ngo_033":
            build_80g(ngo, f, variant, expired=expired_80g,
                      tamper_pan=_pan(ngo["ngo_id"], entity="P"))  # individual PAN — red flag
        else:
            build_80g(ngo, f, variant, expired=expired_80g)
        files["reg_80g"] = {"path": str(f), "page": reg_page}

        f = PDF_DIR / f"{nid}_darpan.pdf"
        build_darpan(ngo, f, variant)
        files["darpan"] = {"path": str(f), "page": reg_page}

        f = PDF_DIR / f"{nid}_audit.pdf"
        # ngo_033's audit does NOT reconcile (tampered)
        build_audit(ngo, f, variant, reconcile=(nid != "ngo_033"))
        files["audit_fy"] = {"path": str(f), "page": reg_page}

        # one scanned doc for the whole corpus (FR-A7)
        if i == 5:
            f = PDF_DIR / f"{nid}_impact_scanned.pdf"
            build_scanned_placeholder(ngo, f)
            files["impact_assessment"] = {"path": str(f), "page": reg_page, "scanned": True}

        manifest[nid] = files
    return manifest
