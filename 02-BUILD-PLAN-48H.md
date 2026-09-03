# SETU — 48-Hour Build Plan

**Three people, three swimlanes, five hard checkpoints, one frozen contract.**
Read `00-PROJECT-CONTEXT.md` first. Formulas and the API contract live there; this file is only *when* and *in what order*.

| Lane | Owner | Folder | Ships |
|---|---|---|---|
| **A** | Piyush | `ml/` | A pure Python library — no HTTP, no database |
| **B** | Vaishnavi | `backend/` | A FastAPI service + seeded data + compliance forensics |
| **C** | Third member | `frontend/` | The Next.js console, GIS, and the pitch deck |

---

## Ground rules for the 48 hours

**Sleep is a build resource, not a luxury.** A team that codes 48 hours straight ships worse work than a team that sleeps in shifts, and the pitch — which is the thing actually being judged — is delivered by whoever is most coherent. Plan: everyone sleeps Hours 20–26 (six hours, overlapping). If someone must stay up, it is one person on a task that cannot break the build, and they hand over notes in writing.

**Checkpoint calls are mandatory** at Hours 8, 16, 24, 32 and 40. Fifteen minutes, standing up, three questions each: what works, what's blocked, what did you change that affects someone else. **Blocked for more than 45 minutes means you say so immediately.** Silent stalling is the most common way three-person hackathon teams fail.

**Commit whenever something works.** Not at the end of a feature — the moment a piece runs correctly. Tag the last known-good state before you start anything experimental.

**Feature freeze at Hour 40.** After that, only bug fixes, polish and rehearsal. This is not a suggestion; it is the difference between a demo and an apology.

### Git, exact PowerShell

```powershell
# --- once, at Hour 0 (one person does this, others clone) ---
cd C:\Users\Piyush
git clone https://github.com/<owner>/setu.git
cd setu

# --- every work session ---
git checkout main
git pull origin main
git checkout -b feat/ml-consortium         # or feat/be-trust  /  feat/fe-console

# --- as you go, whenever something works ---
git add ml/setu_ml/consortium.py ml/tests/test_consortium.py
git commit -m "feat(ml): consortium set-cover with redundancy penalty"
git push -u origin feat/ml-consortium

# --- tag a known-good state before experimenting ---
git tag -a good-h16 -m "working match + trust, pre-consortium"
git push origin good-h16

# --- merging into main (do it often, small merges) ---
git checkout main
git pull origin main
git merge feat/ml-consortium
git push origin main
```

Never `git push --force`. Never `git reset --hard` on a branch anyone else has pulled. If a merge looks frightening, stop and ask before running anything — a stuck merge costs minutes, a bad recovery costs hours.

---

## Hours 0–4 · Together, then split

**Do this as a group. Do not skip it to "save time" — this block prevents the two failures that kill three-person teams: contract drift and a demo nobody agreed on.**

| # | Task | Who |
|---|---|---|
| 0.1 | Create the repo, the folder skeleton from `00-PROJECT-CONTEXT.md §4`, `.gitignore`, `.env.example`. Everyone clones and confirms they can commit. | All |
| 0.2 | **Write the demo narrative first.** Open `06-PITCH-AND-DEMO-RUNBOOK.md` and agree the exact mandate sentence, the exact NGO names in the shell ring, the exact NGO that scores 61 and gets coached to 80. Everything downstream — seed data, tests, UI copy — is generated to satisfy this narrative. | All |
| 0.3 | **Freeze the API contract.** Walk §6 line by line together. Anything unclear gets settled now, in writing, while it is cheap. | All |
| 0.4 | Download the embedding model and **commit the cache**: `python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2').save('ml/artifacts/minilm')"`. Verify it loads with the network disabled. | A |
| 0.5 | Agree the **seeded fraud narrative**: which 3 NGOs form the shell ring and which identifiers they share; which 2 inflate claims; which 4 lack CSR-1; which 3 have expired 80G; which 5 have stale evidence; which mandate is unfillable by one NGO. Fill in the frozen-facts table in `06-PITCH-AND-DEMO-RUNBOOK.md §1` and copy it into `backend/seed/data/NARRATIVE.md`. | All |

**Exit gate for Hour 4:** the contract is frozen, the demo script exists on paper, the model loads offline, and the fraud narrative is written down. If any of those four is missing, do not proceed to parallel work.

---

## Hours 4–8 · Foundations, in parallel

| Lane A — Piyush | Lane B — Vaishnavi | Lane C — third member |
|---|---|---|
| `types.py`: the shared Pydantic models for `Mandate`, `NgoProfile`, `TrustBreakdown`, `MatchResult`, `Consortium`. **B and C code against these names.** Publish them first. | Mongo connection + collections; Pydantic request/response models mirroring §6 exactly. | Next.js scaffold, Tailwind, layout shell, role switcher, dark-on-light theme, `lib/api.ts` typed client. |
| `embeddings.py`: load local model, `embed_texts()`, `cosine_matrix()`, persistence of `ngo_embeddings.npy` + id manifest. | **Priority: the mocked API.** Every endpoint in §6 returning contract-shaped stub data. Ship this by Hour 8 so Lane C is never blocked. | Build against the mocked API from the start. Never wait for real data. |
| `geo.py`: haversine, district Jaccard, `geo_score()`. | Start the seed generator: **48** NGO profiles per the Hour-0.5 narrative, fixed random seed. | `fixtures/` directory + the automatic fallback wrapper in `lib/api.ts`. Build the resilience in now, not at Hour 45. |

**Checkpoint at Hour 8:** the mocked API responds to every endpoint. Lane C renders a list of NGOs from it. Lane A's `types.py` is merged to `main`. *If the mock isn't up, everything else stops until it is.*

---

## Hours 8–16 · Core engine and real data

| Lane A | Lane B | Lane C |
|---|---|---|
| `scoring.py`: `semantic_score()` with the affine calibration, `composite_score()`, `justify()` producing three grounded bullets — each must cite a real number or place from the record. | Finish the seed generator including **all planted fraud cases**. `make_mock_pdfs.py` generating realistic CSR-1 / 12A / 80G / audit PDFs with the right registration numbers on the right pages. | Mandate chat intake UI with streaming, confidence chips, editable fields. Ranked partner deck with real card design. |
| **Fit the calibration constants on the real seed corpus** and eyeball the score distribution across all mandate×NGO pairs. Commit `calibration.json`. | `parsing/`: PyMuPDF text + page anchors; `compliance.py` extracting and format-validating the five artefact types with `{page, snippet, offsets, confidence}`. | Trust dossier drawer: four pillar bars, expandable, evidence list. Wire to the mock's dossier shape. |
| `extract.py`: mandate NLU, LLM path **and** deterministic fallback, both emitting the same schema, per-field confidence, clarifying questions. | `trust.py`: assemble the four pillars per §5.2 with freshness decay, badges, the CSR-1 hard gate. | Leaflet map with bundled district GeoJSON, NGO markers, domain/trust filters. |

**Checkpoint at Hour 16:** a real mandate string goes in and a real ranked list comes out, end to end, through the real backend. Trust scores are real numbers with real evidence references. Tag `good-h16`.

> **If you are behind at Hour 16**, the problem is almost always Lane B's seed data — generating 40 believable NGO profiles *with* mock PDFs is more work than it looks. Lane A should stop and help; the consortium engine can start at Hour 20 and still land.

---

## Hours 16–20 · The differentiators begin

| Lane A | Lane B | Lane C |
|---|---|---|
| **`consortium.py`** — requirement units, coverage, redundancy, trust floor, no-passenger constraint, coordination cost, greedy seed then exhaustive search over the top 12, absorptive-capacity-capped budget split. This is your headline feature; give it your freshest hours. | **`shell_network.py`** — identifier normalisation, edge construction, connected components, the ≥2-members-and-≥2-identifier-types rule, trust cap at 40. Your headline feature. | **Keyword ⇄ semantic A/B toggle** with the delta banner. Cheapest win in the whole build — do it before anything else in this block. |
| Unit tests: a hand-constructed case where the optimal pair is known, and a case where the single NGO should win. | `/api/ngos/{id}/network` + the evidence page renderer `/api/documents/{doc_id}/pages/{n}.png`. | Evidence drill-down: click a pillar → click evidence → **the document page renders with the snippet highlighted**. |

### 🛌 Hours 20–26 · Sleep shift

Everyone sleeps. Before you stop: commit, push, and write one paragraph in the group chat saying exactly where you left off and what breaks. You will not remember at Hour 26 and neither will anyone else.

---

## Hours 26–32 · Second differentiators

| Lane A | Lane B | Lane C |
|---|---|---|
| **`anomaly.py`** — cohort bucketing, median/MAD robust z-scores, `insufficient_cohort` guard, directional flag text (waste vs claim-inflation). | **`counterfactual` persistence** + `/api/ngos/{id}/counterfactual`, and a test asserting predicted delta equals the delta after actually uploading the document. | **Consortium view** — coverage bars filling per member, redundancy %, budget-split donut, capacity-cap indicator, rationale line. |
| **`counterfactual.py`** — Δ per unmet evidence item, actionable/structural/never-show classification, Δ/effort ranking, `achievable_ceiling`. | `POST /api/verify` returning a before/after score diff. RBAC dependency + `review_notes` scoping. | **Counterfactual coach panel** in NGO role — toggles that animate the gauge and badge to the exact API value. |
| Wire the counterfactual to the same shared function the trust recompute uses. **One function, two callers** — this is what stops the on-stage contradiction. | `/api/geo/coverage` with `need_index`, `is_aspirational`, `gap_score` per district. | **Demand-vs-supply choropleth** + radius filter. |

**Checkpoint at Hour 32:** all four headline features work end to end through the UI — A/B toggle, evidence drill-down, shell network, consortium, counterfactual. Tag `good-h32`.

> **This is the decision point.** If any of those five is not working at Hour 32, stop starting new things. Spend Hours 32–40 finishing them. A demo with four flawless differentiators beats one with six shaky ones, every time, in front of every judging panel.

---

## Hours 32–40 · P2s, only if the P1s are solid

Pick from the top of this list and stop when the clock runs out. **Do not start an item you cannot finish inside two hours.**

| Priority | Item | Lane |
|---|---|---|
| 1 | **"₹ at risk" summary** — high impact, roughly 45 minutes | C |
| 2 | **Rank-stability Monte Carlo** + weight sliders — pre-empts the hardest question | A + C |
| 3 | **Document forensics** — cross-document consistency, FY match, arithmetic reconciliation, PDF metadata | B |
| 4 | **Live latency badge** — 15 minutes, visible proof of the performance claim | C |
| 5 | **Pareto frontier** — ~30 lines in A, one chart in C | A + C |
| 6 | **Comparison matrix** for three NGOs | C |
| 7 | **Hash-chained audit log** + verification endpoint | B |
| 8 | **Freshness "last verified N months ago"** everywhere it belongs | B + C |
| 9 | **RFP dispatch + dossier PDF** | B + C |
| 10 | **Outcome feedback + calibration chart** | A + B + C |
| 11 | **SDG auto-tagging** | A |
| 12 | **Unmatched-mandate guard** UI state | A + C |

Whoever finishes their lane's P2s first moves to the deck. **The deck is a shared deliverable, not Lane C's private problem.**

---

## Hour 40 · FEATURE FREEZE

From here, `main` accepts bug fixes and polish only. Anyone who opens a new feature branch after Hour 40 is actively hurting the team's result.

## Hours 40–44 · Harden

| # | Task | Who |
|---|---|---|
| 40.1 | **Offline dry run.** Disable the network adapter. Run the entire ten-beat demo. Fix everything that breaks. This single step has saved more hackathon demos than any other and it must happen at Hour 42, not Hour 47. | All |
| 40.2 | `seed --reset` verified to restore exact demo state in under 60 s, twice in a row. | B |
| 40.3 | Capture live API responses for every demo endpoint into `frontend/fixtures/`; verify the frontend walks the whole path with the backend killed. | B → C |
| 40.4 | Latency benchmark over 1,000 records; confirm p95 < 800 ms; make sure the number the UI shows is the real one. | A + B |
| 40.5 | Responsive pass at 1920 / 1440 / 1024. Keyboard-only walkthrough of the demo path. Confirm every badge has a text label, not just a colour. | C |
| 40.6 | Every trust pillar of every seeded NGO resolves to a document page or an explicit `no_evidence`. Automated test, not a spot check. | B |
| 40.7 | Assert the counterfactual's predicted delta equals the recomputed delta for all seeded NGOs. | A + B |
| 40.8 | `README.md` final: setup, run commands, architecture diagram, screenshots. Judges and graders read this. | All |

## Hours 44–48 · Rehearse

| # | Task | Who |
|---|---|---|
| 44.1 | **Three full run-throughs of the demo**, timed. Target four minutes. First one will run long — cut words, not beats. | All |
| 44.2 | Assign speaking parts. Whoever built a feature narrates it, so answers to follow-ups are first-hand. | All |
| 44.3 | **Q&A drill.** Someone plays a hostile judge using `00-PROJECT-CONTEXT.md §10`. Anyone who fumbles the "why 0.5/0.3/0.2" or "isn't this just cosine similarity" answers drills them again. | All |
| 44.4 | **Cross-training.** Each member explains a feature they did *not* build. Judges choose who to question. | All |
| 44.5 | Two laptops set up identically, both able to run the demo. Charged. Adapters and dongles tested on the actual projector if you can get near it. Browser zoom set so the back row can read the screen. | All |
| 44.6 | Final commit, tag `v1.0-demo`, push. Then stop touching the code. | All |

> **Hour 47 rule:** whatever is broken at Hour 47 stays broken. Demo around it. A confident walkthrough that skips one feature beats a panicked debug in front of a panel.

---

## Cut decision tree

Run this at every checkpoint, out loud.

```
Is the ten-beat demo path complete end-to-end?
├── NO  → Stop all P2 work. Everyone converges on the gap. Nothing else matters.
└── YES → Do all four headline features work? (A/B toggle, shell network,
          consortium, counterfactual)
          ├── NO  → Fix them. Do not start anything new.
          └── YES → Does it run with the network disabled?
                    ├── NO  → Fix that next. It outranks every remaining feature.
                    └── YES → Take the next item off the Hours 32–40 list.
```

**Cut order if you must shed scope:** SDG tagging → latency badge → outcome/calibration loop → hash-chained audit log → Pareto frontier → rank stability → document forensics → freshness display → comparison matrix → RFP dossier.

**Never cut:** consortium engine, shell-network detection, counterfactual coach, keyword⇄semantic toggle, evidence drill-down, offline resilience.

**If you are catastrophically behind at Hour 36** — say only the ranked list and trust scores work — then ship this reduced demo deliberately and well: chat intake → A/B toggle → ranked deck → trust dossier with evidence drill-down → shell network. That is five beats, all real, and it still tells a complete story. Present it with total confidence and describe the consortium engine as designed-and-specified rather than pretending. Judges forgive honest scope; they do not forgive a crash.

---

*`02-BUILD-PLAN-48H.md` · companion to `00-PROJECT-CONTEXT.md` and `01-PRD.md`*

