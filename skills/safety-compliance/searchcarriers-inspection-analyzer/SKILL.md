---
name: searchcarriers-inspection-analyzer
description: Analyzes carrier inspection history for violation trends, OOS rates, and driver-vs-vehicle breakdowns. Use when evaluating inspection patterns.
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

# Inspection Analyzer

Perform deep-dive analysis of a carrier's roadside inspection history —
violation trends, out-of-service rates, driver vs. vehicle breakdowns, and
comparison to national averages. This is where raw FMCSA data becomes
actionable intelligence for brokers, shippers, and safety departments.

## Overview

FMCSA roadside inspections are conducted by state and federal officers at
weigh stations, ports of entry, and roadside locations. Each inspection
record contains 58+ fields covering the inspection itself, violations found,
and out-of-service determinations.

**Inspection Levels** (critical context for interpreting data):

| Level | Name | Scope | Weight |
|---|---|---|---|
| 1 | Full (North American Standard) | Driver credentials + full vehicle mechanical | Most thorough. Highest OOS discovery rate. |
| 2 | Walk-Around | Driver credentials + vehicle exterior/undercarriage | Most common. Good signal for vehicle condition. |
| 3 | Driver-Only | Credentials, logs, medical cert, substance testing | Reveals HOS and driver qualification issues. |
| 4 | Special | One-time examination (e.g., specific recall) | Rare. Low analytical value. |
| 5 | Vehicle-Only | Vehicle without driver present (terminal audit) | Reveals maintenance program quality. |
| 6 | Enhanced NAS for Radioactive Materials | Full + enhanced radiation checks | Very rare. Specialized hazmat carriers. |

**National OOS Rate Benchmarks** (FMCSA annual averages):

| Metric | Approximate Rate |
|---|---|
| Driver OOS rate | ~5.5% |
| Vehicle OOS rate | ~20% |
| Combined OOS rate | ~21% |
| Hazmat OOS rate | ~4% |

A carrier consistently above these benchmarks has a problem. A carrier
consistently below them is performing well — but sample size matters. A
3-truck carrier with 2 inspections is not statistically meaningful.

## Prerequisites

- **Minimum tier**: Pro
- Environment variable `SEARCHCARRIERS_API_KEY` is set with a valid Pro-tier key.
- `curl` and `python3` available in the shell.
- A DOT number for the carrier to analyze.

## Instructions

### 1. Fetch the full inspection history

The inspections endpoint is paginated. Fetch all available pages to build a
complete picture:

```bash
# Page 1
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v1/company/{DOT}/inspections?page=1"
```

Check the response for pagination metadata. Continue fetching until all pages
are retrieved:

```bash
# Subsequent pages
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v1/company/{DOT}/inspections?page=2"
```

For carriers with extensive histories (500+ inspections), fetching all pages
may be necessary for trend analysis but impractical for a quick check. In
those cases, note the total count and focus on the most recent 24 months.

### 2. Parse key fields from each inspection record

Extract these fields from every inspection:

| Field | Use |
|---|---|
| `inspection_id` | Unique identifier, deduplication |
| `dot_number` | Confirms correct carrier |
| `report_state` | Where the inspection occurred — geographic patterns |
| `insp_date` | Date — essential for trending |
| `insp_level_id` | Inspection level (1-6) — determines what was examined |
| `viol_total` | Total violations found |
| `oos_total` | Total out-of-service orders issued |
| `driver_viol_total` | Driver-related violations |
| `vehicle_viol_total` | Vehicle-related violations |
| `hazmat_viol_total` | Hazmat-related violations |
| `violations` | List of individual violations with `part_no` and `violation_description` |
| `per_units` | Power units at time of inspection — fleet size context |

### 3. Calculate core metrics

Use Python for aggregation when the dataset is non-trivial:

```python
import json, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta

# Assume `inspections` is the full list of inspection records
total = len(inspections)
total_violations = sum(i.get("viol_total", 0) for i in inspections)
total_oos = sum(i.get("oos_total", 0) for i in inspections)

# OOS rate
oos_rate = (total_oos / total * 100) if total > 0 else 0

# Driver vs Vehicle breakdown
driver_viols = sum(i.get("driver_viol_total", 0) for i in inspections)
vehicle_viols = sum(i.get("vehicle_viol_total", 0) for i in inspections)
hazmat_viols = sum(i.get("hazmat_viol_total", 0) for i in inspections)

# Driver OOS rate: inspections with driver OOS / total inspections
# (approximate — true calculation uses driver inspections only)
driver_oos = sum(
    1 for i in inspections if i.get("driver_viol_total", 0) > 0 and i.get("oos_total", 0) > 0
)

# Inspection level distribution
level_dist = Counter(i.get("insp_level_id") for i in inspections)
```

**Metrics to report:**

- **Total inspections** (with date range)
- **Overall OOS rate** vs. 21% national average
- **Driver violation count** and estimated driver OOS rate vs. 5.5%
- **Vehicle violation count** and estimated vehicle OOS rate vs. 20%
- **Hazmat violations** (any non-zero count warrants a flag)
- **Average violations per inspection**
- **Clean inspection rate** (inspections with zero violations)

### 4. Analyze violation patterns

Group violations by 49 CFR Part number to identify systemic issues:

```python
part_counter = Counter()
violation_details = defaultdict(list)

for insp in inspections:
    for v in insp.get("violations", []):
        part = v.get("part_no", "Unknown")
        desc = v.get("violation_description", "")
        part_counter[part] += 1
        violation_details[part].append(desc)
```

**Key 49 CFR Parts to flag:**

| Part | Subject | Significance |
|---|---|---|
| 382 | Controlled Substances and Alcohol | Drug/alcohol testing violations — serious |
| 383 | Commercial Driver's License Standards | CDL violations — driver qualification |
| 385 | Safety Fitness Procedures | Safety rating and review process |
| 390 | General Applicability and Definitions | Registration, marking, filing |
| 391 | Qualifications of Drivers | Medical certs, driving records, hiring |
| 392 | Driving of CMVs | Actual driving violations (texting, seatbelt, etc.) |
| 393 | Parts and Accessories | Vehicle equipment (brakes, tires, lights) — most common |
| 395 | Hours of Service | HOS violations — fatigue management |
| 396 | Inspection, Repair, and Maintenance | Maintenance program quality |
| 397 | Transportation of Hazardous Materials | Hazmat handling |

Report the top 5 violation categories with counts and interpret each:
- Part 393 dominance = vehicle maintenance issues (brakes, tires, lights)
- Part 395 dominance = hours-of-service / driver fatigue issues
- Part 391 dominance = driver qualification problems (expired med certs, etc.)
- Parts 382/392 = behavioral and substance issues — most concerning

### 5. Trend over time

Group inspections by quarter or month and plot the trajectory:

```python
from collections import defaultdict

quarterly = defaultdict(lambda: {"count": 0, "violations": 0, "oos": 0})

for insp in inspections:
    date = datetime.strptime(insp["insp_date"], "%Y-%m-%d")
    quarter = f"{date.year}-Q{(date.month - 1) // 3 + 1}"
    quarterly[quarter]["count"] += 1
    quarterly[quarter]["violations"] += insp.get("viol_total", 0)
    quarterly[quarter]["oos"] += insp.get("oos_total", 0)
```

Report the trend direction:
- **Improving**: Violation rate declining over last 4+ quarters. Positive.
- **Stable**: No significant change. Neutral.
- **Deteriorating**: Violation rate increasing. Flag clearly.
- **Insufficient data**: Fewer than 8 inspections total or less than 12
  months of history. State that trend analysis is not statistically reliable.

### 6. Flag serious concerns

Automatically flag these conditions (any one is reportable):

- **Any hazmat violation** (`hazmat_viol_total > 0`) — elevated regulatory
  risk and potential for catastrophic incidents.
- **OOS rate > 30%** — more than 10 points above national average. Indicates
  systemic compliance failures.
- **Driver OOS rate > 10%** — nearly double the national average. Driver
  qualification or management issues.
- **Part 382 violations** — drug and alcohol testing failures. Zero tolerance
  in the industry.
- **Increasing OOS trend** — OOS rate rising over 3+ consecutive quarters.
- **Cluster inspections** — multiple inspections in the same state within a
  short period may indicate targeted enforcement (carrier is on a state's
  radar).
- **Post-crash inspections** — inspections triggered by a crash event carry
  extra weight in the analysis.

### 7. Integrate OOS order history

Fetch formal out-of-service orders (distinct from roadside OOS
determinations):

```bash
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v1/company/{DOT}/out-of-service-orders?page=1"
```

OOS orders are formal federal actions — far more serious than a roadside OOS
on a single vehicle. Any history of OOS orders should be prominently noted.

### 8. Compose the analysis

Structure the output as:

**Inspection Analysis for [Legal Name] (DOT [number])**

1. **Summary Statistics**: Total inspections, date range, OOS rate vs.
   national average. One paragraph.
2. **Driver vs. Vehicle Breakdown**: Which category drives the violations?
   Compare each to benchmarks.
3. **Top Violation Categories**: Top 5 by 49 CFR Part with counts and
   plain-English interpretation.
4. **Trend Direction**: Improving, stable, or deteriorating with supporting
   data points.
5. **Flags and Concerns**: Any serious concerns from Step 6, clearly called
   out.
6. **OOS Order History**: Formal OOS orders, if any.
7. **Analyst Note**: Contextualize the numbers. A 100-truck fleet with 200
   inspections and a 15% OOS rate tells a different story than a 3-truck
   fleet with 4 inspections and 25% OOS (one truck, one bad day).

## Examples

### Example 1: Full inspection analysis

**User prompt**: "Analyze inspections for DOT 12345"

```bash
# Fetch all inspection pages
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v1/company/12345/inspections?page=1"

# Fetch OOS orders
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v1/company/12345/out-of-service-orders?page=1"
```

**Response pattern**: "ABC Trucking (DOT 12345) has 147 inspections over the
past 24 months. Their overall OOS rate is 18%, which is below the 21%
national average. Vehicle violations (Part 393 — brakes and lighting) account
for 62% of all violations. Driver OOS rate is 3.1%, well below the 5.5%
benchmark. The violation trend is stable with no significant change over the
last 4 quarters. No hazmat violations and no formal OOS orders on record.
This carrier's inspection profile is consistent with an adequately managed
fleet."

### Example 2: Carrier with problems

**User prompt**: "What are this carrier's violation trends for DOT 67890?"

**Response pattern**: "XYZ Logistics (DOT 67890) shows a deteriorating
inspection trend. Over 38 inspections in the past 18 months, their OOS rate
is 34% — significantly above the 21% national average. Part 395 (Hours of
Service) violations have increased from 2 per quarter to 7 per quarter over
the last year. They also have 3 Part 382 (controlled substances) violations.
The driver OOS rate is 12%, more than double the 5.5% benchmark. Flags:
elevated OOS rate, increasing HOS violations, substance testing violations.
This carrier's inspection record indicates systemic compliance issues,
particularly around driver management."

### Example 3: OOS rate comparison

**User prompt**: "Show me their OOS rate vs industry average for DOT 11111"

**Response pattern**: Table comparing carrier metrics to national benchmarks,
with a narrative interpretation of where they fall and what it means for risk
assessment.

## Output

Return the requested result with the API route version, relevant carrier identifiers, evidence, missing-data limits, and the next operational action. Never include an API token or an unredacted bulk API response.

## Error Handling

| Scenario | Action |
|---|---|
| `SEARCHCARRIERS_API_KEY` not set | Print: "Set the SEARCHCARRIERS_API_KEY environment variable before running this skill." and stop. |
| API returns 401 | API key is invalid, expired, or not Pro tier. This skill requires a Pro-tier key. |
| API returns 404 or empty results for inspections | Carrier has no inspection history on file. This can happen for very new carriers or non-operational registrations. State this clearly rather than reporting zeros. |
| API returns 429 | Rate limited. Implement exponential backoff. Pro tier has higher limits but large inspection histories may require multiple sequential requests. |
| Fewer than 5 inspections | Warn that the sample size is too small for reliable statistical analysis. Report raw numbers but avoid drawing conclusions about rates or trends. |
| Pagination incomplete | If total count from metadata exceeds fetched records, note that the analysis covers a subset and state the percentage analyzed. |
| Date parsing failures | Some inspection dates may be in unexpected formats. Use lenient parsing and note any records that could not be parsed. |
| `violations` list is empty on a record with `viol_total > 0` | API may return summary counts without detailed violation lists for older records. Note the discrepancy and analyze what is available. |

## Resources

- [FMCSA Inspection Selection System](https://www.fmcsa.dot.gov/safety/inspection-selection-system)
- [49 CFR Parts Index](https://www.ecfr.gov/current/title-49) — full text of all regulations referenced by violation part numbers
- [FMCSA National OOS Rate Data](https://ai.fmcsa.dot.gov/SafetyRating/) — source for benchmark rates
- [CVSA Out-of-Service Criteria](https://www.cvsa.org/inspections/out-of-service-criteria/) — what triggers an OOS determination
- SearchCarriers API documentation: https://searchcarriers.com/docs/api and the repository `API-DISCOVERY.md`
