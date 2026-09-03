# TASK C — Console, GIS & Narrative

**Owner:** third member · **Folder:** `frontend/` · **Stack:** Next.js 14 (App Router), TypeScript, Tailwind, Lucide, Recharts, Leaflet

---

## How to use this document

Paste `00-PROJECT-CONTEXT.md` §0–10 into your AI IDE first, then paste this file. The API contract in §6 is frozen — code against it and do not negotiate field names in chat. If something in the contract genuinely does not work for the UI, raise it at a checkpoint and get it changed in the document, so all three of us change together.

You own `frontend/` and nothing else. You do not write Python. You never edit `ml/` or `backend/`.

---

## Read this before you write a line of code

**You are building the thing that gets judged.** Piyush's optimiser and Vaishnavi's forensics are the substance, but a panel experiences all of it through your screen, in four minutes, from ten feet away. Every point the project earns is a point you rendered. That is not pressure, it is leverage: a mediocre model behind an interface that makes its reasoning obvious will beat a better model behind a wall of JSON, every single time.

**Three consequences you should internalise now.**

Never block on the backend. Vaishnavi ships a mocked API at Hour 8 that returns contract-shaped data for every endpoint. Build against it from Hour 4. If the mock is late, write your own fixtures from the §6 examples and keep moving — waiting is the most expensive thing you can do in this lane.

Legibility beats density. A judge cannot read a table of eleven numbers. They can read one number, one badge, and one sentence that explains the number. Every screen should survive the ten-foot test: stand back from your laptop and see whether the point of the screen is still obvious.

Nothing on screen may be unexplained. Every score has a "why", every badge has a text label as well as a colour, every claim has something to click into. The demo's core move is *click into the number and find a document page*. That drill-down is worth more than any three cosmetic features.

---

## Setup, exact PowerShell

```powershell
cd C:\Users\Piyush\setu
npx create-next-app@14 frontend --typescript --tailwind --eslint --app --src-dir --no-import-alias
cd frontend
npm install lucide-react recharts leaflet react-leaflet@4 clsx
npm install -D @types/leaflet
npm run dev
```

`.env.local` (never committed):

```
NEXT_PUBLIC_API_BASE=http://localhost:8000
NEXT_PUBLIC_USE_FIXTURES=false
NEXT_PUBLIC_DEMO_MODE=true
```

Commit `.env.local.example` with the same keys and no values.

## Repo layout you own

```
frontend/
  src/
    app/
      layout.tsx                 # shell, role switcher, latency badge
      page.tsx                   # corporate console (default view)
      ngo/[id]/page.tsx          # NGO self-service view (counterfactual coach)
      map/page.tsx               # GIS demand-vs-supply
      admin/page.tsx             # audit log + forensics (P2)
    components/
      MandateChat.tsx            # C1
      MandateSummary.tsx         # C1
      PartnerCard.tsx            # C2
      RankedDeck.tsx             # C2
      ModeToggle.tsx             # C3  ★ never cut
      TrustDossier.tsx           # C4
      PillarBar.tsx              # C4
      EvidenceViewer.tsx         # C5  ★ never cut
      ShellNetworkGraph.tsx      # C6
      ConsortiumPanel.tsx        # C7  ★ never cut
      CounterfactualCoach.tsx    # C8  ★ never cut
      CoverageMap.tsx            # C9
      ComparisonMatrix.tsx       # C10
      RiskSummary.tsx            # C11  "₹ at risk"
      WeightSliders.tsx          # C12
      LatencyBadge.tsx           # C13
      Badge.tsx  Gauge.tsx  Skeleton.tsx  EmptyState.tsx
    lib/
      api.ts                     # typed client + fixture fallback
      types.ts                   # mirrors ml/setu_ml/types.py — hand-transcribed
      format.ts                  # ₹ lakh/crore formatting, dates, percentages
      colors.ts                  # badge + domain palettes in ONE place
    fixtures/                    # captured live responses, committed
  public/
    geo/districts.json           # bundled district GeoJSON — no CDN at demo time
```

**`lib/types.ts` is transcribed from Piyush's `ml/setu_ml/types.py`.** Do it by hand, once, at Hour 4, and re-check it at Hour 16 and Hour 32. Field names are snake_case on the wire; do not camelCase them in your client or you will spend twenty minutes at Hour 45 wondering why `trust_score` is undefined.

---

## Design system — decide it once, at Hour 4, then stop thinking about it

Dark text on light background. Judges see your screen on a projector in a lit room; dark themes wash out and low-contrast greys vanish entirely.

```
Surface        #FFFFFF   Card     #F8FAFC   Border   #E2E8F0
Text primary   #0F172A   Muted    #475569
Accent         #1D4ED8   (one accent colour, used sparingly)

Badge palette — must always carry a TEXT LABEL as well as the colour:
  Verified Elite            emerald  #059669
  Standard Audited          amber    #D97706
  Verification Incomplete   slate    #64748B
  High Risk — Review        rose     #E11D48
  Ineligible for CSR Funds  rose     #9F1239  + strikethrough treatment
```

Roughly one in twelve men has a colour-vision deficiency, so there is a real chance somebody on your panel cannot distinguish your emerald from your amber. Every badge carries its words. This is in the PRD as NFR-8 and it is not decoration — it is the difference between a judge reading your screen and a judge guessing at it.

Type: `text-3xl font-semibold` for the one number that matters on a screen, `text-sm` for body, `text-xs uppercase tracking-wide text-slate-500` for labels. Numbers in `tabular-nums` so columns line up. Set browser zoom to 125% during rehearsal and design at that size.

Motion: 150–200 ms transitions on state change, and **animate the trust gauge when the counterfactual toggles** — that single animation is what makes the coaching feature land emotionally. Nothing else needs to move.

---

# C0 · `lib/api.ts` — build the resilience now, not at Hour 45

This file is the reason your demo survives a dead backend. Write it at Hour 4, before any component.

```ts
const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const FORCE_FIXTURES = process.env.NEXT_PUBLIC_USE_FIXTURES === "true";

export type ApiResult<T> = { data: T; source: "live" | "fixture"; latencyMs: number };

async function call<T>(path: string, init?: RequestInit, fixture?: string): Promise<ApiResult<T>> {
  if (FORCE_FIXTURES && fixture) return fromFixture<T>(fixture);
  const t0 = performance.now();
  try {
    const res = await fetch(`${BASE}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
      signal: AbortSignal.timeout(8000),
    });
    if (!res.ok) throw new Error(`${res.status}`);
    return { data: await res.json(), source: "live", latencyMs: performance.now() - t0 };
  } catch {
    if (fixture) return fromFixture<T>(fixture);   // silent, automatic, invisible
    throw new ApiError(path);
  }
}
```

Every call site passes a fixture name. When the backend dies mid-demo the UI keeps working and the only visible change is a small `offline` chip in the header — which you can either point at honestly ("we run fully offline") or ignore. Both are fine. A crash is not.

One typed function per endpoint: `parseMandate`, `createMandate`, `runMatch`, `getNgo`, `getTrust`, `getCounterfactual`, `getNetwork`, `uploadDocument`, `verifyDocument`, `getCoverage`, `getNearby`, `createRfp`, `getAudit`. No raw `fetch` anywhere else in the codebase.

**Test it deliberately at Hour 42:** kill the backend, reload every page, click the entire demo path. If anything shows a stack trace or an infinite spinner, fix it — that is a higher priority than any remaining feature.

---

# C1 · Mandate intake — chat, because a form would be forgettable

Left panel: a conversational input. Right panel: a live-updating structured summary. The split-screen *is* the pitch — natural language on the left becoming machine-readable requirements on the right, in front of the judge, in one gesture.

```tsx
<MandateChat onParsed={(m: ParsedMandate) => void} />
```

Flow: user types or clicks a preset → `POST /api/mandates/parse` → summary card populates field by field with a brief stagger → each field shows a **confidence chip** (`high` / `medium` / `low`) → any field is click-to-edit → clarifying questions from the API render as chips the user can answer in one tap → "Find Partners" calls `POST /api/mandates` then `POST /api/match`.

Three preset buttons, because typing on stage is a needless risk:

1. The demo mandate — the one from `06-PITCH-AND-DEMO-RUNBOOK.md`, verbatim.
2. The unfillable mandate — triggers the consortium path.
3. A Hinglish mandate — "humein rural Maharashtra mein girls ki education ke liye partner chahiye, budget 40 lakh" — proves the parser is not doing keyword lookup on English.

Show the low-confidence fields differently (amber left border, not a warning icon). A system that admits it is unsure about the district but certain about the budget reads as engineered; one that claims 100% confidence on everything reads as a demo.

`EmptyState` and `Skeleton` for every async region. No layout shift when data arrives — reserve the height.

---

# C2 · Ranked partner deck

`RankedDeck` renders `results[]` from `POST /api/match`. Each `PartnerCard` shows, in this visual priority:

The NGO name and district on top. The **trust badge with its text label**. The composite score as a large number with a thin three-segment bar underneath showing the semantic / trust / geo contributions — so the weighting is visible without a legend. Then the **three justification bullets**, each of which cites a real number or a real place, because Piyush's `justify()` guarantees that. Then a compact row: years active, beneficiaries reached, cost per beneficiary, admin ratio. Then two actions: *View Dossier* and *Add to Comparison*.

Cards are keyboard reachable and the whole deck is arrow-navigable. Rank number in a circle at the top-left — judges refer to "the third one" and you want that to be unambiguous.

If `unmatched_warning` is true, replace the deck with an honest panel: "No strong match found. The closest organisations are shown below with low confidence, and here is what a suitable partner would need to look like." Most teams will never build this state. Showing a system that knows when it does not know is disproportionately persuasive.

If `excluded_ineligible_count > 0`, show a line above the deck: "4 organisations excluded — Form CSR-1 not filed." Click to expand and list them with the reason. That line converts a hidden filter into a visible compliance feature.

---

# C3 ★ · Keyword ⇄ Semantic toggle — the cheapest win in the entire build

**Build this before anything else in your differentiator block.** Two hours of work, and it single-handedly answers the question every judge asks: *why is this better than search?*

```tsx
<ModeToggle mode={mode} onChange={setMode} />   // "keyword" | "semantic"
```

Flipping it re-runs `POST /api/match` with `use_keyword_baseline: true|false`. The deck re-orders **with an animated transition** so the movement is visible, and a banner appears:

> Semantic matching surfaced **3 organisations** that keyword search missed entirely, and moved **Aarogya Sakhi Foundation** from rank 14 to rank 2.

Compute that banner from the two result sets: NGOs present in semantic and absent from keyword, plus the largest positive rank movement. Name the NGO. A specific name is an argument; "improved results" is a claim.

Highlight newly-surfaced cards with a thin accent left border and a small `new` chip for a few seconds after the transition.

The seeded NGO that uses "postpartum institutional delivery care" instead of "maternal health" exists exactly for this moment. Confirm with Vaishnavi that it is in the corpus and that it is genuinely invisible to the keyword baseline — and confirm with Piyush that the keyword baseline is *fair*. If the baseline is deliberately crippled, a sharp judge will notice, and the entire comparison loses its force.

---

# C4 · Trust dossier drawer

Slides in from the right at roughly 560px. Header: NGO name, badge with label, the trust score in a `Gauge`, and `last verified N months ago`.

Four `PillarBar` rows — Compliance 30%, Financial 30%, Operational 25%, External 15%. Each shows the raw pillar, the freshness multiplier applied, and the resulting contribution. Expanding a pillar lists its evidence items; each item shows the document name, page number, and the extracted snippet, and is clickable straight into `EvidenceViewer`.

Where a pillar has `no_evidence: true`, say so plainly — "No audit report on file — contributes 0 to this pillar" — rather than showing an empty bar. An explicit zero is a feature; a blank bar is a bug in the judge's mind.

Show penalties as separate negative rows: `Anomaly flags −8`, `Shell network −20`. Never fold them silently into the total. A number that visibly decomposes into its parts is the whole reason this drawer exists.

Footer: `algorithm_version` and the first eight characters of `input_hash`, in `text-xs`. It takes ten seconds to add and it tells a technical judge that you thought about reproducibility.

---

# C5 ★ · Evidence viewer — the moment the project stops looking like a demo

This is the highest-value component in your lane. A judge clicks a trust pillar, clicks an evidence item, and **a rendered page of an actual PDF appears with the relevant text highlighted.** Nothing else you build will produce the same reaction.

```tsx
<EvidenceViewer
  docId={string} page={number}
  snippet={string} charOffsets={[number, number]}
  onClose={() => void}
/>
```

Fetch the page image from `GET /api/documents/{doc_id}/pages/{n}.png`. Overlay a translucent amber highlight over the snippet region. Vaishnavi returns character offsets; if she can also return a bounding box, use it — otherwise render the snippet in a callout beside the page image and highlight there. **A callout beside a real page image is completely acceptable and far better than a fragile overlay that misaligns on stage.** Decide which at Hour 20 and stop iterating.

Include: document name, kind, page N of M, page navigation, and a download link. Preload the pages used in the demo path so there is no spinner during the four minutes that matter.

---

# C6 · Shell network graph

When `GET /api/ngos/{id}/network` returns `flagged: true`, the dossier shows a red panel: **"Linked-entity network detected."**

Render the component as a small force-free graph — three or four nodes positioned on a circle, edges drawn as SVG lines, each edge labelled with what is shared: `same address`, `same trustee`, `same bank account`. Do not pull in a graph library for four nodes; hand-drawn SVG is fewer lines, loads instantly and cannot break.

Below the graph, a plain-language sentence: "These three organisations share a registered address, a trustee name, and a bank account. All three are capped at trust 40 and excluded from recommendation pending human review."

Say *flagged for review*, never *fraudulent*. The restraint is itself a signal of seriousness, and it is the correct claim.

---

# C7 ★ · Consortium panel

Renders `consortiums[]`. This visualises Piyush's optimiser and it needs to make a set-cover result legible in about eight seconds.

Header: "No single partner covers this mandate. Best combination:" then the member names.

**Coverage bars** — one row per requirement unit from the mandate (six, in the demo), each filled in segments coloured by which member covers it. A judge should see instantly that member 1 covers units 1–3, member 2 covers 4–6, that all six are filled, and that the best single NGO would have covered only three.

Then: consortium score versus best-single score, side by side, with the delta called out. Redundancy percentage. A **budget-split donut** with exact rupee amounts. A capacity-cap indicator wherever a member's allocation was limited by absorptive capacity — with the tooltip "capped at 1.5× the largest grant this organisation has previously managed", because that constraint is one of the most credible details in the whole project and it deserves to be seen.

Finally the one-line rationale from the API. Do not compose your own explanation in the frontend — display the one the optimiser produced, so what the judge reads is what the algorithm actually decided.

---

# C8 ★ · Counterfactual coach — the beat that changes the story

Lives in the NGO role at `/ngo/[id]`. Everything else in the product serves the corporate; this serves the NGO, and it is what turns "a matching tool" into "infrastructure for both sides of the market". Say that sentence in the pitch.

Header: current trust score in a large `Gauge`, current badge, and the `achievable_ceiling` from the API drawn as a faint outer arc on the same gauge — so the gap between where they are and where they could get is visible without words.

Below it, the ranked actions from `GET /api/ngos/{id}/counterfactual`, each as a row with a toggle:

> ☐ **Upload FY2024 audited financial statement** · **+12 points** · effort: low
> ☐ **Renew 80G certificate (expired Mar 2025)** · **+7 points** · effort: medium

Toggling animates the gauge to the new value and, when a threshold is crossed, **the badge changes** — `Standard Audited` becomes `Verified Elite` in front of the judge. That badge flip is the emotional peak of the demo. Give it a 200 ms transition and a subtle scale pulse, and nothing else on the screen should move while it happens.

**The predicted number must be exactly the API's number.** Do not add deltas yourself, do not interpolate, do not "smooth" anything. When multiple toggles are on, use the API's combined projection if it provides one; if it does not, show the individual deltas and label the sum as an estimate. Vaishnavi and Piyush have a test asserting predicted equals realised — do not break that guarantee in the presentation layer.

Group actions into *actionable now* and *structural* (things that need time, like years of operating history). Structural items render greyed with an explanation rather than a toggle, because offering someone a checkbox for "exist for five more years" is worse than saying nothing.

The demo NGO goes 61 → 80. Confirm that path works end to end and rehearse it.

---

# C9 · Demand-vs-supply map

`/map`, Leaflet, OpenStreetMap tiles, district GeoJSON bundled in `public/geo/districts.json`.

**Bundle the GeoJSON and pre-cache tiles.** A map that needs a CDN is a map that is blank at demo time. If tile pre-caching proves fiddly, fall back to a plain light background with district polygons only — polygons on white are perfectly readable and they cannot fail.

Two layers, toggleable:

**Supply** — NGO markers, clustered, coloured by trust badge, filterable by domain, trust floor and radius.

**Demand** — district choropleth on `gap_score` from `GET /api/geo/coverage`, with Aspirational Districts outlined in a distinct stroke. The story is the districts that are dark on demand and empty on supply. Label two or three of them directly on the map — a labelled CSR desert makes the argument; an unlabelled colour gradient asks the judge to make it for you.

Hovering a district shows NGO count, total capacity, need index, and whether it is aspirational. Clicking filters the partner deck to that district.

A legend that reads in one glance, a radius slider, and a small note: "Need index is seeded for the prototype; the Aspirational Districts flag follows the NITI Aayog list." Label seeded data as seeded. Every time. A judge who discovers an unlabelled invented statistic stops believing the real ones.

---

# C10–C13 · The P2 block, in this order

**C11 first — "₹ at risk".** Forty-five minutes, highest impact per minute in the whole build. A summary strip above the deck: *"₹2.4 crore of this mandate would be routed to organisations that are ineligible or high-risk under a keyword-based process."* Compute it from the mandate budget and the flagged/ineligible NGOs that a keyword ranking would have placed in the top five. This is the pitch's closing line and it is the number a CSR head actually cares about. Get the arithmetic right and be able to explain it in one sentence.

**C13 next — latency badge.** Fifteen minutes. A header chip showing the real `latency_ms` from the last match response, plus `X-Cache` state. "1,000 NGOs ranked in 340 milliseconds" is a claim you can point at rather than assert. It must be the measured number — a hardcoded one that never changes when a judge reloads is worse than no badge at all.

**C10 — comparison matrix.** Up to three NGOs side by side: all four trust pillars, semantic fit, geo fit, cost per beneficiary, admin ratio, flags. Best value per row gets a subtle emerald tint. Real CSR teams build exactly this spreadsheet by hand over two weeks, so say that when you show it.

**C12 — weight sliders + rank stability.** Three sliders for the 0.50 / 0.30 / 0.20 weights, normalised to sum to 1, re-running the match on release (not on drag). Beside them, the `rank_stability` figures from the API: "Ranks 1–3 hold in 94% of 500 perturbed weightings." This pre-empts the hardest question a judge can ask — *aren't those weights arbitrary?* — and answers it with a measurement instead of a defence. If you build only one of the two, build the stability readout.

**Pareto frontier**, if time allows: a Recharts scatter of trust versus semantic fit with the non-dominated set connected and dominated options greyed. Thirty minutes given the API already returns `pareto_front`.

---

# Accessibility and robustness — NFR-8, and it is checked

Every badge carries text. Every interactive element is keyboard reachable with a visible focus ring. Contrast at least 4.5:1 for body text. `aria-label` on icon-only buttons. The gauge and every chart have a text equivalent nearby — a screen reader must not hit a bare `<svg>`. `prefers-reduced-motion` respected.

Test the full demo path with the keyboard only, at 1920, 1440 and 1024. A judge may ask to drive; a projector may be 1024.

---

# Your second job: the deck

At Hour 32 you create `07-DECK-OUTLINE.md` (it does not exist yet — you write it) and own it as a working document; the rest of us contribute content. Ten slides, no more. Screenshots from the real product, not mockups — a mockup in a deck next to a working demo makes the judge wonder which parts are real.

Slide order that works: the problem in one number; why current practice fails; SETU in one sentence with one screenshot; the semantic-versus-keyword comparison as a before/after image; trust with evidence, showing the rendered document page; shell-network detection; the consortium coverage bars; the counterfactual coach with the 61→80 gauge; architecture on one slide; what is real today versus what is next, stated honestly.

That last slide wins more points than people expect. A team that clearly separates "working" from "designed" is a team a judge trusts on everything else.

---

# Definition of done

The whole ten-beat demo path is clickable without touching a terminal. Every async region has a skeleton and an empty state; nothing shows a spinner longer than 8 seconds or a stack trace ever. The four never-cut features work: mode toggle with a named delta, evidence drill-down to a rendered page, consortium coverage bars, counterfactual gauge and badge flip. The app walks the entire demo path with the backend killed, from fixtures. Keyboard-only pass complete. Responsive at 1920/1440/1024. Every badge has a text label. Every seeded number is labelled as seeded. Latency badge shows a real, changing number.

# Three answers to have loaded

**"Did you build this UI or is it a template?"** — Built. The design system is four colours and three type sizes chosen for projector legibility, and every score on screen decomposes into its inputs, which is not something a template gives you.

**"What happens if your backend goes down right now?"** — It keeps working. Every API call falls back to captured real responses automatically, and I can show you — we tested it with the network adapter disabled at Hour 42.

**"Why the chat instead of a form?"** — Because a CSR head describes a mandate in a sentence, not in eleven fields. The split screen shows the sentence becoming structured requirements with per-field confidence, and any field the parser is unsure about is editable in one click.

---

*`05-TASK-C-FRONTEND-GIS.md` · paste alongside `00-PROJECT-CONTEXT.md` §0–10*




