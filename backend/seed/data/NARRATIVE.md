# SETU Demo Narrative (frozen facts — backend/seed/data/NARRATIVE.md)

The seeded world exists to make the ten-beat demo true. Every row below is
asserted in `backend/tests/test_seed_narrative.py`.

| Slot | Value | Where |
|---|---|---|
| Demo mandate | "₹50 lakh for maternal health and clean drinking water across Kalahandi, Nuapada and Balangir in Odisha, prefer partners with prior corporate CSR experience" | mandate `mnd_demo` |
| Requirement units | 6 — {maternal_health, wash} × {Kalahandi, Nuapada, Balangir} | consortium engine |
| Keyword-invisible NGO | **Aarogya Sakhi Foundation** (`ngo_014`) — says "postpartum institutional delivery care", never "maternal"/"health" | beat 3 |
| Top single match | Aarogya Sakhi Foundation · trust 84 · Verified Elite | beat 4 |
| Shell ring (3) | **Sajag Seva Foundation** (`ngo_041`), **Jan Chetna Trust** (`ngo_042`), **Gramin Srijan Society** (`ngo_043`) — shared address + trustee + bank account | beat 6 |
| Consortium members | **Aarogya Sakhi Foundation** (maternal, all 3 districts) + **Jal Seva Odisha** (`ngo_018`, WASH, all 3 districts) | beat 7 |
| Budget split | ₹32,50,000 / ₹17,50,000 — Jal Seva capped (largest prior grant ₹8,00,000 → cap ₹12,00,000) | beat 7 |
| Coached NGO | **Sarthak Shiksha Evam Seva Sansthan** (`ngo_061`) · scores 61 · reaches 80 after CSR-1 renewal + FY audit upload | beat 8 |
| Claim inflators | **Sampark Mahila Sangh** (`ngo_031`), **Vishal Jan Utthan** (`ngo_032`) — ₹~41/beneficiary vs cohort ₹~1,180 | beat 5 / anomaly |
| Missing CSR-1 (4) | ngo_005, ngo_006, ngo_007, ngo_008 — otherwise STRONG (eligibility overrides fit) | beat 4 |
| Expired 80G (3) | ngo_033, ngo_034, ngo_061 | freshness |
| Stale evidence (5) | ngo_035, ngo_036, ngo_037, ngo_038, ngo_061 (14–26 months) | "last verified N months ago" |
| Tampered document | ngo_033's 80G — PAN disagrees with its annual report; financials don't reconcile | forensics |
| CSR deserts (3) | Malkangiri, Nabarangpur, Koraput (Odisha, Aspirational, zero verified partners) | beat 9 |

The 61→80 and consortium numbers are pinned by tests; if a seed regen breaks
them, the test fails BEFORE the stage does.
