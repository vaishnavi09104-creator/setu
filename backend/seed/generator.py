"""seed.generator — the world the demo lives in (B3 ★).

Deterministic (random.seed(42)); everyone's machine produces byte-identical
data. The narrative (NARRATIVE.md) was written FIRST; this generator exists
to satisfy it. All trust numbers are COMPUTED via setu_ml.trust — never
hardcoded — so the counterfactual round-trip is guaranteed by construction.
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

from setu_ml.trust import compute_trust
from setu_ml.types import (
    ComplianceEvidence, Domain, DistrictRef, EvidenceRef,
    NgoFinancials, NgoProfile, TrackRecord, TrustBadge,
)

SEED_DIR = Path(__file__).resolve().parent
DATA_DIR = SEED_DIR / "data"
PDF_DIR = SEED_DIR / "pdfs"

# two-pass build: specs collected first, trust computed over the full cohort
_SPECS: list[dict] = []

OD = {
    "Kalahandi": (19.91, 83.16, True),
    "Nuapada": (20.11, 82.54, True),
    "Balangir": (20.71, 83.48, True),
    "Koraput": (18.81, 82.71, True),
    "Malkangiri": (18.36, 81.99, True),
    "Nabarangpur": (19.23, 82.55, True),
    "Rayagada": (19.38, 83.42, True),
    "Cuttack": (20.46, 85.88, False),
    "Khordha": (20.18, 85.16, False),
    "Sambalpur": (21.47, 83.97, False),
    "Ganjam": (19.39, 84.79, False),
    "Bargarh": (21.33, 83.62, False),
}
MAH = {
    "Gadchiroli": (20.10, 80.02, True),
    "Nagpur": (21.15, 79.09, False),
    "Pune": (18.52, 73.86, False),
    "Nashik": (19.99, 73.79, False),
    "Yavatmal": (20.39, 78.13, True),
    "Nandurbar": (21.75, 74.24, True),
}
CHH = {
    "Bastar": (19.31, 81.96, True),
    "Raipur": (21.25, 81.63, False),
    "Bilaspur": (22.08, 82.15, False),
    "Surguja": (23.12, 83.21, True),
}
JH = {
    "Gumla": (23.04, 84.54, True),
    "Ranchi": (23.34, 85.31, False),
    "Palamu": (24.04, 84.07, True),
}
UP = {
    "Chitrakoot": (25.20, 80.85, True),
    "Lucknow": (26.85, 80.95, False),
    "Balrampur": (27.43, 82.18, True),
}
BR = {"Gaya": (24.79, 85.00, True), "Patna": (25.59, 85.14, False),
      "Muzaffarpur": (26.36, 85.40, True)}
RJ = {"Barmer": (25.75, 71.39, True), "Jaipur": (26.91, 75.79, False),
      "Dungarpur": (23.84, 73.72, True)}
MP = {"Betul": (21.90, 77.90, True), "Bhopal": (23.26, 77.41, False),
      "Jhabua": (22.77, 74.59, True)}
GJ = {"Dahod": (22.84, 74.25, True), "Surat": (21.17, 72.83, False)}

STATE_POOL = [OD, MAH, CHH, JH, UP, BR, RJ, MP, GJ]

# The CSR deserts: high need, zero verified partners (beat 9)
DESERT_NEED = {"Koraput": 0.91, "Malkangiri": 0.93, "Nabarangpur": 0.90}

TODAY = date(2026, 9, 3)


def dref(district: str, state: str, table: dict, need: float | None = None) -> DistrictRef:
    lat, lng, asp = table[district]
    return DistrictRef(
        district=district, state=state, lat=lat, lng=lng,
        is_aspirational=asp,
        # need_index travels as an extra property via model_extra — store on dict later
    ) if need is None else DistrictRef.model_construct(
        district=district, state=state, lat=lat, lng=lng, is_aspirational=asp,
    )


def ev(kind: str, age_days: int = 60, expired: bool = False, doc: str = "doc",
       conf: float = 0.95) -> EvidenceRef:
    return EvidenceRef(
        doc_id=f"{doc}_{kind}", kind=kind, page=1,
        snippet=f"...{kind.replace('_', ' ')} evidence...",
        present=True, is_expired=expired, evidence_age_days=age_days,
        confidence=conf,
    )


def fin(admin: int, prog: int, ben: int, mgm: int, growth: float = 0.08,
        staff: int | None = 24) -> NgoFinancials:
    return NgoFinancials(
        admin_expense_inr=admin, programme_expense_inr=prog,
        total_expense_inr=admin + prog, beneficiaries_reached=ben,
        max_grant_managed_inr=mgm, growth_rate_yoy=growth, staff_count=staff,
    )


def track(total: int, done: int, mm: int, mt: int, yrs: int,
          partners: list[str] | None = None) -> TrackRecord:
    return TrackRecord(
        projects_total=total, projects_completed=done,
        milestones_met=mm, milestones_total=mt, years_active=yrs,
        past_corporate_partners=partners or [],
    )


# --- hand-written proposal texts for demo-critical NGOs -------------------------

P_KEYWORD_INVISIBLE = (
    "Aarogya Sakhi Foundation trains ASHA workers across tribal western Odisha "
    "in postpartum institutional delivery care, newborn warm-chain practices and "
    "safe childbirth referral protocols. Operating from Bhawanipatna since 2011, "
    "our 48-member team runs 12 monthly sub-centre clinics, a 24x7 referral "
    "helpline and a maternal nutrition support programme, reaching 9,800 mothers "
    "and infants annually across Kalahandi, Nuapada and Balangir. Independent "
    "evaluation by the Indian Institute of Public Health found institutional "
    "delivery rates rose 23% in covered villages."
)

P_WASH_PARTNER = (
    "Jal Seva Odisha builds community-managed piped water supply, greywater "
    "drainage and school sanitation blocks in western Odisha. We have completed "
    "31 hand pump rejuvenation clusters and 14 village piped-water schemes across "
    "Kalahandi, Nuapada and Balangir with Panchayat co-financing. Our WASH-in-"
    "schools programme with Swachh Vidyalaya norms reaches 18,000 students; WHO-"
    "aligned water quality testing runs monthly at 22 source points."
)

P_COACHED = (
    "Sarthak Shiksha Evam Seva Sansthan runs remedial learning centres and "
    "digital literacy labs for first-generation learners in Kalahandi district, "
    "with a 9-year operating history, 7 completed projects, and a girls' "
    "retention programme cited by the District Education Office. Our financial "
    "governance is strong — 15% administrative ratio — and our oldest partner "
    "grant was ₹22 lakh. We are preparing for CSR-1 renewal this quarter."
)

SHELL_TRUSTEE = "Sureshchandra Rathi"
SHELL_ADDRESS = "Plot 14, Gandhi Nagar, Station Road, Bhubaneswar, Odisha 751001"
SHELL_BANK = ("SBIN0007510", "5678")


def _shell_identifiers(email_domain: str) -> dict:
    return {
        "address": SHELL_ADDRESS,
        "phone": "+91 674 2575678",
        "trustees": [SHELL_TRUSTEE, "Manisha Kulkarni"],
        "bank_ifsc": SHELL_BANK[0],
        "bank_account_last4": SHELL_BANK[1],
        "email": f"contact@{email_domain}",
    }


def _districts(state_name: str, table: dict, names: list[str]) -> list[DistrictRef]:
    out = []
    for n in names:
        lat, lng, asp = table[n]
        out.append(DistrictRef(district=n, state=state_name, lat=lat, lng=lng,
                                is_aspirational=asp))
    return out


def build_world() -> list[dict]:
    """48 NGOs — hand-authored narrative cases first, deterministic filler after."""
    rng = random.Random(42)
    world: list[dict] = []
    _SPECS.clear()  # a fresh call builds a fresh world — no cross-call leakage

    def add(ngo_id: str, name: str, primary: Domain, secondary: list[Domain],
            districts: list[DistrictRef], base_district: str, state: str,
            proposal: str, budget: int, financials: NgoFinancials,
            tr: TrackRecord, evidence: ComplianceEvidence,
            identifiers: dict | None = None, need: float = 0.5) -> dict:
        # two-pass world build handled below; anomaly needs the full cohort,
        # so `add` stores specs and compute_trust runs once all 48 exist.
        spec = {
            "ngo_id": ngo_id, "name": name, "primary": primary,
            "secondary": secondary, "districts": districts,
            "base_district": base_district, "state": state,
            "proposal": proposal, "budget": budget, "financials": financials,
            "track": tr, "evidence": evidence, "identifiers": identifiers,
            "need": need,
        }
        _SPECS.append(spec)
        return spec

    # ============ the demo-critical cast (hand-written) ====================

    # 1. KEYWORD-INVISIBLE + top match + consortium member 1 — ngo_014
    add(
        "ngo_014", "Aarogya Sakhi Foundation",
        Domain.MATERNAL_HEALTH, [],
        _districts("Odisha", OD, ["Kalahandi", "Nuapada", "Balangir"]),
        "Kalahandi", "Odisha",
        P_KEYWORD_INVISIBLE,
        4_200_000,
        fin(1_100_000, 9_400_000, 8_900, 3_800_000, growth=0.11, staff=48),
        track(12, 11, 34, 36, 14, ["Tata Trusts", "L&T"]),
        ComplianceEvidence(
            csr1=ev("csr1", 96, doc="doc_031"),
            reg_12a=ev("reg_12a", 96), reg_80g=ev("reg_80g", 96),
            darpan=ev("darpan", 96), audit_fy=ev("audit_fy", 90),
            third_party_audit=ev("third_party_audit", 120),
            impact_assessment=ev("impact_assessment", 150),
        ),
        need=0.82,
    )

    # 2. WASH partner + consortium member 2 (capped) — ngo_018
    add(
        "ngo_018", "Jal Seva Odisha",
        Domain.WASH, [],
        _districts("Odisha", OD, ["Kalahandi", "Nuapada", "Balangir"]),
        "Nuapada", "Odisha",
        P_WASH_PARTNER,
        1_400_000,
        fin(220_000, 1_780_000, 2_600, 800_000, growth=0.14, staff=11),
        track(9, 8, 24, 27, 8, ["Nabard"]),
        ComplianceEvidence(
            csr1=ev("csr1", 120, doc="doc_036"),
            reg_12a=ev("reg_12a", 200), reg_80g=ev("reg_80g", 180),
            darpan=ev("darpan", 150), audit_fy=ev("audit_fy", 150),
            third_party_audit=ev("third_party_audit", 240),
        ),
        need=0.80,
    )

    # 3. THE COACHED NGO — ngo_061: lands 61 → 80 (test-pinned)
    add(
        "ngo_061", "Sarthak Shiksha Evam Seva Sansthan",
        Domain.EDUCATION, [Domain.SKILLING],
        _districts("Odisha", OD, ["Kalahandi"]),
        "Kalahandi", "Odisha",
        P_COACHED,
        2_400_000,
        fin(1_000_000, 9_000_000, 7_400, 2_200_000, growth=0.09, staff=24),
        track(12, 10, 30, 40, 8, ["Axis Bank Foundation"]),
        ComplianceEvidence(
            csr1=ev("csr1", 700, expired=True, doc="doc_061"),
            reg_12a=ev("reg_12a", 260), reg_80g=ev("reg_80g", 300),
            darpan=ev("darpan", 200), audit_fy=ev("audit_fy", 720),
            third_party_audit=ev("third_party_audit", 560),
            impact_assessment=ev("impact_assessment", 900),
        ),
        need=0.75,
    )

    # 4-6. THE SHELL RING — ngo_041/042/043
    ring_specs = [
        ("ngo_041", "Sajag Seva Foundation", Domain.EDUCATION,
         "Sajag Seva Foundation runs tuition centres and scholarship guidance "
         "for underprivileged students in urban Bhubaneswar."),
        ("ngo_042", "Jan Chetna Trust", Domain.SKILLING,
         "Jan Chetna Trust provides vocational training in tailoring and "
         "computer basics for unemployed youth of Khordha."),
        ("ngo_043", "Gramin Srijan Society", Domain.LIVELIHOODS,
         "Gramin Srijan Society promotes self-help-group lending and grain-bank "
         "enterprises across coastal Odisha."),
    ]
    for i, (nid, name, dom, prop) in enumerate(ring_specs):
        add(
            nid, name, dom, [],
            _districts("Odisha", OD, ["Khordha"]),
            "Khordha", "Odisha", prop,
            2_000_000 + i * 250_000,
            fin(1_600_000, 2_400_000, 3_100, 1_500_000, growth=0.06, staff=9),
            track(5, 4, 12, 15, 6),
            ComplianceEvidence(
                csr1=ev("csr1", 200, doc=f"doc_{nid}"),
                reg_12a=ev("reg_12a", 220), reg_80g=ev("reg_80g", 240),
                darpan=ev("darpan", 210), audit_fy=ev("audit_fy", 260),
            ),
            identifiers=_shell_identifiers(f"{['sajagseva', 'janchetna', 'graminsrijan'][i]}.org"),
        )

    # 7-8. CLAIM INFLATORS — ngo_031/032 (education cohort, ₹~41/beneficiary)
    #    Plus four normal cohort-mates so the median/MAD statistics are
    #    meaningful (5-member cohort with 2 outliers kills the MAD — the
    #    planted ring of normal peers keeps the z-score honest).
    _cohort_mates = [
        ("ngo_021", "Vidya Vistar Sanstha"),
        ("ngo_022", "Gyan Jyoti Shiksha Kendra"),
        ("ngo_023", "Siksha Sathi Network"),
        ("ngo_024", "Adarsh Vidya Mandir Trust"),
    ]
    for nid, name in _cohort_mates:
        add(
            nid, name, Domain.EDUCATION, [],
            _districts("Odisha", OD, ["Cuttack", "Sambalpur"]),
            "Cuttack", "Odisha",
            f"{name} runs teacher-training, remedial literacy and digital "
            f"classroom programmes across coastal and western Odisha.",
            2_000_000,
            fin(1_000_000, 9_000_000, 7_500, 2_800_000, growth=0.08, staff=22),
            track(10, 9, 28, 32, 8),
            ComplianceEvidence(
                csr1=ev("csr1", 120, doc=f"doc_{nid}"),
                reg_12a=ev("reg_12a", 130), reg_80g=ev("reg_80g", 140),
                darpan=ev("darpan", 120), audit_fy=ev("audit_fy", 150),
                third_party_audit=ev("third_party_audit", 160),
            ),
        )
    for nid, name, dom in [
        ("ngo_031", "Sampark Mahila Sangh", Domain.EDUCATION),
        ("ngo_032", "Vishal Jan Utthan", Domain.EDUCATION),
    ]:
        add(
            nid, name, dom, [],
            _districts("Odisha", OD, ["Ganjam", "Bargarh"]),
            "Ganjam", "Odisha",
            f"{name} operates large-scale community education drives with "
            f"digitally monitored attendance across Ganjam and Bargarh.",
            1_800_000,
            fin(850_000, 8_150_000, 198_000, 1_600_000, growth=0.42, staff=18),
            track(7, 6, 20, 24, 5),
            ComplianceEvidence(
                csr1=ev("csr1", 150, doc=f"doc_{nid}"),
                reg_12a=ev("reg_12a", 150), reg_80g=ev("reg_80g", 160),
                darpan=ev("darpan", 140), audit_fy=ev("audit_fy", 170),
            ),
        )

    # 9. TAMPERED DOCUMENT NGO — ngo_033: 80G PAN disagrees across docs,
    #    financials don't reconcile (forensics trip-wire)
    add(
        "ngo_033", "Nirmal Nagar Seva Samiti",
        Domain.WASH, [],
        _districts("Odisha", OD, ["Cuttack", "Sambalpur"]),
        "Cuttack", "Odisha",
        "Nirmal Nagar Seva Samiti builds community toilets and runs waste-"
        "segregation awareness in Cuttack and Sambalpur municipalities.",
        2_600_000,
        fin(1_400_000, 6_100_000, 5_200, 2_100_000, growth=0.10, staff=22),
        track(8, 7, 22, 26, 7),
        ComplianceEvidence(
            csr1=ev("csr1", 300, doc="doc_033"),
            reg_12a=ev("reg_12a", 310), reg_80g=ev("reg_80g", 320),
            darpan=ev("darpan", 300), audit_fy=ev("audit_fy", 330),
            third_party_audit=ev("third_party_audit", 300),
        ),
    )

    # 10-13. MISSING CSR-1 (4) — otherwise STRONG so eligibility overrides fit.
    # Constrained to NON-desert districts so the CSR deserts stay empty.
    non_desert_od = {k: v for k, v in OD.items() if k not in DESERT_NEED}
    for idx, (nid, name, dom) in enumerate([
        ("ngo_005", "Unnati Rural Development Association", Domain.RURAL_DEVELOPMENT),
        ("ngo_006", "Pragati Kisan Producer Collective", Domain.LIVELIHOODS),
        ("ngo_007", "Bal Vidya Shiksha Mission", Domain.EDUCATION),
        ("ngo_008", "Sehat Community Clinics Network", Domain.HEALTHCARE),
    ]):
        if idx % 2 == 0:
            state, table = "Odisha", non_desert_od
        else:
            state, table = "Maharashtra", MAH
        dnames = rng.sample(sorted(table), 2)
        add(
            nid, name, dom, [],
            _districts(state, table, dnames), dnames[0], state,
            f"{name} delivers high-quality, well-evaluated programmes in {state} "
            f"with strong governance — but has not yet filed Form CSR-1, so it "
            f"cannot legally receive CSR funds.",
            3_500_000,
            fin(1_200_000, 8_800_000, 8_200, 3_100_000, growth=0.09),
            track(11, 10, 30, 33, 10, ["HDFC Parivartan"]),
            ComplianceEvidence(
                csr1=None,  # ← the point
                reg_12a=ev("reg_12a", 120), reg_80g=ev("reg_80g", 120),
                darpan=ev("darpan", 110), audit_fy=ev("audit_fy", 130),
                third_party_audit=ev("third_party_audit", 150),
                impact_assessment=ev("impact_assessment", 160),
            ),
        )

    # 14. EXPIRED 80G (3): ngo_034 + reuse ngo_033 + ngo_061
    add(
        "ngo_034", "Shikhar Yuva Vikas Mandal",
        Domain.SKILLING, [],
        _districts("Rajasthan", RJ, ["Jaipur", "Barmer"]),
        "Jaipur", "Rajasthan",
        "Shikhar Yuva Vikas Mandal runs trades training — electrical, plumbing, "
        "solar technician — with placement support in Jaipur and Barmer.",
        1_900_000,
        fin(1_500_000, 6_500_000, 4_800, 1_700_000, growth=0.12, staff=19),
        track(9, 7, 24, 28, 8),
        ComplianceEvidence(
            csr1=ev("csr1", 170, doc="doc_034"),
            reg_12a=ev("reg_12a", 170),
            reg_80g=ev("reg_80g", 480, expired=True),  # expired 16 months ago
            darpan=ev("darpan", 160), audit_fy=ev("audit_fy", 200),
            third_party_audit=ev("third_party_audit", 210),
        ),
    )

    # 15-19. STALE EVIDENCE (5): ngo_035..038 + ngo_061 already stale
    for nid, name, dom, state, table in [
        ("ngo_035", "Van Seva Anusandhan Kendra", Domain.ENVIRONMENT, "Gujarat", GJ),
        ("ngo_036", "Sahyog Apang Punarvas Kendra", Domain.DISABILITY, "Maharashtra", MAH),
        ("ngo_037", "Aahar Poshan Abhiyan Network", Domain.NUTRITION, "Madhya Pradesh", MP),
        ("ngo_038", "Samarth Seniors' Care Trust", Domain.HEALTHCARE, "Chhattisgarh", CHH),
    ]:
        dnames = rng.sample(list(table), 2)
        add(
            nid, name, dom, [],
            _districts(state, table, dnames), dnames[0], state,
            f"{name} has delivered steady work in {state} since the late 2010s; "
            f"its last independent verification cycle is now well over a year old.",
            2_200_000,
            fin(1_700_000, 7_300_000, 6_400, 2_400_000, growth=0.07, staff=26),
            track(10, 9, 27, 30, 9),
            ComplianceEvidence(
                csr1=ev("csr1", 500, doc=f"doc_{nid}"),
                reg_12a=ev("reg_12a", 620), reg_80g=ev("reg_80g", 700),
                darpan=ev("darpan", 640), audit_fy=ev("audit_fy", 760),
                third_party_audit=ev("third_party_audit", 690),
            ),
        )

    # ============ deterministic filler to reach 48 across 8+ states ========

    DOMAIN_CYCLE = [Domain.EDUCATION, Domain.HEALTHCARE, Domain.WASH,
                    Domain.ENVIRONMENT, Domain.SKILLING, Domain.LIVELIHOODS,
                    Domain.NUTRITION, Domain.DISABILITY, Domain.RURAL_DEVELOPMENT,
                    Domain.MATERNAL_HEALTH]
    TEMPLATE_VERBS = [
        "runs", "operates", "delivers", "coordinates", "facilitates",
        "manages", "supports", "implements",
    ]
    PROGRAMMES = {
        Domain.EDUCATION: ["remedial learning centres", "digital classrooms",
                           "library networks", "teacher coaching programmes"],
        Domain.HEALTHCARE: ["mobile medical camps", "immunisation drives",
                           "eye-care outreach", "NCD screening clinics"],
        Domain.WASH: ["hand pump rejuvenation", "school sanitation blocks",
                      "greywater drainage", "water-quality testing"],
        Domain.ENVIRONMENT: ["community afforestation", "nursery raising",
                             "waste segregation units", "solar street lighting"],
        Domain.SKILLING: ["industrial trades training", "digital literacy bootcamps",
                          "apprenticeship placement", "entrepreneurship mentoring"],
        Domain.LIVELIHOODS: ["self-help group lending", "dairy value chains",
                             "artisan clusters", "seed banks"],
        Domain.NUTRITION: ["take-home ration units", "growth monitoring camps",
                           "kitchen gardens", "anaemia screening"],
        Domain.DISABILITY: ["inclusive classrooms", "assistive device banks",
                            "rehabilitation camps", "caregiver training"],
        Domain.RURAL_DEVELOPMENT: ["watershed works", "village road upgradation",
                                    "irrigation channels", "community halls"],
        Domain.MATERNAL_HEALTH: ["ASHA mentoring", "sub-centre clinics",
                                  "referral transport", "nutrition support"],
    }

    existing_ids = {s["ngo_id"] for s in _SPECS}
    # deserts must stay EMPTY by construction — filler never samples them
    filler_tables = [
        ("Odisha", {k: v for k, v in OD.items() if k not in DESERT_NEED}),
        ("Maharashtra", MAH), ("Chhattisgarh", CHH),
        ("Jharkhand", JH), ("Uttar Pradesh", UP), ("Bihar", BR),
        ("Rajasthan", RJ), ("Madhya Pradesh", MP), ("Gujarat", GJ),
    ]
    filler_n = 48 - len(_SPECS)

    # build the id list FIRST (skip ids the hand-written cast already used)
    filler_ids: list[str] = []
    i = 0
    while len(filler_ids) < filler_n:
        nid = f"ngo_{i + 1:03d}"
        i += 1
        if nid not in existing_ids:
            filler_ids.append(nid)

    for slot, nid in enumerate(filler_ids):
        state_name, table = filler_tables[slot % 9]
        dom = DOMAIN_CYCLE[slot % len(DOMAIN_CYCLE)]
        dnames = rng.sample(list(table), k=min(2, len(table)))
        prog = rng.choice(PROGRAMMES[dom])
        verb = rng.choice(TEMPLATE_VERBS)
        n_ben = rng.randint(1_800, 24_000)
        spend = rng.randint(2_000_000, 14_000_000)
        admin_ratio = rng.choice([0.08, 0.10, 0.12, 0.14, 0.16, 0.18])
        staff = max(4, n_ben // rng.randint(300, 900))
        proposal = (
            f"Organisation {nid.replace('_', ' ')} {verb} {prog} across "
            f"{', '.join(dnames)} in {state_name}, reaching approximately "
            f"{n_ben:,} beneficiaries annually through community institutions "
            f"and local partnership models."
        )
        age_csr1 = rng.choice([80, 120, 160, 200, 300])
        add(
            nid, f"{rng.choice(['Adarsh', 'Navya', 'Sushiksha', 'Ujjwal', 'Prayas', 'Chetna', 'Disha', 'Kalyan', 'Vikas', 'Samarth'])} "
                 f"{rng.choice(['Seva', 'Kendra', 'Foundation', 'Sansthan', 'Mandal', 'Sangh', 'Trust', 'Mission'])} "
                 f"{rng.choice([str(2000 + rng.randint(0, 22)), 'Odisha', 'Bharat', 'Gramin', 'Jan'])}",
            dom, [],
            _districts(state_name, table, dnames), dnames[0], state_name,
            proposal,
            rng.randint(1_000_000, 6_000_000),
            fin(int(spend * admin_ratio), spend - int(spend * admin_ratio),
                n_ben, rng.randint(800_000, 4_000_000),
                growth=round(rng.uniform(0.02, 0.25), 2), staff=staff),
            track(rng.randint(4, 18), rng.randint(3, 16),
                  rng.randint(10, 40), rng.randint(12, 44),
                  rng.randint(2, 15)),
            ComplianceEvidence(
                csr1=ev("csr1", age_csr1, doc=f"doc_{nid}"),
                reg_12a=ev("reg_12a", age_csr1 + 30),
                reg_80g=ev("reg_80g", age_csr1 + 45),
                darpan=ev("darpan", age_csr1 - 10 if age_csr1 > 10 else 10),
                audit_fy=ev("audit_fy", age_csr1 + 60),
                third_party_audit=ev("third_party_audit", age_csr1 + 90)
                if rng.random() > 0.4 else None,
                impact_assessment=ev("impact_assessment", age_csr1 + 120)
                if rng.random() > 0.6 else None,
                site_visit_log=ev("site_visit_log", age_csr1 + 40)
                if rng.random() > 0.5 else None,
            ),
        )

    # ============ pass 2: compute trust over the FULL cohort =================
    # Same pipeline as the endpoint (compute_for_ngo): anomaly detection sees
    # all 48, so seeded scores == live scores by construction.
    from setu_ml.anomaly import detect_anomalies

    profiles = [
        NgoProfile(
            ngo_id=s["ngo_id"], name=s["name"], primary_domain=s["primary"],
            secondary_domains=s["secondary"], districts_covered=s["districts"],
            base_district=s["base_district"], base_state=s["state"],
            proposal_text=s["proposal"], budget_request_inr=s["budget"],
            financials=s["financials"], track_record=s["track"],
        )
        for s in _SPECS
    ]

    world: list[dict] = []
    for i, (s, p) in enumerate(zip(_SPECS, profiles)):
        anomaly = detect_anomalies(p, profiles)
        breakdown = compute_trust(p, s["evidence"], anomaly=anomaly)
        doc = p.model_dump()
        for dd in doc["districts_covered"]:
            dd["need_index"] = DESERT_NEED.get(dd["district"], s["need"])
        doc["evidence"] = {
            k: v.model_dump() for k, v in s["evidence"].items().items() if v
        }
        if s["identifiers"]:
            doc["identifiers"] = s["identifiers"]
        else:
            doc["identifiers"] = {
                "address": f"Ward {rng.randint(1, 12)}, {s['base_district']}, "
                           f"{s['state']} {rng.randint(100001, 855999)}",
                "phone": f"+91 {rng.randint(70, 99)}{rng.randint(10000000, 99999999)}",
                "trustees": [f"Trustee {s['ngo_id']} A", f"Trustee {s['ngo_id']} B"],
                "bank_ifsc": f"SBIN{rng.randint(100000, 999999)}",
                "bank_account_last4": f"{rng.randint(1000, 9999)}",
                "email": f"contact@{s['ngo_id']}.org.in",
            }
        doc["need_index"] = s["need"]
        doc["trust"] = {
            "score": round(breakdown.score), "badge": breakdown.badge.value,
            "freshness_days": min(
                (pl.freshness_days for pl in breakdown.pillars if pl.freshness_days),
                default=60),
            "input_hash": breakdown.input_hash,
        }
        doc["status"] = "INELIGIBLE" if breakdown.is_ineligible else "ACTIVE"
        world.append(doc)

    _SPECS.clear()
    return world
