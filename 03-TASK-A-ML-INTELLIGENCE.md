# TASK A — Matching & Trust Intelligence Library
### Owner: **Piyush** · Folder: `ml/` · Deliverable: a pure Python package, `setu_ml`

---

## How to use this document

This is a build prompt. Open your AI IDE in the repo root and paste, in one message:

1. Sections 0–10 of `00-PROJECT-CONTEXT.md` (the domain, the formulas, the API contract)
2. This entire file

Then work the numbered items **A1 → A12 in order**. Later items import earlier ones. After each item: run its tests, commit, move on. Do not batch three items and then debug — you will not know which one broke.

---

## Your mandate, and your boundaries

You own the **intelligence layer**. Everything algorithmic lives here: embeddings, the composite score, the consortium optimiser, the anomaly statistics, the counterfactual engine.

**You ship a library, not a service.** `setu_ml` has:

- **no** FastAPI, no Flask, no HTTP client
- **no** MongoDB, no database driver of any kind
- **no** file I/O except reading and writing your own `ml/artifacts/`
- **no** `print()` in library code — use `logging`

Every public function takes plain Python objects or Pydantic models in and returns them out. Vaishnavi's backend does `from setu_ml import ...` and calls you directly. This constraint is not bureaucracy: it is what lets you write fast unit tests, and it is why you will not be blocked on her work for a single minute.

**You are the owner of three of the four features that will decide whether this project wins**: the consortium engine (A7), the anomaly detection (A8), and the counterfactual engine (A9). Items A1–A6 are the foundation those stand on — build them quickly and correctly, then spend your best hours on A7–A9.

---

## Setup

```powershell
cd C:\Users\Piyush\setu
mkdir ml\setu_ml, ml\tests, ml\tests\fixtures, ml\artifacts
```

`ml/pyproject.toml`:

```toml
[project]
name = "setu-ml"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
  "numpy>=1.26",
  "scipy>=1.11",
  "pydantic>=2.5",
  "sentence-transformers>=2.2",
]

[project.optional-dependencies]
dev = ["pytest>=7.4", "pytest-benchmark>=4.0"]
```

```powershell
cd C:\Users\Piyush\setu\ml
python -m pip install -e ".[dev]"
```

**Hour 0 task, do this before anything else** — download and commit the model so the demo never needs the network:

```powershell
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2').save('artifacts/minilm')"
```

Then verify it loads offline: set `$env:HF_HUB_OFFLINE=1`, restart the shell, and load from the local path. If that fails, fix it now — at Hour 44 it is a catastrophe.

---

# A1 · `types.py` — the shared vocabulary

**Build this first and merge it to `main` within the first hour.** Vaishnavi and the frontend both code against these field names. Every hour this is missing is an hour of someone else guessing.

Field naming follows `00-PROJECT-CONTEXT.md §6`: `snake_case`, money as integer rupees with an `_inr` suffix, scores in `[0,1]` except `trust_score` which is `0–100`.

```python
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field

class Domain(str, Enum):
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    MATERNAL_HEALTH = "maternal_health"
    WASH = "wash"                    # water, sanitation, hygiene
    ENVIRONMENT = "environment"
    SKILLING = "skilling"
    LIVELIHOODS = "livelihoods"
    NUTRITION = "nutrition"
    DISABILITY = "disability"
    RURAL_DEVELOPMENT = "rural_development"

class TrustBadge(str, Enum):
    ELITE = "Verified Elite"
    STANDARD = "Standard Audited"
    INCOMPLETE = "Verification Incomplete"
    HIGH_RISK = "High Risk — Review Required"
    INELIGIBLE = "Ineligible for CSR Funds"

class DistrictRef(BaseModel):
    district: str
    state: str
    lat: float
    lng: float
    is_aspirational: bool = False

class RequirementUnit(BaseModel):
    """One cell of the mandate: a domain in a district. The atom of coverage."""
    domain: Domain
    district: str
    state: str
    weight: float = 1.0

class Mandate(BaseModel):
    mandate_id: str | None = None
    raw_text: str
    domains: list[Domain]
    budget_inr: int
    districts: list[DistrictRef]
    duration_months: int | None = None
    beneficiary_profile: str | None = None
    preferences: list[str] = Field(default_factory=list)
    foreign_funded: bool = False
    field_confidence: dict[str, float] = Field(default_factory=dict)
    clarifying_questions: list[str] = Field(default_factory=list)
    requirement_units: list[RequirementUnit] = Field(default_factory=list)

class NgoFinancials(BaseModel):
    admin_expense_inr: int
    programme_expense_inr: int
    total_expense_inr: int
    beneficiaries_reached: int
    max_grant_managed_inr: int
    growth_rate_yoy: float | None = None
    staff_count: int | None = None

    @property
    def admin_ratio(self) -> float:
        return self.admin_expense_inr / max(self.total_expense_inr, 1)

    @property
    def cost_per_beneficiary_inr(self) -> float:
        return self.programme_expense_inr / max(self.beneficiaries_reached, 1)
```

```python
class TrackRecord(BaseModel):
    projects_total: int
    projects_completed: int
    milestones_met: int
    milestones_total: int
    years_active: int
    past_corporate_partners: list[str] = Field(default_factory=list)

class NgoProfile(BaseModel):
    ngo_id: str
    name: str
    primary_domain: Domain
    secondary_domains: list[Domain] = Field(default_factory=list)
    districts_covered: list[DistrictRef]
    base_district: str
    base_state: str
    proposal_text: str
    budget_request_inr: int
    financials: NgoFinancials
    track_record: TrackRecord
    # Vaishnavi computes trust; you consume it.
    trust_score: int = 0
    trust_badge: TrustBadge = TrustBadge.INCOMPLETE
    status: Literal["ACTIVE", "INELIGIBLE", "FLAGGED"] = "ACTIVE"
    freshness_days: int = 0

class Justification(BaseModel):
    domain_synergy: str
    scale_fit: str
    geographic_overlap: str

class MatchResult(BaseModel):
    ngo_id: str
    name: str
    final_score: float
    semantic_score: float          # calibrated, for display
    semantic_cosine_raw: float     # raw, for ranking and honesty
    trust_score: int
    trust_badge: TrustBadge
    geo_score: float
    budget_request_inr: int
    base_district: str
    base_state: str
    districts_covered: list[str]
    cost_per_beneficiary_inr: float
    flags: list[str] = Field(default_factory=list)
    freshness_days: int = 0
    justification: Justification

class ConsortiumMember(BaseModel):
    ngo_id: str
    name: str
    trust_score: int
    covers: list[RequirementUnit]
    unique_units: int
    budget_share_inr: int
    share_pct: float
    absorptive_cap_inr: int
    capped: bool

class Consortium(BaseModel):
    consortium_id: str
    members: list[ConsortiumMember]
    coverage: float
    redundancy: float
    trust_weighted: float
    coordination_cost: float
    score: float
    beats_best_single_by: float
    unallocated_inr: int
    rationale: str

class CounterfactualAction(BaseModel):
    label: str
    delta_points: float
    resulting_score: float
    resulting_badge: TrustBadge
    effort: Literal["upload", "obtain_registration", "structural"]
    evidence_required: str
    sentence: str                  # the exact line the UI renders

class CounterfactualReport(BaseModel):
    ngo_id: str
    current_score: float
    current_badge: TrustBadge
    achievable_ceiling: float
    actions: list[CounterfactualAction]
```

**Acceptance for A1:** `python -c "import setu_ml.types"` succeeds, and you have pushed to `main` and told the other two it is there.

---

# A2 · `embeddings.py` — local, cached, offline-proof

```python
MODEL_PATH = Path(__file__).parent.parent / "artifacts" / "minilm"

def get_model() -> SentenceTransformer:
    """Singleton. Loads from the committed local path only — never from the network."""

def embed_texts(texts: list[str], normalize: bool = True) -> np.ndarray:
    """(n, 384) float32. Normalised, so cosine similarity is a plain dot product."""

def cosine_matrix(query: np.ndarray, corpus: np.ndarray) -> np.ndarray:
    """(n_query, n_corpus). Assumes both already L2-normalised — assert it."""

def build_ngo_index(ngos: list[NgoProfile]) -> tuple[np.ndarray, list[str]]:
    """Embed proposal_text for every NGO. Returns (matrix, ngo_ids) in matching order."""

def save_index(matrix: np.ndarray, ngo_ids: list[str]) -> None:
    """Write artifacts/ngo_embeddings.npy + ngo_index_manifest.json.
    The manifest stores ngo_ids, model name, dimension, and created_at."""

def load_index() -> tuple[np.ndarray, list[str]]:
    """Load the committed index. Raise a clear, actionable error if absent or if the
    manifest's model name doesn't match the loaded model — a silent dimension or
    model mismatch produces garbage scores that look plausible, which is far worse
    than a crash."""
```

**Two things that matter more than they look.**

*Normalise once, at embed time.* Then cosine similarity is `query @ corpus.T` — one matrix multiply, roughly 15 ms for 1,000 × 384. That is your whole performance story; you do not need a vector database and you should be ready to explain why.

*What text do you embed for an NGO?* Not just the proposal abstract. Build a composite so the encoder sees the whole capability picture:

```python
text = (f"{ngo.name}. Focus: {ngo.primary_domain.value}, "
        f"{', '.join(d.value for d in ngo.secondary_domains)}. "
        f"Operates in: {', '.join(d.district + ', ' + d.state for d in ngo.districts_covered)}. "
        f"{ngo.proposal_text}")
```

Keep this construction in **one function**, `ngo_embedding_text(ngo)`, and use it in both indexing and any re-embedding. Two slightly different constructions in two places is a bug you will lose an hour to.

**Tests:** identical text yields cosine ≈ 1.0; a maternal-health string scores higher against a maternal-health NGO than against a reforestation NGO; `load_index` raises on a manifest/model mismatch; embedding 1,000 texts completes in reasonable time and the matrix is `(1000, 384)` float32.

---

# A3 · `geo.py` — distance and district overlap

```python
def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance. Earth radius 6371.0 km."""

def district_jaccard(mandate_districts: list[str], ngo_districts: list[str]) -> float:
    """Case- and whitespace-normalised set Jaccard. Empty mandate list returns 0.0."""

def min_distance_km(mandate: Mandate, ngo: NgoProfile) -> float:
    """Minimum haversine over all (mandate district, NGO district) pairs.
    Returns inf if either side has no coordinates."""

def geo_score(mandate: Mandate, ngo: NgoProfile) -> float:
    """§5.3:  0.60 * district_jaccard + 0.40 * exp(-min_km / 150.0)
    Clamp to [0,1]. If min_km is inf, the decay term contributes 0."""

def centroid(districts: list[DistrictRef]) -> tuple[float, float]:
    """Mean lat/lng. Used in justification text ('34 km from the mandate centroid')."""
```

Normalise district names through **one** helper — `_norm("Kalahandi ") == _norm("kalahandi")`. Indian district names arrive with inconsistent spacing, casing and occasional transliteration variants; if Jaccard silently returns 0 because of a trailing space, your geo scores are quietly wrong everywhere and nothing crashes to tell you.

**Tests:** Delhi↔Mumbai ≈ 1,150 km (±20); identical district lists give Jaccard 1.0; disjoint lists give 0.0; `geo_score` is in [0,1] for all seed pairs; the same NGO scores higher for a mandate in its own district than for one three states away.

---

# A4 · `extract.py` — natural-language mandate intake

This powers demo beats 1 and 2. It must work **with** an LLM and **without** one, producing the identical schema either way.

```python
def parse_mandate(text: str, llm_client=None) -> Mandate:
    """Primary entry point. Tries the LLM path when a client is supplied and the call
    succeeds; falls back to parse_mandate_rules() on any failure — timeout, bad JSON,
    schema violation, no client. Never raises for a parseable-looking sentence."""

def parse_mandate_rules(text: str) -> Mandate:
    """Deterministic fallback. No network. This is the path that runs on stage."""

def build_requirement_units(mandate: Mandate) -> list[RequirementUnit]:
    """Cartesian product of domains × districts, uniform weight 1.0 unless a district
    was flagged as priority in the raw text (then 1.5). This is what the consortium
    engine consumes — get it right or A7 is meaningless."""

def field_confidence(mandate: Mandate, text: str) -> dict[str, float]:
    """Per-field confidence in [0,1]: 1.0 when a field was matched by an explicit
    pattern, 0.5 when inferred from a keyword, 0.0 when defaulted."""

def clarifying_questions(mandate: Mandate) -> list[str]:
    """One question per field below 0.6 confidence. Maximum 2 — a chat interface that
    interrogates the user is worse than one that makes a visible assumption."""
```

### The rule-based path, concretely

**Budget.** Indian numeric conventions are the whole difficulty and you must handle all of these:

```
"₹50 lakh"  "50 lakhs"  "Rs. 50,00,000"  "50L"  "0.5 crore"  "1.2 Cr"  "INR 5000000"
```

Normalise to integer rupees: `lakh/lac/L → ×100_000`, `crore/cr/Cr → ×10_000_000`. Strip `₹`, `Rs.`, `INR`, and commas — noting that Indian digit grouping is `50,00,000` not `5,000,000`, so never assume groups of three when stripping.

**Domains.** Keyword sets mapping to the `Domain` enum. Be generous with the CSR vocabulary that actually appears in these documents:

```python
DOMAIN_KEYWORDS = {
  Domain.MATERNAL_HEALTH: ["maternal", "pregnan", "postpartum", "antenatal", "institutional delivery",
                           "asha worker", "safe motherhood", "neonatal"],
  Domain.WASH:            ["water", "sanitation", "hygiene", "toilet", "drinking water", "swachh",
                           "handwash", "open defecation"],
  Domain.EDUCATION:       ["education", "school", "literacy", "enrolment", "enrollment", "shiksha",
                           "dropout", "learning outcome", "anganwadi"],
  Domain.SKILLING:        ["skill", "vocational", "employability", "training", "kaushal", "apprentice"],
  # …complete for all ten
}
```

**Geography.** Match against a committed `artifacts/districts_india.json` (district, state, lat, lng, is_aspirational). Match districts first, then states — if only a state is named, expand to that state's districts but mark `field_confidence["districts"] = 0.5` and raise a clarifying question, because "Odisha" and "these three districts of Odisha" are materially different mandates and the consortium engine will behave very differently.

**Preferences.** Detect and record phrases like "prior corporate CSR experience", "prefer women-led", "must have FCRA", "minimum 5 years operating". These do not enter the score in v1 — but returning them proves you understood the sentence, and the UI displays them as chips. Set `foreign_funded=True` if FCRA or foreign funding is mentioned, since that switches on the conditional FCRA pillar in §5.2.

### The LLM path

One function-call with a JSON schema mirroring `Mandate`. Then — non-negotiable — **validate the response through Pydantic and fall back on any validation error**. An LLM that returns `"budget": "50 lakh"` as a string instead of an integer must not take your demo down. Wrap the whole call in a 6-second timeout.

**Tests:** create `tests/fixtures/mandates.json` with **at least 12** hand-written mandate sentences, including the exact demo sentence, one with only a state, one with a crore budget, one with three districts and two domains, one with a preference clause, one deliberately vague ("we want to do something for children"), and one in Hinglish ("Odisha ke rural districts mein maternal health ke liye 50 lakh"). Assert: ≥ 10 of 12 extract budget, ≥ 1 domain and ≥ 1 geography correctly; the vague one produces clarifying questions and low confidence rather than confidently wrong fields; **the rule path alone passes with no network**; `build_requirement_units` on the demo mandate returns exactly `len(domains) × len(districts)` units.

---

# A5 · `scoring.py` + `justify.py` — the composite score

```python
CALIBRATION_LO = 0.15      # loaded from artifacts/calibration.json
CALIBRATION_HI = 0.80

def semantic_score(cosine_raw: float) -> float:
    """§5.1 affine calibration, clipped to [0,1]."""

def composite_score(sem: float, trust_0_100: int, geo: float,
                    weights: dict[str, float] | None = None) -> float:
    """§5.6. Default weights {'semantic':0.50,'trust':0.30,'geo':0.20}.
    Assert the weights sum to 1.0 ± 1e-6 and raise a clear error if not —
    a silently renormalised weight set makes the rank-stability numbers meaningless."""

def rank_ngos(mandate: Mandate, ngos: list[NgoProfile],
              index: tuple[np.ndarray, list[str]],
              weights: dict | None = None, top_k: int = 10) -> list[MatchResult]:
    """The main entry point Vaishnavi calls.
    Order of operations, and it matters:
      1. FILTER OUT status == "INELIGIBLE"  ← before scoring, not after
      2. one matrix multiply for all cosine similarities
      3. geo_score per surviving candidate
      4. composite, sort descending, take top_k
      5. build justifications for the survivors only (never for all 1,000)
    Return top_k results plus, separately, excluded_ineligible_count."""

def keyword_baseline(mandate: Mandate, ngos: list[NgoProfile],
                     top_k: int = 10) -> list[MatchResult]:
    """The naive matcher that makes your A/B toggle honest. §see below."""
```

### The keyword baseline must be a *fair* naive matcher

This is the integrity of demo beat 3. If you cripple the baseline, a sharp judge will notice and you lose more than the feature was worth. Implement what a competent developer would actually write without embeddings:

```python
# tokenise mandate and proposal, drop stopwords, stem lightly (strip plural 's'),
# require an exact token overlap, score = |overlap| / |mandate_tokens|,
# keep anything with score > 0
```

That is a legitimate keyword search. It will still miss "postpartum institutional delivery care" for a "maternal health" mandate — **because that is genuinely how keyword search fails**, not because you sabotaged it. Then:

```python
def compare_engines(semantic: list[MatchResult], keyword: list[MatchResult]) -> dict:
    """Returns keyword_result_count, semantic_result_count,
    missed_by_keyword (ngo_ids in semantic top-5 but absent from keyword results),
    and a headline string. Compute the headline from the data — never hardcode it."""
```

### `justify.py` — three grounded bullets, never a template

Each bullet must contain at least one **specific number or place name from that NGO's record**. Generic sentences are worse than none; a judge reading three identical justifications concludes the whole thing is cosmetic.

```python
def domain_synergy(mandate, ngo) -> str:
    """Name the overlapping domains AND quote a distinctive phrase from proposal_text.
    'Mandate pillar "maternal healthcare" aligns with documented work on postpartum
     institutional delivery care and ASHA-worker training.'"""

def scale_fit(mandate, ngo) -> str:
    """State the request as an amount AND a percentage of the mandate, and compare
    against max_grant_managed_inr — the absorptive-capacity angle nobody else has.
    'Requests ₹42.0L against a ₹50.0L mandate (84%); largest grant previously managed
     was ₹38.0L, so this is within demonstrated absorptive capacity.'
    When the request exceeds 1.5× the historical maximum, say so plainly — that is a
    genuine risk signal and surfacing it builds more trust than hiding it."""

def geographic_overlap(mandate, ngo) -> str:
    """Count overlapping districts, mention Aspirational District status if any,
    and give the real distance from the mandate centroid.
    'Covers 2 of 3 target districts, including 1 NITI Aayog Aspirational District.
     Nearest field office is 34 km from the mandate centroid.'"""

def format_inr(paise_free_rupees: int) -> str:
    """₹42.0L / ₹1.2Cr / ₹8,500. Indian conventions, used everywhere. One function."""
```

**Tests:** ineligible NGOs never appear in `rank_ngos` output; passing different weights changes the ordering; no two justification strings in one result set are identical; every justification contains at least one digit; `keyword_baseline` on the demo mandate returns strictly fewer results than `rank_ngos` and `missed_by_keyword` is non-empty; benchmark `rank_ngos` over 1,000 synthetic NGOs and **assert it completes under 150 ms**.

---

# A6 · Fit the calibration constants — do this at Hour 12, not later

`CALIBRATION_LO = 0.15` and `HI = 0.80` are *starting guesses*. Once the real seed corpus exists, fit them, because if you build the whole UI on an uncalibrated score you may discover at Hour 40 that every match reads "97%" and the display is worthless.

```python
# calibrate.py
def fit_semantic_calibration(mandates: list[Mandate], ngos: list[NgoProfile],
                             index) -> dict:
    """Compute cosine for every mandate × NGO pair. Set
        LO = 5th percentile   (the noise floor)
        HI = 95th percentile  (realistic ceiling — NOT max, which is one lucky pair)
    Write artifacts/calibration.json with LO, HI, the full percentile table,
    n_pairs, model name and fitted_at. Print the distribution so you can eyeball it."""
```

**Sanity check before you move on.** Take the demo mandate and look at the calibrated scores of its top ten NGOs. If they are all above 0.90, or all below 0.40, or bunched inside a five-point band, the calibration is not doing its job — widen or narrow the percentile window and refit. You want the top match somewhere around 0.85–0.92 and the tenth somewhere around 0.45–0.60. That spread is what makes a ranked list *look* like it is discriminating, because it actually is.

And keep this sentence ready, because a good judge will ask what the percentage means:

> *"We rank on raw cosine and display a percentile-calibrated score fitted on our corpus. Raw cosine isn't a percentage — anyone showing you raw cosine as a match percentage is showing you a number that doesn't mean what it looks like."*

---

# A7 ★ · `consortium.py` — the headline feature

**Give this your best hours.** It is the single most differentiating thing in the project: it reframes CSR matching from "sort a list" to "solve a weighted set-cover with constraints", and it answers a real objection that no other team will even raise.

Read `00-PROJECT-CONTEXT.md §5.8` before writing a line. Implement it exactly.

```python
def covered_units(ngo: NgoProfile, units: list[RequirementUnit]) -> list[RequirementUnit]:
    """A unit is covered if the NGO's domains include unit.domain AND its
    districts_covered include unit.district. Both conditions — an education NGO in
    the right district does not cover a WASH unit there. This strictness is the point:
    it is what makes coverage gaps real and the consortium necessary."""

def coverage(members: list[NgoProfile], units: list[RequirementUnit]) -> float:
    """Weighted fraction of units covered by at least one member."""

def redundancy(members: list[NgoProfile], units: list[RequirementUnit]) -> float:
    """§5.8. Overlap fraction — two members covering the same unit is duplicated
    spend. In [0,1]; a disjoint set scores 0."""

def unique_units(member: NgoProfile, others: list[NgoProfile],
                 units: list[RequirementUnit]) -> int:
    """Units this member covers that NO other member covers. Zero means the member
    is a passenger and the set must be rejected."""

def absorptive_cap(ngo: NgoProfile) -> int:
    """int(1.5 * ngo.track_record-derived max_grant_managed_inr).
    Floor at ₹2,00,000 so a first-time NGO isn't capped to nothing."""

def split_budget(members, units, mandate_budget_inr) -> tuple[list[int], int]:
    """Proportional to covered weight, then capped by absorptive_cap.
    Redistribute the residual to members with headroom, iterating until no member has
    both headroom and residual to absorb. Return (shares, unallocated_inr).
    Assert sum(shares) + unallocated == mandate_budget_inr EXACTLY — integer rupees,
    so give any rounding remainder to the largest share. An off-by-₹1 assertion
    failure on stage is a bad way to find out you used floats for money."""

def score_consortium(members, units, mandate) -> float:
    """§5.8:  0.45*coverage + 0.30*trust_weighted + 0.15*(1-redundancy)
              - 0.05*(len(members)-1)
    trust_weighted is BUDGET-WEIGHTED mean trust / 100, not the plain mean — a tiny
    partner with a poor score should not drag down a consortium as much as the
    partner receiving 80% of the money."""

def is_valid(members, units, mandate) -> tuple[bool, str]:
    """All four hard constraints from §5.8. Return (False, human-readable reason) so
    you can debug and so the UI can explain a rejection."""

def find_consortiums(mandate: Mandate, ngos: list[NgoProfile],
                     index, top_n: int = 3) -> list[Consortium]:
    """1. Score all NGOs individually (A5); take the top 12 by final_score.
       2. Compute best single-NGO coverage — the baseline to beat.
       3. Enumerate ALL pairs and triples from those 12: C(12,2)+C(12,3) = 286 sets.
       4. Filter through is_valid(); score the survivors.
       5. Return the top_n by score, with rationale text.
    286 combinations is nothing — this runs in milliseconds and is OPTIMAL over the
    shortlist, which is a much stronger claim than 'greedy'. Say exactly that."""
```

### The rationale string is part of the feature

The UI renders it verbatim and you may end up reading it aloud. Generate it from the actual numbers:

```python
f"No single partner covers {uncovered_desc}. This {len(members)}-partner combination "
f"reaches {coverage:.0%} coverage with {redundancy:.0%} overlap. "
f"{capped_note}"
# capped_note when a member hit its cap:
# "₹3.2L was reallocated because Partner B's share exceeded its demonstrated
#  capacity of ₹18.0L."
```

That capped-note sentence is worth rehearsing. It shows the engine refusing to do something naive, which is a much stronger signal of quality than the engine doing something clever.

**Tests — and construct these by hand so you know the right answer:**

1. **Known-optimal pair.** Three NGOs: X covers units {1,2}, Y covers {3,4}, Z covers {1,2,3}. Assert the engine picks {X,Y} or {Z,Y} — whichever genuinely scores higher — and that you can explain why by hand.
2. **Single wins.** One NGO covers all units. Assert `find_consortiums` returns either nothing or a set whose `beats_best_single_by ≤ 0.10`, and that constraint 4 has rejected the pointless pair.
3. **Passenger rejected.** A pair where one member's coverage is a strict subset of the other's. Assert `is_valid` is False with reason mentioning unique units.
4. **Trust floor.** A pair with perfect coverage where one member has trust 40. Assert rejected, reason mentions the trust floor.
5. **Budget conservation.** Over 50 random consortia: `sum(shares) + unallocated == mandate_budget` exactly, every time.
6. **Capacity cap bites.** An NGO with `max_grant_managed_inr = 800_000` in a ₹50L mandate: assert `capped == True`, its share ≤ ₹12L, and the residual went somewhere accounted for.
7. **The demo case.** On the seeded unfillable mandate: assert best single coverage < 0.70 and at least one returned consortium reaches ≥ 0.95. **This test failing means demo beat 7 does not exist.** Wire it into CI if you have CI, and check it after every change to the seed data.

---

# A8 ★ · `anomaly.py` — cohort-relative fraud statistics

Read §5.4. The methodological point you are making — and should say out loud — is that **global outlier detection is wrong for this problem**: a large urban NGO and a rural micro-NGO have legitimately different cost structures, so comparing them produces false positives on both sides.

```python
def cohort_key(ngo: NgoProfile) -> tuple[str, str, str]:
    """(primary_domain, budget_tier, state_group).
    budget_tier from total_expense_inr: <10L / 10L-50L / 50L-2Cr / >2Cr
    state_group: a coarse north/south/east/west/central/northeast mapping — keep the
    dict in the module and comment that it's a proxy for cost-of-operations, which is
    exactly what it is."""

def robust_z(x: float, values: list[float]) -> float:
    """0.6745 * (x - median) / MAD.
    MAD == 0 (all cohort values identical) returns 0.0, never inf — this WILL happen
    with synthetic data and an inf z-score propagating into a trust score is a
    demo-breaking bug that is invisible until it isn't."""

def detect_anomalies(ngo: NgoProfile, all_ngos: list[NgoProfile]) -> AnomalyReport:
    """Metrics: admin_ratio, cost_per_beneficiary_inr,
               beneficiaries_per_staff, growth_rate_yoy.
    Cohort must have >= 5 members, else return insufficient_cohort=True with
    penalty 0. Never penalise on thin data — and be ready to say that you don't,
    because it's the difference between statistics and theatre.
    Flag when |z| > 3.0. penalty = min(15, 5 * n_flags)."""
```

### The direction of the anomaly is the interesting part

Most people would flag a high admin ratio. Fine — that is waste. The signal almost nobody thinks of is the **opposite** direction on efficiency:

| Metric | Direction | What it means | Flag text |
|---|---|---|---|
| `admin_ratio` | far **above** cohort | overhead-heavy; less money reaches programmes | "Administrative overhead is 3.1σ above comparable organisations (41% vs cohort median 14%)." |
| `cost_per_beneficiary` | far **below** cohort | **claim inflation** — implausibly cheap outcomes usually mean inflated beneficiary counts | "Reports ₹41 per beneficiary against a cohort median of ₹1,180 — 4.2σ below peers. Beneficiary counts require verification." |
| `beneficiaries_per_staff` | far **above** cohort | operationally implausible reach for the headcount | "Claims 12,400 beneficiaries per staff member, 3.7σ above peers." |
| `growth_rate_yoy` | far **above** cohort | sudden unexplained scale-up | "Expenditure grew 340% year-on-year, 3.3σ above peers." |

Write the flag text to include **the actual value, the cohort median, and the σ distance**. "Anomaly detected" is worthless; the sentence above is evidence.

**Tests:** the two seeded claim-inflation NGOs are flagged on `cost_per_beneficiary` with negative z and the flag text says *below*; a normal NGO in a healthy cohort has zero flags; a cohort of 3 returns `insufficient_cohort` with penalty 0; an all-identical cohort returns z = 0 and does not raise; penalty never exceeds 15.

---

# A9 ★ · `counterfactual.py` — the coaching engine

Read §5.9. This is demo beat 8 and the emotional high point of the pitch: *"we don't reject NGOs into a black box, we hand them the roadmap."*

**The one thing that must not go wrong.** The predicted delta has to equal what actually happens when the document is uploaded. If you predict +19 and the recompute yields +14, and a judge notices on stage, the feature becomes evidence against you. So:

> **Both the prediction and the recomputation must call the same trust function.** Coordinate with Vaishnavi: she exposes `compute_trust(ngo, evidence_set) -> TrustBreakdown` as a pure function, and your counterfactual calls it with a *hypothetically augmented* evidence set. You are not re-deriving the arithmetic — you are re-running her function with different inputs. Any other design will drift.

```python
def generate_counterfactual(ngo: NgoProfile,
                            current_breakdown: TrustBreakdown,
                            compute_trust_fn: Callable) -> CounterfactualReport:
    """For each candidate evidence item that is missing or stale:
         1. build a hypothetical evidence set with that item present and fresh
         2. call compute_trust_fn on it
         3. delta = hypothetical.score - current.score
       Classify, filter, rank by delta/effort, return the top 3 plus the ceiling."""

def achievable_ceiling(ngo, current_breakdown, compute_trust_fn) -> float:
    """Score with ALL 'upload'-effort items supplied. This is the honest maximum —
    not 100, which would be a lie for an NGO whose track record limits it."""
```

### Classification — get this right, it is an ethics point as much as a UX one

| Class | Effort | Examples | Show? |
|---|---|---|---|
| Actionable | `upload` (1) | CSR-1 renewal, FY25 audited statements, third-party impact assessment, refreshed 80G, site-visit log | ✅ headline these |
| Structural | `obtain_registration` (5) / `structural` (10) | obtain fresh 12A, reduce admin overhead ratio, complete more projects | ⚠️ show, labelled longer-term |
| **Never show** | — | change historical completion rate, change years active, change past beneficiary counts | ❌ suggesting these is insulting and destroys the tool's credibility with the exact user it is meant to help |

That last row matters. An NGO cannot change its history, and a tool that tells it to is a tool it will never trust again. Enforce it with an explicit `NEVER_SUGGEST` set and a test.

### The sentence the UI renders

```python
f"+{delta:.0f} points — {action_label}. Your score would move from "
f"{current:.0f} → {resulting:.0f} and your badge from '{current_badge}' to '{new_badge}'."
```

Only mention the badge change when the badge actually changes; "from Standard Audited to Standard Audited" reads like a bug.

**Tests:** for the seeded 61-point NGO, the top action is the CSR-1 renewal and the predicted resulting score is 80 ± 1; **a round-trip test that actually adds the evidence, recomputes via `compute_trust_fn`, and asserts the realised delta equals the predicted delta** — this is the most important test in your whole lane; no returned action is in `NEVER_SUGGEST`; `achievable_ceiling ≥ current_score` always; an NGO already at Verified Elite with complete fresh evidence returns an empty action list and a graceful message rather than inventing something.

---

# A10 · `pareto.py` + rank stability *(P2 — build after A7–A9 are solid)*

Two small functions that between them answer the hardest question a judge can ask.

```python
def pareto_front(results: list[MatchResult]) -> list[str]:
    """Non-dominated over (semantic_score, trust_score, -cost_per_beneficiary_inr).
    A dominates B if A >= B on all three and > on at least one. Return ngo_ids.
    O(n²) is fine at n=10. Typically 3-6 survive out of 10 — and 'these are the
    defensible choices, the rest are beaten on every axis' is a strong line."""

def rank_stability(mandate, ngos, index, n_samples: int = 1000,
                   concentration: float = 50.0) -> dict[str, dict]:
    """Sample weights from Dirichlet(alpha = concentration * [0.5, 0.3, 0.2]).
    Re-rank under each sample. For each NGO in the base top 5, report
    p_top1 and p_top3. concentration=50 keeps samples plausibly near the base
    weights rather than exploring nonsense like (0.9, 0.05, 0.05) — state the
    concentration when you present it, because 'we perturbed the weights' invites
    'by how much?' and you want the answer ready.
    1000 samples × 1000 NGOs = one 1000×1000 matmul reused, so this is ~1 second.
    Cache the cosine matrix ONCE outside the loop; recomputing embeddings inside
    the loop turns 1 second into 20 minutes."""
```

Then the answer to *"why 0.5/0.3/0.2?"* becomes a measurement, not an opinion — see §5.6 for the exact phrasing to rehearse.

---

# A11 · `sdg.py` — SDG auto-tagging *(P2, first thing to cut)*

Corporates must report SDG alignment, so this is free reporting value for about 40 minutes of work.

```python
SDG_DESCRIPTIONS = { 1: "No poverty — end poverty in all its forms everywhere", ... 17: ... }

def build_sdg_index() -> np.ndarray:
    """Embed all 17 goal descriptions once; save artifacts/sdg_vectors.npy."""

def tag_sdgs(text: str, top_k: int = 3, threshold: float = 0.30) -> list[dict]:
    """Return [{goal: 3, name: 'Good Health and Well-being', confidence: 0.71}, ...]
    Apply the threshold — returning a weak SDG 14 'Life Below Water' tag for a
    school programme is the kind of visible nonsense that costs credibility on an
    otherwise strong demo."""
```

Use the goal-level descriptions (17), not target-level (169). The extra granularity buys nothing here and the noise is worse.

---

# A12 · Outcome calibration *(P2)*

The closing beat of the pitch. **Claim exactly what this does and nothing more.**

```python
def update_track_record(ngo: NgoProfile, outcome: Outcome) -> TrackRecord:
    """Increment projects_total and, if successful, projects_completed; update
    milestones. This is the real feedback: a completed project genuinely moves the
    O pillar through the Laplace-smoothed formula in §5.2."""

def calibration_curve(outcomes: list[Outcome], n_buckets: int = 5) -> list[dict]:
    """Bucket by predicted_impact decile; return mean predicted vs mean realised per
    bucket, with counts. A well-calibrated system sits on the diagonal."""
```

**Do not say "the model retrains" or "the system learns".** With a synthetic dataset that claim collapses under one follow-up question. Say this instead:

> *"Realised outcomes update the track-record pillar directly, and we report our calibration honestly — here's predicted versus realised. The score becomes better-grounded with every completed project. We're not claiming a trained model; we're claiming a feedback loop that we measure."*

The honest version of this is more impressive than the overclaimed version, because a judge who knows machine learning will spot the overclaim immediately and will then doubt everything else you said.

---

## Testing and definition of done

```powershell
cd C:\Users\Piyush\setu\ml
python -m pytest tests -v
python -m pytest tests/test_perf.py --benchmark-only
```

**Task A is done when all of these are true:**

- [ ] `types.py` merged to `main` in the first hour and both teammates confirmed they're building against it
- [ ] Model loads and matches correctly with the network adapter **disabled**
- [ ] `ngo_embeddings.npy` + manifest committed; nothing embeds NGOs at request time
- [ ] `calibration.json` fitted on the real corpus, distribution eyeballed and sensible
- [ ] `rank_ngos` over 1,000 NGOs benchmarked **under 150 ms**
- [ ] Ineligible NGOs are filtered before scoring, verified by test
- [ ] Every justification cites a real number or place; no two are identical
- [ ] Keyword baseline is a *fair* implementation and `missed_by_keyword` is non-empty on the demo mandate
- [ ] Consortium: all seven tests pass, including the demo case (best single < 0.70, consortium ≥ 0.95)
- [ ] Budget split conserves rupees exactly across 50 randomised runs
- [ ] Anomaly detection flags the seeded claim-inflation cases with directional text; `insufficient_cohort` guard works; MAD = 0 does not produce inf
- [ ] **Counterfactual round-trip test passes: predicted delta == realised delta**
- [ ] Nothing in `NEVER_SUGGEST` is ever returned
- [ ] No HTTP, no database, no `print()` anywhere in `setu_ml/`

## What you say about this work in the pitch

You built the intelligence layer, so you narrate beats 3, 7 and 8, and you take the algorithmic questions. Three things to have loaded and ready:

**On the consortium engine:** *"A real mandate spans multiple domains and districts and one grassroots NGO rarely covers all of it. So we don't sort — we solve a weighted set-cover: maximise coverage, penalise overlap because two partners doing the same thing in the same district is duplicated spend, charge a coordination cost per additional partner, enforce a trust floor because a weak link exposes the whole grant, and cap each partner's share at one and a half times the largest grant they've actually managed. We search all pairs and triples over the top twelve candidates, so it's optimal over the shortlist, in a few milliseconds."*

**On the weights:** the rank-stability answer from §5.6, verbatim.

**On the honest limitation, if asked what's weakest:** *"Our dataset is synthetic. The algorithms are tested and the fraud patterns are detected, but they're patterns we planted — so we know detection works in principle, not in the field. Validating against real registry data is the first thing we'd do with another month."*

---

*`03-TASK-A-ML-INTELLIGENCE.md` · authoritative formulas in `00-PROJECT-CONTEXT.md §5`*

