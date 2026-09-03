"""app.services.dossier — one-page partner dossier PDF (B14)."""
from __future__ import annotations

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .. import db
from ..config import get_settings

styles = getSampleStyleSheet()
H1 = ParagraphStyle("h1", parent=styles["Title"], fontSize=16, textColor=colors.HexColor("#0F172A"))
H2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=11,
                    textColor=colors.HexColor("#1D4ED8"), spaceBefore=8)
BODY = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9, leading=12)
SMALL = ParagraphStyle("small", parent=styles["BodyText"], fontSize=7.5,
                       textColor=colors.HexColor("#475569"))


def build_dossier_pdf(mandate_id: str, ngo_ids: list[str]) -> bytes:
    settings = get_settings()
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title="SETU Partner Dossier")
    story = [
        Paragraph("SETU — Partner Dossier", H1),
        Paragraph(f"Mandate: {mandate_id or '—'} · Recipients: {', '.join(ngo_ids) or '—'}", SMALL),
        Spacer(1, 6 * mm),
    ]
    for ngo_id in ngo_ids:
        row = db.get_ngo(ngo_id)
        if not row:
            continue
        d = row["data"]
        trust = d.get("trust", {})
        story.append(Paragraph(f"{d.get('name', ngo_id)}", H2))
        rows = [
            ["Trust score", str(trust.get("score", "—")), "Badge", trust.get("badge", "—")],
            ["Domain", d.get("primary_domain", "—"), "Base", f"{d.get('base_district')}, {d.get('base_state')}"],
            ["Budget request", f"₹{d.get('budget_request_inr', 0):,}",
             "Status", d.get("status", "—")],
        ]
        t = Table(rows, colWidths=[30 * mm, 55 * mm, 25 * mm, 60 * mm])
        t.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E2E8F0")),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F8FAFC")),
        ]))
        story.append(t)
        story.append(Spacer(1, 4 * mm))

    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(
        f"algorithm_version {settings.algorithm_version} · generated {db.utcnow()} · "
        "Every score in this dossier is reproducible from its input hash.",
        SMALL,
    ))
    doc.build(story)
    return buf.getvalue()
