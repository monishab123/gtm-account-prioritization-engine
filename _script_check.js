
const ACCOUNTS = [
  {company:"Brightline Logistics", industry:"Supply Chain", employees:850, funding:"Series C", arr:120000, visits:42, opens:6, demo:true, champion:"VP Operations", stack:"Snowflake", lastTouch:3},
  {company:"Cadence Health", industry:"Healthtech", employees:220, funding:"Series B", arr:65000, visits:18, opens:3, demo:false, champion:"Director of Data", stack:"Databricks", lastTouch:14},
  {company:"Ferro Materials", industry:"Manufacturing", employees:3200, funding:"Public", arr:300000, visits:9, opens:1, demo:false, champion:"IT Manager", stack:"Legacy ERP", lastTouch:45},
  {company:"Vantage Retail Co", industry:"Retail", employees:1400, funding:"Series D", arr:180000, visits:55, opens:9, demo:true, champion:"Head of Growth", stack:"Salesforce+Snowflake", lastTouch:1},
  {company:"Northwind Analytics", industry:"Data/Analytics", employees:90, funding:"Series A", arr:28000, visits:31, opens:5, demo:false, champion:"Founder/CEO", stack:"Postgres", lastTouch:7},
  {company:"Solace Robotics", industry:"Robotics", employees:410, funding:"Series B", arr:95000, visits:12, opens:2, demo:false, champion:"Eng Manager", stack:"AWS", lastTouch:30},
  {company:"Circuit Peak Semiconductors", industry:"Hardware", employees:5000, funding:"Public", arr:250000, visits:6, opens:1, demo:false, champion:"Procurement Lead", stack:"SAP", lastTouch:60},
  {company:"Lumen Insurance Group", industry:"Insurance", employees:2100, funding:"Series E", arr:210000, visits:38, opens:7, demo:true, champion:"VP Data Platform", stack:"Snowflake+Databricks", lastTouch:2},
  {company:"Marrow Biotech", industry:"Biotech", employees:150, funding:"Series A", arr:32000, visits:22, opens:4, demo:false, champion:"Head of R&D Ops", stack:"AWS", lastTouch:10},
  {company:"Tidewater Financial", industry:"FinServ", employees:980, funding:"Series C", arr:140000, visits:47, opens:8, demo:true, champion:"Chief Data Officer", stack:"Snowflake", lastTouch:4},
  {company:"Pinehill Media", industry:"Media/AdTech", employees:300, funding:"Series B", arr:58000, visits:15, opens:2, demo:false, champion:"VP Marketing", stack:"GCP", lastTouch:20},
  {company:"Ashgrove Energy", industry:"Energy", employees:1700, funding:"Series D", arr:160000, visits:29, opens:5, demo:false, champion:"Director of IT", stack:"Snowflake", lastTouch:12},
  {company:"Copperline Freight", industry:"Logistics", employees:600, funding:"Series B", arr:72000, visits:10, opens:1, demo:false, champion:"Ops Analyst", stack:"Legacy", lastTouch:50},
  {company:"Nimbus Cloud Systems", industry:"SaaS/Infra", employees:270, funding:"Series A", arr:40000, visits:36, opens:6, demo:false, champion:"Head of Platform", stack:"Snowflake+dbt", lastTouch:6},
  {company:"Alderway Retailers", industry:"Retail", employees:4200, funding:"Public", arr:220000, visits:8, opens:1, demo:false, champion:"Category Manager", stack:"Oracle", lastTouch:55},
];

const ICP_TECH = ["snowflake", "databricks", "dbt"];
const ICP_FUNDING = new Set(["Series B", "Series C", "Series D"]);

function norm(v, lo, hi) { if (hi === lo) return 0; return Math.max(0, Math.min(1, (v - lo) / (hi - lo))); }

function scoreEngagement(a) {
  let s = norm(a.visits, 0, 60) * 0.4 + norm(a.opens, 0, 10) * 0.4;
  s += a.demo ? 0.2 : 0;
  return Math.round(s * 1000) / 10;
}
function scoreFit(a) {
  const size = norm(a.employees, 50, 3000);
  const funding = ICP_FUNDING.has(a.funding) ? 1 : 0.4;
  const arr = norm(a.arr, 20000, 250000);
  return Math.round((size * 0.3 + funding * 0.4 + arr * 0.3) * 1000) / 10;
}
function scoreRecency(a) { return Math.round((1 - norm(a.lastTouch, 0, 60)) * 1000) / 10; }
function scoreTech(a) {
  const stack = a.stack.toLowerCase();
  const hits = ICP_TECH.filter(k => stack.includes(k)).length;
  return Math.round(norm(hits, 0, 2) * 1000) / 10;
}
function tierFor(total, demo) {
  if (total >= 70 || demo) return "1:1";
  if (total >= 45) return "1:few";
  return "1:many";
}
function buildReasons(a, eng, fit, rec, tech) {
  const r = [];
  if (a.demo) r.push("requested a demo");
  if (eng >= 60) r.push("high recent engagement (visits + opens)");
  if (fit >= 60) r.push("strong ICP fit (size/funding/ARR potential)");
  if (tech >= 50) r.push(`existing stack overlap (${a.stack})`);
  if (rec >= 80) r.push("touched within the last few days");
  return r.length ? r.join("; ") : "baseline nurture signals only";
}
function draftFor(a, reasonsStr) {
  const top = reasonsStr.split(";")[0].trim() || "showing renewed activity";
  const subject = `Quick idea for ${a.company}'s data team`;
  const body = `Hi {first_name},\n\nNoticed ${a.company} ${top} — given your team's work with ${a.stack}, thought it was worth a quick note to the ${a.champion}.\n\nHappy to share how teams with a similar setup have approached this. Worth 15 minutes this week?\n\nBest,\n{sender_name}`;
  return { subject, body };
}

const pillStyle = { "1:1": ["#fdecea", "#c0392b"], "1:few": ["#fdf3d9", "#b8860b"], "1:many": ["#eef1f3", "#5a6b7a"] };

let sortKey = "total", sortDir = -1;

const els = {
  wEng: document.getElementById("wEng"), wFit: document.getElementById("wFit"),
  wRec: document.getElementById("wRec"), wTech: document.getElementById("wTech"),
  search: document.getElementById("search"), tierFilter: document.getElementById("tierFilter"),
  tbody: document.getElementById("tbody"), stats: document.getElementById("stats"),
};

function currentWeights() {
  const raw = { eng: +els.wEng.value, fit: +els.wFit.value, rec: +els.wRec.value, tech: +els.wTech.value };
  const sum = raw.eng + raw.fit + raw.rec + raw.tech || 1;
  return { eng: raw.eng / sum, fit: raw.fit / sum, rec: raw.rec / sum, tech: raw.tech / sum };
}

function computeRows() {
  const w = currentWeights();
  return ACCOUNTS.map(a => {
    const eng = scoreEngagement(a), fit = scoreFit(a), rec = scoreRecency(a), tech = scoreTech(a);
    const total = Math.round((eng * w.eng + fit * w.fit + rec * w.rec + tech * w.tech) * 10) / 10;
    const tier = tierFor(total, a.demo);
    const reasons = buildReasons(a, eng, fit, rec, tech);
    return { ...a, eng, fit, rec, tech, total, tier, reasons };
  });
}

function render() {
  document.getElementById("wEngVal").textContent = els.wEng.value + "%";
  document.getElementById("wFitVal").textContent = els.wFit.value + "%";
  document.getElementById("wRecVal").textContent = els.wRec.value + "%";
  document.getElementById("wTechVal").textContent = els.wTech.value + "%";

  let rows = computeRows();

  const q = els.search.value.trim().toLowerCase();
  if (q) rows = rows.filter(r => r.company.toLowerCase().includes(q) || r.industry.toLowerCase().includes(q) || r.champion.toLowerCase().includes(q));
  const tf = els.tierFilter.value;
  if (tf !== "all") rows = rows.filter(r => r.tier === tf);

  rows.sort((a, b) => {
    const av = a[sortKey], bv = b[sortKey];
    if (typeof av === "string") return sortDir * av.localeCompare(bv);
    return sortDir * (av - bv);
  });

  const tierCounts = { "1:1": 0, "1:few": 0, "1:many": 0 };
  computeRows().forEach(r => tierCounts[r.tier]++);
  const draftCount = computeRows().filter(r => r.tier === "1:1").length;
  els.stats.innerHTML = `
    <div class="stat"><div class="num" style="color:#c0392b">${tierCounts["1:1"]}</div><div class="lbl">1:1 accounts</div></div>
    <div class="stat"><div class="num" style="color:#b8860b">${tierCounts["1:few"]}</div><div class="lbl">1:few accounts</div></div>
    <div class="stat"><div class="num" style="color:#5a6b7a">${tierCounts["1:many"]}</div><div class="lbl">1:many accounts</div></div>
    <div class="stat"><div class="num">${draftCount}</div><div class="lbl">Drafts ready</div></div>
  `;

  els.tbody.innerHTML = rows.map((r, i) => {
    const [bg, fg] = pillStyle[r.tier];
    const hasDraft = r.tier === "1:1";
    const draft = hasDraft ? draftFor(r, r.reasons) : null;
    return `
    <tr class="acct-row" data-idx="${i}">
      <td><span class="pill" style="background:${bg};color:${fg}">${r.tier}</span></td>
      <td class="company">${r.company}</td>
      <td>${r.industry}</td>
      <td class="score">${r.total}</td>
      <td>${r.eng}</td>
      <td>${r.fit}</td>
      <td>${r.rec}</td>
      <td>${r.tech}</td>
      <td>${r.champion}</td>
    </tr>
    <tr class="detail" data-idx="${i}"><td colspan="9">
      <div class="reasons"><strong>Why this score:</strong> ${r.reasons}</div>
      ${hasDraft ? `
        <div class="draft-box">
          <div class="draft-subject">Subject: ${draft.subject}</div>
          <textarea class="draft-body">${draft.body}</textarea>
          <div class="draft-actions">
            <button class="btn btn-ghost copy-btn">Copy draft</button>
            <span class="copied" style="display:none">Copied ✓</span>
          </div>
        </div>` : `<div class="no-draft">Not in the 1:1 tier at current weights — no draft generated. Raise its score or add manually.</div>`}
    </td></tr>`;
  }).join("");

  els.tbody.querySelectorAll(".acct-row").forEach(row => {
    row.addEventListener("click", () => {
      const idx = row.getAttribute("data-idx");
      els.tbody.querySelector(`.detail[data-idx="${idx}"]`).classList.toggle("open");
    });
  });
  els.tbody.querySelectorAll(".copy-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const box = btn.closest(".draft-box");
      const text = box.querySelector("textarea").value;
      navigator.clipboard.writeText(text).then(() => {
        const c = box.querySelector(".copied");
        c.style.display = "inline";
        setTimeout(() => c.style.display = "none", 1500);
      });
    });
  });
}

document.querySelectorAll("th[data-key]").forEach(th => {
  th.addEventListener("click", () => {
    const key = th.getAttribute("data-key");
    if (sortKey === key) sortDir *= -1; else { sortKey = key; sortDir = -1; }
    render();
  });
});

[els.wEng, els.wFit, els.wRec, els.wTech, els.search, els.tierFilter].forEach(el => {
  el.addEventListener("input", render);
});

document.getElementById("resetWeights").addEventListener("click", () => {
  els.wEng.value = 35; els.wFit.value = 35; els.wRec.value = 15; els.wTech.value = 15;
  render();
});

document.getElementById("exportBtn").addEventListener("click", () => {
  const rows = computeRows();
  const header = "company,industry,tier,total,engagement,fit,recency,tech,champion,reasons";
  const csv = [header, ...rows.map(r => [r.company, r.industry, r.tier, r.total, r.eng, r.fit, r.rec, r.tech, r.champion, `"${r.reasons}"`].join(","))].join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url; link.download = "scored_accounts_export.csv";
  link.click();
  URL.revokeObjectURL(url);
});

render();
