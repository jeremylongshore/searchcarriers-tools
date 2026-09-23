# Watchdog - User Journey

## Persona

**Name:** Mike Rodriguez
**Role:** Operations Manager at a mid-size 3PL (120 employees, 450 loads/day)
**Goal:** Keep his 200+ carrier panel compliant and catch status changes before they cause claims
**Tier:** Pro+ ($99/month -- his company upgraded after a $73,000 cargo claim from a carrier whose insurance had lapsed unnoticed)
**Current workflow:** Mike's compliance team runs quarterly carrier re-qualifications by manually checking each carrier on FMCSA SAFER. Between re-qualifications, nobody is watching. Carriers on the approved panel are assumed to be good until the next quarterly check or until something goes wrong.
**Pain:** Two months ago, Mike tendered a high-value electronics load to a carrier that had been on his approved list for 18 months. The carrier's common authority had been revoked three weeks earlier due to an unpaid fine. The carrier moved the load anyway, but the shipper's insurance company denied the claim because the carrier was not legally authorized to operate. Mike's 3PL absorbed a $73,000 loss. His CEO asked: "How are we monitoring our carrier panel?"

## Prerequisites

- [ ] SearchCarriers account with Pro+ tier -- upgrade at [searchcarriers.com/pricing](https://searchcarriers.com/pricing)
- [ ] API key generated at [searchcarriers.com/settings/api-tokens](https://searchcarriers.com/settings/api-tokens)
- [ ] API key set in environment: `export SEARCHCARRIERS_API_KEY="your_id|your_token"`
- [ ] Claude Code installed with MCP support
- [ ] Watchdog plugin installed: copy `searchcarriers-watchdog/` to `.claude/plugins/` or configure in `.mcp.json`

## Step-by-Step Walkthrough

### Step 1: Build the Watch List

Mike starts by adding his most critical carriers to the watch list. He has their DOT numbers from his TMS export.

```
Add DOT 69494 to my watch list
```

**What happens behind the scenes:**
1. Claude invokes `manage_watchlist` with `action="add"` and `dot_number="69494"`
2. The MCP server checks tier: user must be Pro+
3. API call: `POST /api/v1/company/69494/watch` with body `{ "watch_types": ["all"] }`
4. Carrier Watch API confirms the addition and returns carrier details

**Expected output:**

```
Added to watch list:

  WERNER ENTERPRISES INC
  DOT: 69494 | MC: MC-14983
  Status: Active | Rating: Satisfactory
  Added: 2026-02-26

Your watch list now has 1 carrier.
```

Mike adds a few more carriers:

```
Add these carriers to my watch list: DOT 2247895, DOT 3456789, DOT 1872034
```

**Expected output:**

```
Added 3 carriers to watch list:

  1. HEARTLAND EXPRESS INC (DOT 2247895) -- Active, Satisfactory
  2. COLD STAR LOGISTICS LLC (DOT 3456789) -- Active, No Rating
  3. MIDWEST FREIGHT SERVICES INC (DOT 1872034) -- Active, Conditional

Your watch list now has 4 carriers.
```

Mike notices DOT 1872034 has a Conditional safety rating. He makes a mental note to check that one more carefully later.

### Step 2: View the Watch List

After adding carriers over the course of a week, Mike wants to verify his monitoring coverage.

```
Show me my carrier watch list
```

**What happens behind the scenes:**
1. Claude invokes `manage_watchlist` with `action="list"`
2. API call: `GET /api/v1/company/watch`
3. Returns all watched carriers with details

**Expected output:**

```
CARRIER WATCH LIST (12 carriers)
==================================

  #    DOT         Carrier Name                         Status     Rating          Added
  --   ---------   ----------------------------------   --------   -------------   ----------
  1    69494       WERNER ENTERPRISES INC               Active     Satisfactory    2026-02-26
  2    2247895     HEARTLAND EXPRESS INC                 Active     Satisfactory    2026-02-26
  3    3456789     COLD STAR LOGISTICS LLC               Active     None            2026-02-26
  4    1872034     MIDWEST FREIGHT SERVICES INC          Active     Conditional     2026-02-26
  5    27021       KLLM TRANSPORT SERVICES INC           Active     Satisfactory    2026-02-27
  6    2345671     SUMMIT CARRIERS LLC                   Active     Satisfactory    2026-02-27
  7    890123      PRIME INC                             Active     Satisfactory    2026-02-28
  8    4501234     RELIABLE REEFER TRANSPORT INC         Active     None            2026-02-28
  9    3212456     DELTA LOGISTICS GROUP LLC             Active     Satisfactory    2026-03-01
  10   1567890     WESTBOUND FREIGHT SOLUTIONS INC       Active     Satisfactory    2026-03-01
  11   2890345     EAGLE TRANSPORT SERVICES LLC          Active     None            2026-03-02
  12   4123456     COASTAL HAULING INC                   Active     Satisfactory    2026-03-02
```

Mike sees all 12 carriers on his critical list. Three have no safety rating (newer or unaudited carriers). One has a Conditional rating. He has visibility into exactly what he is monitoring.

### Step 3: Check for Alerts

Two weeks later, Mike's morning routine includes checking for carrier alerts.

```
Any alerts on my watched carriers in the last 24 hours?
```

**What happens behind the scenes:**
1. Claude invokes `get_alerts` with `hours=24`
2. `get_alerts` returns `endpoint_unavailable`; the published API has no alert-feed route.
3. Returns alerts sorted by severity and timestamp

**Expected output:**

```
CARRIER WATCH ALERTS (last 24 hours)
=====================================

3 alerts found:

CRITICAL
--------
  [1] INSURANCE CANCELLED -- COLD STAR LOGISTICS LLC (DOT 3456789)
      Change: Cargo insurance policy CANCELLED
      Previous: $100,000 coverage (Active, expires 2026-03-20)
      Current:  No active cargo insurance on file
      Detected: 2026-03-15 08:14:00 UTC
      Action:   DO NOT TENDER loads to this carrier until coverage is confirmed

WARNING
-------
  [2] SAFETY RATING DOWNGRADE -- MIDWEST FREIGHT SERVICES INC (DOT 1872034)
      Change: Safety rating changed from Conditional to Unsatisfactory
      Previous: Conditional (since 2025-06-01)
      Current:  Unsatisfactory (since 2026-03-14)
      Detected: 2026-03-15 06:30:00 UTC
      Action:   Review carrier qualification; Unsatisfactory rating may disqualify

INFO
----
  [3] MCS-150 FILED -- EAGLE TRANSPORT SERVICES LLC (DOT 2890345)
      Change: MCS-150 biennial update filed
      Previous: Filed 2024-03-15 (overdue)
      Current:  Filed 2026-03-14 (current)
      Detected: 2026-03-15 04:15:00 UTC
      Action:   No action required; this is a positive compliance indicator
```

Mike sees three alerts. The critical one is immediately actionable -- Cold Star's cargo insurance was cancelled. He needs to stop tendering loads to them right now and notify his dispatch team.

### Step 4: Route the Critical Alert to Slack

Mike's dispatch team monitors a `#carrier-alerts` channel in Slack. He needs the insurance cancellation alert formatted for Slack.

```
Format alert 1 for Slack
```

**What happens behind the scenes:**
1. Claude invokes `route_alert` with the alert data and `channel="slack"`
2. The formatter builds Slack Block Kit JSON with severity coloring
3. Returns the formatted blocks array

**Expected output:**

```
Formatted for Slack (Block Kit JSON):

{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "CRITICAL: Insurance Cancelled",
        "emoji": true
      }
    },
    {
      "type": "section",
      "fields": [
        {
          "type": "mrkdwn",
          "text": "*Carrier:*\nCOLD STAR LOGISTICS LLC"
        },
        {
          "type": "mrkdwn",
          "text": "*DOT:*\n3456789"
        }
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
        {
          "type": "mrkdwn",
          "text": "Detected: 2026-03-15 08:14 UTC | Source: SearchCarriers Carrier Watch"
        }
      ]
    }
  ],
  "attachments": [
    {
      "color": "#dc3545"
    }
  ]
}

To send this to Slack, POST this JSON to your Slack incoming webhook URL:
  curl -X POST -H 'Content-Type: application/json' \
    -d '<above JSON>' \
    https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

Mike copies the JSON and posts it to his Slack webhook. His dispatch team sees a red-flagged alert in their channel within seconds.

### Step 5: Route an Alert to Telegram

Mike's overnight dispatch team uses Telegram. He wants the same alert sent there.

```
Format alert 1 for Telegram
```

**Expected output:**

```
Formatted for Telegram (MarkdownV2):

🚨 *CRITICAL: Insurance Cancelled*

*Carrier:* COLD STAR LOGISTICS LLC
*DOT:* `3456789`

*Change:* Cargo insurance policy CANCELLED
*Previous:* $100,000 coverage \(Active\)
*Current:* No active cargo insurance on file

⚠️ *Action Required:* DO NOT TENDER loads to this carrier until coverage is confirmed\.

_Detected: 2026\-03\-15 08:14 UTC \| Source: SearchCarriers Carrier Watch_

To send via Telegram Bot API:
  curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/sendMessage" \
    -d chat_id=<CHAT_ID> \
    -d parse_mode=MarkdownV2 \
    -d text='<above text>'
```

### Step 6: Check Compliance Drift

After the insurance cancellation alert, Mike wants to know if Cold Star has been deteriorating over time or if this was an isolated event.

```
Show me the compliance drift for DOT 3456789 over the last 6 months
```

**What happens behind the scenes:**
1. Claude invokes `monitor_compliance` with `dot_number="3456789"` and `days=180`
2. Fetch current company, authority, and insurance data for DOT 3456789.
3. Drift analyzer categorizes each change event and computes the trend

**Expected output:**

```
COMPLIANCE DRIFT: COLD STAR LOGISTICS LLC (DOT 3456789)
========================================================

Period: 2025-09-15 to 2026-03-15 (180 days)
Drift Direction: DETERIORATING

CHANGE TIMELINE
  Date          Type         Change                              Severity
  ----------    ---------    ----------------------------------  --------
  2025-10-02    Insurance    Cargo coverage reduced $250K->$100K WARNING
  2025-11-18    Safety       Vehicle OOS rate increased 22%->31% WARNING
  2026-01-05    Operational  MCS-150 filing became overdue       INFO
  2026-02-10    Safety       Driver OOS rate increased 5%->8.2%  INFO
  2026-03-14    Insurance    Cargo insurance CANCELLED           CRITICAL

SUMMARY
  Total changes:      5
  Critical changes:   1
  Warning changes:    2
  Info changes:       2
  Days since last:    1

DRIFT ASSESSMENT
  Direction: DETERIORATING
  Pattern:   Progressive decline over 6 months. Insurance coverage reduced
             in October, OOS rates rising through winter, insurance cancelled
             in March. This carrier shows a consistent negative trajectory.

  Recommendation: Remove from approved carrier panel. This carrier has shown
  a pattern of declining compliance posture over the past 6 months. If the
  carrier is retained, require proof of insurance reinstatement, updated
  MCS-150 filing, and a corrective action plan before tendering any loads.
```

Mike now has the evidence he needs. Cold Star is not just having a bad day -- they have been deteriorating for six months. He removes them from the watch list and the approved carrier panel.

### Step 7: Remove a Carrier from the Watch List

```
Remove DOT 3456789 from my watch list
```

**Expected output:**

```
Removed from watch list:

  COLD STAR LOGISTICS LLC (DOT 3456789)
  Removed: 2026-03-15

Your watch list now has 11 carriers.
```

### Step 8: Route an Alert for Webhook Integration

Mike's company uses an internal system that accepts webhook payloads. He wants to format alerts in a generic JSON structure for automation.

```
Format alert 2 for webhook
```

**Expected output:**

```
Formatted for webhook (JSON payload):

{
  "event": "carrier_alert",
  "severity": "warning",
  "carrier_dot": "1872034",
  "carrier_name": "MIDWEST FREIGHT SERVICES INC",
  "alert_type": "safety",
  "change_field": "safety_rating",
  "old_value": "Conditional",
  "new_value": "Unsatisfactory",
  "detected_at": "2026-03-15T06:30:00Z",
  "action": "Review carrier qualification; Unsatisfactory rating may disqualify",
  "source": "SearchCarriers Carrier Watch"
}

To send to your webhook:
  curl -X POST -H 'Content-Type: application/json' \
    -d '<above JSON>' \
    https://your-internal-system.com/webhooks/carrier-alerts
```

### Step 9: Format an Alert for Email

Mike's account manager needs to notify a customer about the safety rating downgrade on a carrier in their dedicated fleet.

```
Format alert 2 for email
```

**Expected output:**

```
Formatted for email (HTML body):

<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <div style="background-color: #ffc107; padding: 16px; border-radius: 4px 4px 0 0;">
    <h2 style="margin: 0; color: #333;">⚠️ WARNING: Safety Rating Downgrade</h2>
  </div>
  <div style="padding: 20px; border: 1px solid #ddd; border-top: none;">
    <table style="width: 100%; border-collapse: collapse;">
      <tr>
        <td style="padding: 8px; font-weight: bold; width: 120px;">Carrier:</td>
        <td style="padding: 8px;">MIDWEST FREIGHT SERVICES INC</td>
      </tr>
      <tr>
        <td style="padding: 8px; font-weight: bold;">DOT:</td>
        <td style="padding: 8px;">1872034</td>
      </tr>
      <tr>
        <td style="padding: 8px; font-weight: bold;">Change:</td>
        <td style="padding: 8px;">Safety rating changed from Conditional to Unsatisfactory</td>
      </tr>
      <tr>
        <td style="padding: 8px; font-weight: bold;">Previous:</td>
        <td style="padding: 8px;">Conditional (since 2025-06-01)</td>
      </tr>
      <tr>
        <td style="padding: 8px; font-weight: bold;">Current:</td>
        <td style="padding: 8px;">Unsatisfactory (since 2026-03-14)</td>
      </tr>
    </table>
    <div style="margin-top: 16px; padding: 12px; background-color: #fff3cd; border-radius: 4px;">
      <strong>Recommended Action:</strong> Review carrier qualification.
      An Unsatisfactory safety rating may disqualify this carrier from your
      approved panel per company policy and shipper requirements.
    </div>
  </div>
  <div style="padding: 12px; font-size: 12px; color: #666; text-align: center;">
    Detected: 2026-03-15 06:30 UTC | Source: SearchCarriers Carrier Watch
  </div>
</div>

To send, embed this HTML in your email API (SendGrid, SES, etc.) or
paste into your email client as HTML.
```

## Error Scenarios

### Scenario: No Pro+ Tier

**Trigger:** A Pro-tier user attempts to use any Watchdog tool.

```
Add DOT 69494 to my watch list
```

**Response:**

```
Carrier Watch tools require a Pro+ subscription.
Your current tier: Pro

Watchdog provides ongoing carrier monitoring with:
  - Watch list management (add, remove, list carriers)
  - Change alerts (safety, insurance, authority changes)
  - Multi-channel alert routing (Slack, Telegram, email, webhook)
  - Compliance drift monitoring (trend analysis over time)

Upgrade at https://searchcarriers.com/pricing

Tools available on your Pro tier:
  - Carrier Intel: carrier_lookup, carrier_profile, entity_map, fleet_summary
  - Risk Engine: risk_score, insurance_check, compliance_audit, vetting_check
  - Ops Reporter: generate_report, generate_fleet, generate_compare, export_data
```

### Scenario: Carrier Already on Watch List

**Trigger:** Adding a carrier that is already being watched.

```
Add DOT 69494 to my watch list
```

**Response:**

```
WERNER ENTERPRISES INC (DOT 69494) is already on your watch list.
Added: 2026-02-26

No action needed. You will continue to receive alerts for this carrier.
```

### Scenario: API Key Not Set

**Trigger:** Running any command without `SEARCHCARRIERS_API_KEY` in environment.

```
Show my watch list
```

**Response:**

```
SearchCarriers API key is not configured.

To set up your API key:
1. Sign up or log in at https://searchcarriers.com
2. Go to Settings > API (https://searchcarriers.com/settings/api-tokens)
3. Generate a new API token
4. Set the environment variable:

   export SEARCHCARRIERS_API_KEY="your_id|your_token"

   Or add it to your .env file for persistence.
```

### Scenario: No Alerts Found

**Trigger:** Checking for alerts when nothing has changed.

```
Any critical alerts in the last 24 hours?
```

**Response:**

```
No critical alerts in the last 24 hours.

Your 12 watched carriers have no critical changes to report. This is good
news -- all carriers on your watch list maintain their current status.

To check for all alert types (including warnings and info):
  "Show all alerts from the last 24 hours"

To extend the time window:
  "Any alerts in the last 7 days?"
```

### Scenario: Rate Limit Hit

**Trigger:** Rapid successive API calls.

```
Rate limit reached on SearchCarriers API. Waiting 2 seconds before retrying...

[Retrying...]

CARRIER WATCH ALERTS (last 24 hours)
[results follow]
```

## FAQ

**Q: How often does Watchdog check for changes?**
A: Watchdog does not poll automatically. `monitor_compliance` evaluates current company, authority, and insurance data when invoked. The published API does not expose an alert-feed route, so `get_alerts` returns a structured compatibility error.

**Q: Can I set up automatic polling?**
A: Schedule `monitor_compliance` with your own automation if you need periodic current-state checks. Feed a validated event from your notification channel into `route_alert` when you need channel-specific formatting.

**Q: What types of changes trigger alerts?**
A: Insurance changes (new policy, cancellation, expiration, coverage amount changes), authority changes (granted, revoked, suspended, reinstated), safety changes (rating upgrade/downgrade, OOS rate changes), and operational changes (MCS-150 filings, fleet size changes, address changes, status changes).

**Q: Does Watchdog send messages directly to Slack/Telegram/email?**
A: No. Watchdog formats messages for each channel but does not send them. This is intentional -- it avoids storing delivery credentials (Slack tokens, email passwords, etc.) in the plugin. You send the formatted message using your existing tools: a Slack webhook, the Telegram Bot API, your email service, or a custom script.

**Q: How many carriers can I watch?**
A: The watch list limit depends on your SearchCarriers account. Pro+ tier typically supports up to 500 watched carriers. Contact SearchCarriers for enterprise limits beyond that.

**Q: What is compliance drift?**
A: Compliance drift is the change in a carrier's compliance posture over time. A single point-in-time check tells you "this carrier is OK right now." Drift analysis tells you "this carrier has been getting worse over the past 6 months." It tracks insurance status changes, authority changes, safety rating movements, and operational updates to compute whether the carrier is improving, stable, or deteriorating.

**Q: Can I use Watchdog without the other pipeline plugins?**
A: Yes. Watchdog is completely standalone. You do not need Carrier Intel, Risk Engine, or Ops Reporter installed. Watchdog connects directly to the SearchCarriers Carrier Watch API for all its data. That said, using Watchdog alongside the pipeline plugins gives you a complete workflow: look up a carrier (Carrier Intel), assess its risk (Risk Engine), generate a report (Ops Reporter), and monitor it ongoing (Watchdog).

**Q: What is the difference between `get_alerts` and `monitor_compliance`?**
A: `get_alerts` exists for compatibility and reports that no published alert-feed endpoint is available. `monitor_compliance` performs a current-state compliance evaluation for one DOT number.

**Q: Can I filter alerts by carrier?**
A: Apply filters in the notification system that produced the event, then pass the selected event to `route_alert`. Watchdog does not claim an upstream alert-filtering API.

**Q: What happens if I remove a carrier and re-add it?**
A: Removal synchronizes the carrier to an empty `watch_types` array. Re-adding synchronizes the requested watch types. The plugin makes no retention claim about upstream alert history.
