# Watchdog - Product Requirements

## Goals

1. **Enable carrier watch list management from an MCP-capable client.** A user types "add DOT 69494 to my watch list" and the carrier is monitored for changes without leaving the terminal. List, add, and remove operations complete in under 3 seconds.
2. **Surface carrier changes as classified alerts.** When a watched carrier's insurance lapses, authority changes, or safety record shifts, Watchdog detects the change and presents it with clear severity classification. Alert retrieval completes in under 5 seconds.
3. **Route alerts to the channels teams already use.** Slack, Telegram, email, and webhook -- Watchdog formats alerts for each channel's native message format. Formatted alerts are returned to the MCP client for delivery; Watchdog does not send messages directly.
4. **Track compliance drift over time.** Beyond point-in-time alerts, Watchdog shows whether a carrier's compliance posture is improving, stable, or deteriorating. This longitudinal view is what compliance managers and auditors need.

## Non-Goals

1. **NOT replacing SearchCarriers Carrier Watch web UI.** The web UI provides visual dashboards, notification preferences, and team-wide monitoring. This plugin serves users who want watch list management and alert access in their terminal.
2. **NOT sending alerts directly.** Watchdog formats alert messages for each channel (Slack blocks, Telegram markdown, email HTML, webhook JSON). The user or their automation sends the formatted message. Watchdog is a formatting tool, not a delivery service. This avoids storing OAuth tokens, webhook URLs, or SMTP credentials.
3. **NOT part of the stackable pipeline.** Watchdog is a standalone monitoring plugin. It does not consume output from Carrier Intel, Risk Engine, or Ops Reporter. It does not produce output for other plugins to consume. It operates independently against the SearchCarriers Carrier Watch API.
4. **No alert-feed retrieval.** The public API does not expose an alert-feed
   route. `get_alerts` exists only to return a truthful compatibility response.
5. **NOT storing watch list data locally.** The watch list lives on SearchCarriers servers. Watchdog is a stateless client that reads and writes via the Carrier Watch API.

## User Stories

### US-01: Add Carrier to Watch List

As an **operations manager**, I want to **add a carrier to my watch list by DOT number**, so that **I am alerted when that carrier's insurance, authority, or safety status changes**.

**Acceptance Criteria:**
- Adding a carrier by DOT number confirms the addition with carrier name and DOT
- Adding a carrier already on the watch list returns a clear "already watching" message
- Adding an invalid DOT returns a clear error with suggestions
- The watch list is persisted server-side (not local)

### US-02: Remove Carrier from Watch List

As a **compliance analyst**, I want to **remove a carrier from my watch list when we no longer work with them**, so that **I stop receiving alerts for carriers that are no longer in our panel**.

**Acceptance Criteria:**
- Removing a carrier by DOT number confirms the removal
- Removing a carrier not on the watch list returns a clear "not found" message
- Removal is immediate; no further alerts are generated for that carrier

### US-03: View Watch List

As a **freight broker**, I want to **see all carriers currently on my watch list**, so that **I can verify my monitoring coverage and identify gaps**.

**Acceptance Criteria:**
- List returns all watched carriers with DOT, legal name, and date added
- List supports pagination for large watch lists (50+ carriers)
- Empty watch list returns a helpful "no carriers watched" message with instructions to add

### US-04: Retrieve Recent Alerts

As an **operations manager**, I want to **pull recent alerts for my watched carriers**, so that **I can review what changed since my last check and take action on critical items**.

**Acceptance Criteria:**
- Returns alerts within a configurable time window (default: last 24 hours)
- Alerts categorized by type: safety, insurance, authority, operational
- Alerts classified by severity: critical, warning, info
- Each alert includes: carrier name, DOT, change type, old value, new value, timestamp
- Empty result returns "no alerts in the last {period}" message

### US-05: Route Alert to Slack

As a **compliance lead**, I want to **format an alert as a Slack message with Block Kit formatting**, so that **I can send it to our #carrier-alerts channel and my team sees a rich, readable notification**.

**Acceptance Criteria:**
- Output is valid Slack Block Kit JSON
- Critical alerts use red color indicator, warnings use yellow, info uses blue
- Message includes carrier name, DOT, change summary, and timestamp
- Output is ready to POST to a Slack webhook (user handles delivery)

### US-06: Route Alert to Telegram

As a **dispatcher**, I want to **format an alert as a Telegram message**, so that **I can send it to our dispatch group chat for immediate visibility**.

**Acceptance Criteria:**
- Output is Telegram-compatible markdown
- Uses bold, italic, and emoji for readability on mobile
- Includes carrier name, DOT, change type, and severity
- Output is ready for Telegram Bot API `sendMessage` (user handles delivery)

### US-07: Monitor Compliance Drift

As a **compliance manager**, I want to **see how a carrier's compliance posture has changed over time**, so that **I can identify deteriorating carriers before they become a problem and prepare for audits**.

**Acceptance Criteria:**
- Shows compliance events over a configurable period (default: 90 days)
- Tracks: insurance changes, authority changes, safety rating changes, OOS rate trends
- Identifies drift direction: improving, stable, deteriorating
- Includes change count and most recent change details

### US-08: Email Alert Formatting

As an **account manager**, I want to **format an alert as an HTML email**, so that **I can forward carrier status changes to customers who need visibility into their carrier panel**.

**Acceptance Criteria:**
- Output is a complete HTML email body (not a full MIME message)
- Professional formatting with tables, colors, and clear structure
- Includes carrier details, change summary, and recommended action
- Output is ready to embed in an email send API call

## Functional Requirements

### FR-01: Watch List CRUD Operations

**Description:** The `manage_watchlist` tool supports three actions: `add` (add a carrier by DOT), `remove` (remove a carrier by DOT), and `list` (return all watched carriers). All operations go through the SearchCarriers Carrier Watch API.

**Acceptance Criteria:**
- `add` action accepts a DOT number and calls the Carrier Watch add endpoint
- `remove` action accepts a DOT number and calls the Carrier Watch remove endpoint
- `list` action returns all watched carriers with pagination support
- All actions require Pro+ tier
- All actions return structured JSON with a `meta` block

**Priority:** P0

### FR-02: Truthful Alert-Feed Compatibility

**Description:** The `get_alerts` tool preserves client compatibility while
clearly reporting that the published API has no alert-feed route.

**Acceptance Criteria:**
- Makes no upstream HTTP call
- Returns the `endpoint_unavailable` error code
- Names the documented company-watch routes
- Directs users to their configured SearchCarriers notification channel

**Priority:** P0

### FR-03: Alert Severity Classification

**Description:** Caller-supplied events are classified into three severity
levels while `route_alert` formats them. Classification does not imply that the
event came from a SearchCarriers alert-feed endpoint.

**Acceptance Criteria:**
- **Critical**: Authority revoked, insurance policy cancelled, Out-of-Service order issued
- **Warning**: Insurance expiring within 30 days, safety rating downgrade, authority status change
- **Info**: MCS-150 filing update, fleet size change, address change, contact update
- Severity is included in every alert object

**Priority:** P0

### FR-04: Slack Block Kit Formatting

**Description:** The `route_alert` tool with `channel="slack"` formats an alert into Slack Block Kit JSON. The output is a valid blocks array ready for the Slack `chat.postMessage` API or incoming webhook.

**Acceptance Criteria:**
- Output is valid Slack Block Kit JSON (array of block objects)
- Severity mapped to color: critical = danger (red), warning = warning (yellow), info = good (green)
- Includes header block with carrier name, section blocks with change details
- Context block with timestamp and source attribution

**Priority:** P1

### FR-05: Telegram Markdown Formatting

**Description:** The `route_alert` tool with `channel="telegram"` formats an alert into Telegram MarkdownV2 format. The output is a string ready for the Telegram Bot API `sendMessage` endpoint with `parse_mode=MarkdownV2`.

**Acceptance Criteria:**
- Output is valid Telegram MarkdownV2 (escaped special characters)
- Uses bold for carrier name and severity, monospace for DOT numbers
- Severity indicators: CRITICAL, WARNING, INFO with appropriate emoji
- Compact format suitable for mobile reading

**Priority:** P1

### FR-06: Email HTML Formatting

**Description:** The `route_alert` tool with `channel="email"` formats an alert into an HTML email body. The output is a complete `<div>` element suitable for embedding in an email template or sending via an email API.

**Acceptance Criteria:**
- Output is valid HTML with inline CSS (email-client compatible)
- Professional table layout with severity-colored header
- Includes carrier details, change summary, recommended action, and footer
- Renders correctly in Gmail, Outlook, and Apple Mail

**Priority:** P2

### FR-07: Webhook JSON Formatting

**Description:** The `route_alert` tool with `channel="webhook"` formats an alert into a generic JSON payload suitable for any webhook consumer. The output is a standardized JSON object with all alert data.

**Acceptance Criteria:**
- Output is a flat JSON object with consistent field names
- Includes: carrier_dot, carrier_name, alert_type, severity, change_field, old_value, new_value, timestamp
- Follows common webhook conventions (no nested objects beyond one level)
- Suitable for consumption by Zapier, Make, n8n, or custom webhook handlers

**Priority:** P2

### FR-08: Compliance Drift Detection

**Description:** The `monitor_compliance` tool retrieves current carrier,
authority, and insurance data and evaluates the carrier against explicit
compliance checks.

**Acceptance Criteria:**
- Accepts a DOT number and returns itemized pass/fail checks
- Checks operating authority, revoked authority, insurance coverage, operating status, and filing freshness
- Returns `compliant`, `drift`, or `critical` from current evidence
- Lists failed checks in `drift_items` without claiming historical trend data

**Priority:** P1

## MVP Scope

Initial v0.1.0 planning scope (superseded where the public API contract differs):

- [ ] `manage_watchlist` -- add, remove, list operations via Carrier Watch API
- [ ] `get_alerts` -- compatibility response explaining that no published alert-feed route exists
- [ ] `route_alert` -- Slack and webhook formatting (email and Telegram in v0.2)
- [ ] `monitor_compliance` -- compliance drift detection with trend analysis
- [ ] Tier gating on all four tools (Pro+ required)
- [ ] Structured JSON output with meta blocks
- [ ] Error handling for 401, 403, 404, 429, 504

Deferred to v0.2.0:

- Telegram MarkdownV2 formatting for route_alert
- Email HTML formatting for route_alert
- Alert digest mode (batch multiple alerts into a single formatted message)
- Watch list groups (organize carriers by lane, customer, or category)
- Compliance drift comparison across multiple carriers

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|-------------|
| Alert retrieval latency | Target: < 3 seconds | Timer in MCP tool handler |
| Watch list operation latency | Target: < 2 seconds | Timer per add/remove/list |
| Alert formatting latency | Target: < 500 milliseconds | Timer in route_alert handler |
| Compliance drift computation | Target: < 5 seconds | Timer across history retrieval + analysis |
| Missed critical alerts | Target: 0 (every critical change surfaces) | Integration tests against known change events |
| Tier gate accuracy | Target: 100% (no non-Pro+ user accesses tools) | Unit tests |
| Alert severity accuracy | Target: > 95% correct classification | Manual review of alert classification against FMCSA change types |

## Dependencies

- **SearchCarriers API** -- watch management uses the documented v1 company-watch routes; compliance monitoring reads current company data through the hybrid API contract. Alert formatting accepts validated external events because no alert-feed route is published.
- **Valid API key with Pro+ tier** -- `SEARCHCARRIERS_API_KEY` environment variable must be set with a Pro+ tier Laravel Sanctum bearer token
- **MCP protocol** -- plugin runs as an MCP server; requires Grok Build, Claude Code, or another MCP-capable client
- **httpx** -- async HTTP client for API calls
- **No dependency on pipeline plugins** -- Watchdog is standalone. It does not consume output from Carrier Intel, Risk Engine, or Ops Reporter. It can be installed and used independently.
