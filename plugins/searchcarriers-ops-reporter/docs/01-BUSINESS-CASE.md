# Ops Reporter - Business Case

## Problem Statement

Freight professionals spend more time assembling carrier vetting documents than they spend making the actual vetting decision. A compliance manager runs a carrier through SAFER, copies the results into a Word document, reformats the data into her company's standard vetting template, adds insurance details from a second source, pastes in a safety summary she wrote by hand, and emails the finished report to her operations team. The research takes 5 minutes. The formatting and assembly takes 25 to 55 minutes.

The problem is worse when comparisons are involved. A broker evaluating three carriers for a high-value lane has to build three separate profiles, then manually construct a side-by-side comparison table in a spreadsheet. Column alignment, data normalization, metric selection -- all done by hand. If one of the carriers is later disqualified and a replacement needs to be added, the entire comparison is rebuilt from scratch.

And when operations teams need carrier data in their TMS, they re-key it. A carrier profile displayed on a screen cannot be imported into a transportation management system without someone typing the values into the correct fields or formatting a CSV by hand. This manual transcription introduces errors and wastes time that should be spent moving freight.

There is also no standardized vetting report format across the industry. Every brokerage has its own template -- some use Word, some use Google Docs, some use a TMS-specific form. When a compliance manager moves companies, she starts from scratch. When an auditor requests carrier qualification records, they receive a patchwork of formats, half-completed forms, and screenshots of SAFER pages. The lack of standardization makes compliance audits slower, more expensive, and less reliable.

The data exists. The analysis exists (thanks to Carrier Intel and Risk Engine). What is missing is the last mile: turning structured data and risk assessments into documents that freight professionals can actually use -- vetting reports, comparison tables, and machine-readable exports.

## Target Customer

| Segment | Role | Pain Level | Frequency |
|---------|------|-----------|-----------|
| Compliance managers | Carrier qualification, audit documentation | Critical | 10-30 reports/day |
| Freight brokers | Load tendering decisions, carrier selection | High | 5-20 comparisons/day |
| Operations teams | TMS data import, carrier onboarding | High | 10-40 exports/day |
| Account managers | Customer-facing carrier recommendations | Medium | 5-10 reports/week |
| Safety departments | Fleet audits, equipment verification | Medium | 5-15 fleet reports/week |

The primary buyer is the compliance manager at a mid-size brokerage or 3PL. She is the person who turns raw carrier data into the vetting packet that goes to operations, account management, and legal. Today she does it in Word and Excel. Tomorrow she types one command and gets a professional report with risk scores, insurance validation, and a qualification verdict already embedded.

## Efficiency Gains

| Metric | Without Ops Reporter | With Ops Reporter | Impact |
|--------|---------------------|-------------------|--------|
| Time per vetting report | 30-60 min (manual assembly) | Seconds (automated) | Eliminates manual assembly |
| Time per carrier comparison (3 carriers) | 45-90 min (manual spreadsheet) | Seconds (automated) | Eliminates manual comparison building |
| Time per data export for TMS | 10-20 min (manual re-keying) | Seconds (automated) | Eliminates manual re-keying |
| Report format consistency | Varies by author | Identical every time | Eliminates format drift |
| Data accuracy in exports | Error-prone (manual transcription) | Structured output (no transcription) | Eliminates human error |
| Carrier comparison turnaround | Hours (manual spreadsheet work) | Seconds | On-demand comparisons |

The primary value is eliminating the assembly step. A compliance analyst spending hours per day formatting vetting reports can redirect that time to actually reviewing the data and making qualification decisions.

## Competitive Positioning

| Capability | Ops Reporter | Manual Process | Carrier411 | Highway | RMIS |
|-----------|-------------|----------------|-----------|---------|------|
| Automated vetting report | Yes (one command) | No (30-60 min manual) | PDF export | Yes (templated) | Yes (templated) |
| Embedded risk scores | Yes (from Risk Engine pipeline) | No | No | Separate module | No |
| Side-by-side carrier comparison | Yes (2-5 carriers) | Manual spreadsheet | No | Limited | No |
| Multi-format export (JSON, CSV, MD) | Yes | Manual conversion | CSV only | API/JSON | CSV/PDF |
| CLI/terminal workflow | Yes (MCP-native) | No | No | No | No |
| Pipeline integration | Yes (auto-consumes Carrier Intel + Risk Engine) | No | Standalone | Standalone | Standalone |
| Customizable report sections | Planned (v0.2) | Manual template editing | No | Limited | Yes |
| Current data (nightly FMCSA sync) | Yes (on-demand API) | No (point-in-time snapshots) | Nightly batch | On-demand | Daily batch |

**Key differentiator**: Ops Reporter is not a standalone reporting tool. It is the OUTPUT stage of a three-stage pipeline. When it generates a vetting report, that report contains current carrier data from Carrier Intel AND computed risk assessments from Risk Engine. No other carrier reporting tool in the market embeds risk scores, insurance gap analysis, and compliance audit results into a single generated document.

**Secondary differentiator**: Multi-format export. Ops Reporter outputs Markdown (human-readable), JSON (machine-readable), and CSV (spreadsheet/TMS-importable) from the same source data. A compliance manager gets a formatted report; her TMS gets a structured import file; her developer gets a JSON payload -- all from the same pipeline execution.

## Revenue Model

Ops Reporter is the final stage of the pipeline and reinforces the Pro tier value proposition:

| Plugin Tool | Min Tier | Revenue Driver |
|------------|----------|----------------|
| `generate_report` | Pro ($49/mo) | Primary deliverable -- the vetting report customers show to management |
| `generate_fleet` | Pro ($49/mo) | Fleet analysis for equipment verification and capacity assessment |
| `generate_compare` | Pro ($49/mo) | Carrier comparison for competitive load tendering |
| `export_data` | Pro ($49/mo) | Data portability -- feeds TMS, spreadsheets, internal systems |

**Conversion funnel**: Users enter through Carrier Intel (Free), discover risk scoring (Pro), and realize they need formatted deliverables for their team. The vetting report is often the artifact that justifies the Pro subscription to management -- it is the visible output that non-technical stakeholders can evaluate.

**Retention driver**: Once an organization standardizes on Ops Reporter's vetting report format, switching costs increase. Their compliance records, audit trails, and management reports all reference the same report structure. Consistency creates stickiness.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Report formatting limitations | Medium | Medium -- Markdown may not satisfy teams that need PDF/branded templates | Markdown renders well in most tools; PDF export is a v0.2 candidate; provide clean Markdown that converts well with pandoc |
| Upstream data quality | Medium | High -- reports are only as good as the data from Carrier Intel and Risk Engine | Include data completeness indicators in every report; flag sections with missing data |
| Report misuse as compliance certification | Medium | High -- someone treats a generated report as a legal compliance document | Every report includes disclaimer: "This report is informational and does not constitute a compliance guarantee" |
| Performance on large comparisons | Low | Medium -- comparing 5 carriers with full profiles could be slow | Comparison limited to 2-5 carriers; data is pre-fetched by Carrier Intel, so Ops Reporter only formats |
| Competitor replication | Medium | Low -- anyone can format carrier data | Moat is the pipeline integration and embedded risk scores, not the formatting itself |
