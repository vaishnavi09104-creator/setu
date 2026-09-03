# SETU — Product Requirements Document

**Version** 1.0 · **Date** 2026-09-03 · **Status** Approved for 48-hour build
**Track** Corporate Social Responsibility — Problem Statement 2 (NGO–Corporate CSR Matching)
**Companion documents** `00-PROJECT-CONTEXT.md` (formulas + API contract, authoritative) · `02-BUILD-PLAN-48H.md` (schedule)

> Scoring formulas and API shapes are **not duplicated here**. `00-PROJECT-CONTEXT.md` is the single source of truth for both; this document defines *what* must be true and *how we will know*, and references §-numbers there.

---

## 1. Executive summary

India mandates corporate social responsibility spending by law (Companies Act 2013, Section 135): qualifying companies must spend at least 2% of their three-year average net profit on prescribed social activities. The capital is committed. What is missing is a reliable way to find, verify and combine implementation partners.

CSR teams today run discovery on spreadsheets and referrals, verification on manual document collection over weeks, and mandate design around whichever single NGO they can find — shrinking the mandate to fit the partner rather than assembling partners to fit the mandate. The results are predictable: good NGOs stay invisible because their vocabulary differs from the search box, shell entities slip through because nobody can see the network behind an individual registration, and budget sits unspent at year end.

SETU addresses all three. Semantic matching finds partners by meaning rather than keyword. An evidence-anchored trust index — built from real Indian compliance artefacts, cohort-relative financial anomaly detection and shell-network graph analysis — makes credibility auditable, with every score component linked to the page of the document it came from. And a consortium engine assembles two or three complementary partners when no single organisation can deliver a mandate, penalising overlap and respecting each partner's demonstrated absorptive capacity.

Two design commitments distinguish SETU from a ranking tool. First, **eligibility is enforced, not scored**: an NGO without valid CSR-1 registration cannot legally receive CSR funds, so it is excluded from results rather than ranked low. Second, **the supply side is served, not merely judged**: every NGO that falls short receives a specific, evidenced roadmap — *"upload your renewed CSR-1 and your score moves from 61 to 80"* — turning a rejection into a path to fundability.

---

## 2. Goals and non-goals

### 2.1 Goals

**G1 — Collapse discovery time from weeks to seconds.** A CSR director states a mandate in natural language and receives a ranked, eligibility-filtered shortlist with justifications in under a second.

**G2 — Make credibility auditable rather than asserted.** Every point of every trust score traces to a specific document page, and the trail is tamper-evident.

**G3 — Detect coordinated fraud, not just missing paperwork.** Identify shell networks and statistically implausible claims, which a document checklist cannot.

**G4 — Fulfil mandates that no single NGO can deliver.** Propose optimal partner combinations with a defensible budget split.

**G5 — Improve the supply side.** Give every NGO an actionable, quantified path to becoming corporate-ready.

### 2.2 Explicit non-goals for this build

Naming these protects the schedule and, said out loud, reads as judgement rather than omission.

| Not doing | Why | What we say if asked |
|---|---|---|
| Live MCA / NGO-Darpan API verification | No open public API exists for programmatic CSR-1 or Darpan verification. | "The verifier is an interface. Format validation and cross-document consistency ship now; a registry integration drops in behind the same interface without touching scoring." |
| Payment or fund disbursement | Regulated, out of scope, and adds nothing to the judged demo. | "We end at RFP dispatch. Disbursement is a banking integration, deliberately downstream of us." |
| Production authentication (OIDC/SSO) | Hours spent here are invisible to judges. | "Role-scoped access is enforced in the API today via a demo role header; swapping in JWT/OIDC is a middleware change." |
| Model fine-tuning or training a custom embedding model | Zero benefit at this corpus size; large risk. | "We use a pretrained sentence encoder with affine calibration fitted on our corpus. Fine-tuning needs labelled match data we don't yet have." |
| Mobile-native app | Buyer persona works at a desk. | "Responsive down to tablet. The buyer is a compliance professional on a laptop." |
| Multilingual mandate intake | Real need, but a whole workstream. | "The encoder has multilingual siblings — a model swap, not a rearchitecture. Out of scope for 48 hours." |

---

## 3. Users

### 3.1 Primary — Corporate CSR Director *(the buyer)*

Owns an annual mandate: a budget fixed by statute, board-approved thematic pillars, often specific geographies tied to plant or operational locations. Measured on deployed-and-defensible spend, not on shortlist size. Her real fear is not picking a suboptimal partner — it is a partner that becomes an audit finding or a news story.

*Jobs to be done:* translate a board mandate into a fundable shortlist; prove to a compliance officer that each partner is legitimate, with evidence; cover a multi-district, multi-domain mandate without managing a dozen grantees; get money out of the door before year end.

*Success for her:* a defensible shortlist in one sitting, with the evidence pack already assembled.

### 3.2 Secondary — NGO Operations Head *(the supply)*

Runs real programmes on thin margins and chases recurring funding. Holds registrations in various states of renewal and reporting quality. Loses opportunities without ever knowing why — corporate rejection is silent.

*Jobs to be done:* be discoverable by corporates whose language differs from hers; understand what is blocking her from qualifying; know which single document would most improve her position.

*Success for her:* a specific, quantified next action instead of silence.

### 3.3 Tertiary — Auditor / CSR Consultant *(the verifier)*

Signs off, or reports to a board that did. Needs to reconstruct *why* a partner was selected, months after the fact, from evidence rather than recollection.

*Jobs to be done:* trace any score to its source document; confirm the trail has not been edited; reproduce a historical score exactly.

*Success for her:* every number is clickable down to a document page, and the log is tamper-evident.

---

## 4. Functional requirements

Each requirement carries an **ID**, a **tier** (P0 = demo doesn't exist without it, P1 = differentiator, protect it, P2 = build if ahead, otherwise ship on fixtures), an **owner** (A = ML, B = Backend, C = Frontend) and **acceptance criteria** that are objectively checkable. "Looks good" is not an acceptance criterion.

### Module A — Ingestion and structured extraction

| ID | Requirement | Tier | Owner |
|---|---|---|---|
| **FR-A1** | Accept drag-and-drop upload of PDF and DOCX for corporate mandates, NGO proposals and compliance certificates. Max 20 MB, reject other types with a clear message. | P0 | B + C |
| **FR-A2** | Extract text with **page anchors** — every extracted span retains its page number and character offsets so it can be cited later. | P0 | B |
| **FR-A3** | Detect a document's kind automatically (mandate / proposal / CSR-1 / 12A / 80G / audited financials / impact report) and report `extraction_confidence`. | P1 | B |
| **FR-A4** | Extract structured mandate fields from free text: domains, budget, target districts and states, duration, beneficiary profile, preferences. Report **per-field confidence** and emit `clarifying_questions[]` for low-confidence fields. | P1 | A |
| **FR-A5** | Natural-language chat intake: the director types a sentence; the system returns a populated, editable structured mandate. Must work with an LLM *and* degrade to a deterministic rule/regex extractor when offline. | P1 | A + C |
| **FR-A6** | Generate and cache embeddings for every NGO proposal at seed time; commit them as an artefact. No NGO embedding is computed at request time. | P0 | A |
| **FR-A7** | Scanned documents with no text layer are flagged and scored at reduced extraction confidence rather than silently yielding empty fields. | P2 | B |

**Acceptance criteria.** A1: a 12-page PDF and a DOCX both upload and return `page_count` and non-empty text; a `.txt` is rejected with `UNSUPPORTED_MEDIA_TYPE`. A2: for any extracted registration number, the API returns its page and a ±120-character snippet, and the snippet genuinely contains the number. A4: on the ten canned mandate strings in `ml/tests/fixtures/mandates.json`, ≥ 8 extract budget, ≥ 1 domain and ≥ 1 geography correctly; any field below 0.6 confidence produces a clarifying question. A5: with the network disabled, the same ten strings still parse via the fallback path. A6: `/api/health` reports `index_ready: true` within 5 s of a cold start with no network.

### Module B — Semantic matching and ranking

| ID | Requirement | Tier | Owner |
|---|---|---|---|
| **FR-B1** | Rank NGOs by the composite score in `00-PROJECT-CONTEXT.md §5.6`, with configurable weights supplied per request. | P0 | A |
| **FR-B2** | Display a **calibrated** semantic score (§5.1), never raw cosine, while ranking on raw cosine. Return both. | P0 | A |
| **FR-B3** | Exclude `INELIGIBLE` NGOs (no valid CSR-1) from results entirely and report `excluded_ineligible_count`. | P1 | A + B |
| **FR-B4** | Generate a three-part justification per match — domain synergy, scale fit, geographic overlap — each grounded in a specific fact from the NGO's record, never a generic template sentence. | P0 | A |
| **FR-B5** | **Keyword baseline mode**: `use_keyword_baseline: true` runs a naive token-overlap matcher and returns `keyword_baseline_comparison` naming which NGOs keyword search would have missed. | P1 | A + C |
| **FR-B6** | **Consortium engine**: when no single NGO reaches adequate coverage, propose sets of 2–3 with coverage, redundancy, trust-weighted score, coordination cost, per-member unique units and an absorptive-capacity-capped budget split (§5.8). | P1 | A |
| **FR-B7** | Return the **Pareto frontier** of non-dominated partners over (semantic, trust, cost efficiency). | P2 | A |
| **FR-B8** | Return **rank stability** — probability each top result stays in the top 1 / top 3 across 1,000 Dirichlet-resampled weightings. | P2 | A |
| **FR-B9** | **Unmatched guard**: if best raw cosine < 0.28, return `unmatched_warning` with the closest adjacent capability instead of a misleading ranked list. | P2 | A + C |
| **FR-B10** | Auto-tag mandates and NGOs with UN SDG alignment by embedding similarity against goal descriptions. | P2 | A |

**Acceptance criteria.** B1: two mandates with different geographies produce demonstrably different orderings, and passing `weights` changes the order. B3: the four seeded NGOs lacking CSR-1 never appear in any `/api/match` response, and the count is reported. B4: no two NGOs in one response share an identical justification string, and each justification cites at least one number or place name from that NGO's record. B5: on the demo mandate, keyword mode returns strictly fewer results than semantic mode and `missed_by_keyword` is non-empty. B6: on the seeded unfillable mandate, at least one consortium reaches `coverage ≥ 0.95` while the best single NGO is below 0.70; every member satisfies `trust ≥ 55`; every member has `unique_units ≥ 1`; the sum of shares plus `unallocated_inr` equals the mandate budget exactly. B8: rank-stability probabilities lie in [0,1] and `p_top3 ≥ p_top1` for every entry.

### Module C — Trust index and Fraud Shield

| ID | Requirement | Tier | Owner |
|---|---|---|---|
| **FR-C1** | Compute a 0–100 trust index from four freshness-adjusted pillars per §5.2, and assign one of five badges by the exact thresholds given there. | P0 | B |
| **FR-C2** | Extract and format-validate CSR-1, 12A, 80G, Darpan ID and (conditionally) FCRA from uploaded documents. | P0 | B |
| **FR-C3** | Treat CSR-1 as a **hard eligibility gate**, setting status `INELIGIBLE` and badge *Ineligible for CSR Funds*. | P1 | B |
| **FR-C4** | **Evidence ledger**: every pillar contribution stores `{doc_id, page, snippet, char_offsets, extraction_confidence}`, exposed via `/api/ngos/{id}/trust`. | P1 | B |
| **FR-C5** | Serve a rendered PNG of any cited document page so the UI can display the evidence itself. | P1 | B |
| **FR-C6** | **Cohort-relative anomaly detection** using median/MAD robust z-scores within (domain × budget tier × region), with a minimum cohort size of 5 and directional flag text (waste vs claim-inflation). | P1 | A |
| **FR-C7** | **Shell-network detection**: graph over shared address / phone / trustee / bank / email-domain identifiers; flag components with ≥ 2 members sharing ≥ 2 distinct identifier types; cap trust at 40; expose the ring via `/api/ngos/{id}/network`. | P1 | B |
| **FR-C8** | **Counterfactual engine**: return top-3 ranked-by-Δ/effort actions with exact point deltas, resulting badge, an `achievable_ceiling`, and a strict actionable / structural / never-show classification (§5.9). | P1 | A + B |
| **FR-C9** | **Freshness decay** with documented per-pillar half-lives, surfaced as "last verified N months ago". | P2 | B |
| **FR-C10** | **Document forensics**: cross-document identifier agreement, financial-year consistency, arithmetic reconciliation of stated totals, PDF metadata plausibility, missing-text-layer detection. Each produces a named warning, not a silent adjustment. | P2 | B |
| **FR-C11** | **Score reproducibility**: every score carries `algorithm_version` and `input_hash`; recomputation from the same inputs yields a byte-identical result. | P2 | B |
| **FR-C12** | **Hash-chained audit log**: each entry stores the hash of the previous entry; a verification endpoint confirms chain integrity. Auditor role only. | P2 | B |

**Acceptance criteria.** C1: for a hand-computed reference NGO, the API's trust score matches a spreadsheet computation to within ±0.5 points. C3: the seeded no-CSR-1 NGOs return status `INELIGIBLE` and are absent from match results. C4: every pillar in every dossier has ≥ 1 evidence reference, or is explicitly marked `no_evidence` with the pillar contributing 0 — never a number with nothing behind it. C6: the two seeded claim-inflation NGOs are flagged with `|z| > 3` on `cost_per_beneficiary` and the flag text says *below* cohort; an NGO in a cohort of 3 returns `insufficient_cohort` and receives no penalty. C7: the seeded three-NGO ring is returned as one component listing all three members and ≥ 2 shared identifier types, all three capped at trust ≤ 40. C8: for the seeded 61-point NGO, uploading the CSR-1 renewal produces exactly the delta the counterfactual predicted (±1 point) — **this is the demo's credibility test; if prediction and outcome disagree on stage, the feature is worse than not having it.** C12: tampering with any historical log row makes chain verification fail.

### Module D — GIS impact and gap analysis

| ID | Requirement | Tier | Owner |
|---|---|---|---|
| **FR-D1** | Render an interactive map of NGO operational footprints at state and district level, filterable by domain, trust band and badge. | P0 | C |
| **FR-D2** | **Demand-vs-supply layer**: choropleth contrasting verified-partner density against a need index, with NITI Aayog Aspirational Districts marked. Districts with high need and zero verified partners are visually unmistakable — the "CSR deserts". | P1 | B + C |
| **FR-D3** | Radius filter: click a point, set a radius, list verified NGOs of a chosen domain inside it. | P1 | C |
| **FR-D4** | Consortium coverage overlay: each member's contribution to the mandate shown in a distinct colour, with uncovered requirement cells visibly outlined. | P2 | C |
| **FR-D5** | Map degrades gracefully with no internet: bundled district GeoJSON and either cached or blank tiles, never a broken grey rectangle. | P1 | C |

**Acceptance criteria.** D1: all seeded NGOs render; applying a domain filter changes the visible set. D2: `gap_score` is computed for every district in the GeoJSON and at least three Aspirational Districts show zero verified partners. D3: a 50 km radius around a named industrial location returns a result set consistent with an independent haversine check. D5: with the network disabled, district boundaries still render and the app does not throw.

### Module E — Corporate Match Console

| ID | Requirement | Tier | Owner |
|---|---|---|---|
| **FR-E1** | Chat-style mandate intake with streaming feedback, editable extracted fields, per-field confidence chips and inline clarifying questions. | P1 | C |
| **FR-E2** | Ranked partner deck: cards showing calibrated match %, trust badge, trust score, budget request, cost per beneficiary, base district and flag chips. | P0 | C |
| **FR-E3** | Trust dossier drawer: four pillar bars → expand a pillar → evidence list → click evidence → **the rendered document page appears with the cited snippet highlighted**. | P1 | C |
| **FR-E4** | **Keyword ⇄ semantic toggle** with a visible delta banner ("keyword search would have missed 2 of your top 3"). | P1 | C |
| **FR-E5** | Consortium view: coverage bars that fill per member, redundancy percentage, budget-split donut, absorptive-capacity cap indicator, and a one-line rationale. | P1 | C |
| **FR-E6** | **Counterfactual coach** in NGO role: a what-if panel where toggling prospective evidence animates the gauge and badge live. | P1 | C |
| **FR-E7** | Weight sliders that re-run the match, with rank-stability shown so the director sees which recommendations are robust. | P2 | C |
| **FR-E8** | Side-by-side comparison of up to three NGOs across trust pillars, admin ratio, cost per beneficiary, districts and past corporate collaborations. | P2 | C |
| **FR-E9** | One-click RFP dispatch to one NGO or a whole consortium, generating a one-page partner dossier PDF. | P2 | B + C |
| **FR-E10** | **Live latency badge** showing the real `latency_ms` from the last match call. | P2 | C |
| **FR-E11** | **"₹ at risk" summary**: rupees that would have been allocated to a sub-threshold-trust partner under naive keyword matching. | P1 | C |
| **FR-E12** | Role switcher (corporate / NGO / auditor) demonstrating scoped access, with corporate review notes invisible outside the corporate role. | P2 | B + C |
| **FR-E13** | Calibration chart of predicted vs realised impact from simulated completed projects. | P2 | B + C |

**Acceptance criteria.** E2: the full deck renders in under 300 ms after the API responds, with skeleton loaders during flight and no layout shift on arrival. E3: three clicks maximum from a trust number to a visible document page. E4: toggling re-runs the query and the delta banner reflects the actual API response, not a hardcoded string. E6: the animated gauge lands on exactly the value `/api/ngos/{id}/counterfactual` returned. E11: the figure is derived from the live response, and you can explain its derivation in one sentence on stage.

### Module F — Demo resilience *(judged indirectly, but it decides whether you get judged at all)*

| ID | Requirement | Tier | Owner |
|---|---|---|---|
| **FR-F1** | `DEMO_MODE=true` serves deterministic responses from committed fixtures with no model load and no database. | P1 | B |
| **FR-F2** | `frontend/fixtures/` contains a captured response for every endpoint used in the demo; the frontend falls back to them automatically on any API failure and shows a small "offline fixtures" indicator. | P1 | C |
| **FR-F3** | Embedding model cache and precomputed NGO embeddings are committed; the backend starts and matches correctly with networking fully disabled. | P0 | A + B |
| **FR-F4** | A single `seed --reset` command restores the exact demo state, including all planted fraud cases, in under 60 seconds. | P1 | B |
| **FR-F5** | One "Reset demo" control in the UI returns the app to its opening state between judging passes. | P2 | C |

**Acceptance criteria.** F3 is verified by literally disabling the network adapter and running the full demo click-path end to end. **Do this at Hour 42, not at Hour 47.**

---

## 5. Non-functional requirements

| ID | Requirement | Target | How it is verified |
|---|---|---|---|
| **NFR-1** | Match latency across 1,000 NGO records | **p95 < 800 ms** end to end; internal scoring < 150 ms | `latency_ms` logged on every call and shown in the UI; a `pytest` benchmark over 1,000 synthetic records asserts the bound |
| **NFR-2** | Cold start with no network | Ready in < 15 s | `/api/health` returns `index_ready: true` with the adapter disabled |
| **NFR-3** | Role-scoped access | NGO sees only its own dossier; corporate review notes never leave the corporate role; auditor is read-only | One `pytest` per role asserting a 403 on each forbidden path |
| **NFR-4** | Auditability | 100% of trust pillars carry an evidence reference or an explicit `no_evidence` marker | Test iterates every seeded NGO and asserts the invariant |
| **NFR-5** | Reproducibility | Identical inputs ⇒ identical score, byte for byte | Recompute-and-compare test over all seeded NGOs |
| **NFR-6** | Responsive layout | Correct at 1920, 1440 and 1024 px wide; usable on tablet | Manual pass at all three widths before Hour 44 |
| **NFR-7** | Accessibility | Keyboard-navigable primary flow; WCAG AA contrast; no information conveyed by colour alone — every badge carries a text label beside its colour | Keyboard-only walkthrough of the demo path; contrast checked on badge colours |
| **NFR-8** | Graceful degradation | No unhandled promise rejection or blank screen on any API failure | Kill the backend mid-demo-path; the UI must continue on fixtures |
| **NFR-9** | Determinism | Seeded data and scores are identical on every machine | Fixed random seed in the generator; embeddings committed, not regenerated |

Note on NFR-7: the badge colours in §5.2 carry meaning, so each must always render with its text label. Roughly one in twelve men has some form of colour-vision deficiency; a judge may be one of them.

---

## 6. Data model (conceptual)

Field-level schemas belong to Task B; this is the shared vocabulary. Money is integer rupees with an `_inr` suffix; identifiers are prefixed strings (`ngo_014`, `mnd_01`, `doc_07`, `cns_1`).

**`ngo_profiles`** — identity (name, registration numbers, Darpan ID, PAN), contact and address fingerprints, trustee list, bank fingerprint, `primary_domain` + `secondary_domains`, `districts_covered[]` with lat/lng, financials (`admin_expense_inr`, `programme_expense_inr`, `total_expense_inr`, `beneficiaries_reached`, `max_grant_managed_inr`), track record (`projects_total`, `projects_completed`, `milestones_met`, `milestones_total`, `years_active`), `proposal_text` + `embedding_ref`, `trust` sub-document, `status ∈ {ACTIVE, INELIGIBLE, FLAGGED}`.

**`corporates`** — name, sector, CSR budget, thematic pillars, plant locations, `foreign_funded` flag.

**`mandates`** — `corporate_id`, `raw_text`, extracted fields with per-field confidence, `requirement_units[]` (the domain × district cells with weights), `embedding_ref`, `created_at`.

**`documents`** — `ngo_id`, `kind`, `page_count`, `text_by_page[]`, `extracted{}`, `extraction_confidence`, `forensics{}`, `uploaded_at`, storage path.

**`compliance_audit`** — one row per pillar per NGO: `pillar`, `raw`, `effective`, `freshness_days`, `evidence[]`, `computed_at`, `algorithm_version`, `input_hash`.

**`shell_networks`** — `component_id`, `member_ngo_ids[]`, `shared_identifier_types[]`, `edges[]`, `flagged_at`.

**`matches`** — persisted match runs for auditability: `mandate_id`, `weights`, `results[]`, `algorithm_version`, `latency_ms`, `run_at`.

**`outcomes`** — `ngo_id`, `mandate_id`, `predicted_impact`, `realised_impact`, `completed_at`.

**`audit_log`** — append-only: `seq`, `actor_role`, `action`, `entity_id`, `payload_hash`, `prev_hash`, `this_hash`, `at`.

**`review_notes`** — `corporate_id`, `author`, `ngo_id`, `body`. Visible only to the authoring corporate; this collection is the concrete thing NFR-3 protects.

---

## 7. Technical stack and the reasoning behind each choice

| Layer | Choice | Why this and not the alternative |
|---|---|---|
| Frontend | **Next.js 14 (App Router), Tailwind CSS, Lucide icons, Recharts** | Fast to build, server components keep the first paint quick, and the team has prior React experience. Recharts over D3 because we need four standard charts, not custom visualisation. |
| Mapping | **Leaflet + react-leaflet, OpenStreetMap tiles, bundled district GeoJSON** | Zero cost, no API key, no quota, and — decisively — it works offline with bundled boundaries. Mapbox would be prettier and would fail on venue wifi. |
| Backend | **Python 3.11 + FastAPI + Pydantic v2** | Same language as the ML layer, so embeddings, robust statistics and the consortium solver are a direct import rather than a service call. Async I/O handles concurrent document parsing. Automatic OpenAPI docs at `/docs` are a free credibility artefact to show judges. |
| Database | **MongoDB (Atlas free tier or local), with a vector-index adapter** | Document store matches our nested, irregular NGO profiles without migrations. Vector search sits behind an interface: `USE_LOCAL_INDEX=true` uses brute-force NumPy cosine (~15 ms at 1,000 records), `false` uses Atlas Vector Search. Being able to say "the index is an interface, so it scales by swapping the implementation" is worth more than either choice alone. |
| Embeddings | **`sentence-transformers/all-MiniLM-L6-v2`, local, cache committed** | 384 dimensions, ~80 MB, no API key, no rate limit, no network dependency during judging. Quality is more than adequate for CSR-domain text. An API embedding model is marginally better and one wifi hiccup from ending the demo. |
| Document parsing | **PyMuPDF (`fitz`)** for PDF text + page rendering, **python-docx** for DOCX | PyMuPDF gives us text with character offsets *and* page rasterisation from one dependency — which is exactly what the evidence drill-down needs. |
| Mandate NLU | LLM function-calling **with a deterministic regex/rule fallback** | The LLM path demos better; the fallback means the demo cannot die. Both paths must produce the same schema. |
| Statistics | **NumPy + SciPy** | Median/MAD robust z-scores, Dirichlet sampling for rank stability, haversine distances. No heavier ML dependency is justified. |
| PDF output | **ReportLab** | Partner dossier generation; well-understood, no browser dependency. |

**Deliberately rejected:** LangChain (an abstraction layer we do not need for one embedding call and one function call — it adds dependency weight and debugging surface for no gain at this size); a custom vector database (MongoDB plus NumPy is sufficient and one less service to start on stage); ChromaDB (fine tool, but a second datastore to seed, back up and keep consistent).

---

## 8. Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Scope overrun — seven half-working features instead of four polished ones** | High | Fatal | P0/P1/P2 tiers with a written cut order (`00-PROJECT-CONTEXT.md §7`). Feature freeze at Hour 40, enforced. |
| **Venue wifi fails during judging** | Medium | Fatal | Every model and dataset local and committed; `DEMO_MODE`; frontend fixtures; offline dry-run at Hour 42. |
| **Integration breaks late because the contract drifted** | High | Severe | Contract frozen at Hour 4. Task B publishes a mocked API returning contract-shaped stubs by Hour 8 so Task C is never blocked. Contract changes need all three to agree. |
| **Counterfactual prediction disagrees with the actual recomputed score on stage** | Medium | Severe | Both paths use one shared function from `setu_ml.counterfactual`. An automated test asserts predicted delta equals realised delta for every seeded NGO. |
| **Calibrated semantic score looks implausible (everything 95%, or everything 40%)** | Medium | Moderate | Fit `LO`/`HI` on the real seed corpus at Hour 12 and eyeball the distribution across all mandate/NGO pairs before building UI on top of it. |
| **Seed data doesn't actually contain the cases the demo narrates** | Medium | Severe | Write the demo narrative *first* (`06-PITCH-AND-DEMO-RUNBOOK.md`), then generate data to satisfy it, then assert the planted cases in tests. |
| **A judge asks about live registry verification and the answer sounds evasive** | High | Moderate | Rehearse the pluggable-verifier answer verbatim. Claiming live verification you don't have is far worse than scoping it honestly. |
| **Merge conflicts consume hours** | Medium | Moderate | Folder-level ownership; branch per person; nobody edits another's folder. |
| **One member gets blocked and stalls silently** | Medium | Severe | Checkpoint calls at Hours 8, 16, 24, 32, 40. Blocked for more than 45 minutes means say so immediately, not after four hours. |

---

## 9. Evaluation alignment

> ⚠️ The official rubric could not be read — the problem-statement PDF was not available in this session. The mapping below is **inferred from typical hackathon criteria**. Re-supply the PDF and this section should be rewritten against the real weightings before you finalise the deck.

| Likely criterion | How SETU answers it | Where to show it |
|---|---|---|
| **Problem understanding / domain depth** | Statutory framing (Section 135, Schedule VII), correct treatment of CSR-1 as a legal gate rather than a score, and the distinction between the company's 5% admin cap and the NGO's own overhead ratio. | Demo beat 5 and the Q&A. This is where domain knowledge separates you from a generic matching app. |
| **Technical sophistication** | Weighted set-cover consortium optimisation with redundancy penalty and capacity constraints; graph-based shell-network detection; robust cohort statistics; Monte Carlo rank stability; Pareto dominance filtering. | Demo beats 6 and 7. |
| **Innovation / novelty** | Consortium matching, counterfactual coaching, shell-network detection, demand-vs-supply gap mapping. Say plainly that embeddings are the baseline and these are the contribution — pre-empting the "isn't this just cosine similarity" question rather than waiting for it. | Demo beats 3, 6, 7, 8. |
| **Completeness / working demo** | End-to-end flow with no dead ends, running offline, reproducible from one seed command. | Whole demo. |
| **Business viability** | A named buyer with a legal obligation and audit exposure; free supply side; the "₹ at risk" number that translates the product into a CFO's language. | Demo beat 10. |
| **Presentation** | Four minutes, five rehearsed wow beats, honest answers ready for the hard questions including "what's your weakest point". | Rehearsed three times minimum. |

---

## 10. Success metrics for the 48 hours

**Must be true or the build has failed:**
- The full ten-beat demo runs end to end with the network adapter disabled.
- Match p95 latency under 800 ms over 1,000 records, displayed live.
- Every trust pillar of every seeded NGO resolves to a document page or an explicit `no_evidence`.
- The consortium engine solves the seeded unfillable mandate with coverage ≥ 0.95.
- The seeded shell ring is detected with all three members and ≥ 2 shared identifier types.
- The counterfactual's predicted delta matches the recomputed score within 1 point.
- `seed --reset` restores exact demo state in under 60 seconds.
- All three members can explain any part of the system, including the parts they did not build. **Judges pick who to question, and a member who cannot explain their own product's core algorithm undoes a lot of good work.**

**Should be true:**
- Pareto frontier and rank stability rendered from live data.
- Document forensics producing named warnings on the seeded tampered document.
- Calibration chart populated from simulated outcomes.
- RFP dossier PDF generating cleanly for a consortium.

---

## 11. Open questions

1. **The official rubric and deck template** — re-upload needed (§9).
2. **Third member's name and strengths** — Task C spans UI craft, data visualisation and GIS. If their strength is visual design, have them start on the deck early; if it is data work, have Task B hand over the geo endpoints sooner.
3. **Real national CSR spend figure for the opening slide** — must be pulled from `csr.gov.in` with the financial year cited. Do not pitch an unsourced number.
4. **Do you want a live-hosted URL?** Vercel for the frontend plus a tunnel for the API is roughly 90 minutes and is genuinely optional. `localhost` demos fine. Only do this if you are ahead at Hour 40, and never make the demo depend on it.

---

*`01-PRD.md` · v1.0 · algorithm_version `setu-1.0.0` · authoritative formulas in `00-PROJECT-CONTEXT.md §5`*

