# Watchdog - Architecture

## System Context

Watchdog is a **STANDALONE** monitoring plugin. It manages the documented
company watch list, evaluates current compliance evidence, and formats caller
supplied events for external channels. It does not claim an upstream alert
feed or historical change stream.

```
                    SEARCHCARRIERS PLUGIN ECOSYSTEM
  =====================================================================

  STACKABLE PIPELINE (data flows left to right):

  +-----------------------+     +------------------------+     +-------------------------+
  |   CARRIER INTEL       |     |   RISK ENGINE          |     |   OPS REPORTER          |
  |   (INPUT)             |---->|   (ANALYSIS)           |---->|   (OUTPUT)              |
  |                       |     |                        |     |                         |
  |   carrier_lookup      |     |   risk_score           |     |   generate_report       |
  |   carrier_profile     |     |   vetting_check        |     |   generate_fleet        |
  |   entity_map          |     |   insurance_check      |     |   generate_compare      |
  |   fleet_summary       |     |   compliance_audit     |     |   export_data           |
  |                       |     |                        |     |                         |
  |   Min: Free           |     |   Min: Pro             |     |   Min: Pro              |
  +-----------------------+     +------------------------+     +-------------------------+

  STANDALONE MONITORING (independent):

  +----------------------------+
  |   WATCHDOG                 |
  |   (MONITORING)             |
  |                            |
  |   manage_watchlist         |
  |   get_alerts               |
  |   route_alert              |
  |   monitor_compliance       |
  |                            |
  |   Min: Pro+                |
  +----------------------------+
         ^
         |
  SearchCarriers Carrier Watch API
  (monitoring data source)
```

**Upstream**: SearchCarriers' documented company-watch routes plus current
company data from the hybrid API contract. There is no published alert-feed
route; `get_alerts` returns a structured compatibility response.

**No downstream consumers**: Watchdog output is for humans and external systems (Slack channels, Telegram groups, email inboxes, webhook endpoints). No other plugin reads Watchdog's output programmatically.

**Relationship to pipeline plugins**: Watchdog is complementary, not dependent. A user might use Carrier Intel to look up a carrier, Risk Engine to score it, and then add it to the Watchdog watch list for ongoing monitoring. But these are separate user actions, not automated pipeline steps. Watchdog does not import data from or export data to the pipeline plugins.

## Component Design

| Component | Location | Responsibility |
|-----------|----------|---------------|
| **MCP Server** | `scripts/watchdog_mcp.py` | Implements watch synchronization, current-state compliance checks, compatibility errors, and four channel formatters. |
| **Commands** | `commands/` | Slash commands for common watch operations. |
| **Embedded Skill** | `skills/searchcarriers-watchdog/SKILL.md` | Teaches the supported API boundary and safe notification formatting. |
| **Agent** | `agents/watchdog-monitor.md` | Coordinates watch-list and current-state review workflows without inventing unavailable alert history. |

## Data Flow

### Adding a Carrier to the Watch List

```
User: "Add DOT 69494 to my watch list"
  |
  v
the MCP client parses natural language, identifies manage_watchlist tool
  |
  v
MCP Server: manage_watchlist(action="add", dot_number="69494")
  |
  +--> Tier check: is user's tier >= proplus? (yes)
  |
  +--> HTTP POST to Carrier Watch add endpoint
  |    POST /api/v1/company/{dot}/watch
  |    Body: { dot_number: "69494" }
  |
  +--> Parse response: confirm carrier added, return carrier details
  |
  +--> Build response JSON: { meta: {...}, result: { status: "added", carrier: {...} } }
  |
  v
the MCP client receives structured JSON, formats confirmation for user
  |
  v
User sees: "Added WERNER ENTERPRISES INC (DOT 69494) to your watch list."
```

### Formatting a Validated External Event

```
User: "Format this validated carrier event for Slack"
  |
  v
the MCP client validates the caller-supplied event, then calls:
  |
  +--> route_alert(alert={...}, channel="slack")
       |
       +--> Tier check: proplus? (yes)
       |
       +--> Select formatter: slack -> build Block Kit JSON
       |
       +--> Build blocks:
       |    - Header: carrier name + severity badge
       |    - Section: change details (old value -> new value)
       |    - Context: timestamp + source
       |    - Color: red (critical), yellow (warning), green (info)
       |
       +--> Return: { meta: {...}, formatted: { channel: "slack", blocks: [...] } }
  |
  v
the MCP client presents formatted Slack messages to user
  |
  v
User copies the Block Kit JSON to their Slack integration, or sends via webhook
```

### Current-State Compliance Monitoring

```
User: "Check the current compliance posture for DOT 3456789"
  |
  v
MCP Server: monitor_compliance(dot_number="3456789")
  |
  +--> Tier check: proplus? (yes)
  |
  +--> Current company, authority, and insurance requests for DOT 3456789
  |
  +--> Evaluate current evidence:
  |    - active and revoked authority records
  |    - active insurance coverage and federal minimums
  |    - current operating status
  |    - MCS-150 filing freshness
  |
  +--> Return: { compliance_status, checks, drift_items, carrier, ... }
  |
  v
the MCP client receives the current-state assessment and presents the evidence
  |
  v
User sees: current posture, failed checks, and required review actions
```

## Alert Routing Architecture

Watchdog uses a **format-only** architecture for alert routing. This is a deliberate design decision.

```
                    ALERT ROUTING (format-only)
  =====================================================================

  +-------------------+     +-------------------+     +-------------------+
  | External event    |     |  route_alert      |     |  User/Automation  |
  | (validated input) |---->|  (formatting)     |---->|  (delivery)       |
  |                   |     |                   |     |                   |
  |  Notification     |     |  Channel-specific |     |  Sends formatted  |
  |  supplied by the  |     |  formatting:      |     |  message via:     |
  |  caller           |     |  - Slack blocks   |     |  - Slack webhook  |
  |                   |     |  - Telegram MD    |     |  - Telegram Bot   |
  |                   |     |  - Email HTML     |     |  - SMTP/SendGrid  |
  |                   |     |  - Webhook JSON   |     |  - HTTP POST      |
  +-------------------+     +-------------------+     +-------------------+
```

**Why format-only?** Three reasons:

1. **No credential storage.** Sending Slack messages requires OAuth tokens. Sending emails requires SMTP credentials or API keys. Sending Telegram messages requires bot tokens. Storing these credentials in a plugin or environment variable is a security liability. By formatting only, Watchdog never touches delivery credentials.

2. **User controls delivery.** The user decides when, where, and how alerts are sent. They can preview the formatted message before sending. They can modify it. They can route different severities to different channels. This flexibility is impossible if the plugin sends messages directly.

3. **Infrastructure independence.** Watchdog works regardless of whether the user has Slack, Telegram, email, or a custom webhook. The formatting is useful even if the user just reads the formatted output in an MCP-capable client and never sends it anywhere.

## Integration Points

| Endpoint | Method | Used By | Purpose |
|----------|--------|---------|---------|
| `/api/v1/company/{dot}/watch` | POST | `manage_watchlist` (add/remove) | Synchronize watch types; empty array removes watches |
| `/api/v1/company/watch` | GET | `manage_watchlist` (list) | List all watched carriers |
| No published alert-feed route | None | `get_alerts` | Return a structured compatibility error |
| Hybrid current-data routes | GET | `monitor_compliance` | Evaluate current compliance state |

Published endpoints use the `Authorization: Bearer {token}` header and return
JSON. Time-window, type, and severity filters apply only to externally supplied
events passed to the formatter; they are not sent to an undocumented upstream
alert route.

## Security Model

**API key handling:**
- API key is stored in the `SEARCHCARRIERS_API_KEY` environment variable
- The MCP server reads this at startup; if missing, the server fails with a clear error message
- The key is passed as a Bearer token in the Authorization header on every API request
- The key is never logged, never written to disk, never included in tool output

**No delivery credentials:**
- Watchdog does not store, request, or handle Slack tokens, Telegram bot tokens, email passwords, or webhook URLs
- Formatted alert output is returned to the MCP client; the user handles delivery
- This eliminates an entire class of credential management and leakage risks

**Data classification:**
- Watch list data (which carriers a user monitors) is stored on SearchCarriers servers, not locally
- Alert data is derived from public FMCSA records and is not PII
- Compliance checks are computed from current API evidence; the plugin does not claim a historical change feed
- No user-specific data beyond the API key is handled by the plugin

**What gets logged:**
- Tool invocations (tool name, action, DOT number, channel) for debugging
- API response status codes and latency for performance monitoring
- Error conditions (timeouts, rate limits, auth failures)

**What does NOT get logged:**
- Full alert content (stays in context only)
- API keys or tokens
- Formatted messages (may contain carrier details)
- User identity or session information

## Error Handling Strategy

| Error | HTTP Code | User Message | Recovery Action |
|-------|----------|-------------|----------------|
| API key not set | N/A (startup) | "SEARCHCARRIERS_API_KEY not set. Get your key at https://searchcarriers.com/settings/api-tokens" | Block all tool calls until key is configured |
| Invalid API key | 401 | "Invalid API key. Verify your key at https://searchcarriers.com/settings/api-tokens" | No retry -- user must fix key |
| Insufficient tier | 403 | "Watchdog tools require Pro+ tier. Your tier: {tier}. Upgrade at https://searchcarriers.com/pricing" | No retry -- show upgrade path |
| Carrier not found | 404 | "No carrier found for DOT {dot}. Verify the DOT number is correct." | Suggest carrier_lookup for name search |
| Carrier not watched | 404 | "DOT {dot} is not on your watch list." | Suggest manage_watchlist add |
| Rate limited | 429 | "Rate limit reached. Retrying in {n} seconds..." | Respect `Retry-After` header, retry up to 3 times |
| API timeout | 504 | "Carrier Watch API timed out. Retrying..." | Retry up to 3 times with 2s/4s/8s backoff |
| Invalid channel | 422 | "Unsupported channel: {channel}. Supported: slack, telegram, email, webhook" | No retry -- user selects valid channel |
| No alerts found | 200 | "No alerts in the last {hours} hours for your watched carriers." | Informational -- not an error |
| Network error | N/A | "Cannot reach SearchCarriers API. Check your network connection." | No retry -- surface immediately |

All errors return structured JSON: `{ "error": { "code": "TIER_INSUFFICIENT", "message": "...", "upgrade_url": "..." } }`

## Performance Requirements

| Operation | Target Latency | Max Latency | Notes |
|-----------|---------------|-------------|-------|
| `manage_watchlist` (add) | < 1 second | 3 seconds | Single API POST |
| `manage_watchlist` (remove) | < 1 second | 3 seconds | Single API DELETE |
| `manage_watchlist` (list) | < 2 seconds | 5 seconds | Single API GET, may return 200+ carriers |
| `get_alerts` | < 100 milliseconds | 500 milliseconds | Local compatibility response; no API call |
| `route_alert` (single alert) | < 100 milliseconds | 500 milliseconds | Pure formatting, no I/O |
| `route_alert` (batch of 10) | < 500 milliseconds | 2 seconds | 10x formatting calls |
| `monitor_compliance` | < 3 seconds | 8 seconds | Three current-data API calls plus checks |
| MCP server cold start | < 1 second | 3 seconds | Python import + env validation |
| Tier check | < 1 millisecond | N/A | In-memory comparison, no I/O |

Primary bottleneck is network round-trip time to the SearchCarriers API. Alert formatting (`route_alert`) is pure string/JSON construction with no I/O; current-state compliance checks add negligible CPU time.
