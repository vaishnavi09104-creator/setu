// Build script: generates fixture evidence page SVGs + district GeoJSON into public/.
// Run: node scripts/gen-fixtures.mjs  (idempotent)

import { writeFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";

const out = (p) => join(process.cwd(), "public", p);
mkdirSync(out("evidence"), { recursive: true });
mkdirSync(out("geo"), { recursive: true });

function esc(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// wrap snippet text into lines for the callout
function wrap(text, width = 92) {
  const words = text.split(" ");
  const lines = [];
  let cur = "";
  for (const w of words) {
    if ((cur + " " + w).trim().length > width) {
      lines.push(cur.trim());
      cur = w;
    } else cur += " " + w;
  }
  if (cur.trim()) lines.push(cur.trim());
  return lines;
}

const docs = [
  { id: "doc_csr1_014", title: "Form CSR-1 Registration", org: "Ashadeep Gramin Vikas Samiti", pages: [
    { n: 1, body: "MINISTRY OF CORPORATE AFFAIRS — FORM CSR-1\n\nEntity: Ashadeep Gramin Vikas Samiti\nRegistration No.: CSR-00024187\nDate of registration: 14-03-2022\nValid from 14-03-2022, no expiry recorded\n\nCertified that the above entity is registered to receive\nCorporate Social Responsibility funds under Section 135\nof the Companies Act, 2013 read with the CSR Policy Rules.",
      highlight: "CSR-00024187" },
    { n: 2, body: "FORM CSR-1 (continued)\n\nAuthorised signatory: S. Meher (Secretary)\nDarpan ID: OD/2016/0149832\nPAN: AACTA4491K", highlight: "" },
  ]},
  { id: "doc_80g_014", title: "80G Renewal Certificate", org: "Ashadeep Gramin Vikas Samiti", pages: [
    { n: 1, body: "INCOME TAX DEPARTMENT — 80G CERTIFICATE\n\nCertificate No.: AA/8G/2024/1147\nGranted under section 80G(5)(vi) of the\nIncome Tax Act, 1961 to:\nAshadeep Gramin Vikas Samiti, Bhawanipatna, Kalahandi (Odisha)\n\nValid up to 31-03-2027",
      highlight: "AA/8G/2024/1147" },
  ]},
  { id: "doc_audit_014", title: "Audited Financial Statement FY2024-25", org: "Ashadeep Gramin Vikas Samiti", pages: [
    { n: 1, body: "AUDITED FINANCIAL STATEMENT FY 2024-25\nAshadeep Gramin Vikas Samiti\nStatutory auditors: R. Das & Associates, Chartered Accountants", highlight: "" },
    { n: 2, body: "BALANCE SHEET SUMMARY (INR)\n\nFixed assets            1,12,40,000\nCurrent assets           68,55,000\nLiabilities              21,30,000\n Corpus fund           1,59,65,000", highlight: "1,59,65,000" },
    { n: 3, body: "INCOME & EXPENDITURE SUMMARY (INR)\n\nGrants & donations     3,02,00,000\nProgramme expense      2,49,92,000\nAdministrative overhead  34,08,000  (12.0% of total)\nTotal expenditure      2,84,00,000\nSurplus                 18,00,000", highlight: "34,08,000" },
    { n: 4, body: "SCHEDULE III — ADMINISTRATIVE OVERHEAD DETAIL (INR)\n\nStaff salaries (admin)      22,80,000\nOffice & utilities           6,40,000\nAudit & professional        3,20,000\nTravel (admin)              1,68,000\n                            ---------\nAdministrative overhead    34,08,000   12.0% of total expenditure\nProgramme expense        2,49,92,000   88.0%\nCost per beneficiary (programme/beneficiaries) = Rs 1,180", highlight: "12.0% of total expenditure" },
    { n: 5, body: "AUDITOR'S OPINION\n\nIn our opinion, the accompanying financial statements give a true and fair view and comply with the Income Tax Act provisions applicable to charitable trusts.", highlight: "true and fair view" },
  ]},
  { id: "doc_ar_014", title: "Annual Report 2024-25", org: "Ashadeep Gramin Vikas Samiti", pages: [
    { n: 12, body: "PROGRAMME COMPLETION RECORD\n\nProjects completed since 2016:        42\nProjects sanctioned since 2016:       47\nMilestones reported:                240\nMilestones met:                      218  (91%)\nBeneficiaries reached (cumulative): 48,900", highlight: "42" },
  ]},
  { id: "doc_impact_014", title: "Third-Party Impact Assessment", org: "Assessment by Sigma Development Analytics", pages: [
    { n: 2, body: "IMPACT ASSESSMENT — MATERNAL HEALTH PROGRAMME\n\nIndependent assessment commissioned by the corporate CSR partner.\nSafe-delivery referrals achieved: 11,240 (target 10,000)\nASHA workers trained: 312\nInstitutional delivery rate in covered blocks rose from 61% to 78%.",
      highlight: "11,240" },
  ]},
  { id: "doc_csr1_040", title: "Form CSR-1 Registration (stale)", org: "Maa Bhoomi Trust", pages: [
    { n: 1, body: "MINISTRY OF CORPORATE AFFAIRS — FORM CSR-1\n\nEntity: Maa Bhoomi Trust\nRegistration No.: CSR-00031542\nDate of registration: 09-11-2021\n\nRegistered address: Plot 14, Industrial Area Road, Balangir", highlight: "CSR-00031542" },
  ]},
  { id: "doc_ar_040", title: "Annual Report 2022-23 (latest on file)", org: "Maa Bhoomi Trust", pages: [
    { n: 3, body: "PROJECT RECORD\n\nProjects completed: 9 of 15 sanctioned.\nMilestone reporting irregular after FY22.", highlight: "9" },
  ]},
];

function pageSvg(doc, page) {
  const lines = page.body.split("\n");
  let y = 90;
  const rendered = [];
  for (const line of lines) {
    rendered.push(`<text x="70" y="${y}" font-size="15" fill="#0F172A">${esc(line)}</text>`);
    y += 26;
  }
  // highlight box: find the highlight text in the first matching line, approximate
  let hlRect = "";
  if (page.highlight) {
    const idx = lines.findIndex((l) => l.includes(page.highlight));
    if (idx >= 0) {
      const hlY = 90 + idx * 26;
      hlRect = `<rect x="60" y="${hlY - 16}" width="${Math.min(660, 14 + page.highlight.length * 9)}" height="22" fill="#FDE68A" fill-opacity="0.55" stroke="#D97706" stroke-dasharray="4 2" rx="3"/>`;
    }
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" width="794" height="1123" viewBox="0 0 794 1123">
  <rect width="794" height="1123" fill="#FFFFFF"/>
  <rect x="30" y="30" width="734" height="1063" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="2"/>
  <text x="70" y="72" font-size="17" font-weight="bold" fill="#0F172A">${esc(doc.title)}</text>
  <text x="70" y="94" font-size="12" fill="#475569">${esc(doc.org)} · page ${page.n} · fixture capture</text>
  <line x1="70" y1="104" x2="724" y2="104" stroke="#E2E8F0" stroke-width="1"/>
  ${hlRect}
  ${rendered.join("\n  ")}
  <text x="70" y="1070" font-size="11" fill="#94A3B8">SETU evidence fixture — offline capture of GET /api/documents/${esc(doc.id)}/pages/${page.n}.png</text>
</svg>`;
}

for (const doc of docs) {
  for (const page of doc.pages) {
    writeFileSync(out(`evidence/${doc.id}_${page.n}.svg`), pageSvg(doc, page));
  }
}

// ---- districts geojson (boxes around real district centroids, fine for prototype) ----
const districts = [
  { name: "Kalahandi", state: "Odisha", box: [82.9, 19.7, 83.6, 20.3] },
  { name: "Nuapada", state: "Odisha", box: [82.4, 19.9, 83.1, 20.6] },
  { name: "Balangir", state: "Odisha", box: [82.8, 20.4, 83.7, 21.1] },
  { name: "Cuttack", state: "Odisha", box: [85.0, 20.2, 85.8, 20.9] },
  { name: "Mayurbhanj", state: "Odisha", box: [86.6, 20.2, 87.4, 21.0] },
  { name: "Palghar", state: "Maharashtra", box: [72.7, 19.4, 73.5, 20.3] },
  { name: "Nashik", state: "Maharashtra", box: [73.3, 19.8, 74.3, 20.8] },
  { name: "Khandwa", state: "Madhya Pradesh", box: [75.4, 21.3, 76.6, 22.4] },
  { name: "Barwani", state: "Madhya Pradesh", box: [74.2, 21.4, 75.3, 22.3] },
  { name: "Narsinghpur", state: "Madhya Pradesh", box: [77.8, 21.9, 79.0, 23.0] },
];
function polygon(box) {
  const [x1, y1, x2, y2] = box;
  return [[[x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1]]];
}
const geojson = {
  type: "FeatureCollection",
  features: districts.map((d) => ({
    type: "Feature",
    properties: { district: d.name, state: d.state },
    geometry: { type: "Polygon", coordinates: polygon(d.box) },
  })),
};
writeFileSync(out("geo/districts.json"), JSON.stringify(geojson, null, 1));

console.log(`generated ${docs.reduce((n, d) => n + d.pages.length, 0)} evidence pages + districts.json`);
