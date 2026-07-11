import csv
import json

with open("scored_accounts.csv") as f:
    accounts = list(csv.DictReader(f))

with open("outreach_drafts.json") as f:
    drafts = json.load(f)
draft_by_company = {d["company"]: d for d in drafts}

tier_order = {"1:1": 0, "1:few": 1, "1:many": 2}
accounts.sort(key=lambda a: (tier_order[a["tier"]], -float(a["total_score"])))

tier_colors = {"1:1": "#c0392b", "1:few": "#b8860b", "1:many": "#5a6b7a"}
tier_bg = {"1:1": "#fdecea", "1:few": "#fdf3d9", "1:many": "#eef1f3"}

rows_html = []
for a in accounts:
    tier = a["tier"]
    has_draft = a["company"] in draft_by_company
    draft = draft_by_company.get(a["company"])
    draft_html = ""
    if draft:
        body_html = draft["body"].replace("\n", "<br>")
        draft_html = f"""
        <div class="draft">
          <div class="draft-subject">Subject: {draft['subject']}</div>
          <div class="draft-body">{body_html}</div>
        </div>"""
    rows_html.append(f"""
    <tr class="acct-row" onclick="this.nextElementSibling.classList.toggle('open')">
      <td><span class="tier-pill" style="background:{tier_bg[tier]};color:{tier_colors[tier]}">{tier}</span></td>
      <td class="company">{a['company']}</td>
      <td>{a['industry']}</td>
      <td class="score">{a['total_score']}</td>
      <td>{a['engagement_score']}</td>
      <td>{a['fit_score']}</td>
      <td>{a['recency_score']}</td>
      <td>{a['tech_score']}</td>
      <td>{a['champion_title']}</td>
      <td>{'✓' if has_draft else '—'}</td>
    </tr>
    <tr class="detail-row"><td colspan="10">
      <div class="reasons"><strong>Why this score:</strong> {a['reasons']}</div>
      {draft_html}
    </td></tr>
    """)

tier_counts = {}
for a in accounts:
    tier_counts[a["tier"]] = tier_counts.get(a["tier"], 0) + 1

html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Account Prioritization Engine</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    background: #f7f8fa;
    margin: 0;
    padding: 40px 24px;
    color: #1c2b36;
  }}
  .wrap {{ max-width: 980px; margin: 0 auto; }}
  h1 {{ font-size: 26px; margin-bottom: 4px; }}
  .subtitle {{ color: #5a6b7a; margin-top: 0; margin-bottom: 28px; font-size: 15px; }}
  .stats {{ display: flex; gap: 14px; margin-bottom: 28px; flex-wrap: wrap; }}
  .stat-card {{
    background: white; border-radius: 10px; padding: 16px 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08); flex: 1; min-width: 140px;
  }}
  .stat-num {{ font-size: 26px; font-weight: 700; }}
  .stat-label {{ font-size: 12px; color: #5a6b7a; text-transform: uppercase; letter-spacing: 0.04em; }}
  table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
  th {{ text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: #5a6b7a; padding: 12px 14px; border-bottom: 2px solid #e8eaed; }}
  td {{ padding: 12px 14px; font-size: 14px; border-bottom: 1px solid #eef0f2; }}
  .acct-row {{ cursor: pointer; }}
  .acct-row:hover {{ background: #f9fafb; }}
  .company {{ font-weight: 600; }}
  .score {{ font-weight: 700; }}
  .tier-pill {{ padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }}
  .detail-row {{ display: none; }}
  .detail-row.open {{ display: table-row; }}
  .detail-row td {{ background: #fafbfc; border-bottom: 1px solid #e8eaed; }}
  .reasons {{ font-size: 13px; color: #3d4b56; margin-bottom: 10px; }}
  .draft {{ background: white; border: 1px solid #e2e5e8; border-radius: 8px; padding: 14px 16px; margin-top: 6px; }}
  .draft-subject {{ font-weight: 600; font-size: 13px; margin-bottom: 8px; color: #1c2b36; }}
  .draft-body {{ font-size: 13px; color: #3d4b56; line-height: 1.6; }}
  .hint {{ font-size: 12px; color: #8a97a1; margin-top: 24px; text-align: center; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Account Prioritization + AI Outreach Engine</h1>
  <p class="subtitle">Scores accounts on engagement, ICP fit, recency, and tech-stack signal — auto-tiers them 1:1 / 1:few / 1:many, and drafts outreach for the top tier. Click a row for the reasoning and draft.</p>
  <div class="stats">
    <div class="stat-card"><div class="stat-num" style="color:#c0392b">{tier_counts.get('1:1', 0)}</div><div class="stat-label">1:1 accounts</div></div>
    <div class="stat-card"><div class="stat-num" style="color:#b8860b">{tier_counts.get('1:few', 0)}</div><div class="stat-label">1:few accounts</div></div>
    <div class="stat-card"><div class="stat-num" style="color:#5a6b7a">{tier_counts.get('1:many', 0)}</div><div class="stat-label">1:many accounts</div></div>
    <div class="stat-card"><div class="stat-num">{len(drafts)}</div><div class="stat-label">Drafts generated</div></div>
  </div>
  <table>
    <thead>
      <tr>
        <th>Tier</th><th>Company</th><th>Industry</th><th>Total</th><th>Engage</th><th>Fit</th><th>Recency</th><th>Tech</th><th>Champion</th><th>Draft</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows_html)}
    </tbody>
  </table>
  <p class="hint">Synthetic demo data — swap accounts.csv for a real CRM export to run this on live pipeline.</p>
</div>
</body>
</html>
"""

with open("dashboard.html", "w") as f:
    f.write(html)

print("wrote dashboard.html")
