# SETU — Master Project Context

**Read this file before you write a single line of code. All three of you.**

> **Product name:** SETU (Hindi: *bridge*) — "the bridge between corporate CSR capital and verified grassroots capacity."
> Earlier working title was *SynergyCSR*. **SETU is now the only name we use** — in the repo, the UI, the deck and the pitch. Consistency matters to judges.
>
> **Track:** Corporate Social Responsibility — Problem Statement 2 (NGO–Corporate CSR Matching)
> **Team size:** 3 · **Window:** 48 hours · **Deliverable:** working web app + pitch

---

## 0. How to use these documents

| File | What it is | Who reads it |
|---|---|---|
| `00-PROJECT-CONTEXT.md` | This file. Shared brain: domain facts, formulas, frozen API contract, ownership rules. | **All three, start to finish** |
| `01-PRD.md` | Formal requirements with acceptance criteria. The "what". | All three, skim then reference |
| `02-BUILD-PLAN-48H.md` | Hour-by-hour schedule, checkpoints, cut list. | All three, pinned open |
| `03-TASK-A-ML-INTELLIGENCE.md` | Ready-to-paste build prompt — matching + trust intelligence library. | **Piyush** |
| `04-TASK-B-BACKEND-TRUST.md` | Ready-to-paste build prompt — data, documents, API, compliance forensics. | **Vaishnavi** |
| `05-TASK-C-FRONTEND-GIS.md` | Ready-to-paste build prompt — console, visualisation, GIS, demo polish. | **Third member** |
| `06-PITCH-AND-DEMO-RUNBOOK.md` | 3-minute script, click-path, judge Q&A, failure recovery. | All three, rehearse together |
| `README.md` | Repo front page + setup commands. | Judges and graders |

**Working method:** each task file is written as a *prompt*. Open your AI IDE (Antigravity / Claude Code / Cursor) in the repo, paste **Section 0 of this file plus your whole task file**, and work through the numbered work items in order. Do not skip ahead — later items depend on earlier ones.

> ⚠️ **One open item:** the hackathon problem-statement PDF and the `RECURSION_EDITION_II_TEMPLATE.pdf` deck template were referenced but are **not present in this session** (the uploads folder is empty). Re-upload them and I will (a) map every PRD requirement line-by-line to the official evaluation rubric and (b) rebuild the deck inside the official template. Until then, treat the rubric alignment in `01-PRD.md §9` as *inferred, not confirmed*.

---

## 1. The problem, stated so a judge nods along

India is the **first country in the world to make corporate social responsibility spending legally mandatory** — Section 135 of the Companies Act, 2013. A company crossing **any** of these thresholds in a financial year is caught by it:

- net worth ≥ ₹500 crore, **or**
- turnover ≥ ₹1,000 crore, **or**
- net profit ≥ ₹5 crore

Such a company must spend **at least 2% of its average net profit of the preceding three financial years** on prescribed social activities (Schedule VII: education, healthcare, sanitation, environment, livelihoods, and more). Unspent money does not simply roll over quietly — under the 2021 amendments it must be transferred to a specified fund or parked in an *Unspent CSR Account*, and non-compliance is penalised.

So thousands of crores per year are legally obligated to move from corporate balance sheets into social projects. The money is not the bottleneck. **Trustworthy partner discovery is the bottleneck.**

Four failures compound:

**Discovery is manual.** CSR teams work from spreadsheets, referrals and cold email. A keyword search for "maternal health" misses an NGO whose proposal says "postpartum institutional delivery care" — same work, different vocabulary. Good partners stay invisible.

**Verification is slow and shallow.** Before a rupee moves, a compliance officer must establish that the NGO can *legally* receive CSR money at all, and that it will not embarrass the board. That means CSR-1, 12A, 80G, Darpan ID, audited financials, and a track record. Assembling that dossier by hand takes weeks per candidate.

**Shell and paper NGOs exist.** Entities that exist mainly on paper absorb funds without delivering. They are hard to spot one at a time — they become visible when you look at *networks* (shared addresses, shared trustees, shared bank details across supposedly unrelated registrations) and at *statistical outliers* (an administrative overhead ratio five times its peer group's).

**Mandates rarely fit one NGO.** A real mandate reads "₹50 lakh for maternal health and clean water across three districts of Odisha." Almost no single grassroots NGO covers all of that. So the mandate either gets shrunk to fit one partner, or gets split by hand over weeks of coordination, or is dropped.

The consequence is the outcome nobody wants: **budget that is legally committed but not deployed, or deployed badly.**

> 📌 **Before you pitch:** the statutory facts above are stable, but any *rupee figure* you quote for national CSR spend or unspent funds must be pulled fresh from the MCA National CSR Portal (`csr.gov.in`) and cited on the slide with the financial year. A judge who works in this sector will check. One correctly-cited number beats five vague ones. Do not invent statistics.

---

## 2. What SETU does — one paragraph

A CSR director types their mandate in plain English. SETU converts it into a structured mandate, embeds it, and finds NGOs whose *meaning* matches — not whose keywords match. Every candidate is scored on an evidence-anchored 0–100 trust index built from real Indian compliance artefacts, cohort-relative financial anomaly detection, and shell-network graph analysis; NGOs that cannot legally receive CSR funds are excluded outright rather than merely ranked low. When no single NGO can cover the mandate, SETU assembles a **consortium** of two or three complementary partners, penalises overlap, respects each partner's absorptive capacity, and proposes a budget split. Every score component links back to the exact page of the source document it came from. And NGOs that fall short are not silently rejected — they are told precisely which document would raise their score by how much.

**One-liner for the pitch:**
> *SETU turns India's spreadsheet-driven CSR allocation into a verified marketplace: semantic mandate matching, forensic fraud detection on MCA compliance artefacts, and a consortium engine that funds what a single NGO can't deliver alone.*

**Backup one-liner (if the room is non-technical):**
> *We don't just tell corporates which NGO to fund. We tell them why they can trust it, we prove it with the document, and we tell the NGOs that missed out exactly how to become fundable.*

---

## 3. Domain glossary — learn these, judges will test you

| Term | What it actually is | Why SETU cares |
|---|---|---|
| **Section 135, Companies Act 2013** | The clause creating mandatory CSR spend (2% of 3-year average net profit) for companies over the net-worth / turnover / profit thresholds. | This is *why* our buyer exists. It's a legal obligation, not charity. |
| **Schedule VII** | The statutory list of permitted CSR activity categories. Spend outside it doesn't count as CSR. | Our domain taxonomy maps to Schedule VII, not to arbitrary categories. |
| **CSR-1** | Form filed with the Ministry of Corporate Affairs (MCA) that registers an implementing agency to receive CSR funds. Mandatory since 1 April 2021. | **Hard legal gate.** No valid CSR-1 → the NGO *cannot* legally receive CSR money → we mark it `INELIGIBLE` and exclude it from results. Not "low score". Excluded. |
| **12A registration** | Income Tax registration granting the NGO exemption on its own income. | Baseline legitimacy signal. |
| **80G registration** | Lets the *donor* claim a deduction. Renewable, not perpetual. | Baseline legitimacy + it's the one corporates ask about first. |
| **Darpan ID** | Unique NGO identifier from NITI Aayog's NGO-Darpan portal. | Cross-checkable national identity — anchors an NGO to a government record. |
| **FCRA** | Foreign Contribution (Regulation) Act registration — needed to accept foreign funds. | Only relevant for MNC subsidiaries routing foreign money. Conditional pillar, not mandatory. |
| **Impact assessment** | Independent evaluation of a CSR project. Required by the CSR Rules for larger obligations/projects. | Feeds our External Verification pillar; explains *why* corporates need documented outcomes. |
| **Administrative overhead** | Two different things — don't conflate them: (a) the *company's* CSR admin overhead, capped at 5% of its CSR expenditure by the CSR Policy Rules; (b) the *NGO's* own admin-to-programme expense ratio, which has no statutory cap but has strong sector norms. | We score (b). Knowing that (a) exists and is a different number is exactly the detail that makes a judge believe you. |
| **Aspirational Districts** | NITI Aayog's programme identifying India's most under-developed districts (112 in the original cohort). | Ground truth for the "need" side of our demand-vs-supply map. Real data, not invented. |
| **Vector embedding** | A text passage compressed into a fixed-length list of numbers that encodes meaning, so semantically similar text lands nearby. | Lets "free girls' education" match "shiksha abhiyan for rural adolescent women". |
| **Cosine similarity** | Cosine of the angle between two vectors; 1 = same direction, 0 = unrelated. | Our semantic score. Note: on our model, *related* text sits around 0.35–0.75, so we calibrate before displaying — see §5.1. |
| **Consortium matching** | Selecting a *set* of NGOs that jointly satisfy a mandate one NGO cannot, with the budget split between them. | Our headline differentiator. It's a weighted set-cover problem, not a sort. |
| **Counterfactual score** | "If you did X, your score would become Y." | Turns a rejection into a roadmap. Our second headline differentiator. |
| **Absorptive capacity** | The largest grant an organisation can realistically manage, inferred from its history. | Stops the engine from handing ₹40 lakh to an NGO that has never managed more than ₹8 lakh. Very few teams will think of this. |
| **RFP** | Request for Proposal — the formal "send us your detailed workplan and budget" step. | The conversion action at the end of our funnel. |

---

## 4. Architecture and ownership

```
┌──────────────────────── TASK C · frontend/ (Next.js 14) ───────────────────────┐
│  Chat Mandate Intake   Ranked Deck   Trust Dossier   Consortium View          │
│  Counterfactual Coach  Comparison Matrix  Keyword⇄Semantic Toggle  GIS Map    │
└───────────────────────────────────┬───────────────────────────────────────────┘
                                    │  REST (contract frozen in §6)
┌───────────────────────────────────▼──── TASK B · backend/ (FastAPI) ──────────┐
│  Routers  ·  RBAC  ·  Hash-chained audit log  ·  Demo-mode fixture server     │
│  Document parsing (PDF/DOCX → text + page anchors)                            │
│  Compliance artefact extraction  (CSR-1 / 12A / 80G / Darpan / FCRA)          │
│  Trust pillar assembly + evidence ledger  ·  Tamper & consistency forensics    │
│  Shell-network graph detection            ·  MongoDB + vector index adapter   │
└───────────────────────────────────┬───────────────────────────────────────────┘
                                    │  direct Python import (no HTTP)
┌───────────────────────────────────▼──── TASK A · ml/setu_ml/ (pure library) ──┐
│  embeddings.py    extract.py     scoring.py      geo.py       justify.py      │
│  consortium.py    anomaly.py     counterfactual.py            calibrate.py    │
│  No database. No web framework. Pure functions + typed models + unit tests.   │
└───────────────────────────────────────────────────────────────────────────────┘
                                    ▲
                       outcomes feed back into calibration
```

**Why this split works for 3 people in 48 hours:** Task A ships a *library*, Task B ships a *service*, Task C ships an *interface*. Task A never touches HTTP or the database. Task C never touches Python. The only coupling is the API contract in §6 and the type definitions in `ml/setu_ml/types.py`. Three people can work at full speed without stepping on each other.

### Repository layout — you own your folder and nothing else

```
setu/
├─ ml/                          ← Piyush ONLY
│  ├─ setu_ml/{embeddings,extract,scoring,consortium,anomaly,
│  │           counterfactual,geo,justify,calibrate,types}.py
│  ├─ artifacts/                ← committed: model cache, ngo_embeddings.npy,
│  │                              calibration.json, sdg_vectors.npy
│  ├─ tests/
│  └─ pyproject.toml
├─ backend/                     ← Vaishnavi ONLY
│  ├─ app/{main,config,db,security,audit}.py
│  ├─ app/{models,routers,services,parsing}/
│  ├─ seed/{seed_ngos.py,make_mock_pdfs.py,data/}
│  └─ requirements.txt
├─ frontend/                    ← third member ONLY
│  ├─ app/  components/  lib/  fixtures/
│  └─ public/geo/districts.geojson
├─ docs/                        ← these 8 files
└─ .env.example
```

**Boundary rule:** if a change you need lives in someone else's folder, message them — do not edit it. If a change you need alters the API contract in §6, it must be agreed by all three and this file must be updated in the same commit. An unannounced contract change is the single most likely way to lose four hours.

---

## 5. The scoring model — SINGLE SOURCE OF TRUTH

Every number the UI shows comes from here. If any of you implements a formula that differs from this section, the demo will contradict itself in front of judges. **Change this section first, then the code.**

Every score carries `algorithm_version` (string, e.g. `"setu-1.0.0"`) and `input_hash` (SHA-256 of the canonicalised inputs) so any score can be reproduced byte-identically later. Bump the version whenever a weight changes.

### 5.1 Semantic score — `sem ∈ [0,1]`

Raw cosine similarity between the mandate embedding `V_c` and the NGO proposal embedding `V_n`:

```
cos(V_c, V_n) = (V_c · V_n) / (‖V_c‖ · ‖V_n‖)
```

With `all-MiniLM-L6-v2`, genuinely related CSR text lands roughly in `0.35–0.75` and unrelated text still sits near `0.10–0.25`. Showing raw cosine as "a 42% match" would understate a great match and look broken. So we rank on raw cosine but **display a calibrated value**:

```
sem = clip( (cos - LO) / (HI - LO), 0, 1 )        LO = 0.15, HI = 0.80
```

`LO`/`HI` are fitted once on the seed corpus and stored in `ml/artifacts/calibration.json`. **This is an honest affine calibration, and you must be able to say so out loud** — "we rank on raw cosine and display a calibrated score fitted on our corpus, because raw cosine isn't a percentage." That sentence earns more credibility than a fake 97%.

**Unmatched guard:** if the best raw cosine across the whole network `< 0.28`, do **not** return a ranked list as if it were fine. Return `unmatched_warning` with the closest adjacent capability. Honest failure modes read as maturity.

### 5.2 Trust score — `T ∈ [0,100]`

```
T_base = 100 × ( 0.30·C + 0.30·F + 0.25·O + 0.15·E )
T      = clip( T_base − anomaly_penalty − shell_penalty , 0, 100 )
```

Each pillar is in `[0,1]` and each is **freshness-adjusted** before weighting:

```
pillar_effective = pillar_raw × ( 0.60 + 0.40 × freshness )
freshness        = 0.5 ^ ( evidence_age_days / half_life_days )
half_life_days   = 365 (compliance) · 540 (financial) · 730 (track record) · 540 (external)
```

The `0.60 +` floor means stale-but-real evidence is discounted, never annihilated. A score with old evidence surfaces in the UI as *"last verified 14 months ago"* rather than silently collapsing.

**C — Compliance Baseline (30%).** Weighted presence *and* format validity of artefacts:

| Artefact | Weight within C | Notes |
|---|---|---|
| CSR-1 | 0.40 | **Hard gate.** Absent/invalid ⇒ status `INELIGIBLE`, excluded from `/api/match` entirely. |
| 12A | 0.20 | Must parse a registration number + validity window. |
| 80G | 0.20 | Expired 80G scores 0.5 of its weight, not 0 — it's renewable. |
| Darpan ID | 0.10 | Format-validated and cross-checked against the annual report. |
| FCRA | 0.10 | **Conditional**: only counted when the mandate is flagged `foreign_funded`; otherwise C is renormalised over the remaining 0.90 so domestic NGOs are not punished for lacking FCRA. |

**F — Financial Efficiency (30%).** From the administrative overhead ratio `r = admin_expense / total_expense`:

```
r ≤ 0.10            → 1.00
0.10 < r ≤ 0.25     → 1.00 − 0.50 × (r − 0.10) / 0.15        # 1.00 → 0.50
0.25 < r ≤ 0.50     → 0.50 − 0.50 × (r − 0.25) / 0.25        # 0.50 → 0.00
r > 0.50            → 0.00
```

Also compute, store and display **cost per beneficiary** = `programme_expense / beneficiaries_reached`. It does not enter `F` directly (units differ wildly across domains) but it is the input to cohort anomaly detection in §5.4 and it is the single most intuitive efficiency number to show a judge.

**O — Operational Track Record (25%).** Never compute a raw completion rate — an NGO with one completed project out of one would score 100% and outrank a veteran. Use Laplace smoothing:

```
completion  = (projects_completed + 1) / (projects_total + 2)
milestone   = milestones_met / max(milestones_total, 1)
tenure      = min(years_active / 10, 1)
O           = 0.60·completion + 0.25·milestone + 0.15·tenure
```

**E — External Verification (15%).**

```
E = 0.40·has_third_party_audit + 0.30·has_impact_assessment
  + 0.20·has_peer_or_media_citation + 0.10·has_site_visit_log
```

**Badges** (drive the colour in the UI — Task C must use exactly these thresholds):

| `T` | Badge | Colour |
|---|---|---|
| ≥ 80 and no open flags | **Verified Elite** | emerald |
| 60 – 79 | **Standard Audited** | amber |
| 40 – 59 | **Verification Incomplete** | slate |
| < 40, or any shell flag | **High Risk — Review Required** | rose |
| CSR-1 missing/invalid | **Ineligible for CSR Funds** | rose, and excluded from match |

### 5.3 Geographic fit — `geo ∈ [0,1]`

```
geo = 0.60 × district_jaccard + 0.40 × exp( −min_haversine_km / 150 )

district_jaccard = |mandate_districts ∩ ngo_districts| / |mandate_districts ∪ ngo_districts|
```

The Jaccard term rewards precise district-level overlap; the exponential decay term prevents a hard cliff at a district border — an NGO 12 km outside the boundary is still useful. If the mandate specifies only a state, `district_jaccard` is computed over that state's districts present in the NGO's footprint.

### 5.4 Cohort-relative anomaly detection — `anomaly_penalty ∈ [0,15]`

Global outlier detection is wrong here: a large urban NGO and a rural micro-NGO have legitimately different cost structures. Bucket first, then compare **within cohort**:

```
cohort = (primary_domain, budget_tier, state_group)
budget_tier ∈ {<10L, 10L–50L, 50L–2Cr, >2Cr}
```

For each metric `m ∈ {admin_ratio, cost_per_beneficiary, beneficiaries_per_staff, growth_rate_yoy}` use a **robust** z-score (median/MAD, not mean/σ — a fraudster's own value drags the mean):

```
z = 0.6745 × (x − median_cohort) / MAD_cohort
```

Flag when `|z| > 3.0` (and require cohort size ≥ 5, otherwise report `insufficient_cohort` and apply no penalty — never penalise on thin data). Penalty `= min(15, 5 × number_of_flagged_metrics)`.

The direction matters and must be stated in the flag text: an admin ratio far *above* cohort is a waste signal; a cost-per-beneficiary far *below* cohort is a **claim-inflation** signal (implausibly cheap outcomes), which is the more interesting fraud pattern.

### 5.5 Shell-network detection — `shell_penalty ∈ {0, 20}` + hard cap

Real fraud rings are invisible one entity at a time and obvious as a graph. Build an undirected graph over NGOs, adding an edge whenever two organisations share a **normalised** identifier:

```
shared identifier types:
  address_fingerprint  (lowercased, punctuation-stripped, PIN-anchored)
  phone_e164
  trustee_name_normalised   (any overlap in the trustee/board list)
  bank_ifsc + account_last4
  email_domain              (ignore gmail/yahoo/outlook/rediff — allowlist these)
  PAN prefix (first 5 chars encode entity type + surname → weak signal, weight low)
```

Take connected components. Flag a component as `POSSIBLE_SHELL_NETWORK` when it has **≥ 2 members** *and* they share **≥ 2 distinct identifier types** (one shared landline is a coincidence; a shared address *and* a shared trustee *and* a shared bank account is a pattern). Effect: `shell_penalty = 20`, trust capped at **40**, badge forced to *High Risk*, and the UI must be able to show the other members of the ring.

This is the highest-leverage thing in the whole project. Almost no competing team will build it, it maps onto how financial-crime teams actually work, and it demos in five seconds: *"these three NGOs are supposedly unrelated. They share a registered address, a trustee, and a bank account. We caught them because we look at the network, not the row."*

### 5.6 Final composite — `S_final ∈ [0,1]`

```
S_final = 0.50 × sem + 0.30 × (T / 100) + 0.20 × geo
```

`INELIGIBLE` NGOs are filtered out *before* ranking, not ranked low.

**Defending the weights (rehearse this).** Do not say "we chose them because they felt right." Say:

> *"Any fixed weighting is a judgement call, so we measured how much it matters. We resample the weights from a Dirichlet distribution around (0.5, 0.3, 0.2) a thousand times and report rank stability — our top recommendation stays in the top three under 94% of plausible weightings. And the console lets the director move the sliders themselves, because a pharma company and an infrastructure company genuinely should weight trust and geography differently."*

That answer converts your weakest technical point into your strongest.

### 5.7 Pareto frontier

A single weighted number hides trade-offs. Alongside the ranked list, return the **non-dominated set** over `(sem, T, cost_efficiency)` — an NGO is dominated if another is at least as good on all three and strictly better on one. Typically 3–6 survive. Present as "these are the defensible choices; the rest are beaten on every axis."

### 5.8 Consortium engine

A mandate decomposes into **requirement units** — the cells of `domains × districts`, each with a weight (default uniform; the director can weight a district as priority). For a candidate set `K` of NGOs:

```
Coverage(K)    = Σ weight(u) for units u covered by at least one member   / Σ weight(u)
Redundancy(K)  = Σ weight(u) × (members_covering(u) − 1)  /  Σ weight(u) × members_covering(u)
TrustW(K)      = Σ (budget_share_i × T_i) / 100          # budget-weighted, not plain mean
CoordCost(K)   = 0.05 × (|K| − 1)

S_consortium = 0.45·Coverage + 0.30·TrustW + 0.15·(1 − Redundancy) − CoordCost
```

Hard constraints — reject any set violating these:
1. `|K| ≤ 3` (a corporate CSR team will not manage more than three grantees for one mandate)
2. every member `T_i ≥ 55` — **a weak link poisons the whole consortium**, and a corporate is liable for where the money went
3. every member must cover at least one requirement unit no one else in the set covers (no passengers)
4. `Coverage(K) > best single-NGO coverage + 0.10` — otherwise recommend the single NGO and say so

**Budget split** — proportional to covered requirement weight, then constrained by reality:

```
raw_share_i     = covered_weight_i / Σ covered_weight
absorptive_cap_i = 1.5 × max_grant_managed_historically_i
share_i         = min(raw_share_i × mandate_budget, absorptive_cap_i)
# redistribute any residual to members with headroom; if residual remains,
# report `unallocated_amount` honestly rather than silently over-granting
```

The absorptive-capacity cap is the detail that makes this look like it was designed by someone who has met an NGO. An organisation that has never managed more than ₹8 lakh should not be handed ₹40 lakh, and saying that out loud in the pitch lands hard.

**Solver:** greedy marginal-gain selection to seed, then exhaustive search over the top 12 candidates for `|K| ∈ {2,3}` (that's ≤ 286 combinations — trivially fast, and *optimal* within the shortlist, so you can honestly say "optimal over the shortlist" rather than "greedy"). Do not reach for an ILP library; you do not have the hours and you do not need it.

### 5.9 Counterfactual engine

For each **unmet or stale** evidence item `e` with intra-pillar weight `w_e` in pillar `p` (pillar weight `W_p`), the achievable gain is:

```
Δ_e = 100 × W_p × w_e × (0.60 + 0.40 × 1.0)   −   current_contribution_of_e
```

(the `freshness = 1.0` term reflects that newly-uploaded evidence is maximally fresh).

Split candidate actions into **actionable** and **structural**:

| Class | Examples | Show it? |
|---|---|---|
| Actionable now | upload CSR-1 renewal, upload FY25 audited statements, upload third-party impact assessment, refresh stale 80G | ✅ show with Δ |
| Structural / slow | obtain a fresh 12A registration, reduce admin overhead ratio, complete more projects | ⚠️ show as "longer-term", Δ shown but flagged with effort |
| Not actionable | change historical completion rate, change years active | ❌ never show — suggesting it is insulting and undermines trust in the tool |

Rank by `Δ / effort` where `effort ∈ {upload: 1, obtain registration: 5, change financial structure: 10}`, return the top 3, and render one plain sentence each:

> **+19 points** — Upload your renewed CSR-1 certificate. Your score would move from **61 → 80** and your badge from *Standard Audited* to *Verified Elite*.

Also return `achievable_ceiling` — the score if every actionable item were supplied — so the NGO sees the realistic maximum, not a fantasy 100.

### 5.10 Outcome feedback loop

When a funded project is marked complete, store `predicted_impact` vs `realised_impact`. Then:

1. Recompute the NGO's `O` pillar with the new data point (this is the real, non-hand-wavy feedback).
2. Maintain a **calibration curve**: bucket predictions into deciles and plot mean predicted vs mean realised. A well-calibrated system sits on the diagonal.
3. Nudge cohort priors — nothing more ambitious. Do **not** claim you "retrain the model"; with a synthetic dataset that claim will not survive one follow-up question. Claim exactly what you do: *"realised outcomes update the track-record pillar and we report our calibration honestly, so the score gets better-grounded with every completed project."*

---

## 6. API contract — FROZEN at Hour 4, changes require all three to agree

Base URL `http://localhost:8000`. All responses JSON. Demo role via header `X-Demo-Role: corporate | ngo | auditor` (production would be JWT/OIDC — say that if asked, don't pretend this is production auth).

Error envelope, always: `{"error": {"code": "STRING_CODE", "message": "human readable", "detail": {...}}}`

Every scored response carries `algorithm_version`, `input_hash`, `latency_ms`.

| Method | Path | Purpose | Owner |
|---|---|---|---|
| GET | `/api/health` | `{status, algorithm_version, demo_mode, ngo_count, index_ready, model_loaded}` — Task C polls this to show a readiness pill | B |
| POST | `/api/mandates/parse` | `{text}` → structured mandate draft + `confidence` per field + `clarifying_questions[]`. **Does not persist.** Powers the chat intake. | B wraps A |
| POST | `/api/mandates` | Persist a confirmed mandate → `{mandate_id}` | B |
| GET | `/api/mandates/{id}` | Fetch a mandate | B |
| POST | `/api/match` | The core call. See payload below. | B wraps A |
| GET | `/api/ngos` | `?domain=&state=&district=&trust_min=&badge=&q=&page=&limit=` → paginated summaries | B |
| GET | `/api/ngos/{id}` | Full profile | B |
| GET | `/api/ngos/{id}/trust` | Full trust dossier with per-pillar evidence references | B |
| GET | `/api/ngos/{id}/counterfactual` | `{current, achievable_ceiling, actions[]}` | B wraps A |
| GET | `/api/ngos/{id}/network` | Shell-network component: `{flagged, members[], shared_identifier_types[]}` | B |
| POST | `/api/documents/upload` | multipart → `{doc_id, kind_detected, extracted{}, page_count, warnings[], forensics{}}` | B |
| GET | `/api/documents/{doc_id}/pages/{n}.png` | Rendered page image so the UI can show the evidence itself | B |
| POST | `/api/verify` | `{ngo_id}` → re-run verification, return before/after score diff | B |
| GET | `/api/geo/coverage` | `?domain=&state=` → GeoJSON FeatureCollection, properties `{district, state, ngo_count, verified_count, need_index, is_aspirational, gap_score}` | B |
| GET | `/api/geo/nearby` | `?lat=&lng=&radius_km=&domain=&trust_min=` → NGOs inside the radius | B |
| POST | `/api/rfp` | `{mandate_id, ngo_ids[], message}` → `{rfp_id, status, dossier_url}` | B |
| GET | `/api/rfp/{id}/dossier.pdf` | One-page partner dossier PDF | B |
| POST | `/api/outcomes` | Simulate project completion → feeds §5.10 | B |
| GET | `/api/analytics/calibration` | Predicted-vs-realised buckets for the calibration chart | B |
| GET | `/api/audit` | `?entity_id=` → hash-chained audit entries. `auditor` role only. | B |

### `POST /api/match` — request

```json
{
  "mandate_id": "mnd_01",
  "mandate_inline": null,
  "top_k": 10,
  "mode": "both",
  "weights": { "semantic": 0.50, "trust": 0.30, "geo": 0.20 },
  "use_keyword_baseline": false,
  "include_pareto": true,
  "include_rank_stability": true,
  "foreign_funded": false
}
```

`mode` ∈ `"single" | "consortium" | "both"`. `use_keyword_baseline: true` runs the naive keyword matcher instead of embeddings — this powers the A/B toggle in the UI and is the cheapest high-impact demo device we have.

### `POST /api/match` — response (this exact shape; Task C builds against it)

```json
{
  "algorithm_version": "setu-1.0.0",
  "input_hash": "sha256:9f2c…",
  "latency_ms": 214,
  "mode_used": "both",
  "engine": "semantic",
  "excluded_ineligible_count": 3,
  "unmatched_warning": null,

  "results": [
    {
      "ngo_id": "ngo_014",
      "name": "Ashadeep Gramin Vikas Samiti",
      "final_score": 0.871,
      "semantic_score": 0.88,
      "semantic_cosine_raw": 0.687,
      "trust_score": 84,
      "trust_badge": "Verified Elite",
      "geo_score": 0.79,
      "budget_request_inr": 4200000,
      "base_district": "Kalahandi",
      "base_state": "Odisha",
      "districts_covered": ["Kalahandi", "Nuapada"],
      "cost_per_beneficiary_inr": 1180,
      "flags": [],
      "freshness_days": 96,
      "justification": {
        "domain_synergy": "Mandate pillar 'maternal healthcare' aligns with the NGO's documented work on postpartum institutional delivery care and ASHA-worker training.",
        "scale_fit": "Requests ₹42.0L against a ₹50.0L mandate (84%); largest grant previously managed was ₹38.0L, so this is within demonstrated absorptive capacity.",
        "geographic_overlap": "Covers 2 of the 3 target districts, including 1 NITI Aayog Aspirational District. Nearest field office is 34 km from the mandate centroid."
      },
      "evidence_summary": { "csr1": true, "reg_12a": true, "reg_80g": true, "darpan": true, "audit_fy": "2024-25" }
    }
  ],

  "consortiums": [
    {
      "consortium_id": "cns_1",
      "members": [
        { "ngo_id": "ngo_014", "name": "Ashadeep…", "trust_score": 84,
          "covers": [{ "domain": "maternal_health", "districts": ["Kalahandi","Nuapada"] }],
          "unique_units": 4, "budget_share_inr": 3250000, "share_pct": 65,
          "absorptive_cap_inr": 5700000, "capped": false }
      ],
      "coverage": 1.00,
      "redundancy": 0.08,
      "trust_weighted": 0.79,
      "coordination_cost": 0.05,
      "score": 0.842,
      "beats_best_single_by": 0.31,
      "unallocated_inr": 0,
      "rationale": "No single partner covers both maternal health and clean water across all three districts. This pair reaches full coverage with 8% overlap."
    }
  ],

  "pareto_front": ["ngo_014", "ngo_007", "ngo_022"],
  "rank_stability": { "ngo_014": { "p_top1": 0.71, "p_top3": 0.94 } },
  "keyword_baseline_comparison": {
    "keyword_result_count": 2,
    "semantic_result_count": 9,
    "missed_by_keyword": ["ngo_014", "ngo_022"],
    "headline": "Keyword search would have missed your best-scoring partner."
  }
}
```

**Field-naming rules, non-negotiable:** `snake_case` everywhere; all money in **paise-free integer rupees** with an `_inr` suffix; all scores in `[0,1]` **except** `trust_score` which is `0–100` (because that is what the UI shows as a gauge); every timestamp ISO-8601 UTC with a `Z`. Getting this wrong across three codebases costs hours.

---

## 7. Novelty map — what is table-stakes, what actually wins

Be honest with yourselves about this. Embeddings + cosine similarity is now the *baseline* for any matching problem; judges have seen it dozens of times. A weighted composite score is sound engineering, not innovation. A map with pins on it is decoration. None of those three will be why you win — they are the price of entry.

These are what differentiate you, with a single owner and a priority tier each. **Every feature below appears exactly once in exactly one task file.**

| # | Feature | Why it's differentiating | Owner | Tier |
|---|---|---|---|---|
| 1 | **Consortium engine** with redundancy penalty, trust floor, no-passenger constraint and absorptive-capacity-capped budget split | Reframes the problem from a sort into weighted set-cover. Solves a real constraint (no single NGO fills a multi-district mandate) that almost no team will even notice. | **A** | **P1 ★ headline** |
| 2 | **Shell-network graph detection** over shared address / trustee / bank / phone | This is how financial-crime teams actually work. Converts "Fraud Shield" from a checklist into detection. Demos in five seconds. | **B** | **P1 ★ headline** |
| 3 | **Counterfactual coach** — "+19 pts if you upload your renewed CSR-1", with actionable/structural split and achievable ceiling | Turns a judging tool into a coaching tool. Serves the *supply* side, which every other team ignores. | A (math) + B (persist) + C (UI) | **P1 ★ headline** |
| 4 | **Evidence-anchored scoring** — every pillar links to `{doc_id, page, snippet, confidence}` and the UI renders the actual PDF page | Makes the auditability requirement real instead of aspirational. This is the feature a compliance officer would buy. | **B** | **P1** |
| 5 | **Keyword ⇄ semantic A/B toggle** in the live UI | Cheapest high-impact device in the build. Proves your core tech's value in one click instead of asserting it. | **C** | **P1** |
| 6 | **Cohort-relative robust anomaly detection** (median/MAD within domain × budget-tier × region) | Methodologically correct where naive global outlier detection is wrong. The claim-inflation direction is the genuinely interesting fraud signal. | **A** | **P1** |
| 7 | **CSR-1 as a hard eligibility gate**, not a score penalty | Domain accuracy: without CSR-1 the transaction is *legally impossible*. Shows you understand the statute, not just the vibe. | **B** | **P1** |
| 8 | **Demand-vs-supply GIS layer** on real NITI Aayog Aspirational Districts — "CSR deserts" | Surfaces where NGOs *aren't*, which is the actual insight. Grounded in real public data. | **C** | **P1** |
| 9 | **Rank-stability Monte Carlo** over Dirichlet-resampled weights | Pre-empts the #1 judge question ("why 0.5/0.3/0.2?") with a measurement instead of an opinion. | **A** | P2 |
| 10 | **Pareto frontier** of non-dominated partners | Honest about multi-objective trade-offs where a single weighted score hides them. ~30 lines. | **A** | P2 |
| 11 | **Document tamper & cross-consistency forensics** — registration numbers agreeing across documents, FY periods matching, totals reconciling, PDF metadata dates, missing text layer ⇒ lower extraction confidence | Real forensics, fully deterministic, no ML risk. Strong under questioning. | **B** | P2 |
| 12 | **Hash-chained append-only audit log** | Fifteen lines. Sounds extremely serious and is genuinely correct for a compliance product. | **B** | P2 |
| 13 | **Freshness decay with documented half-lives** + "last verified N months ago" | Stops one-time gaming; makes trust a live number rather than a stamp. | B (compute) + C (display) | P2 |
| 14 | **Cost-per-beneficiary normalisation** as a comparable efficiency metric | The most intuitive number on the screen, and the input to claim-inflation detection. | A (compute) + C (display) | P2 |
| 15 | **Chat-based mandate intake** with per-field confidence and clarifying questions | Better demo than a form, and the confidence/clarification behaviour is what separates it from a gimmick. | A (NLU) + C (UI) | P1 |
| 16 | **SDG auto-tagging** by embedding similarity against the 17 goals | Corporates must report SDG alignment; this is free reporting value. | **A** | P2 |
| 17 | **Outcome feedback loop + calibration curve** | Closing beat of the pitch: the system gets better-grounded with use. Claim only calibration, never "retraining". | A (calibrate) + B (store) | P2 |
| 18 | **"₹ at risk" framing** — rupees that would have gone to a sub-threshold partner under naive matching | Converts the whole system into one rupee number a CFO understands. This is your closing slide. | **C** | P1 |
| 19 | **Live latency badge** showing real query milliseconds | Proves the sub-800 ms requirement on screen instead of claiming it. | **C** | P2 |
| 20 | **Unmatched-mandate honesty guard** | Refusing to return garbage when nothing fits reads as maturity, and judges probe for exactly this. | A (detect) + C (render) | P2 |

**Tier meanings.** **P0** = the demo does not exist without it (not listed above; that's the baseline: embeddings, composite score, trust pillars, seed data, ranked list). **P1** = these are why you win; protect them. **P2** = build if ahead of schedule, otherwise ship with static fixture data and say nothing.

**If you fall behind, cut in this order:** 16 → 19 → 17 → 12 → 10 → 9 → 11 → 13. Never cut 1, 2, 3, 5.

---

## 8. Non-negotiable engineering rules

**1 — The demo must survive with the wifi unplugged.** This is the rule that has saved more hackathon teams than any other. Concretely:
- Embedding model is **local** (`sentence-transformers/all-MiniLM-L6-v2`, ~80 MB). Download it in Hour 1, commit the cache under `ml/artifacts/`, and set `HF_HUB_OFFLINE=1` for the demo run.
- All NGO embeddings are **pre-computed and committed** as `ml/artifacts/ngo_embeddings.npy` plus an id-order manifest. Nothing embeds NGOs at request time.
- `DEMO_MODE=true` makes the backend serve deterministic responses from `backend/seed/data/` with no model and no database.
- `frontend/fixtures/` holds a full captured set of API responses. If the backend dies mid-demo, the frontend still walks the entire flow.
- No feature may depend on an external API call during the demo. If an LLM is used for mandate parsing, there must be a regex/rule fallback that produces a valid mandate offline.

**2 — Protect the working build.** Commit whenever something works, before you experiment. Tag it. From Hour 40 onward, the `main` branch is **frozen except for bug fixes** — no new features. A polished four-feature demo beats a broken seven-feature demo every single time.

**3 — Branch per person, PR to main.**
```powershell
# start of your session
git checkout main
git pull origin main
git checkout -b feat/ml-consortium      # or feat/be-trust, feat/fe-console

# commit as you go
git add ml/setu_ml/consortium.py
git commit -m "feat(ml): consortium set-cover with redundancy penalty"
git push -u origin feat/ml-consortium
```
Never `git push --force`. Never `git reset --hard` on a branch someone else has pulled. If a merge looks scary, stop and ask before running anything destructive.

**4 — Seed data is a first-class deliverable, not filler.** 40 NGOs minimum (target 60), spanning education / healthcare / WASH / environment / skilling / livelihoods, across at least 8 states, with *deliberately planted* cases: one shell network of three, two claim-inflation outliers, four missing CSR-1, three with expired 80G, five with stale evidence, and at least one mandate that is genuinely unfillable by a single NGO. **The demo narrative is only as good as the planted cases.** Write the story first, then generate data that tells it.

**5 — Every number on screen must be traceable.** If the UI shows 84, `/api/ngos/{id}/trust` must explain how 84 was reached, and each pillar must point at a document page. A judge clicking into a number and finding nothing behind it is the fastest way to lose the room.

**6 — Don't overclaim.** Say "calibrated on our corpus", "synthetic dataset modelled on public registries", "pluggable verifier interface — we validate format and cross-document consistency; live MCA/Darpan verification is an integration, not a hack". Precise honesty beats confident vagueness, and experienced judges are specifically listening for it.

**7 — `.env.example` is committed, `.env` never is.** No API keys in the repo. Check before every push.

---

## 9. The demo, defined up front

Build toward this. If a feature does not appear in this flow, it is a P2 by definition.

| # | Beat | On screen | The line |
|---|---|---|---|
| 1 | Mandate in plain English | Director types *"₹50 lakh for maternal health and clean drinking water across Kalahandi, Nuapada and Balangir in Odisha, prefer partners with prior corporate CSR experience"* | "No forms. She just says what she wants to fund." |
| 2 | Structured extraction | Fields populate with confidence chips; one clarifying question appears | "We extracted budget, two domains, three districts and a preference — and we ask when we're unsure rather than guessing." |
| 3 | **A/B toggle** | Flip to *Keyword*: 2 results. Flip to *Semantic*: 9 results, with the top match highlighted as missed-by-keyword | "Keyword search would have missed her best partner, because they call it 'postpartum institutional delivery care'." |
| 4 | Ranked deck + latency | Cards with score, badge, cost-per-beneficiary; latency badge reads the real measured figure | "We benchmarked ranking at a thousand organisations — **[fill in the measured p95 at Hour 42]** milliseconds end to end. What you're seeing here is our forty-eight fully-documented profiles." *(Say the benchmark size and the corpus size in the same breath, and quote the number you actually measured. A judge who works out unaided that the deck holds 48 rows while you claimed nine hundred has just decided to distrust every other number you say.)* |
| 5 | **Trust dossier drill-down** | Click 84 → four pillars → click Compliance → **the actual CSR-1 PDF page appears with the number highlighted** | "Every point traces to a document. This is what a compliance officer signs off on." |
| 6 | **Shell network catch** | Open a *High Risk* NGO → network panel shows three "unrelated" NGOs sharing an address, a trustee and a bank account | "We didn't catch this by reading its documents. We caught it by looking at the network." |
| 7 | **Consortium** | No single NGO covers all three districts across both domains — 6 requirement units, best single covers 3. Two-partner consortium: coverage bars fill to 100%, 8% overlap, ₹32.5L / ₹17.5L split, one partner capped at absorptive capacity | "The real mandate needed two partners. We found the pair, penalised overlap, refused to hand ₹40 lakh to an organisation that's never managed more than ₹8 lakh — and we evaluated three-partner combinations too; the coordination penalty made them worse." |
| 8 | **Counterfactual coach** | Switch to NGO role. Score 61. Toggle "CSR-1 renewal uploaded" → gauge animates 61 → 80, badge changes | "We don't reject NGOs into a black box. We hand them the roadmap." |
| 9 | GIS deserts | Map: verified-partner density vs Aspirational Districts; red zones with zero verified partners | "And here's where the money still isn't going." |
| 10 | Close: ₹ at risk | One number: rupees that would have gone to a sub-threshold partner under naive matching | "Same budget. Verified partners. Full coverage. Nothing sitting unspent." |

Target: **four minutes**, leaving time for questions. Beats 3, 5, 6, 7 and 8 are the memorable ones — rehearse those until they are muscle memory, and let the rest breathe.

---

## 10. Judge Q&A — the questions that will actually come

| Question | Answer |
|---|---|
| *"Isn't this just cosine similarity?"* | "Cosine similarity is our entry price, not our contribution. Our contribution is the consortium set-cover with a redundancy penalty and absorptive-capacity caps, shell-network graph detection, and evidence-anchored trust scoring. Happy to show any of the three." |
| *"Why 0.5 / 0.3 / 0.2?"* | The rank-stability answer in §5.6. Then move the sliders live. |
| *"How do you know the certificates are real?"* | "We don't claim live government verification — there's no open MCA API for this. We do three things: validate artefact formats, cross-check identifiers across independent documents, and run tamper signals on the PDFs themselves. The verifier is an interface, so a registry integration drops in without touching the scoring." |
| *"What stops an NGO gaming the score?"* | "Three things, layered: cohort-relative anomaly detection catches implausible numbers, shell-network analysis catches coordinated fraud, and freshness decay means a one-time document dump doesn't hold a high score. And the counterfactual coach deliberately only exposes actions that require real evidence." |
| *"Is your data real?"* | "The compliance framework, the district data and the Aspirational Districts list are real. The 48 NGO profiles are synthetic, modelled on NGO-Darpan and MCA CSR portal structures, with fraud patterns planted deliberately so the detection is testable. We'd onboard real NGOs through the same upload path." |
| *"Does it scale?"* | "At a thousand records, brute-force cosine in NumPy is about 15 ms — the index is behind an interface, so at a hundred thousand we swap in Atlas Vector Search or HNSW without touching the scoring layer. The consortium search is exhaustive over a top-12 shortlist, which is 286 combinations regardless of network size." |
| *"Who pays?"* | "Corporates, as compliance-risk reduction — a subscription is trivially cheaper than one misallocated grant or one audit finding. Free for NGOs, because they're the supply side we need to attract. Aggregate sector benchmarking is a natural second product." |
| *"What about privacy / conflicts of interest?"* | "Role-scoped access: an NGO sees only its own dossier and counterfactual, a corporate's internal review notes are invisible to other corporates and to NGOs, and auditors get read-only access to the hash-chained log." |
| *"What would you do with another month?"* | "Registry integrations for live CSR-1 and Darpan verification, real NGO onboarding in one district to validate the trust pillars against ground truth, and a proper outcome-tracking loop so calibration runs on real completions instead of simulated ones." |
| *"What's your weakest point?"* | Answer this honestly — deflecting costs you more than admitting. "Our synthetic dataset. The algorithms are sound and tested, but the fraud patterns are ones we planted, so we know detection works in principle rather than in the field. Validating against real registry data is the first thing we'd do." |

---

*Last updated: 2026-09-03 · algorithm_version `setu-1.0.0`*

