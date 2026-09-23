# /sc-vet -- Carrier Vetting Check

When the user runs `/sc-vet [DOT]` or `/sc-vet [DOT] --rules [ruleset]`, run the carrier
through qualification rules and display a detailed pass/review/fail verdict.

## Parse the Input

The first argument must be a DOT number (7-digit numeric). If the user passes an MC number
or name instead, tell them to run `/sc-lookup` first to resolve the DOT number.

Optional flags:

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `--rules` | `standard`, `strict`, `custom` | `standard` | Qualification ruleset to apply |
| `--format` | `full`, `summary` | `full` | Output detail level |

If `--rules custom` is specified, the user must also provide a rules definition (see
Custom Rules section below).

## Execute the Vetting

Call the `vetting_check` MCP tool with the DOT number and the selected ruleset.

This returns a verdict (PASS, REVIEW, or FAIL), individual rule results, and an
overall qualification summary.

## Display Results

### Verdict Header

Display the overall verdict prominently:

```
CARRIER VETTING REPORT -- DOT {dot_number}
Carrier:    {legal_name}
Ruleset:    {ruleset_name}
Evaluated:  {timestamp}

 VERDICT:  [PASS]    Carrier meets all qualification criteria.
 VERDICT:  [REVIEW]  Carrier requires manual review on {n} rule(s).
 VERDICT:  [FAIL]    Carrier fails {n} mandatory rule(s). Do not qualify.
```

### Rule-by-Rule Results

Show every rule evaluated with its result:

```
QUALIFICATION RULES

| #  | Rule                      | Result | Threshold        | Actual           | Notes                  |
|----|---------------------------|--------|------------------|------------------|------------------------|
| 1  | Active Operating Status   | PASS   | Status = ACTIVE  | ACTIVE           |                        |
| 2  | Active BIPD Insurance     | PASS   | Coverage >= $750K| $1,000,000       | Above minimum          |
| 3  | Safety Rating             | PASS   | Not UNSATISFACTORY| SATISFACTORY    |                        |
| 4  | Authority Status          | PASS   | At least 1 active| Common: ACTIVE   |                        |
| 5  | Vehicle OOS Rate          | REVIEW | <= 25%           | 23.8%            | Near threshold         |
| 6  | Driver OOS Rate           | PASS   | <= 10%           | 4.1%             |                        |
| 7  | MCS-150 Currency          | PASS   | Filed < 2 years  | 2024-12-10       | 14 months ago          |
| 8  | Operating History         | PASS   | >= 12 months     | 36 months        |                        |
| 9  | Crash Record              | PASS   | 0 fatal (2yr)    | 0 fatal          |                        |
| 10 | Cargo Insurance           | REVIEW | Coverage > $0    | None on file     | Not required but flagged|
| 11 | Entity Network Clean      | N/A    | No flagged rels  | Not evaluated    | Requires entity_map    |
```

Result codes:

| Result  | Meaning |
|---------|---------|
| PASS    | Carrier meets or exceeds the threshold for this rule |
| REVIEW  | Carrier is near the threshold or data is ambiguous -- requires human judgment |
| FAIL    | Carrier does not meet the mandatory threshold -- disqualifying |
| N/A     | Rule could not be evaluated (missing data or tier restriction) |

### Verdict Summary

After the rule table, summarize the disposition:

```
SUMMARY
  Total rules evaluated:  11
  Passed:                 8
  Review required:        2
  Failed:                 0
  Not evaluated:          1

  Disposition: QUALIFIED WITH REVIEW
  Review items: Vehicle OOS rate near threshold, No cargo insurance on file
```

Disposition mapping:

| Condition | Disposition |
|-----------|------------|
| All PASS, no FAIL, no REVIEW | QUALIFIED |
| No FAIL, 1+ REVIEW | QUALIFIED WITH REVIEW |
| 1+ FAIL | NOT QUALIFIED |

## Standard vs Strict Rulesets

**Standard** (default): Industry-standard qualification thresholds used by most brokers.
Matches the rule table shown above.

**Strict**: Tighter thresholds for high-value or sensitive freight:

| Rule | Standard Threshold | Strict Threshold |
|------|-------------------|------------------|
| BIPD Coverage | >= $750K | >= $1M |
| Vehicle OOS | <= 25% | <= 15% |
| Driver OOS | <= 10% | <= 5% |
| Operating History | >= 12 months | >= 24 months |
| Cargo Insurance | Flagged if absent | Required (FAIL if absent) |
| Crash Record | 0 fatal (2yr) | 0 fatal + 0 injury (2yr) |

## Custom Rules

When `--rules custom` is used, the user provides a JSON or natural-language rules definition.
Parse it into the rule evaluation format and pass it to the `vetting_check` tool as the
`custom_rules` parameter.

Example custom rule input:

```json
{
  "rules": [
    {"field": "power_units", "operator": "gte", "value": 10, "mandatory": true},
    {"field": "safety_rating", "operator": "eq", "value": "SATISFACTORY", "mandatory": true},
    {"field": "bipd_coverage", "operator": "gte", "value": 2000000, "mandatory": true}
  ]
}
```

If the user describes rules in natural language, translate them into the structured format
before calling the tool.

## Follow-Up Actions

After displaying the vetting report, offer these next steps based on the verdict:

- **PASS**: "Carrier is qualified. Proceed with onboarding or run `/sc-analyze {DOT}` for the full risk analyst report."
- **REVIEW**: "Review items flagged above. Run `insurance_check` or `compliance_audit` for deeper analysis on specific concerns."
- **FAIL**: "Carrier does not meet qualification criteria. Failing rules must be resolved before qualification. Run `/sc-risk {DOT}` to see the full risk score breakdown."

## Error Handling

- **Carrier not found (404)**: "No carrier found with DOT {dot_number}. Verify the number or use `/sc-lookup` to search."
- **Tier insufficient (403)**: "Carrier vetting requires a Pro Plus subscription. Current tier does not include `vetting_check`. Upgrade at searchcarriers.com/pricing."
- **Invalid custom rules**: "Could not parse custom rules. Provide rules as a JSON array or describe each rule with a field, operator, and threshold value."
- **API timeout**: Retry once. On second failure: "Vetting check timed out for DOT {dot_number}. Try again shortly."
- **API authentication (401)**: "API authentication failed. Check that SEARCHCARRIERS_API_KEY is set and valid."
- **Partial evaluation**: If some rules return N/A due to missing data, display available results and note which rules could not be evaluated. The verdict should reflect only evaluated rules, with a caveat about incomplete assessment.
