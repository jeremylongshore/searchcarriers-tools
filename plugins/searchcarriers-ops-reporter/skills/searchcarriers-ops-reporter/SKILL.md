---
name: searchcarriers-ops-reporter
description: Generate vetting reports, fleet analysis, comparisons, and data exports. Use when producing carrier documentation or formatted output.
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

# Ops Reporter -- Embedded Skill

## Overview

> **API contract:** Use the repository `API-DISCOVERY.md` for the current v3/v2/v1 route map and verified parameter names. Do not infer newer-version routes.

This skill provides the output layer for the searchcarriers Ops Reporter plugin. It teaches you how to consume upstream pipeline data from Carrier Intel (INPUT) and Risk Engine (ANALYSIS), produce formatted reports, comparisons, fleet analyses, and data exports, and maintain output quality standards across all document types.

The Ops Reporter sits at the OUTPUT stage of the searchcarriers pipeline. It receives structured carrier data and scored risk assessments, then transforms them into actionable documents for human decision-makers. Every report this plugin produces must be complete, accurate, and immediately usable for carrier qualification decisions.

## Prerequisites

- **Minimum tier**: Pro
- MCP server `searchcarriers-ops-reporter` must be running and accessible
- `SEARCHCARRIERS_API_KEY` environment variable set with a valid key
- Upstream plugins: `searchcarriers-carrier-intel` and `searchcarriers-risk-engine` should be available for full pipeline execution
- Familiarity with FMCSA terminology (DOT, MC, SCAC, OOS, BIPD, MCS-150)

## Instructions

### Report Types

The Ops Reporter produces four document types through its MCP tools:

**Vetting Report** (`generate_report`)

The primary output document. Combines carrier profile data with risk assessment into a comprehensive vetting report suitable for qualification decisions. Sections include: executive summary, carrier profile, authority and insurance, safety and compliance, risk assessment, red flags, and recommendation.

**Fleet Analysis** (`generate_fleet`)

Equipment-focused report combining fleet_summary data with risk context. Covers: equipment roster, fleet composition analysis (make/model diversity, GVWR distribution, age patterns), consistency checks (reported vs. actual power units), and maintenance risk indicators derived from vehicle OOS rates.

**Carrier Comparison** (`generate_compare`)

Side-by-side comparison of 2-5 carriers across all key metrics. Produces: comparison matrix with best/worst highlighting, per-carrier red flag summary, overall ranking by composite risk score, and assessment recommendation for each carrier.

**Data Export** (`export_data`)

Structured data output in JSON, CSV, or Markdown format. Exports the raw and processed data from any report type for integration with external systems, spreadsheets, or documentation workflows.

### Consuming Upstream Pipeline Data

The Ops Reporter consumes data from two upstream stages. Each stage provides a `_pipeline` envelope.

**From Carrier Intel (INPUT stage)**

The carrier intel pipeline output provides:

```json
{
  "dot_number": 1234567,
  "carrier": {
    "legal_name": "...",
    "status": "ACTIVE",
    "carrier_operation": "A",
    "power_units": 42,
    "drivers": 55,
    "safety_rating": "SATISFACTORY",
    "mcs150_date": "2024-06-15"
  },
  "authorities": [...],
  "insurances": [...],
  "entity_relationships": [],
  "fleet": { "power_units": 42, "vehicles": [] }
}
```

Required keys: `dot_number`, `carrier`. All other keys are optional but their absence creates gaps in the output report. When a key is missing, omit the corresponding report section and note: "Section unavailable -- upstream data not provided."

**From Risk Engine (ANALYSIS stage)**

Each Risk Engine tool response includes a `_pipeline` key:

```json
{
  "_pipeline": {
    "source": "searchcarriers-risk-engine",
    "tool": "risk_score",
    "version": "0.2.0",
    "dot_number": 1234567,
    "timestamp": "2026-02-26T14:30:00Z",
    "tier": "pro",
    "data": {
      "composite_score": 28,
      "level": "MEDIUM",
      "factors": { ... }
    }
  }
}
```

Tool-specific `_pipeline.data` keys consumed by Ops Reporter:

| Source Tool | Key Fields | Used In |
|------------|-----------|---------|
| risk_score | `composite_score`, `level`, `factors` | Vetting report risk section, comparison ranking |
| vetting_check | `verdict`, `disposition`, `rules_evaluated`, `review_items[]`, `fail_items[]` | Vetting report qualification section |
| insurance_check | `status`, `bipd_active`, `bipd_amount`, `cargo_active`, `pending_cancellations[]` | Insurance assessment section |
| compliance_audit | `grade`, `mcs150_current`, `authority_clean`, `issues[]` | Compliance posture section |

Missing `_pipeline` keys cause rendering gaps. When a tool's data is absent, omit the corresponding section and note which upstream tool was not run.

### Report Formatting Guidance

**Structural Standards**

- Every report starts with a header block: report type, generation date, subject carrier, DOT, MC, status, location.
- Executive summary appears immediately after the header. Keep it to 2-3 sentences.
- Use markdown tables for structured data (factor breakdowns, rule results, comparisons).
- Use prose for analysis, synthesis, and recommendations.
- Separate red flags into a distinct section with severity labels.
- End every report with a recommendation and next-step suggestions.

**Data Formatting**

- Dollar amounts: `$1,000,000` (commas, $ prefix, no decimals unless cents matter)
- Percentages: `15.2%` (one decimal place)
- Dates: `YYYY-MM-DD` format consistently
- Risk scores: `28/100 (MEDIUM)` -- always show both the score and the level label
- OOS rates: Always include the national average for context (vehicle ~20%, driver ~5%)

**Comparison Tables**

- Column headers are carrier names or DOT numbers (user preference)
- Best value in each row is marked in the "Best" column
- Critical values are bolded
- N/A values are excluded from ranking for that metric
- Overall ranking uses composite risk score as primary key, red flag count as tiebreaker

**Export Formats**

| Format | Use Case | Structure |
|--------|----------|-----------|
| JSON | System integration, API consumption | Full nested object with all fields |
| CSV | Spreadsheet analysis, bulk processing | Flat rows, one carrier per row, columns for each metric |
| Markdown | Documentation, sharing, archival | Formatted report text identical to display output |

### Output Quality Standards

Every report produced by Ops Reporter must meet these criteria:

1. **Completeness**: All available data sections are present. Missing sections are explicitly noted with the reason.
2. **Accuracy**: All values match upstream data exactly. No rounding errors, no paraphrased statuses. "SATISFACTORY" stays "SATISFACTORY", not "satisfactory" or "Sat".
3. **Currency**: The generation timestamp is included. Data staleness is flagged if MCS-150 is overdue or risk score is from a previous session.
4. **Actionability**: Every report ends with a clear recommendation and concrete next steps. The reader should know what to do after reading the report.
5. **Traceability**: Report sections reference their data source (Carrier Intel, Risk Engine tool name). This allows the reader to re-run specific checks if needed.

### Pipeline Output Contracts

Ops Reporter is the terminal stage, but its outputs include a `_pipeline` key for audit and integration purposes:

```json
{
  "result": { ... },
  "_pipeline": {
    "source": "searchcarriers-ops-reporter",
    "tool": "generate_report",
    "version": "0.2.0",
    "dot_number": 1234567,
    "timestamp": "2026-02-26T15:00:00Z",
    "tier": "pro",
    "data": {
      "report_type": "vetting_report",
      "format": "markdown",
      "sections_rendered": ["header", "executive_summary", "carrier_profile", "authority_insurance", "safety_compliance", "risk_assessment", "red_flags", "recommendation"],
      "sections_omitted": [],
      "upstream_sources": ["carrier_lookup", "carrier_profile", "risk_score"],
      "recommendation": "QUALIFY",
      "red_flag_count": { "critical": 0, "high": 0, "medium": 1 },
      "composite_risk_score": 28,
      "risk_level": "MEDIUM"
    }
  }
}
```

This envelope enables downstream auditing, report archival, and integration with external systems that consume pipeline metadata.

## Examples

### Example 1: Full Vetting Report

User asks: "Generate a vetting report for DOT 1234567"

1. Call `carrier_lookup` with `dot_number: 1234567` to get base carrier data
2. Call `carrier_profile` with `dot_number: 1234567` for authorities and insurance
3. Call `risk_score` with `dot_number: 1234567` for risk assessment
4. Call `generate_report` with the DOT number and all upstream data
5. Display the formatted report with all sections
6. Offer export, comparison, and monitoring as follow-ups

### Example 2: Carrier Comparison

User asks: "Compare DOT 1234567, 2345678, and 3456789"

1. For each DOT, call `carrier_lookup` and `risk_score` in parallel
2. Call `generate_compare` with all three carriers' data
3. Display the comparison matrix with best/worst highlighting
4. Show per-carrier red flags and overall ranking
5. Suggest full reports for specific carriers of interest

### Example 3: Data Export

User asks: "Export the last report as CSV"

1. Retrieve the most recent report data from the session
2. Call `export_data` with format "csv" and the report payload
3. Display the CSV output or write to a file if a path was specified
4. Note the export format and record count

### Example 4: Report Without Risk Data

User asks: "/sc-report 1234567 --no-risk"

1. Call `carrier_lookup` and `carrier_profile` only (skip Risk Engine)
2. Call `generate_report` with carrier data but no risk assessment
3. Display report with risk section omitted
4. Note: "Risk assessment was skipped. Run `/sc-report 1234567` for the full pipeline."

## Output

Return the requested result with the API route version, relevant carrier identifiers, evidence, missing-data limits, and the next operational action. Never include an API token or an unredacted bulk API response.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| MCP tool not available | Server not started or misconfigured | Check `.mcp.json` config and restart the MCP server |
| 401 from API | Invalid or missing API key | Verify `SEARCHCARRIERS_API_KEY` is set and valid |
| 403 tier restriction | User tier below Pro | State: "Report generation requires Pro tier. Upgrade at searchcarriers.com/pricing." |
| 404 carrier not found | DOT number not in FMCSA database | Suggest searching by name via `/sc-lookup` |
| 422 invalid parameters | Wrong parameter types | DOT must be numeric; format must be json/csv/markdown |
| 429 rate limit | Too many requests | Wait for `Retry-After` header duration; cache results |
| Upstream data missing | Carrier Intel or Risk Engine did not return expected keys | Generate report with available sections; note omissions |
| Export format unsupported | User requested a format other than JSON/CSV/Markdown | State supported formats and ask user to choose |
| Report too large | Comparison with 5 carriers produces excessive output | Paginate or summarize; offer full export as alternative |

## Resources

- Plugin configuration: `{baseDir}/.claude-plugin/plugin.json`
- MCP server source: `{baseDir}/scripts/ops_reporter_mcp.py`
- Carrier Intel skill (upstream): `searchcarriers-carrier-intel`
- Risk Engine skill (upstream): `searchcarriers-risk-engine`
- Pipeline architecture: Carrier Intel (INPUT) -> Risk Engine (ANALYSIS) -> Ops Reporter (OUTPUT)
- FMCSA insurance minimums: 49 CFR Part 387
- National OOS benchmarks: vehicle ~20%, driver ~5%
- Export format specs: JSON (RFC 8259), CSV (RFC 4180), Markdown (CommonMark)
