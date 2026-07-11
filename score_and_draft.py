"""
Account Prioritization + AI Outreach Engine
--------------------------------------------
Mirrors real ABM tiering (1:1 / 1:few / 1:many) with an automated scoring
pipeline, then flags which accounts get a hand-drafted 1:1 outreach note.

Swap `accounts.csv` for a real HubSpot/Salesforce export (same column names,
or edit COLUMN_MAP below) to run this against live pipeline data.

Usage:
    python score_and_draft.py
Outputs:
    scored_accounts.csv   -- every account, scored and tiered
    outreach_drafts.json  -- drafted outreach copy for top-tier accounts
"""

import csv
import json
from dataclasses import dataclass, asdict

INPUT_CSV = "accounts.csv"
SCORED_CSV_OUT = "scored_accounts.csv"
DRAFTS_JSON_OUT = "outreach_drafts.json"

# ---- Scoring weights (tune these against your own win-rate data) ----
WEIGHTS = {
    "engagement": 0.35,   # website visits + email opens + demo requested
    "fit": 0.35,          # employee count / funding stage vs ICP
    "recency": 0.15,      # how fresh the last touch is
    "tech_signal": 0.15,  # existing stack overlap (warm technical fit)
}

ICP_TECH_KEYWORDS = ["Snowflake", "Databricks", "dbt"]
ICP_FUNDING_SWEET_SPOT = {"Series B", "Series C", "Series D"}


@dataclass
class ScoredAccount:
    company: str
    industry: str
    tier: str
    total_score: float
    engagement_score: float
    fit_score: float
    recency_score: float
    tech_score: float
    champion_title: str
    reasons: str


def normalize(value, lo, hi):
    if hi == lo:
        return 0.0
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))


def score_engagement(row):
    visits = float(row["website_visits_30d"])
    opens = float(row["email_opens_30d"])
    demo = row["demo_requested"].strip().upper() == "TRUE"
    score = normalize(visits, 0, 60) * 0.4 + normalize(opens, 0, 10) * 0.4
    score += 0.2 if demo else 0.0
    return round(score * 100, 1)


def score_fit(row):
    employees = int(row["employee_count"])
    funding = row["funding_stage"].strip()
    arr = float(row["arr_potential_usd"])
    size_score = normalize(employees, 50, 3000)
    funding_score = 1.0 if funding in ICP_FUNDING_SWEET_SPOT else 0.4
    arr_score = normalize(arr, 20000, 250000)
    return round((size_score * 0.3 + funding_score * 0.4 + arr_score * 0.3) * 100, 1)


def score_recency(row):
    days_ago = int(row["last_touch_days_ago"])
    return round((1 - normalize(days_ago, 0, 60)) * 100, 1)


def score_tech(row):
    stack = row["tech_stack_signal"]
    hits = sum(1 for kw in ICP_TECH_KEYWORDS if kw.lower() in stack.lower())
    return round(normalize(hits, 0, 2) * 100, 1)


def tier_for_score(total, demo_requested):
    if total >= 70 or demo_requested:
        return "1:1"
    elif total >= 45:
        return "1:few"
    else:
        return "1:many"


def build_reasons(row, eng, fit, rec, tech):
    reasons = []
    if row["demo_requested"].strip().upper() == "TRUE":
        reasons.append("requested a demo")
    if eng >= 60:
        reasons.append("high recent engagement (visits + opens)")
    if fit >= 60:
        reasons.append("strong ICP fit (size/funding/ARR potential)")
    if tech >= 50:
        reasons.append(f"existing stack overlap ({row['tech_stack_signal']})")
    if rec >= 80:
        reasons.append("touched within the last few days")
    return "; ".join(reasons) if reasons else "baseline nurture signals only"


def draft_outreach(row, reasons):
    """
    Illustrative draft-writer. In production this calls an LLM (Claude/GPT)
    with account context + reasons as the prompt. Stubbed here with a
    template so the pipeline runs end-to-end with zero API keys required.
    """
    company = row["company"]
    champion = row["champion_title"]
    stack = row["tech_stack_signal"]
    top_reason = reasons.split(";")[0].strip() if reasons else "showing renewed activity"
    subject = f"Quick idea for {company}'s data team"
    body = (
        f"Hi {{first_name}},\n\n"
        f"Noticed {company} {top_reason} — "
        f"given your team's work with {stack}, thought it was worth a quick note to the {champion}.\n\n"
        f"Happy to share how teams with a similar setup have approached this. "
        f"Worth 15 minutes this week?\n\n"
        f"Best,\n{{sender_name}}"
    )
    return {"company": company, "subject": subject, "body": body, "reasons": reasons}


def main():
    with open(INPUT_CSV, newline="") as f:
        rows = list(csv.DictReader(f))

    scored = []
    drafts = []

    for row in rows:
        eng = score_engagement(row)
        fit = score_fit(row)
        rec = score_recency(row)
        tech = score_tech(row)
        total = round(
            eng * WEIGHTS["engagement"]
            + fit * WEIGHTS["fit"]
            + rec * WEIGHTS["recency"]
            + tech * WEIGHTS["tech_signal"],
            1,
        )
        demo = row["demo_requested"].strip().upper() == "TRUE"
        tier = tier_for_score(total, demo)
        reasons = build_reasons(row, eng, fit, rec, tech)

        scored.append(
            ScoredAccount(
                company=row["company"],
                industry=row["industry"],
                tier=tier,
                total_score=total,
                engagement_score=eng,
                fit_score=fit,
                recency_score=rec,
                tech_score=tech,
                champion_title=row["champion_title"],
                reasons=reasons,
            )
        )

        if tier == "1:1":
            drafts.append(draft_outreach(row, reasons))

    scored.sort(key=lambda a: a.total_score, reverse=True)

    with open(SCORED_CSV_OUT, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(scored[0]).keys()))
        writer.writeheader()
        for acct in scored:
            writer.writerow(asdict(acct))

    with open(DRAFTS_JSON_OUT, "w") as f:
        json.dump(drafts, f, indent=2)

    tier_counts = {}
    for acct in scored:
        tier_counts[acct.tier] = tier_counts.get(acct.tier, 0) + 1

    print(f"Scored {len(scored)} accounts -> {SCORED_CSV_OUT}")
    print(f"Tier breakdown: {tier_counts}")
    print(f"Drafted outreach for {len(drafts)} 1:1 accounts -> {DRAFTS_JSON_OUT}")


if __name__ == "__main__":
    main()
