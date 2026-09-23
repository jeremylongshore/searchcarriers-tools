# Ops Reporter - Product Requirements

## Goals

1. **Generate professional vetting reports in under 5 seconds.** Given carrier data from Carrier Intel and risk assessments from Risk Engine, produce a formatted, multi-section vetting report that a compliance manager can send to her operations team without editing. The report includes company overview, safety record, insurance status, authority history, risk assessment, and a qualification recommendation.
2. **Enable side-by-side carrier comparison for load tendering.** Given 2 to 5 carriers, produce a comparison table that lets a broker evaluate carriers across safety, insurance, compliance, and operational metrics on one screen. No spreadsheet assembly required.
3. **Export carrier data in machine-readable formats.** Output structured carrier data as JSON (for developer integrations), CSV (for TMS import and spreadsheet analysis), or Markdown (for documentation and sharing). Same data, multiple consumption patterns.
4. **Produce fleet analysis reports for equipment verification.** Generate a fleet composition report with equipment roster, vehicle type breakdown, make/model distribution, and fleet-to-driver ratios so operations teams can verify a carrier has the right equipment before tendering.

## Non-Goals

1. **NOT a document management system.** Ops Reporter generates reports. It does not store, version, organize, or search past reports. Report persistence is the user's responsibility -- save the output wherever your organization keeps compliance records.
2. **NOT a printing or PDF service.** Reports are generated in Markdown format. If you need PDF, use a Markdown-to-PDF tool like pandoc. Ops Reporter does not manage print layouts, page breaks, or branded templates.
3. **NOT a CRM or carrier management platform.** Ops Reporter does not track carrier relationships, communication history, or load assignment records. It produces point-in-time reports from live data.
4. **NOT a data retrieval tool.** Ops Reporter does not call the SearchCarriers API directly for carrier data. It consumes structured output from Carrier Intel and Risk Engine. If data is not already in the model client's context, the MCP client orchestrates the upstream lookups automatically.
5. **NOT a notification or alerting system.** Ops Reporter does not monitor carriers or send alerts when conditions change. It generates reports on demand.

## User Stories

### US-01: Compliance Manager Generates Vetting Report

As a **compliance manager**, I want to **generate a complete carrier vetting report from a single command**, so that **I can send a professional, standardized document to my operations team instead of spending 30 minutes assembling one by hand**.

**Acceptance Criteria:**
- Report generated from a DOT number (the MCP client handles upstream data fetching)
- Report includes all standard sections: company overview, safety, insurance, authority, risk assessment, recommendation
- Risk scores and vetting verdicts from Risk Engine are embedded in the report
- Report includes a generated timestamp and data source attribution
- Report includes an advisory disclaimer
- Report is formatted in clean Markdown with consistent headers, tables, and section breaks

### US-02: Broker Compares Carriers for Load Tendering

As a **freight broker**, I want to **compare 2 to 5 carriers side-by-side on key metrics**, so that **I can make a load tendering decision based on objective data instead of gut feel or whoever answers the phone first**.

**Acceptance Criteria:**
- Accepts 2 to 5 DOT numbers (or carrier names that the MCP client resolves to DOTs)
- Produces a comparison table with columns for each carrier and rows for key metrics
- Metrics include: safety rating, risk score, vehicle OOS rate, driver OOS rate, insurance coverage (BIPD, cargo), authority age, power units, driver count
- Highlights the best and worst value in each metric row
- Includes a summary recommendation identifying the lowest-risk carrier
- Rejects requests for more than 5 carriers with a clear explanation

### US-03: Operations Team Exports Data for TMS Import

As an **operations coordinator**, I want to **export a carrier's profile data in CSV format**, so that **I can import it into our TMS without re-keying 20 fields by hand**.

**Acceptance Criteria:**
- Exports in JSON, CSV, or Markdown format based on user request
- CSV output uses standard headers that map to common TMS fields (DOT, MC, legal name, status, power units, drivers, etc.)
- JSON output is valid, parseable, and includes all carrier fields
- Markdown output is the same as the vetting report format
- Export includes data timestamp and source attribution

### US-04: Fleet Verification Report

As a **load planner**, I want to **see a carrier's fleet composition report**, so that **I can verify they have the right equipment type (reefer, flatbed, dry van) before I tender a specialized load**.

**Acceptance Criteria:**
- Report shows equipment breakdown by type with counts and percentages
- Includes top makes and model distribution
- Shows fleet age distribution (year ranges)
- Includes power unit to driver ratio
- Flags any notable fleet characteristics (e.g., "100% reefer fleet" or "no trailers on file")

## Functional Requirements

### FR-01: Vetting Report Generation

**Description:** The `generate_report` tool produces a formatted Markdown vetting report from carrier data and risk assessments. It consumes output from Carrier Intel (`carrier_profile`) and Risk Engine (`risk_score`, `insurance_check`, `compliance_audit`, `vetting_check`).

**Report Sections:**

| Section | Source Data | Content |
|---------|------------|---------|
| Header | carrier_profile | Carrier name, DOT, MC, report date |
| Executive Summary | risk_score, vetting_check | Risk score, risk tier, vetting verdict, one-line recommendation |
| Company Overview | carrier_profile | Legal name, DBA, entity type, status, location, contact, DUNS |
| Safety Record | carrier_profile | Safety rating, rating date, vehicle OOS rate, driver OOS rate, crash indicator |
| Insurance Status | insurance_check | Policy types, coverage amounts, status, expiration, gap findings |
| Operating Authority | carrier_profile, compliance_audit | Authority types, status, grant dates, compliance posture |
| Risk Assessment | risk_score | Composite score, dimension breakdown, flags, confidence level |
| Recommendation | vetting_check | Verdict (PASS/REVIEW/FAIL), per-rule results, failed rule details |
| Disclaimer | (static) | Advisory language, data source attribution, timestamp |

**Priority:** P0

### FR-02: Fleet Analysis Report

**Description:** The `generate_fleet` tool produces a formatted fleet analysis report from Carrier Intel's `fleet_summary` data. Includes equipment roster, type breakdown, make/model distribution, and fleet age analysis.

**Report Sections:**

| Section | Content |
|---------|---------|
| Fleet Overview | Power units, drivers, driver-to-unit ratio |
| Equipment Breakdown | Table: equipment type, count, percentage of fleet |
| Top Makes | Table: manufacturer, unit count |
| Fleet Age | Table: year range, count, percentage |
| Notable Characteristics | Auto-detected flags (e.g., specialized fleet, aging equipment) |

**Priority:** P1

### FR-03: Carrier Comparison Table

**Description:** The `generate_compare` tool produces a side-by-side comparison of 2 to 5 carriers. Each carrier occupies a column; each metric occupies a row.

**Comparison Metrics:**

| Metric | Source |
|--------|--------|
| Legal Name | carrier_profile |
| DOT / MC | carrier_profile |
| Status | carrier_profile |
| Safety Rating | carrier_profile |
| Risk Score (0-100) | risk_score |
| Risk Tier | risk_score |
| Vehicle OOS Rate | carrier_profile |
| Driver OOS Rate | carrier_profile |
| BIPD Coverage | insurance_check |
| Cargo Coverage | insurance_check |
| Authority Age | carrier_profile |
| Power Units | carrier_profile |
| Total Drivers | carrier_profile |
| Vetting Verdict | vetting_check |

**Priority:** P1

### FR-04: Multi-Format Data Export

**Description:** The `export_data` tool outputs carrier data in the requested format. Supports JSON, CSV, and Markdown.

**Format Specifications:**

| Format | Use Case | Structure |
|--------|----------|-----------|
| JSON | API integration, developer workflows | Full carrier object with meta block, authorities, insurances |
| CSV | TMS import, spreadsheet analysis | Flat row with standard headers: DOT, MC, legal_name, status, safety_rating, power_units, drivers, bipd_coverage, cargo_coverage, authority_status |
| Markdown | Documentation, email, sharing | Same as vetting report format from `generate_report` |

**Priority:** P1

### FR-05: Tier Gating

**Description:** All four tools require Pro tier. Free and Basic users receive a structured error with upgrade URL.

| Tool | Min Tier | Gate Behavior |
|------|----------|--------------|
| `generate_report` | Pro ($49/mo) | Tier error with upgrade URL |
| `generate_fleet` | Pro ($49/mo) | Tier error with upgrade URL |
| `generate_compare` | Pro ($49/mo) | Tier error with upgrade URL |
| `export_data` | Pro ($49/mo) | Tier error with upgrade URL |

**Priority:** P0

### FR-06: Structured Output with Metadata

**Description:** All tools return output wrapped in a meta block with generation metadata.

**Every response includes:**
- `meta` block: tool name, timestamp, DOT number(s), output format, tier used
- `report` or `data` block: the generated content
- `disclaimer`: "This report is informational and does not constitute a compliance guarantee or legal advice."
- `sources`: list of upstream tools that provided data (e.g., carrier_profile, risk_score)

**Priority:** P0

### FR-07: Missing Data Handling in Reports

**Description:** When upstream data is incomplete (Risk Engine returned low confidence, insurance records empty, no safety rating), the report must clearly indicate what is missing rather than omitting sections or showing blanks.

**Strategy:**
- Missing sections display: "Data not available" with explanation
- Sections with partial data show what is available and note what is missing
- Risk assessment section shows confidence level prominently when LOW
- Comparison table shows "N/A" for missing metrics with footnote

**Priority:** P0

### FR-08: Comparison Limit Enforcement

**Description:** The `generate_compare` tool enforces a 2-carrier minimum and 5-carrier maximum.

**Behavior:**
- Fewer than 2 carriers: "Comparison requires at least 2 carriers. Provide 2 to 5 DOT numbers."
- More than 5 carriers: "Comparison supports a maximum of 5 carriers. Please select 5 or fewer."
- Exactly 1 carrier: suggest `generate_report` instead

**Priority:** P1

## MVP Scope

Historical v0.1.0 planning scope:

- [ ] `generate_report` -- formatted vetting report with all sections
- [ ] `generate_fleet` -- fleet analysis with equipment breakdown
- [ ] `generate_compare` -- side-by-side carrier comparison (2-5 carriers)
- [ ] `export_data` -- JSON, CSV, and Markdown export
- [ ] Tier gating on all four tools
- [ ] Meta blocks and disclaimers on all output
- [ ] Missing data handling with clear indicators

Deferred to v0.2.0:

- Customizable report templates (user-defined section order and content)
- PDF export via pandoc integration
- Batch report generation (multiple DOTs, one report each)
- Report branding (company name, logo placeholder in header)
- Historical comparison (compare a carrier against its own past data)

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|-------------|
| Report generation latency | Target: < 5 seconds (including upstream data fetch) | Timer in MCP tool handler |
| Comparison generation latency | Target: < 10 seconds (2-5 carriers) | Timer across data fetch + formatting |
| Export generation latency | Target: < 2 seconds | Timer in MCP tool handler |
| Report completeness | Target: 100% of available data sections populated | Section presence check in output |
| Format validity (JSON) | Target: 100% valid JSON | JSON parse test on every export |
| Format validity (CSV) | Target: 100% parseable CSV | CSV parse test on every export |
| Tier gate accuracy | Target: 100% (no Free user accesses any Ops Reporter tool) | Integration tests |

## Dependencies

- **Carrier Intel plugin** -- Ops Reporter consumes carrier data, authority records, insurance records, and fleet data from Carrier Intel's structured output. Required for all four tools.
- **Risk Engine plugin** -- Ops Reporter embeds risk scores, vetting verdicts, insurance assessments, and compliance audits from Risk Engine. Required for `generate_report`; optional for other tools (they work with carrier data alone but produce richer output with risk data).
- **Shared tier_gate module** -- `plugins/shared/tier_gate.py` provides the `check_tier` function used by all plugins.
- **MCP protocol** -- Plugin runs as an MCP server; requires Grok Build, Claude Code, or another MCP-capable client.
- **No external dependencies beyond the pipeline** -- Ops Reporter does not call the SearchCarriers API. It formats data that has already been retrieved and analyzed.
