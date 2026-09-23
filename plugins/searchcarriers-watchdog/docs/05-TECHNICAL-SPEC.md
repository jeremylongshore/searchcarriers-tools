# Watchdog - Technical Specification

## Tech Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Runtime | Python | 3.10+ | MCP server runtime |
| Protocol | MCP (Model Context Protocol) | 1.0+ | Tool registration and invocation |
| HTTP client | httpx | 0.27+ | Async HTTP requests to Carrier Watch API |
| Validation | pydantic | 2.0+ | Request/response schema validation |
| Testing | pytest | 8.0+ | Unit and integration tests |

## Dependencies

```
httpx>=0.27
mcp>=1.0
```

Specified in `scripts/requirements.txt`. Pydantic is recommended for v0.2 response validation but not required for MVP.

## File Structure

```
searchcarriers-watchdog/
├── .claude-plugin/
│   └── plugin.json                    # Plugin manifest (name, tools, tiers, version)
├── .mcp.json                          # MCP server configuration (command, args, env)
├── docs/                              # 6-doc enterprise documentation set
│   ├── 01-BUSINESS-CASE.md
│   ├── 02-PRD.md
│   ├── 03-ARCHITECTURE.md
│   ├── 04-USER-JOURNEY.md
│   ├── 05-TECHNICAL-SPEC.md           # (this file)
│   └── 06-STATUS.md
├── commands/                          # Slash command definitions (planned)
├── agents/                            # Agent definitions (planned)
│   └── watchdog-analyst.md
├── skills/
│   └── searchcarriers-watchdog/
│       └── SKILL.md                   # Embedded skill for Claude (planned)
├── scripts/
│   ├── watchdog_mcp.py                # MCP server implementation
│   ├── formatters.py                  # Channel-specific alert formatters (planned)
│   ├── drift.py                       # Compliance drift analyzer (planned)
│   └── requirements.txt               # Python dependencies
└── README.md                          # Quick start guide (planned)
```

## API Endpoints

| Tool | Endpoint | Method | Parameters | Min Tier | Notes |
|------|----------|--------|-----------|----------|-------|
| `manage_watchlist` (add) | `/api/v1/company/{dot}/watch` | POST | `watch_types` array | Pro+ | Synchronize watch categories |
| `manage_watchlist` (remove) | `/api/v1/company/{dot}/watch` | POST | Empty `watch_types` array | Pro+ | Stop all watches for carrier |
| `manage_watchlist` (list) | `/api/v1/company/watch` | GET | None | Pro+ | List watched carriers |
| `get_alerts` | No published route | None | None | Pro+ | Returns structured `endpoint_unavailable` compatibility response |
| `monitor_compliance` | Hybrid company/detail routes | GET | DOT number | Pro+ | Evaluate current company, authority, and insurance data |

**Base URL:** `https://searchcarriers.com/api/v1`

**Authentication:** All requests include `Authorization: Bearer {SEARCHCARRIERS_API_KEY}` header.

**Pagination:** The watch list uses the pagination metadata returned by the API.
No pagination behavior is claimed for an alert feed because no such route is
published. The `route_alert` tool performs local formatting only.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SEARCHCARRIERS_API_KEY` | Yes | -- | Bearer token for API authentication. Format: `{id}\|{token}` (Laravel Sanctum). Get from https://searchcarriers.com/settings/api-tokens |
| `SEARCHCARRIERS_TIER` | No | -- | Override tier detection. Values: free, basic, pro, proplus, smb, enterprise. If not set, tier is determined from API response. |
| `SEARCHCARRIERS_API_BASE` | No | `https://searchcarriers.com/api/v1` | API base URL override (for testing against staging) |
| `SEARCHCARRIERS_TIMEOUT` | No | `10` | HTTP request timeout in seconds |
| `SEARCHCARRIERS_MAX_RETRIES` | No | `3` | Maximum retry attempts for transient failures (429, 504) |
| `SEARCHCARRIERS_LOG_LEVEL` | No | `WARNING` | Logging level: DEBUG, INFO, WARNING, ERROR |

## MCP Tool Schemas

### manage_watchlist

**Input:**
```json
{
  "action": "string (required) - One of: add, remove, list",
  "dot_number": "string (required for add/remove) - DOT number of the carrier",
  "per_page": "integer (optional, default 25) - Results per page (list only)",
  "page": "integer (optional, default 1) - Page number (list only)"
}
```

**Output (add):**
```json
{
  "meta": {
    "tool": "manage_watchlist",
    "action": "add",
    "timestamp": "2026-02-26T14:30:00Z",
    "dot_number": "69494"
  },
  "result": {
    "status": "added",
    "carrier": {
      "dot_number": "69494",
      "legal_name": "WERNER ENTERPRISES INC",
      "status_code": "A",
      "safety_rating": "S",
      "added_at": "2026-02-26T14:30:00Z"
    },
    "watchlist_count": 12
  }
}
```

**Output (list):**
```json
{
  "meta": {
    "tool": "manage_watchlist",
    "action": "list",
    "timestamp": "2026-02-26T14:30:00Z",
    "total_carriers": 12,
    "page": 1,
    "per_page": 25
  },
  "carriers": [
    {
      "dot_number": "69494",
      "legal_name": "WERNER ENTERPRISES INC",
      "status_code": "A",
      "safety_rating": "S",
      "added_at": "2026-02-26T14:30:00Z"
    }
  ]
}
```

### get_alerts

**Input:**
```json
{
  "hours": "integer (optional, default 24) - Time window in hours",
  "alert_type": "string (optional, default 'all') - Filter: safety, insurance, authority, operational, all",
  "severity": "string (optional, default 'all') - Filter: critical, warning, info, all"
}
```

**Output:**
```json
{
  "meta": {
    "tool": "get_alerts",
    "timestamp": "2026-03-15T09:00:00Z",
    "hours": 24,
    "filters": {
      "alert_type": "all",
      "severity": "all"
    },
    "total_alerts": 3
  },
  "alerts": [
    {
      "id": "alert_001",
      "carrier_dot": "3456789",
      "carrier_name": "COLD STAR LOGISTICS LLC",
      "alert_type": "insurance",
      "severity": "critical",
      "change_field": "cargo_insurance_status",
      "old_value": "Active ($100,000)",
      "new_value": "Cancelled",
      "detected_at": "2026-03-15T08:14:00Z",
      "action": "DO NOT TENDER loads to this carrier until coverage is confirmed"
    }
  ]
}
```

### route_alert

**Input:**
```json
{
  "alert": "object (required) - Validated carrier event supplied by the caller",
  "channel": "string (required) - One of: slack, telegram, email, webhook"
}
```

**Output (slack):**
```json
{
  "meta": {
    "tool": "route_alert",
    "timestamp": "2026-03-15T09:05:00Z",
    "channel": "slack",
    "carrier_dot": "3456789"
  },
  "formatted": {
    "channel": "slack",
    "content_type": "application/json",
    "blocks": [
      {
        "type": "header",
        "text": { "type": "plain_text", "text": "CRITICAL: Insurance Cancelled", "emoji": true }
      },
      {
        "type": "section",
        "fields": [
          { "type": "mrkdwn", "text": "*Carrier:*\nCOLD STAR LOGISTICS LLC" },
          { "type": "mrkdwn", "text": "*DOT:*\n3456789" }
        ]
      },
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": "*Change:* Cargo insurance policy CANCELLED\n*Previous:* $100,000 coverage (Active)\n*Current:* No active cargo insurance on file"
        }
      },
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": ":rotating_light: *Action Required:* DO NOT TENDER loads to this carrier until coverage is confirmed."
        }
      },
      {
        "type": "context",
        "elements": [
          { "type": "mrkdwn", "text": "Detected: 2026-03-15 08:14 UTC | Source: SearchCarriers Carrier Watch" }
        ]
      }
    ],
    "attachments": [{ "color": "#dc3545" }]
  }
}
```

**Output (telegram):**
```json
{
  "meta": {
    "tool": "route_alert",
    "timestamp": "2026-03-15T09:05:00Z",
    "channel": "telegram",
    "carrier_dot": "3456789"
  },
  "formatted": {
    "channel": "telegram",
    "content_type": "text/markdown",
    "parse_mode": "MarkdownV2",
    "text": "🚨 *CRITICAL: Insurance Cancelled*\n\n*Carrier:* COLD STAR LOGISTICS LLC\n*DOT:* `3456789`\n\n*Change:* Cargo insurance policy CANCELLED\n*Previous:* $100,000 coverage \\(Active\\)\n*Current:* No active cargo insurance on file\n\n⚠️ *Action Required:* DO NOT TENDER loads to this carrier until coverage is confirmed\\.\n\n_Detected: 2026\\-03\\-15 08:14 UTC \\| Source: SearchCarriers Carrier Watch_"
  }
}
```

**Output (email):**
```json
{
  "meta": {
    "tool": "route_alert",
    "timestamp": "2026-03-15T09:05:00Z",
    "channel": "email",
    "carrier_dot": "3456789"
  },
  "formatted": {
    "channel": "email",
    "content_type": "text/html",
    "subject": "CRITICAL: Insurance Cancelled - COLD STAR LOGISTICS LLC (DOT 3456789)",
    "html": "<div style=\"font-family: Arial, sans-serif; max-width: 600px;\">..."
  }
}
```

**Output (webhook):**
```json
{
  "meta": {
    "tool": "route_alert",
    "timestamp": "2026-03-15T09:05:00Z",
    "channel": "webhook",
    "carrier_dot": "3456789"
  },
  "formatted": {
    "channel": "webhook",
    "content_type": "application/json",
    "payload": {
      "event": "carrier_alert",
      "severity": "critical",
      "carrier_dot": "3456789",
      "carrier_name": "COLD STAR LOGISTICS LLC",
      "alert_type": "insurance",
      "change_field": "cargo_insurance_status",
      "old_value": "Active ($100,000)",
      "new_value": "Cancelled",
      "detected_at": "2026-03-15T08:14:00Z",
      "action": "DO NOT TENDER loads to this carrier until coverage is confirmed",
      "source": "SearchCarriers Carrier Watch"
    }
  }
}
```

### monitor_compliance

**Input:**
```json
{
  "dot_number": "string (required) - DOT number of the watched carrier",
  "days": "integer (optional, default 90) - Monitoring period in days"
}
```

**Output:**
```json
{
  "meta": {
    "tool": "monitor_compliance",
    "timestamp": "2026-03-15T09:10:00Z",
    "dot_number": "3456789",
    "days": 180
  },
  "carrier": {
    "dot_number": "3456789",
    "legal_name": "COLD STAR LOGISTICS LLC"
  },
  "drift": {
    "direction": "deteriorating",
    "period_start": "2025-09-15",
    "period_end": "2026-03-15",
    "total_changes": 5,
    "critical_changes": 1,
    "warning_changes": 2,
    "info_changes": 2,
    "days_since_last_change": 1
  },
  "events": [
    {
      "date": "2025-10-02",
      "type": "insurance",
      "change": "Cargo coverage reduced $250K to $100K",
      "severity": "warning",
      "impact": "negative"
    },
    {
      "date": "2025-11-18",
      "type": "safety",
      "change": "Vehicle OOS rate increased 22% to 31%",
      "severity": "warning",
      "impact": "negative"
    },
    {
      "date": "2026-01-05",
      "type": "operational",
      "change": "MCS-150 filing became overdue",
      "severity": "info",
      "impact": "negative"
    },
    {
      "date": "2026-02-10",
      "type": "safety",
      "change": "Driver OOS rate increased 5% to 8.2%",
      "severity": "info",
      "impact": "negative"
    },
    {
      "date": "2026-03-14",
      "type": "insurance",
      "change": "Cargo insurance CANCELLED",
      "severity": "critical",
      "impact": "negative"
    }
  ]
}
```

## Alert Severity Classification

| Severity | Alert Types | Criteria |
|----------|------------|----------|
| **Critical** | Insurance cancelled, authority revoked, Out-of-Service order issued, carrier status changed to inactive | Immediate action required -- carrier may not be legally authorized to operate |
| **Warning** | Insurance expiring within 30 days, safety rating downgrade, authority suspended, cargo coverage reduced below minimum, vehicle OOS rate exceeds national average by 50%+ | Action recommended within 24-48 hours |
| **Info** | MCS-150 filed, fleet size change, address change, contact update, insurance renewal, safety rating upgrade, authority reinstated | Informational -- positive or neutral changes |

Classification logic is implemented in the MCP server's alert processing layer, not in the API. The Carrier Watch API returns raw change events; the MCP server classifies severity based on the change type and magnitude.

## Alert Message Format Specifications

### Slack Block Kit

- **Header block**: Plain text with severity level and change type
- **Section blocks**: mrkdwn fields for carrier details and change information
- **Context block**: Timestamp and source attribution
- **Attachment color**: `#dc3545` (critical/red), `#ffc107` (warning/yellow), `#28a745` (info/green)
- **Character limit**: 3,000 per text field (Slack limit); truncate change details if exceeded
- **Spec reference**: [Slack Block Kit](https://api.slack.com/block-kit)

### Telegram MarkdownV2

- **Bold**: Carrier name, severity level, section labels
- **Monospace**: DOT numbers, numeric values
- **Emoji**: Severity indicators (red circle for critical, warning sign for warning, info for info)
- **Escaping**: Special characters `_*[]()~>#+-=|{}.!` must be escaped with backslash
- **Character limit**: 4,096 per message (Telegram limit)
- **Parse mode**: `MarkdownV2` (specified in output for Telegram Bot API)
- **Spec reference**: [Telegram MarkdownV2](https://core.telegram.org/bots/api#markdownv2-style)

### Email HTML

- **Container**: Single `<div>` with inline CSS (no external stylesheets -- email clients strip them)
- **Header**: Colored banner matching severity (red/yellow/green background)
- **Body**: Table layout with carrier details, change summary, and recommended action
- **Footer**: Timestamp, source attribution, small text
- **Compatibility**: Tested rendering targets: Gmail, Outlook 365, Apple Mail
- **No images**: Inline CSS only, no external images (blocked by email clients)
- **Character limit**: No practical limit, but keep under 100KB for email client compatibility

### Webhook JSON

- **Flat structure**: Maximum one level of nesting
- **Field naming**: snake_case for all fields
- **Required fields**: `event`, `severity`, `carrier_dot`, `carrier_name`, `alert_type`, `change_field`, `old_value`, `new_value`, `detected_at`, `source`
- **Optional fields**: `action` (recommended action text)
- **Content type**: `application/json`
- **Compatibility**: Designed for Zapier, Make (Integromat), n8n, and custom webhook handlers

## Tier Gating Implementation

```python
TIER_ORDER = ["free", "basic", "pro", "proplus", "smb", "enterprise"]

TOOL_TIERS = {
    "manage_watchlist": "proplus",
    "get_alerts": "proplus",
    "route_alert": "proplus",
    "monitor_compliance": "proplus",
}


def check_tier(tool_name: str, user_tier: str) -> bool:
    """Return True if user_tier is sufficient for tool_name."""
    required = TOOL_TIERS[tool_name]
    return TIER_ORDER.index(user_tier) >= TIER_ORDER.index(required)
```

All four Watchdog tools require Pro+ tier. This is the highest tier gate in the SearchCarriers plugin ecosystem. The rationale: Watchdog is a premium monitoring feature that targets compliance-conscious organizations. The server-side Carrier Watch infrastructure has per-user resource costs (monitoring loops, change detection, alert storage) that justify the higher tier requirement.

Tier is determined from the `SEARCHCARRIERS_TIER` environment variable or from the API key validation response. The tier check happens before any API calls to avoid wasting rate-limited requests on users who cannot access the tools.

## Testing Strategy

### Unit Tests (mock API)

Mock all HTTP responses using `httpx.MockTransport` or `respx`. Test:

- **Watch list CRUD**: Verify add, remove, and list actions produce correct API calls and parse responses
- **Alert compatibility**: Verify `get_alerts` returns `endpoint_unavailable` without an HTTP call
- **Alert severity classification**: Verify critical/warning/info classification for all change types
- **Slack formatting**: Verify valid Block Kit JSON output, correct color mapping
- **Telegram formatting**: Verify MarkdownV2 output, special character escaping
- **Email formatting**: Verify HTML structure, inline CSS, severity-colored headers
- **Webhook formatting**: Verify flat JSON payload with required fields
- **Compliance checks**: Verify current-state pass/fail checks and aggregate status
- **Error handling**: Verify correct user messages for 401, 403, 404, 429, 504
- **Tier gating**: Verify non-Pro+ user cannot access any tool

### Integration Tests (real API)

Marked with `@pytest.mark.integration`. Require a valid `SEARCHCARRIERS_API_KEY` with Pro+ tier. Run against the live API:

- **manage_watchlist("add", "69494")** -- add Werner to watch list and confirm
- **manage_watchlist("list")** -- verify Werner appears in list
- **get_alerts()** -- verify the truthful compatibility response
- **manage_watchlist("remove", "69494")** -- remove Werner and confirm
- **Latency**: manage_watchlist < 3s; `get_alerts` completes locally

Integration tests are excluded from CI by default (no API key in CI environment). Run locally with:

```bash
SEARCHCARRIERS_API_KEY="your_key" pytest -v -m integration
```

### Formatter Tests

Test each channel formatter independently with known alert data:

- **Slack**: Parse output as JSON, verify block types and structure match Block Kit spec
- **Telegram**: Verify all special characters are properly escaped for MarkdownV2
- **Email**: Verify HTML is well-formed (no unclosed tags), inline CSS is present
- **Webhook**: Verify all required fields are present, JSON is valid, structure is flat

### Drift Analyzer Tests

Test drift computation with synthetic change histories:

- **All positive changes** -> direction: improving
- **All negative changes** -> direction: deteriorating
- **Mixed changes, net positive** -> direction: improving
- **No changes** -> direction: stable
- **Single critical negative change** -> direction: deteriorating (critical changes weighted heavily)

## Deployment

### Installation

1. Copy the `searchcarriers-watchdog/` directory into your Claude Code plugins location:

```bash
cp -r plugins/searchcarriers-watchdog/ ~/.claude/plugins/searchcarriers-watchdog/
```

2. Or add the MCP server configuration to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "searchcarriers-watchdog": {
      "command": "python3",
      "args": ["plugins/searchcarriers-watchdog/scripts/watchdog_mcp.py"],
      "env": {
        "SEARCHCARRIERS_API_KEY": "${SEARCHCARRIERS_API_KEY}"
      }
    }
  }
}
```

3. Set your API key (must be Pro+ tier):

```bash
export SEARCHCARRIERS_API_KEY="your_id|your_token"
```

4. Restart Claude Code. The MCP server starts automatically and registers four tools: `manage_watchlist`, `get_alerts`, `route_alert`, `monitor_compliance`.

5. Verify:

```
Show my carrier watch list
```

If configured correctly, this will return your watch list (possibly empty). If the API key is missing, invalid, or below Pro+ tier, you will see a clear error message.

### Updating

Pull the latest version and copy the updated plugin directory:

```bash
git pull origin main
cp -r plugins/searchcarriers-watchdog/ ~/.claude/plugins/searchcarriers-watchdog/
```

Restart Claude Code to pick up changes. No database migrations, no config file changes -- the plugin is stateless.

## Performance Benchmarks

| Operation | Target p50 | Target p95 | Target p99 | Bottleneck |
|-----------|-----------|-----------|-----------|-----------|
| `manage_watchlist` (add) | 400ms | 800ms | 1.5s | Single API POST + network latency |
| `manage_watchlist` (remove) | 400ms | 800ms | 1.5s | Single API DELETE + network latency |
| `manage_watchlist` (list, 50 carriers) | 600ms | 1.2s | 2.5s | Single API GET + response size |
| `manage_watchlist` (list, 200 carriers) | 1.0s | 2.0s | 3.5s | Paginated response |
| `get_alerts` | <100ms | <250ms | 500ms | Local compatibility response; no API call |
| `route_alert` (slack) | 5ms | 15ms | 50ms | JSON construction, no I/O |
| `route_alert` (telegram) | 3ms | 10ms | 30ms | String formatting, no I/O |
| `route_alert` (email) | 8ms | 20ms | 60ms | HTML construction, no I/O |
| `route_alert` (webhook) | 2ms | 8ms | 25ms | JSON serialization, no I/O |
| `monitor_compliance` (90d) | 1.0s | 2.5s | 5.0s | API call + drift analysis |
| `monitor_compliance` (365d) | 2.0s | 4.0s | 8.0s | Larger history + analysis |
| MCP server cold start | 500ms | 1s | 2s | Python import + env validation |
| Tier check | <1ms | <1ms | <1ms | In-memory lookup, no I/O |

Primary bottleneck is network round-trip time to the SearchCarriers Carrier Watch API. Alert formatting (`route_alert`) is the fastest operation -- pure string/JSON construction with no I/O. Compliance drift analysis adds milliseconds of CPU time for event categorization and trend computation.
