---
name: searchcarriers-safety-scorer
description: Translates FMCSA safety ratings, review history, and crash data into plain-English carrier safety summaries. Use when a user asks how safe a carrier is or wants a safety rating explained.
allowed-tools: Read,Grep,Bash(curl:*),Bash(python:*)
metadata:
  tier: free
version: 0.2.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: Apache-2.0
compatibility: Claude Code or another MCP-capable client; Python 3.10+; network access to searchcarriers.com; an appropriate SearchCarriers API subscription.
tags:
- searchcarriers
- motor-carrier
- safety-compliance
---

# Safety Scorer

Interpret FMCSA safety data from the SearchCarriers API and produce a
plain-English safety summary for any motor carrier. Freight professionals
routinely confuse Safety Ratings with CSA/BASICs scores, misread missing data
as negative signals, and lack context for crash-rate numbers. This skill fills
that gap.

## Overview

The FMCSA Safety Rating is assigned during an on-site **Compliance Review**
(CR) or **Security Contact Review** (SCR). It is *not* the same as a CSA
score, a BASICs percentile, or an SMS alert. The three possible ratings are:

| Rating | Meaning |
|---|---|
| **Satisfactory** | Carrier demonstrated adequate safety management controls during the review. |
| **Conditional** | Carrier has deficiencies that could result in an Unsatisfactory rating if not corrected. Operating authority remains active but shippers and brokers often treat this as a red flag. |
| **Unsatisfactory** | Carrier failed to demonstrate adequate safety management. Operating authority may be revoked. |
| **None / blank** | Carrier has never undergone a compliance review. This is *normal* — the vast majority of carriers (especially small fleets) have never been reviewed. It does NOT mean the carrier is unsafe. |

The **MCSI&P** (Motor Carrier Safety Improvement Process) is an escalating
enforcement pipeline. A carrier enters it when BASICs scores trigger
intervention thresholds. Stages progress from warning letters to
investigations to proposed and final ratings.

## Prerequisites

- **Minimum tier**: Free
- Environment variable `SEARCHCARRIERS_API_KEY` is set with a valid API key.
- `curl` and optionally `python3` available in the shell.
- A DOT number for the carrier to evaluate.

## Instructions

### 1. Fetch carrier data

Query the search endpoint with the carrier's DOT number:

```bash
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v3/search?dotNumber={DOT}"
```

Parse the first result from the response. The carrier object contains 143
fields; the safety-relevant subset is:

| Field | Type | Notes |
|---|---|---|
| `safety_rating` | string | "Satisfactory", "Conditional", "Unsatisfactory", or empty |
| `safety_rating_date` | date | Date of the compliance review that produced the rating |
| `review_type` | string | Type of review (e.g., "CR" = Compliance Review, "SCR" = Security Contact Review) |
| `review_date` | date | Date of the most recent review event |
| `mcsipstep` | string | Current MCSI&P stage, empty if not in the process |
| `mcsipdate` | date | Date the carrier entered the current MCSI&P stage |
| `recordable_crash_rate` | number | DOT-recordable crashes per million miles |
| `status_code` | string | "A" = Active, "I" = Inactive |

### 2. Interpret the safety rating

Apply these interpretation rules in order:

1. **Unsatisfactory** — Carrier has failed a compliance review. This is the
   most severe rating. Check `safety_rating_date` to determine recency. An
   Unsatisfactory rating from this year is an immediate disqualifier for most
   brokers. One from 5+ years ago may have been superseded by operational
   changes, but the formal rating persists until a new review occurs.

2. **Conditional** — Carrier passed with deficiencies. Check `review_date` to
   see how recently this was assessed. If the rating is recent (< 2 years),
   the carrier is actively under scrutiny. If older, conditions may have been
   addressed but no follow-up review occurred.

3. **Satisfactory** — The best possible rating. Note the date: a Satisfactory
   rating from 2015 tells you the carrier was compliant a decade ago. FMCSA
   does not routinely re-review carriers, so a stale Satisfactory rating is
   still positive but not a guarantee of current compliance.

4. **No rating** — The carrier has never been reviewed. Explain clearly:
   *"This carrier has no FMCSA Safety Rating. This does not indicate a
   problem — the majority of active carriers have never undergone a compliance
   review. Safety Ratings are only assigned when FMCSA conducts an on-site
   review, which is triggered by BASICs alerts, complaints, or crashes."*

### 3. Check MCSI&P status

If `mcsipstep` is populated, the carrier is in the enforcement pipeline.
Interpret the stage:

| Step | Meaning |
|---|---|
| Warning Letter | BASICs thresholds triggered a formal notice. Earliest stage. |
| Investigation | FMCSA is actively investigating the carrier. |
| Cooperative Safety Plan | Carrier agreed to a corrective action plan. |
| NOD (Notice of Deficiency) | Formal deficiencies identified post-investigation. |
| Proposed Rating | FMCSA has proposed a Conditional or Unsatisfactory rating. |
| Final Rating | The proposed rating has been finalized. |
| Operations Out-of-Service | Carrier has been ordered to cease operations. Most severe. |

Include `mcsipdate` to show how long the carrier has been at the current step.
A carrier stuck at "Investigation" for 6+ months may indicate a complex case.

### 4. Evaluate crash rate

`recordable_crash_rate` is DOT-recordable crashes per million vehicle miles
traveled. Context matters:

- **0.0** — No recordable crashes. Good, but may also indicate very low
  mileage or recent registration.
- **< 1.0** — Below industry average for most segments. Generally favorable.
- **1.0 - 2.0** — Elevated. Warrants attention, especially for larger fleets
  where the mileage denominator should smooth out randomness.
- **> 2.0** — Significantly elevated. Flag this clearly.
- **No value** — Crash rate data is not available for all carriers. Not
  necessarily concerning.

Always caveat: crash rate alone is insufficient. A single crash for a
one-truck carrier produces a misleadingly high rate. Fleet size context from
`total_power_units` is essential.

### 5. Compose the plain-English summary

Structure the output as:

**Safety Summary for [Legal Name] (DOT [number])**

1. **Rating**: One sentence on the safety rating and its date (or absence).
2. **Enforcement**: One sentence on MCSI&P status (or "Not currently under
   enhanced oversight").
3. **Crash Rate**: One sentence with context.
4. **Review History**: When the carrier was last reviewed, what type.
5. **Bottom Line**: A single-sentence overall assessment using freight
   industry language. Examples:
   - *"This carrier is in good standing with a current Satisfactory rating and
     no enforcement actions."*
   - *"This carrier has a Conditional rating from 2022 and is currently under
     investigation — proceed with caution and verify insurance."*
   - *"This carrier has never been reviewed by FMCSA. This is normal for
     small carriers but means there is no federal safety opinion on file."*

### 6. Explain what's missing

Always end with a "What this doesn't tell you" section:

- Safety Rating is NOT the same as CSA/BASICs scores. BASICs percentiles
  come from inspection and crash data and are not included in this endpoint.
- A Satisfactory rating does not mean the carrier is currently safe — it
  means they passed a review at a point in time.
- No rating does not mean the carrier is unsafe — it means FMCSA has not
  conducted a review.
- Crash rate without fleet size and mileage context can be misleading.
- For deeper analysis, use the `searchcarriers-inspection-analyzer` skill
  to examine actual inspection history and violation patterns.

## Examples

### Example 1: Rated carrier in good standing

**User prompt**: "How safe is DOT 12345?"

```bash
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v3/search?dotNumber=12345"
```

**Response pattern**: "ABC Trucking (DOT 12345) has a Satisfactory safety
rating issued on 2023-06-15 following a Compliance Review. They are not
currently in the MCSI&P enforcement process. Their recordable crash rate is
0.4, which is below industry average. Bottom line: this carrier is in good
standing with a recent favorable review."

### Example 2: Unrated carrier

**User prompt**: "Is DOT 67890 rated?"

**Response pattern**: "XYZ Transport (DOT 67890) has no FMCSA Safety Rating.
This is normal — the majority of active carriers have never undergone an
on-site compliance review. The absence of a rating does not indicate safety
concerns. Their recordable crash rate is 0.0 and they are not under any
enforcement action. To assess this carrier's safety posture, examine their
inspection history using the inspection-analyzer skill."

### Example 3: Carrier under enforcement

**User prompt**: "Explain this carrier's safety record for DOT 11111"

**Response pattern**: "DEF Logistics (DOT 11111) has a Conditional safety
rating from 2021-09-20. They are currently at the 'Investigation' stage of
the MCSI&P process as of 2024-03-10, meaning FMCSA is actively examining
their operations. Their recordable crash rate is 1.8, which is elevated.
Bottom line: this carrier has multiple risk signals — a Conditional rating,
active federal investigation, and above-average crash rate. Recommend
additional vetting before tendering freight."

## Output

Return the requested result with the API route version, relevant carrier identifiers, evidence, missing-data limits, and the next operational action. Never include an API token or an unredacted bulk API response.

## Error Handling

| Scenario | Action |
|---|---|
| `SEARCHCARRIERS_API_KEY` not set | Print: "Set the SEARCHCARRIERS_API_KEY environment variable before running this skill." and stop. |
| API returns 401 | API key is invalid or expired. Advise the user to check their key. |
| API returns 404 or empty results | DOT number not found. Confirm the number is correct. Suggest searching by name or MC number instead. |
| API returns 429 | Rate limited. Wait and retry. Free tier has lower rate limits. |
| Safety fields are all empty | Carrier exists but has no safety data. This is different from "no rating" — it may indicate a very new registration. Note the `add_date` field. |
| `recordable_crash_rate` is null | State that crash rate data is not available rather than reporting it as zero. |

## Resources

- [FMCSA Safety Rating Methodology](https://www.fmcsa.dot.gov/safety/carrier-safety/motor-carrier-safety-rating-methodology)
- [CSA/SMS Methodology](https://csa.fmcsa.dot.gov/About/Measures) — for understanding the difference between Safety Ratings and BASICs
- [MCSI&P Process Overview](https://www.fmcsa.dot.gov/safety/carrier-safety/motor-carrier-safety-improvement-process)
- SearchCarriers API documentation: https://searchcarriers.com/docs/api and the repository `API-DISCOVERY.md`
