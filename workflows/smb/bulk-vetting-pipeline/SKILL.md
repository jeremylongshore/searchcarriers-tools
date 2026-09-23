---
name: searchcarriers-bulk-vetting-pipeline
description: Upload a list of carriers, run full vetting on each, and produce a consolidated report with pass/fail results. Use when vetting in bulk.
allowed-tools: Read,Grep,Bash(python:*)
metadata:
  tier: smb
version: 0.2.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: Apache-2.0
compatibility: Claude Code or another MCP-capable client; Python 3.10+; network access to searchcarriers.com; an appropriate SearchCarriers API subscription.
tags:
- searchcarriers
- motor-carrier
- workflow
---

# Bulk Vetting Pipeline -- Workflow Skill

## Overview

> **API contract:** Use the repository `API-DISCOVERY.md` for the current v3/v2/v1 route map and verified parameter names. Do not infer newer-version routes.

This workflow orchestrates a cross-plugin pipeline that takes a list of carrier DOT numbers (up to 100), runs each through the full vetting pipeline, and produces a consolidated pass/fail report with a CSV export. It coordinates three plugins in sequence: API Bridge (bulk ingestion), Risk Engine (scoring and vetting), and Ops Reporter (report generation and export).

The pipeline follows this execution path:

```
bulk_lookup (API Bridge)
    |
    v
[For each carrier returned]
    |-- risk_score (Risk Engine)
    |-- vetting_check (Risk Engine)
    |
    v
generate_report (Ops Reporter) -- for failures only
    |
    v
export_data (Ops Reporter) -- CSV summary of all carriers
    |
    v
Consolidated report with pass/fail per carrier
```

This workflow eliminates the manual effort of running individual lookups, scoring, and vetting across dozens of carriers. A 100-carrier batch that would take hours manually completes in under 10 minutes.

## Prerequisites

- **Minimum tier**: SMB (bulk_lookup requires SMB; vetting_check requires Pro Plus)
- `SEARCHCARRIERS_API_KEY` environment variable set with a valid Bearer token
- MCP servers running: `searchcarriers-api-bridge`, `searchcarriers-risk-engine`, `searchcarriers-ops-reporter`
- API base URL: `https://searchcarriers.com/api/v1`
- Authentication format: `Authorization: Bearer {id}|{token}` (Laravel Sanctum)
- Input: A list of DOT numbers (inline, from file, or from a previous result set)

## Instructions

### Stage 1: Input Validation and Bulk Lookup

Accept DOT numbers from one of three sources:

| Source | Format | Example |
|--------|--------|---------|
| Inline list | Comma or newline separated | `1234567, 2345678, 3456789` |
| File | CSV or text file with one DOT per line | `/path/to/dots.csv` |
| Previous results | DOT numbers extracted from a prior search | Output of `/sc-lookup` |

**Validation rules:**

1. Strip whitespace and non-numeric characters from each entry.
2. Reject entries that are not 1-8 digit numbers.
3. Deduplicate the list -- report duplicates removed.
4. Enforce the 100-carrier maximum. If the list exceeds 100, reject with: "Batch limited to 100 carriers. Split into multiple batches."
5. Report the validated count before proceeding.

**Execute bulk lookup:**

Call `bulk_lookup` from the API Bridge plugin with the validated DOT list. This performs rate-limited lookups (max 3 requests/second) against the SearchCarriers API.

Collect results into three categories:

| Category | Condition | Action |
|----------|-----------|--------|
| Found | API returned carrier data | Proceed to Stage 2 |
| Not found | API returned 404 for DOT | Log as NOT_FOUND in final report |
| Error | API returned 5xx or timeout | Log as ERROR in final report |

### Stage 2: Risk Scoring

For each carrier in the "found" category, call `risk_score` from the Risk Engine plugin.

**Rate management:** Process carriers sequentially to respect API rate limits. The risk_score tool makes multiple API calls per carrier (base search + authorities + insurances + inspections), so expect approximately 4-6 API calls per carrier.

**Collect per-carrier results:**

| Field | Source | Purpose |
|-------|--------|---------|
| `composite_score` | risk_score `_pipeline.data` | Primary risk metric |
| `level` | risk_score `_pipeline.data` | LOW / MEDIUM / ELEVATED / HIGH |
| `factors` | risk_score `_pipeline.data` | Individual factor breakdown |

Track scoring failures separately. If `risk_score` fails for a carrier (missing data, API error), mark that carrier as SCORE_FAILED and continue with the remaining carriers.

### Stage 3: Vetting Check

For each carrier that received a risk score, call `vetting_check` from the Risk Engine plugin.

**Ruleset selection:**

| Scenario | Ruleset | Rationale |
|----------|---------|-----------|
| General freight vetting | `standard` | Industry-consensus thresholds |
| High-value or hazmat freight | `strict` | Tighter thresholds for elevated liability |
| User-specified custom rules | `custom` | User provides rule definitions |

Default to `standard` unless the user specifies otherwise.

**Collect per-carrier results:**

| Field | Source | Purpose |
|-------|--------|---------|
| `verdict` | vetting_check `_pipeline.data` | PASS / REVIEW / FAIL |
| `disposition` | vetting_check `_pipeline.data` | Human-readable summary |
| `fail_items[]` | vetting_check `_pipeline.data` | Rules that caused FAIL |
| `review_items[]` | vetting_check `_pipeline.data` | Rules flagged for REVIEW |

### Stage 4: Failure Report Generation

For each carrier with a verdict of FAIL, call `generate_report` from the Ops Reporter plugin to produce a detailed vetting report. These individual reports document why the carrier failed and provide evidence for the decision.

**Skip report generation for:**

- Carriers with PASS verdict (no report needed).
- Carriers with REVIEW verdict (include in summary but no full report unless user requests it).
- Carriers that were NOT_FOUND, ERROR, or SCORE_FAILED (no data to report on).

### Stage 5: CSV Export

Call `export_data` from the Ops Reporter plugin with format `csv` to produce a flat summary of all carriers in the batch.

**CSV columns:**

| Column | Source | Notes |
|--------|--------|-------|
| DOT | Input list | Original DOT number |
| Legal Name | bulk_lookup result | Carrier legal name |
| Status | bulk_lookup result | ACTIVE / INACTIVE |
| State | bulk_lookup result | 2-letter state code |
| Power Units | bulk_lookup result | Fleet size |
| Risk Score | risk_score result | 0-100 composite |
| Risk Level | risk_score result | LOW / MEDIUM / ELEVATED / HIGH |
| Verdict | vetting_check result | PASS / REVIEW / FAIL |
| Fail Reasons | vetting_check result | Semicolon-separated list of failing rules |
| Disposition | vetting_check result | Summary text |
| Result | Pipeline status | PASS / REVIEW / FAIL / NOT_FOUND / ERROR / SCORE_FAILED |

### Stage 6: Consolidated Report

Assemble the final consolidated report combining all stages into a single output.

**Report structure:**

1. **Header**: Batch ID, date, total carriers submitted, ruleset used.
2. **Summary metrics**: Total processed, pass count, review count, fail count, not found, errors.
3. **Pass/fail table**: Every carrier in a single table with DOT, name, risk score, verdict, and top flag.
4. **Failure detail section**: For each FAIL carrier, include the disposition and failing rules.
5. **Review detail section**: For each REVIEW carrier, include the review items and how close each is to the threshold.
6. **Export link**: Reference to the CSV file produced in Stage 5.

**Summary metric calculations:**

| Metric | Calculation |
|--------|-------------|
| Pass rate | `PASS count / total found * 100` |
| Fail rate | `FAIL count / total found * 100` |
| Average risk score | Mean of all composite scores |
| Highest risk | Carrier with the highest composite score |
| Most common fail reason | Mode of all fail_items across failed carriers |

## Examples

### Example 1: Standard Bulk Vetting

User provides: "Vet these 25 DOTs: 1234567, 2345678, ..." (inline list)

1. Validate and deduplicate: 25 unique DOTs confirmed.
2. `bulk_lookup` retrieves 23 found, 1 not found, 1 error.
3. `risk_score` for 23 carriers: all succeed, scores range 12-67.
4. `vetting_check` with standard rules: 18 PASS, 3 REVIEW, 2 FAIL.
5. `generate_report` for the 2 FAIL carriers.
6. `export_data` produces CSV with all 25 rows.
7. Consolidated report: "25 submitted. 23 found. 18 pass (78%), 3 review (13%), 2 fail (9%). 1 not found, 1 API error. Average risk: 31/100. CSV exported."

### Example 2: Strict Rules for Hazmat Carriers

User provides: "Vet these DOTs with strict rules" plus a file path.

1. Parse DOTs from file: 50 unique DOTs.
2. `bulk_lookup` retrieves 48 found.
3. `risk_score` for 48 carriers.
4. `vetting_check` with `strict` ruleset: 30 PASS, 10 REVIEW, 8 FAIL.
5. `generate_report` for the 8 FAIL carriers.
6. `export_data` produces CSV.
7. Consolidated report notes strict ruleset applied. Higher fail rate expected with strict thresholds.

### Example 3: Re-vetting After Failures

User asks: "Re-vet the 3 carriers that failed last batch."

1. Extract the 3 FAIL DOTs from the previous batch results.
2. Run the full pipeline on just those 3 carriers.
3. If any now PASS (data corrected, insurance updated), report the change.
4. If still failing, confirm the same or different rules are triggering.

## Output

Return the requested result with the API route version, relevant carrier identifiers, evidence, missing-data limits, and the next operational action. Never include an API token or an unredacted bulk API response.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Batch exceeds 100 carriers | Input list too large | Split into batches of 100 or fewer |
| bulk_lookup partial failure | Some DOTs return errors while others succeed | Continue pipeline with successful lookups; report failures in final summary |
| risk_score timeout | API latency or carrier data complexity | Retry once after 5 seconds; if persistent, mark carrier as SCORE_FAILED |
| vetting_check 403 | User tier below Pro Plus | State: "Vetting check requires Pro Plus. Bulk lookup and risk scoring completed -- upgrade to add vetting." |
| generate_report failure | Ops Reporter MCP not available | Skip individual reports; still produce CSV summary and consolidated table |
| export_data format error | Invalid format parameter | Default to CSV; report the format constraint |
| All carriers NOT_FOUND | Invalid DOT list or stale data | Verify DOT numbers are valid 1-8 digit FMCSA identifiers |
| API rate limit (429) | Batch processing exceeded rate limit | Pause for `Retry-After` duration; reduce processing concurrency |
| MCP server unavailable | One of the three required MCP servers is not running | Report which server is down and which pipeline stages are affected |

## Resources

- API Bridge plugin tools: `bulk_lookup`, `api_health` -- `{baseDir}/plugins/searchcarriers-api-bridge/SCHEMA.md`
- Risk Engine plugin tools: `risk_score`, `vetting_check` -- `{baseDir}/plugins/searchcarriers-risk-engine/SCHEMA.md`
- Ops Reporter plugin tools: `generate_report`, `export_data` -- `{baseDir}/plugins/searchcarriers-ops-reporter/SCHEMA.md`
- Rate limit guidance: max 3 req/sec, 5-min cache TTL
- Pipeline architecture: API Bridge (INTEGRATION) -> Risk Engine (ANALYSIS) -> Ops Reporter (OUTPUT)
- Vetting rulesets: standard, strict, custom -- see Risk Engine SKILL.md for rule definitions
- CSV export spec: RFC 4180
- SearchCarriers API base: `https://searchcarriers.com/api/v1`
- FMCSA insurance minimums: 49 CFR Part 387
