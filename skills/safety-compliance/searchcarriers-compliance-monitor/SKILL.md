---
name: searchcarriers-compliance-monitor
description: Tracks MCS-150 currency, registration freshness, safety reviews, and insurance status. Use when checking carrier compliance or filing status.
allowed-tools: Read,Grep,Bash(curl:*),Bash(python:*)
metadata:
  tier: pro
version: 0.2.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: Apache-2.0
compatibility: Claude Code or another MCP-capable client; Python 3.10+; network access to searchcarriers.com; an appropriate SearchCarriers API subscription.
tags:
- searchcarriers
- motor-carrier
- safety-compliance
---

# Compliance Monitor

Track and assess a motor carrier's regulatory compliance posture — MCS-150
filing currency, registration status, safety review freshness, MCSI&P
oversight, and insurance coverage. Produce a compliance checklist with
pass/fail/warning status for each item and flag anything that needs attention.

## Overview

FMCSA compliance is not a single score — it is a mosaic of filings, reviews,
registrations, and insurance requirements, each with its own lifecycle and
expiration logic. Brokers and shippers often check only operating authority
status and miss critical signals like a lapsed MCS-150 filing (which can
trigger registration revocation) or stale insurance on file.

**Key compliance signals and their decay rates:**

| Signal | Source Field | Freshness Rule |
|---|---|---|
| MCS-150 filing | `mcs150_date` | Must be updated biennially (every 24 months). Stale filings can lead to FMCSA deactivation. |
| Operating status | `status_code` | "A" = Active. Anything else = cannot legally operate for hire. |
| Registration age | `add_date` | Date carrier was first registered. Carriers under 18 months old are statistically higher risk (New Entrant program). |
| Safety rating | `safety_rating` + `safety_rating_date` | Compliance review result. Older ratings have less predictive value. |
| Safety review | `review_type` + `review_date` | Most recent review of any type. |
| MCSI&P status | `mcsipstep` + `mcsipdate` | Active enforcement process. Any value here is a flag. |
| Insurance | Via `/company/{DOT}/insurances` | FMCSA-filed insurance must be active and meet minimum requirements. |

**New Entrant Safety Assurance Program**: Carriers registered for fewer than
18 months are in the New Entrant program and subject to a mandatory safety
audit. During this period, they operate under heightened scrutiny. Failure to
pass the audit results in revocation. Carriers in this window present
elevated risk not because they are inherently unsafe but because they have no
track record.

## Prerequisites

- **Minimum tier**: Pro
- Environment variable `SEARCHCARRIERS_API_KEY` is set with a valid Pro-tier key.
- `curl` and optionally `python3` available in the shell.
- A DOT number for the carrier to evaluate.

## Instructions

### 1. Fetch carrier data

```bash
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v3/search?dotNumber={DOT}"
```

Parse the carrier object from the response. Extract all compliance-relevant
fields listed in the Overview table.

### 2. Check MCS-150 currency

The MCS-150 (Motor Carrier Identification Report) must be updated every 24
months. Calculate months since last filing:

```python
from datetime import datetime

mcs150_date = datetime.strptime(carrier["mcs150_date"], "%Y-%m-%d")
months_since = (datetime.now() - mcs150_date).days / 30.44

if months_since <= 24:
    status = "CURRENT"
    note = f"Filed {months_since:.0f} months ago. Next filing due by {next_due}."
elif months_since <= 30:
    status = "WARNING"
    note = (
        f"Filed {months_since:.0f} months ago. Past the 24-month biennial deadline. "
        "FMCSA may begin deactivation proceedings."
    )
else:
    status = "OVERDUE"
    note = (
        f"Filed {months_since:.0f} months ago. Significantly past deadline. "
        "Carrier risks involuntary deactivation if not already flagged."
    )
```

**Why this matters**: FMCSA periodically deactivates carriers with overdue
MCS-150 filings. An overdue filing often correlates with disengagement from
compliance obligations generally. Some brokers use MCS-150 currency as a
first-pass vetting filter.

### 3. Evaluate operating status

Check `status_code`:

| Code | Meaning | Action |
|---|---|---|
| `A` | Active — authorized to operate | Pass. Continue with remaining checks. |
| `I` | Inactive — not authorized | **Fail.** Carrier cannot legally operate for hire. Full stop. No further compliance checks are meaningful if the carrier is inactive. |
| Other codes | Various administrative states | Flag and explain. The carrier may be in a transitional state (e.g., pending reactivation). |

### 4. Assess registration age and New Entrant status

Calculate the carrier's age from `add_date`:

```python
add_date = datetime.strptime(carrier["add_date"], "%Y-%m-%d")
months_registered = (datetime.now() - add_date).days / 30.44

if months_registered < 18:
    status = "NEW ENTRANT"
    note = (
        f"Registered {months_registered:.0f} months ago. Still in the FMCSA New Entrant "
        "Safety Assurance Program. Subject to mandatory safety audit. Higher statistical "
        "risk profile due to limited operating history."
    )
elif months_registered < 36:
    status = "RELATIVELY NEW"
    note = (
        f"Registered {months_registered:.0f} months ago. Past New Entrant period but "
        "limited track record."
    )
else:
    status = "ESTABLISHED"
    note = f"Registered {months_registered / 12:.1f} years ago."
```

**Industry context**: New Entrant carriers (< 18 months) have crash rates
roughly 2-3x higher than established carriers. This is a well-documented
FMCSA finding. It does not mean every new carrier is dangerous, but the
statistical risk is real and should be noted.

### 5. Evaluate safety review freshness

Check `safety_rating_date` and `review_date`:

```python
if carrier.get("safety_rating_date"):
    rating_date = datetime.strptime(carrier["safety_rating_date"], "%Y-%m-%d")
    rating_age_years = (datetime.now() - rating_date).days / 365.25

    if rating_age_years <= 3:
        status = "CURRENT"
        note = f"{carrier['safety_rating']} rating from {rating_age_years:.1f} years ago."
    elif rating_age_years <= 5:
        status = "AGING"
        note = (
            f"{carrier['safety_rating']} rating from {rating_age_years:.1f} years ago. "
            "Still valid but may not reflect current operations."
        )
    else:
        status = "STALE"
        note = (
            f"{carrier['safety_rating']} rating from {rating_age_years:.1f} years ago. "
            "Limited relevance to current compliance posture."
        )
else:
    status = "NONE"
    note = "No safety rating on file. Carrier has never undergone a compliance review."
```

Cross-reference with `review_date` and `review_type`. A carrier may have a
recent review event (e.g., a focused review or complaint investigation) even
if the formal safety rating is old.

### 6. Check MCSI&P enforcement status

If `mcsipstep` is populated:

```python
if carrier.get("mcsipstep"):
    status = "FLAGGED"
    step = carrier["mcsipstep"]
    step_date = carrier.get("mcsipdate", "unknown date")
    note = (
        f"Carrier is in the MCSI&P enforcement process at stage: {step} "
        f"(since {step_date}). This indicates FMCSA has identified safety "
        "concerns through BASICs scores and is actively pursuing enforcement."
    )
else:
    status = "CLEAR"
    note = "Not currently under enhanced FMCSA oversight."
```

**Interpretation**: Any MCSI&P status is a compliance concern. The process
only triggers when a carrier's BASICs scores exceed intervention thresholds.
Early stages (Warning Letter) are less severe but still indicate the carrier
is on FMCSA's radar. Later stages (Investigation, Proposed Rating) indicate
active enforcement.

### 7. Verify insurance status

Fetch insurance filings:

```bash
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v1/company/{DOT}/insurances"
```

Check for:

- **Active filings**: At least one active liability insurance filing (Form
  BMC-91 or BMC-91X for brokers, MCS-90 for carriers).
- **Minimum coverage**: Federal minimum is $750,000 for general freight,
  $1,000,000 for hazmat, $5,000,000 for certain hazmat classes. Many
  shippers require $1M minimum regardless of commodity.
- **Filing currency**: Insurance can be cancelled with 30 days' notice to
  FMCSA. Check that coverage is currently active, not in a cancellation
  pending state.

```python
active_policies = [p for p in insurances if p.get("status") == "Active"]

if not active_policies:
    status = "FAIL"
    note = (
        "No active insurance filings on record with FMCSA. "
        "Carrier cannot legally operate without required insurance."
    )
else:
    status = "PASS"
    # Report coverage amounts and insurer names
```

### 8. Build the compliance checklist

Compile all checks into a structured checklist:

**Compliance Checklist for [Legal Name] (DOT [number])**

| Check | Status | Detail |
|---|---|---|
| Operating Status | PASS / FAIL | Active or Inactive |
| MCS-150 Filing | CURRENT / WARNING / OVERDUE | Months since filing |
| Registration Age | ESTABLISHED / NEW ENTRANT | Months/years registered |
| Safety Rating | CURRENT / AGING / STALE / NONE | Rating and date |
| MCSI&P Status | CLEAR / FLAGGED | Stage if applicable |
| Insurance | PASS / FAIL | Active filings and coverage |
| Safety Review | CURRENT / AGING / STALE / NONE | Last review type and date |

**Overall Compliance Posture**: Summarize in one paragraph using these tiers:

- **Strong**: All checks pass. Current MCS-150, active status, established
  carrier, current or no-issues safety record, clear MCSI&P, active
  insurance.
- **Adequate**: Most checks pass. Minor warnings (aging safety rating,
  MCS-150 approaching deadline).
- **Concerns**: One or more warning-level items. MCS-150 overdue, very new
  carrier, stale safety rating. Not necessarily disqualifying but warrants
  additional diligence.
- **Deficient**: Any hard fail. Inactive status, no insurance, active
  enforcement. Do not tender freight without resolution.

### 9. Provide actionable recommendations

Based on the checklist results, provide specific next steps:

- If MCS-150 is overdue: "Carrier should file an updated MCS-150 immediately
  via FMCSA portal to avoid deactivation."
- If no safety rating: "Consider requesting a pre-screening report or
  reviewing inspection history via the inspection-analyzer skill."
- If New Entrant: "Verify the carrier has completed their New Entrant safety
  audit. Request a copy of the audit results."
- If insurance has issues: "Confirm insurance directly with the carrier's
  insurer. FMCSA filings can lag behind actual coverage changes."
- If MCSI&P flagged: "Monitor this carrier closely. Consider the
  safety-scorer skill for full safety context."

## Examples

### Example 1: Full compliance check

**User prompt**: "Check compliance status for DOT 12345"

```bash
# Fetch carrier data
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v3/search?dotNumber=12345"

# Fetch insurance data
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v1/company/12345/insurances"
```

**Response pattern**: Full compliance checklist table with all 7 checks, each
showing PASS/WARNING/FAIL status with detail. Overall assessment: "ABC
Trucking has a strong compliance posture. All filings are current, operating
status is active, and insurance is in good standing. The carrier has been
registered for 8 years with a Satisfactory safety rating from 2022."

### Example 2: MCS-150 currency check

**User prompt**: "Is this carrier's MCS-150 current? DOT 67890"

```bash
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v3/search?dotNumber=67890"
```

**Response pattern**: "XYZ Transport's MCS-150 was last filed on 2023-11-15,
which is 27 months ago. This is OVERDUE — the biennial filing deadline has
passed by 3 months. While the carrier's operating authority is still active,
continued non-filing puts them at risk of FMCSA-initiated deactivation. The
carrier should file an updated MCS-150 through the FMCSA portal immediately."

### Example 3: New carrier vetting

**User prompt**: "Give me a compliance checklist for DOT 11111"

**Response pattern**: "DEF Logistics (DOT 11111) was registered 9 months ago
and is currently in the New Entrant Safety Assurance Program. Key findings:
MCS-150 is current (filed at registration). No safety rating — expected for
a carrier this new. MCSI&P clear. Insurance active with $1M liability
coverage. Overall: Adequate compliance posture for a New Entrant, but
elevated statistical risk due to limited operating history. Recommend
verifying completion of the mandatory safety audit and reviewing any
available inspection records."

## Output

Return the requested result with the API route version, relevant carrier identifiers, evidence, missing-data limits, and the next operational action. Never include an API token or an unredacted bulk API response.

## Error Handling

| Scenario | Action |
|---|---|
| `SEARCHCARRIERS_API_KEY` not set | Print: "Set the SEARCHCARRIERS_API_KEY environment variable before running this skill." and stop. |
| API returns 401 | API key is invalid, expired, or not Pro tier. This skill requires a Pro-tier key for insurance endpoint access. |
| API returns 404 or empty results | DOT number not found. Confirm the number is correct. |
| API returns 429 | Rate limited. Wait and retry with backoff. |
| `mcs150_date` is null or empty | State that MCS-150 date is not available. This may indicate a data gap or a very old registration that predates electronic filing. Do not report it as overdue — report it as unknown. |
| `add_date` is null | Cannot calculate registration age. Note the gap and skip the New Entrant assessment. |
| Insurance endpoint returns empty | Either the carrier has no insurance filings or the data is not available. Distinguish between "no filings" (fail) and "data unavailable" (unknown). Check if the carrier type requires FMCSA-filed insurance — some private carriers do not. |
| Date fields in unexpected formats | Use lenient parsing. If a date cannot be parsed, report the raw value and note that age calculation was not possible. |
| Carrier is a broker or freight forwarder | Adjust insurance requirements. Brokers need BMC-84 (surety bond) or BMC-85 (trust fund), not MCS-90. Note the entity type and apply correct requirements. |

## Resources

- [MCS-150 Filing Requirements](https://www.fmcsa.dot.gov/registration/updating-your-registration) — biennial update rules and deadlines
- [New Entrant Safety Assurance Program](https://www.fmcsa.dot.gov/safety/new-entrant-safety-assurance-program) — audit requirements for new carriers
- [FMCSA Insurance Requirements](https://www.fmcsa.dot.gov/registration/insurance-requirements) — minimum coverage by commodity type
- [MCSI&P Process](https://www.fmcsa.dot.gov/safety/carrier-safety/motor-carrier-safety-improvement-process) — enforcement pipeline stages
- SearchCarriers API documentation: https://searchcarriers.com/docs/api and the repository `API-DISCOVERY.md`
