# searchcarriers-watchdog

**STANDALONE monitoring plugin** for carrier watch list management and alert routing.

```
                    ┌──────────────────┐
                    │     Watchdog     │
                    │   (MONITORING)   │
                    │                  │
                    │  manage_watchlist│
                    │  get_alerts      │
                    │  route_alert     │
                    │  monitor_compliance│
                    │                  │
                    │  Min: Pro+       │
                    └──────────────────┘
```

Monitors carriers on your watch list and detects changes in safety, insurance, authority, and compliance status. Routes alerts to Slack, Telegram, email, or webhook endpoints.

## Quick Start

```bash
# 1. Set API key
export SEARCHCARRIERS_API_KEY="your_id|your_token"

# 2. Install dependencies
pip install -r plugins/searchcarriers-watchdog/scripts/requirements.txt

# 3. Start MCP server
python3 plugins/searchcarriers-watchdog/scripts/watchdog_mcp.py
```

## Tools

| Tool | Description | Min Tier |
|------|-------------|----------|
| `manage_watchlist` | Add, remove, or list carriers on the watch list | Pro+ |
| `get_alerts` | Return a truthful compatibility response when no alert-feed route is published | Pro+ |
| `route_alert` | Format alerts for Slack, Telegram, email, or webhook delivery | Pro+ |
| `monitor_compliance` | Detect compliance drift over time for watched carriers | Pro+ |

## Slash Commands

| Command | Description |
|---------|-------------|
| `/sc-watch <add\|remove\|list> [DOT]` | Manage carrier watch list |
| `/sc-alerts [event JSON] [--route CHANNEL]` | Explain alert availability or format a supplied event |

## Alert Routing Channels

| Channel | Format | Use Case |
|---------|--------|----------|
| Slack | Block Kit JSON | Team notifications |
| Telegram | Markdown message | Mobile alerts |
| Email | HTML body + text fallback | Compliance records |
| Webhook | Generic JSON payload | Custom integrations |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SEARCHCARRIERS_API_KEY` | Yes | API authentication token |
| `SEARCHCARRIERS_TIER` | No | User subscription tier (default: free) |

## Documentation

See `docs/` for enterprise documentation:
- [Business Case](docs/01-BUSINESS-CASE.md)
- [PRD](docs/02-PRD.md)
- [Architecture](docs/03-ARCHITECTURE.md)
- [User Journey](docs/04-USER-JOURNEY.md)
- [Technical Spec](docs/05-TECHNICAL-SPEC.md)
- [Status](docs/06-STATUS.md)
