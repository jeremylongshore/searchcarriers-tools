# SCHEMA: searchcarriers-risk-engine

## Directory Tree

```
searchcarriers-risk-engine/
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
│   ├── sc-risk.md               ✅ Written
│   └── sc-vet.md                ✅ Written
├── agents/
│   └── risk-analyst.md          ✅ Written
├── skills/
│   └── searchcarriers-risk-engine/
│       └── SKILL.md             ✅ Written
├── scripts/
│   ├── risk_engine_mcp.py       ✅ Written
│   └── requirements.txt         ✅ Written
├── README.md                    ✅ Written
└── SCHEMA.md                    ✅ This file
```

## Plugin Manifest Fields

| Field | Value | Status |
|-------|-------|--------|
| name | searchcarriers-risk-engine | ✅ |
| description | Risk scoring, vetting checks, insurance validation, and compliance auditing | ✅ |
| version | 0.1.0 | ✅ |
| type | mcp | ✅ |
| pipeline_stage | analysis | ✅ |
| min_tier | pro | ✅ |

## MCP Tools

| Tool | Purpose | Min Tier | Status |
|------|---------|----------|--------|
| risk_score | Composite 0-100 risk score | pro | ✅ |
| vetting_check | Qualification rules (PASS/REVIEW/FAIL) | proplus | ✅ |
| insurance_check | Coverage analysis with gap detection | pro | ✅ |
| compliance_audit | Regulatory compliance audit | pro | ✅ |

## Slash Commands

| Command | Purpose | Status |
|---------|---------|--------|
| /sc-risk | Risk score lookup | ✅ |
| /sc-vet | Vetting qualification check | ✅ |

## Skills

| Skill | Purpose | Status |
|-------|---------|--------|
| searchcarriers-risk-engine | Risk assessment interpretation and pipeline integration | ✅ |

## Agents

| Agent | Purpose | Status |
|-------|---------|--------|
| risk-analyst | Autonomous carrier risk analysis and recommendation | ✅ |

## Non-Functional Requirements

| NFR | Target |
|-----|--------|
| Response time | < 3s per tool call |
| Availability | Follows SearchCarriers API SLA |
| Scoring accuracy | < 5% false positive rate on high-risk flags |
| Data freshness | Current via API, no caching (FMCSA data synced nightly) |

## Inventory Reference

| Field | Value |
|-------|-------|
| WHO | Jeremy Longshore |
| WHAT | Risk scoring and vetting logic |
| WHEN | Phase 5 |
| TARGET | Working MCP with 4 tools |
| PRODUCTION | No |
