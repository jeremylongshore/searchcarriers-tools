---
name: searchcarriers-insurance-validator
description: Validates carrier insurance coverage status, detects lapses, and verifies minimum coverage requirements. Use when vetting a carrier's insurance or checking for coverage gaps.
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
- vetting-risk
---

# Insurance Validator

## Overview

Insurance is the single most critical vetting requirement in freight. A carrier without active liability insurance is operating illegally, and any broker or shipper who tenders freight to an uninsured carrier faces catastrophic liability exposure.

This skill fetches insurance records from the SearchCarriers API, interprets coverage status, validates minimum amounts by operation type, detects lapses and pending cancellations, and cross-references insurance status with operating authority. It transforms raw insurance data into an actionable coverage assessment with clear pass/fail determinations.

## Prerequisites

- **Minimum tier**: Pro
- Environment variable `SEARCHCARRIERS_API_KEY` must be set with a valid Pro-tier API key.
- The carrier's DOT number must be known. If only an MC number or name is available, use the `/search` endpoint first to resolve the DOT number.
- `curl` and optionally `python3` must be available in the execution environment.

## Instructions

### Step 1: Resolve the Carrier DOT Number

If the user provides a DOT number, proceed to Step 2. If they provide an MC number, legal name, or other identifier, resolve it first.

```bash
# Search by MC number
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v3/search?docketNumber=1672915"

# Search by legal name
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v3/search?superSearchTerm=PACIFIC%20TRANSPORT"

# Search by DOT number directly
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v3/search?dotNumber=12345"
```

Extract the `dot_number` from the response to use in subsequent calls.

### Step 2: Fetch Insurance Records

Retrieve all insurance records for the carrier. The endpoint is paginated, so fetch all pages.

```bash
# Fetch first page of insurance records
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v1/company/{dot}/insurances?page=1&perPage=50"
```

Continue paginating until all records are retrieved. Each insurance record contains:
- `insurance_type` — The coverage type (e.g., BIPD, cargo, bond/trust, surety bond)
- `insurance_status` — Current status: active, cancelled, pending
- `policy_number` — The policy or surety number
- `insurance_company` — The insurer or surety company name
- `coverage_amount` — Dollar amount of coverage
- `effective_date` — When coverage began
- `cancelled_date` — When coverage was cancelled (null if active)
- `posted_date` — When the filing was posted with FMCSA

### Step 3: Classify Insurance by Coverage Type

Group the insurance records by type. The critical coverage categories are:

| Coverage Type | Code/Label | Purpose |
|---|---|---|
| **BIPD** | Bodily Injury & Property Damage | Required for all for-hire carriers. Covers third-party injury/damage. |
| **Cargo** | Cargo Insurance | Covers freight in transit. Not federally required but contractually expected. |
| **Bond/Trust** | BMC-84 Surety Bond or BMC-85 Trust Fund | Required for freight brokers and freight forwarders. $75,000 minimum. |
| **Surety Bond** | BMC-91X or BMC-91 | Alternative financial responsibility filing. |

### Step 4: Validate Minimum Coverage Amounts

Federal minimum insurance requirements vary by operation type and cargo:

| Operation Type | Minimum BIPD Required |
|---|---|
| General freight, < 10,001 lbs GVWR | $750,000 |
| General freight, >= 10,001 lbs GVWR | $1,000,000 |
| Hazardous materials (non-bulk) | $1,000,000 |
| Hazardous materials (bulk), compressed gas, explosives | $5,000,000 |
| Oil transport (bulk) | $1,000,000 |
| Household goods | $750,000 |
| Passengers (< 16 seats) | $1,500,000 |
| Passengers (>= 16 seats) | $5,000,000 |
| Freight brokers (BMC-84 or BMC-85) | $75,000 |

To determine which threshold applies, check the carrier's `carrier_operation` and `hm_ind` fields from the carrier object. If `hm_ind` is "Y", the carrier hauls hazmat and higher thresholds apply.

For each active BIPD policy, compare `coverage_amount` against the applicable minimum. Flag as **FAIL** if below minimum, **PASS** if at or above.

### Step 5: Detect Insurance Gaps and Lapses

Insurance lapses are among the most serious red flags in carrier vetting. Analyze the timeline:

1. **Sort all BIPD records by date** (effective_date and cancelled_date).
2. **Identify gaps**: Any period where no active BIPD policy existed. A gap means the carrier was operating without legally required insurance.
3. **Calculate gap duration**: Gaps longer than 1 day are reportable. Gaps longer than 30 days are severe.
4. **Check for overlapping policies**: Multiple active BIPD policies can indicate a carrier switching insurers — verify no gap exists between the old policy cancellation and new policy effective date.

```python
import json
from datetime import datetime, timedelta


# Parse insurance records (assume `records` is the list of BIPD insurance entries)
def detect_gaps(records):
    bipd = [
        r
        for r in records
        if "BIPD" in r.get("insurance_type", "").upper()
        or "BODILY" in r.get("insurance_type", "").upper()
    ]

    periods = []
    for r in bipd:
        eff = datetime.strptime(r["effective_date"], "%Y-%m-%d")
        cancel = (
            datetime.strptime(r["cancelled_date"], "%Y-%m-%d")
            if r.get("cancelled_date")
            else datetime.now()
        )
        periods.append((eff, cancel))

    periods.sort(key=lambda x: x[0])

    gaps = []
    if not periods:
        return [("NO_COVERAGE", "No BIPD records found")]

    for i in range(1, len(periods)):
        prev_end = periods[i - 1][1]
        curr_start = periods[i][0]
        if curr_start > prev_end + timedelta(days=1):
            gap_days = (curr_start - prev_end).days
            gaps.append(
                {
                    "from": prev_end.strftime("%Y-%m-%d"),
                    "to": curr_start.strftime("%Y-%m-%d"),
                    "days": gap_days,
                    "severity": "SEVERE" if gap_days > 30 else "WARNING",
                }
            )

    return gaps
```

### Step 6: Flag Pending Cancellations

A pending cancellation means the carrier's insurance is about to lapse. This is a critical vetting signal:

- If `insurance_status` is "pending" with a future `cancelled_date`, the carrier has a **pending cancellation**.
- Check if a replacement policy has been filed (look for a new record with a later `effective_date`).
- If no replacement exists, flag as **REVIEW WITH URGENCY** — the carrier may lose legal authority to operate.

### Step 7: Cross-Reference with Authority Status

Insurance and authority are linked. A carrier whose insurance lapses should have their authority revoked by FMCSA:

```bash
# Fetch authority status
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v1/company/{dot}/authorities"
```

Check for inconsistencies:
- **Active authority but no active insurance**: Critical red flag. The carrier is operating illegally.
- **Revoked authority but active insurance**: May indicate the carrier is in the process of reinstating.
- **Insurance cancelled but authority still active**: FMCSA revocation may be pending (there is typically a 30-day grace period after insurance cancellation before authority is revoked).

### Step 8: Build the Insurance Summary Report

Generate a structured report with the following sections:

```
INSURANCE VALIDATION REPORT — DOT {dot_number}
Carrier: {legal_name}
Report Date: {today}

COVERAGE STATUS
| Type | Provider | Policy # | Amount | Status | Effective | Cancelled |
|------|----------|----------|--------|--------|-----------|-----------|
| BIPD | [name]   | [num]    | $X     | Active | YYYY-MM-DD| —         |
| Cargo| [name]   | [num]    | $X     | Active | YYYY-MM-DD| —         |

MINIMUM COVERAGE CHECK
  Operation type: {carrier_operation}
  Hazmat indicator: {hm_ind}
  Required minimum BIPD: ${amount}
  Current BIPD coverage: ${amount}
  Result: PASS / FAIL

LAPSE ANALYSIS
  Total BIPD records analyzed: {count}
  Coverage gaps found: {count}
  [List each gap with dates and severity]

PENDING CANCELLATIONS
  [List any pending cancellations with dates]

AUTHORITY CROSS-REFERENCE
  Common authority: {status}
  Insurance supports authority: YES / NO

OVERALL INSURANCE VERDICT: PASS / FAIL / REVIEW
[Explanation of verdict]
```

### Decision Logic

Apply these rules to determine the overall insurance verdict:

- **FAIL** if:
  - No active BIPD insurance exists
  - BIPD coverage is below the federal minimum for the carrier's operation type
  - Active authority exists with no active insurance (illegal operation)
- **REVIEW** if:
  - Pending cancellation with no replacement policy on file
  - Coverage gaps exist in the last 24 months
  - BIPD coverage exactly meets the minimum (no margin)
  - Cargo insurance is missing (not federally required, but industry standard)
- **PASS** if:
  - Active BIPD at or above minimum coverage
  - No gaps in the last 24 months
  - No pending cancellations
  - Authority and insurance are consistent

## Examples

### Check insurance for a specific DOT number

**User prompt**: "Check insurance for DOT 12345"

Fetch insurance records, run all validation steps, and produce the full insurance summary report with pass/fail determination.

### Verify active liability coverage

**User prompt**: "Does this carrier have active liability coverage?"

Focus on BIPD records only. Check for an active policy with `insurance_status` = "active" and a null `cancelled_date`. Verify the coverage amount meets the minimum for the carrier's operation type. Respond with a clear yes/no and the coverage details.

### Show insurance history

**User prompt**: "Show me insurance history for MC 1672915"

First resolve the MC number to a DOT number via `/api/v3/search?docketNumber=1672915`. Then fetch all insurance records across all pages. Present them in chronological order, highlighting any gaps, cancellations, and changes in insurer. Include the lapse analysis.

### Validate insurance for hazmat carrier

**User prompt**: "Check if this hazmat carrier has enough insurance"

Check the carrier's `hm_ind` field. If "Y", apply the $5,000,000 minimum for bulk hazmat or $1,000,000 for non-bulk. Report the current BIPD amount and whether it meets the hazmat threshold.

## Output

Return the requested result with the API route version, relevant carrier identifiers, evidence, missing-data limits, and the next operational action. Never include an API token or an unredacted bulk API response.

## Error Handling

| Error | Cause | Resolution |
|---|---|---|
| `401 Unauthorized` | Invalid or expired API key | Verify `SEARCHCARRIERS_API_KEY` is set and the key has Pro-tier access |
| `404 Not Found` | DOT number does not exist in FMCSA database | Verify the DOT number; try searching by name or MC number instead |
| `429 Too Many Requests` | Rate limit exceeded | Wait and retry with exponential backoff; consider caching results |
| Empty insurance array | Carrier has no insurance filings on record | This is a critical finding — report as FAIL with no coverage |
| `cancelled_date` in the past but status shows "active" | Data lag in FMCSA reporting | Flag for manual review; FMCSA data can lag 1-2 weeks |
| Pagination incomplete | More records exist beyond current page | Always check for next page indicators and fetch all pages |

When an API call fails, report the HTTP status code and response body. Do not silently skip failed calls — insurance validation requires complete data.

## Resources

- FMCSA Insurance Requirements: 49 CFR Part 387
- FMCSA Minimum Levels of Financial Responsibility: 49 CFR 387.9
- BMC-91X Surety Bond form: FMCSA Form BMC-91X
- SearchCarriers API documentation: https://searchcarriers.com/docs/api and the repository `API-DISCOVERY.md`
- Insurance status codes reference: `{baseDir}/docs/insurance-codes.md`
- FMCSA SAFER System: https://safer.fmcsa.dot.gov
