"""Domain keyword lexicon — shared by extract.py (mandate NLU) and scoring.

Generous with real CSR vocabulary (English + Hinglish + common Hindi terms)
because Indian CSR documents mix registers freely.
"""
from __future__ import annotations

from .types import Domain

DOMAIN_KEYWORDS: dict[Domain, list[str]] = {
    Domain.MATERNAL_HEALTH: [
        "maternal", "maternity", "pregnan", "postpartum", "post-partum", "antenatal",
        "prenatal", "institutional delivery", "safe delivery", "safe childbirth",
        "safe motherhood", "asha worker", "asha didi", "janani", "suraksha", "neonatal",
        "newborn care", "obstetric", "midwife", "maa", "garbh", "prasin",
    ],
    Domain.WASH: [
        "water", "drinking water", "sanitation", "hygiene", "toilet", "latrine",
        "swachh", "swachata", "open defecation", "odf", "handwash", "hand-wash",
        "wash", "jal", "paani", "solid waste", "drainage", "sewer", "borewell",
        "water conservation", "rainwater", "watershed", "jal jeevan",
    ],
    Domain.EDUCATION: [
        "education", "school", "literacy", "enrolment", "enrollment", "shiksha",
        "dropout", "drop-out", "learning outcome", "anganwadi", "balwadi", "teacher",
        "classroom", "digital learning", "scholarship", "vidyalaya", "padhai",
        "girls education", "girl child education", "remedial", "library", "stem",
        "early childhood", "eccd",
    ],
    Domain.HEALTHCARE: [
        "health", "healthcare", "clinic", "hospital", "mobile medical", "medical camp",
        "health camp", "immunization", "immunisation", "vaccination", "tb",
        "tuberculosis", "malaria", "dengue", "anemia", "anaemia", "nutrition screening",
        "primary health", "phc", "chc", "telemedicine", "arogya", "swasthya",
        "medicine", "doctor", "nurse", "screening", "ncd", "diabetes", "cancer",
        "eye care", "cataract", "dental",
    ],
    Domain.ENVIRONMENT: [
        "environment", "reforestation", "afforestation", "tree plantation", "forest",
        "climate", "carbon", "biodiversity", "wildlife", "conservation", "solar",
        "renewable", "clean energy", "pollution", "waste management", "recycling",
        "green", "van", "vriksh", "paryavaran",
    ],
    Domain.SKILLING: [
        "skill", "skills", "skilling", "vocational", "employability", "training",
        "kaushal", "apprentice", "apprenticeship", "placement", "it training",
        "digital literacy", "computer training", "trade", "upskilling", "reskilling",
        "hunar", "capacity building trainings", "pmKVk", "polytechnic", "tvET",
    ],
    Domain.LIVELIHOODS: [
        "livelihood", "livelihoods", "income generation", "self-help group", "shg",
        "microfinance", "micro-enterprise", "entrepreneur", "entrepreneurship",
        "artisan", "handloom", "handicraft", "farmer", "fpo", "agriculture",
        "dairy", "poultry", "goat rearing", "fisheries", "mgnrega", "rojgar",
        "employment", "wage", "value chain", "off-farm", "farm livelihood",
    ],
    Domain.NUTRITION: [
        "nutrition", "nutritional", "malnutrition", "stunting", "wasting",
        "underweight", "anemia prevention", "anaemia prevention", "mid-day meal",
        "mdm", "take home ration", "thr", "poshan", "supplementary nutrition",
        "iron folic", "ifa", "growth monitoring", "feeding", "kaposi", "khadya",
    ],
    Domain.DISABILITY: [
        "disability", "disabled", "divyang", "divyaang", "specially-abled",
        "accessibility", "inclusive education", "assistive", "wheelchair",
        "hearing impaired", "visually impaired", "rehabilitation", "physiotherapy",
        "special needs", "autism", "cerebral palsy", "disability rights",
    ],
    Domain.RURAL_DEVELOPMENT: [
        "rural development", "village development", "gramin", "gram panchayat",
        "community development", "irrigation", "watershed development", "road",
        "electrification", "housing", "shelter", "migration", "community infrastructure",
        "ponga", "gaon", "village", "integrated development", "cluster development",
    ],
}

# Preference phrases — recorded, not scored (v1), displayed as chips by Task C.
PREFERENCE_PHRASES: list[tuple[str, str]] = [
    (r"prior\s+corporate\s+csr\s+experience", "Prior corporate CSR experience"),
    (r"corporate\s+csr\s+experience", "Prior corporate CSR experience"),
    (r"prefer(?:s|ence)?\s+women[- ]led", "Prefer women-led"),
    (r"women[- ]led", "Prefer women-led"),
    (r"must\s+have\s+fcra", "Must have FCRA"),
    (r"fcra[- ]registered", "Must have FCRA"),
    (r"minimum\s+(\d+)\s+years?\s+operating", "Minimum operating experience"),
    (r"minimum\s+(\d+)\s+years?\s+of\s+experience", "Minimum operating experience"),
    (r"(\d+)\+?\s+years?\s+of\s+operating", "Minimum operating experience"),
    (r"experience\s+with\s+aspirational\s+districts", "Aspirational Districts experience"),
    (r"audited\s+financials", "Audited financials expected"),
    (r"prefer(?:s|ence)?\s+local\s+partners", "Prefer local partners"),
]

# Foreign-funding signals — switch on the conditional FCRA pillar (§5.2).
FOREIGN_FUNDING_PHRASES: list[str] = [
    "fcra", "foreign contribution", "foreign fund", "foreign direct",
    "international funding", "global grant", "overseas", "mnC subsidiary",
    "mnc subsidiary", "videsh",
]

# Beneficiary-profile noun phrases worth capturing for display.
BENEFICIARY_PATTERNS: list[tuple[str, str]] = [
    (r"(adolescent|teenage)\s+girls?", "adolescent girls"),
    (r"girls?", "girls"),
    (r"women", "women"),
    (r"(school[- ])?children", "children"),
    (r"(tribal|adivasi)", "tribal communities"),
    (r"(farmers?|kisan)", "farmers"),
    (r"pregnant\s+women", "pregnant women"),
    (r"(maternal|lactating)\s+mothers?", "mothers"),
    (r"youth", "youth"),
    (r"rural\s+(households?|families|communit)", "rural households"),
    (r"persons?\s+with\s+disabilit", "persons with disabilities"),
    (r"elderly|senior\s+citizens?", "elderly"),
    (r"(bpl|below[- ]poverty)", "below-poverty-line households"),
]

# Duration patterns like "over 2 years", "12-month program", "3 year programme"
DURATION_PATTERN: str = (
    r"(?:over|for|across|spanning|duration\s+of|period\s+of)?\s*"
    r"(\d{1,2})\s*(?:[-\s]?year|[-\s]?month|saal|mahin)"
)
