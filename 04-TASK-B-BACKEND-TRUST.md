# TASK B — Backend, Compliance Forensics & Data
### Owner: **Vaishnavi** · Folder: `backend/` · Deliverable: a FastAPI service + the seeded world

---

## How to use this document

Open your AI IDE in the repo root and paste, in one message:

1. Sections 0–10 of `00-PROJECT-CONTEXT.md` (the domain, the formulas, the frozen API contract)
2. This entire file

Then work **B1 → B14 in order**. Two items are urgent for reasons beyond their own value:

- **B2 (the mocked API) must ship by Hour 8.** Until it exists, the frontend has nothing to build against and one third of your team is idle. It is the highest-leverage two hours in the whole project.
- **B3 (seed data) is the biggest single chunk of work in the entire build** and it is the thing most likely to make you late. Start it early, and if you are behind at Hour 16, ask Piyush to help — that hand-off is already written into the build plan.

---

## Your mandate

You own **truth**: the data, the documents, the compliance verification, and the API that exposes them. Piyush's library computes scores; you decide what goes into it and you are accountable for every number being traceable to a document.

You also own **two of the four features that decide whether this wins**: shell-network detection (B8) and evidence-anchored scoring (B6/B7). Those are yours to make excellent.

**Design rule that matters more than any other in your lane:** `compute_trust()` must be a **pure function** — evidence in, score out, no database access inside it. Piyush's counterfactual engine calls the *same function* with a hypothetically augmented evidence set. If you bury trust computation inside a database-reading service method, he cannot reuse it, he will re-derive the arithmetic, the two implementations will drift, and the counterfactual will predict +19 while the recompute yields +14 — in front of judges. One function, two callers.

---

## Setup

```powershell
cd C:\Users\Piyush\setu
mkdir backend\app, backend\app\models, backend\app\routers, backend\app\services, backend\app\parsing, backend\seed, backend\seed\data, backend\seed\pdfs, backend\tests
```

`backend/requirements.txt`:

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0
motor==3.3.2
pymongo==4.6.1
PyMuPDF==1.23.8
python-docx==1.1.0
python-multipart==0.0.6
reportlab==4.0.9
faker==22.0.0
numpy==1.26.3
pytest==7.4.4
httpx==0.26.0
-e ../ml
```

```powershell
cd C:\Users\Piyush\setu\backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

`uvicorn` will not be on your PATH — always use `python -m uvicorn`.

`.env.example` (commit this; never commit `.env`):

```
MONGO_URI=mongodb://localhost:27017
MONGO_DB=setu
DEMO_MODE=false
USE_LOCAL_INDEX=true
USE_MOCK_DATA=false
LLM_API_KEY=
ALGORITHM_VERSION=setu-1.0.0
```

---

# B1 · Skeleton, config, database

```
app/
  main.py          # app factory, CORS for localhost:3000, exception handlers, /docs
  config.py        # pydantic-settings Settings, read once, injected
  db.py            # Motor client, collection accessors, index creation on startup
  security.py      # X-Demo-Role dependency
  audit.py         # hash-chained append-only log
  models/          # request/response models mirroring §6 EXACTLY
  routers/         # one file per resource group
  services/        # trust.py, shell_network.py, matching.py, geo.py, forensics.py
  parsing/         # pdf.py, docx.py, compliance.py
```

Two things to get right in `main.py` from the start, because retrofitting them at Hour 44 is miserable:

**A global exception handler** returning the §6 error envelope. Every unhandled exception becomes `{"error": {"code": "INTERNAL", "message": ..., "detail": ...}}` with a 500 — never a raw stack trace to the frontend. A traceback rendered in the UI during judging is an avoidable embarrassment.

**A latency middleware** stamping `latency_ms` on every response. The frontend displays it (demo beat 4) and you need it for the NFR-1 benchmark. Measure the real thing, not an estimate.

```python
@app.middleware("http")
async def add_latency(request, call_next):
    t0 = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Latency-Ms"] = f"{(time.perf_counter()-t0)*1000:.1f}"
    return response
```

Collections and indexes per `01-PRD.md §6`: `ngo_profiles`, `corporates`, `mandates`, `documents`, `compliance_audit`, `shell_networks`, `matches`, `outcomes`, `audit_log`, `review_notes`. Index `ngo_profiles` on `primary_domain`, `base_state`, `status`, `trust.score`.

`GET /api/health` returns `{status, algorithm_version, demo_mode, ngo_count, index_ready, model_loaded}`. The frontend polls this for a readiness pill, so it must be honest — `index_ready` should reflect whether the embedding index actually loaded, not just that the process is up.

---

# B2 · The mocked API — ship this by Hour 8

**This is your most urgent deliverable and it is not about your own progress.** Every endpoint in §6, returning contract-shaped data read from hand-written JSON files, with `USE_MOCK_DATA=true`.

Write `backend/seed/data/mock_responses/` containing one JSON file per endpoint — literally copy the example payloads out of `00-PROJECT-CONTEXT.md §6`, since those were written to be exactly this. Then:

```python
# app/services/mock.py
def mock_response(name: str) -> dict:
    """Load seed/data/mock_responses/{name}.json. Used when settings.USE_MOCK_DATA."""
```

Every router checks the flag first and returns the mock. Rough shapes are fine; **correct field names are not optional** — the frontend is being written against these keys and a rename later costs both of you an hour.

Tell the third member the moment it is up. Then get back to B3.

---

# B3 ★ · Seed data — the world the demo lives in

**This is a first-class deliverable, not filler.** The demo's every claim rests on it. Two rules:

1. **Write the narrative before the generator.** `backend/seed/data/NARRATIVE.md` was agreed at Hour 0.5 (build plan item 0.5). It names the specific NGOs, the specific fraud, the specific mandate. Generate data to satisfy the narrative — never generate randomly and hope a story emerges.
2. **Fixed random seed.** `random.seed(42)`, `Faker.seed(42)`. Everyone's machine must produce byte-identical data or your team will debug phantom discrepancies at 3 a.m.

### Volume and spread

**48 NGOs** (40 minimum, 60 if you have time), across **all ten domains** and **at least 8 states**, with a realistic long tail: a few large professionalised organisations, many mid-size, several small rural ones. Use real district names with real approximate coordinates — pull the district list into `artifacts/districts_india.json` (district, state, lat, lng, is_aspirational) and share it with Piyush, since his `geo.py` and `extract.py` both need it. Real district names are load-bearing: a judge from Odisha will notice "Kalahandi" and will also notice an invented district.

### The planted cases — every one of these is a demo beat

| Case | Count | What exactly | Serves |
|---|---|---|---|
| **The shell ring** | 3 | Three NGOs with different names, in different-looking towns, that share: the same registered address fingerprint, one overlapping trustee name, and the same bank IFSC + account last-4. Give them plausible individual documents so they look fine one at a time — **the whole point is that they are only catchable as a network.** | Beat 6 |
| **Claim inflators** | 2 | `cost_per_beneficiary` roughly 25× below their cohort median (e.g. ₹41 against ₹1,180). Achieve it by inflating `beneficiaries_reached`, not by lowering spend — that is how the real thing looks. | Beat 5 / anomaly |
| **Missing CSR-1** | 4 | Otherwise strong NGOs — good proposals, high semantic match — with no CSR-1. **They must be strong**, because the point is that eligibility overrides fit. | Beat 4 / FR-C3 |
| **Expired 80G** | 3 | Valid registration, validity window ended 4–14 months ago. | Freshness + counterfactual |
| **Stale evidence** | 5 | Last audit 14–26 months old, so freshness decay visibly bites. | "last verified N months ago" |
| **The 61-point NGO** | 1 | **Engineer this one deliberately.** Everything decent except an expired CSR-1 and a missing FY25 audit. Uploading the CSR-1 renewal must move it from **61 → 80** and its badge from *Standard Audited* to *Verified Elite*. Tune its other pillars until the arithmetic lands on those numbers, then write a test that asserts 61 ± 1 and 80 ± 1. Landing on 79 means the badge never flips and the peak of the demo silently does not happen. | **Beat 8 — the emotional high point** |
| **The unfillable mandate** | 1 | ₹50L, two domains (maternal health + WASH), three Odisha districts (Kalahandi, Nuapada, Balangir) = **6 requirement units**. **No single NGO covers more than 3 of the 6**, and one specific *complementary pair* covers all 6 with ≤10% overlap. One of that pair must have `max_grant_managed_inr` low enough (₹8,00,000) that its share gets capped by absorptive capacity. Three-member combinations must also exist and must *lose* on coordination cost — that gives Piyush a real trade-off to demonstrate rather than an artificial one. | **Beat 7 — the headline** |
| **The keyword-invisible NGO** | 1 | Your best semantic match for the demo mandate, whose `proposal_text` deliberately never uses the words "maternal" or "health" — it says "postpartum institutional delivery care", "ASHA-worker capacity building", "safe childbirth". | **Beat 3 — the A/B toggle** |
| **A tampered document** | 1 | An 80G certificate whose registration number disagrees with the same NGO's annual report, and a financial statement whose stated total does not equal the sum of its parts. | Forensics (P2) |
| **CSR deserts** | ≥ 3 | At least three Aspirational Districts with high need index and **zero** verified partners. | Beat 9 |

Write `tests/test_seed_narrative.py` asserting **every row above**. When someone regenerates the seed data at Hour 30 and quietly breaks the 61→80 case, this test is the only thing that will tell you before the stage does.

### Proposal text quality

This is where synthetic datasets usually give themselves away. Do not generate `"We work on education in rural areas."` for 48 organisations. Each `proposal_text` needs 80–150 words with sector-specific vocabulary, a named intervention model, a beneficiary count, and a district reference. Write 10 strong templates by hand with slot-filling, and hand-write the 5 NGOs that appear in the demo entirely.

**The semantic matching demo is only as convincing as this text.** If every proposal reads the same, embeddings have nothing to discriminate on, your calibrated scores bunch together, and beat 3 falls flat.

---

# B4 · Mock compliance PDFs — `make_mock_pdfs.py`

Generate with ReportLab, one per NGO per artefact type, into `seed/pdfs/`. These are what beat 5 displays, so they must survive being projected.

| Artefact | Must contain |
|---|---|
| CSR-1 | MCA-style header, `CSR Registration Number: CSR00012345`, NGO name, PAN, date of registration, a signature block |
| 12A | Income Tax Department header, order/registration number, effective date |
| 80G | Registration number, **validity period with explicit from/to dates** (this is what expiry detection reads) |
| Darpan | NITI Aayog header, `Unique ID: OR/2019/0234567`, state, sector |
| Audited financials | A small table: total income, programme expenditure, administrative expenditure, total expenditure, FY label. **Make the numbers agree with the NGO's `financials` object** — except for the deliberately tampered one. |
| Impact assessment | Title, evaluator name, period, a findings paragraph, a beneficiary figure |

Two requirements that make beat 5 land:

**Put the registration number on a predictable page** and record which page in the generator. Then your evidence reference `{doc_id, page, snippet}` is verifiable rather than approximate.

**Vary the layout across NGOs.** If all 48 CSR-1s are pixel-identical, your extraction is matching a fixed template, not extracting. Rotate through three layouts, and make one or two documents render as an **image-only page with no text layer** so FR-A7 (reduced extraction confidence on scanned documents) has something real to detect.

---

# B5 · `parsing/pdf.py` — text with page anchors

The whole evidence-drill-down feature depends on this being anchored, not just extracted.

```python
def extract_pages(path: str) -> list[PageText]:
    """PyMuPDF. One entry per page: {page_no (1-based), text, char_count, has_text_layer}."""

def find_with_anchor(pages: list[PageText], pattern: str) -> EvidenceRef | None:
    """Regex search across pages. Returns
    {page, match, snippet (±120 chars around the match), char_start, char_end}.
    The snippet is what the UI highlights — it MUST actually contain the match."""

def render_page_png(path: str, page_no: int, dpi: int = 120) -> bytes:
    """PyMuPDF pixmap → PNG bytes. Served by /api/documents/{id}/pages/{n}.png.
    Cache to disk on first render; re-rasterising on every request is slow enough to
    be visible when a judge is clicking through evidence."""

def detect_kind(pages: list[PageText]) -> tuple[str, float]:
    """Classify by keyword signature; return (kind, confidence).
    Pages with has_text_layer == False across the whole document → confidence
    capped at 0.3 and kind 'scanned_unknown'. Never return empty extracted fields
    as though extraction succeeded — a confident empty result is the worst outcome."""
```

`docx.py` mirrors this with python-docx, treating paragraph index as the anchor since DOCX has no real page concept. Say that plainly in the code comment rather than faking page numbers.

---

# B6 ★ · `parsing/compliance.py` — artefact extraction and validation

```python
CSR1_RE   = re.compile(r"CSR\s*(?:Registration\s*)?(?:No\.?|Number)?\s*[:\-]?\s*(CSR\d{8})", re.I)
DARPAN_RE = re.compile(r"\b([A-Z]{2}/\d{4}/\d{7})\b")
PAN_RE    = re.compile(r"\b([A-Z]{5}\d{4}[A-Z])\b")
REG_12A_RE = re.compile(r"12\s*-?A.{0,80}?([A-Z0-9/\-]{8,25})", re.I | re.S)
REG_80G_RE = re.compile(r"80\s*-?G.{0,80}?([A-Z0-9/\-]{8,25})", re.I | re.S)
VALIDITY_RE = re.compile(r"valid(?:ity)?\s*(?:from|period)?\s*[:\-]?\s*"
                         r"(\d{2}[/-]\d{2}[/-]\d{4})\s*(?:to|–|-)\s*(\d{2}[/-]\d{2}[/-]\d{4})", re.I)

def extract_compliance(pages, kind) -> ComplianceExtraction:
    """Returns, per artefact: present, value, format_valid, valid_from, valid_to,
    is_expired, EvidenceRef, confidence."""

def validate_csr1(value: str) -> bool:
    """'CSR' + exactly 8 digits. Say plainly in the docstring that this is FORMAT
    validation, not registry verification — and be ready to say the same out loud."""

def validate_pan(value: str) -> bool:
    """5 letters + 4 digits + 1 letter. The 4th character encodes entity type;
    'T' = trust, 'A' = AOP, 'F' = firm. An NGO with a PAN whose 4th char is 'P'
    (individual) is a genuine red flag worth surfacing — a small detail that reads as
    real domain knowledge."""
```

### The evidence ledger — this is FR-C4 and it is a P1

Every extracted artefact produces an `EvidenceRef`. Store them in `compliance_audit`, one document per pillar per NGO:

```python
{
  "ngo_id": "ngo_014", "pillar": "compliance",
  "raw": 0.90, "effective": 0.86, "freshness_days": 96,
  "evidence": [
    {"doc_id": "doc_031", "kind": "csr1", "page": 1,
     "snippet": "...CSR Registration Number: CSR00012345 dated 12/04/2023...",
     "char_start": 412, "char_end": 468, "confidence": 0.97}
  ],
  "computed_at": "...", "algorithm_version": "setu-1.0.0", "input_hash": "sha256:..."
}
```

**The invariant, and it is worth a test of its own:** every pillar has at least one evidence reference, **or** is explicitly marked `no_evidence: true` with a contribution of exactly 0. A trust number with nothing behind it is the fastest way to lose a judge who clicks into it, and clicking into it is precisely what an interested judge will do.

---

# B7 ★ · `services/trust.py` — a pure function, and the whole build depends on that

Implement `00-PROJECT-CONTEXT.md §5.2` exactly. **Read the design rule at the top of this document again before you write this file.**

```python
def compute_trust(profile: NgoProfile,
                  evidence: EvidenceSet,
                  anomaly: AnomalyReport | None = None,
                  shell_flag: bool = False,
                  now: datetime | None = None) -> TrustBreakdown:
    """PURE. No database. No I/O. No global state. Deterministic given its inputs.

    Piyush's counterfactual engine calls THIS function with a hypothetically
    augmented EvidenceSet. That is the only way the predicted delta and the
    realised delta can be guaranteed to agree. Do not move any part of this
    computation into a service method that reads Mongo."""

def pillar_compliance(evidence, foreign_funded: bool) -> tuple[float, list[EvidenceRef]]
def pillar_financial(profile) -> tuple[float, list[EvidenceRef]]
def pillar_operational(profile) -> tuple[float, list[EvidenceRef]]
def pillar_external(evidence) -> tuple[float, list[EvidenceRef]]

def freshness(evidence_age_days: int, half_life_days: int) -> float:
    """0.5 ** (age / half_life)"""

def apply_freshness(pillar_raw: float, fresh: float) -> float:
    """pillar_raw * (0.60 + 0.40 * fresh) — the 0.60 floor is deliberate;
    stale-but-real evidence is discounted, not annihilated."""

def assign_badge(score: float, is_ineligible: bool, has_shell_flag: bool) -> TrustBadge
def input_hash(profile, evidence, anomaly, shell_flag) -> str
    """SHA-256 of canonical JSON with sorted keys. This is what makes FR-C11
    reproducibility real rather than aspirational."""
```

Three details that are easy to get wrong and expensive to find late:

**The FCRA renormalisation.** When `foreign_funded` is False, FCRA is dropped and the remaining compliance weights are renormalised over 0.90. If you forget this, every domestic NGO silently loses 10% of its compliance pillar and all your trust scores are a bit too low — which you will discover when the 61-point NGO refuses to reach 61.

**The CSR-1 hard gate happens before scoring.** Set `status = "INELIGIBLE"` and badge `Ineligible for CSR Funds`. Piyush filters on `status`, so this field is the contract between you.

**Laplace smoothing in the operational pillar** — `(completed + 1) / (total + 2)`, per §5.2. A one-for-one NGO must not score 100%.

**Tests:** hand-compute one NGO's trust in a spreadsheet and assert the code matches within ±0.5; `compute_trust` called twice with identical inputs returns an identical `input_hash`; a no-CSR-1 NGO returns `INELIGIBLE`; a domestic NGO with everything except FCRA scores the same as if FCRA did not exist; **the 61-point NGO scores exactly 61 ± 1, and 80 ± 1 once the CSR-1 renewal is added.**

---

# B8 ★ · `services/shell_network.py` — your headline feature

Read §5.5. This is demo beat 6 and it is the single most memorable thing in the project, because it is how financial-crime teams actually work and no other team will have it.

```python
def normalise_address(raw: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace, drop the common noise words
    ('plot', 'near', 'opp', 'behind', 'road', 'street'), anchor on the 6-digit PIN.
    Return a stable fingerprint. Over-normalising creates false rings; under-
    normalising misses real ones. Test on your seeded ring both ways."""

def normalise_phone(raw: str) -> str:
    """Digits only, strip +91 / leading 0, keep the last 10."""

def normalise_name(raw: str) -> str:
    """Lowercase, strip honorifics (shri, smt, dr, mr, mrs), collapse whitespace."""

GENERIC_EMAIL_DOMAINS = {"gmail.com","yahoo.com","yahoo.in","outlook.com",
                         "hotmail.com","rediffmail.com","protonmail.com"}
    # Two NGOs sharing gmail.com is not a signal. Allowlisting these is the
    # difference between a detector and a random flag generator.

def build_graph(ngos: list[NgoProfile]) -> dict:
    """Undirected. Edge when two NGOs share a normalised identifier. Each edge
    records WHICH identifier types matched — the UI displays them and you will
    say them out loud."""

def find_components(graph) -> list[ShellNetwork]:
    """Connected components. Flag when >= 2 members AND >= 2 distinct shared
    identifier types. One shared landline is a coincidence; a shared address AND a
    shared trustee AND a shared bank account is a pattern."""

def apply_penalties(ngos, networks) -> None:
    """shell_penalty = 20, trust capped at 40, badge forced to High Risk,
    status -> FLAGGED. Persist to shell_networks."""
```

`GET /api/ngos/{id}/network` returns `{flagged, component_id, members[{ngo_id, name, trust_score}], shared_identifier_types[], edges[]}`.

**Two guards against embarrassment.** First, run detection across the *whole* seeded set and read the output yourself — if it flags eight rings, your normalisation is too loose and the feature looks like noise. You want exactly the one planted ring, plus possibly one defensible near-miss you can explain. Second, the two-identifier-type rule exists precisely to prevent single-coincidence flags; do not weaken it to catch more.

**Tests:** the seeded ring returns as one component with all three members and ≥ 2 shared types; all three are capped at trust ≤ 40 and badged High Risk; two NGOs sharing only a gmail address are **not** flagged; two sharing only a phone number are **not** flagged; no unplanted component is flagged across the full seed set.

---

# B9 · `/api/ngos/{id}/counterfactual` — thin wrapper, zero cleverness

Your job here is plumbing, and the discipline is in what you *don't* do.

```python
@router.get("/api/ngos/{ngo_id}/counterfactual")
async def counterfactual(ngo_id: str, db = Depends(get_db)):
    profile  = await repo.get_profile(ngo_id)
    evidence = await repo.get_evidence(ngo_id)
    report   = setu_ml.counterfactual.analyse(
        profile, evidence, compute_trust_fn=services.trust.compute_trust
    )
    return report.model_dump()
```

You pass `compute_trust` **in**. Piyush's module never imports from `backend/`, and never re-derives the arithmetic. If you find yourself computing a delta inside this endpoint, stop — you have just created the on-stage contradiction the whole design was built to prevent.

Persist each generated report to `counterfactuals` with `algorithm_version` and `input_hash` so the audit trail survives a re-run.

**The round-trip test — write this one even if you skip others.** For every seeded NGO: fetch the counterfactual, take the top actionable item, actually add that evidence via `POST /api/documents/upload` + `POST /api/verify`, recompute trust, and assert `realised_delta == predicted_delta` within ±0.5. Run it in CI. A judge who spots a mismatch between "+19 pts" and the number that appears after uploading has found the one flaw that discredits everything else on the screen.

---

# B10 · `POST /api/match` — the endpoint the demo lives on

```python
@router.post("/api/match")
async def match(req: MatchRequest, db = Depends(get_db)):
    t0 = time.perf_counter()
    mandate = await repo.get_mandate(req.mandate_id)
    ngos    = await repo.list_profiles(filters=req.filters)

    eligible   = [n for n in ngos if n.status != "INELIGIBLE"]
    excluded_n = len(ngos) - len(eligible)          # surfaced in the response

    results = setu_ml.scoring.rank(
        mandate, eligible,
        trust_scores={n.id: n.trust_score for n in eligible},
        use_keyword_baseline=req.use_keyword_baseline,
        weights=req.weights or DEFAULT_WEIGHTS,
    )
    consortiums = setu_ml.consortium.build(mandate, eligible, results) \
                  if req.include_consortiums else []
    ...
    return MatchResponse(..., latency_ms=round((time.perf_counter()-t0)*1000, 1))
```

Order matters: **filter ineligible before scoring, not after.** Ranking an NGO you are about to hide wastes work and, worse, changes the percentile calibration Piyush fitted.

`excluded_ineligible_count` goes in the response and the UI shows it. "Four organisations were excluded because they have not filed CSR-1" is a stronger statement than silently returning six results.

Return the real measured `latency_ms`. Lane C displays it. Do not hardcode a flattering number — if a judge reloads and the number never changes, you have handed them a reason to doubt everything else.

Set `X-Cache: hit|miss`. Cache the embedding matrix in memory at startup; recompute only when an NGO's profile text changes.

---

# B11 · Geo endpoints — the "need" side of the map

`GET /api/geo/coverage` returns, per district: `{district, state, ngo_count, total_capacity_inr, need_index, is_aspirational, gap_score, domains[]}`.

```
need_index  ∈ [0,1]   # seeded per district; higher = greater unmet need
gap_score   = need_index × (1 − min(ngo_count / 5, 1))
```

`is_aspirational` comes from the NITI Aayog Aspirational Districts list. **Ship only the districts you can actually verify against the published list** — a wrong district in that flag is the kind of error a domain-expert judge catches instantly. If you cannot verify a district, set the flag `false` and move on.

`GET /api/geo/nearby?lat=&lon=&radius_km=&domain=` — haversine filter, reuse `setu_ml.geo`.

Guarantee at least three districts with `gap_score > 0.7` and `ngo_count == 0`. Those are the CSR deserts, and they are what turns the map from decoration into an argument.

---

# B12 · `services/forensics.py` — P2, and worth it if you get there

Four checks, each returning `{check, passed, detail, severity}`:

**Cross-document identifier agreement** — the PAN on the 12A certificate must equal the PAN on the 80G certificate and the audit report. A mismatch is the strongest single fraud signal in the whole system.

**Financial-year consistency** — the FY stated in the audit report must match the FY of the figures being claimed.

**Arithmetic reconciliation** — programme + admin + other should sum to total expenditure within ₹1,000. Real audited statements reconcile; fabricated ones frequently do not.

**PDF metadata plausibility** — `CreationDate` after the claimed FY end, `Producer` present, `ModDate` not wildly after `CreationDate`. Report it as a *signal*, never a verdict; plenty of legitimate documents have odd metadata.

Say "inconsistency detected, flagged for human review", not "fraudulent". The tampered seeded document should trip exactly two checks so you can point at the specifics.

---

# B13 · RBAC, review notes, audit log

Three roles: `corporate`, `ngo`, `admin`. A dependency `require_role(*roles)` on every mutating route. `review_notes` are visible to `corporate` and `admin` and **never** returned to `ngo` — enforce it in the serialiser, not in the frontend, and write a test that asserts an NGO token cannot read them.

Hash-chained audit log:

```python
entry_hash = sha256(f"{prev_hash}{actor}{action}{target}{timestamp}{payload_json}")
```

`GET /api/audit?verify=true` walks the chain and returns `{valid: bool, entries_checked: int, broken_at: str | None}`. Seed one deliberately broken chain in a *separate* collection so you can demonstrate detection working — never break the live one.

---

# B14 · RFP dispatch, dossier PDF, outcomes

`POST /api/rfp` creates the record and returns `{rfp_id, status: "sent", recipients[]}`. Do not send real email; `DEMO_MODE` logs the payload. Say "dispatch is stubbed" if asked — it is a two-line change and no judge deducts for it.

`GET /api/rfp/{id}/dossier.pdf` — ReportLab. Cover page with mandate and shortlist; one page per NGO with the trust breakdown, badge, and evidence citations including document name and page number; a final page with `algorithm_version`, `input_hash` and generation timestamp. Under 3 seconds for five NGOs.

`POST /api/outcomes` + `GET /api/analytics/calibration` — record predicted vs realised, return buckets for a reliability chart. **Never say the model retrains.** Say: "We log outcomes so the weights can be calibrated against reality over time; that loop is instrumented, not trained."

---

# Demo mode and reset

`python -m seed --reset` must restore exact demo state in under 60 seconds, and you must run it twice in a row and confirm identical output. `DEMO_MODE=true` disables destructive routes, `USE_MOCK_DATA=true` serves `seed/data/mock_responses/`. Capture live responses for every demo endpoint into `frontend/fixtures/` at Hour 42 and hand them to Lane C.

---

# Definition of done

Every §6 endpoint responds with contract-shaped data. `compute_trust` is pure and is the *only* place trust arithmetic exists. The round-trip counterfactual test passes for all 48 NGOs. Every pillar of every NGO resolves to a document page or explicit `no_evidence`. The shell ring is detected; nothing else is. p95 latency under 800 ms over 1,000 records, measured. `seed --reset` verified twice. Everything runs with the network adapter disabled.

# Three answers to have loaded

**"How do you know the documents are real?"** — We don't claim to. We verify format, internal consistency across documents, and arithmetic, and we anchor every score to a page a human can open. Registry verification against MCA and Darpan is an API integration, not a research problem — the evidence architecture is already built for it.

**"Isn't shell detection just string matching?"** — It's connected components over a multi-identifier graph with normalisation and a two-identifier-type threshold, which is how financial-crime teams actually approach it. The threshold is what stops it from being a random flag generator; two NGOs sharing a gmail address are not flagged, and I can show you that.

**"Why is CSR-1 a hard gate rather than a weight?"** — Because it's law, not judgement. Since 1 April 2021 a company cannot legally count a contribution as CSR spend if the recipient hasn't filed Form CSR-1. A weighted score that ranks an ineligible NGO seventh instead of excluding it is giving a CSR head advice that could fail their audit.

---

*`04-TASK-B-BACKEND-TRUST.md` · paste alongside `00-PROJECT-CONTEXT.md` §0–10*
