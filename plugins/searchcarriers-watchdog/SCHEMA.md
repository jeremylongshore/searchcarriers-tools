# SCHEMA: searchcarriers-watchdog

## Directory Tree

```
searchcarriers-watchdog/
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
│   ├── sc-watch.md              ✅ Written
│   └── sc-alerts.md             ✅ Written
├── agents/
│   └── watchdog-monitor.md      ✅ Written
├── skills/
│   └── searchcarriers-watchdog/
│       └── SKILL.md             ✅ Written
├── scripts/
│   ├── watchdog_mcp.py          ✅ Written
│   └── requirements.txt         ✅ Written
├── README.md                    ✅ Written
└── SCHEMA.md                    ✅ This file
```

## Plugin Manifest Fields

| Field | Value | Status |
|-------|-------|--------|
| name | searchcarriers-watchdog | ✅ |
| description | Carrier watch list management, alerts, and compliance drift monitoring | ✅ |
| version | 0.1.0 | ✅ |
| type | mcp | ✅ |
| pipeline_stage | monitoring | ✅ |
| min_tier | proplus | ✅ |

## MCP Tools

| Tool | Purpose | Min Tier | Status |
|------|---------|----------|--------|
| manage_watchlist | Watch list CRUD (add/remove/list) | proplus | ✅ |
| get_alerts | Report that no published alert-feed route is available | proplus | ✅ |
| route_alert | Format alerts for Slack/Telegram/email/webhook | proplus | ✅ |
| monitor_compliance | Compliance drift detection | proplus | ✅ |

## Slash Commands

| Command | Purpose | Status |
|---------|---------|--------|
| /sc-watch | Watch list management | ✅ |
| /sc-alerts | Explain alert availability or format a supplied event | ✅ |

## Skills

| Skill | Purpose | Status |
|-------|---------|--------|
| searchcarriers-watchdog | Monitoring interpretation and alert management | ✅ |

## Agents

| Agent | Purpose | Status |
|-------|---------|--------|
| watchdog-monitor | Autonomous monitoring and alert routing workflow | ✅ |

## Inventory Reference

| Field | Value |
|-------|-------|
| WHO | Jeremy Longshore |
| WHAT | Carrier watch and alert routing |
| WHEN | Phase 7 |
| TARGET | Working MCP with 4 tools |
| PRODUCTION | No |
