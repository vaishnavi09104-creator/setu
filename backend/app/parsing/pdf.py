"""app.parsing.pdf — text with page anchors (B5). The whole evidence
drill-down depends on extraction being ANCHORED, not just extracted."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pymupdf  # PyMuPDF


@dataclass
class PageText:
    page_no: int  # 1-based
    text: str
    char_count: int
    has_text_layer: bool


@dataclass
class EvidenceAnchor:
    page: int
    match: str
    snippet: str  # ±120 chars around the match — MUST contain the match
    char_start: int
    char_end: int


def extract_pages(path: str | Path) -> list[PageText]:
    doc = pymupdf.open(str(path))
    pages: list[PageText] = []
    for i, page in enumerate(doc, start=1):
        text = page.get_text("text")
        has_layer = bool(text.strip())
        pages.append(PageText(page_no=i, text=text,
                              char_count=len(text), has_text_layer=has_layer))
    doc.close()
    return pages


def find_with_anchor(pages: list[PageText], pattern: str) -> EvidenceAnchor | None:
    """Regex search across pages; returns page, snippet (±120 chars),
    char offsets. The snippet is what the UI highlights — it must actually
    contain the match."""
    rx = re.compile(pattern, re.I | re.S)
    for p in pages:
        if not p.has_text_layer:
            continue
        m = rx.search(p.text)
        if m:
            start, end = m.span()
            lo = max(0, start - 120)
            hi = min(len(p.text), end + 120)
            snippet = p.text[lo:hi].replace("\n", " ").strip()
            return EvidenceAnchor(
                page=p.page_no, match=m.group(0), snippet=snippet,
                char_start=start, char_end=end,
            )
    return None


def render_page_png(path: str | Path, page_no: int, dpi: int = 120,
                    cache_dir: str | Path | None = None) -> bytes:
    """PyMuPDF pixmap → PNG bytes, cached to disk on first render (re-rasterising
    on every request is slow enough to be visible when a judge clicks through)."""
    cache_path = None
    if cache_dir:
        cdir = Path(cache_dir)
        cdir.mkdir(parents=True, exist_ok=True)
        cache_path = cdir / f"{Path(path).stem}_p{page_no}_{dpi}.png"
        if cache_path.exists():
            return cache_path.read_bytes()
    doc = pymupdf.open(str(path))
    page = doc[page_no - 1]
    pix = page.get_pixmap(dpi=dpi)
    data = pix.tobytes("png")
    doc.close()
    if cache_path:
        cache_path.write_bytes(data)
    return data


# keyword signatures for kind detection
_KIND_SIGNATURES: list[tuple[str, list[str]]] = [
    ("csr1", ["csr registration number", "form csr-1", "csr0000"]),
    ("reg_12a", ["12a", "section 12a", "income tax"]),
    ("reg_80g", ["80g", "section 80g"]),
    ("darpan", ["ngo-darpan", "niti aayog", "unique id"]),
    ("fcra", ["foreign contribution", "fcra"]),
    ("audited_financials", ["audited", "balance sheet", "income and expenditure", "total expenditure"]),
    ("impact_report", ["impact assessment", "evaluation", "findings"]),
    ("mandate", ["mandate", "proposal", "budget"]),
]


def detect_kind(pages: list[PageText]) -> tuple[str, float]:
    """Classify by keyword signature; scanned docs (no text layer anywhere)
    → confidence capped at 0.3 and kind 'scanned_unknown'. A confident empty
    result is the worst outcome — never return one."""
    full = " ".join(p.text.lower() for p in pages if p.has_text_layer)
    if not full.strip():
        return "scanned_unknown", 0.3

    best_kind, best_score = "unknown", 0.0
    for kind, kws in _KIND_SIGNATURES:
        hits = sum(1 for kw in kws if kw in full)
        score = hits / len(kws)
        if score > best_score:
            best_kind, best_score = kind, score
    confidence = 0.5 + 0.5 * best_score  # signature coverage → [0.5, 1.0]
    if best_kind == "unknown":
        return "unknown", 0.4
    return best_kind, round(min(1.0, confidence), 2)
