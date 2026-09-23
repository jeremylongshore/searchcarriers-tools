# Ops Reporter - Architecture

## System Context

Ops Reporter is the **OUTPUT** stage of the SearchCarriers stackable pipeline. It consumes structured data from Carrier Intel and risk assessments from Risk Engine, then produces formatted deliverables: vetting reports, fleet analyses, carrier comparisons, and data exports.

```
                    SEARCHCARRIERS STACKABLE PIPELINE
  =====================================================================

  +-----------------------+     +------------------------+     +-------------------------+
  |   CARRIER INTEL       |     |   RISK ENGINE          |     |   OPS REPORTER          |
  |   (INPUT)             |---->|   (ANALYSIS)           |---->|   (OUTPUT)              |
  |                       |     |                        |     |                         |
  |   carrier_lookup      |     |   risk_score           |     |   generate_report       |
  |   carrier_profile     |     |   vetting_check        |     |   generate_fleet        |
  |   entity_map          |     |   insurance_check      |     |   generate_compare      |
  |   fleet_summary       |     |   compliance_audit     |     |   export_data           |
  |                       |     |                        |     |                         |
  |   Min: Free           |     |   Min: Pro             |     |   Min: Pro              |
  +-----------------------+     +------------------------+     +-------------------------+
         ^                              ^                              ^
         |                              |                              |
  SearchCarriers API v1         Consumes Carrier Intel         Consumes Carrier Intel
  (data source)                 JSON output                    + Risk Engine JSON output
```

**Upstream**: Ops Reporter consumes output from both Carrier Intel and Risk Engine. It is the terminal stage of the pipeline -- nothing downstream consumes its output programmatically. Its output is for humans and external systems (TMS import, email, compliance records).

**Data flow**: Claude orchestrates the pipeline. When a user asks for a vetting report, Claude calls Carrier Intel (data retrieval), then Risk Engine (risk assessment), then Ops Reporter (formatting). Ops Reporter receives pre-computed data as function arguments -- it does not call APIs or compute risk scores.

**Standalone usage**: Ops Reporter can generate output with only Carrier Intel data (no risk scores). In this mode, the risk assessment and recommendation sections display "Risk assessment not available -- run risk_score for a complete report." The tool degrades gracefully rather than failing.

## Component Design

| Component | Location | Responsibility |
|-----------|----------|---------------|
| **MCP Server** | `scripts/ops_reporter_mcp.py` | Registers 4 MCP tools, handles incoming tool calls, delegates to formatting modules, enforces tier gating, returns structured output with meta blocks and disclaimers. Thin I/O shell with no business logic. |
| **Report Generator** | `scripts/report.py` (planned) | Builds the multi-section vetting report. Accepts normalized carrier data and risk assessments, produces Markdown string. Pure function: data in, Markdown out. |
| **Comparison Engine** | `scripts/compare.py` (planned) | Constructs side-by-side comparison tables. Accepts 2-5 carrier data sets, extracts comparison metrics, builds Markdown table with highlight annotations. |
| **Export Formatter** | `scripts/export.py` (planned) | Converts carrier data to JSON, CSV, or Markdown format. Handles field mapping, CSV header generation, and JSON serialization. |
| **Fleet Formatter** | `scripts/fleet.py` (planned) | Builds fleet analysis report from equipment and vehicle data. Computes type breakdowns, make distributions, and age analysis. |
| **Template Helpers** | `scripts/templates.py` (planned) | Shared formatting utilities: table builders, section headers, disclaimer text, metadata blocks, number formatting, date formatting. |
| **Commands** | `commands/` (planned) | Slash command definitions: `/sc-report` for generate_report, `/sc-compare` for generate_compare. |
| **Embedded Skill** | `skills/` (planned) | Teaches Claude when to use each Ops Reporter tool, how to chain the full pipeline, and how to present reports to freight professionals. |

## Data Flow

### Vetting Report Generation

```
User: "Give me a vetting report on DOT 69494"
  |
  v
Claude orchestrates three-stage pipeline:
  |
  +--> Stage 1: Carrier Intel
  |    carrier_profile(dot=69494)
  |    Returns: { carrier: {...}, authorities: [...], insurances: [...] }
  |
  +--> Stage 2: Risk Engine
  |    risk_score(dot=69494, carrier_data={...})
  |    insurance_check(dot=69494, carrier_data={...})
  |    compliance_audit(dot=69494, carrier_data={...})
  |    vetting_check(dot=69494, carrier_data={...})
  |    Returns: { risk_assessment, insurance_assessment, compliance, vetting }
  |
  +--> Stage 3: Ops Reporter
  |    generate_report(
  |      dot_number="69494",
  |      carrier_data={...from Stage 1...},
  |      risk_data={...from Stage 2...}
  |    )
  |
  |    Internal flow:
  |    +--> Tier check: is user's tier >= pro? (yes)
  |    +--> Normalize inputs (handle missing sections)
  |    +--> Build Header section (carrier name, DOT, date)
  |    +--> Build Executive Summary (risk score, verdict, one-liner)
  |    +--> Build Company Overview (identity, contact, fleet size)
  |    +--> Build Safety Record (rating, OOS rates, crash data)
  |    +--> Build Insurance Status (policies, gaps, warnings)
  |    +--> Build Operating Authority (types, status, grant dates)
  |    +--> Build Risk Assessment (composite score, breakdown, flags)
  |    +--> Build Recommendation (verdict, per-rule results)
  |    +--> Append Disclaimer and metadata
  |    +--> Return assembled Markdown report
  |
  v
Claude receives formatted report, presents to user
```

### Carrier Comparison

```
User: "Compare DOT 69494, DOT 3456789, and DOT 27021"
  |
  v
Claude orchestrates data fetching for all carriers:
  |
  +--> For each carrier (parallel where possible):
  |    carrier_profile(dot=N)     [Carrier Intel]
  |    risk_score(dot=N)          [Risk Engine]
  |
  +--> Ops Reporter:
  |    generate_compare(
  |      carriers=[
  |        { dot: "69494", carrier_data: {...}, risk_data: {...} },
  |        { dot: "3456789", carrier_data: {...}, risk_data: {...} },
  |        { dot: "27021", carrier_data: {...}, risk_data: {...} }
  |      ]
  |    )
  |
  |    Internal flow:
  |    +--> Tier check
  |    +--> Validate carrier count (2-5)
  |    +--> Extract comparison metrics from each carrier
  |    +--> Build comparison table (carriers as columns, metrics as rows)
  |    +--> Identify best/worst per metric
  |    +--> Generate summary recommendation
  |    +--> Append disclaimer
  |
  v
User receives: side-by-side comparison table with recommendation
```

### Data Export

```
User: "Export carrier data for DOT 69494 as CSV"
  |
  v
Claude fetches carrier data if not in context:
  |
  +--> carrier_profile(dot=69494)     [Carrier Intel]
  |
  +--> Ops Reporter:
  |    export_data(
  |      dot_number="69494",
  |      carrier_data={...},
  |      format="csv"
  |    )
  |
  |    Internal flow:
  |    +--> Tier check
  |    +--> Select format handler (json | csv | markdown)
  |    +--> For CSV: flatten carrier object, map to standard headers, generate rows
  |    +--> For JSON: serialize carrier data with meta block
  |    +--> For Markdown: delegate to report generator
  |    +--> Return formatted output
  |
  v
User receives: CSV data ready for TMS import or spreadsheet
```

## Report Template System

Ops Reporter uses a Markdown-based template system. Templates are built programmatically -- not stored as static files -- because report content depends on data availability. Each section is a function that accepts data and returns a Markdown string. Missing data produces a "not available" stub rather than an omitted section.

### Vetting Report Template Structure

```markdown
# CARRIER VETTING REPORT: {LEGAL_NAME} (DOT {DOT})
Generated: {TIMESTAMP} | Source: SearchCarriers API

---

## Executive Summary
| Metric | Value |
|--------|-------|
| Risk Score | {SCORE} / 100 ({TIER}) |
| Vetting Verdict | {VERDICT} |
| Insurance Status | {INSURANCE_STATUS} |
| Compliance Posture | {COMPLIANCE_POSTURE} |

**Recommendation:** {ONE_LINE_RECOMMENDATION}

## Company Overview
{company details table}

## Safety Record
{safety metrics table}

## Insurance Status
{insurance policies table}
{findings list}

## Operating Authority
{authority status table}

## Risk Assessment
{composite score breakdown table}
{flags list}

## Qualification
{vetting rules results table}
{failed/review rule details}

---
*{DISCLAIMER}*
*Data source: SearchCarriers API (searchcarriers.com) | Report generated by Ops Reporter v{VERSION}*
```

### Section Independence

Each section is independently renderable. If Risk Engine data is not available, the Risk Assessment and Qualification sections render as:

```markdown
## Risk Assessment
*Risk assessment data not available. Run risk_score for DOT {DOT} to include risk analysis in this report.*

## Qualification
*Vetting check data not available. Run vetting_check for DOT {DOT} to include qualification results in this report.*
```

This design means Ops Reporter never fails due to missing upstream data. It produces the best report it can with the data it has.

## Security Model

**API access:** Ops Reporter reads `SEARCHCARRIERS_API_KEY` at request time and fetches the current carrier sections needed for reports, comparisons, fleet analysis, and export. Calls use the documented v3 company contract plus the retained v1 detail routes described in `API-DISCOVERY.md`. Callers may also supply pre-fetched data where a tool schema permits it.

**No upstream-data storage:** Ops Reporter is stateless. API responses are formatted in memory and returned to the caller. It does not cache or persist licensed SearchCarriers response data. A caller may explicitly save a generated report outside the plugin.

**Disclaimer enforcement:** Every generated report, comparison, and export includes a disclaimer. The disclaimer is appended at the response-building layer, not the presentation layer, so it cannot be accidentally omitted.

**Data classification:** All output is derived from public FMCSA records and computed risk assessments. No PII beyond FMCSA-reported business contact information (phone, address). Reports are informational, not certifications.

**What gets logged:**
- Tool invocations (tool name, DOT numbers, output format)
- Generation latency for performance monitoring
- Error conditions (missing data, tier failures)

**What does NOT get logged:**
- Full report content (stays in context only)
- Carrier data (enters and leaves as function arguments)
- API keys or user credentials

## Error Handling Strategy

| Error | Trigger | Response | Recovery |
|-------|---------|----------|----------|
| No carrier data provided | Tool called without carrier_data or dot_number | "Provide a DOT number or carrier data from carrier_profile" | Claude fetches via Carrier Intel |
| Risk data missing | generate_report called without risk_data | Report generated with "Risk assessment not available" stubs | Informational; suggest running risk_score |
| Tier insufficient | Free/Basic user calls any Ops Reporter tool | Structured tier error with upgrade URL | No retry; show pricing |
| Invalid DOT format | Non-numeric DOT input | "DOT number must be numeric" | User corrects input |
| Too few carriers for comparison | generate_compare with < 2 carriers | "Comparison requires at least 2 carriers" | User adds carriers |
| Too many carriers for comparison | generate_compare with > 5 carriers | "Comparison supports a maximum of 5 carriers" | User reduces selection |
| Invalid export format | export_data with unsupported format | "Supported formats: json, csv, markdown" | User selects valid format |
| Upstream pipeline failure | Carrier Intel or Risk Engine failed | Report includes available data; missing sections noted | Partial report is better than no report |

## Performance Requirements

| Operation | Target Latency | Max Latency | Notes |
|-----------|---------------|-------------|-------|
| `generate_report` (pre-fetched data) | < 100ms | 500ms | Pure formatting, no I/O |
| `generate_report` (needs upstream data) | < 5 seconds | 8 seconds | Carrier Intel + Risk Engine + formatting |
| `generate_fleet` (pre-fetched data) | < 50ms | 200ms | Equipment data formatting |
| `generate_compare` (2 carriers, pre-fetched) | < 100ms | 300ms | Table construction |
| `generate_compare` (5 carriers, needs data) | < 10 seconds | 15 seconds | 5x Carrier Intel + 5x Risk Engine + formatting |
| `export_data` (JSON) | < 20ms | 100ms | Serialization only |
| `export_data` (CSV) | < 30ms | 150ms | Field mapping + serialization |
| `export_data` (Markdown) | < 100ms | 500ms | Delegates to report generator |
| MCP server cold start | < 1 second | 3 seconds | Python import + module load |
| Tier check | < 1ms | N/A | In-memory via shared tier_gate |

Ops Reporter is the fastest stage in the pipeline. All tools with pre-fetched data complete in under 500ms at p99. The formatting operations are string concatenation and table construction -- no computation, no I/O, no external calls. The only scenario where Ops Reporter approaches multi-second latency is when Claude needs to fetch data from Carrier Intel and Risk Engine first.
