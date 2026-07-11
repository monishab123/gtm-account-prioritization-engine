# Account Prioritization + AI Outreach Engine

**▶ Live demo: https://monishab123.github.io/gtm-account-prioritization-engine/**

Sorting a target account list into "call this one personally," "small-batch
campaign," and "just nurture it" is something I did by hand, in a
spreadsheet, running ABM campaigns at Snowflake. It's slow, it doesn't scale
past a couple hundred accounts, and the criteria live in someone's head
instead of anywhere reusable. This is that sorting logic turned into an
actual system: score every account on engagement, ICP fit, recency, and
tech-stack overlap, tier it automatically, and draft the outreach for
whoever lands in the top tier.

Open the live demo above (or `index.html` locally) to use it. The weight sliders aren't
decoration — pull "fit" up and "engagement" down and the tiers actually
reshuffle, because the whole pipeline recomputes on every change instead of
just re-sorting a fixed list.

## How it's built

```
CRM export → score (engagement / fit / recency / tech) → tier (1:1 / 1:few / 1:many) → draft → export
```

There are two versions of the same scoring logic: a Python CLI
(`score_and_draft.py`) for a batch job against a real CRM export, and a JS
version inside `index.html` for the interactive version. I ported the math
twice on purpose and checked the outputs account-by-account to make sure
both agree exactly — same inputs, same score, every time. (They do — check
Brightline Logistics and Vantage Retail Co in both `scored_accounts.csv` and
the app; they match to one decimal place.)

## Judgment calls worth knowing about

- Tech-stack overlap is capped at 15% of the total score on purpose. An
  earlier version weighted it higher, and it kept surfacing accounts that
  already use compatible tools but haven't shown any real interest lately —
  technically a good fit, not who a rep should be calling this week.
- A demo request auto-promotes an account to the 1:1 tier regardless of its
  score. A low-fit account that asked for a demo is still a live
  opportunity; the model shouldn't bury it under a formula.
- The tier cutoffs (70 / 45) are round numbers I picked for legibility, not
  numbers backed by real win-rate data yet. The honest next step is tuning
  them against actual close rates once there's a real CRM behind this.

## What's real and what's a stand-in

The scoring, weighting, tiering, filtering, sorting, and CSV export all
genuinely run — nothing is hardcoded per account. What's stubbed for the
demo: `accounts.csv` is synthetic, and outreach copy is templated instead of
calling a live LLM, so this runs with zero API keys or CRM credentials.
Wiring it to production means pointing ingestion at a real HubSpot/Salesforce
export, swapping the template in `draftFor()` / `draft_outreach()` for an
actual LLM call, and replacing the CSV export with a real CRM write-back.
