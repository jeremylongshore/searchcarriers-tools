# SCHEMA: searchcarriers-ops-reporter

## Directory Tree

```
searchcarriers-ops-reporter/
├── .claude-plugin/
│   └── plugin.json              ✅ Written
├── .mcp.json                    ✅ Written
├── docs/
│   ├── 01-BUSINESS-CASE.md      ✅ Written
│   ├── 02-PRD.md                ✅ Written
│   ├── 03-ARCHITECTURE.md       ✅ Written
│   ├── 04-USER-JOURNEY.md       ✅ Written
│   ├── 05-TECHNICAL-SPEC.md     ✅ Written
│   └── 06-STATUS.md             ✅ Written
├── commands/
│   ├── sc-report.md             ✅ Written
│   └── sc-compare.md            ✅ Written
├── agents/
│   └── ops-reporter.md          ✅ Written
├── skills/
│   └── searchcarriers-ops-reporter/
│       └── SKILL.md             ✅ Written
├── scripts/
│   ├── ops_reporter_mcp.py      ✅ Written
│   └── requirements.txt         ✅ Written
├── README.md                    ✅ Written
└── SCHEMA.md                    ✅ This file
```

## Plugin Manifest Fields

| Field | Value | Status |
|-------|-------|--------|
| name | searchcarriers-ops-reporter | ✅ |
| description | Vetting reports, fleet analysis, carrier comparisons, and data export | ✅ |
| version | 0.1.0 | ✅ |
| type | mcp | ✅ |
| pipeline_stage | output | ✅ |
| min_tier | pro | ✅ |

## MCP Tools

| Tool | Purpose | Min Tier | Status |
|------|---------|----------|--------|
| generate_report | Comprehensive vetting report | pro | ✅ |
| generate_fleet | Fleet analysis with equipment roster | pro | ✅ |
| generate_compare | Side-by-side carrier comparison (2-5) | pro | ✅ |
| export_data | Multi-format data export (JSON/CSV/MD) | pro | ✅ |

## Slash Commands

| Command | Purpose | Status |
|---------|---------|--------|
| /sc-report | Generate vetting report | ✅ |
| /sc-compare | Compare carriers side-by-side | ✅ |

## Skills

| Skill | Purpose | Status |
|-------|---------|--------|
| searchcarriers-ops-reporter | Report generation and pipeline output interpretation | ✅ |

## Agents

| Agent | Purpose | Status |
|-------|---------|--------|
| ops-reporter | Autonomous reporting workflow with pipeline orchestration | ✅ |

## Non-Functional Requirements

| NFR | Target |
|-----|--------|
| Report generation time | < 5s (single carrier) |
| Comparison time | < 10s (5 carriers) |
| Report quality | Professional markdown formatting |
| Export formats | JSON, CSV, Markdown |

## Inventory Reference

| Field | Value |
|-------|-------|
| WHO | Jeremy Longshore |
| WHAT | Reports and data export |
| WHEN | Phase 6 |
| TARGET | Working MCP with 4 tools |
| PRODUCTION | No |
