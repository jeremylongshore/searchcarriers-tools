---
name: sc-report
description: Generate a comprehensive carrier vetting report
allowed-tools: "Bash(python:*),Read"
---

# /sc-report -- Carrier Vetting Report

When the user runs `/sc-report <DOT_NUMBER> [--no-risk] [--format text|markdown]`, generate
a comprehensive carrier vetting report by orchestrating the full pipeline.

## Parse the Input

The first argument must be a DOT number (7-digit numeric). If the user passes an MC number
or name instead, tell them to run `/sc-lookup` first to resolve the DOT number.

Optional flags:

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `--no-risk` | (none) | false | Skip Risk Engine stage; report carrier data only |
| `--format` | `text`, `markdown` | `markdown` | Output format for the report |

## Execute the Pipeline

Run the full pipeline to gather data before generating the report. Each stage feeds the next.

### Stage 1: Carrier Intel (INPUT)

Call `carrier_lookup` with the DOT number to retrieve the base carrier record. Then call
`carrier_profile` to get the combined record (authorities, insurance, base data).

If carrier_lookup returns no results, stop and report: "No carrier found with DOT {dot_number}.
Verify the number or use `/sc-lookup` to search."

### Stage 2: Risk Engine (ANALYSIS)

Unless `--no-risk` is set, call `risk_score` with the DOT number to retrieve the composite
risk score and factor breakdown. This provides the risk assessment section of the report.

If the risk_score call fails due to tier restriction, note this in the report and continue
with carrier data only. Do not abort the report.

### Stage 3: Ops Reporter (OUTPUT)

Call `generate_report` with the DOT number and all upstream data. This produces the formatted
vetting report with all sections assembled.

## Display the Report

Present the complete vetting report with these sections:

```
CARRIER VETTING REPORT
Generated: {date}
Format:    {format}

Subject:   {legal_name}
DOT:       {dot_number}    MC: {mc_number}
Status:    {status}         Location: {city}, {state}
```

### Executive Summary

2-3 sentences capturing the carrier's overall profile and risk posture. Lead with the
qualification assessment: is this carrier suitable for onboarding?

### Carrier Profile

Identity, contact, fleet size, operation type, and registration details from Carrier Intel.

### Authority & Insurance

Authority types and statuses, insurance coverage with amounts and adequacy assessment.

### Safety & Compliance

Safety rating, OOS rates vs. national averages, crash history, and MCS-150 currency.

### Risk Assessment

Composite risk score with level, factor breakdown table, and critical alerts. Omit this
section entirely if `--no-risk` was specified.

### Red Flags & Concerns

Consolidated list of all identified issues with severity labels (CRITICAL, HIGH, MEDIUM).

### Recommendation

Clear QUALIFY, INVESTIGATE, or REJECT recommendation based on all findings.
If `--no-risk` was used, note that the recommendation is based on carrier data only and
suggest running the full pipeline for a complete assessment.

## Follow-Up Actions

After displaying the report, offer these next steps:

- **Export**: "Run `export_data` to save this report as JSON, CSV, or Markdown."
- **Compare**: "Run `/sc-compare {DOT} {DOT2}` to compare against another carrier."
- **Monitor**: "Set up Carrier Watch for ongoing alerts on this carrier."
- **Deep dive**: "Run `/sc-vet {DOT}` for rule-by-rule qualification check."

## Error Handling

- **Carrier not found (404)**: "No carrier found with DOT {dot_number}. Verify the number or use `/sc-lookup` to search."
- **API authentication (401)**: "API authentication failed. Check that SEARCHCARRIERS_API_KEY is set and valid."
- **Tier insufficient (403)**: "Report generation requires a Pro subscription. Upgrade at searchcarriers.com/pricing."
- **Risk Engine unavailable**: Generate the report without risk data. Note the omission and suggest retrying.
- **Partial upstream data**: Generate the report with available sections. Note which sections could not be populated and why.
- **API timeout**: Retry the failing stage once. On second failure, report which stage timed out and generate with available data.
