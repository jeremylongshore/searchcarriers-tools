---
name: searchcarriers-authority-checker
description: Checks carrier operating authority status, types, and history to determine what a carrier can legally transport. Use when verifying a carrier's authority or investigating revocations.
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
- vetting-risk
---

# Authority Checker

## Overview

Operating authority is the legal permission granted by FMCSA that determines what a carrier, broker, or freight forwarder can do. A carrier with revoked authority is prohibited from operating. A broker without active authority cannot legally arrange transportation. Authority type determines scope — common authority allows for-hire carriage, contract authority allows carriage under specific contracts, and broker authority allows arranging transportation without asset ownership.

This skill fetches authority records and history from the SearchCarriers API, interprets authority types and statuses, flags risk indicators like recent grants, revocations, and chameleon carrier signals, and produces a clear authority assessment. It is the foundational check in any carrier vetting workflow.

## Prerequisites

- **Minimum tier**: Free
- Environment variable `SEARCHCARRIERS_API_KEY` must be set with a valid API key (Free tier or above).
- The carrier's DOT number must be known. If only an MC number or name is available, use the `/search` endpoint first to resolve the DOT number.
- `curl` and optionally `python3` must be available in the execution environment.

## Instructions

### Step 1: Resolve the Carrier DOT Number

If the user provides a DOT number, proceed to Step 2. Otherwise, resolve the identifier.

```bash
# Search by MC number
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v3/search?docketNumber=1672915"

# Search by legal name
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v3/search?superSearchTerm=SWIFT%20TRANSPORTATION"

# Search by DOT number
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v3/search?dotNumber=12345"
```

From the search response, extract `dot_number` and also note these carrier-level fields for later use:
- `status_code` — Overall FMCSA status ("A" = active, "I" = inactive, etc.)
- `prior_revoke_flag` — "Y" if the carrier previously operated under a different DOT that was revoked
- `prior_revoke_dot_number` — The previous DOT number (chameleon carrier indicator)
- `add_date` — When this DOT was registered with FMCSA
- `carrier_operation` — Type of operation (interstate, intrastate, etc.)
- `company_officers` — Names and titles of company officers

### Step 2: Fetch Authority Records

```bash
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v1/company/{dot}/authorities"
```

The response contains authority records with these key fields:
- `broker_authority_status` — Status of broker authority: "authorized", "pending", "revoked", or null
- `contract_authority_status` — Status of contract carrier authority
- `common_authority_status` — Status of common (for-hire) carrier authority
- `sub_types` — Object containing:
  - `passenger` — Whether authorized for passenger transport
  - `property` — Whether authorized for property (freight) transport
  - `household_goods` — Whether authorized for household goods moves
- `status_since_date` — When the current status took effect
- `docket_number` — The MC, FF, or MX number assigned to this authority

### Step 3: Interpret Authority Types

Understanding authority types is essential for correct vetting:

**Common Authority (MC Number)**
- Grants the right to transport property or passengers **for hire** — meaning the carrier is paid by shippers/brokers.
- Most trucking companies need common authority.
- Sub-types determine what they can haul:
  - **Property**: General freight, specialized commodities
  - **Passenger**: Buses, charter services
  - **Household Goods**: Moving companies (additional regulations apply under 49 CFR Part 375)

**Contract Authority**
- Allows a carrier to haul under specific, ongoing contracts with individual shippers.
- Less common today; most carriers prefer common authority for flexibility.
- A carrier can hold both common and contract authority simultaneously.

**Broker Authority (MC Number)**
- Allows arranging transportation of freight without owning trucks.
- Brokers must maintain a $75,000 surety bond (BMC-84) or trust fund (BMC-85).
- A company can hold both carrier and broker authority under the same DOT.

**Freight Forwarder Authority (FF Number)**
- Allows assembling and consolidating shipments.
- Freight forwarders take possession of freight and issue their own bill of lading.

**Docket Number Prefixes**
| Prefix | Meaning |
|--------|---------|
| MC | Motor Carrier or Broker |
| FF | Freight Forwarder |
| MX | Mexico-domiciled carrier (requires additional FMCSA registration) |

### Step 4: Evaluate Authority Status

For each authority type present, classify the status:

| Status | Meaning | Vetting Impact |
|--------|---------|----------------|
| **Authorized** | Active, legal to operate | PASS |
| **Pending** | Application submitted, not yet approved | REVIEW — cannot legally operate yet |
| **Revoked** | Authority taken away by FMCSA | FAIL — cannot legally operate |
| **Inactive** | Voluntarily deactivated | FAIL — not currently authorized |
| **Not Authorized** | Never held this type | Neutral — only relevant if the carrier needs this type |

### Step 5: Fetch Authority History

Authority history reveals the timeline of status changes, which is critical for risk assessment.

```bash
# Fetch authority history (paginated)
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v1/authority/{docketNumber}/history?page=1&perPage=50"
```

Analyze the history for these patterns:

1. **Revocation followed by reinstatement**: This means the carrier lost authority (usually due to insurance lapse) and later regained it. One occurrence may be explainable; multiple occurrences are a red flag.

2. **Recent grant date**: Calculate the age of the authority from `status_since_date` or the earliest "authorized" entry in history.
   - **< 6 months**: Very new, high risk. Limited safety data available.
   - **6-18 months**: New entrant. FMCSA New Entrant Safety Audit should be complete or pending.
   - **18-36 months**: Established but still relatively young.
   - **> 36 months**: Mature authority.

3. **Multiple authority types added/removed**: Can indicate business model changes or instability.

4. **Short-lived authorities**: Authority granted and revoked within a few months suggests inability to maintain insurance or compliance.

### Step 6: Check for Chameleon Carrier Indicators

Chameleon carriers are unsafe operators who shut down and reopen under a new DOT. Authority data provides key indicators:

```python
import json
from datetime import datetime, timedelta


def check_chameleon_risk(carrier, authority):
    risks = []

    # Check prior revocation flag
    if carrier.get("prior_revoke_flag") == "Y":
        prev_dot = carrier.get("prior_revoke_dot_number", "unknown")
        risks.append(
            {
                "indicator": "PRIOR_REVOCATION",
                "severity": "HIGH",
                "detail": f"Carrier previously operated under DOT {prev_dot} which was revoked",
            }
        )

    # Check authority age
    add_date = datetime.strptime(carrier["add_date"], "%Y-%m-%d")
    age_months = (datetime.now() - add_date).days / 30
    if age_months < 18:
        risks.append(
            {
                "indicator": "NEW_AUTHORITY",
                "severity": "MEDIUM",
                "detail": f"Authority is only {int(age_months)} months old (new entrant)",
            }
        )

    # New authority + prior revocation = strong chameleon signal
    if age_months < 18 and carrier.get("prior_revoke_flag") == "Y":
        risks.append(
            {
                "indicator": "CHAMELEON_PATTERN",
                "severity": "CRITICAL",
                "detail": "New authority combined with prior revocation — strong chameleon carrier indicator",
            }
        )

    return risks
```

### Step 7: Determine Required Authority for the Use Case

Match the carrier's authority to what is needed:

- **Hiring a carrier to haul freight**: Requires common or contract authority with property sub_type authorized.
- **Hiring a broker to arrange freight**: Requires broker authority authorized.
- **Hiring a carrier for a household goods move**: Requires common authority with household_goods sub_type authorized.
- **Hiring a passenger carrier**: Requires common authority with passenger sub_type authorized.
- **Mexico cross-border freight**: Requires MX docket number and appropriate authority.

If the carrier lacks the required authority type for the intended use, this is an automatic **FAIL**.

### Step 8: Build the Authority Report

```
AUTHORITY STATUS REPORT — DOT {dot_number}
Carrier: {legal_name}
Report Date: {today}
FMCSA Status: {status_code}

AUTHORITY TYPES
  Common Authority: {status} (since {date})
    Property: {authorized/not authorized}
    Passenger: {authorized/not authorized}
    Household Goods: {authorized/not authorized}
  Contract Authority: {status} (since {date})
  Broker Authority: {status} (since {date})
  Docket Number: {MC/FF/MX}-{number}

AUTHORITY AGE
  DOT Registration Date: {add_date}
  Authority Age: {X} months
  Classification: {New Entrant / Established / Mature}

HISTORY ANALYSIS
  Total status changes: {count}
  Revocations found: {count}
  Reinstatements found: {count}
  [Timeline of significant changes]

CHAMELEON CARRIER CHECK
  Prior Revocation Flag: {Y/N}
  Prior DOT Number: {number or N/A}
  Risk Level: {LOW / MEDIUM / HIGH / CRITICAL}

OVERALL AUTHORITY VERDICT: PASS / FAIL / REVIEW
[Explanation of verdict]
```

### Decision Logic

- **FAIL** if:
  - Required authority type is revoked or inactive
  - Carrier status_code is not "A" (active)
  - Carrier has no authority of any type
- **REVIEW** if:
  - Authority is less than 18 months old (new entrant)
  - Prior revocation flag is set
  - History shows revocation/reinstatement pattern
  - Authority is pending (not yet granted)
- **PASS** if:
  - Required authority type is authorized
  - Authority age is 18+ months
  - No prior revocation
  - Stable history with no revocations

## Examples

### Check authority for a DOT number

**User prompt**: "Check authority for DOT 12345"

Fetch authority records and history. Report all authority types, their statuses, authority age, and any risk flags. Produce the full authority report with a verdict.

### Verify property hauling authorization

**User prompt**: "Is this carrier authorized to haul property?"

Focus on common authority status and the property sub_type. Check that `common_authority_status` is "authorized" and `sub_types.property` is true. Respond with a clear yes/no, the docket number, and any caveats (new authority, prior revocation, etc.).

### Authority history investigation

**User prompt**: "Show authority history for this carrier"

Fetch the full authority history via `/authority/{docketNumber}/history`. Present a chronological timeline of all status changes. Highlight revocations, reinstatements, and any patterns. Calculate time between events. Note if the authority has been stable or volatile.

### MC vs DOT number explanation

**User prompt**: "What's the difference between this carrier's MC and DOT numbers?"

Explain that the DOT number is the FMCSA registration number (required for all commercial vehicles in interstate commerce) while the MC number is the operating authority docket number (required for for-hire carriers and brokers). A carrier can have a DOT number without an MC number if they operate as a private carrier. Show both numbers from the carrier record and what authority the MC number grants.

## Output

Return the requested result with the API route version, relevant carrier identifiers, evidence, missing-data limits, and the next operational action. Never include an API token or an unredacted bulk API response.

## Error Handling

| Error | Cause | Resolution |
|---|---|---|
| `401 Unauthorized` | Invalid or expired API key | Verify `SEARCHCARRIERS_API_KEY` is set correctly |
| `404 Not Found` | DOT number does not exist | Verify the DOT number; search by name or MC number instead |
| `429 Too Many Requests` | Rate limit exceeded | Wait and retry; the Free tier has lower rate limits |
| Empty authorities response | Carrier has no operating authority on file | Report as a finding — carrier may be a private carrier or may have never applied for authority |
| `status_since_date` is null | FMCSA data gap | Use `add_date` from carrier record as a fallback for authority age calculation |
| History pagination | More history pages exist | Always check for pagination indicators and fetch all pages |

When encountering errors, report them clearly. Authority status is binary — a carrier is either authorized or not. Ambiguity should always result in a REVIEW verdict, never a PASS.

## Resources

- FMCSA Operating Authority Overview: 49 CFR Parts 365, 368
- FMCSA New Entrant Safety Assurance Program: 49 CFR Part 385 Subpart D
- FMCSA Household Goods Regulations: 49 CFR Part 375
- Docket number registration: FMCSA OP-1 Form
- SearchCarriers API documentation: https://searchcarriers.com/docs/api and the repository `API-DISCOVERY.md`
- Authority status codes reference: `{baseDir}/docs/authority-codes.md`
- FMCSA SAFER System: https://safer.fmcsa.dot.gov
- FMCSA LICENSING & INSURANCE (L&I) System: https://li-public.fmcsa.dot.gov
