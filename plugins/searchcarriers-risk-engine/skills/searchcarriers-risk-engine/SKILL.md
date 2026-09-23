---
name: searchcarriers-risk-engine
description: Assess carrier risk with scoring, vetting, insurance, and compliance tools. Use when evaluating carrier safety or qualification.
allowed-tools: Read,Grep,Bash(python:*)
metadata:
  tier: pro
version: 0.2.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: Apache-2.0
compatibility: Claude Code or another MCP-capable client; Python 3.10+; network access to searchcarriers.com; an appropriate SearchCarriers API subscription.
tags:
- searchcarriers
- motor-carrier
- plugin
---

# Risk Engine -- Embedded Skill

## Overview

> **API contract:** Use the repository `API-DISCOVERY.md` for the current v3/v2/v1 route map and verified parameter names. Do not infer newer-version routes.

This skill provides the analysis layer for the searchcarriers Risk Engine plugin. It teaches you how to interpret outputs from the four Risk Engine MCP tools (`risk_score`, `vetting_check`, `insurance_check`, `compliance_audit`), apply freight-industry risk context, detect critical patterns, and format results for both human consumption and downstream pipeline stages.

The Risk Engine sits at the ANALYSIS stage of the searchcarriers pipeline. It receives structured carrier data from Carrier Intel (INPUT stage) and produces scored, classified risk assessments that feed into Ops Reporter (OUTPUT stage). Correct interpretation here determines the quality and actionability of all downstream reports.

## Prerequisites

- **Minimum tier**: Pro (vetting_check requires Pro Plus)
- MCP server `searchcarriers-risk-engine` must be running and accessible
- `SEARCHCARRIERS_API_KEY` environment variable set with a valid key
- Upstream data: Carrier Intel plugin should be available for carrier resolution
- Familiarity with FMCSA terminology (DOT, MC, OOS, BIPD, MCS-150)

## Instructions

### Interpreting risk_score Results

The `risk_score` tool returns a composite risk score (0-100) with individual factor breakdowns. The higher the score, the greater the risk.

**Score Ranges**

| Range | Level    | Meaning | Action |
|-------|----------|---------|--------|
| 0-25  | LOW      | Carrier presents minimal risk across all factors | Standard onboarding procedures |
| 26-50 | MEDIUM   | Some risk factors present but within acceptable bounds | Review flagged factors before qualifying |
| 51-75 | ELEVATED | Multiple risk factors or one severe factor detected | Detailed investigation required before qualifying |
| 76-100| HIGH     | Serious risk concerns across multiple dimensions | Do not qualify without executive review and mitigation plan |

**Risk Factor Weights**

The composite score is a weighted sum of individual factor scores. Each factor is scored 0-100 independently, then weighted:

| Factor | Max Penalty | What It Measures |
|--------|-------------|------------------|
| Operating Status | +30 | Not-authorized operating status |
| Safety Rating | +25 | Unsatisfactory (+25), Conditional (+15), Not Rated (+10) |
| OOS Rates | +20 | Vehicle OOS rate vs. 21% national average |
| Crash Rate | +20 | Crashes per power unit (>1.0, >0.5, >0.2 thresholds) |
| Insurance Status | +20 | No active policies or near-cancellation |
| Authority Status | +20 | Revoked or no active authority |
| MCS-150 Age | +10 | >2 years (+5) or >4 years (+10) since filing |

The score is additive: each factor contributes a penalty (0 to its max). The total is capped at 100.

**Interpreting Individual Factors**

- A factor score of 0 means no risk signal detected for that dimension.
- A factor score above 50 means the carrier is below industry benchmarks for that dimension.
- A factor score above 75 indicates a serious deficiency that alone may warrant rejection.
- When the composite is LOW but a single factor is above 50, call attention to the outlier -- the weighted average can mask a concentrated risk.

### Interpreting vetting_check Results

The `vetting_check` tool evaluates a carrier against a set of qualification rules and returns a verdict.

**Verdicts**

| Verdict | Meaning | Recommended Action |
|---------|---------|-------------------|
| PASS    | Carrier meets all qualification thresholds | Proceed with onboarding |
| REVIEW  | Carrier meets mandatory rules but has flagged items near thresholds | Human review required on flagged rules before qualifying |
| FAIL    | Carrier fails one or more mandatory rules | Do not qualify; failing rules must be resolved first |

**Rule Results**

Each rule in the evaluation returns one of:

- **PASS**: Carrier value meets or exceeds the threshold.
- **REVIEW**: Carrier value is within a warning margin of the threshold (typically within 10-20% of the cutoff). Requires human judgment.
- **FAIL**: Carrier value does not meet the mandatory threshold. This is a disqualifying result for mandatory rules.
- **N/A**: Rule could not be evaluated due to missing data or tier restriction. Treat N/A rules as unknowns -- note them in the report and recommend sourcing the missing data.

**Ruleset Selection**

- **Standard**: Industry-consensus thresholds suitable for general freight. Default choice.
- **Strict**: Tighter thresholds for high-value, hazmat, or temperature-sensitive freight.
- **Custom**: User-defined rules for specialized vetting requirements.

When presenting REVIEW results, always state the threshold, the actual value, and how close the carrier is to the cutoff so the reviewer can make an informed decision.

### Interpreting insurance_check Results

The `insurance_check` tool validates a carrier's insurance posture including active policies, coverage adequacy, and gap detection.

**Coverage Statuses**

| Status | Meaning | Severity |
|--------|---------|----------|
| ADEQUATE | All required coverage types are active and meet or exceed federal minimums | None |
| WARNING | Coverage exists but has concerning characteristics (pending cancellation, near-minimum amounts, stale effective dates) | Medium |
| CRITICAL | Required coverage is missing, lapsed, or below federal minimum | Critical |

**Federal BIPD Minimums (49 CFR Part 387)**: General freight $750K, oil (non-bulk) $1M, hazmat (bulk) $5M, passengers $1.5-5M.

**Key Checks**: Compare BIPD against minimums for the carrier's operation type. Check for pending cancellation dates (future `cancelled_date` = imminent lapse). Verify cargo insurance exists (not required but absence is a vetting red flag). Check BMC-84/85 bond ($75K min) if broker authority held. Look for coverage gaps indicating instability.

### Interpreting compliance_audit Results

The `compliance_audit` tool examines a carrier's regulatory compliance posture including MCS-150 filing status, authority standing, and registration completeness.

**Compliance Grades**

| Grade | Meaning | Implication |
|-------|---------|-------------|
| A | Fully compliant across all dimensions | No compliance concerns |
| B | Minor issues detected (stale MCS-150, administrative gaps) | Low risk, recommend correction |
| C | Moderate issues (lapsed filing, authority anomalies) | Investigate before qualifying |
| D | Serious non-compliance (multiple lapses, regulatory actions) | Elevated risk, may affect insurability |
| F | Critical non-compliance (OOS order, revoked authority, no registration) | Cannot legally operate |

**Audit Dimensions**: MCS-150 Currency (biennial filing; >24mo = overdue, >36mo = possibly dormant), Authority Standing (all types should be ACTIVE), Insurance Compliance (cross-references insurance_check), Registration Completeness (required FMCSA fields present).

### Pipeline Integration

Every Risk Engine tool response includes a `_pipeline` key for downstream consumption by Ops Reporter (OUTPUT stage). Envelope structure:

```json
{
  "result": { ... },
  "_pipeline": {
    "source": "searchcarriers-risk-engine",
    "tool": "risk_score",
    "version": "0.2.0",
    "dot_number": 1234567,
    "timestamp": "2026-02-26T14:30:00Z",
    "tier": "pro",
    "data": { ... }
  }
}
```

**Tool-specific `_pipeline.data` keys:**

| Tool | Key Fields |
|------|-----------|
| risk_score | `composite_score` (int), `level` (LOW/MEDIUM/ELEVATED/HIGH), `factors` (object with score + weight per factor) |
| vetting_check | `verdict` (PASS/REVIEW/FAIL), `disposition`, `rules_evaluated`, `passed`, `review`, `failed`, `na`, `review_items[]`, `fail_items[]` |
| insurance_check | `status` (ADEQUATE/WARNING/CRITICAL), `bipd_active`, `bipd_amount`, `bipd_adequate`, `cargo_active`, `cargo_amount`, `bond_required`, `pending_cancellations[]`, `coverage_gaps[]` |
| compliance_audit | `grade` (A-F), `mcs150_current`, `mcs150_age_months`, `authority_clean`, `insurance_compliant`, `registration_complete`, `issues[]` |

The Ops Reporter consumes these `_pipeline.data` objects to generate consolidated reports and dashboards. Missing keys cause downstream rendering gaps -- always include the full envelope.

### Red Flags to Watch For

Apply these checks when interpreting any Risk Engine output. When a flag triggers, include it in a clearly separated warning block.

| Priority | Condition | Flag | Severity |
|----------|-----------|------|----------|
| 1 | Composite risk score >= 76 | High-risk carrier | CRITICAL |
| 2 | Vetting verdict is FAIL | Fails mandatory qualification rules | CRITICAL |
| 3 | Insurance status is CRITICAL | Missing or lapsed required coverage | CRITICAL |
| 4 | Compliance grade is F | Cannot legally operate | CRITICAL |
| 5 | Composite score 51-75 with any single factor >= 75 | Concentrated risk in one dimension | HIGH |
| 6 | Vetting verdict is REVIEW with 3+ review items | Multiple near-threshold concerns compound risk | HIGH |
| 7 | Insurance has pending cancellation within 30 days | Coverage about to lapse | HIGH |
| 8 | Compliance grade is D | Serious regulatory deficiencies | HIGH |
| 9 | Composite score 26-50 with upward trend (if historical data available) | Deteriorating risk profile | MEDIUM |
| 10 | Any vetting rule returns N/A | Incomplete assessment -- unknown risk | MEDIUM |

### Formatting Guidelines

**For human-readable output** (slash commands, chat responses):

- Use markdown tables for structured data (factor breakdowns, rule results)
- Display the risk score prominently with its level label
- Separate red flags into a distinct warning section with severity labels
- Format dollar amounts with commas and $ prefix
- Show dates as YYYY-MM-DD
- Include thresholds alongside actual values so the reader understands context
- Always offer next-step suggestions with specific commands

**For pipeline output** (passing to Ops Reporter):

- Always include the full `_pipeline` envelope in tool responses
- Use the JSON contract structures defined above
- Set missing fields to `null`, not empty strings or zero
- Ensure numeric fields are numbers, not strings
- Include `timestamp` in ISO 8601 format

## Examples

### Example 1: Risk Score Assessment

User asks: "What's the risk score for DOT 1234567?"

1. Call `risk_score` with `dot_number: 1234567`
2. Receive composite score of 28 (MEDIUM)
3. Display score header with visual indicator
4. Show factor breakdown table -- note that OOS Rates factor (45) is the highest contributor
5. Highlight: "OOS rates are the primary risk driver. Vehicle OOS is above the national average."
6. Suggest `/sc-vet 1234567` for formal qualification check

### Example 2: Vetting with Strict Rules

User asks: "Vet DOT 2345678 with strict rules"

1. Call `vetting_check` with `dot_number: 2345678, ruleset: "strict"`
2. Receive verdict: FAIL (cargo insurance required under strict ruleset, none on file)
3. Display verdict header: FAIL
4. Show rule-by-rule table -- rule 10 (Cargo Insurance) shows FAIL with strict threshold
5. Summarize: "Carrier fails strict vetting due to missing cargo insurance. Under standard rules, this would be a REVIEW item."
6. Suggest: "Request certificate of cargo insurance from carrier, then re-evaluate."

### Example 3: Pipeline Handoff to Ops Reporter

After running all four Risk Engine tools, collect each `_pipeline.data` object and assemble into the Ops Reporter input envelope with keys: `dot_number`, `carrier_intel` (from upstream), and `risk_engine` containing sub-keys `risk_score`, `vetting_check`, `insurance_check`, `compliance_audit`. Validate all four are present before passing downstream.

## Output

Return the requested result with the API route version, relevant carrier identifiers, evidence, missing-data limits, and the next operational action. Never include an API token or an unredacted bulk API response.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| MCP tool not available | Server not started or misconfigured | Check `.mcp.json` config and restart the MCP server |
| 401 from API | Invalid or missing API key | Verify `SEARCHCARRIERS_API_KEY` is set and valid |
| 403 tier restriction | User tier below tool minimum (Pro or Pro Plus) | State which tier is required and suggest upgrade path |
| 404 carrier not found | DOT number not in FMCSA database | Suggest searching by name via `/sc-lookup` |
| 422 invalid parameters | Wrong parameter types or format | DOT must be numeric; ruleset must be standard/strict/custom |
| 429 rate limit | Too many requests | Wait for `Retry-After` header duration; cache results |
| Partial scoring | Some risk factors could not be calculated | Display available factors, note gaps, adjust confidence |
| Stale upstream data | Carrier Intel data is outdated | Recommend refreshing carrier profile before re-scoring |
| Custom rules parse failure | Malformed custom rules JSON | Validate rule structure: field, operator, value, mandatory |

## Resources

- Plugin configuration: `{baseDir}/.claude-plugin/plugin.json`
- MCP server source: `{baseDir}/scripts/risk_engine_mcp.py`
- Carrier Intel skill (upstream): `searchcarriers-carrier-intel`
- Ops Reporter skill (downstream): `searchcarriers-ops-reporter`
- FMCSA insurance minimums: 49 CFR Part 387
- National OOS benchmarks: vehicle ~20%, driver ~5%
- Pipeline architecture: Carrier Intel (INPUT) -> Risk Engine (ANALYSIS) -> Ops Reporter (OUTPUT)
