---
name: sc-compare
description: Compare multiple carriers side-by-side
allowed-tools: "Bash(python:*),Read"
---

# /sc-compare -- Carrier Comparison

When the user runs `/sc-compare <DOT1> <DOT2> [DOT3] [DOT4] [DOT5]`, fetch data for all
carriers and display a side-by-side comparison highlighting strengths and weaknesses.

## Parse the Input

All arguments must be DOT numbers (7-digit numeric). Minimum 2, maximum 5 carriers.

| Validation | Action |
|-----------|--------|
| Fewer than 2 DOT numbers | "Comparison requires at least 2 DOT numbers. Usage: `/sc-compare DOT1 DOT2 [DOT3] [DOT4] [DOT5]`" |
| More than 5 DOT numbers | "Maximum 5 carriers per comparison. Provide 2-5 DOT numbers." |
| Non-numeric argument | "All arguments must be DOT numbers. Use `/sc-lookup` to resolve names to DOT numbers first." |
| Duplicate DOT numbers | Remove duplicates silently and proceed if 2+ unique remain |

## Fetch Carrier Data

For each DOT number, gather data from all pipeline stages. Process carriers in parallel
where possible to minimize latency.

### Per-Carrier Pipeline

For each carrier:

1. Call `carrier_lookup` with the DOT number to get the base carrier record
2. Call `risk_score` with the DOT number to get the composite risk score and factor breakdown
3. If any call fails for a specific carrier, include that carrier with available data and
   mark missing fields as "N/A"

### Aggregation

Call `generate_compare` with all carrier DOT numbers and gathered data. This produces the
formatted comparison output with rankings.

## Display the Comparison

### Comparison Header

```
CARRIER COMPARISON
Generated: {date}
Carriers:  {count} compared

| DOT       | Legal Name             | City, State     | Status   |
|-----------|------------------------|-----------------|----------|
| {dot1}    | {name1}                | {city1}, {st1}  | {status1}|
| {dot2}    | {name2}                | {city2}, {st2}  | {status2}|
```

### Side-by-Side Comparison Table

Display all key metrics in a comparison grid. Highlight the best and worst value in each row.

```
COMPARISON MATRIX

| Metric              | {name1}      | {name2}      | {name3}      | Best |
|---------------------|--------------|--------------|--------------|------|
| Status              | ACTIVE       | ACTIVE       | INACTIVE     | --   |
| Risk Score          | 18 (LOW)     | 42 (MED)     | 67 (ELEVD)   | #1   |
| Safety Rating       | SATISFACTORY | NOT RATED    | CONDITIONAL  | #1   |
| Power Units         | 42           | 8            | 125          | #3   |
| Drivers             | 55           | 12           | 140          | #3   |
| BIPD Coverage       | $1,000,000   | $750,000     | $1,000,000   | #1,3 |
| Cargo Insurance     | $100,000     | None         | $250,000     | #3   |
| Vehicle OOS Rate    | 15.2%        | 28.1%        | 19.8%        | #1   |
| Driver OOS Rate     | 4.1%         | 8.5%         | 6.2%         | #1   |
| Operating History   | 8 years      | 2 years      | 15 years     | #3   |
| Crashes (2yr)       | 1            | 0            | 4            | #2   |
| Compliance Grade    | A            | B            | C            | #1   |
| Authority           | Common: ACT  | Common: ACT  | Common: INACT| #1,2 |
```

Highlight conventions:

- **Best value**: Mark with the carrier number in the "Best" column
- **Worst value**: Bold the cell value in the table when it represents a critical concern
- **Tied values**: List all tied carrier numbers (e.g., "#1,3")
- **N/A values**: Do not rank carriers with missing data for that metric

### Red Flags by Carrier

For each carrier, list any red flags detected. Group by carrier:

```
RED FLAGS

Carrier #1 (DOT {dot1} -- {name1}):
  (none)

Carrier #2 (DOT {dot2} -- {name2}):
  - [MEDIUM] No cargo insurance on file
  - [MEDIUM] Vehicle OOS rate 28.1% exceeds 25% threshold

Carrier #3 (DOT {dot3} -- {name3}):
  - [CRITICAL] Operating status is INACTIVE
  - [HIGH] Safety rating is CONDITIONAL
  - [HIGH] Authority status is INACTIVE
```

### Ranking Summary

Provide an overall ranking based on composite risk score and red flag count:

```
OVERALL RANKING

| Rank | DOT     | Carrier              | Risk Score | Red Flags | Assessment        |
|------|---------|----------------------|------------|-----------|-------------------|
| 1    | {dot1}  | {name1}              | 18 (LOW)   | 0         | Recommended       |
| 2    | {dot2}  | {name2}              | 42 (MED)   | 2         | Review required   |
| 3    | {dot3}  | {name3}              | 67 (ELEVD) | 3         | Not recommended   |
```

Assessment mapping:

| Condition | Assessment |
|-----------|-----------|
| Risk LOW, 0 critical/high flags | Recommended |
| Risk MEDIUM or 1-2 non-critical flags | Review required |
| Risk ELEVATED+ or any critical flag | Not recommended |

## Follow-Up Actions

After displaying the comparison, offer these next steps:

- **Full report**: "Run `/sc-report {DOT}` for a complete vetting report on any carrier above."
- **Export**: "Run `export_data` to save this comparison as JSON, CSV, or Markdown."
- **Expand comparison**: "Add another carrier: `/sc-compare {DOT1} {DOT2} {DOT_NEW}`"
- **Vetting**: "Run `/sc-vet {DOT}` for formal qualification check on a specific carrier."

## Error Handling

- **Carrier not found**: If a DOT number returns no results, exclude it from the comparison and note: "DOT {dot_number} not found. Comparing remaining {n} carriers."
- **All carriers not found**: "None of the provided DOT numbers returned results. Verify the numbers or use `/sc-lookup` to search."
- **Single carrier remains**: If failures reduce the set to 1 carrier, display that carrier's data as a standalone summary and suggest: "Only one carrier could be retrieved. Run `/sc-report {DOT}` for a full report instead."
- **Risk Engine unavailable**: Compare carriers using Carrier Intel data only. Note that risk scores are unavailable and the ranking is based on carrier data alone.
- **API authentication (401)**: "API authentication failed. Check that SEARCHCARRIERS_API_KEY is set and valid."
- **Tier insufficient (403)**: "Carrier comparison requires a Pro subscription. Upgrade at searchcarriers.com/pricing."
- **API timeout**: Retry the failing carrier once. On second failure, proceed with available carriers.
