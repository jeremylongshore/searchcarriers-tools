# SCHEMA: searchcarriers-api-bridge

## Directory Tree

```
searchcarriers-api-bridge/
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
│   ├── sc-api.md                ✅ Written
│   └── sc-bulk.md               ✅ Written
├── agents/
│   └── integration-manager.md   ✅ Written
├── skills/
│   └── searchcarriers-api-bridge/
│       └── SKILL.md             ✅ Written
├── scripts/
│   ├── api_bridge_mcp.py        ✅ Written
│   └── requirements.txt         ✅ Written
├── README.md                    ✅ Written
└── SCHEMA.md                    ✅ This file
```

## Plugin Manifest Fields

| Field | Value | Status |
|-------|-------|--------|
| name | searchcarriers-api-bridge | ✅ |
| description | API health, bulk ops, TMS sync, webhook management | ✅ |
| version | 0.1.0 | ✅ |
| type | mcp | ✅ |
| pipeline_stage | integration | ✅ |
| min_tier | smb | ✅ |

## MCP Tools

| Tool | Purpose | Min Tier | Status |
|------|---------|----------|--------|
| api_health | Endpoint status and rate limits | smb | ✅ |
| bulk_lookup | Batch carrier lookups (max 100) | smb | ✅ |
| tms_sync | TMS data export/import | enterprise | ✅ |
| webhook_manage | Webhook CRUD | smb | ✅ |

## Slash Commands

| Command | Purpose | Status |
|---------|---------|--------|
| /sc-api | API health dashboard | ✅ |
| /sc-bulk | Bulk carrier lookups | ✅ |

## Skills

| Skill | Purpose | Status |
|-------|---------|--------|
| searchcarriers-api-bridge | Integration management and bulk processing | ✅ |

## Agents

| Agent | Purpose | Status |
|-------|---------|--------|
| integration-manager | Autonomous bulk processing and TMS integration workflow | ✅ |

## Inventory Reference

| Field | Value |
|-------|-------|
| WHO | Jeremy Longshore |
| WHAT | Bulk ops and TMS sync |
| WHEN | Phase 8 |
| TARGET | Working MCP with 4 tools |
| PRODUCTION | No |
