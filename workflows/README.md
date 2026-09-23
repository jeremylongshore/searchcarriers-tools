# Premium Workflows

Cross-plugin workflow orchestrations that chain multiple MCP tools together. These are the value-add workflows that justify higher subscription tiers.

## Workflow Catalog

### Pro Tier ($49/mo)

| Workflow | Plugins Used | Description |
|----------|-------------|-------------|
| [Daily Vetting Digest](pro/daily-vetting-digest/SKILL.md) | Risk Engine + Watchdog + Ops Reporter | Auto-vet all watched carriers, email daily digest with pass/review/fail |

### Pro+ Tier ($99/mo)

| Workflow | Plugins Used | Description |
|----------|-------------|-------------|
| [Slack Carrier Watch](proplus/slack-carrier-watch/SKILL.md) | Watchdog | Format validated external carrier notifications as Slack Block Kit payloads |
| [Insurance Lapse Alert](proplus/insurance-lapse-alert/SKILL.md) | Risk Engine + Watchdog | Instant alert on insurance cancellation or lapse |
| [Compliance Dashboard](proplus/compliance-dashboard/SKILL.md) | Risk Engine + Watchdog + Ops Reporter | Weekly compliance report with drift tracking |

### SMB Tier ($199/mo)

| Workflow | Plugins Used | Description |
|----------|-------------|-------------|
| [Bulk Vetting Pipeline](smb/bulk-vetting-pipeline/SKILL.md) | API Bridge + Risk Engine + Ops Reporter | Upload carrier list, get consolidated vetting report |

### Enterprise Tier ($499/mo)

| Workflow | Plugins Used | Description |
|----------|-------------|-------------|
| [TMS Auto-Sync](enterprise/tms-auto-sync/SKILL.md) | Watchdog + API Bridge | Auto-sync carrier changes to TMS platforms |
| [Fleet Risk Dashboard](enterprise/fleet-risk-dashboard/SKILL.md) | All stackable + Watchdog | Weekly fleet-wide risk analysis with executive summary |

## How Workflows Work

Each workflow is a SKILL.md that orchestrates multiple plugin MCP tools in sequence:

```
Workflow Skill
    ├── Step 1: Call Plugin A tool
    ├── Step 2: Call Plugin B tool
    ├── Step 3: Process/aggregate results
    ├── Step 4: Call Plugin C tool (output/routing)
    └── Result: Formatted deliverable
```

Workflows don't require additional code — they're instruction sets that Claude follows using the existing MCP tools.

## Plugin Dependencies

```
daily-vetting-digest     → watchdog + risk-engine + ops-reporter
slack-carrier-watch      → watchdog
insurance-lapse-alert    → watchdog + risk-engine
compliance-dashboard     → watchdog + risk-engine + ops-reporter
bulk-vetting-pipeline    → api-bridge + risk-engine + ops-reporter
tms-auto-sync            → watchdog + api-bridge
fleet-risk-dashboard     → carrier-intel + risk-engine + ops-reporter + watchdog
```
