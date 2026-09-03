# SETU

**A matching and verification layer for corporate CSR in India.**

A company describes a funding mandate in one sentence. SETU returns NGO partners who are legally eligible, verified against their own filed documents, and geographically able to deliver — and where no single organisation can deliver the mandate, it assembles the smallest consortium that can.

*Setu* — सेतु — means bridge.

---

## Why this exists

Section 135 of the Companies Act 2013 requires large Indian companies to spend 2% of their three-year average net profit on social causes. Money is not the constraint. Finding a partner who is *legally eligible* to receive CSR funds, *financially clean*, and *actually operating in the district you care about* is a manual process that takes weeks, and getting it wrong is an audit finding.

Since 1 April 2021, a company cannot legally count a contribution as CSR spend unless the recipient has filed Form CSR-1 with the MCA. SETU treats that as a hard eligibility gate rather than a scoring factor, because it is law rather than judgement.

---

## What it does

**Understands a mandate in plain language.** Budget, domains, districts and preferences are extracted from one sentence, with per-field confidence, and the system asks a clarifying question rather than guessing when it is unsure. Hindi-English code-mixed input works.

**Matches on meaning, not keywords.** An NGO describing its work as "postpartum institutional delivery care" is found by a mandate asking for "maternal health". A built-in A/B toggle runs the same query through a fair keyword baseline so the difference is measurable rather than asserted.

**Scores trust against evidence, not self-declaration.** Four pillars — compliance, financial discipline, operational track record, external validation — assembled from uploaded documents, with freshness decay so a one-time document dump does not hold a high score. Every point traces to a document page a compliance officer can open, with the extracted text highlighted.

**Detects coordinated fraud through the network.** Organisations whose own paperwork looks clean but which share a registered address, a trustee and a bank account with two other apparently-unrelated NGOs are surfaced as a linked-entity network and flagged for human review.

**Assembles consortiums when no single partner fits.** A weighted set-cover over requirement units, with a redundancy penalty for overlapping capability, a coordination cost per additional partner, a trust floor, a no-passenger constraint, and a budget split capped at 1.5× the largest grant each member has previously managed.

**Coaches the NGOs it rejects.** An organisation scoring below threshold is told exactly which missing evidence costs it how many points, ranked by impact per unit of effort, with an achievable ceiling. The predicted delta is computed by the *same* trust function the corporate side runs, so it is guaranteed to match what actually happens after the document is uploaded.

**Maps demand against supply.** Verified partner density against the NITI Aayog Aspirational Districts, surfacing districts with high need and no verified partners.

---

## Architecture

```
┌──────────────────────────┐
│  frontend/  Next.js 14   │   corporate console · NGO coach · GIS · admin
└────────────┬─────────────┘
             │  REST, JSON, snake_case
┌────────────┴─────────────┐
│  backend/   FastAPI      │   endpoints · document parsing · trust assembly
│                          │   shell-network graph · forensics · audit log
└──────┬──────────────┬────┘
       │              │
┌──────┴──────┐  ┌────┴─────────────┐
│  MongoDB    │  │  ml/  setu_ml    │   embeddings · scoring · consortium
│             │  │  pure library    │   anomaly · counterfactual · geo
└─────────────┘  └──────────────────┘
```

`setu_ml` is a pure Python library — no HTTP, no database, no global state. It is installed into the backend with `pip install -e ../ml`. That boundary is what let three people build in parallel, and it is why the trust computation can be called identically by the scoring path and by the counterfactual engine.

Everything runs locally and offline. The sentence-transformer model cache and the pre-computed NGO embeddings are committed to the repository.

---

## Setup

Requires Python 3.11+, Node 18+, and MongoDB running locally (or a connection string).

```powershell
git clone https://github.com/<owner>/setu.git
cd setu

# --- ML library ---
cd ml
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest

# --- backend ---
cd ..\backend
pip install -r requirements.txt          # includes -e ../ml
copy .env.example .env                   # then fill in MONGODB_URI
python -m seed --reset                   # ~45s: 48 NGO profiles + mock PDFs
python -m uvicorn app.main:app --reload --port 8000

# --- frontend, in a second terminal ---
cd ..\frontend
npm install
copy .env.local.example .env.local
npm run dev
```

Open `http://localhost:3000`. API docs at `http://localhost:8000/docs`.

To run without the backend, set `NEXT_PUBLIC_USE_FIXTURES=true` — the console serves captured API responses from `frontend/fixtures/` and the full demo path works with no Python process and no network.

---

## Repository layout

```
ml/setu_ml/        types · embeddings · geo · extract · scoring · justify
                   consortium · anomaly · counterfactual · pareto · stability
ml/artifacts/      committed model cache, embeddings, calibration.json, districts
backend/app/       main · config · db · routers/ · services/ · parsing/
backend/seed/      generator, NARRATIVE.md, mock PDF builder, mock_responses/
frontend/src/      app/ · components/ · lib/ · fixtures/
docs/              project context, PRD, build plan, task briefs, demo runbook
```

Folder ownership was strict during the build: one person per top-level folder, coupled only through `ml/setu_ml/types.py` and the frozen API contract in `docs/00-PROJECT-CONTEXT.md` §6.

---

## What is real and what is synthetic

Stated plainly, because it matters for how you read the results.

**Real:** the statutory framework (Section 135, Schedule VII, CSR-1 / 12A / 80G / FCRA requirements and their formats), the district names and coordinates, the NITI Aayog Aspirational Districts list, and every algorithm in `setu_ml`.

**Synthetic:** the 48 NGO profiles and their supporting documents, generated with a fixed random seed and modelled on the structure of NGO-Darpan and MCA CSR portal records. The fraud patterns — the shell ring, the claim inflators, the expired certificates, the tampered document — are planted deliberately so that detection is testable. The district need index is seeded.

**Not claimed:** live verification against MCA or NGO-Darpan registries. There is no open API for this. SETU validates artefact formats, cross-checks identifiers across independent documents, and runs tamper signals on the PDFs themselves. The verifier is an interface, so a registry integration drops in without touching the scoring layer.

The trust score is a decision-support signal, not a certification, and the system says so wherever it is displayed.

---

## Reproducibility

Every score carries an `algorithm_version` and an `input_hash` — a SHA-256 of the canonical inputs — so any number in the interface can be regenerated and audited. Verification actions are recorded in a hash-chained append-only log; `GET /api/audit?verify=true` walks the chain and reports whether it is intact.

Scoring weights are documented in one place (`docs/00-PROJECT-CONTEXT.md` §5) and are the single source of truth for all three layers. Rank stability under weight perturbation is measured rather than assumed.

---

## Team

| | Lane | Folder |
|---|---|---|
| Piyush | ML & optimisation | `ml/` |
| Vaishnavi | Backend, trust & forensics | `backend/` |
| — | Frontend, GIS & narrative | `frontend/` |

---

## Documentation

Read `docs/00-PROJECT-CONTEXT.md` first — it holds the domain primer, the scoring model, and the frozen API contract. `docs/01-PRD.md` has requirements and acceptance criteria; `docs/02-BUILD-PLAN-48H.md` is the schedule we actually ran.

Built for a 48-hour hackathon · CSR track, Problem Statement 2 · `setu-1.0.0`
