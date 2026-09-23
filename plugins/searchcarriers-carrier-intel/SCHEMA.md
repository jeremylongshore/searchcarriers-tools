# searchcarriers-carrier-intel — Schema

## Directory Tree

```
searchcarriers-carrier-intel/
├── .claude-plugin/
│   └── plugin.json              [done]
├── .mcp.json                    [done]
├── docs/
│   ├── 01-BUSINESS-CASE.md      [done]
│   ├── 02-PRD.md                [done]
│   ├── 03-ARCHITECTURE.md       [done]
│   ├── 04-USER-JOURNEY.md       [done]
│   ├── 05-TECHNICAL-SPEC.md     [done]
│   └── 06-STATUS.md             [done]
├── commands/
│   ├── sc-lookup.md             [done]
│   └── sc-profile.md            [done]
├── agents/
│   └── carrier-analyst.md       [done]
├── skills/
│   └── searchcarriers-carrier-intel/
│       └── SKILL.md             [done]
├── scripts/
│   ├── carrier_intel_mcp.py     [done]
│   └── requirements.txt         [done]
├── README.md                    [done]
└── SCHEMA.md                    [this file]
```

## Plugin Manifest Fields

| Field | Value | Status |
|-------|-------|--------|
| name | searchcarriers-carrier-intel | done |
| description | Carrier lookup, profile, entity mapping, fleet summary | done |
| version | 0.1.0 | done |
| type | mcp | done |
| pipeline_stage | input | done |
| min_tier | free | done |

## MCP Tools

| Tool | Purpose | Min Tier | API Endpoints |
|------|---------|----------|---------------|
| carrier_lookup | Search carriers by any identifier | free | GET /search |
| carrier_profile | Full carrier + authorities + insurance | free | GET /search, GET /company/{dot}/authorities, GET /company/{dot}/insurances |
| entity_map | Find related companies via VINs | pro | GET /company/{dot}/equipment, GET /search/by-vin/ |
| fleet_summary | Equipment + vehicle roster | free | GET /company/{dot}/equipment, GET /company/{dot}/vehicles |

## Slash Commands

| Command | Trigger | MCP Tool |
|---------|---------|----------|
| /sc-lookup | Carrier search | carrier_lookup |
| /sc-profile | Full carrier profile | carrier_profile |

## Skills Registry

| Skill | Type | Description |
|-------|------|-------------|
| searchcarriers-carrier-intel | embedded | Interprets carrier data with freight industry context |

## Agents Registry

| Agent | Description |
|-------|-------------|
| carrier-analyst | Autonomous full carrier analysis with recommendations |

## Non-Functional Requirements

| Metric | Target | Max |
|--------|--------|-----|
| Single lookup | < 1s | 3s |
| Profile aggregation | < 3s | 5s |
| Entity mapping | < 10s | 30s |
| Fleet summary | < 2s | 5s |

## Inventory Reference

| Field | Value |
|-------|-------|
| WHO | Jeremy Longshore / Intent Solutions |
| WHAT | Carrier data retrieval (INPUT stage) |
| WHEN | Phase 4 (2026-02-26) |
| TARGET | Freight brokers, 3PLs, safety teams |
| PRODUCTION | Requires active SearchCarriers subscription |
